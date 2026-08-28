"""Property S7's detector: no naked stub — a road that just stops.

`find_naked_stubs` used to be an inline check at the end of
`plan_street_features` that raised `ValueError` on a violation, which meant a
real geometry defect turned `/city.json` into a 500 and the exporter into a
traceback. It is now a pure detector: it reports violating tiles instead of
raising, so callers on the request path can keep going and tests can assert
on the result directly.
"""


def test_find_naked_stubs_reports_a_degree_one_tile():
    """A three-tile spur off a lot at (-1, 0): (0,0) touches the lot (degree
    2), (1,0) sits between two road tiles (degree 2), but (2,0) touches only
    (1,0) (degree 1) — the naked stub.

    (The lot anchor matters: with no lot tile behind it, (0,0) would ALSO be
    degree 1 and the detector would correctly report both ends — a variant of
    this fixture with `lot_tiles=set()` asserts a single-element result and
    fails for that reason, not a detector bug.)
    """
    from tycoon_city.sim.town_streets import find_naked_stubs

    road = {(0, 0), (1, 0), (2, 0)}
    lot = {(-1, 0)}
    assert find_naked_stubs(road, lot, ()) == ((2, 0),)


def test_find_naked_stubs_exempts_every_tile_of_a_multi_tile_feature():
    """The old inline check exempted only a feature's anchor, so a 2x1 plaza
    reported its own second tile as a violation. (0,0) is anchored to a lot
    at (-1, 0), same as the fixture above, so the plaza's exemption is the
    only thing under test here."""
    from tycoon_city.sim.town_streets import StreetFeature, find_naked_stubs

    road = {(0, 0), (1, 0), (2, 0)}
    lot = {(-1, 0)}
    plaza = StreetFeature(kind="plaza", x=1, y=0, w=2, h=1)
    assert find_naked_stubs(road, lot, (plaza,)) == ()


def test_find_naked_stubs_exempts_every_tile_of_a_vertical_multi_tile_feature():
    """The shipped code only ever emits a multi-tile feature as `w=1, h=2`
    (`dress()`'s `y, h = lots[key][1], 2` branch for a 2x2 lot's frontage) —
    never `w=2, h=1`. The horizontal-plaza test above exercises `range(f.w)`
    but leaves `range(f.h)` uncovered, which is the axis the real bug lives
    on. This is the same vertical spur anchored to a lot at (0, -1), so the
    exemption is the only thing under test."""
    from tycoon_city.sim.town_streets import StreetFeature, find_naked_stubs

    road = {(0, 0), (0, 1), (0, 2)}
    lot = {(0, -1)}
    plaza = StreetFeature(kind="plaza", x=0, y=1, w=1, h=2)
    assert find_naked_stubs(road, lot, (plaza,)) == ()


def test_planning_a_naked_stub_returns_features_instead_of_raising():
    """A geometry defect must never reach the request path as an exception.

    `plan_street_features` keeps its real signature (routes/lots/big/depth/
    access_road/firehouse_xy) — the brief's two-set sketch doesn't match it.
    'b' is deliberately left out of `lots`: that is exactly the kind of
    upstream data bug that used to surface as a naked stub at (3, 0) (its
    road tile has one neighbour, (2, 0)) and a `ValueError` at request time.
    Confirmed against the pre-fix code that this construction does raise
    `ValueError: S7 violation: naked stub at (3, 0)`.
    """
    from tycoon_city.sim.town_streets import find_naked_stubs, plan_street_features

    routes = {("a", "b"): ((0, 0), (1, 0), (2, 0), (3, 0))}
    lots = {"a": (0, 0)}

    features = plan_street_features(routes, lots, frozenset(), {"a": 0}, (), (0, 0))
    assert isinstance(features, tuple)

    route_tiles = {t for route in routes.values() for t in route}
    road_tiles = route_tiles - {(0, 0)}
    assert find_naked_stubs(road_tiles, {(0, 0)}, features) == ((3, 0),)
