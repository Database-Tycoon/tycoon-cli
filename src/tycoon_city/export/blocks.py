"""The per-section builders behind `city.json`: one function per document block.

Split out of `city_json` on 2026-08-06 so the assembler stays a readable list of
blocks while four workstreams add their own. `city_json` remains the only
module that assembles a document and the only one that serialises it;
everything here builds *one* value and returns plain data.

`docs/city-json-v1.md` is normative for every shape below. The same three
properties the assembler guarantees constrain each builder: byte-stable output
(sort on a key that cannot tie, round floats, emit no timestamp or path), no
pygame, and no engine (derived state only, never tweened presentation state).

Names are re-exported from `city_json` so the historical import paths --
`from tycoon_city.export.city_json import encode_rle`, `_focus` and friends --
keep resolving.
"""

from typing import Any

from ..catalog.models import PipelineContext
from ..catalog.run_history import daily_load_s
from ..sim.build_replay import ReplayPlan, plan_replay
from ..sim.city import CityMap
from ..sim.tiles import TileKind
from ..theme_data import ThemeData

# Tile kind ids are positions in this legend, and the legend ships inside every
# document as `grid.tile_kinds` -- so a client resolves a name, never a bare
# number, and inserting a kind into TileKind renumbers the wire ids without
# breaking anything that reads the legend. Derived from the enum's declaration
# order rather than from `TileKind.value`, which `auto()` happens to make
# 1-based; nothing should depend on that coincidence.
TILE_KINDS: tuple[str, ...] = tuple(kind.name.lower() for kind in TileKind)
_TILE_ID: dict[TileKind, int] = {kind: index for index, kind in enumerate(TileKind)}

# Edge rates are normalised 0..1 and drive a spawn probability, so six decimals
# is far past anything visible. Rounding is what keeps the JSON readable and the
# golden diffable instead of carrying 17 significant digits of division noise.
RATE_PRECISION = 6


def encode_rle(tiles: list[list[TileKind]]) -> list[int]:
    """Row-major run-length encoding: a flat `[kind_id, run, kind_id, run, ...]`.

    Runs cross row boundaries. That is deliberate -- a grid whose rows are mostly
    one colour encodes to a handful of runs instead of one pair per row -- and it
    is why decoding needs the width to re-split rows.

    Measured against the alternatives on three catalogs (see
    `docs/city-json-v1.md`): this beats shipping the raw grid everywhere,
    decisively on realistic catalogs and still by a third on the pathological
    one.
    """
    runs: list[int] = []
    for row in tiles:
        for tile in row:
            kind = _TILE_ID[tile]
            # runs holds pairs, so it is either empty or has a kind at -2.
            if runs and runs[-2] == kind:
                runs[-1] += 1
            else:
                runs.extend((kind, 1))
    return runs


def decode_rle(runs: list[int], width: int, height: int) -> list[list[TileKind]]:
    """Inverse of `encode_rle`. Used by the round-trip test and mirrored in JS.

    Raises `ValueError` when the runs do not describe exactly `width * height`
    cells, which is the only way a truncated or doctored document can be caught
    before it renders as a subtly shifted map.
    """
    if len(runs) % 2 != 0:
        raise ValueError(f"tiles_rle must hold (kind, run) pairs; got {len(runs)} numbers")
    kinds = list(TileKind)
    flat: list[TileKind] = []
    for index in range(0, len(runs), 2):
        kind_id, run = runs[index], runs[index + 1]
        if not 0 <= kind_id < len(kinds):
            raise ValueError(f"unknown tile kind id {kind_id}")
        if run < 1:
            raise ValueError(f"run length must be positive; got {run}")
        flat.extend([kinds[kind_id]] * run)
    if len(flat) != width * height:
        raise ValueError(f"tiles_rle decodes to {len(flat)} cells, expected {width * height}")
    return [flat[y * width : (y + 1) * width] for y in range(height)]


def _focus(city: CityMap) -> dict[str, int]:
    """Bounding box of every lot plus the plant, in tile coordinates, inclusive.

    Exactly the coordinate set `app._built_tiles` frames the 2D camera on, so the
    opening 3D frame inherits the framing policy instead of inventing one.
    `tests/export/test_build.py` asserts the two agree rather than trusting this
    comment. Lots and LOT tiles coincide because the generator writes one for
    every lot it records.

    A catalog with no objects still has a plant, so the box is never empty.
    """
    xs = [x for lot in city.lots.values() for x in (lot.x, lot.x + lot.w - 1)]
    ys = [y for lot in city.lots.values() for y in (lot.y, lot.y + lot.h - 1)]
    xs.append(city.plant_xy[0])
    ys.append(city.plant_xy[1])
    # Civic buildings join the frame so the opening camera never crops them.
    for civic in (city.library_xy, city.firehouse_xy):
        if civic is not None:
            xs.append(civic[0])
            ys.append(civic[1])
    return {"min_x": min(xs), "min_y": min(ys), "max_x": max(xs), "max_y": max(ys)}


