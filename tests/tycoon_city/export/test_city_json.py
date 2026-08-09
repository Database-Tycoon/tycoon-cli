"""What crosses the wire, asserted on the emitted bytes rather than on intent.

Two habits here are deliberate reactions to this repo's history of tests that
asserted the right value on the wrong axis:

* Structural claims are checked against a **decoded** grid or a **re-parsed**
  document, not against the dict that was handed to the serialiser. A document
  that serialises wrongly passes every assertion made on the dict.
* Absence is asserted where a decision was to leave something out (`density`,
  `style_rules`, `roads`, `district_of`). A contract test that only checks what
  is present cannot notice presentation state leaking in.
"""

import json
from pathlib import Path

import pytest

from tycoon_city.catalog.models import CatalogObject, Edge, PipelineContext
from tycoon_city.export.build import build_city
from tycoon_city.export.city_json import (
    FORMAT,
    RATE_PRECISION,
    TILE_KINDS,
    VERSION,
    city_document,
    decode_rle,
    dumps,
    encode_rle,
)
from tycoon_city.sim.channels import DEFAULT_BINDINGS, apply_signals
from tycoon_city.sim.generator import generate_city
from tycoon_city.sim.tiles import TileKind
from tycoon_city.theme_data import load_theme_data, theme_dir

REPO = Path(__file__).resolve().parents[2]
DEMO_DB = REPO / "demo.duckdb"
GOLDEN = REPO / "contract" / "fixtures" / "demo.city.json"


@pytest.fixture
def theme():
    return load_theme_data(theme_dir("default"))


def _city_from(ctx: PipelineContext, theme):
    city = generate_city(ctx, theme.style_rules)
    apply_signals(city, ctx, DEFAULT_BINDINGS)
    return city


def _document_for(ctx: PipelineContext, theme) -> dict:
    """A document round-tripped through the serialiser, which is what a client
    actually receives. Every test below reads this, never `city_document`'s dict."""
    return json.loads(dumps(city_document(ctx, _city_from(ctx, theme), theme)))


# ---------------------------------------------------------------------------
# Adversarial catalog set. Every structural test runs over all of these, so a
# rule that only holds on the demo catalog cannot pass.
# ---------------------------------------------------------------------------


def _ctx(objects, edges=()):
    return PipelineContext(database_name="fx", objects=tuple(objects), edges=tuple(edges))


def _obj(schema, name, rows=0, kind="table"):
    return CatalogObject(schema=schema, name=name, kind=kind, row_count=rows)


CATALOGS: dict[str, PipelineContext] = {
    "empty": _ctx([]),
    "single": _ctx([_obj("main", "only", 10)]),
    "cycle": _ctx(
        [_obj("a", "x", 5), _obj("a", "y", 6), _obj("b", "z", 7)],
        [Edge("a.x", "a.y"), Edge("a.y", "a.x"), Edge("a.y", "b.z")],
    ),
    "disconnected": _ctx(
        [_obj("a", "x", 1), _obj("b", "y", 2), _obj("c", "orphan", 3)],
        [Edge("a.x", "b.y")],
    ),
    # A 2x2 building (the top decile of eleven row counts) fed by one edge:
    # the only shape that emits a plaza pad bigger than one tile, and therefore
    # the only shape that can pin `w`/`h` on the wire. Without it, swapping the
    # two fields in the emitter passes every test in this file (measured).
    # The filler tables sit in their own schema so this catalog says one thing
    # only -- plaza geometry. `mixed_schema` below is where a schema holding
    # both connected lots and suburb orphans gets exercised.
    "big_plaza": _ctx(
        [_obj("filler", f"t{i}", 10 + i) for i in range(9)] + [_obj("m", "hub", 90_000), _obj("s", "feeder", 5)],
        [Edge("s.feeder", "m.hub")],
    ),
    # `raw` owns a lot in the working city AND a stray in the suburb: the one
    # arrangement the district rule is actually about, and the one no catalog
    # here had. `scratch` is all-orphan, the other half of the rule. Until this
    # landed (2026-08-06) the district assertion below said every lot sits in
    # its schema's plate -- the opposite of what the format documents -- and
    # passed, because no fixture ever put the two kinds in one schema.
    "mixed_schema": _ctx(
        [_obj("raw", "a", 3), _obj("raw", "stray", 4), _obj("m", "c", 5), _obj("scratch", "x", 6)],
        [Edge("raw.a", "m.c")],
    ),
    # The loader's cap, so the widest grid the format has to carry. 500
    # one-object schemas is the case plan_layout cannot compact.
    "at_cap_wide": _ctx([_obj(f"s{i:03d}", "t", i) for i in range(500)]),
    "at_cap_chain": _ctx(
        [_obj(f"s{i // 10:02d}", f"t{i}", i) for i in range(500)],
        [Edge(f"s{i // 10:02d}.t{i}", f"s{(i + 1) // 10:02d}.t{i + 1}") for i in range(499)],
    ),
}
CATALOG_IDS = sorted(CATALOGS)


