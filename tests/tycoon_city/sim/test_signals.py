from tycoon_city.catalog.models import CatalogObject, Edge, PipelineContext
from tycoon_city.sim.signals import REGISTRY


def _ctx(objects, edges=()):
    return PipelineContext("demo", tuple(objects), tuple(edges))


def test_v1_functions_are_registered():
    assert set(REGISTRY) >= {"row_count", "lineage_reachability", "edge_volume"}
    assert REGISTRY["row_count"].scope == "object"
    assert REGISTRY["lineage_reachability"].scope == "object"
    assert REGISTRY["edge_volume"].scope == "edge"


def test_row_count_returns_raw_counts():
    ctx = _ctx(
        [
            CatalogObject("raw", "orders", "table", 100),
            CatalogObject("raw", "customers", "table", 5),
        ]
    )
    result = REGISTRY["row_count"].compute(ctx)
    assert result == {"raw.orders": 100.0, "raw.customers": 5.0}


def test_lineage_reachability_marks_sources_and_descendants():
    ctx = _ctx(
        [
            CatalogObject("raw", "orders", "table", 100),  # source
            CatalogObject("mart", "revenue", "view", 0),  # downstream
            CatalogObject("misc", "orphan", "table", 3),  # source with no edges
        ],
        [Edge(src="raw.orders", dst="mart.revenue")],
    )
    result = REGISTRY["lineage_reachability"].compute(ctx)
    assert result["raw.orders"] == 1.0
    assert result["mart.revenue"] == 1.0
    assert result["misc.orphan"] == 1.0  # no lineage still powers normally


def test_lineage_reachability_cycle_is_unreachable():
    # a and b depend on each other with no source entry -> unreachable
    ctx = _ctx(
        [
            CatalogObject("s", "a", "view", 1),
            CatalogObject("s", "b", "view", 1),
        ],
        [Edge(src="s.a", dst="s.b"), Edge(src="s.b", dst="s.a")],
    )
    result = REGISTRY["lineage_reachability"].compute(ctx)
    assert result["s.a"] == 0.0
    assert result["s.b"] == 0.0


def test_edge_volume_is_the_upstream_row_count():
    ctx = _ctx(
        [
            CatalogObject("raw", "orders", "table", 100),
            CatalogObject("mart", "revenue", "view", 40),
        ],
        [Edge(src="raw.orders", dst="mart.revenue")],
    )
    result = REGISTRY["edge_volume"].compute(ctx)
    assert result == {"raw.orders->mart.revenue": 100.0}


def test_edge_volume_survives_the_shape_the_loader_actually_produces():
    """SQL-scan lineage always points into a view, and the loader records every
    view as 0 rows. min(src, dst) was therefore 0 on every real edge -- the
    traffic feature was dead code against real data, and one test with a 40-row
    view (a shape the loader never emits) hid it. The table -> view edge must
    carry the table's volume; a view -> view edge stays 0, since both ends are
    unmeasured and this project does not invent numbers."""
    ctx = _ctx(
        [
            CatalogObject("raw", "orders", "table", 50000),
            CatalogObject("staging", "stg_orders", "view", 0),
            CatalogObject("mart", "revenue", "view", 0),
        ],
        [
            Edge(src="raw.orders", dst="staging.stg_orders"),
            Edge(src="staging.stg_orders", dst="mart.revenue"),
        ],
    )
    result = REGISTRY["edge_volume"].compute(ctx)
    assert result["raw.orders->staging.stg_orders"] == 50000.0
    assert result["staging.stg_orders->mart.revenue"] == 0.0


def test_lineage_participation_marks_orphans_unpowered():
    from tycoon_city.catalog.models import CatalogObject, Edge, PipelineContext
    from tycoon_city.sim.signals import REGISTRY

    ctx = PipelineContext(
        "demo",
        (
            CatalogObject("raw", "a", "table", 1),
            CatalogObject("mart", "b", "view", 1),
            CatalogObject("raw", "orphan", "table", 1),
        ),
        (Edge("raw.a", "mart.b"),),
    )
    values = REGISTRY["lineage_participation"].compute(ctx)
    assert values == {"raw.a": 1.0, "mart.b": 1.0, "raw.orphan": 0.0}


def test_lineage_participation_ignores_edges_to_unknown_objects():
    # Expectation superseded by the no-known-edges-at-all rule: this catalog's
    # only edge leaves the catalog, so it has no known edges and stays lit. It
    # asserted 0.0 before that rule landed. The "external edges do not count as
    # participation" intent it was written for is now carried by
    # test_lineage_participation_still_dims_orphans_once_one_known_edge_exists,
    # where a known edge elsewhere keeps orphanhood meaningful.
    from tycoon_city.catalog.models import CatalogObject, Edge, PipelineContext
    from tycoon_city.sim.signals import REGISTRY

    ctx = PipelineContext(
        "demo",
        (CatalogObject("raw", "a", "table", 1),),
        (Edge("raw.a", "gone.b"),),
    )
    assert REGISTRY["lineage_participation"].compute(ctx) == {"raw.a": 1.0}


def test_lineage_participation_lights_everything_when_the_catalog_has_no_edges():
    # A tables-only DuckDB file yields zero edges. "We know of no lineage at
    # all" is not the same fact as "this object is an orphan", so nothing dims.
    ctx = _ctx(
        [
            CatalogObject("raw", "a", "table", 1),
            CatalogObject("raw", "b", "table", 1),
            CatalogObject("raw", "c", "table", 1),
        ]
    )
    values = REGISTRY["lineage_participation"].compute(ctx)
    assert values == {"raw.a": 1.0, "raw.b": 1.0, "raw.c": 1.0}


def test_lineage_participation_lights_everything_when_all_edges_leave_the_catalog():
    # The only edge points at a key that is not in the catalog, so there is no
    # *known* edge and the no-lineage-at-all rule applies.
    ctx = _ctx(
        [
            CatalogObject("raw", "a", "table", 1),
            CatalogObject("raw", "b", "table", 1),
        ],
        [Edge("raw.a", "gone.b")],
    )
    values = REGISTRY["lineage_participation"].compute(ctx)
    assert values == {"raw.a": 1.0, "raw.b": 1.0}


def test_lineage_participation_still_dims_orphans_once_one_known_edge_exists():
    # Regression guard for the behaviour the signal exists to deliver: a single
    # known edge is enough to make orphans meaningful again, even alongside an
    # edge that leaves the catalog.
    ctx = _ctx(
        [
            CatalogObject("raw", "a", "table", 1),
            CatalogObject("mart", "b", "view", 1),
            CatalogObject("raw", "orphan", "table", 1),
        ],
        [Edge("raw.a", "mart.b"), Edge("raw.orphan", "gone.c")],
    )
    values = REGISTRY["lineage_participation"].compute(ctx)
    assert values == {"raw.a": 1.0, "mart.b": 1.0, "raw.orphan": 0.0}


def test_lineage_reachability_is_always_true_on_a_dag():
    # Documents why it is unfit as the POWERED default: every node of an
    # acyclic graph traces back to some source, so nothing ever dims.
    from tycoon_city.catalog.models import CatalogObject, Edge, PipelineContext
    from tycoon_city.sim.signals import REGISTRY

    ctx = PipelineContext(
        "demo",
        (
            CatalogObject("raw", "a", "table", 1),
            CatalogObject("stg", "b", "view", 1),
            CatalogObject("mart", "c", "view", 1),
        ),
        (Edge("raw.a", "stg.b"), Edge("stg.b", "mart.c")),
    )
    values = REGISTRY["lineage_reachability"].compute(ctx)
    assert set(values.values()) == {1.0}
