"""The DAG planner (streets v2): columns, channels, routes, suburb, power.

The plan IS the geometry — the generator only paints it — so the rules live
here as planner facts: concrete coordinates, never abstractions of them.
"""

from tycoon_city.catalog.models import CatalogObject, Edge, PipelineContext
from tycoon_city.sim.layout import GRID_MIN, ROW_PITCH, TRACK_PITCH, plan_dag_layout


def _ctx(objects, edges=()):
    return PipelineContext("demo", tuple(objects), tuple(edges))


def _obj(schema, name):
    return CatalogObject(schema, name, "table", 0)


def _chain_ctx():
    """raw.a -> staging.b -> marts.c, plus an orphan."""
    return _ctx(
        [_obj("raw", "a"), _obj("staging", "b"), _obj("marts", "c"), _obj("scratch", "x")],
        [Edge("raw.a", "staging.b"), Edge("staging.b", "marts.c")],
    )


def test_columns_follow_depth_and_flow_reads_east():
    plan = plan_dag_layout(_chain_ctx())
    ax, _ = plan.positions["raw.a"]
    bx, _ = plan.positions["staging.b"]
    cx, _ = plan.positions["marts.c"]
    assert ax < bx < cx


def test_every_edge_has_a_route_from_lot_to_lot():
    plan = plan_dag_layout(_chain_ctx())
    assert set(plan.routes) == {("raw.a", "staging.b"), ("staging.b", "marts.c")}
    for (src, dst), route in plan.routes.items():
        assert route[0] == plan.positions[src]
        assert route[-1] == plan.positions[dst]
        for (x0, y0), (x1, y1) in zip(route, route[1:], strict=False):
            assert abs(x1 - x0) + abs(y1 - y0) == 1


def test_no_building_stands_on_any_route_interior():
    """The redirect's core sentence: 'there shouldn't be other buildings in
    the way.' Interior tiles of every route must avoid every lot."""
    ctx = _ctx(
        [_obj("s", f"t{i}") for i in range(8)] + [_obj("m", "far")],
        # A fan-in onto s.t0 plus a two-layer edge that must cross the middle
        # column where the other buildings live.
        [Edge("s.t1", "m.far"), Edge("m.far", "s.t0")] + [Edge(f"s.t{i}", "s.t0") for i in range(2, 8)],
    )
    plan = plan_dag_layout(ctx)
    lot_tiles = set(plan.positions.values())
    for (src, dst), route in plan.routes.items():
        for tile in route[1:-1]:
            assert tile not in lot_tiles, f"{src}->{dst} passes through a building at {tile}"


def _vertical_tiles(route):
    verticals = set()
    for i in range(1, len(route) - 1):
        (x0, _y0), (x1, _y1), (x2, _y2) = route[i - 1], route[i], route[i + 1]
        if x0 == x1 == x2:  # strictly inside a vertical run
            verticals.add(route[i])
    return verticals


def test_vertical_sharing_is_allowed_only_within_a_source_or_destination_group():
    """V3, streets v2.1: edges bound for the SAME destination merge like
    tributaries — they must share their trunk — but two edges with different
    sources AND different destinations may never share a vertical run, or two
    unrelated streets would fuse into something untraceable."""
    ctx = _ctx(
        [_obj("a", f"s{i}") for i in range(1, 5)] + [_obj("b", "d1"), _obj("b", "d2")],
        [Edge(f"a.s{i}", "b.d1") for i in range(1, 5)] + [Edge("a.s1", "b.d2"), Edge("a.s2", "b.d2")],
    )
    plan = plan_dag_layout(ctx)

    pairs = sorted(plan.routes)
    for i, p in enumerate(pairs):
        for q in pairs[i + 1 :]:
            shared = _vertical_tiles(plan.routes[p]) & _vertical_tiles(plan.routes[q])
            if p[0] != q[0] and p[1] != q[1]:
                assert not shared, f"unrelated {p} and {q} share a track at {sorted(shared)}"

    # The merge is real, not merely permitted. All four d1 tributaries run
    # their verticals on ONE trunk x, and (four sources, one destination row:
    # two sources must sit on the same side, ROW_PITCH apart) at least one
    # pair physically shares trunk tiles.
    d1_verticals = [_vertical_tiles(plan.routes[(f"a.s{i}", "b.d1")]) for i in range(1, 5)]
    trunk_xs = {x for tiles in d1_verticals for x, _ in tiles}
    assert len(trunk_xs) == 1, f"d1's tributaries use {len(trunk_xs)} trunks: {sorted(trunk_xs)}"
    assert any(a & b for i, a in enumerate(d1_verticals) for b in d1_verticals[i + 1 :]), (
        "a shared destination must share trunk tiles"
    )