# ---------------------------------------------------------------------------
# The run-length encoding
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_rle_round_trips_to_the_original_grid(name, theme):
    """The decoded grid must equal `city.tiles` cell for cell.

    Asserting run counts or lengths instead would pass on an encoder that
    dropped or duplicated a cell in the middle of the grid.
    """
    city = _city_from(CATALOGS[name], theme)
    runs = encode_rle(city.tiles)

    assert decode_rle(runs, city.width, city.height) == city.tiles


def test_rle_runs_cross_row_boundaries(theme):
    """A uniform grid encodes to one run, not one run per row.

    This is the property that makes the encoding worth having, and it is
    invisible in a round-trip test: a per-row encoder round-trips perfectly.
    """
    grid = [[TileKind.GRASS] * 8 for _ in range(8)]

    assert encode_rle(grid) == [0, 64]


def test_rle_ids_are_positions_in_the_shipped_legend():
    """Every kind's id must index `tile_kinds` back to its own name.

    The legend is the client's only way to resolve an id, so an encoder using
    `TileKind.value` (which `auto()` makes 1-based) would put every tile one
    slot off while still round-tripping through `decode_rle`.
    """
    for kind in TileKind:
        [kind_id, run] = encode_rle([[kind]])
        assert run == 1
        assert TILE_KINDS[kind_id] == kind.name.lower()


@pytest.mark.parametrize(
    ("runs", "width", "height"),
    [
        ([0, 4, 1], 2, 2),  # odd number of values: a truncated pair
        ([0, 3], 2, 2),  # too few cells
        ([0, 5], 2, 2),  # too many cells
        ([99, 4], 2, 2),  # kind id not in the legend
        ([0, 0, 1, 4], 2, 2),  # zero-length run
    ],
)
def test_decode_rle_rejects_malformed_runs(runs, width, height):
    with pytest.raises(ValueError):
        decode_rle(runs, width, height)


# ---------------------------------------------------------------------------
# Byte stability and the golden
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_two_emits_are_byte_identical(name, theme):
    ctx = CATALOGS[name]
    first = dumps(city_document(ctx, _city_from(ctx, theme), theme))
    second = dumps(city_document(ctx, _city_from(ctx, theme), theme))

    assert first == second


def test_golden_matches_a_fresh_emit(theme):
    ctx, city = build_city(DEMO_DB, theme.style_rules)

    assert dumps(city_document(ctx, city, theme)) == GOLDEN.read_text(encoding="utf-8"), (
        "The emitted contract no longer matches contract/fixtures/demo.city.json. "
        "If the change is deliberate, run "
        "`uv run python scripts/update_contract_golden.py` and review the diff."
    )


def test_serialised_rle_survives_the_one_line_substitution(theme):
    """`dumps` splices the run array in as one line, so re-parsing must recover
    exactly the numbers `encode_rle` produced -- for a big grid, not just a small
    one, since the substitution is a text operation."""
    ctx = CATALOGS["at_cap_wide"]
    city = _city_from(ctx, theme)
    document = city_document(ctx, city, theme)

    parsed = json.loads(dumps(document))

    assert parsed["grid"]["tiles_rle"] == encode_rle(city.tiles)
    assert decode_rle(parsed["grid"]["tiles_rle"], city.width, city.height) == city.tiles


def test_tiles_rle_stays_on_one_line(theme):
    """The whole point of the substitution. Measured: the widest catalog costs
    1.1 MB collapsed against 2.8 MB at one number per line."""
    ctx = CATALOGS["at_cap_wide"]
    text = dumps(city_document(ctx, _city_from(ctx, theme), theme))

    rle_lines = [line for line in text.splitlines() if '"tiles_rle"' in line]
    assert len(rle_lines) == 1
    assert rle_lines[0].rstrip().endswith("]")


