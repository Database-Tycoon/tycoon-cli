"""Streets v5 as a real planner: schema neighbourhoods on an S8-clean lattice.

Stephen, 2026-08-07: *"The buildings cant be lined up linearly like that"*, then
*"You cant have two consecutive intersection tiles"*, then — after being shown a
spike sheet he could not drive — *"Im not seeing the clustering of schemas that I
asked for."* This module is the answer to the last one: it produces a real
`DagPlan`, so the app, the exporter and every overlay run on the clustered
layout instead of a PNG.

**Opt-in only.** `DATABASE_TYCOON_PLANNER=v5` selects it in `generator.generate_city`;
unset, `plan_dag_layout` (v4) runs exactly as before, so the `city.json` golden
and the contract tests are untouched. This is deliberately a FLAG and not a
replacement: v5 has known gaps (below) and v4 is what the contract was frozen
against.

What it reuses, and why that matters: the whole precinct -> lattice -> slots ->
frontage chain already exists and already satisfies property S8 by construction
(0 violations, every intersection isolated, measured on both catalogs at both
cell sizes). Streets here are lattice lines, so a contiguous paved area cannot
occur — the defect that made the v4 city read as a plaza with junction markings
on every square.

What it changes: precincts are keyed by SCHEMA, not `(depth, schema)`. Depth
only ORDERS the neighbourhoods west to east; a schema spanning three depths
becomes ONE blob. Stephen chose that from the mockups knowing some streets then
run westward.

Honest gaps against v4, all visible rather than hidden:

  * Lot footprints are 1x1 (2x2 for the big ones) anchored at the tile that
    touches the lot's own door, because `DagPlan` cannot express a 3x2 lot.
    The block keeps its shape; the building sits in one corner of it.
  * Routes are shortest paths over the lattice, not v4's channel trunks, so
    the merge-into-one-trunk look is gone. Lane widths are not modelled.
  * `edges.rate`-driven widening, the pass-through highway rows and the
    orphan suburb are v4 concepts with no v5 equivalent yet; orphans get
    ordinary neighbourhood land here, which is arguably more honest.

Imports no pygame and holds no rendering concepts.
"""

from __future__ import annotations

import os
from collections import deque
from dataclasses import replace
from fractions import Fraction
from math import isqrt

from ..catalog.models import PipelineContext
from .layout import _known_edges, compute_depths
from .town_blocks import (
    Precinct,
    TileMap,
    plan_lattice,
    resolve_coordinates,
)
from .town_frontage import door_tile, lot_rect, segment_cover
from .town_plan import DagPlan, DistrictPlan
from .town_rows import MARGIN, PLANT_X, TRUNK_X, big_lots
from .town_streets import plan_street_features
from .town_texture import fit_blocks, texture_for
from .town_zoning import block_demand, plan_slots, solid_blocks

ENV_FLAG = "DATABASE_TYCOON_PLANNER"
V5 = "v5"

# The lattice is shifted east by this much so the plant, the power trunk and the
# civic strip keep the western margin they have always had. v4's FIRST_COL_X is
# the same idea; naming it separately keeps the two planners' constants apart.
WEST_MARGIN = 6
CELL_SIZE = 2  # spike decision, 2026-08-06: cell 1 reads as a circuit board
NEIGHBOURHOOD_GAP = 1  # empty cells between blobs: Stephen's "mild ~2x" gap

Tile = tuple[int, int]


def v5_selected() -> bool:
    """Read the flag at CALL time, never at import: a test that sets the env var
    would otherwise race module import order and pass or fail by accident."""
    return os.environ.get(ENV_FLAG, "").strip().lower() == V5


# --- precincts: one per schema, ordered by depth ---------------------------