def test_sprawl_channel_width_grows_with_distinct_destination_count():
    """The gameplay signal, v2.1: a channel is as wide as the number of
    PLACES its edges lead to. Destinations here sit in distinct schemas so
    the sibling-block rule cannot merge them — same-schema same-source fans
    now deliberately collapse to ONE block trunk (that is the reward)."""

    def width_for(n_dsts):
        objects = [_obj("a", "src")] + [_obj(f"s{i}", f"d{i}") for i in range(n_dsts)]
        edges = [Edge("a.src", f"s{i}.d{i}") for i in range(n_dsts)]
        return plan_dag_layout(_ctx(objects, edges)).width

    assert width_for(12) >= width_for(2) + 10 * TRACK_PITCH


def test_pure_fan_in_stays_barely_wider_than_a_pair():
    """Twelve tributaries into one destination share one trunk: the city must
    be no wider than the two-edge fan-in (the small roads combined)."""

    def width_for(n_edges):
        objects = [_obj("a", f"s{i}") for i in range(n_edges)] + [_obj("b", "sink")]
        edges = [Edge(f"a.s{i}", "b.sink") for i in range(n_edges)]
        return plan_dag_layout(_ctx(objects, edges)).width

    assert width_for(12) <= width_for(2) + TRACK_PITCH


def test_orphans_live_in_the_southern_suburb():
    plan = plan_dag_layout(_chain_ctx())
    assert plan.orphans == ("scratch.x",)
    _, oy = plan.positions["scratch.x"]
    city_rows = [plan.positions[k][1] for k in ("raw.a", "staging.b", "marts.c")]
    assert oy > max(city_rows), "the suburb sits south of the working city"
    assert not any("scratch.x" in pair for pair in plan.routes)


def test_power_stubs_reach_exactly_the_source_lots():
    ctx = _ctx(
        [_obj("raw", "a"), _obj("raw", "b"), _obj("m", "c")],
        [Edge("raw.a", "m.c"), Edge("raw.b", "m.c")],
    )
    plan = plan_dag_layout(ctx)
    source_col = plan.positions["raw.a"][0]
    stub_rows = {y for x, y in plan.power_tiles if x == source_col - 1}
    assert stub_rows == {plan.positions["raw.a"][1], plan.positions["raw.b"][1]}
    # The sink column gets no power of its own: data enters at the sources.
    assert all(x < plan.positions["m.c"][0] - 1 for x, _ in plan.power_tiles)


def test_a_cycle_shares_a_column_and_both_directions_get_routes():
    ctx = _ctx(
        [_obj("s", "a"), _obj("s", "b")],
        [Edge("s.a", "s.b"), Edge("s.b", "s.a")],
    )
    plan = plan_dag_layout(ctx)
    assert plan.positions["s.a"][0] == plan.positions["s.b"][0]
    assert set(plan.routes) == {("s.a", "s.b"), ("s.b", "s.a")}
    row_gap = abs(plan.positions["s.a"][1] - plan.positions["s.b"][1])
    for route in plan.routes.values():
        assert len(route) > row_gap + 1, "a loop route must detour through its channel, not phase through the column"