def test_dumps_ends_with_exactly_one_newline(theme):
    """A trailing newline so the golden is a well-formed text file, and exactly
    one so `git diff` never reports a whitespace-only change."""
    text = dumps(city_document(CATALOGS["single"], _city_from(CATALOGS["single"], theme), theme))

    assert text.endswith("}\n")
    assert not text.endswith("\n\n")


# ---------------------------------------------------------------------------
# Document shape
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_document_declares_its_format_and_version(name, theme):
    document = _document_for(CATALOGS[name], theme)

    assert document["format"] == FORMAT
    assert document["version"] == VERSION


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_grid_matches_the_declared_dimensions(name, theme):
    ctx = CATALOGS[name]
    city = _city_from(ctx, theme)
    grid = _document_for(ctx, theme)["grid"]

    assert (grid["width"], grid["height"]) == (city.width, city.height)
    assert grid["tile_kinds"] == list(TILE_KINDS)
    # Decodes against the *declared* dimensions, so a document whose width and
    # runs disagree fails here rather than rendering a sheared map.
    assert decode_rle(grid["tiles_rle"], grid["width"], grid["height"]) == city.tiles


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_every_lot_names_an_emitted_object_and_sits_on_a_lot_tile(name, theme):
    ctx = CATALOGS[name]
    city = _city_from(ctx, theme)
    document = _document_for(ctx, theme)

    tiles = decode_rle(document["grid"]["tiles_rle"], document["grid"]["width"], document["grid"]["height"])
    keys = {obj["key"] for obj in document["objects"]}

    assert len(document["lots"]) == len(city.lots)
    for lot in document["lots"]:
        assert lot["object_key"] in keys
        assert tiles[lot["y"]][lot["x"]] is TileKind.LOT


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_plant_sits_on_the_plant_tile(name, theme):
    ctx = CATALOGS[name]
    document = _document_for(ctx, theme)

    tiles = decode_rle(document["grid"]["tiles_rle"], document["grid"]["width"], document["grid"]["height"])
    plant = document["plant"]

    assert tiles[plant["y"]][plant["x"]] is TileKind.PLANT


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_focus_is_the_box_around_every_lot_plant_and_civic_building(name, theme):
    document = _document_for(CATALOGS[name], theme)
    focus = document["focus"]

    # A lot's whole ground plan is in frame (2x2 big tables, 2026-08-05).
    xs = [x for lot in document["lots"] for x in (lot["x"], lot["x"] + lot["w"] - 1)]
    ys = [y for lot in document["lots"] for y in (lot["y"], lot["y"] + lot["h"] - 1)]
    xs.append(document["plant"]["x"])
    ys.append(document["plant"]["y"])
    # Civic buildings joined the frame (2026-08-05): the opening camera must
    # never crop the library or the firehouse.
    for civic in (document["library"], document["firehouse"]):
        if civic is not None:
            xs.append(civic["x"])
            ys.append(civic["y"])

    assert (focus["min_x"], focus["max_x"]) == (min(xs), max(xs))
    assert (focus["min_y"], focus["max_y"]) == (min(ys), max(ys))


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_lots_carry_target_density_and_never_the_tween(name, theme):
    """`density` is presentation: the client animates 0 -> target itself.

    Emitting it would make the bytes depend on how many engine ticks happened to
    have run before the export, which is exactly what makes a golden impossible.
    """
    for lot in _document_for(CATALOGS[name], theme)["lots"]:
        assert "density" not in lot
        assert 1 <= lot["target_density"] <= 8


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_zone_styles_are_resolved_names_and_the_rules_stay_home(name, theme):
    document = _document_for(CATALOGS[name], theme)
    allowed = {"industrial", "commercial", "residential"}

    for lot in document["lots"]:
        assert lot["zone_style"] in allowed
    # The regexes must not cross the wire; the client never re-matches them.
    assert "style_rules" not in document["theme"]


def _connected_keys(document: dict) -> set[str]:
    """Keys taking part in at least one known edge — the planner's own
    definition of "connected", read off the wire rather than re-derived from
    the context, with self-edges dropped exactly as `plan_dag_layout` drops
    them. Everything else is a suburb orphan."""
    return {k for e in document["edges"] if e["src"] != e["dst"] for k in (e["src"], e["dst"])}


