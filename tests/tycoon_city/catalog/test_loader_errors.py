import logging

import duckdb
import pytest

from tycoon_city.catalog.errors import CatalogError
from tycoon_city.catalog.loader import load_catalog


def test_missing_file_raises_catalog_error(tmp_path):
    with pytest.raises(CatalogError) as exc:
        load_catalog(tmp_path / "nope.duckdb")
    assert "not found" in str(exc.value).lower()


def test_invalid_file_raises_catalog_error(tmp_path):
    bad = tmp_path / "bad.duckdb"
    bad.write_bytes(b"this is not a duckdb database")
    with pytest.raises(CatalogError):
        load_catalog(bad)


def test_locked_file_raises_catalog_error(tmp_path):
    db = tmp_path / "locked.duckdb"
    writer = duckdb.connect(str(db))
    writer.execute("create table t as select 1 as x")
    try:
        with pytest.raises(CatalogError):
            load_catalog(db)
    finally:
        writer.close()


def test_cap_to_500_largest(tmp_path, caplog):
    db = tmp_path / "big.duckdb"
    con = duckdb.connect(str(db))
    for i in range(505):
        con.execute(f"create table t{i} as select * from range({i}) r(id)")
    con.close()

    with caplog.at_level(logging.WARNING):
        ctx = load_catalog(db)

    assert ctx.object_count == 500
    assert any("capping" in r.message.lower() for r in caplog.records)
    # the smallest tables (t0, t1) must be dropped; the largest (t504) kept
    keys = {o.key for o in ctx.objects}
    assert "main.t504" in keys
    assert "main.t0" not in keys


def test_the_cap_keeps_views_and_names_the_truncation(tmp_path):
    """The cap must not cost the catalog its lineage, and must not be silent.

    Views carry `row_count=0` because a view has no measured size, so a pure
    "largest by row count" retention ranks EVERY view below every non-empty
    table: at 501+ objects a real catalog loses all of them, and with them the
    SQL that streets are derived from. Here the only view is dead last by row
    count -- the exact case that sort drops -- and it has to survive, its edge
    with it, and the truncation has to reach `notes` rather than the logger.
    """
    db = tmp_path / "capped.duckdb"
    con = duckdb.connect(str(db))
    con.execute("create schema raw")
    # 505 tables, every one of them non-empty, so the view (row_count 0) is
    # strictly the smallest object in the catalog.
    for i in range(505):
        con.execute(f"create table raw.t{i} as select * from range({i + 1}) r(id)")
    con.execute("create view main.v_top as select * from raw.t504")
    con.close()

    ctx = load_catalog(db)

    keys = {o.key for o in ctx.objects}
    # Preconditions: truncation really happened, and every retained table
    # outranks the view on the row count the old rule sorted by.
    assert ctx.object_count == 500, "the cap did not trigger; the test proves nothing"
    assert "raw.t0" not in keys, "nothing was dropped; the test proves nothing"
    assert all(o.row_count >= 1 for o in ctx.objects if o.kind == "table")

    assert "main.v_top" in keys, "the only view was dropped -- lineage cannot exist"
    assert edge_present(ctx, "raw.t504", "main.v_top")
    assert any("506 objects" in note and "500 most relevant" in note for note in ctx.notes), (
        f"truncation never reached the UI: {ctx.notes}"
    )


def test_edges_from_view_sql(tmp_path):
    db = tmp_path / "lin.duckdb"
    con = duckdb.connect(str(db))
    con.execute("create schema raw")
    con.execute("create table raw.orders as select * from range(3) r(id)")
    con.execute("create view main.v_orders as select * from raw.orders")
    con.close()

    ctx = load_catalog(db)

    assert edge_present(ctx, "raw.orders", "main.v_orders")


def test_ambiguous_bare_name_is_skipped_but_qualified_reference_derives_edge(tmp_path):
    db = tmp_path / "ambig.duckdb"
    con = duckdb.connect(str(db))
    con.execute("create schema s1")
    con.execute("create table s1.events as select * from range(3) r(id)")
    # Created while search_path resolves the bare name to s1.events, but the
    # view's stored SQL text keeps the bare, unqualified reference.
    con.execute("set search_path='s1'")
    con.execute("create view main.v_bare as select * from events")
    con.execute("set search_path=''")
    con.execute("create schema s2")
    con.execute("create table s2.events as select * from range(3) r(id)")
    con.execute("create view main.v_qualified as select * from s1.events")
    con.close()

    ctx = load_catalog(db)

    # "events" is now ambiguous across s1 and s2, so the bare-name reference
    # in v_bare must not derive an edge from either candidate.
    assert not edge_present(ctx, "s1.events", "main.v_bare")
    assert not edge_present(ctx, "s2.events", "main.v_bare")
    # The schema-qualified reference in v_qualified is unambiguous.
    assert edge_present(ctx, "s1.events", "main.v_qualified")
    assert not edge_present(ctx, "s2.events", "main.v_qualified")


def edge_present(ctx, src, dst):
    return any(e.src == src and e.dst == dst for e in ctx.edges)


def test_freshness_without_a_manifest_does_not_crash(tmp_path):
    """sources.json can exist without manifest.json — `dbt source freshness`
    writes one and not the other. The freshness join must degrade to a note,
    not an AttributeError that kills the whole load."""
    from tycoon_city.catalog.loader import _enrich_freshness
    from tycoon_city.catalog.models import PipelineContext

    sources = tmp_path / "sources.json"
    sources.write_text(
        '{"results": [{"unique_id": "source.p.raw.orders", "status": "pass", "max_loaded_at": "2026-08-09T00:00:00Z"}]}'
    )
    ctx = PipelineContext(database_name="db", objects=(), edges=())

    freshness_by_key, notes = _enrich_freshness(ctx, None, sources)

    assert freshness_by_key == {}, "no manifest means no unique_id -> key map, so no verdicts land"
