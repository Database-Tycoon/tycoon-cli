"""The DAG town plan — the plan object, and the planner that assembles it.

Schema neighbourhoods on an S8-clean lattice. Born as "streets v5" behind an
env flag while the original channel-and-rows planner ("v4") stayed the
default; Stephen dissolved the split on 2026-08-09 — this is now the ONLY
planner, and the version names are retired. The rules it answers to, in his
words (2026-08-07): *"The buildings cant be lined up linearly like that"*,
*"You cant have two consecutive intersection tiles"* (property S8,
`road_junctions.py`), and *"Im not seeing the clustering of schemas that I
asked for."*

How it satisfies them: the precinct -> lattice -> slots -> frontage chain
produces streets as lattice lines, so a contiguous paved area cannot occur —
the defect that made the old city read as a plaza with junction markings on
every square. Precincts are keyed by SCHEMA; the cross-schema chain depth
only ORDERS the neighbourhoods radially (2026-08-14: gold downtown, sources
on the periphery — see `town_precincts.schema_precincts`), so a schema spanning three
depths becomes ONE blob.

Division of labour:

    town_rows      shared site facts: margins, big lots, source rows
    town_precincts one precinct per schema, dealt into rings by depth
    town_blocks    precinct lattice and coordinate resolution
    town_zoning    slots: which block face each object fronts
    town_frontage  doors, lot rectangles, segment cover
    town_streets   street features (aprons, docks, plazas) and their tiles
    town_plan      this module: the DagPlan contract and the planner

`layout` re-exports this API, so `tycoon_city.sim.layout` remains the import
path of record.

Imports no pygame and holds no rendering concepts. Guarded by
tests/sim/test_no_pygame.py via the `layout` re-export.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from ..catalog.models import PipelineContext
from .layout import _known_edges, compute_depths
from .town_blocks import TileMap, plan_lattice, resolve_coordinates
from .town_frontage import door_tile, lot_rect, segment_cover
from .town_precincts import CIVIC_CORE_CELLS, NEIGHBOURHOOD_GAP, schema_precincts
from .town_rows import MARGIN, PLANT_X, TRUNK_X, big_lots
from .town_streets import StreetFeature, feature_tiles, plan_street_features
from .town_zoning import plan_slots, solid_blocks

# The lattice is shifted east by this much so the plant, the power trunk and
# the civic strip keep the western margin they have always had.
WEST_MARGIN = 6
CELL_SIZE = 2  # spike decision, 2026-08-06: cell 1 reads as a circuit board

Tile = tuple[int, int]

__all__ = [
    "CELL_SIZE",
    "CIVIC_CORE_CELLS",
    "MARGIN",
    "NEIGHBOURHOOD_GAP",
    "WEST_MARGIN",
    "DagPlan",
    "DistrictPlan",
    "StreetFeature",
    "plan_dag_layout",
    "schema_precincts",
]


@dataclass(frozen=True)
class DistrictPlan:
    """A schema's bounding rectangle around its placed lots (padded by one).
    Rectangles may overlap channels and each other — they are ground tint and
    labels, not exclusive land; only lots and roads claim tiles."""

    schema: str
    x: int
    y: int
    w: int
    h: int


@dataclass(frozen=True)
class DagPlan:
    width: int
    height: int
    plant_xy: tuple[int, int]
    positions: dict[str, tuple[int, int]]  # every real object, orphans included
    # Full tile path per edge, lot to lot, orthogonal steps: THE street.
    routes: dict[tuple[str, str], tuple[tuple[int, int], ...]]
    power_tiles: tuple[tuple[int, int], ...]
    orphans: tuple[str, ...]
    districts: tuple[DistrictPlan, ...]
    # Civic buildings on the western utility strip, below the plant: the
    # public library (where the city's context/documentation lives) and the
    # firehouse (where responses to fires dispatch from).
    library_xy: tuple[int, int] = (1, 1)
    firehouse_xy: tuple[int, int] = (1, 1)
    # The firehouse's access road: a civic street from the station to the
    # nearest lineage road, because vehicles must travel on roads. Empty when
    # the city has no roads at all.
    access_road: tuple[tuple[int, int], ...] = ()
    # Lattice tiles no route used — still streets, painted as ROAD, so the
    # whole grid renders and S8 stays measured over the tile set the lattice
    # guaranteed.
    lane_tiles: tuple[tuple[int, int], ...] = ()
    # Lots with a 2x2 ground plan — the top decile of this catalog's row
    # counts. Their position stays the NW anchor; they grow east and south.
    big_lots: tuple[str, ...] = ()
    # How each road is allowed to END — an apron, a dock or a plaza at every
    # route endpoint (see `town_streets.StreetFeature` and
    # docs/road-grammar.md). Sorted; derived from routes and lot metadata.
    street_features: tuple[StreetFeature, ...] = ()


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


def plan_dag_layout(ctx: PipelineContext) -> DagPlan:
    """Plan the layered city. Pure and deterministic: sorted everywhere, no
    wall clock, no unseeded randomness."""
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
    # NOTE, measured 2026-08-10: do NOT hand resolve_coordinates 2-wide
    # ring arterials — a 2-wide street is wall-to-wall degree>=3 tiles under
    # the junction grammar (185 S8 violations, clump 67, on the ring
    # fixture). Width stays 1 until the road grammar itself learns lanes.
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

    # The lattice can SPLIT under the staggered ring placement — a precinct
    # can rest on the bounding-box line without its frame overlapping any
    # inner segment (measured: random seed 5 left 8 of 13 edges unroutable).
    # So before any routing, the doors are joined into one drivable body:
    # connectors prefer the lattice and may cut across open ground (never a
    # building) when the lattice itself is the problem.
    footprints: set[Tile] = set()
    for key, (lx, ly) in positions.items():
        size = 2 if key in big else 1
        footprints |= {(lx + i, ly + j) for i in range(size) for j in range(size)}
    from .town_network import bridge_lattice, bfs_route, connected_street_net

    open_ground = frozenset(
        (x, y)
        for x in range(1, tiles.width + WEST_MARGIN + MARGIN)
        for y in range(1, tiles.height + 2 * MARGIN)
        if (x, y) not in footprints and (x, y) not in road
    )
    drivable = bridge_lattice(road, set(doors.values()), open_ground=open_ground)

    # Routes: door to door over the drivable body. An edge whose endpoints
    # share a door tile (two lots on one kerb) yields a single-tile route.
    routes: dict[tuple[str, str], tuple[Tile, ...]] = {}
    for src, dst in edges:
        if src in doors and dst in doors:
            path = bfs_route(drivable, doors[src], doors[dst])
            if path:
                routes[(src, dst)] = path

    # Streets exist where something NEEDS them (pavement-fraction defect,
    # measured 2026-08-10: painting the whole lattice left road at ~85% of
    # used land on dogfood). The kept network is every route tile, every
    # lot's door — frontage is a law — plus the shortest connectors that
    # make the network ONE component, because every vehicle class drives on
    # roads and a fire response must be able to reach every building.
    # Everything else returns to grass.
    routed = {t for path in routes.values() for t in path}
    street_net = connected_street_net(drivable, routed | set(doors.values()), open_ground=open_ground)
    lane_tiles = tuple(sorted(street_net - routed))

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
        # One line per district, from the trunk to its west edge — not one per
        # object.
        row = min(max(y + MARGIN + h // 2, plant_y), lot_ys[-1])
        power += [(px, row) for px in range(TRUNK_X + 1, x + WEST_MARGIN)]

    # The civic core: plant, library and firehouse cluster DOWNTOWN, on the
    # grass the ring placement reserved in the centre (Stephen, 2026-08-10).
    # A column of three, anchored at the first spot scanning outward from the
    # map centre where the whole column sits on open ground.
    occupied = set(street_net)
    for key, (lx, ly) in positions.items():
        size = 2 if key in big else 1
        occupied |= {(lx + i, ly + j) for i in range(size) for j in range(size)}
    cx0 = tiles.width // 2 + WEST_MARGIN
    cy0 = tiles.height // 2 + MARGIN

    def _civic_anchor() -> Tile:
        for r in range(max(tiles.width, tiles.height)):
            for sx in sorted(range(-r, r + 1), key=lambda v: (abs(v), v)):
                for sy in sorted(range(-r, r + 1), key=lambda v: (abs(v), v)):
                    if max(abs(sx), abs(sy)) != r:
                        continue
                    x, y = cx0 + sx, cy0 + sy - 2
                    column = {(x, y), (x, y + 2), (x, y + 4)}
                    if y >= 1 and not column & occupied:
                        return (x, y)
        return (cx0, cy0)  # degenerate map: overlap beats a crash

    plant_xy = _civic_anchor()
    library_xy = (plant_xy[0], plant_xy[1] + 2)
    firehouse_xy = (plant_xy[0], plant_xy[1] + 4)
    lot_tiles = occupied - set(street_net)
    from .town_network import access_road

    access = access_road(
        frozenset(street_net),
        firehouse_xy,
        blocked=frozenset(lot_tiles | {plant_xy, library_xy}),
    )

    features = plan_street_features(
        routes=routes,
        lots=positions,
        big=frozenset(big),
        depth={k: depths[k] for k in connected},
        access_road=access,
        firehouse_xy=firehouse_xy,
        doors=doors,
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

    # Power radiates from the central plant along the four compass axes to
    # the city edge — data enters downtown and feeds outward, which is the
    # radial story told in wire. It yields to everything already there:
    # streets, the access road, feature pads, the civic buildings and lots
    # (a line skips the crossing tile and resumes on the far side).
    px_, py_ = plant_xy
    power += [(px_, y) for y in range(MARGIN, py_)]
    power += [(px_, y) for y in range(firehouse_xy[1] + 2, height - MARGIN)]
    power += [(x, py_) for x in range(MARGIN, px_)]
    power += [(x, py_) for x in range(px_ + 1, width - MARGIN)]
    keep_off = set(access) | set(feature_tiles(features)) | occupied | {plant_xy, library_xy, firehouse_xy}
    power = [t for t in power if t not in keep_off]

    return DagPlan(
        width=width,
        height=height,
        plant_xy=plant_xy,
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