def _inside(box: dict, lot: dict) -> bool:
    return box["x"] <= lot["x"] < box["x"] + box["w"] and box["y"] <= lot["y"] < box["y"] + box["h"]


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_districts_bound_connected_lots_and_exclude_a_mixed_schemas_orphans(name, theme):
    """A plate is the schema's WORKING NEIGHBOURHOOD, not a bounding box over
    everything the schema owns.

    `docs/city-json-v1.md` and
    `tests/sim/test_layout_plan.py::test_districts_bound_their_connected_lots_and_exclude_suburb_orphans`
    both say the same thing: a schema that has connected lots leaves its
    suburb orphans OUT of its plate, or one stray table stretches the rect
    across the map and washes every band into a blur. Only an all-orphan
    schema wraps its orphans.

    Until 2026-08-06 this asserted the opposite — every lot inside its
    schema's plate — and passed, because no fixture mixed the two kinds in one
    schema. `mixed_schema` is that fixture; see the precondition test below,
    which is what stops it degrading back into an assertion that cannot fail.
    """
    ctx = CATALOGS[name]
    document = _document_for(ctx, theme)

    boxes = {d["schema"]: d for d in document["districts"]}
    assert set(boxes) == {obj.schema for obj in ctx.objects}

    connected = _connected_keys(document)
    schema_of = {lot["object_key"]: lot["object_key"].rsplit(".", 1)[0] for lot in document["lots"]}
    members: dict[str, list[str]] = {}
    for key, schema in schema_of.items():
        members.setdefault(schema, []).append(key)
    # A schema is "mixed" when it owns at least one of each kind; only those
    # schemas exclude anything.
    mixed = {
        schema
        for schema, keys in members.items()
        if any(k in connected for k in keys) and any(k not in connected for k in keys)
    }

    for lot in document["lots"]:
        key = lot["object_key"]
        box = boxes[schema_of[key]]
        if key in connected:
            assert _inside(box, lot), f"{key} is connected and must sit in its plate: {box}"
        elif schema_of[key] in mixed:
            # The exclusion, asserted rather than merely exempted: an orphan
            # that crept back inside means the plate stretched to the suburb.
            assert not _inside(box, lot), f"{key} is a suburb orphan inside a mixed plate: {box}"
        else:
            assert _inside(box, lot), f"{key}'s schema is all-orphan and keeps its plate: {box}"


def test_the_mixed_schema_fixture_actually_mixes(theme):
    """The precondition the test above needs and cannot check per-catalog.

    `mixed_schema` exists for exactly one reason: to put a connected lot and a
    suburb orphan in ONE schema, so the exclusion branch runs at all. Assert
    the arrangement here, on the emitted document, so an edit that reconnects
    `raw.stray` or moves it to its own schema fails loudly instead of turning
    the exclusion branch off in silence.
    """
    document = _document_for(CATALOGS["mixed_schema"], theme)
    connected = _connected_keys(document)

    assert connected == {"raw.a", "m.c"}, connected
    keys = {lot["object_key"] for lot in document["lots"]}
    assert keys == {"raw.a", "raw.stray", "m.c", "scratch.x"}, keys

    raw = [k for k in keys if k.startswith("raw.")]
    assert {k for k in raw if k in connected} and {k for k in raw if k not in connected}, (
        "`raw` must own both a connected lot and a suburb orphan"
    )
    scratch = [k for k in keys if k.startswith("scratch.")]
    assert all(k not in connected for k in scratch), "`scratch` must stay all-orphan"

    # And the exclusion is real on this document: raw's plate stops north of
    # the suburb row its stray sits on.
    boxes = {d["schema"]: d for d in document["districts"]}
    lots = {lot["object_key"]: lot for lot in document["lots"]}
    assert _inside(boxes["raw"], lots["raw.a"])
    assert lots["raw.stray"]["y"] >= boxes["raw"]["y"] + boxes["raw"]["h"]
    assert _inside(boxes["scratch"], lots["scratch.x"])


def test_omitted_keys_stay_omitted(theme):
    """`roads` and `district_of` were deliberately left out -- roads are
    derivable from the tile grid and district membership from the district
    rects. Re-adding either silently doubles the format's size."""
    document = _document_for(CATALOGS["disconnected"], theme)

    assert "roads" not in document
    assert "district_of" not in document


# ---------------------------------------------------------------------------
# Reserved seams (2026-08-06) — the four 1.0 workstreams' keys, cut in once
# ---------------------------------------------------------------------------

