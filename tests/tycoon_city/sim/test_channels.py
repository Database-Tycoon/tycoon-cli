from tycoon_city.catalog.models import CatalogObject, Edge, PipelineContext
from tycoon_city.sim.channels import DEFAULT_BINDINGS, VisualChannel, apply_signals
from tycoon_city.sim.city import CityMap, Lot
from tycoon_city.sim.tiles import TileKind, ZoneStyle


def _ctx():
    objects = (
        CatalogObject("raw", "orders", "table", 100),
        CatalogObject("raw", "customers", "table", 5),
        CatalogObject("mart", "revenue", "view", 40),
    )
    edges = (
        Edge(src="raw.orders", dst="mart.revenue"),
        Edge(src="raw.customers", dst="mart.revenue"),
    )
    return PipelineContext("demo", objects, edges)


def _city(ctx):
    tiles = [[TileKind.GRASS for _ in range(4)] for _ in range(4)]
    lots = {o.key: Lot(o.key, i, 0, ZoneStyle.RESIDENTIAL, target_density=1) for i, o in enumerate(ctx.objects)}
    return CityMap(4, 4, tiles, lots, (0, 0), [], {})


def test_density_is_the_decade_of_rows_an_absolute_scale():
    """Height means the same thing in every catalog: level = decade of rows.
    Replaced percentile rank, which made 1,200 and 250,000 rows
    near-neighbours and destroyed the magnitude a skyline shows well."""
    ctx = _ctx()
    city = _city(ctx)

    apply_signals(city, ctx, DEFAULT_BINDINGS)

    assert city.lots["raw.orders"].target_density == 3  # 100 rows: 3rd decade
    assert city.lots["raw.customers"].target_density == 1  # 5 rows
    assert city.lots["mart.revenue"].target_density == 2  # 40 rows


def test_density_decades_cover_the_full_range():
    from tycoon_city.sim.channels import _rows_to_density

    assert _rows_to_density(0) == 1  # unmeasured (views) and empty
    assert _rows_to_density(9) == 1
    assert _rows_to_density(10) == 2
    assert _rows_to_density(99_999) == 5
    assert _rows_to_density(100_000) == 6
    assert _rows_to_density(10_000_000) == 8
    assert _rows_to_density(10**12) == 8  # clamped, never past the top


def test_powered_from_lineage_reachability():
    ctx = _ctx()
    city = _city(ctx)

    apply_signals(city, ctx, DEFAULT_BINDINGS)

    # every object is reachable in this DAG -> all powered
    assert all(lot.powered for lot in city.lots.values())


def test_unreachable_object_is_unpowered():
    objects = (
        CatalogObject("s", "a", "view", 1),
        CatalogObject("s", "b", "view", 1),
    )
    edges = (Edge(src="s.a", dst="s.b"), Edge(src="s.b", dst="s.a"))
    ctx = PipelineContext("demo", objects, edges)
    city = _city(ctx)

    # Pinned explicitly to lineage_reachability: this asserts *that* function's
    # cycle behaviour. POWERED's default binding is now lineage_participation,
    # under which cycle members do participate in lineage and stay powered.
    bindings = {**DEFAULT_BINDINGS, VisualChannel.POWERED: "lineage_reachability"}
    apply_signals(city, ctx, bindings)

    assert city.lots["s.a"].powered is False
    assert city.lots["s.b"].powered is False


def test_edge_rates_are_normalized():
    ctx = _ctx()
    city = _city(ctx)

    apply_signals(city, ctx, DEFAULT_BINDINGS)

    rates = city.edge_rates
    assert set(rates) == {
        ("raw.orders", "mart.revenue"),
        ("raw.customers", "mart.revenue"),
    }
    # edge_volume = upstream rows: orders->revenue = 100, customers->revenue = 5
    assert rates[("raw.orders", "mart.revenue")] == 1.0  # largest volume normalizes to 1.0
    assert rates[("raw.customers", "mart.revenue")] == 0.05


def test_powered_binds_to_lineage_participation():
    from tycoon_city.sim.channels import DEFAULT_BINDINGS, VisualChannel

    assert DEFAULT_BINDINGS[VisualChannel.POWERED] == "lineage_participation"


def test_apply_signals_dims_an_orphaned_object():
    from tycoon_city.catalog.models import CatalogObject, Edge, PipelineContext
    from tycoon_city.sim.channels import DEFAULT_BINDINGS, apply_signals
    from tycoon_city.sim.generator import generate_city
    from tycoon_city.sim.tiles import ZoneStyle

    rules = [("raw", ZoneStyle.INDUSTRIAL), ("mart", ZoneStyle.RESIDENTIAL)]
    ctx = PipelineContext(
        "demo",
        (
            CatalogObject("raw", "a", "table", 10),
            CatalogObject("mart", "b", "view", 5),
            CatalogObject("raw", "orphan", "table", 7),
        ),
        (Edge("raw.a", "mart.b"),),
    )
    city = generate_city(ctx, rules)
    apply_signals(city, ctx, DEFAULT_BINDINGS)

    assert city.lots["raw.a"].powered is True
    assert city.lots["mart.b"].powered is True
    assert city.lots["raw.orphan"].powered is False