def test_districts_bound_their_connected_lots_and_exclude_suburb_orphans():
    """The plate is the schema's working neighbourhood. A schema with city
    lots must not stretch its plate to a suburb orphan; an all-orphan schema
    keeps a plate around its suburb lots."""
    ctx = _ctx(
        [_obj("raw", "a"), _obj("raw", "stray"), _obj("m", "c"), _obj("scratch", "x")],
        [Edge("raw.a", "m.c")],
    )
    plan = plan_dag_layout(ctx)
    by_schema = {d.schema: d for d in plan.districts}

    raw = by_schema["raw"]
    ax, ay = plan.positions["raw.a"]
    assert raw.x <= ax < raw.x + raw.w and raw.y <= ay < raw.y + raw.h
    _, stray_y = plan.positions["raw.stray"]
    assert stray_y >= raw.y + raw.h, "the suburb orphan must sit outside raw's plate"

    scratch = by_schema["scratch"]  # all-orphan schema keeps its plate
    sx, sy = plan.positions["scratch.x"]
    assert scratch.x <= sx < scratch.x + scratch.w and scratch.y <= sy < scratch.y + scratch.h


def test_rows_and_grid_respect_the_pitches_and_minimum():
    plan = plan_dag_layout(_chain_ctx())
    ys = sorted({plan.positions[k][1] for k in ("raw.a", "staging.b", "marts.c")})
    for y0, y1 in zip(ys, ys[1:], strict=False):
        assert (y1 - y0) % ROW_PITCH == 0
    assert plan.width >= GRID_MIN and plan.height >= GRID_MIN


def test_empty_catalog_yields_a_bare_grid():
    plan = plan_dag_layout(_ctx([]))
    assert plan.width == GRID_MIN and plan.height == GRID_MIN
    assert plan.positions == {} and plan.routes == {}


def test_plan_ignores_the_order_objects_and_edges_arrive_in():
    objects = [_obj("raw", "a"), _obj("staging", "b"), _obj("marts", "c")]
    edges = [Edge("raw.a", "staging.b"), Edge("staging.b", "marts.c")]
    forward = plan_dag_layout(_ctx(objects, edges))
    backward = plan_dag_layout(_ctx(list(reversed(objects)), list(reversed(edges))))
    assert forward == backward


def test_two_merging_models_become_a_two_lane_road():
    """Stephen, verbatim: 'two models merging becomes a two lane road.' Where
    routes share a run the road is one lane wider per merged flow (capped);
    where a tributary still runs alone it stays single-lane."""
    from tycoon_city.sim.layout import LANE_CAP

    ctx = _ctx(
        [_obj("a", "s1"), _obj("a", "s2"), _obj("a", "s3"), _obj("b", "sink")],
        [Edge("a.s1", "b.sink"), Edge("a.s2", "b.sink"), Edge("a.s3", "b.sink")],
    )
    plan = plan_dag_layout(ctx)
    interiors = {pair: plan.routes[pair][1:-1] for pair in plan.routes}
    crossing: dict[tuple[int, int], int] = {}
    for tiles in interiors.values():
        for t in set(tiles):
            crossing[t] = crossing.get(t, 0) + 1
    merged = {t for t, c in crossing.items() if c >= 2}
    assert merged, "three tributaries to one sink must share trunk tiles"

    # Every merged tile is widened beside itself (east for the trunk, south
    # for the shared approach row).
    lanes = set(plan.lane_tiles)
    for x, y in merged:
        assert (x + 1, y) in lanes or (x, y + 1) in lanes, f"merged tile {(x, y)} stayed single-lane"

    # A tributary's PRE-merge vertical run stays one lane. Measured away from
    # the corner (2+ rows below any merged tile) so the shared approach row's
    # own south lane cannot be mistaken for tributary widening.
    corner_y = max(y for _, y in merged)
    for pair, tiles in interiors.items():
        solo_vertical = [
            t
            for i, t in enumerate(tiles)
            if crossing[t] == 1
            and t[1] > corner_y + 1
            and ((i > 0 and tiles[i - 1][0] == t[0]) or (i + 1 < len(tiles) and tiles[i + 1][0] == t[0]))
        ]
        for x, y in solo_vertical:
            assert (x + 1, y) not in lanes, f"solo {pair} tile {(x, y)} grew a lane"

    # And the cap holds: a 12-way merge reserves LANE_CAP lanes, not 12 —
    # its city is exactly (LANE_CAP - 2) tiles wider than the 2-way's.
    def width_for(n_edges):
        objects = [_obj("a", f"s{i}") for i in range(n_edges)] + [_obj("b", "sink")]
        return plan_dag_layout(_ctx(objects, [Edge(f"a.s{i}", "b.sink") for i in range(n_edges)])).width

    assert width_for(12) == width_for(2) + (LANE_CAP - 2)