# Every key a workstream landed into during the 2026-08-06 seam pass. All five
# now carry content when a catalog has something to say; what survives from the
# reserved era -- and is the whole point of having cut them in at once -- is
# that each is emitted UNCONDITIONALLY. The empty shapes are pinned by the two
# tests below, one per provenance: measured, and declared.
UNCONDITIONAL_TOP_LEVEL = ("budget", "weather", "joins")
UNCONDITIONAL_PER_OBJECT = ("usage", "semantic")

# The measured three, and what they must say on a catalog with no run history
# and no freshness verdicts -- which is every hand-built catalog here.
MEASURED_TOP_LEVEL = ("budget", "weather")


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_the_seam_keys_are_emitted_unconditionally_on_every_catalog(name, theme):
    """The point of a reserved key is that it is ALWAYS there.

    A workstream lands content into a key the client already accepts; if the
    emitter could omit one on some catalog, a client would still need the
    absent case and the seam would have bought nothing. So this runs over
    every catalog, not just the demo one the golden pins -- the golden alone
    would let an emitter drop `joins` on, say, a catalog with no lineage.

    The empty values are asserted too: `[]` and null are the only legal values
    at version 1 for the seams still reserved, and a builder that starts
    guessing a shape has made a contract change that must go through the doc
    and the golden first.
    """
    document = _document_for(CATALOGS[name], theme)

    for key in UNCONDITIONAL_TOP_LEVEL:
        assert key in document, f"{key!r} must be emitted on every document"

    for record in document["objects"]:
        for key in UNCONDITIONAL_PER_OBJECT:
            assert key in record, f"{key!r} missing from objects[{record['key']!r}]"


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_the_measured_blocks_are_emitted_on_every_catalog_and_stay_honest(name, theme):
    """`budget`, `weather` and `objects[].usage` are filled now, but the key is
    still unconditional -- a client must never meet a document that simply
    lacks one.

    Every catalog here is hand-built: no run history, no dbt manifest, no
    `dbt source freshness`. So this pins the ABSENCE shapes, which are the ones
    that lie if they are got wrong:

    * `budget` is null, not a $0 bill. Local DuckDB really does cost nothing,
      and a zero emitted here would be indistinguishable from that fact.
    * `weather` carries NO cells. All-clear would be clear-because-unknown
      rendered as clear-because-fine, which is the exact confusion the
      freshness block exists to avoid.
    * `usage` is null on every object -- unknown, never "unused".
    """
    document = _document_for(CATALOGS[name], theme)

    for key in MEASURED_TOP_LEVEL:
        assert key in document, f"{key!r} must be emitted on every document"

    assert document["budget"] is None, document["budget"]

    weather = document["weather"]
    assert weather["cells"] == [], weather
    assert "unknown" in weather["note"], weather["note"]

    for record in document["objects"]:
        assert "usage" in record, f"usage missing from objects[{record['key']!r}]"
        assert record["usage"] is None, record["usage"]


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_the_semantic_keys_stay_empty_without_a_semantic_model(name, theme):
    """The OSI keys are populated now, but only by a DECLARATION.

    None of these catalogs has a semantic model, so every one of them must
    still emit `[]` and null -- an emitter that started deriving joins from
    lineage would light this up, and that is exactly the provenance mistake
    the OSI workstream must not make.
    """
    document = _document_for(CATALOGS[name], theme)

    assert document["joins"] == []
    for record in document["objects"]:
        assert "semantic" in record, f"objects[{record['key']!r}] must always carry `semantic`"
        assert record["semantic"] is None


# ---------------------------------------------------------------------------
# Street features (streets v4) — the frozen seam the renderer builds against
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_street_features_carry_the_frozen_record_shape(name, theme):
    """The renderer reads these keys by name, so the record shape IS the
    contract. Asserted on the re-parsed document: an emitter that dropped a key
    would still satisfy any assertion made on the plan's dataclasses."""
    document = _document_for(CATALOGS[name], theme)
    features = document["street_features"]
    assert isinstance(features, list)
    for feature in features:
        assert set(feature) == {"kind", "x", "y", "facing", "w", "h"}, feature
        assert feature["kind"] in {"apron", "dock", "plaza"}, feature
        assert feature["facing"] in {"n", "s", "e", "w", None}, feature
        assert isinstance(feature["x"], int) and isinstance(feature["y"], int)
        assert feature["w"] >= 1 and feature["h"] >= 1
        # A pad wider than one tile is a plaza, and only a plaza — the
        # invariant the renderer keys its forecourt geometry off.
        if feature["w"] > 1 or feature["h"] > 1:
            assert feature["kind"] == "plaza", feature


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_street_features_are_sorted_by_kind_then_position(name, theme):
    document = _document_for(CATALOGS[name], theme)
    keys = [(f["kind"], f["x"], f["y"]) for f in document["street_features"]]
    assert keys == sorted(keys), keys


