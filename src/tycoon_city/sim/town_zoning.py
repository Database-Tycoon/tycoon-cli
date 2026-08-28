"""Streets v5, SPIKE 2: LOTS ON FRONTAGE — buildings on the lattice.

**Not wired into anything.** `plan_dag_layout` is still the only planner the
app, the contract and the tests reach; nothing here is imported by `layout`,
`town_plan`, `city_json` or any test. The only caller is
`scripts/spike_zoning.py`, which renders it so it can be JUDGED before a rule
earns a test (four spec-first geometry attempts have been wrong in this repo).

Spike 1 (`town_blocks`) decided the LAND: precincts west->east by depth,
texture from depth, blocks from texture, and one prefix-sum conversion to tiles
last. This round decides which building stands on which piece of it. Spike 3
then made the block shape follow the band's demand (`town_texture`), so every
`BLOCK_CELLS[texture]` lookup here became `p.block_w`/`p.block_h` and the
packer's capacity became `p.block_cells`.

**The property this spike exists to prove: EVERY LOT FRONTS A STREET**, by
CONSTRUCTION rather than by a repair pass. A block is at most
`MAX_INTERIOR_SHORT = 2` cells on its short axis, so every cell of every block
has that block's own boundary line on one of its own edges — and every block
boundary carries a segment (frame or block seam), so every one of those edges
is pavement. There is no interior to strand a lot in. Spike 3's TRIMMED blocks
only strengthen that: a block one cell thick has every cell on both of its long
sides, so it offers one frontage face instead of two and still has no interior.
`interior_cells` is the instrument that says so, and `scripts/spike_zoning.py`
paints any lot that misses in MAGENTA, following `spike_road_defects.py`'s
defect convention.

The v4 placement inputs map onto blocks better than they mapped onto rows, and
are REUSED from `town_rows`, never reinvented:

  `_sibling_blocks`     exact same source set -> ONE literal city block, its
                        members filling that block's frontage in sequence.
                        "Block" stops being a metaphor.
  `_cluster_columns`    affinity clusters -> adjacent blocks in the precinct;
                        cluster order is lineage pull, unchanged.
  `_barycenter_order`   slot order along a block's frontage, so crossing
                        reduction still pulls related buildings adjacent.
  `big_lots`            the top row-count decile CONSUMES A WHOLE BLOCK and is
                        RINGED by streets, never threaded through
                        (road-grammar theme 3, verbatim).

Fill order is deterministic and stated once: blocks row-major, sides n/e/s/w,
slots by barycenter rank then key. Sorted everywhere, integer arithmetic, no
floats in any structural decision.

Lattice-space discipline holds: `plan_slots` never sees a tile. `plan_zoning`
is the only function here that does, and it reads the `TileMap` spike 1
already produced rather than resolving anything itself.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..catalog.models import PipelineContext
from .layout import _known_edges, compute_depths
from .town_blocks import Lattice, Precinct, TileMap
from .town_frontage import (
    LineCover,
    Slot,
    ZonePlan,
    door_tile,
    door_unit,
    lot_rect,
    segment_cover,
    unit_cover,
)
from .town_rows import (
    _barycenter_order,
    _cluster_columns,
    _forward_chains,
    _sibling_blocks,
    big_lots,
)
from .town_texture import block_capacity

# Re-exported so every existing `from .town_zoning import ...` stays valid:
# the split is a line-law move, not an interface change.
__all__ = [
    "CELL_SIZE",
    "LineCover",
    "Slot",
    "ZonePlan",
    "block_demand",
    "block_slots",
    "door_tile",
    "door_unit",
    "interior_cells",
    "lot_rect",
    "pack_units",
    "placement_inputs",
    "plan_slots",
    "plan_zoning",
    "segment_cover",
    "solid_blocks",
    "unit_cover",
    "whole_block_slot",
]

# A cell is this many tiles square. 1 made an ordinary lot a single tile and
# 60% of the settled land pavement; 2 makes it 2x2 — the footprint v4 reserved
# for its BIG buildings.
#
# **3 from spike 5, and it is Stephen's call** (2026-08-06, from the spike-4
# PNGs): once hierarchy widths landed, cell 2 came out 65% pavement against 29%
# built on the settled land, which is a road map with buildings in the gaps. A
# three-tile cell restores it to 52/39 and costs 0.22x v4's grid area instead of
# 0.15x — the area was never the constraint, the proportion was.
CELL_SIZE = 3

# Ranks come from v4's barycenter sequence; an object with no lineage at all is
# not in it, so it sorts after everything that is, then by key.
_NO_RANK = 1 << 30


@dataclass(frozen=True)
class _Unit:
    """A run of consecutive slots that must not be broken up: one sibling
    block, one big lot's whole block, or one unaffiliated building."""

    rank: tuple[int, str]
    gid: str
    members: tuple[str, ...]
    size: int


