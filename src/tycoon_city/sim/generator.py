"""Paint the planned DAG city onto tiles — the edge IS the street.

`layout.plan_dag_layout` clusters each schema into a lattice neighbourhood
(property S8 by construction — see `town_plan` and `road_junctions`) and
routes every edge door to door over the lattice — geometry is decided there;
this module only paints it. The rules the tests pin:

  V1  Every known edge has a route, and no building stands anywhere on it:
      route interiors are never LOT tiles. The street literally and cleanly
      connects the two.
  V2  The plant and its POWER_LINE trunk feed the city from the western
      utility strip — data enters the city there.
  V3  Every road ENDING is dressed: the planner's street features are
      painted last, which is what gives a plaza its forecourt pavement.
      A naked stub is a failing build — see property S7.

Paint order is the guard: lots and the plant first (unconditional), then
streets over GRASS only — a street can never clobber a building.

Fully deterministic: no randomness, every collection sorted upstream.
"""

import re

from ..catalog.models import PipelineContext
from .city import CityMap, Lot
from .layout import DagPlan, plan_dag_layout
from .tiles import TileKind, ZoneStyle
from .town_streets import feature_tiles

_PLACEHOLDER_DENSITY = 1  # real target density is set later by apply_signals

Tile = tuple[int, int]


def _match_style(schema: str, style_rules: list[tuple[str, ZoneStyle]]) -> ZoneStyle:
    for pattern, style in style_rules:
        if re.search(pattern, schema):
            return style
    return ZoneStyle.RESIDENTIAL


def _paint(tiles: list[list[TileKind]], path: list[Tile] | tuple[Tile, ...], kind: TileKind) -> None:
    """Streets and power lines claim GRASS only — never a building."""
    for x, y in path:
        if tiles[y][x] is TileKind.GRASS:
            tiles[y][x] = kind


def _build(
    ctx: PipelineContext,
    plan: DagPlan,
    style_rules: list[tuple[str, ZoneStyle]],
) -> CityMap:
    tiles = [[TileKind.GRASS for _ in range(plan.width)] for _ in range(plan.height)]
    lots: dict[str, Lot] = {}
    district_of: dict[str, str] = {}

    # 1. Lots and the plant, unconditional and first: nothing may pave them.
    #    Big tables (plan.big_lots) claim their whole 2x2 ground plan.
    big_lots = set(plan.big_lots)
    for obj in sorted(ctx.objects, key=lambda o: o.key):
        x, y = plan.positions[obj.key]
        size = 2 if obj.key in big_lots else 1
        for dx in range(size):
            for dy in range(size):
                tiles[y + dy][x + dx] = TileKind.LOT
        lots[obj.key] = Lot(
            object_key=obj.key,
            x=x,
            y=y,
            zone_style=_match_style(obj.schema, style_rules),
            target_density=_PLACEHOLDER_DENSITY,
            w=size,
            h=size,
        )
        district_of[obj.key] = obj.schema
    px, py = plan.plant_xy
    tiles[py][px] = TileKind.PLANT

    # 2. The utility strip (V2), then every edge's street (V1), then the
    #    lattice tiles no route claimed — still streets.
    _paint(tiles, plan.power_tiles, TileKind.POWER_LINE)
    for pair in sorted(plan.routes):
        _paint(tiles, plan.routes[pair], TileKind.ROAD)
    _paint(tiles, plan.lane_tiles, TileKind.ROAD)
    # The firehouse's civic access road: vehicles must travel on roads, so
    # the station is wired into the network the moment the city has one.
    _paint(tiles, plan.access_road, TileKind.ROAD)
    # Every road ending is dressed, and a plaza's forecourt is PAVEMENT — the
    # only feature tiles that are not already road. Painted last, under the
    # same grass-only guard, so a pad can never eat a building.
    _paint(tiles, feature_tiles(plan.street_features), TileKind.ROAD)

    return CityMap(
        width=plan.width,
        height=plan.height,
        tiles=tiles,
        lots=lots,
        plant_xy=plan.plant_xy,
        district_of=district_of,
        districts=plan.districts,
        edge_routes=dict(plan.routes),
        library_xy=plan.library_xy,
        firehouse_xy=plan.firehouse_xy,
        street_features=plan.street_features,
    )


def generate_city(
    ctx: PipelineContext,
    style_rules: list[tuple[str, ZoneStyle]],
) -> CityMap:
    """Lay out a catalog as a layered city whose streets are its lineage."""
    return _build(ctx, plan_dag_layout(ctx), style_rules)


def refresh(
    city: CityMap,
    new_ctx: PipelineContext,
    style_rules: list[tuple[str, ZoneStyle]],
) -> CityMap:
    # Regenerate deterministically, carrying the current (presentation) density
    # for lots that persist so buildings do not snap.
    new_city = generate_city(new_ctx, style_rules)
    for key, lot in new_city.lots.items():
        previous = city.lots.get(key)
        if previous is not None:
            lot.density = previous.density
    return new_city
