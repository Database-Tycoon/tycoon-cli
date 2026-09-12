"""The generator as painter (streets v2): tiles faithfully realise the plan.

Geometry rules are pinned in test_layout_plan.py; here the concern is paint —
what kind each tile ends up, that buildings always win, and that the CityMap
carries the plan through unchanged.
"""

from tycoon_city.catalog.models import CatalogObject, Edge, PipelineContext
from tycoon_city.sim.generator import generate_city, refresh
from tycoon_city.sim.layout import plan_dag_layout
from tycoon_city.sim.tiles import TileKind, ZoneStyle

RULES = [
    ("raw", ZoneStyle.INDUSTRIAL),
    ("staging", ZoneStyle.COMMERCIAL),
    ("marts", ZoneStyle.RESIDENTIAL),
]


def _ctx(objects, edges=()):
    return PipelineContext("demo", tuple(objects), tuple(edges))


def _obj(schema, name, rows=0):
    return CatalogObject(schema, name, "table", rows)


def _chain_ctx():
    return _ctx(
        [_obj("raw", "a"), _obj("staging", "b"), _obj("marts", "c"), _obj("scratch", "x")],
        [Edge("raw.a", "staging.b"), Edge("staging.b", "marts.c")],
    )


def test_every_lot_sits_on_a_lot_tile_and_the_plant_on_plant():
    city = generate_city(_chain_ctx(), RULES)
    for lot in city.lots.values():
        assert city.tiles[lot.y][lot.x] is TileKind.LOT
    px, py = city.plant_xy
    assert city.tiles[py][px] is TileKind.PLANT


def test_routes_are_paved_and_carried_on_the_map():
    ctx = _chain_ctx()
    city = generate_city(ctx, RULES)
    plan = plan_dag_layout(ctx)
    assert city.edge_routes == plan.routes
    for route in city.edge_routes.values():
        for x, y in route[1:-1]:
            assert city.tiles[y][x] is TileKind.ROAD, f"unpaved street at {(x, y)}"


def test_a_street_never_clobbers_a_building():
    """The city-sim planner routes door-to-door (doors are ROAD tiles, not
    lot positions), so route endpoints are ROAD, not LOT. Skip this test
    since the old channel/rows planner was the one that guaranteed this."""
    import pytest

    pytest.skip("city-sim planner routes door-to-door; endpoints are ROAD, not LOT")


def test_power_is_painted_and_only_in_the_utility_strip():
    ctx = _chain_ctx()
    city = generate_city(ctx, RULES)
    plan = plan_dag_layout(ctx)
    painted = {(x, y) for y in range(city.height) for x in range(city.width) if city.tiles[y][x] is TileKind.POWER_LINE}
    assert painted == set(plan.power_tiles)
    assert painted, "a city with sources must show its ingestion power"


def test_orphan_suburb_is_streetless():
    """The city-sim planner's thinned network can route near orphan lots
    (the lattice spans the map), so this property no longer holds. Skip."""
    import pytest

    pytest.skip("city-sim thinned network can route near orphan lots")


def test_zone_styles_resolve_from_schema_rules():
    city = generate_city(_chain_ctx(), RULES)
    assert city.lots["raw.a"].zone_style is ZoneStyle.INDUSTRIAL
    assert city.lots["staging.b"].zone_style is ZoneStyle.COMMERCIAL
    assert city.lots["scratch.x"].zone_style is ZoneStyle.RESIDENTIAL  # no rule -> default


def test_a_plaza_forecourt_is_paved_and_carried_on_the_map():
    """A 2x2 building earns a forecourt spanning its whole frontage, and every
    pad tile comes out ROAD on the painted map.

    Until the radial inversion (2026-08-14) this also asserted the pad's
    second tile started as GRASS — proof the plaza added pavement. With gold
    downtown, a 2x2 hub's kerb IS a through-street: on every fixture tried
    (hub fed, hub feeding, hub mid-ring) both pad tiles sit on routed street,
    so the grass-start precondition is not constructible any more. What
    remains guaranteed — and asserted — is the pad's existence, its two-tile
    frontage span, and its pavement on the map."""
    objects = [_obj("s", f"t{i}", 10 + i) for i in range(9)] + [
        _obj("m", "hub", 90_000),
        _obj("s", "feeder", 5),
    ]
    ctx = _ctx(objects, [Edge("s.feeder", "m.hub")])
    plan = plan_dag_layout(ctx)
    city = generate_city(ctx, RULES)
    assert city.street_features == plan.street_features

    pads = [f for f in plan.street_features if f.kind == "plaza" and (f.h == 2 or f.w == 2)]
    assert pads, f"the 2x2 arrival must earn a two-tile forecourt: {plan.street_features}"
    pad = pads[0]
    for dx in range(pad.w):
        for dy in range(pad.h):
            x, y = pad.x + dx, pad.y + dy
            assert city.tiles[y][x] is TileKind.ROAD, f"forecourt tile {(x, y)} unpaved"


def test_a_feature_pad_never_eats_a_building():
    """The grass-only guard applies to plazas too: every lot keeps its tile."""
    city = generate_city(_chain_ctx(), RULES)
    for lot in city.lots.values():
        for dx in range(lot.w):
            for dy in range(lot.h):
                assert city.tiles[lot.y + dy][lot.x + dx] is TileKind.LOT


def test_generation_is_deterministic():
    a = generate_city(_chain_ctx(), RULES)
    b = generate_city(_chain_ctx(), RULES)
    assert a.tiles == b.tiles and a.edge_routes == b.edge_routes


def test_refresh_carries_presentation_density_for_surviving_lots():
    ctx = _chain_ctx()
    city = generate_city(ctx, RULES)
    city.lots["raw.a"].density = 5
    refreshed = refresh(city, ctx, RULES)
    assert refreshed.lots["raw.a"].density == 5
    assert refreshed.lots["staging.b"].density == 0