# --- the v4 placement inputs, reused ---------------------------------------


def placement_inputs(
    ctx: PipelineContext,
) -> tuple[dict[str, int], dict[str, str], frozenset[str]]:
    """`(rank_of, block_of, big)` — v4's own ordering, read from `town_rows`.

    This is `plan_site`'s body up to (and not including) row assignment: rows
    are the thing v5 replaces, everything before them is the thing v5 keeps.
    `rank_of` is the position in the banded/clustered sequence
    `_cluster_columns` writes, which already has affinity clusters in lineage
    order with sibling blocks contiguous inside them — so restricting it to one
    precinct's members yields the precinct's fill order with no extra rule.
    """
    depths = compute_depths(ctx)
    edges = sorted({(s, d) for s, d in _known_edges(ctx) if s != d})
    schema_of = {obj.key: obj.schema for obj in ctx.objects}
    row_count_of = {obj.key: obj.row_count for obj in ctx.objects}
    big = big_lots(ctx)

    preds: dict[str, set[str]] = {}
    for src, dst in edges:
        preds.setdefault(dst, set()).add(src)
    connected = sorted({k for pair in edges for k in pair})
    depth = {k: depths[k] for k in connected}
    block_of = _sibling_blocks(connected, preds, schema_of, depth)

    rank_of: dict[str, int] = {}
    if edges:
        chains, node_layer, columns = _forward_chains(edges, depth)
        forward = sorted(
            {
                (a, b)
                for chain in chains.values()
                for a, b in zip(chain, chain[1:], strict=False)
                if node_layer[b] > node_layer[a]
            }
        )
        order = _barycenter_order(columns, forward, node_layer)
        _cluster_columns(columns, order, preds, block_of, schema_of, row_count_of)
        for sequence in order.values():
            for node, i in sequence.items():
                if not node.startswith("\x00"):
                    rank_of[node] = i
    return rank_of, block_of, big


def _units(
    members: tuple[str, ...],
    rank_of: dict[str, int],
    block_of: dict[str, str],
    big: frozenset[str],
    capacity: int,
) -> tuple[_Unit, ...]:
    """One precinct's members as unbreakable runs, in lineage-pull order.

    A big lot is its own unit sized at the WHOLE block, which is what makes it
    ringed by streets: a unit that size can never share a block, so no street
    is ever threaded through it. Bigs are pulled out of their sibling group
    first, so the group's remaining members stay contiguous.
    """

    def rank(key: str) -> tuple[int, str]:
        return (rank_of.get(key, _NO_RANK), key)

    groups: dict[str, list[str]] = {}
    for key in sorted(members):
        gid = f"\x00big\x00{key}" if key in big else block_of.get(key, key)
        groups.setdefault(gid, []).append(key)

    units: list[_Unit] = []
    for gid, group in groups.items():
        ordered = tuple(sorted(group, key=rank))
        size = capacity if gid.startswith("\x00big\x00") else len(ordered)
        units.append(_Unit(rank(ordered[0]), gid, ordered, size))
    return tuple(sorted(units, key=lambda u: (u.rank, u.gid)))


def pack_units(sizes: tuple[int, ...], capacity: int) -> tuple[tuple[int, int], ...]:
    """`(block, first slot)` per unit. Integer arithmetic, order-sensitive and
    therefore shared: `block_demand` sizes a precinct with the SAME walk
    `plan_slots` then fills it with, so a precinct can never come up a block
    short of the buildings it was sized for.

    A unit that does not fit in what is left of the current block starts a new
    one — the sibling block earns a whole block face rather than straddling a
    street. A unit bigger than a block spills into the next one.
    """
    out: list[tuple[int, int]] = []
    block = slot = 0
    for size in sizes:
        if slot and slot + size > capacity:
            block, slot = block + 1, 0
        out.append((block, slot))
        slot += size
        while slot >= capacity:
            block, slot = block + 1, slot - capacity
    return tuple(out)