def test_schemas_form_contiguous_bands_within_a_column():
    """No circuit board: within one depth column, a schema's buildings sit in
    one unbroken band — never A B A when reading rows top to bottom."""
    ctx = _ctx(
        # Both schemas split their loyalty between the two destinations, so
        # plain barycenter provably interleaves them (verified: without the
        # banding pass this fixture renders apple,apple,zebra,apple,...).
        [_obj("apple", f"a{i}") for i in range(3)]
        + [_obj("zebra", f"z{i}") for i in range(3)]
        + [_obj("m1", "d1"), _obj("m2", "d2")],
        [
            Edge("apple.a0", "m1.d1"),
            Edge("apple.a2", "m1.d1"),
            Edge("zebra.z0", "m1.d1"),
            Edge("apple.a1", "m2.d2"),
            Edge("zebra.z1", "m2.d2"),
            Edge("zebra.z2", "m2.d2"),
        ],
    )
    plan = plan_dag_layout(ctx)
    by_column: dict[int, list[tuple[int, str]]] = {}
    for key, (x, y) in plan.positions.items():
        by_column.setdefault(x, []).append((y, key.split(".")[0]))
    for x, rows in by_column.items():
        sequence = [schema for _, schema in sorted(rows)]
        seen_closed: set[str] = set()
        previous = None
        for schema in sequence:
            if schema != previous:
                assert schema not in seen_closed, f"column x={x}: schema {schema} appears in two bands: {sequence}"
                if previous is not None:
                    seen_closed.add(previous)
                previous = schema


def test_same_source_siblings_pack_into_a_touching_block_with_one_trunk():
    """Stephen, verbatim: 'if two models have the exact same sources, they
    should be clustered together to form a block.' Three marts cut from the
    same two staging tables: adjacent rows (pitch 1, touching), one shared
    delivery trunk, and the sprawl bill is one unit, not three."""
    ctx = _ctx(
        [_obj("stg", "a"), _obj("stg", "b")]
        + [_obj("mart", f"m{i}") for i in range(3)]
        + [_obj("mart", "other")],  # same schema+depth, DIFFERENT sources
        [Edge(f"stg.{s}", f"mart.m{i}") for s in ("a", "b") for i in range(3)] + [Edge("stg.a", "mart.other")],
    )
    plan = plan_dag_layout(ctx)

    rows = sorted(plan.positions[f"mart.m{i}"][1] for i in range(3))
    assert rows[1] == rows[0] + 1 and rows[2] == rows[0] + 2, f"block members must touch: rows {rows}"
    # 'other' shares stg.a with the block, so the AFFINITY rule (Stephen,
    # 2026-08-05: "cluster together the bigger buildings... especially if
    # they share common sources") pulls it against the block — touching,
    # never interleaved into it.
    other_row = plan.positions["mart.other"][1]
    assert other_row in {rows[0] - 1, rows[2] + 1}, (
        f"a common-source neighbour must touch the block: {other_row} vs {rows}"
    )

    # One delivery trunk: all six block in-edges run their verticals on a
    # single shared x; other's edge uses a different one.
    def trunk_xs(pairs):
        xs = set()
        for pair in pairs:
            route = plan.routes[pair]
            for i in range(1, len(route) - 1):
                if route[i - 1][0] == route[i][0] == route[i + 1][0]:
                    xs.add(route[i][0])
        return xs

    block_pairs = [(f"stg.{s}", f"mart.m{i}") for s in ("a", "b") for i in range(3)]
    assert len(trunk_xs(block_pairs)) == 1, "the block must be served by ONE trunk"
    other_xs = trunk_xs([("stg.a", "mart.other")])
    assert not (other_xs & trunk_xs(block_pairs)), "a non-sibling never rides the block trunk"


