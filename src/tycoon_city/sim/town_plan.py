"""The DAG town plan — the plan object, and the pass that assembles it.

Split out of `layout.py` (the 500-line rule), and split again on 2026-08-05
when it hit the rule itself. Lineage STRUCTURE (depths, SCC condensation,
orphans) stays in `layout`; turning that structure into geometry is shared:

    town_rows     columns, bands, affinity clusters, footprints, ROWS
    town_streets  channels, trunks, tile routes, merged lane width, ENDINGS
    town_plan     this module: the DagPlan contract, plus the utility strip,
                  the civic buildings, the orphan suburb and the district
                  plates — and the orchestration that runs the two halves.

`layout` re-exports this whole API, so `tycoon_city.sim.layout` remains the import
path of record.

Imports no pygame and holds no rendering concepts. Guarded by
tests/sim/test_no_pygame.py via the `layout` re-export.
"""

from dataclasses import dataclass

from ..catalog.models import PipelineContext
from .layout import _known_edges, compute_depths
from .town_rows import BAND_GAP, MARGIN, NEIGHBOUR_PITCH, PLANT_X, TRUNK_X, plan_site
from .town_streets import (
    H_LANE_CAP,
    LANE_CAP,
    TRACK_PITCH,
    StreetFeature,
    plan_street_features,
    plan_streets,
)

ROW_PITCH = 3  # dummy/pass-through pitch, and the unit `rows_and_grid` tests use
SUBURB_PER_ROW = 16  # orphan suburb wraps into rows of this many
GRID_MIN = 16

