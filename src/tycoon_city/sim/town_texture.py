"""Streets v5, SPIKE 3: TEXTURE -> BLOCK SHAPE, and block shape from DEMAND.

**Not wired into anything.** Split out of `town_blocks` this round because that
is where the seam actually is: `town_blocks` decides where land goes and which
lines enclose it, and this module decides what one piece of that land is SHAPED
like. Reachable from `town_blocks`, `town_zoning` and `scripts/` and nowhere
else.

Spikes 1 and 2 gave every block of a texture the SAME shape, and that is what
made the plan bigger than v4 on a sparse catalog: a block holds 4-8 lots, a
typical schema band wants 1-4, so half of every block came out bare land
(block fill 47%). Districts must stay 1:1 with schemas — that mapping is
load-bearing for the product and is not up for trade — so the band cannot be
merged into a neighbour's precinct. The block has to shrink to the band
instead.

The rule this module implements, and the two things it is not allowed to break:

  **grain, not size, is the texture.** What the eye reads at thumbnail size is
  that industrial land runs WIDER than tall, downtown is square, and suburban
  runs TALLER than wide. So a texture's candidate shapes are all the same
  handedness: industrial never squares off, suburban never flattens, and
  downtown never leaves 2x2 at all (its tell is the tight square grid; a
  trimmed downtown domino would be indistinguishable from a trimmed industrial
  one). Trimming spends the block's LONG axis first and its short axis last,
  so a 3-lot industrial band becomes a 3x1 bar — still the longest run on the
  sheet — rather than a square.

  **short axis <= `MAX_INTERIOR_SHORT`.** Every candidate is at most two cells
  on its short axis, which is the whole of "every lot fronts a street by
  construction" (see `town_zoning.block_slots`, where the guarantee is cashed).
  A one-cell-thick block is the degenerate end of that: every cell touches both
  of the block's long sides, so it has ONE frontage face rather than two.

Choice is by WASTE, ties to the biggest block: waste is what this spike exists
to remove, and among shapes that waste the same the largest block buys the
least pavement per lot. Integer arithmetic, fixed candidate order, no floats —
the fit has to fall out the same way under any input permutation.
"""

from __future__ import annotations

from collections.abc import Callable

# Every enclosed region is at most this many cells on its SHORT axis, so "every
# lot fronts a street" holds by CONSTRUCTION and not by a repair pass: a cell in
# a 4x2 interior still has the block's north or south line on one of its own
# edges. Round 1 held BOTH axes to 2 and the interior lines that forces made
# every downtown block a plus-sign of road around four one-tile lots — the
# circuit board. Raising it needs the shapes below re-derived AND
# `town_zoning.block_slots`, where the guarantee is cashed.
MAX_INTERIOR_SHORT = 2

INDUSTRIAL = "industrial"
DOWNTOWN = "downtown"
SUBURBAN = "suburban"

# The FULL block per texture — the shape a band with enough buildings to fill
# one gets, and the head of its candidate list.
#   industrial 4x2  horizontal grain, longest run, fewest streets
#   downtown   2x2  tight grid: smallest blocks, most frontage, 4-ways
#   suburban   2x4  grain turns 90 degrees, plus one cul-de-sac stub
BLOCK_CELLS = {INDUSTRIAL: (4, 2), DOWNTOWN: (2, 2), SUBURBAN: (2, 4)}

# Candidate shapes, biggest first, all of one handedness per texture. The long
# axis trims from 4 down to 2 at full thickness and then the block thins to one
# cell and trims again — so the smallest industrial block is a 2x1 domino lying
# down and the smallest suburban one is a 1x2 standing up, and the two are still
# telling you which district you are looking at. Downtown trims the only way a
# square can, to 1x1: a two-cell downtown domino would be indistinguishable from
# a trimmed industrial or suburban one, and the render is emphatic that leaving
# downtown at 2x2 was worse than trimming it — a one- or two-object band on a
# 2x2 block is three-quarters bare slate, and after the first trim those were
# the largest fields of empty land left on the whole bench (`random-6`).
BLOCK_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    INDUSTRIAL: ((4, 2), (3, 2), (4, 1), (3, 1), (2, 1)),
    DOWNTOWN: ((2, 2), (1, 1)),
    SUBURBAN: ((2, 4), (2, 3), (1, 4), (1, 3), (1, 2)),
}


