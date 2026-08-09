from tycoon_city.sim.city import CityMap, Lot
from tycoon_city.sim.layout import DistrictPlan
from tycoon_city.sim.tiles import TileKind, ZoneStyle


def test_zone_and_tile_members():
    assert {z.name for z in ZoneStyle} == {"INDUSTRIAL", "COMMERCIAL", "RESIDENTIAL"}
    assert {t.name for t in TileKind} == {
        "GRASS",
        "ROAD",
        "POWER_LINE",
        "PLANT",
        "LOT",
        "WATER",
    }


def test_lot_defaults():
    lot = Lot(object_key="raw.orders", x=2, y=3, zone_style=ZoneStyle.INDUSTRIAL, target_density=5)
    assert lot.density == 0
    assert lot.powered is False


def test_citymap_holds_grid():
    tiles = [[TileKind.GRASS for _ in range(4)] for _ in range(4)]
    city = CityMap(
        width=4,
        height=4,
        tiles=tiles,
        lots={},
        plant_xy=(2, 2),
        district_of={},
    )
    assert city.tiles[0][0] is TileKind.GRASS
    assert city.plant_xy == (2, 2)
    assert city.edge_rates == {}  # defaults empty; apply_signals populates it


def test_citymap_carries_the_district_plan():
    """A renderer needs district footprints, which the tile grid cannot express.

    Defaults to empty so hand-built CityMaps stay valid; the generator fills it
    from the plan it already holds, rather than a consumer re-deriving it via
    plan_layout(ctx) and hoping the two agree.
    """
    tiles = [[TileKind.GRASS for _ in range(4)] for _ in range(4)]
    bare = CityMap(width=4, height=4, tiles=tiles, lots={}, plant_xy=(2, 2), district_of={})
    assert bare.districts == ()

    plan = DistrictPlan(schema="raw", x=1, y=1, w=3, h=2)
    with_districts = CityMap(
        width=4,
        height=4,
        tiles=tiles,
        lots={},
        plant_xy=(2, 2),
        district_of={},
        districts=(plan,),
    )
    assert with_districts.districts == (plan,)