# Re-exported for `layout`'s public API: these constants live with the pass
# that owns them, but every caller has always imported them from here.
__all__ = [
    "BAND_GAP",
    "GRID_MIN",
    "H_LANE_CAP",
    "LANE_CAP",
    "MARGIN",
    "NEIGHBOUR_PITCH",
    "ROW_PITCH",
    "SUBURB_PER_ROW",
    "TRACK_PITCH",
    "DagPlan",
    "DistrictPlan",
    "StreetFeature",
    "plan_dag_layout",
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
    # Extra ROAD tiles that widen merged runs to their combined lane count.
    # Routes stay centre-line paths; these are the additional lanes beside
    # them, in space the channel allocation reserved.
    lane_tiles: tuple[tuple[int, int], ...] = ()
    # Lots with a 2x2 ground plan — the top decile of this catalog's row
    # counts. Their position stays the NW anchor; they grow east and south.
    big_lots: tuple[str, ...] = ()
    # Streets v4: how each road is allowed to END — an apron, a dock or a
    # plaza at every route endpoint (see `town_streets.StreetFeature` and
    # docs/road-grammar.md). Sorted; derived from routes and lot metadata.
    street_features: tuple[StreetFeature, ...] = ()


def plan_dag_layout(ctx: PipelineContext) -> DagPlan:
    """Plan the layered city. Pure and deterministic: sorted everywhere."""
    keys = sorted(obj.key for obj in ctx.objects)
    edges = sorted({(s, d) for s, d in _known_edges(ctx) if s != d})
    depths = compute_depths(ctx)
    connected = sorted({k for pair in edges for k in pair})
    orphans = tuple(k for k in keys if k not in set(connected))
    depth = {k: depths[k] for k in connected}

    site = plan_site(ctx, edges, depth)
    streets = plan_streets(site, depth)
    big = site.big
    positions = dict(streets.positions)
    routes = streets.routes

    # The utility strip: plant beside the TOPMOST source row (north — the
    # orphan suburb grows south, and a tall orphan in front of the plant
    # occludes the landmark from the default camera), POWER_LINE trunk
    # spanning the source rows, a stub east to each source lot.
    power: list[tuple[int, int]] = []
    plant_y = MARGIN
    sources = [k for k in connected if depth[k] == 0]
    if sources:
        rows = sorted(positions[k][1] for k in sources)
        plant_y = rows[0]
        power.append((PLANT_X + 1, plant_y))
        power += [(TRUNK_X, sy) for sy in range(rows[0], rows[-1] + 1)]
        power += [(TRUNK_X + 1, sy) for sy in rows]

    library_xy = (PLANT_X, plant_y + 3)
    firehouse_xy = (PLANT_X, plant_y + 6)
    access_road = _access_road(
        routes,
        streets.lane_tiles,
        positions,
        big,
        power,
        plant_y,
        library_xy,
        firehouse_xy,
        streets.right_edge,
    )

    # The orphan suburb: south of the city AND below the civic strip (the
    # access road must never brush a streetless orphan), wrapped rows.
    main_bottom = max((y for _, y in positions.values()), default=MARGIN)
    suburb_y = max(main_bottom + ROW_PITCH + 1, firehouse_xy[1] + 3)
    for i, key in enumerate(orphans):
        positions[key] = (
            MARGIN + 2 * (i % SUBURB_PER_ROW),
            suburb_y + 2 * (i // SUBURB_PER_ROW),
        )

    # Every road ending gets dressed once the suburb is placed, so a plaza pad
    # is checked against every lot on the map (property S7 fails the build on
    # any naked stub that is left).
    street_features = plan_street_features(
        routes=routes,
        lots={k: positions[k] for k in keys},
        big=big,
        depth=depth,
        access_road=access_road,
        firehouse_xy=firehouse_xy,
    )

    real_xs = [positions[k][0] + (1 if k in big else 0) for k in keys] or [MARGIN]
    real_ys = [positions[k][1] + (1 if k in big else 0) for k in keys] or [MARGIN]
    width = max(GRID_MIN, streets.right_edge + MARGIN, max(real_xs) + 1 + MARGIN)
    height = max(GRID_MIN, max(real_ys) + 1 + MARGIN, firehouse_xy[1] + 1 + MARGIN)

    districts = _districts(ctx, keys, positions, set(connected), big, width, height)

    # Dummies served their purpose (row reservations + route shape); only
    # real objects leave the planner.
    positions = {k: positions[k] for k in keys}

    return DagPlan(
        width=width,
        height=height,
        plant_xy=(PLANT_X, plant_y),
        positions=positions,
        routes=routes,
        power_tiles=tuple(power),
        orphans=orphans,
        districts=districts,
        lane_tiles=streets.lane_tiles,
        library_xy=library_xy,
        firehouse_xy=firehouse_xy,
        access_road=access_road,
        big_lots=tuple(sorted(big)),
        street_features=street_features,
    )


def _access_road(
    routes: dict[tuple[str, str], tuple[tuple[int, int], ...]],
    lane_tiles: tuple[tuple[int, int], ...],
    positions: dict[str, tuple[int, int]],
    big: frozenset[str],
    power: list[tuple[int, int]],
    plant_y: int,
    library_xy: tuple[int, int],
    firehouse_xy: tuple[int, int],
    right_edge: int,
) -> tuple[tuple[int, int], ...]:
    """The firehouse's access road: BFS over GRASS (deterministic neighbour
    order) from the station to the nearest road tile. Power lines, lots and the
    plant block it; no roads in the city -> no access road."""
    road_tiles = {t for route in routes.values() for t in route[1:-1]}
    road_tiles |= set(lane_tiles)
    if not road_tiles:
        return ()
    blocked = (
        {
            (px0 + dx, py0 + dy)
            for k, (px0, py0) in positions.items()
            for dx in range(2 if k in big else 1)
            for dy in range(2 if k in big else 1)
        }
        | set(power)
        | {(PLANT_X, plant_y), library_xy}
    )
    from collections import deque

    start = firehouse_xy
    frontier = deque([start])
    came: dict[tuple[int, int], tuple[int, int]] = {start: start}
    found: tuple[int, int] | None = None
    # Generous bound: the search space is the utility strip + margins.
    while frontier and found is None:
        cx, cy = frontier.popleft()
        for dx, dy in ((1, 0), (0, -1), (0, 1), (-1, 0)):
            nxt = (cx + dx, cy + dy)
            if nxt in came or nxt in blocked:
                continue
            if not (0 <= nxt[0] < right_edge + MARGIN and 0 <= nxt[1] < 4000):
                continue
            came[nxt] = (cx, cy)
            if nxt in road_tiles:
                found = nxt
                break
            frontier.append(nxt)
    if found is None:
        return ()
    path = [found]
    while path[-1] != start:
        path.append(came[path[-1]])
    # Station tile itself is the firehouse, not road; keep the rest.
    return tuple(reversed(path[:-1]))


def _districts(
    ctx: PipelineContext,
    keys: list[str],
    positions: dict[str, tuple[int, int]],
    connected: set[str],
    big: frozenset[str],
    width: int,
    height: int,
) -> tuple[DistrictPlan, ...]:
    schema_of = {obj.key: obj.schema for obj in ctx.objects}
    districts = []
    for schema in sorted({obj.schema for obj in ctx.objects}):
        members = [k for k in keys if schema_of[k] == schema]
        # The plate marks the schema's working NEIGHBOURHOOD: suburb orphans
        # are excluded whenever the schema has connected lots, or one stray
        # table stretches the plate across the whole map and washes every
        # band into a single blur. An all-orphan schema keeps its plate.
        in_city = [k for k in members if k in connected]
        xs: list[int] = []
        ys: list[int] = []
        for k in in_city or members:
            kx, ky = positions[k]
            reach = 1 if k in big else 0
            xs += [kx, kx + reach]
            ys += [ky, ky + reach]
        districts.append(
            DistrictPlan(
                schema=schema,
                x=max(0, min(xs) - 1),
                y=max(0, min(ys) - 1),
                w=min(width, max(xs) + 2) - max(0, min(xs) - 1),
                h=min(height, max(ys) + 2) - max(0, min(ys) - 1),
            )
        )
    return tuple(districts)