def _districts(city: CityMap) -> list[dict[str, Any]]:
    # Streets v2: districts are bounding rectangles around a schema's placed
    # lots (w/h replaced the ring-era square `size`/`ring` on 2026-08-05).
    return [
        {
            "schema": district.schema,
            "x": district.x,
            "y": district.y,
            "w": district.w,
            "h": district.h,
        }
        # Schema names are unique per district, so this order cannot tie.
        for district in sorted(city.districts, key=lambda d: d.schema)
    ]


def _street_features(city: CityMap) -> list[dict[str, Any]]:
    """How every road is allowed to END (streets v4, 2026-08-05).

    A derived fact the tile grid cannot express: a ROAD tile says nothing about
    which building it serves, which way it faces, or that it is a paved
    forecourt rather than a lane. `facing` is null only if a future kind has no
    building to point at — every kind in this version has one. Sorted by
    (kind, x, y), with the remaining fields breaking the tie a tile serving two
    buildings creates, so the array is byte-stable.
    """
    return [
        {
            "kind": feature.kind,
            "x": feature.x,
            "y": feature.y,
            "facing": feature.facing,
            "w": feature.w,
            "h": feature.h,
        }
        for feature in sorted(
            city.street_features,
            key=lambda f: (f.kind, f.x, f.y, f.facing or "", f.w, f.h),
        )
    ]


def _lots(city: CityMap) -> list[dict[str, Any]]:
    """Placement and derived visual state, one record per placed object.

    `target_density` and not `density`: the tween is presentation, so the client
    animates 0 -> target itself. Emitting the tweened value would make the
    document depend on how many ticks happened to have run.

    `zone_style` is already resolved. The theme's `[[style_rules]]` regexes never
    cross the wire and no client re-implements pattern matching.
    """
    return [
        {
            "object_key": lot.object_key,
            "x": lot.x,
            "y": lot.y,
            # Ground plan in tiles, NW-anchored: big tables (top decile of
            # this catalog's row counts) are 2x2, everything else 1x1.
            "w": lot.w,
            "h": lot.h,
            "zone_style": lot.zone_style.name.lower(),
            "target_density": lot.target_density,
            "powered": lot.powered,
            # Temporal signals (Phase F). null means UNKNOWN and the client
            # must render unknown as full colour, no tint, no marker — never
            # as stale. Age in whole seconds so the document stays diffable.
            "last_build_age_s": (int(lot.last_build_age_s) if lot.last_build_age_s is not None else None),
            "build_status": lot.build_status,
            "test_status": lot.test_status,
            "freshness_status": lot.freshness_status,
            "schema_drift_age_s": (int(lot.schema_drift_age_s) if lot.schema_drift_age_s is not None else None),
        }
        for lot in sorted(city.lots.values(), key=lambda lot: lot.object_key)
    ]