def _blocks_used(sizes: tuple[int, ...], capacity: int) -> tuple[int, int]:
    """`(blocks, spills)` for one precinct's units at one block capacity.

    A SPILL is a unit the packer had to break across a block boundary — a
    sibling group too big for the block on offer. It is the price `fit_blocks`
    refuses to pay for a saved cell: trimming a downtown band to 1x1 blocks
    wastes nothing and scatters a 3-object sibling group over three of them,
    and "one sibling block on ONE literal city block" is spike 2's claim.
    """
    placed = pack_units(sizes, capacity)
    if not placed:
        return 1, 0
    spills = sum(1 for (_b, slot), size in zip(placed, sizes, strict=True) if slot + size > capacity)
    block, slot = placed[-1]
    return max(1, block + -(-(slot + sizes[-1]) // capacity)), spills


def block_demand(
    ctx: PipelineContext,
) -> Callable[[tuple[str, ...], str, tuple[int, int]], tuple[int, int, int]]:
    """The `plan_precincts` sizing hook: `(members, texture, shape) -> (cells,
    blocks, spills)`, answered fresh for every CANDIDATE block shape.

    Spike 1's default priced a big lot at four cells wherever it stood. Once a
    big lot consumes a whole block that is wrong on two of the three textures
    (a full industrial block is eight cells), and a sibling block that refuses
    to straddle a street costs the tail of the block before it. Both are decided
    here, by the packer that will actually do the filling.

    Spike 3 makes the shape an argument rather than a lookup, and that is what
    lets `town_texture.fit_blocks` compare candidates honestly: a band of three
    siblings demands one 3x1 bar and no waste, or two 2x1 dominoes and a cell of
    waste, and only the packer can say which.
    """
    rank_of, block_of, big = placement_inputs(ctx)

    def demand(members: tuple[str, ...], _texture: str, shape: tuple[int, int]) -> tuple[int, int, int]:
        capacity = block_capacity(shape)
        sizes = tuple(u.size for u in _units(members, rank_of, block_of, big, capacity))
        blocks, spills = _blocks_used(sizes, capacity)
        return sum(sizes), blocks, spills

    return demand


# --- slots: which cells a block offers, in lattice space --------------------


def _block_origin(p: Precinct, index: int) -> tuple[int, int]:
    """Block `index` row-major within the precinct -> its NW cell."""
    bx, by = index % p.blocks_x, index // p.blocks_x
    return p.cell_x + bx * p.block_w, p.cell_y + by * p.block_h


def block_slots(p: Precinct, index: int) -> tuple[Slot, ...]:
    """Every ordinary slot of one block, in fill order.

    Frontage is taken on the block's SHORT axis, which is what makes the
    property hold with no repair pass: a 4x2 block hands its north row to the
    north street and its south row to the south street and has nothing left
    over; a 2x4 block does the same east and west. `MAX_INTERIOR_SHORT = 2` is
    exactly the condition under which "nothing left over" is true.

    Sides enumerate n/e/s/w, but the two faces INTERLEAVE — slot 0 north, slot
    1 south, slot 2 north. The first render filled one whole face before
    touching the other, and since block capacity (4-8) badly outruns the
    typical band's demand, every block came out built along its north street
    and bare along its south: every street in the city had buildings on one
    side only, which reads as a frontier road, not a city block. Pairing the
    faces spends the same lots on twice as much frontage. A sibling group still
    lands on ONE block; it takes a corner of it rather than a whole face.

    A block TRIMMED to one cell thick (spike 3's smallest shapes) has ONE face,
    not two: every cell of a 3x1 bar already touches both the north and the
    south street, so enumerating both would hand the same cell out twice. The
    frontage guarantee is stronger there, not weaker — the trim never costs it.

    Fill alternates end on `block row + band` (`Slot.index` still means
    position along the side; only the order of consumption reverses). Blocks
    are rarely full — even trimmed, the last one takes the remainder — and
    filling every one from the same end stacked the vacant halves into a single
    unbroken column of empty land. `+ band` is the same correction
    `_interior_keys` needed: most precincts on this bench are ONE block tall, so
    a block-row parity alone never flips and every stacked precinct built
    against the same kerb.
    """
    bw, bh = p.block_w, p.block_h
    x0, y0 = _block_origin(p, index)
    faces: list[list[Slot]] = []
    if bh <= bw:
        rows = (("n", 0),) if bh == 1 else (("n", 0), ("s", bh - 1))
        for side, row in rows:
            faces.append([Slot((x0, y0), side, i, ((x0 + i, y0 + row),)) for i in range(bw)])
    else:
        cols = (("e", 0),) if bw == 1 else (("e", bw - 1), ("w", 0))
        for side, col in cols:
            faces.append([Slot((x0, y0), side, i, ((x0 + col, y0 + i),)) for i in range(bh)])
    if (index // p.blocks_x + p.band) % 2:
        faces = [list(reversed(face)) for face in faces]
    return tuple(slot for pair in zip(*faces, strict=True) for slot in pair)


def whole_block_slot(p: Precinct, index: int) -> Slot:
    """A big lot: every cell of the block, one door on its first frontage."""
    bw, bh = p.block_w, p.block_h
    x0, y0 = _block_origin(p, index)
    cells = tuple((x0 + dx, y0 + dy) for dy in range(bh) for dx in range(bw))
    return Slot((x0, y0), "n" if bh <= bw else "e", 0, cells)


def interior_cells(p: Precinct) -> tuple[tuple[int, int], ...]:
    """Cells of `p`'s blocks that NO slot fronts — the number this spike exists
    to hold at zero. Nonzero means the block shaping is wrong, and that is the
    finding, not something to repair afterwards."""
    bw, bh = p.block_w, p.block_h
    out: list[tuple[int, int]] = []
    for index in range(p.blocks_x * p.blocks_y):
        x0, y0 = _block_origin(p, index)
        fronted = {c for slot in block_slots(p, index) for c in slot.cells}
        out.extend((x0 + dx, y0 + dy) for dy in range(bh) for dx in range(bw) if (x0 + dx, y0 + dy) not in fronted)
    return tuple(sorted(out))


def plan_slots(ctx: PipelineContext, precincts: tuple[Precinct, ...]) -> dict[str, Slot]:
    """Every building's slot, decided entirely in lattice space.

    Takes PRECINCTS, not a `Lattice`, and deliberately: a big lot's block gets
    no interior stub, so `plan_lattice` needs `solid_blocks(plan_slots(...))`
    as an input. Zoning therefore runs BETWEEN precincts and lines, and the
    prefix sum is still the last thing that happens.

    Precincts in `pid` order, units in lineage order, slots by the packer. The
    unit's members take consecutive slots from a single running index over the
    precinct's blocks, so a group that outgrows one block continues into the
    next rather than scattering.
    """
    rank_of, block_of, big = placement_inputs(ctx)
    out: dict[str, Slot] = {}
    for p in sorted(precincts, key=lambda p: p.pid):
        capacity = p.block_cells
        units = _units(p.members, rank_of, block_of, big, capacity)
        placed = pack_units(tuple(u.size for u in units), capacity)
        for unit, (block, first) in zip(units, placed, strict=False):
            base = block * capacity + first
            if unit.gid.startswith("\x00big\x00"):
                out[unit.members[0]] = whole_block_slot(p, block)
                continue
            for i, key in enumerate(unit.members):
                n = base + i
                out[key] = block_slots(p, n // capacity)[n % capacity]
    return out


# --- the orchestration; frontage geometry is `town_frontage` ---------------


def solid_blocks(slot_of: dict[str, Slot]) -> frozenset[tuple[int, int]]:
    """The NW cell of every block one building consumes whole — `plan_lattice`'s
    `solid` argument, and the whole of "ringed by streets, never threaded
    through". Without it the suburban cul-de-sac stub lands inside a big lot."""
    return frozenset(slot.block for slot in slot_of.values() if len(slot.cells) > 1)


def plan_zoning(ctx: PipelineContext, lattice: Lattice, tiles: TileMap, cover: LineCover | None = None) -> ZonePlan:
    """Slots, then the single conversion of them into tiles.

    `tiles` is spike 1's `resolve_coordinates` output and is READ here, never
    recomputed — the prefix sum stays the one and only place lattice indices
    become coordinates, which is what made hierarchy widths cheap.
    """
    slot_of = plan_slots(ctx, lattice.precincts)
    lot_xy: dict[str, tuple[int, int]] = {}
    door_of: dict[str, tuple[tuple[int, int], str]] = {}
    for key in sorted(slot_of):
        slot = slot_of[key]
        x, y, _w, _h = lot_rect(slot, tiles, cover)
        lot_xy[key] = (x, y)
        door_of[key] = door_tile(slot, tiles)
    return ZonePlan(slot_of=slot_of, lot_xy=lot_xy, door_of=door_of)
