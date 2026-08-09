"""The Phase E dispatcher and the enriched tycoon path.

The headline test is first: a tables-only warehouse — where view-SQL lineage is
structurally zero — gets real edges from the manifest. That is the root-cause
fix the whole backend exists for.
"""

import os
from pathlib import Path

import pytest

from tests.fixtures.tycoon_factory import make_tycoon_project
from tycoon_city.catalog.errors import CatalogError
from tycoon_city.catalog.loader import load_catalog, load_context


def test_tables_only_warehouse_with_a_manifest_gets_real_edges(tmp_path):
    """THE headline. Every object in the factory warehouse is a table, so the
    SQL scan finds nothing; the edges must come from the manifest, tagged so."""
    root = make_tycoon_project(tmp_path / "fx")

    ctx = load_context(root)

    assert all(obj.kind == "table" for obj in ctx.objects)
    assert len(ctx.edges) >= 4
    assert {e.provenance for e in ctx.edges} == {"manifest"}
    # And the specific joins that would break under a last-segment join:
    pairs = {(e.src, e.dst) for e in ctx.edges}
    assert ("staging.stg_orders", "marts.fct_revenue") in pairs, "alias override lost"
    assert ("raw.orders", "staging.daily") in pairs
    assert ("staging.stg_orders", "marts.daily") in pairs, "same-name pair conflated"


def test_run_history_is_attached_and_ok_is_derived(tmp_path):
    root = make_tycoon_project(tmp_path / "fx")

    ctx = load_context(root)

    assert ctx.runs is not None
    assert len(ctx.runs.runs) == 3
    # Newest first, and ok derived from error counts -- the stored `success`
    # column is NULL on every row the factory writes, like the real database.
    assert ctx.runs.latest.command == "test"
    assert ctx.runs.latest.ok is True
    assert ctx.runs.node_results["model.fx_dbt.stg_orders"].status == "success"


def test_a_directory_without_tycoon_yml_is_an_error_not_a_guess(tmp_path):
    (tmp_path / "not_a_project").mkdir()

    with pytest.raises(CatalogError, match="not a tycoon project"):
        load_context(tmp_path / "not_a_project")


def test_a_plain_file_path_is_byte_identical_to_load_catalog(tmp_path):
    root = make_tycoon_project(tmp_path / "fx")
    warehouse = root / "data" / "fx.duckdb"

    # Even though this file sits inside a tycoon project, the file path takes
    # today's path exactly: no manifest edges, no runs, no notes.
    assert load_context(warehouse) == load_catalog(warehouse)


# --- The degradation ladder, one rung per test -------------------------------


def test_missing_manifest_degrades_to_scan_lineage_with_a_note(tmp_path):
    root = make_tycoon_project(tmp_path / "fx", with_manifest=False)

    ctx = load_context(root)

    assert ctx.edges == ()  # tables-only, so the scan finds nothing
    assert any("no dbt manifest" in note for note in ctx.notes)
    assert ctx.runs is not None  # the other enrichment still landed


def test_corrupt_manifest_degrades_like_a_missing_one(tmp_path):
    root = make_tycoon_project(tmp_path / "fx")
    (root / "dbt" / "target" / "manifest.json").write_text("{ not json")

    ctx = load_context(root)

    assert ctx.edges == ()
    assert any("no dbt manifest" in note for note in ctx.notes)


def test_missing_metadata_db_still_renders_the_structural_city(tmp_path):
    root = make_tycoon_project(tmp_path / "fx", with_metadata=False)

    ctx = load_context(root)

    assert len(ctx.edges) >= 4  # lineage unaffected
    assert ctx.runs is None
    assert any("no run metadata" in note for note in ctx.notes)


def test_empty_run_history_is_named_not_silent(tmp_path):
    root = make_tycoon_project(tmp_path / "fx", runs=())

    ctx = load_context(root)

    assert ctx.runs is not None
    assert ctx.runs.runs == ()
    assert any("no run history yet" in note for note in ctx.notes)


