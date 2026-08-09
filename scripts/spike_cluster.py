"""Spike: does clustering by SCHEMA beat the depth column, and does it survive S8?

Stephen, 2026-08-07: *"The buildings cant be lined up linearly like that. It
just doesn't look right. Find ways to randomly cluster them so most of the
buildings have a fairly similar median radius from each other"* — and then, once
road paint went on every tile and the dogfood city turned out to be a paved
field, *"You cant have two consecutive intersection tiles."*

**Not wired into anything.** `plan_dag_layout` is still the only planner the app
and the contract reach. This is the look-first instrument, per the repo law that
no geometry rule earns a test before its PNG is accepted.

What it holds constant matters more than what it varies. Panels 2-5 all use the
**same S8-clean v5 lattice**, so the only thing changing is how buildings sit on
the land. That isolates the variable Stephen is objecting to; if roads changed
too, no panel would tell us anything about clustering.

    1  v4              the shipping planner, for the baseline
    2  v5-depth        v5 as it stands: one precinct per (depth, schema)
    3  v5-schema       precincts merged per SCHEMA, depth only ORDERS them
                       (the layout Stephen chose from the mockups)
    4  v5-schema+jit   panel 3, lots jittered inside their own block
    5  v5-schema+noise panel 3, lots re-sampled blue-noise over the precinct,
                       ignoring the block grid entirely
    6  v5-schema+stag  panel 3 with each neighbourhood phase-shifted

## What the sheet found (dogfood, cell 2)

**v5 already answers the roads and makes the LINEARITY worse.** road:lot falls
17.35 -> 1.15 and S8 goes 984 violations / 207-tile clump -> 0 / 1, but `linear`
RISES from 0.56 to 0.86-0.89: a regular block grid is more lined-up than v4's
stripes were, not less.

**Neither naive de-gridding survives contact.** Jitter puts 16 lots on top of
each other and 17 in the carriageway; blue noise, 11 and 33 of 42. They do cut
`linear` (0.44, 0.20) — by destroying the city.

**Staggering whole neighbourhoods does nothing** (0.87): the collinearity is
INSIDE a precinct, not between them.

So the tension is located precisely, and it is a documented invariant:
`Precinct` promises *"every block of a precinct is the same shape; the variation
is between precincts, which is what keeps the district reading uniform"*. That
promise is the source of the rows. Breaking the linearity means varying block
shape WITHIN a precinct while every lot keeps its frontage by construction —
which is a change to `town_blocks.py`, and that file must be SPLIT first (489
lines against the 500-line law).

## Reading the metrics

`nn_med` is the median near-neighbour distance and `nn_iqr` its spread —
Stephen's "fairly similar median radius from each other", as a number. But
`nn_iqr` alone is a TRAP: a perfect lattice scores 0.0, so that criterion is
maximised by exactly the grid he rejected. `linear` exists to say the other half.

`no_front`/`overlap`/`on_road` are the defect trio, and the first version of this
sheet had only the first of them — it reported panels 4 and 5 as clean while they
were stacking buildings on each other, and the only trace was a `lot` tile count
that quietly fell from 214 to 199. MAGENTA marks the lots, the convention
`spike_zoning.py` and `spike_road_defects.py` already use.

`s8_viol` and `s8_clump` are property S8 (`docs/road-grammar.md`,
`sim/road_junctions.py`). They stay 0/1 across panels 2-6 by construction and
are printed anyway, because a silent invariant is one nobody notices breaking.

Deterministic everywhere: jitter and noise offsets are BLAKE2b of the object
key, never an unseeded RNG, because `city.json` is byte-stable by law and a
layout that moved between exports could never back a golden.

Usage (Pillow is not a runtime dependency; bring it in for the spike):

    uv run --with pillow python scripts/spike_cluster.py
    uv run --with pillow python scripts/spike_cluster.py --src demo.duckdb
    uv run --with pillow python scripts/spike_cluster.py --cell 1 --gap 0
"""

from __future__ import annotations

import argparse
import hashlib
import os
import statistics
from dataclasses import dataclass, replace
from fractions import Fraction
from math import isqrt