def schema_precincts(ctx: PipelineContext, gap: int = NEIGHBOURHOOD_GAP) -> tuple[Precinct, ...]:
    """One placed precinct per schema, west to east by the schema's mean depth.

    `town_blocks.plan_precincts` keys on `(depth, schema)`; this keys on schema
    alone. Kept here rather than as a parameter over there because
    `town_blocks.py` sits at 489 lines against the 500-line law and must be
    SPLIT at its next change, not grown by a second grouping rule.
    """
    keys = sorted(obj.key for obj in ctx.objects)
    if not keys:
        return ()
    schema_of = {obj.key: obj.schema for obj in ctx.objects}
    depths = compute_depths(ctx)
    max_depth = max(depths[k] for k in keys)
    size_band = block_demand(ctx)

    members_of: dict[str, list[str]] = {}
    for key in keys:
        members_of.setdefault(schema_of[key], []).append(key)

    def mean_depth(members: list[str]) -> Fraction:
        """Exact, never a float: this decides geometry, and a tie that resolved
        differently per machine would move whole neighbourhoods."""
        return Fraction(sum(depths[k] for k in members), len(members))

    sized: list[Precinct] = []
    for schema in sorted(members_of, key=lambda s: (mean_depth(members_of[s]), s)):
        members = tuple(sorted(members_of[schema]))
        depth = int(mean_depth(list(members)))
        texture = texture_for(depth, max_depth)
        shape, blocks_x, blocks_y, capacity = fit_blocks(texture, lambda s, m=members, t=texture: size_band(m, t, s))
        sized.append(
            Precinct(
                pid=schema,
                schema=schema,
                depth=depth,
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

    # Shelf-pack towards square, wrapping at isqrt of the total land, exactly as
    # plan_precincts does per depth column — a ribbon city was that function's
    # round-1 defect and this would reproduce it.
    target = max(1, isqrt(sum(p.cells_w * p.cells_h for p in sized)))
    placed: list[Precinct] = []
    cx = cy = column_w = 0
    for p in sized:
        if cy and cy + p.cells_h > target:
            cx += column_w + gap
            cy = column_w = 0
        placed.append(replace(p, cell_x=cx, cell_y=cy))
        cy += p.cells_h + gap
        column_w = max(column_w, p.cells_w)
    return tuple(placed)


# --- routing: shortest path over the lattice -------------------------------


def _bfs(road: frozenset[Tile], start: Tile, goal: Tile) -> tuple[Tile, ...]:
    """Shortest lattice path, with a DETERMINISTIC tie-break.

    Neighbours are visited in a fixed N/E/S/W order and the queue is FIFO, so
    equal-length paths always resolve the same way. That is not a nicety: two
    exports of one catalog must produce the same bytes, and a set-iteration
    order would break that on the first rehash.
    """
    if start == goal:
        return (start,)
    if start not in road or goal not in road:
        return ()
    prev: dict[Tile, Tile] = {start: start}
    queue = deque([start])
    while queue:
        at = queue.popleft()
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            nxt = (at[0] + dx, at[1] + dy)
            if nxt in road and nxt not in prev:
                prev[nxt] = at
                if nxt == goal:
                    path = [nxt]
                    while path[-1] != start:
                        path.append(prev[path[-1]])
                    return tuple(reversed(path))
                queue.append(nxt)
    return ()


def _anchor(rect: tuple[int, int, int, int], door: Tile, big: bool) -> Tile:
    """Where the building stands inside its block: the corner touching its door.

    `DagPlan` carries one (x, y) plus a 1x1/2x2 flag, so a 3x2 block cannot be
    filled. Anchoring at the door guarantees the lot keeps its frontage — the
    property spike 2 holds at zero — instead of landing in the block's middle
    with pavement nowhere near it.
    """
    x, y, w, h = rect
    size = 2 if big and w >= 2 and h >= 2 else 1
    ax = min(max(door[0] - (size - 1) if door[0] > x else x, x), x + max(w - size, 0))
    ay = min(max(door[1] - (size - 1) if door[1] > y else y, y), y + max(h - size, 0))
    return ax, ay


def plan_v5_layout(ctx: PipelineContext) -> DagPlan:
    """A full `DagPlan` from the v5 chain. Pure and deterministic: sorted
    everywhere, no wall clock, no unseeded randomness."""
    keys = sorted(obj.key for obj in ctx.objects)
    edges = sorted({(s, d) for s, d in _known_edges(ctx) if s != d})
    depths = compute_depths(ctx)
    connected = sorted({k for pair in edges for k in pair})
    orphans = tuple(k for k in keys if k not in set(connected))

    precincts = schema_precincts(ctx)
    if not precincts:
        return DagPlan(
            width=MARGIN * 2,
            height=MARGIN * 2,
            plant_xy=(PLANT_X, MARGIN),
            positions={},
            routes={},
            power_tiles=(),
            orphans=orphans,
            districts=(),
        )

    slots = plan_slots(ctx, precincts)
    lattice = plan_lattice(precincts, solid=solid_blocks(slots))
    tiles: TileMap = resolve_coordinates(lattice, cell_size=CELL_SIZE)
    cover = segment_cover(lattice)

    def shift(t: Tile) -> Tile:
        return t[0] + WEST_MARGIN, t[1] + MARGIN

    road = frozenset(shift(t) for t in tiles.road_tiles)
    big_keys = big_lots(ctx)

    positions: dict[str, Tile] = {}
    doors: dict[str, Tile] = {}
    big: set[str] = set()
    for key in keys:
        slot = slots.get(key)
        if slot is None:  # a catalog object the zoning found no land for
            continue
        x, y, w, h = lot_rect(slot, tiles, cover)
        door = shift(door_tile(slot, tiles)[0])
        doors[key] = door
        is_big = key in big_keys
        positions[key] = _anchor((x + WEST_MARGIN, y + MARGIN, w, h), door, is_big)
        if is_big and w >= 2 and h >= 2:
            big.add(key)

    # Routes: door to door over the lattice. An edge whose endpoints share a
    # door tile (two lots on one kerb) yields a single-tile route, which is what
    # v4 produces for touching lots too.
    routes: dict[tuple[str, str], tuple[Tile, ...]] = {}
    for src, dst in edges:
        if src in doors and dst in doors:
            path = _bfs(road, doors[src], doors[dst])
            if path:
                routes[(src, dst)] = path

    # Every lattice tile no route used still IS a street, and `lane_tiles` is
    # painted as ROAD — so the whole grid renders and S8 stays measured over the
    # same tile set the lattice guaranteed.
    routed = {t for path in routes.values() for t in path}
    lane_tiles = tuple(sorted(road - routed))

    # The utility strip, west of the lattice: plant at the topmost lot row, a
    # power trunk spanning the city, one stub east per district.
    lot_ys = sorted(y for _, y in positions.values()) or [MARGIN]
    plant_y = lot_ys[0]
    power: list[Tile] = [(PLANT_X + 1, plant_y)]
    power += [(TRUNK_X, y) for y in range(plant_y, lot_ys[-1] + 1)]

    districts: list[DistrictPlan] = []
    for pid, x, y, w, h in sorted(tiles.precinct_rects):
        schema = next((p.schema for p in precincts if p.pid == pid), pid)
        districts.append(DistrictPlan(schema=schema, x=x + WEST_MARGIN, y=y + MARGIN, w=w, h=h))
        # One line per district, from the trunk to its west edge (not one per
        # object — that was v4's rule and it stays v4's rule).
        row = min(max(y + MARGIN + h // 2, plant_y), lot_ys[-1])
        power += [(px, row) for px in range(TRUNK_X + 1, x + WEST_MARGIN)]

    library_xy = (PLANT_X, plant_y + 3)
    firehouse_xy = (PLANT_X, plant_y + 6)
    access = _access_road(road, firehouse_xy)

    features = plan_street_features(
        routes=routes,
        lots=positions,
        big=frozenset(big),
        depth={k: depths[k] for k in connected},
        access_road=access,
        firehouse_xy=firehouse_xy,
    )

    width = max(
        tiles.width + WEST_MARGIN + MARGIN,
        max((x for x, _ in positions.values()), default=MARGIN) + 2 + MARGIN,
    )
    height = max(
        tiles.height + MARGIN * 2,
        max((y for _, y in positions.values()), default=MARGIN) + 2 + MARGIN,
        firehouse_xy[1] + 1 + MARGIN,
    )
    return DagPlan(
        width=width,
        height=height,
        plant_xy=(PLANT_X, plant_y),
        positions=positions,
        routes=routes,
        power_tiles=tuple(power),
        orphans=orphans,
        districts=tuple(districts),
        library_xy=library_xy,
        firehouse_xy=firehouse_xy,
        access_road=access,
        lane_tiles=lane_tiles,
        big_lots=tuple(sorted(big)),
        street_features=features,
    )


def _access_road(road: frozenset[Tile], firehouse_xy: Tile) -> tuple[Tile, ...]:
    """A civic street from the firehouse east to the nearest lattice road.

    The RoadNet rule is absolute — every vehicle class drives on roads — so a
    firehouse with no road touching it is a dispatch that cannot leave.
    """
    if not road:
        return ()
    fx, fy = firehouse_xy
    target = min(road, key=lambda t: (abs(t[0] - fx) + abs(t[1] - fy), t))
    run: list[Tile] = [(x, fy) for x in range(fx + 1, target[0] + 1)]
    step = 1 if target[1] > fy else -1
    run += [(target[0], y) for y in range(fy, target[1] + step, step)]
    seen: set[Tile] = set()
    return tuple(t for t in run if not (t in seen or seen.add(t)))