def test_clustering_rhythm_tight_bands_wide_boundaries():
    """Grouping only READS when spacing varies: same-schema neighbours sit
    NEIGHBOUR_PITCH apart, a schema boundary opens a BAND_GAP, blocks touch."""
    from tycoon_city.sim.layout import BAND_GAP, NEIGHBOUR_PITCH

    ctx = _ctx(
        [_obj("apple", f"a{i}") for i in range(3)] + [_obj("zebra", f"z{i}") for i in range(3)] + [_obj("m", "sink")],
        [Edge(f"apple.a{i}", "m.sink") for i in range(3)] + [Edge(f"zebra.z{i}", "m.sink") for i in range(3)],
    )
    plan = plan_dag_layout(ctx)
    rows = sorted((plan.positions[k][1], k.split(".")[0]) for k in plan.positions if k != "m.sink")
    gaps = [(rows[i + 1][0] - rows[i][0], rows[i][1] == rows[i + 1][1]) for i in range(len(rows) - 1)]
    for gap, same_schema in gaps:
        assert gap == (NEIGHBOUR_PITCH if same_schema else BAND_GAP), (
            f"rhythm broken: gap {gap}, same_schema={same_schema} in {rows}"
        )


def test_firehouse_gets_a_road_and_the_suburb_stays_clear_of_it():
    """Vehicles must travel on roads: the station is wired to the network
    (contiguous, ends ON a road tile), and the streetless suburb sits below
    the civic strip so the access road can never brush an orphan."""
    plan = plan_dag_layout(_chain_ctx())
    assert plan.access_road, "a city with roads must wire in its firehouse"
    fx, fy = plan.firehouse_xy
    first = plan.access_road[0]
    assert abs(first[0] - fx) + abs(first[1] - fy) == 1, "road starts at the station door"
    for a, b in zip(plan.access_road, plan.access_road[1:], strict=False):
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1, "access road jumps"
    street_tiles = {t for route in plan.routes.values() for t in route[1:-1]}
    assert plan.access_road[-1] in street_tiles, "access road must reach a real street"
    _, oy = plan.positions["scratch.x"]
    assert oy >= fy + 3, "suburb sits below the civic strip"

    # No roads at all -> no access road (a road to nowhere would be theater).
    bare = plan_dag_layout(_ctx([_obj("s", "lonely")]))
    assert bare.access_road == ()


# ---------------------------------------------------------------------------
# Streets v3 (2026-08-05, Stephen: "strange and unrealistic and ugly roads" —
# zigzag staircases and dead-end/redundant runs). Straight streets, aligned
# columns, one highway row per destination, direction-aware merging.
# ---------------------------------------------------------------------------