def texture_for(depth: int, max_depth: int) -> str:
    """Texture is DERIVED from depth, never styled. Depth 0 wins outright, so a
    catalog with no lineage (max_depth 0) is all industrial, not all suburb."""
    if depth == 0:
        return INDUSTRIAL
    return SUBURBAN if depth == max_depth else DOWNTOWN


def block_capacity(shape: tuple[int, int]) -> int:
    """Lots one block of this shape holds — its cell count. Every cell of every
    candidate shape is fronted, so capacity and area are the same number."""
    return shape[0] * shape[1]


def arrange(blocks: int, cell_w: int, cell_h: int) -> tuple[int, int]:
    """Blocks in the rectangle whose CELL footprint is nearest to square.

    Round 1 arranged near-square in BLOCKS, only the same thing when the block
    is square: a suburban precinct of 2x4 blocks came out 1:2 on the ground.
    The cost is squareness error PLUS wasted cells, not squareness with waste
    as a tiebreak — cap-500's industrial bands need 4 blocks and
    squareness-first bought 6 (2x3) to save two tiles of aspect, an empty block
    row per precinct stamped down the district. Waste-FIRST is the other
    failure: it takes 1x7 (a 1:3.5 ribbon) over a square 2x4. Ties break
    TALLER; growing east blurs the depth reading."""
    n = max(1, blocks)
    best_key: tuple[int, int] | None = None
    best = (1, n)
    for by in range(1, n + 1):
        bx = -(-n // by)
        w, h = bx * cell_w, by * cell_h
        key = (abs(w - h) + (bx * by - n) * cell_w * cell_h, w - h)
        if best_key is None or key < best_key:
            best_key, best = key, (bx, by)
    return best


def fit_blocks(
    texture: str,
    size_band: Callable[[tuple[int, int]], tuple[int, int, int]],
) -> tuple[tuple[int, int], int, int, int]:
    """`(shape, blocks_x, blocks_y, cells_demanded)` for one band.

    `size_band(shape) -> (cells, blocks, spills)` is asked once per candidate
    rather than once per band, because the answer DEPENDS on the shape: a big
    lot consumes a whole block, so it demands 8 cells on a full industrial block
    and 2 on a domino, and a sibling group that refuses to straddle a street
    costs the tail of the block before it. `town_zoning.block_demand` is the real
    one; the caller's default prices a lot at a cell.

    Cost is `(spills, wasted cells, -block area, shape)`.

    SPILLS first, and it is the one part of this that is a constraint rather
    than a preference: a spill is a group that no longer fits on one block, and
    the sibling block landing on ONE literal city block is a claim spike 2
    already banked. Trimming purely on waste took it from 7 groups of 8 to 4 —
    a 3-object sibling group on 1x1 blocks wastes nothing and scatters over
    three of them. Spilling stays legal (a group can outgrow the biggest block
    there is) but never gets chosen to save a cell.

    Then waste, which is the point of the round. The block-area tiebreak is what
    stops a band with nothing to say about its shape — one big lot, or a demand
    that divides evenly however you cut it — from being handed the smallest
    domino that fits: bigger blocks mean fewer streets per lot, and the full
    shape is the one the texture reads loudest at. `shape` last so the walk is
    total and the fit is a function of the demand alone, not of dict order.
    """
    best: tuple[tuple[int, int, int, tuple[int, int]], tuple[int, int], int, int, int] | None
    best = None
    for shape in BLOCK_SHAPES[texture]:
        cells, blocks, spills = size_band(shape)
        blocks_x, blocks_y = arrange(blocks, *shape)
        have = blocks_x * blocks_y * block_capacity(shape)
        key = (spills, have - cells, -block_capacity(shape), shape)
        if best is None or key < best[0]:
            best = (key, shape, blocks_x, blocks_y, cells)
    assert best is not None  # BLOCK_SHAPES is never empty for a real texture
    _key, shape, blocks_x, blocks_y, cells = best
    return shape, blocks_x, blocks_y, cells