def test_locked_metadata_db_degrades_with_a_note(tmp_path):
    import duckdb

    root = make_tycoon_project(tmp_path / "fx")
    # A running `tycoon` command holds the write handle; a read-only connect
    # from another configuration must fail, and the city must still load.
    writer = duckdb.connect(str(root / ".tycoon" / "metadata.duckdb"))
    try:
        ctx = load_context(root)
    finally:
        writer.close()

    assert ctx.runs is None
    assert any("unreadable" in note for note in ctx.notes)
    assert len(ctx.edges) >= 4  # lineage still landed


def test_manifest_tag_wins_when_scan_sees_the_same_edge(tmp_path):
    """Tag precedence is only observable when two sources agree an edge
    exists — a tables-only fixture never exercises it (that hole let a
    union-order flip survive the first mutation pass). Here marts.daily is
    rebuilt as a VIEW over staging.stg_orders, so the SQL scan finds the same
    edge the manifest declares; the manifest's tag must win."""
    import duckdb

    root = make_tycoon_project(tmp_path / "fx")
    con = duckdb.connect(str(root / "data" / "fx.duckdb"))
    con.execute('drop table "marts"."daily"')
    con.execute('create view "marts"."daily" as select * from "staging"."stg_orders"')
    con.close()

    ctx = load_context(root)

    edge = next(e for e in ctx.edges if (e.src, e.dst) == ("staging.stg_orders", "marts.daily"))
    assert edge.provenance == "manifest"
    # The scan genuinely saw it too — prove the overlap this test depends on.
    plain = load_catalog(root / "data" / "fx.duckdb")
    assert any((e.src, e.dst) == ("staging.stg_orders", "marts.daily") for e in plain.edges)


def test_manifest_edges_only_reference_catalog_objects(tmp_path):
    """The external source (database=somewhere_else) exists in the manifest but
    not in the warehouse: no edge may point at it, and it is counted."""
    root = make_tycoon_project(tmp_path / "fx")

    ctx = load_context(root)

    keys = {obj.key for obj in ctx.objects}
    for edge in ctx.edges:
        assert edge.src in keys and edge.dst in keys
    assert any("1 upstream sources outside this catalog" in n for n in ctx.notes)


@pytest.mark.skipif(
    not os.environ.get("DATABASE_TYCOON_DOGFOOD"),
    reason="opt-in canary: set DATABASE_TYCOON_DOGFOOD=<path to a real tycoon project>",
)
def test_canary_a_real_tycoon_project_loads(tmp_path):
    """Read-only against a real project (never in CI, never by default)."""
    ctx = load_context(Path(os.environ["DATABASE_TYCOON_DOGFOOD"]))

    assert ctx.object_count > 0
    assert ctx.runs is not None or any("metadata" in n for n in ctx.notes)


def test_column_lineage_traces_through_manifest_raw_code(tmp_path):
    """The tables-only warehouse: view SQL gives zero column edges, so every
    bridge here was traced through resolved dbt raw_code. The alias override
    must hold at the column grain too (ref('stg_daily') -> staging.daily)."""
    ctx = load_context(make_tycoon_project(tmp_path / "fx"))

    pairs = {(e.src, e.src_col, e.dst, e.dst_col) for e in ctx.column_edges}
    # stg_orders: payload->>'name' traces JSON extraction back to payload.
    assert ("raw.orders", "payload", "staging.stg_orders", "name") in pairs
    # fct_revenue via ref('stg_orders'), plain pass-through.
    assert ("staging.stg_orders", "amount", "marts.fct_revenue", "amount") in pairs
    # mart_daily reads ref('stg_daily') == staging.daily (the ALIAS): the
    # traced table edge must exist even though depends_on never declared it.
    assert ("staging.daily", "id", "marts.daily", "id") in pairs
    assert any(e.src == "staging.daily" and e.dst == "marts.daily" and e.provenance == "manifest" for e in ctx.edges)
    # stg_daily has no raw_code -- counted, not guessed at.
    assert any("no column lineage for 1 dbt models" in n for n in ctx.notes)