def test_first_member_float_aligns_matched_columns():
    """A column's first building starts on its predecessors' row, not the
    margin — so a destination fed from row 5 sits at row 5 and the street
    from its same-row source never turns."""
    ctx = _ctx(
        [_obj("a", "s0"), _obj("a", "s1"), _obj("b", "d")],
        [Edge("a.s0", "b.d"), Edge("a.s1", "b.d")],
    )
    plan = plan_dag_layout(ctx)
    assert plan.positions["b.d"][1] == plan.positions["a.s1"][1] == 5
    straight = plan.routes[("a.s1", "b.d")]
    assert len({y for _, y in straight}) == 1, f"aligned street turned: {straight}"


def test_straight_streets_reserve_no_channel_width():
    """A comb of aligned 1:1 hops needs no vertical trunks, so the channel
    stays at pad width no matter how many pairs cross it. This is what keeps
    a warehouse of raw -> staging hops from paving a 30-tile-wide channel."""

    def width_for(n_pairs):
        objects = [_obj("a", f"s{i}") for i in range(n_pairs)] + [_obj("b", f"d{i}") for i in range(n_pairs)]
        edges = [Edge(f"a.s{i}", f"b.d{i}") for i in range(n_pairs)]
        plan = plan_dag_layout(_ctx(objects, edges))
        for route in plan.routes.values():
            assert len({y for _, y in route}) == 1, f"comb street turned: {route}"
        return plan.width

    assert width_for(12) == width_for(2)


def test_a_long_edge_rides_one_highway_row():
    """The highway pass: a street crossing intermediate columns takes ONE
    constant pass-through row (the nearest free-everywhere row to its
    destination), so however many columns it crosses it visits at most three
    rows — source, highway, destination — and turns at most four times.
    Before v3 each column reserved its own crossing row and the street
    staircased once per column."""
    objects = [_obj(f"s{i}", f"t{j}") for i in range(6) for j in range(2)] + [_obj("s5", "extra")]
    edges = [Edge(f"s{i}.t{j}", f"s{i + 1}.t{j}") for i in range(5) for j in range(2)] + [
        Edge("s4.t1", "s5.extra"),
        Edge("s0.t0", "s5.extra"),
    ]
    plan = plan_dag_layout(_ctx(objects, edges))
    route = plan.routes[("s0.t0", "s5.extra")]
    rows = {y for _, y in route}
    assert len(rows) <= 3, f"the long street staircased: rows {sorted(rows)}"
    turns = sum(
        1
        for i in range(1, len(route) - 1)
        if (route[i][0] - route[i - 1][0], route[i][1] - route[i - 1][1])
        != (route[i + 1][0] - route[i][0], route[i + 1][1] - route[i][1])
    )
    assert turns <= 4, f"the long street turned {turns} times: {route}"


def test_a_street_splitting_off_widens_nothing_at_the_corner():
    """Direction-aware merging: flows moving the SAME WAY widen the road;
    a corner where one street splits from another (one route vertical, one
    horizontal) widens nothing. The old any-direction count dropped an
    orphan lane tile at every such corner — Stephen's dead-end stubs."""
    ctx = _ctx(
        [_obj("s1", "t1"), _obj("s0", "t3"), _obj("s2", "t2")],
        [Edge("s1.t1", "s0.t3"), Edge("s1.t1", "s2.t2")],
    )
    plan = plan_dag_layout(ctx)
    lanes = set(plan.lane_tiles)
    # The shared run out of the source still earns its second lane...
    assert {(6, 4), (7, 4)} <= lanes, f"shared run lost its lane: {sorted(lanes)}"
    # ...but the split corner (8,3) grows no orphan stub beside it.
    assert (9, 3) not in lanes, "a mere split grew a dead-end lane stub"
    assert (8, 4) not in lanes or (8, 4) in {t for r in plan.routes.values() for t in r}, (
        "a mere split grew a lane below the corner"
    )


