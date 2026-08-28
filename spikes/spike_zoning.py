"""Spike 2: does the streets v5 lattice read as a CITY once buildings land on it?

Not a test — the look-first instrument for `dbtycoon.sim.town_zoning`, which is
reachable from here and nowhere else. Draws every fixture's precincts tinted by
texture, the lattice on top, and then the LOTS: every catalog object on the
frontage slot `plan_zoning` gave it, with its door marked on the road tile it
opens onto.

The one question this sheet exists to answer, and it is a number before it is a
picture: **does every lot front a street?** `no_frontage` is the count of lots
with no road tile orthogonally adjacent to their footprint, and it must be 0 on
all 38 fixtures. Any lot that misses is painted MAGENTA, the same defect
convention `spike_road_defects.py` uses for naked endings. A nonzero count
means the block shaping is wrong — it is the finding, not a bug to repair with
a later pass.

Printed alongside: big lots (each consuming a whole block, ringed by streets —
`threaded` counts any road tile INSIDE a lot and must also be 0), block fill
ratio, unzoned interior cells, `seam` (spike 3's new cost — see `seam_tiles`),
sibling-block contiguity, the share of settled land that is pavement and the
share that is building, grid area against the v4 baseline, and the zoning
fingerprint under three shuffles of the input order — including `dotted-tie`,
the fixture that exists because an earlier round's bench could not see a whole
class of ordering regression.

Spike 3 made block SHAPE follow demand (`town_texture.fit_blocks`), so `fill`
is the headline here: 47% before, 90% after, and the fixtures that used to come
out LARGER than v4 on a sparse catalog no longer do. Read `fill` and `paved`
together — pavement's share of the settled land went UP (40% -> 55%) only
because the bare land it was being measured against went away; street per
BUILDING went down (paved:built 2.1 -> 1.6).

Usage (Pillow is not a runtime dependency; bring it in for the spike):

    uv run --with pillow python scripts/spike_zoning.py
    uv run --with pillow python scripts/spike_zoning.py --detail random-0
    uv run --with pillow python scripts/spike_zoning.py --cell 1

`--cell` re-resolves the SAME lattice and the SAME slots at a different cell
size: 2 is the working default (an ordinary lot is 2x2 tiles), 1 is spike 1's
and the honest A/B for the pavement fraction.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spike_fixtures import load_fixtures, shuffled  # noqa: E402
from spike_lattice import (  # noqa: E402
    COL_GRASS,
    OUT_DIR,
    ROLE_COLOURS,
    _segment_tiles,
    contact_sheet,
    detail,
)

from dbtycoon.catalog.models import PipelineContext  # noqa: E402
from dbtycoon.sim.layout import plan_dag_layout  # noqa: E402
from dbtycoon.sim.town_blocks import (  # noqa: E402
    Lattice,
    TileMap,
    plan_lattice,
    plan_precincts,
    resolve_coordinates,
)
from dbtycoon.sim.town_texture import DOWNTOWN, INDUSTRIAL, SUBURBAN  # noqa: E402
from dbtycoon.sim.town_zoning import (  # noqa: E402
    CELL_SIZE,
    ZonePlan,
    block_demand,
    interior_cells,
    lot_rect,
    placement_inputs,
    plan_slots,
    plan_zoning,
    segment_cover,
    solid_blocks,
)


def build(ctx: PipelineContext, cell: int):
    """precincts -> slots -> lattice -> tiles -> zoning, in that order.

    Slots come BEFORE the lines because a big lot's block must not get the
    suburban cul-de-sac stub threaded into it (`solid_blocks`); the prefix-sum
    conversion is still the last thing that happens.
    """
    precincts = plan_precincts(ctx, demand=block_demand(ctx))
    lattice = plan_lattice(precincts, solid=solid_blocks(plan_slots(ctx, precincts)))
    tiles = resolve_coordinates(lattice, cell_size=cell)
    # Spike 4's seam fix: a lot absorbs a bounding line that carries no segment
    # beside it, which is answerable from the lattice alone (`segment_cover`).
    cover = segment_cover(lattice)
    return precincts, lattice, tiles, plan_zoning(ctx, lattice, tiles, cover), cover


# Land is darker than in spike 1 so the buildings are what the eye lands on:
# the question here is "city of buildings?", not "legible districts?".
LAND_COLOURS = {
    INDUSTRIAL: (96, 68, 46),
    DOWNTOWN: (54, 60, 86),
    SUBURBAN: (62, 96, 56),
}
# Two bone tones, alternating with the slot's parity along its face. Lots
# TOUCH — that is the point of a city block — so at one pixel per tile a run of
# them paints as one bar and the eye cannot count buildings. The alternation is
# render-only; nothing structural reads it.
COL_LOT = ((216, 202, 170), (188, 174, 142))
COL_BIG = (198, 92, 70)  # a whole-block lot: terracotta, unmistakably other
COL_DOOR = (90, 210, 230)  # cyan, as `spike_road_defects` paints its aprons
COL_NAKED = (255, 0, 255)  # a lot with no street: the defect this spike hunts


def zoning_image(lattice: Lattice, tiles: TileMap, zone: ZonePlan, naked: set[str], cover) -> Image.Image:
    """One pixel per tile: land, streets, lots, doors, defects — in that order,
    so a magenta failure always survives everything painted under it."""
    img = Image.new("RGB", (max(tiles.width, 1), max(tiles.height, 1)), COL_GRASS)
    px = img.load()
    texture_of = {p.pid: p.texture for p in lattice.precincts}
    for pid, x, y, w, h in tiles.precinct_rects:
        colour = LAND_COLOURS[texture_of[pid]]
        for ix in range(x, min(x + w, img.width)):
            for iy in range(y, min(y + h, img.height)):
                px[ix, iy] = colour
    for role in ("internal", "edge", "spine"):
        for seg in lattice.segments:
            if seg.role == role:
                for x, y in _segment_tiles(seg, tiles):
                    if 0 <= x < img.width and 0 <= y < img.height:
                        px[x, y] = ROLE_COLOURS[role]
    for key in sorted(zone.slot_of):
        slot = zone.slot_of[key]
        x, y, w, h = lot_rect(slot, tiles, cover)
        # A whole-block lot is bigger AND terracotta: at cell_size 1 the size
        # alone would not carry it.
        if key in naked:
            colour = COL_NAKED
        elif len(slot.cells) > 1:
            colour = COL_BIG
        else:
            colour = COL_LOT[(slot.index + (0 if slot.side in "nw" else 1)) % 2]
        for ix in range(x, min(x + w, img.width)):
            for iy in range(y, min(y + h, img.height)):
                px[ix, iy] = colour
    for key in sorted(zone.door_of):
        (dx, dy), _facing = zone.door_of[key]
        if 0 <= dx < img.width and 0 <= dy < img.height:
            px[dx, dy] = COL_DOOR
    return img


# --- the instruments -------------------------------------------------------


def _neighbours(x: int, y: int) -> list[tuple[int, int]]:
    return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]


def frontage_defects(zone: ZonePlan, tiles: TileMap, cover) -> tuple[set[str], set[str]]:
    """`(no_frontage, threaded)`, measured against the ACTUAL road tiles.

    Not against the rule that was supposed to guarantee them — the whole point
    of the instrument is that it can disagree with the construction.
    """
    road = set(tiles.road_tiles)
    naked: set[str] = set()
    threaded: set[str] = set()
    for key in sorted(zone.slot_of):
        x, y, w, h = lot_rect(zone.slot_of[key], tiles, cover)
        lot = {(ix, iy) for ix in range(x, x + w) for iy in range(y, y + h)}
        if lot & road:
            threaded.add(key)
        if not any(n in road for t in lot for n in _neighbours(*t) if n not in lot):
            naked.add(key)
    return naked, threaded


def seam_tiles(precincts, tiles: TileMap) -> int:
    """Tiles lost to a lattice line that runs INSIDE somebody's block.

    Spike 3's new cost, and it is a cost the block grammar cannot see: line
    widths are global by index, so once precincts stop being the same number of
    cells wide a line that is a block boundary for one of them lands mid-block
    in its neighbour and takes a tile of that block's land. Depth columns all
    start at cell_y 0, so the horizontal ones cross the whole city.

    It is LAND, never pavement — the lots either side of it still front their
    own streets, `naked` and `threaded` both stay 0 — so it reads as a one-tile
    alley between buildings rather than as a street. But it is exactly the
    plus-sign of gap round 1 was condemned for, so it gets a number.
    """
    total = 0
    for p in precincts:
        inner_v = [p.cell_x + i for i in range(p.cells_w) if i % p.block_w]
        inner_h = [p.cell_y + i for i in range(p.cells_h) if i % p.block_h]
        east, south = p.cell_x + p.cells_w, p.cell_y + p.cells_h
        width = tiles.v_at[east] + tiles.v_w[east] - tiles.v_at[p.cell_x]
        height = tiles.h_at[south] + tiles.h_w[south] - tiles.h_at[p.cell_y]
        total += sum(tiles.v_w[i] for i in inner_v) * height
        total += sum(tiles.h_w[i] for i in inner_h) * width
    return total


def sibling_contiguity(zone: ZonePlan, block_of: dict[str, str]) -> tuple[int, int, int]:
    """`(groups, one_block, contiguous)` for exact-source sibling blocks.

    `one_block` is the number that landed on a SINGLE literal city block, which
    is the claim; `contiguous` also counts a group that outgrew one block and
    spilled into an adjacent one rather than scattering.
    """
    groups: dict[str, list[str]] = {}
    for key, gid in sorted(block_of.items()):
        if key in zone.slot_of:
            groups.setdefault(gid, []).append(key)
    one = whole = 0
    for members in groups.values():
        blocks = sorted({zone.slot_of[k].block for k in members})
        if len(blocks) == 1:
            one += 1
            whole += 1
        elif all(abs(a[0] - b[0]) + abs(a[1] - b[1]) <= 8 for a, b in zip(blocks, blocks[1:], strict=False)):
            whole += 1
    return len(groups), one, whole


def zone_fingerprint(ctx: PipelineContext, cell: int) -> str:
    """sha256 over the placement AND the zoning: every precinct, every segment,
    every slot, every lot anchor, every door. A change to the fill order that
    the lattice fingerprint cannot see shows up here."""
    _precincts, lattice, tiles, zone, _cover = build(ctx, cell)
    parts = [f"lines {lattice.v_lines}x{lattice.h_lines} grid {tiles.width}x{tiles.height}"]
    for p in lattice.precincts:
        parts.append(
            f"precinct {p.pid} d{p.depth} b{p.band} {p.texture} cap{p.capacity} "
            f"{p.blocks_x}x{p.blocks_y} @{p.cell_x},{p.cell_y} {sorted(p.members)}"
        )
    for s in lattice.segments:
        parts.append(f"seg {s.key.axis} {s.key.line} {s.key.start}-{s.key.end} {s.role} {s.pid}")
    for key in sorted(zone.slot_of):
        slot = zone.slot_of[key]
        parts.append(
            f"lot {key} block{slot.block} {slot.side}{slot.index} cells{list(slot.cells)} "
            f"xy{zone.lot_xy[key]} door{zone.door_of[key]}"
        )
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:16]


def shuffle_check(ctx: PipelineContext, cell: int, digest: str) -> tuple[bool, str]:
    for seed in (1, 2, 3):
        other = zone_fingerprint(shuffled(ctx, seed), cell)
        if other != digest:
            return False, other
    return True, digest


def _shares(tiles: TileMap, zone: ZonePlan, cover) -> tuple[int, int]:
    """`(paved%, built%)` of the SETTLED land — the precincts' own footprint,
    never the whole grid, so margins and open ground cannot flatter either."""
    land = {
        (x, y) for _pid, rx, ry, rw, rh in tiles.precinct_rects for x in range(rx, rx + rw) for y in range(ry, ry + rh)
    }
    if not land:
        return 0, 0
    built: set[tuple[int, int]] = set()
    for slot in zone.slot_of.values():
        x, y, w, h = lot_rect(slot, tiles, cover)
        built |= {(ix, iy) for ix in range(x, x + w) for iy in range(y, y + h)}
    return 100 * len(land & set(tiles.road_tiles)) // len(land), 100 * len(built & land) // len(land)


def main() -> None:
    args = sys.argv[1:]
    only = args[args.index("--detail") + 1] if "--detail" in args else None
    cell = int(args[args.index("--cell") + 1]) if "--cell" in args else CELL_SIZE
    suffix = "" if cell == CELL_SIZE else f"-cell{cell}"
    OUT_DIR.mkdir(exist_ok=True)

    fixtures = load_fixtures(only)
    if not fixtures:
        raise SystemExit(f"no fixture named {only!r}")

    rows: list[tuple[str, Image.Image, str]] = []
    print(
        f"{'fixture':<16}{'grid':>11}{'lots':>6}{'big':>5}{'NAKED':>7}{'thread':>7}"
        f"{'fill':>6}{'inter':>6}{'seam':>6}{'sib':>9}{'paved':>7}{'built':>7}"
        f"{'v5 area':>9}{'v4 area':>9}{'ratio':>7}  fingerprint      shuf"
    )
    failures: list[str] = []
    naked_total = threaded_total = interior_total = lots_total = big_total = 0
    seam_total = 0
    slots_used = slots_have = 0
    sib_groups = sib_one = sib_whole = 0
    v4_total = v5_total = 0
    paved_all: list[int] = []
    built_all: list[int] = []
    alt_paved: list[int] = []
    alt_built: list[int] = []
    for name, ctx in fixtures:
        precincts, lattice, tiles, zone, cover = build(ctx, cell)
        plan = plan_dag_layout(ctx)

        naked, threaded = frontage_defects(zone, tiles, cover)
        interior = sum(len(interior_cells(p)) for p in precincts)
        seam = seam_tiles(precincts, tiles)
        _rank, block_of, big = placement_inputs(ctx)
        groups, one, whole = sibling_contiguity(zone, block_of)
        have = sum(p.blocks * p.block_cells for p in precincts)
        used = sum(len(slot.cells) for slot in zone.slot_of.values())
        paved, built = _shares(tiles, zone, cover)
        alt = resolve_coordinates(lattice, cell_size=1 if cell != 1 else 2)
        alt_zone = plan_zoning(ctx, lattice, alt, cover)
        a_paved, a_built = _shares(alt, alt_zone, cover)

        v4_area, v5_area = plan.width * plan.height, tiles.width * tiles.height
        digest = zone_fingerprint(ctx, cell)
        ok, other = shuffle_check(ctx, cell, digest)
        if not ok:
            failures.append(f"{name}: {digest} vs shuffled {other}")

        n_big = sum(1 for k in zone.slot_of if k in big)
        lots_total += len(zone.slot_of)
        big_total += n_big
        naked_total += len(naked)
        threaded_total += len(threaded)
        interior_total += interior
        seam_total += seam
        slots_used += used
        slots_have += have
        sib_groups, sib_one, sib_whole = sib_groups + groups, sib_one + one, sib_whole + whole
        v4_total, v5_total = v4_total + v4_area, v5_total + v5_area
        if precincts:
            paved_all.append(paved)
            built_all.append(built)
            alt_paved.append(a_paved)
            alt_built.append(a_built)
        print(
            f"{name:<16}{tiles.width:>5}x{tiles.height:<5}{len(zone.slot_of):>6}{n_big:>5}"
            f"{len(naked):>7}{len(threaded):>7}"
            f"{(100 * used // max(have, 1)):>5}%{interior:>6}{seam:>6}{f'{one}/{groups}':>9}"
            f"{paved:>6}%{built:>6}%{v5_area:>9}{v4_area:>9}"
            f"{(f'{v5_area / v4_area:.2f}x' if v4_area else '-'):>7}"
            f"  {digest} {'OK ' if ok else 'DIFFERS'}"
        )
        caption = (
            f"{tiles.width}x{tiles.height}  lots={len(zone.slot_of)} big={n_big}  "
            f"naked={len(naked)}  paved={paved}% built={built}%"
        )
        rows.append((name, zoning_image(lattice, tiles, zone, naked, cover), caption))

    if only:
        out = OUT_DIR / f"v5-zoning-detail-{only.replace('/', '_')}{suffix}.png"
        detail(only, rows[0][1], rows[0][2], out)
    else:
        out = OUT_DIR / f"v5-zoning-contact-sheet{suffix}.png"
        contact_sheet(
            rows,
            out,
            title=(
                f"streets v5 SPIKE 3 - blocks trimmed to demand: {len(rows)} fixtures, cell_size={cell}, no routing"
            ),
            subtitle=(
                "land tint = texture (rust industrial / slate downtown / green suburban); "
                "bone = lot, terracotta = whole-block big lot, cyan = door, MAGENTA = no frontage"
            ),
        )
    print(f"\nlots={lots_total}  big={big_total}  LOTS WITH NO FRONTAGE = {naked_total}")
    print(f"lots with a road threaded through them = {threaded_total}")
    print(f"unzoned interior cells = {interior_total}")
    print(
        f"mid-block seam tiles = {seam_total} "
        f"({100 * seam_total // max(v5_total, 1)}% of the v5 grid) - GEOMETRIC, before "
        "absorption; spike 4 gives them to the lot that bounds them and reports what "
        "is left over (`spike_arterials.py`, column seam1)"
    )
    print(f"block fill = {100 * slots_used // max(slots_have, 1)}% of {slots_have} slots")
    print(f"sibling blocks: {sib_one}/{sib_groups} on ONE block, {sib_whole}/{sib_groups} contiguous")
    print(f"total grid area  v5={v5_total}  v4={v4_total}  ratio={v5_total / max(v4_total, 1):.2f}x")
    other_cell = 1 if cell != 1 else 2
    for label, paved, built in (
        (f"cell_size={cell}", paved_all, built_all),
        (f"cell_size={other_cell}", alt_paved, alt_built),
    ):
        if paved:
            p, b = sorted(paved), sorted(built)
            print(
                f"{label:<14} paved  min={p[0]}% median={p[len(p) // 2]}% max={p[-1]}%   "
                f"built  min={b[0]}% median={b[len(b) // 2]}% max={b[-1]}%"
            )
    print("shuffled-input determinism: " + ("ALL IDENTICAL" if not failures else "FAILED"))
    for line in failures:
        print(f"  {line}")
    print(f"image -> {out}")


if __name__ == "__main__":
    main()