def test_street_features_dress_the_ends_of_a_real_street(theme):
    """The `cycle` catalog has lineage, so it has streets, so it has endings —
    each sitting on a ROAD tile of the DECODED grid and facing a building. The
    lineage-free catalog emits none, which is what stops this from being a
    shape-only test a stub emitter could satisfy."""
    document = _document_for(CATALOGS["cycle"], theme)
    grid = decode_rle(document["grid"]["tiles_rle"], document["grid"]["width"], document["grid"]["height"])
    features = document["street_features"]
    assert features, "a catalog with lineage must dress its road endings"
    steps = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}
    for f in features:
        assert grid[f["y"]][f["x"]] is TileKind.ROAD, f"{f} is not on pavement"
        dx, dy = steps[f["facing"]]
        faced = grid[f["y"] + dy][f["x"] + dx]
        # A lot, or the civic strip's grass (the library and firehouse are
        # buildings the tile grid does not paint).
        assert faced in (TileKind.LOT, TileKind.GRASS), f"{f} faces {faced.name}"

    assert _document_for(CATALOGS["at_cap_wide"], theme)["street_features"] == [], (
        "no lineage, no street, nothing to dress"
    )


def test_a_big_lots_plaza_ships_its_frontage_geometry(theme):
    """`w`/`h` are how the renderer sizes a forecourt, so they are pinned on the
    emitted bytes for the one shape that produces a pad bigger than a tile: a
    2x2 building's west frontage, two tiles TALL (h=2, w=1 — not the other way
    round), both of them paved in the decoded grid."""
    ctx = CATALOGS["big_plaza"]
    document = _document_for(ctx, theme)
    grid = decode_rle(document["grid"]["tiles_rle"], document["grid"]["width"], document["grid"]["height"])
    hub = next(lot for lot in document["lots"] if lot["object_key"] == "m.hub")
    assert (hub["w"], hub["h"]) == (2, 2), hub

    pads = [f for f in document["street_features"] if f["w"] > 1 or f["h"] > 1]
    assert len(pads) == 1, document["street_features"]
    pad = pads[0]
    assert (pad["kind"], pad["w"], pad["h"], pad["facing"]) == ("plaza", 1, 2, "e"), pad
    assert (pad["x"], pad["y"]) == (hub["x"] - 1, hub["y"]), pad
    for dy in range(pad["h"]):
        assert grid[pad["y"] + dy][pad["x"]] is TileKind.ROAD, f"forecourt row {dy} unpaved"


# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------


def test_edges_carry_their_rate_and_are_sorted(theme):
    ctx = CATALOGS["disconnected"]
    city = _city_from(ctx, theme)
    document = _document_for(ctx, theme)

    pairs = [(edge["src"], edge["dst"]) for edge in document["edges"]]
    assert pairs == [("a.x", "b.y")]
    assert pairs == sorted(pairs)
    for edge in document["edges"]:
        expected = city.edge_rates[(edge["src"], edge["dst"])]
        assert edge["rate"] == pytest.approx(expected, abs=10**-RATE_PRECISION)


def test_edges_pointing_outside_the_catalog_are_dropped(theme):
    """A client cannot draw a road to something that is not on the map.

    The loader already guarantees this, so the filter only shows up on a
    hand-built context -- which is exactly what Phase E's manifest lineage will
    hand it.
    """
    ctx = _ctx(
        [_obj("a", "x", 1), _obj("b", "y", 2)],
        [Edge("a.x", "b.y"), Edge("a.x", "gone.z"), Edge("gone.z", "b.y")],
    )

    document = _document_for(ctx, theme)

    assert [(e["src"], e["dst"]) for e in document["edges"]] == [("a.x", "b.y")]


def test_duplicate_edges_are_emitted_once(theme):
    ctx = _ctx([_obj("a", "x", 1), _obj("b", "y", 2)], [Edge("a.x", "b.y"), Edge("a.x", "b.y")])

    assert len(_document_for(ctx, theme)["edges"]) == 1