def test_bigger_tables_lead_their_affinity_cluster():
    """Downtown (Stephen, 2026-08-05: "cluster together the bigger
    buildings"): inside an affinity cluster the biggest tables sit first, so
    mass gathers instead of scattering. Names deliberately contradict size
    order — alphabetical luck cannot pass this."""
    from tycoon_city.catalog.models import CatalogObject

    objects = [
        _obj("s", "a"),
        _obj("s", "b"),
        _obj("s", "c"),
        CatalogObject("mart", "alpha_tiny", "table", 10),
        CatalogObject("mart", "zed_huge", "table", 9000),
        CatalogObject("mart", "midsize", "table", 500),
    ]
    edges = [
        Edge("s.a", "mart.zed_huge"),
        Edge("s.b", "mart.zed_huge"),
        Edge("s.a", "mart.midsize"),
        Edge("s.a", "mart.alpha_tiny"),
        Edge("s.c", "mart.alpha_tiny"),
    ]
    plan = plan_dag_layout(_ctx(objects, edges))
    ys = {k: plan.positions[f"mart.{k}"][1] for k in ("zed_huge", "midsize", "alpha_tiny")}
    assert ys["zed_huge"] < ys["midsize"] < ys["alpha_tiny"], f"size order broken: {ys}"
    assert ys["midsize"] == ys["zed_huge"] + 1 and ys["alpha_tiny"] == ys["midsize"] + 1, (
        f"one shared source must make the cluster touch: {ys}"
    )


def test_big_tables_claim_2x2_and_their_streets_leave_the_east_face():
    """Scale (Stephen, 2026-08-05, approved): the top decile of the catalog's
    row counts gets a 2x2 ground plan. The anchor stays NW; the outbound
    street leaves from the EAST FACE so it never crosses its own building."""
    objects = [CatalogObject("s", f"t{i}", "table", 10 + i) for i in range(9)] + [
        CatalogObject("s", "hub", "table", 90_000),
        CatalogObject("m", "sink", "table", 0),
    ]
    edges = [Edge("s.hub", "m.sink"), Edge("s.t0", "m.sink")]
    plan = plan_dag_layout(_ctx(objects, edges))
    assert plan.big_lots == ("s.hub",), f"top decile of 10 tables is 1: {plan.big_lots}"
    hx, hy = plan.positions["s.hub"]
    route = plan.routes[("s.hub", "m.sink")]
    assert route[0] == (hx + 1, hy), f"outbound street must leave the east face: {route[0]}"


# ---------------------------------------------------------------------------
# Streets v4 (2026-08-05, Stephen: "there needs to be a clear definition for
# when and where a road is allowed to end, and what that looks like"). Every
# ending is dressed — see docs/road-grammar.md's legal-ending taxonomy. The
# no-naked-stub guarantee itself is property S7 in the generator sweep; these
# pin the CONCRETE features the planner derives.
# ---------------------------------------------------------------------------


def test_every_route_endpoint_is_dressed_and_the_kind_reads_the_building():
    """raw.a -> staging.b -> marts.c, all on row 3. Four road endings: the
    departure from the raw SOURCE (a dock — industrial read), the arrival at
    staging.b and the departure from it (aprons), the arrival at marts.c
    (apron). Coordinates are measured from the plan, not guessed: the tile is
    always the last ROAD tile before the lot, and `facing` points AT it."""
    plan = plan_dag_layout(_chain_ctx())
    by_tile = {(f.x, f.y): f for f in plan.street_features}

    ax, ay = plan.positions["raw.a"]
    bx, by = plan.positions["staging.b"]
    cx, cy = plan.positions["marts.c"]

    # raw.a is depth 0 — data enters the city there, so its street gets a dock.
    dock = by_tile[(ax + 1, ay)]
    assert (dock.kind, dock.facing) == ("dock", "w"), f"source ending: {dock}"
    # staging.b is an ordinary building: an apron on each side of it.
    arrival = by_tile[(bx - 1, by)]
    departure = by_tile[(bx + 1, by)]
    assert (arrival.kind, arrival.facing) == ("apron", "e"), f"arrival: {arrival}"
    assert (departure.kind, departure.facing) == ("apron", "w"), f"departure: {departure}"
    # ...and the last building in the chain terminates its street too.
    last = by_tile[(cx - 1, cy)]
    assert (last.kind, last.facing) == ("apron", "e"), f"final arrival: {last}"
    assert all(f.w == 1 and f.h == 1 for f in plan.street_features if f.kind != "plaza")