def _objects(ctx: PipelineContext, usage: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Catalog facts plus dbt's declared semantics, when a manifest supplied
    them. `dbt` is null for objects dbt does not manage -- the client renders
    absence as absence, not as empty documentation.

    `usage` is measured run appearances (`measured._usage_by_key`), passed in
    rather than imported so this module keeps depending on nothing that
    depends on it. A key missing from that map means the run history says
    nothing about the object: **unknown, never unused.**

    `semantic` carries the OSI declaration when one exists and null otherwise —
    declared, where everything beside it is measured."""
    usage = usage or {}
    return [
        {
            "key": obj.key,
            "schema": obj.schema,
            "name": obj.name,
            "kind": obj.kind,
            "row_count": obj.row_count,
            "dbt": _dbt_block(ctx, obj.key),
            # Measured appearances in recorded runs; null = unknown.
            "usage": usage.get(obj.key),
            # Declared OSI context and keys; null when nothing was declared.
            "semantic": _semantic_block(ctx, obj.key),
            "columns": _columns(ctx, obj.key),
        }
        for obj in sorted(ctx.objects, key=lambda obj: obj.key)
    ]


def _semantic_block(ctx: PipelineContext, key: str) -> dict[str, Any] | None:
    """What an OSI file DECLARES about this object, or null.

    Null and "declared but empty" are different facts and the client renders
    them differently — null is a building nobody documented, an all-empty block
    is a dataset someone named without annotating. So this returns null only
    when no dataset claims the object at all.
    """
    dataset = ctx.ai_context_by_key.get(key)
    if dataset is None:
        return None
    return {
        # The business name the semantic layer uses, which is often not the
        # table's name -- the nameplate over the lobby door.
        "name": dataset.name,
        "primary_key": list(dataset.primary_key),
        "unique_keys": [list(columns) for columns in dataset.unique_keys],
        # ai_context: the legibility layer. "" and [] mean undeclared.
        "instructions": dataset.ai_context.instructions or None,
        "synonyms": list(dataset.ai_context.synonyms),
        "example_queries": list(dataset.ai_context.example_queries),
    }


def _columns(ctx: PipelineContext, key: str) -> list[dict[str, Any]]:
    """The table's schema as architecture material: name and type MEASURED from
    the warehouse, description DECLARED by dbt (null when undocumented), and
    the worst verdict among that column's tests (null = untested or never
    run -- absence stays absence)."""
    context = ctx.dbt_context_by_key.get(key)
    docs = context.column_docs if context else {}
    node_results = ctx.runs.node_results if ctx.runs is not None else {}
    verdicts: dict[str, str] = {}
    for ref in ctx.tests_by_key.get(key, ()):
        if ref.column is None or ref.unique_id not in node_results:
            continue
        status = node_results[ref.unique_id].status.lower()
        word = "fail" if status in ("fail", "error") else "warn" if status == "warn" else "pass"
        current = verdicts.get(ref.column)
        rank = {"fail": 2, "warn": 1, "pass": 0}
        if current is None or rank[word] > rank[current]:
            verdicts[ref.column] = word
    return [
        {
            "name": name,
            "type": data_type,
            "description": docs.get(name) or None,
            "test_status": verdicts.get(name),
        }
        for name, data_type in ctx.columns_by_key.get(key, ())
    ]


def _dbt_block(ctx: PipelineContext, key: str) -> dict[str, Any] | None:
    context = ctx.dbt_context_by_key.get(key)
    refs = ctx.tests_by_key.get(key, ())
    if context is None and not refs:
        return None
    node_results = ctx.runs.node_results if ctx.runs is not None else {}
    tests = [
        {
            "name": ref.name,
            "column": ref.column,
            # dbt's own words (pass/fail/warn/error/skipped); null = declared
            # but never run, which must not render as either verdict.
            "status": (node_results[ref.unique_id].status if ref.unique_id in node_results else None),
        }
        for ref in sorted(refs, key=lambda r: (r.column or "", r.name))
    ]
    return {
        "description": context.description if context else "",
        "materialized": context.materialized if context else "",
        "tags": list(context.tags) if context else [],
        "owner": context.owner if context else None,
        "tests": tests,
    }


def _edges(ctx: PipelineContext, city: CityMap) -> list[dict[str, Any]]:
    """Known edges with their traffic rate folded on.

    Only edges whose *both* endpoints are objects in this catalog are emitted: a
    client cannot draw a road to something that is not on the map, and this is
    the same "known edge" definition `sim.layout` lays out from. The loader
    already guarantees it, so the filter matters for hand-built contexts.

    Folding the rate onto the edge record is what retires `CityMap.edge_rates`'
    `tuple[str, str]` keys -- unrepresentable in JSON -- and keeps the
    `"src->dst"` string convention a private detail of `sim.channels`.
    """
    keys = {obj.key for obj in ctx.objects}
    # Warehouse load per edge (the road-heat overlay): the destination
    # model's measured cadence x mean build cost, in warehouse-seconds/day.
    # Roads carry load because the warehouse does (Stephen's analogy). None
    # without >= 2 successful builds — absence, never a guess.
    load_of: dict[str, float] = {}
    if ctx.runs is not None:
        for key, unique_id in ctx.dbt_nodes_by_key.items():
            load = daily_load_s(ctx.runs.build_history.get(unique_id, ()))
            if load is not None:
                load_of[key] = round(load, 2)
    # Column-grain lineage grouped under its table edge (skybridges). Column
    # edges always ride an existing table edge: the loader unions a table
    # edge in for every traced pair, so nothing is dropped here.
    columns_of: dict[tuple[str, str], list[list[str]]] = {}
    for col_edge in ctx.column_edges:
        columns_of.setdefault((col_edge.src, col_edge.dst), []).append([col_edge.src_col, col_edge.dst_col])
    seen: set[tuple[str, str]] = set()
    records: list[dict[str, Any]] = []
    for edge in ctx.edges:
        pair = (edge.src, edge.dst)
        if edge.src not in keys or edge.dst not in keys or pair in seen:
            continue
        seen.add(pair)
        records.append(
            {
                "src": edge.src,
                "dst": edge.dst,
                "rate": round(city.edge_rates.get(pair, 0.0), RATE_PRECISION),
                # Declared vs inferred, resolved in Python: "manifest" (dbt),
                # "duckdb" (engine dependency catalog), "view_sql" (regex scan).
                "provenance": edge.provenance,
                # Streets ARE the lineage: the exact tile path this edge's
                # street takes, lot to lot. The client's traffic drives it.
                "route": [[x, y] for x, y in city.edge_routes.get(pair, ())],
                # Column-level lineage: [src_col, dst_col] pairs, the
                # skybridges between this pair of buildings.
                "columns": sorted(columns_of.get(pair, [])),
                # Expected warehouse-seconds/day this street carries (its
                # destination's measured cadence x mean build cost); null
                # when the history cannot say.
                "daily_load_s": load_of.get(edge.dst),
            }
        )
    records.sort(key=lambda record: (record["src"], record["dst"]))
    return records


def _joins(ctx: PipelineContext) -> list[dict[str, Any]]:
    """DECLARED joins — a separate array, deliberately not folded onto `edges`.

    The reason is decisive: **a join and a lineage edge are different claims.**
    An edge asserts "data moved here at build time"; a join asserts "these two
    are formally joinable", which is true whether or not anything ever built
    one from the other. The common case proves it — a dimension joined in every
    query but never a build input of the fact — and folding that onto `edges`
    would either invent an edge that implies data movement or leave the join
    with nowhere to live. Clients that draw lineage keep drawing exactly what
    they drew before this key existed.

    `lineage_edge` is how the two stay reconciled: when the same pair also has
    lineage, this names that edge (in ITS own direction, which is usually the
    reverse of the join's — the dimension is built *into* the fact) so a
    renderer marks the existing street instead of laying a parallel road.
    Null when the pair has no lineage: that is the join street that has to be
    paved from dirt.
    """
    keys = {obj.key for obj in ctx.objects}
    lineage = {(e.src, e.dst) for e in ctx.edges if e.src in keys and e.dst in keys}
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str, tuple[tuple[str, str], ...]]] = set()
    for rel in ctx.semantic_relationships:
        # Same rule as `_edges`: a client cannot draw to something off the map.
        if rel.many not in keys or rel.one not in keys:
            continue
        # Two relationships between the same pair on DIFFERENT columns are
        # ordinary (billing vs shipping customer), so the identity is the pair
        # plus its keys -- deduping on the pair alone would drop a real join.
        identity = (rel.many, rel.one, rel.keys)
        if identity in seen:
            continue
        seen.add(identity)
        lineage_edge: list[str] | None = None
        if (rel.many, rel.one) in lineage:
            lineage_edge = [rel.many, rel.one]
        elif (rel.one, rel.many) in lineage:
            lineage_edge = [rel.one, rel.many]
        records.append(
            {
                "name": rel.name,
                # many-to-one is the spec's invariant, so the record names
                # which side is the "one": a pair alone cannot signpost.
                "many": rel.many,
                "one": rel.one,
                "cardinality": "many_to_one",
                # [many-side column, one-side column], in declaration order.
                "keys": [list(pair) for pair in rel.keys],
                "composite": rel.composite,
                # Declared, always. Nothing here is inferred from SQL -- that
                # weaker provenance exists already, as lineage.
                "provenance": "declared",
                "lineage_edge": lineage_edge,
            }
        )
    # Sorted on a key that cannot tie: `seen` made (many, one, keys) unique.
    records.sort(key=lambda record: (record["many"], record["one"], record["keys"]))
    return records


def _replay(ctx: PipelineContext) -> dict[str, Any] | None:
    """The last run as a playable schedule, or null with the refusal folded
    into a note-like reason field. Deterministic: built from durations and
    topology only, so tycoon documents stay byte-stable for a fixed catalog."""
    plan = plan_replay(ctx)
    if not isinstance(plan, ReplayPlan):
        return None
    return {
        "span_ticks": plan.span_ticks,
        "note": plan.note,
        "steps": [{"object_key": s.object_key, "start": s.start, "duration": s.duration} for s in plan.steps],
    }


def _theme(theme: ThemeData) -> dict[str, Any]:
    """Everything a client needs to paint the city, minus the rules it must not
    re-run and the paths it must not see.

    `spritesheet` is a bare filename, resolved relative to `city.json`, so the
    document says nothing about the machine that produced it.
    """
    return {
        "name": theme.name,
        "logo_text": theme.logo_text,
        "labels": {name: theme.labels[name] for name in sorted(theme.labels)},
        "colors": {name: list(theme.colors[name]) for name in sorted(theme.colors)},
        "sprites": {name: list(theme.sprites[name]) for name in sorted(theme.sprites)},
        "spritesheet": theme.spritesheet_path.name,
    }