from PIL import Image, ImageDraw

from tycoon_city.catalog.loader import load_context
from tycoon_city.catalog.models import PipelineContext
from tycoon_city.sim import layout as _layout  # noqa: F401  (fixes the import cycle)
from tycoon_city.sim.layout import compute_depths
from tycoon_city.sim.road_junctions import check_junctions
from tycoon_city.sim.town_blocks import (
    Precinct,
    TileMap,
    plan_lattice,
    plan_precincts,
    resolve_coordinates,
)
from tycoon_city.sim.town_frontage import lot_rect, segment_cover
from tycoon_city.sim.town_plan import plan_dag_layout
from tycoon_city.sim.town_texture import fit_blocks, texture_for
from tycoon_city.sim.town_zoning import block_demand, plan_slots, solid_blocks

Tile = tuple[int, int]
Rect = tuple[int, int, int, int]


@dataclass
class Panel:
    """One candidate layout, reduced to what both the metrics and the paint need."""

    label: str
    note: str
    width: int
    height: int
    road: set[Tile]
    lots: dict[str, Rect]  # key -> (x, y, w, h) in tiles
    districts: list[tuple[str, Rect]]  # (schema, rect) for the ground tint


# --- determinism -----------------------------------------------------------


def _hash_unit(key: str, salt: str) -> float:
    """A stable float in [0, 1) from an object key. BLAKE2b, not `hash()`, whose
    string seed changes per process — that alone would make the layout
    unreproducible and `city.json` unable to back a golden."""
    digest = hashlib.blake2b(f"{salt}\x00{key}".encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big") / float(1 << 64)


# --- panel 1: the v4 baseline ---------------------------------------------


def panel_v4(ctx: PipelineContext) -> Panel:
    plan = plan_dag_layout(ctx)
    lots: dict[str, Rect] = {}
    for key, (x, y) in plan.positions.items():
        n = 2 if key in plan.big_lots else 1
        lots[key] = (x, y, n, n)
    lot_tiles = {(x + dx, y + dy) for (x, y, w, h) in lots.values() for dx in range(w) for dy in range(h)}
    road: set[Tile] = set()
    for path in plan.routes.values():
        road.update(path)
    road.update(plan.lane_tiles)
    road.update(plan.access_road)
    for f in plan.street_features:
        road.update((f.x + dx, f.y + dy) for dx in range(f.w) for dy in range(f.h))
    districts = [(d.schema, (d.x, d.y, d.w, d.h)) for d in plan.districts]
    return Panel(
        label="1  v4 (shipping)",
        note="x = lineage depth; the stripes",
        width=plan.width,
        height=plan.height,
        road=road - lot_tiles,
        lots=lots,
        districts=districts,
    )


# --- panels 2-5: the v5 lattice, four ways of settling it ------------------


def _schema_precincts(ctx: PipelineContext, gap: int, stagger: bool = False) -> tuple[Precinct, ...]:
    """One precinct per SCHEMA, placed west->east by the schema's mean depth.

    Stephen's pick from the mockups: districts lead, and depth only orders the
    neighbourhoods rather than the buildings. A schema spanning three depths
    becomes ONE blob, which he accepted knowing some streets then run westward.

    Deliberately a local reimplementation rather than a parameter on
    `plan_precincts`: that lives in `town_blocks.py`, which sits at 489 lines
    against the 500-line law and must be SPLIT at its next change, not grown by
    a spike that may not survive review.
    """
    keys = sorted(obj.key for obj in ctx.objects)
    if not keys:
        return ()
    schema_of = {obj.key: obj.schema for obj in ctx.objects}
    depths = compute_depths(ctx)
    max_depth = max(depths[k] for k in keys)
    size_band = block_demand(ctx)

    bands: dict[str, list[str]] = {}
    for key in keys:
        bands.setdefault(schema_of[key], []).append(key)

    def mean_depth(members: list[str]) -> Fraction:
        return Fraction(sum(depths[k] for k in members), len(members))

    sized: list[Precinct] = []
    for schema in sorted(bands, key=lambda s: (mean_depth(bands[s]), s)):
        members = tuple(sorted(bands[schema]))
        # Texture from the schema's own centre of mass: a staging blob reads
        # industrial, a mart blob downtown, exactly as depth textures did.
        texture = texture_for(int(mean_depth(list(members))), max_depth)
        shape, blocks_x, blocks_y, capacity = fit_blocks(texture, lambda s, m=members, t=texture: size_band(m, t, s))
        sized.append(
            Precinct(
                pid=schema,
                schema=schema,
                depth=int(mean_depth(list(members))),
                band=0,
                texture=texture,
                members=members,
                capacity=capacity,
                block_w=shape[0],
                block_h=shape[1],
                blocks_x=blocks_x,
                blocks_y=blocks_y,
                cell_x=0,
                cell_y=0,
            )
        )

    # Shelf-pack into near-square, wrapping at isqrt of the total land, with an
    # optional empty-cell GAP between neighbourhoods: Stephen chose ~2x the
    # inside spacing so one dominant near-neighbour mode survives while a
    # district still reads without leaning on its label chip.
    target = max(1, isqrt(sum(p.cells_w * p.cells_h for p in sized)))
    placed: list[Precinct] = []
    cx = cy = 0
    column_w = 0
    for p in sized:
        if cy and cy + p.cells_h > target:
            cx += column_w + gap
            cy = 0
            column_w = 0
        # STAGGER (panel 6): give each neighbourhood its own vertical phase, a
        # hashed 0-2 cells. Frontage survives untouched because the block grid
        # INSIDE a precinct is not disturbed — only the precinct's offset moves —
        # yet city-wide row alignment breaks, which is the collinearity Stephen
        # is objecting to. Added to the cursor, never subtracted, so precincts
        # can never overlap. This is the structural answer that jitter and blue
        # noise both failed to give: vary the BLOCKS, not the buildings.
        offset = int(_hash_unit(p.schema, "stagger") * 3) if stagger else 0
        placed.append(replace(p, cell_x=cx, cell_y=cy + offset))
        cy += p.cells_h + offset + gap
        column_w = max(column_w, p.cells_w)
    return tuple(placed)


def _settle(
    ctx: PipelineContext, precincts: tuple[Precinct, ...], cell: int
) -> tuple[TileMap, dict[str, Rect], list[tuple[str, Rect]]]:
    """Lattice -> tiles -> one lot rect per object, the ordinary v5 way."""
    slots = plan_slots(ctx, precincts)
    lattice = plan_lattice(precincts, solid=solid_blocks(slots))
    tiles = resolve_coordinates(lattice, cell_size=cell)
    cover = segment_cover(lattice)
    lots = {key: lot_rect(slot, tiles, cover) for key, slot in slots.items()}
    districts = [
        (next((p.schema for p in precincts if p.pid == pid), pid), (x, y, w, h))
        for pid, x, y, w, h in tiles.precinct_rects
    ]
    return tiles, lots, districts


def _jitter(lots: dict[str, Rect], cell: int) -> dict[str, Rect]:
    """Nudge each lot inside its own block by a hashed offset. The lattice is
    untouched, so S8 cannot break — what CAN break is frontage, and that is the
    question this panel exists to answer."""
    out: dict[str, Rect] = {}
    for key, (x, y, w, h) in lots.items():
        dx = int(_hash_unit(key, "jx") * max(1, cell))
        dy = int(_hash_unit(key, "jy") * max(1, cell))
        out[key] = (x + dx, y + dy, w, h)
    return out


def _blue_noise(lots: dict[str, Rect], districts: list[tuple[str, Rect]], schema_of: dict[str, str]) -> dict[str, Rect]:
    """Re-sample every lot over its own district rect, keeping a minimum
    separation — Mitchell's best-candidate, which needs no rejection loop and is
    deterministic given a hashed candidate sequence. The block grid is ignored
    on purpose: this is the panel that shows what 'nothing reads as a grid'
    actually costs."""
    rect_of = {schema: rect for schema, rect in districts}
    out: dict[str, Rect] = {}
    taken: dict[str, list[tuple[int, int]]] = {}
    for key in sorted(lots):
        _, _, w, h = lots[key]
        rect = rect_of.get(schema_of.get(key, ""))
        if rect is None:
            out[key] = lots[key]
            continue
        rx, ry, rw, rh = rect
        best: tuple[int, int] | None = None
        best_gap = -1.0
        # Ten hashed candidates; keep the one furthest from what is already
        # placed in this district. More candidates = more uniform spacing.
        neighbours = taken.setdefault(schema_of.get(key, ""), [])
        for i in range(10):
            cxx = rx + int(_hash_unit(f"{key}#{i}", "nx") * max(1, rw - w + 1))
            cyy = ry + int(_hash_unit(f"{key}#{i}", "ny") * max(1, rh - h + 1))
            gap = min((abs(cxx - px) + abs(cyy - py) for px, py in neighbours), default=1e9)
            if gap > best_gap:
                best_gap, best = gap, (cxx, cyy)
        assert best is not None
        taken.setdefault(schema_of.get(key, ""), []).append(best)
        out[key] = (best[0], best[1], w, h)
    return out


# --- metrics ---------------------------------------------------------------


def _lot_tiles(lots: dict[str, Rect]) -> set[Tile]:
    return {(x + dx, y + dy) for (x, y, w, h) in lots.values() for dx in range(w) for dy in range(h)}


def _no_frontage(lots: dict[str, Rect], road: set[Tile]) -> list[str]:
    """Lots with no road tile orthogonally touching their footprint — buildings
    no vehicle can reach, which the RoadNet rule forbids outright."""
    bad = []
    for key, (x, y, w, h) in sorted(lots.items()):
        touching = any(
            (x + dx + ox, y + dy + oy) in road
            for dx in range(w)
            for dy in range(h)
            for ox, oy in ((0, -1), (1, 0), (0, 1), (-1, 0))
        )
        if not touching:
            bad.append(key)
    return bad


def _overlaps(lots: dict[str, Rect]) -> int:
    """Lots sharing a tile with another lot. Two buildings in one place is not a
    style opinion, and the first version of this sheet could not see it: the only
    trace was a `lot` tile count that quietly fell from 214 to 199."""
    seen: dict[Tile, str] = {}
    bad: set[str] = set()
    for key, (x, y, w, h) in sorted(lots.items()):
        for dx in range(w):
            for dy in range(h):
                other = seen.setdefault((x + dx, y + dy), key)
                if other != key:
                    bad.add(key)
                    bad.add(other)
    return len(bad)


def _on_road(lots: dict[str, Rect], road: set[Tile]) -> int:
    """Lots standing ON pavement — the same class of error as a road threaded
    through a lot, which spike 2 already holds at zero."""
    return sum(
        1 for (x, y, w, h) in lots.values() if any((x + dx, y + dy) in road for dx in range(w) for dy in range(h))
    )


def _collinear(lots: dict[str, Rect]) -> float:
    """The share of lots sitting in a run of 4+ sharing an edge line — the
    LINEARITY Stephen objected to, as a number.

    This exists because `nn_iqr` cannot express his complaint. A perfect lattice
    has an interquartile spread of ZERO, so "most buildings at a similar median
    radius" is *maximised* by precisely the striped grid he rejected. Uniform
    spacing and non-linearity are separate goals; a sheet reporting only the
    first will always crown the grid.
    """
    if not lots:
        return 0.0
    rows: dict[int, list[int]] = {}
    cols: dict[int, list[int]] = {}
    for x, y, _w, _h in lots.values():
        rows.setdefault(y, []).append(x)
        cols.setdefault(x, []).append(y)
    in_run = sum(len(v) for v in rows.values() if len(v) >= 4)
    in_run += sum(len(v) for v in cols.values() if len(v) >= 4)
    return round(in_run / (2 * len(lots)), 2)


def _nn_stats(lots: dict[str, Rect]) -> tuple[float, float]:
    """Median near-neighbour distance between lot CENTRES, and its interquartile
    spread. Stephen's criterion is that most buildings sit at a similar radius
    from each other, so the spread is the number that matters, not the median."""
    centres = [(x + w / 2, y + h / 2) for (x, y, w, h) in lots.values()]
    if len(centres) < 2:
        return 0.0, 0.0
    dists = []
    for i, (ax, ay) in enumerate(centres):
        dists.append(min(abs(ax - bx) + abs(ay - by) for j, (bx, by) in enumerate(centres) if j != i))
    dists.sort()
    med = statistics.median(dists)
    q1 = dists[len(dists) // 4]
    q3 = dists[(3 * len(dists)) // 4]
    return med, q3 - q1


def metrics(panel: Panel) -> dict[str, object]:
    lot_tiles = _lot_tiles(panel.lots)
    report = check_junctions(panel.road)
    med, iqr = _nn_stats(panel.lots)
    no_front = _no_frontage(panel.lots, panel.road)
    return {
        "grid": f"{panel.width}x{panel.height}",
        "road": report.road_tiles,
        "lot": len(lot_tiles),
        "road:lot": round(report.road_tiles / max(len(lot_tiles), 1), 2),
        "s8_viol": len(report.violations),
        "s8_clump": report.largest_clump,
        "no_front": len(no_front),
        "overlap": _overlaps(panel.lots),
        "on_road": _on_road(panel.lots, panel.road),
        "linear": _collinear(panel.lots),
        "nn_med": round(med, 2),
        "nn_iqr": round(iqr, 2),
        "_bad": no_front,
    }


# --- the contact sheet -----------------------------------------------------

GRASS = (86, 140, 74)
ROAD = (70, 70, 76)
LOT = (150, 160, 190)
OUTLINE = (44, 48, 66)
BAD = (255, 0, 200)  # the defect convention: a lot with no street
TINT = [(210, 170, 120), (150, 190, 210), (200, 200, 150), (190, 160, 200), (170, 210, 170)]
BG = (24, 22, 40)
INK = (235, 235, 240)


def draw_panel(panel: Panel, scale: int, bad: set[str]) -> Image.Image:
    img = Image.new("RGB", (panel.width * scale, panel.height * scale), GRASS)
    d = ImageDraw.Draw(img, "RGBA")
    for i, (_schema, (x, y, w, h)) in enumerate(panel.districts):
        c = TINT[i % len(TINT)]
        d.rectangle(
            [x * scale, y * scale, (x + w) * scale - 1, (y + h) * scale - 1],
            fill=(c[0], c[1], c[2], 70),
        )
    for x, y in sorted(panel.road):
        d.rectangle([x * scale, y * scale, (x + 1) * scale - 1, (y + 1) * scale - 1], fill=ROAD)
    for key, (x, y, w, h) in sorted(panel.lots.items()):
        d.rectangle(
            [x * scale, y * scale, (x + w) * scale - 1, (y + h) * scale - 1],
            fill=BAD if key in bad else LOT,
            outline=OUTLINE,
            width=1,
        )
    return img


def build_sheet(panels: list[tuple[Panel, dict[str, object]]], out: str) -> None:
    scale = 6
    pad, caption = 14, 62
    cols = min(3, len(panels))
    rows = -(-len(panels) // cols)
    cw = max(p.width for p, _ in panels) * scale + pad * 2
    ch = max(p.height for p, _ in panels) * scale + pad + caption
    sheet = Image.new("RGB", (cw * cols, ch * rows + 30), BG)
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), "streets: schema clustering vs the depth column  (S8 held at 0)", fill=INK)
    for i, (panel, m) in enumerate(panels):
        ox, oy = (i % cols) * cw, (i // cols) * ch + 30
        sheet.paste(draw_panel(panel, scale, set(m["_bad"])), (ox + pad, oy + 4))  # type: ignore[arg-type]
        ty = oy + panel.height * scale + 8
        d.text((ox + pad, ty), f"{panel.label} — {panel.note}", fill=INK)
        d.text(
            (ox + pad, ty + 12),
            f"grid {m['grid']}  road {m['road']}  road:lot {m['road:lot']}  "
            f"S8 viol {m['s8_viol']} clump {m['s8_clump']}",
            fill=INK,
        )
        broken = bool(m["no_front"]) or bool(m["overlap"]) or bool(m["on_road"])
        d.text(
            (ox + pad, ty + 36),
            f"DEFECTS  no_frontage {m['no_front']}  overlap {m['overlap']}  on_road {m['on_road']}",
            fill=BAD if broken else INK,
        )
        d.text(
            (ox + pad, ty + 24),
            f"nn_med {m['nn_med']}  nn_iqr {m['nn_iqr']}  linear {m['linear']}",
            fill=INK,
        )
    sheet.save(out)
    print(f"wrote {out}  ({sheet.width}x{sheet.height})")


def main() -> None:
    ap = argparse.ArgumentParser()
    # No default: this used to point at ~/clients/dogfood, a client directory on
    # one machine. A spike script in a public repo should not name it, and should
    # not quietly read it when run with no arguments.
    ap.add_argument("--src", required=True, help="Path to the dbt/tycoon project to cluster.")
    ap.add_argument("--cell", type=int, default=2)
    ap.add_argument("--gap", type=int, default=1, help="empty cells between neighbourhoods")
    ap.add_argument("--out", default="spike-out/cluster-sheet.png")
    args = ap.parse_args()

    ctx = load_context(args.src)
    schema_of = {obj.key: obj.schema for obj in ctx.objects}
    panels: list[Panel] = [panel_v4(ctx)]

    # Panel 2: v5 exactly as it stands today.
    depth_precincts = plan_precincts(ctx, demand=block_demand(ctx))
    tiles, lots, districts = _settle(ctx, depth_precincts, args.cell)
    panels.append(
        Panel(
            "2  v5-depth",
            "one precinct per (depth, schema)",
            tiles.width,
            tiles.height,
            set(tiles.road_tiles),
            lots,
            districts,
        )
    )

    # Panels 3-5 share ONE lattice: only the settling changes.
    schema_precincts = _schema_precincts(ctx, args.gap)
    s_tiles, s_lots, s_districts = _settle(ctx, schema_precincts, args.cell)
    road = set(s_tiles.road_tiles)
    panels.append(
        Panel(
            "3  v5-schema",
            "precincts merged per schema",
            s_tiles.width,
            s_tiles.height,
            road,
            s_lots,
            s_districts,
        )
    )
    panels.append(
        Panel(
            "4  v5-schema+jitter",
            "lots nudged inside their block",
            s_tiles.width,
            s_tiles.height,
            road,
            _jitter(s_lots, args.cell),
            s_districts,
        )
    )
    panels.append(
        Panel(
            "5  v5-schema+noise",
            "blue noise, block grid ignored",
            s_tiles.width,
            s_tiles.height,
            road,
            _blue_noise(s_lots, s_districts, schema_of),
            s_districts,
        )
    )

    # Panel 6: the structural alternative — same block model, staggered phases.
    st_precincts = _schema_precincts(ctx, args.gap, stagger=True)
    t6, lots6, districts6 = _settle(ctx, st_precincts, args.cell)
    panels.append(
        Panel(
            "6  v5-schema+stagger",
            "neighbourhoods phase-shifted",
            t6.width,
            t6.height,
            set(t6.road_tiles),
            lots6,
            districts6,
        )
    )

    measured = [(p, metrics(p)) for p in panels]
    head = [
        "grid",
        "road",
        "lot",
        "road:lot",
        "s8_viol",
        "s8_clump",
        "no_front",
        "overlap",
        "on_road",
        "linear",
        "nn_med",
        "nn_iqr",
    ]
    print(f"{'panel':22s} " + " ".join(f"{h:>9s}" for h in head))
    for p, m in measured:
        print(f"{p.label:22s} " + " ".join(f"{str(m[h]):>9s}" for h in head))
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    build_sheet(measured, args.out)


if __name__ == "__main__":
    main()