def test_has_known_edges_is_false_only_when_no_edge_has_both_ends_here(theme):
    tables_only = _ctx([_obj("a", "x", 1), _obj("b", "y", 2)])
    dangling = _ctx([_obj("a", "x", 1)], [Edge("a.x", "gone.z")])
    real = CATALOGS["disconnected"]

    assert _document_for(tables_only, theme)["database"]["has_known_edges"] is False
    assert _document_for(dangling, theme)["database"]["has_known_edges"] is False
    assert _document_for(real, theme)["database"]["has_known_edges"] is True


# ---------------------------------------------------------------------------
# Database block and theme
# ---------------------------------------------------------------------------


def test_database_block_reports_the_catalog_totals(theme):
    ctx = CATALOGS["cycle"]

    block = _document_for(ctx, theme)["database"]

    assert block["name"] == "fx"
    assert block["object_count"] == 3
    assert block["total_rows"] == 18


def test_theme_block_is_self_contained(theme):
    block = _document_for(CATALOGS["single"], theme)["theme"]

    assert block["name"] == theme.name
    assert block["logo_text"] == theme.logo_text
    # A bare filename, resolved next to city.json: the document must say nothing
    # about the machine that produced it.
    assert block["spritesheet"] == "spritesheet.png"
    assert "/" not in block["spritesheet"]

    assert set(block["sprites"]) == set(theme.sprites)
    assert all(len(rect) == 4 for rect in block["sprites"].values())
    assert set(block["colors"]) == set(theme.colors)
    assert all(len(rgb) == 3 for rgb in block["colors"].values())


def test_theme_block_carries_a_sprite_for_every_tile_kind_the_grid_uses(theme):
    """A kind in the legend with no sprite renders as a hole in the client.

    WATER is exempt: it is in the enum but the generator never emits it, and the
    check is against what the *grid* actually contains.
    """
    ctx, city = build_city(DEMO_DB, theme.style_rules)
    document = json.loads(dumps(city_document(ctx, city, theme)))
    sprites = document["theme"]["sprites"]

    used = {TILE_KINDS[document["grid"]["tiles_rle"][i]] for i in range(0, len(document["grid"]["tiles_rle"]), 2)}
    for name in used:
        if name == "lot":
            assert any(key.startswith("lot_") for key in sprites)
        elif name == "grass":
            assert "grass" in sprites and "grass_alt" in sprites
        else:
            assert name in sprites, f"no sprite for tile kind {name!r}"


@pytest.mark.parametrize("name", CATALOG_IDS)
def test_lots_carry_temporal_fields_null_when_unknown(name, theme):
    """Phase F: the three temporal keys are always present; on catalogs with no
    run history every value is null -- unknown, never zero or stale."""
    for lot in _document_for(CATALOGS[name], theme)["lots"]:
        assert lot["last_build_age_s"] is None
        assert lot["build_status"] is None
        assert lot["test_status"] is None


def test_edges_carry_provenance(theme):
    for edge in _document_for(CATALOGS["disconnected"], theme)["edges"]:
        assert edge["provenance"] in {"manifest", "duckdb", "view_sql"}


def test_edges_carry_daily_load_from_build_history(theme, tmp_path):
    """The road-load overlay's number: dst cadence x mean cost, on the edge;
    null (not 0, not guessed) when history has fewer than two builds."""
    from datetime import datetime, timedelta

    from tests.fixtures.tycoon_factory import RunSpec, make_tycoon_project
    from tycoon_city.catalog.loader import load_context

    t0 = datetime(2026, 8, 1, 2, 0, 0)
    runs = tuple(
        RunSpec(
            f"r{i}",
            "run",
            t0 + timedelta(days=i),
            nodes=(("model.fx_dbt.stg_orders", "success", 6.0),),
        )
        for i in range(4)
    )
    ctx = load_context(make_tycoon_project(tmp_path / "fx", runs=runs))
    document = _document_for(ctx, theme)

    by_pair = {(e["src"], e["dst"]): e for e in document["edges"]}
    into_stg = by_pair[("raw.orders", "staging.stg_orders")]
    assert into_stg["daily_load_s"] == 6.0  # 3 builds / 3 days x 6s mean
    # fct_revenue was never built in these runs: absence stays null.
    assert by_pair[("staging.stg_orders", "marts.fct_revenue")]["daily_load_s"] is None