def test_the_firehouse_door_is_a_civic_plaza():
    """The access road is a road too, so its station end is an ending: the
    civic building legitimises it as a plaza (the terminated-vista move)."""
    plan = plan_dag_layout(_chain_ctx())
    fx, fy = plan.firehouse_xy
    door = plan.access_road[0]
    match = [f for f in plan.street_features if (f.x, f.y) == door]
    assert match, f"the station door {door} is undressed: {plan.street_features}"
    assert match[0].kind == "plaza", f"civic ending must be a plaza: {match[0]}"
    step = (fx - door[0], fy - door[1])
    assert match[0].facing == {(1, 0): "e", (-1, 0): "w", (0, 1): "s", (0, -1): "n"}[step]


def test_a_big_lot_earns_a_plaza_spanning_its_whole_frontage():
    """A 2x2 building's forecourt is two tiles, not a one-tile nick: the pad
    spans the shared face and is NW-anchored on the lot's own row. Kind
    precedence matters here — m.hub is a 2x2, so plaza beats apron; s.feeder
    and s.t0 are depth-0 sources, so they keep their docks (1x1)."""
    objects = [CatalogObject("s", f"t{i}", "table", 10 + i) for i in range(9)] + [
        CatalogObject("m", "hub", "table", 90_000),
        CatalogObject("s", "feeder", "table", 5),
    ]
    edges = [Edge("s.feeder", "m.hub"), Edge("s.t0", "m.hub")]
    plan = plan_dag_layout(_ctx(objects, edges))
    assert plan.big_lots == ("m.hub",), plan.big_lots
    hx, hy = plan.positions["m.hub"]

    plazas = [f for f in plan.street_features if f.kind == "plaza" and f.x == hx - 1]
    assert len(plazas) == 1, f"one arrival, one forecourt: {plan.street_features}"
    pad = plazas[0]
    assert (pad.x, pad.y, pad.w, pad.h, pad.facing) == (hx - 1, hy, 1, 2, "e"), (
        f"a 2x2's west frontage is two tiles tall, anchored on its row: {pad}"
    )
    docks = sorted((f.x, f.y) for f in plan.street_features if f.kind == "dock")
    assert docks == sorted((plan.positions[k][0] + 1, plan.positions[k][1]) for k in ("s.feeder", "s.t0")), (
        f"both depth-0 sources keep a 1x1 dock: {docks}"
    )
    assert all(f.w == 1 and f.h == 1 for f in plan.street_features if f.kind == "dock")


def test_street_features_are_sorted_and_input_order_independent():
    """Byte stability: the tuple is sorted by (kind, x, y) and the plan does
    not care what order the catalog listed things in."""
    objects = [_obj("raw", "a"), _obj("staging", "b"), _obj("marts", "c")]
    edges = [Edge("raw.a", "staging.b"), Edge("staging.b", "marts.c")]
    forward = plan_dag_layout(_ctx(objects, edges)).street_features
    backward = plan_dag_layout(_ctx(list(reversed(objects)), list(reversed(edges)))).street_features
    assert forward == backward
    assert list(forward) == sorted(forward, key=lambda f: (f.kind, f.x, f.y)), forward
    assert len(forward) == len({(f.kind, f.x, f.y, f.facing, f.w, f.h) for f in forward})


def test_a_catalog_without_lineage_dresses_nothing():
    """No street, no ending. A feature without a road would be pure invention."""
    plan = plan_dag_layout(_ctx([_obj("s", "lonely"), _obj("s", "other")]))
    assert plan.routes == {} and plan.street_features == ()
