"""Tests for `tycoon data sync` (issue #12).

Covers the core ``sync_to_local`` function and the CLI surface. We use a
local DuckDB file as the source instead of ``md:`` so tests work without
MotherDuck credentials. The ATTACH path is the same whether the URL is
local or ``md:``, so this exercises the same code paths.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from tycoon.cli import app
from tycoon.project import SyncSourceSpec
from tycoon.sync import sync_to_local


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def source_db(tmp_path: Path) -> Path:
    """A local DuckDB file with three schemas, six tables, varying row counts."""
    src = tmp_path / "source.duckdb"
    con = duckdb.connect(str(src))
    try:
        con.execute("CREATE SCHEMA mart")
        con.execute("CREATE SCHEMA staging")
        con.execute("CREATE SCHEMA raw")
        con.execute("CREATE TABLE mart.dim_users AS SELECT range AS id FROM range(10)")
        con.execute("CREATE TABLE mart.fct_orders AS SELECT range AS id FROM range(25)")
        con.execute("CREATE TABLE staging.stg_widgets AS SELECT range AS id FROM range(5)")
        con.execute("CREATE TABLE staging.stg_orders AS SELECT range AS id FROM range(7)")
        con.execute("CREATE TABLE raw.events AS SELECT range AS id FROM range(100)")
        con.execute("CREATE TABLE raw.users AS SELECT range AS id FROM range(50)")
    finally:
        con.close()
    return src


@pytest.fixture
def project(tmp_path: Path, monkeypatch):
    """Minimal tycoon project + monkey-patched config so the sync command can
    resolve a ``config.root``."""
    (tmp_path / "tycoon.yml").write_text(
        "name: test\n"
        "version: 0.1.0\n"
        "database:\n"
        "  raw: data/raw.duckdb\n"
        "  warehouse: data/warehouse.duckdb\n"
        "sources: {}\n"
    )

    from tycoon.commands import sync_cmd as sync_mod
    from tycoon.config import TycoonConfig

    cfg = TycoonConfig(project_root=tmp_path)
    monkeypatch.setattr(sync_mod, "config", cfg)
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Core sync_to_local
# ---------------------------------------------------------------------------


class TestSyncToLocal:
    def test_replace_copies_all_tables_when_unfiltered(self, tmp_path, source_db):
        dest = tmp_path / "out.duckdb"
        spec = SyncSourceSpec(**{"from": str(source_db)})
        result = sync_to_local([spec], dest, mode="replace")

        assert dest.exists()
        # 6 tables total across mart / staging / raw
        assert len(result.tables) == 6
        assert result.total_rows == 10 + 25 + 5 + 7 + 100 + 50

        # Verify tables actually exist with correct row counts
        con = duckdb.connect(str(dest))
        try:
            assert con.execute("SELECT COUNT(*) FROM mart.dim_users").fetchone()[0] == 10
            assert con.execute("SELECT COUNT(*) FROM raw.events").fetchone()[0] == 100
        finally:
            con.close()

    def test_schema_glob_filters(self, tmp_path, source_db):
        dest = tmp_path / "out.duckdb"
        spec = SyncSourceSpec(**{"from": str(source_db)}, schemas=["mart"])
        result = sync_to_local([spec], dest, mode="replace")

        # Only mart schema → 2 tables
        assert len(result.tables) == 2
        synced_schemas = {t.schema for t in result.tables}
        assert synced_schemas == {"mart"}

    def test_table_glob_filters(self, tmp_path, source_db):
        dest = tmp_path / "out.duckdb"
        # All schemas, but only stg_* and dim_* tables
        spec = SyncSourceSpec(
            **{"from": str(source_db)},
            schemas=["*"],
            tables=["stg_*", "dim_*"],
        )
        result = sync_to_local([spec], dest, mode="replace")

        names = {(t.schema, t.table) for t in result.tables}
        assert names == {
            ("mart", "dim_users"),
            ("staging", "stg_widgets"),
            ("staging", "stg_orders"),
        }

    def test_replace_mode_overwrites_existing_destination(self, tmp_path, source_db):
        dest = tmp_path / "out.duckdb"
        spec = SyncSourceSpec(**{"from": str(source_db)}, schemas=["mart"])

        # First sync — copy
        sync_to_local([spec], dest, mode="replace")

        # Second sync after source changes
        con = duckdb.connect(str(source_db))
        con.execute("INSERT INTO mart.dim_users SELECT 1000 + range FROM range(5)")
        con.close()

        result = sync_to_local([spec], dest, mode="replace")
        rows = next(t.rows for t in result.tables if t.table == "dim_users")
        assert rows == 15  # original 10 + new 5; replace re-copies the full source

    def test_append_mode_adds_to_existing(self, tmp_path, source_db):
        dest = tmp_path / "out.duckdb"
        spec = SyncSourceSpec(**{"from": str(source_db)}, schemas=["mart"])

        sync_to_local([spec], dest, mode="replace")
        # Append the same source again — rows should double for unchanged source
        result = sync_to_local([spec], dest, mode="append")
        rows = next(t.rows for t in result.tables if t.table == "dim_users")
        assert rows == 20  # 10 original + 10 appended

    def test_skip_existing_leaves_dest_alone(self, tmp_path, source_db):
        dest = tmp_path / "out.duckdb"
        spec = SyncSourceSpec(**{"from": str(source_db)}, schemas=["mart"])

        # First sync seeds the dest
        first = sync_to_local([spec], dest, mode="replace")
        assert len(first.tables) == 2

        # Second sync in skip-existing mode should NOT re-copy anything
        # (returns no synced tables for the already-present ones)
        second = sync_to_local([spec], dest, mode="skip-existing")
        assert second.tables == []

    def test_unknown_mode_raises(self, tmp_path, source_db):
        dest = tmp_path / "out.duckdb"
        spec = SyncSourceSpec(**{"from": str(source_db)}, schemas=["mart"])
        with pytest.raises(ValueError, match="Unknown sync mode"):
            sync_to_local([spec], dest, mode="upsert")

    def test_system_schemas_excluded(self, tmp_path, source_db):
        """information_schema / pg_catalog are present in any DuckDB file but
        must never appear in the snapshot."""
        dest = tmp_path / "out.duckdb"
        spec = SyncSourceSpec(**{"from": str(source_db)})
        result = sync_to_local([spec], dest, mode="replace")
        for t in result.tables:
            assert t.schema not in {"information_schema", "pg_catalog", "system"}

    def test_creates_dest_parent_dir(self, tmp_path, source_db):
        dest = tmp_path / "nested" / "deep" / "snapshot.duckdb"
        assert not dest.parent.exists()
        spec = SyncSourceSpec(**{"from": str(source_db)}, schemas=["mart"])
        sync_to_local([spec], dest, mode="replace")
        assert dest.exists()

    def test_multiple_sources(self, tmp_path):
        """Two sources, no schema collision: both get copied into the same dest."""
        src_a = tmp_path / "a.duckdb"
        src_b = tmp_path / "b.duckdb"
        for path, schema, n in [(src_a, "src_a", 3), (src_b, "src_b", 7)]:
            con = duckdb.connect(str(path))
            con.execute(f"CREATE SCHEMA {schema}")
            con.execute(f"CREATE TABLE {schema}.t AS SELECT range AS id FROM range({n})")
            con.close()

        dest = tmp_path / "merged.duckdb"
        result = sync_to_local(
            [
                SyncSourceSpec(**{"from": str(src_a)}),
                SyncSourceSpec(**{"from": str(src_b)}),
            ],
            dest,
            mode="replace",
        )
        assert len(result.tables) == 2
        assert result.total_rows == 3 + 7


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


class TestSyncCli:
    def test_no_sources_errors(self, project, cli_runner):
        result = cli_runner.invoke(app, ["data", "sync"])
        assert result.exit_code == 1
        combined = (result.stdout or "") + (result.stderr or "")
        assert "Nothing to sync" in combined

    def test_no_destination_errors(self, project, cli_runner, source_db):
        result = cli_runner.invoke(
            app, ["data", "sync", "--from", str(source_db)]
        )
        assert result.exit_code == 1
        combined = (result.stdout or "") + (result.stderr or "")
        assert "No destination" in combined

    def test_unknown_mode_errors(self, project, cli_runner, source_db):
        dest = project / "snap.duckdb"
        result = cli_runner.invoke(
            app,
            [
                "data",
                "sync",
                "--from", str(source_db),
                "--to", str(dest),
                "--mode", "rebase",
            ],
        )
        assert result.exit_code == 1
        combined = (result.stdout or "") + (result.stderr or "")
        assert "Unknown --mode" in combined

    def test_cli_sync_succeeds(self, project, cli_runner, source_db):
        dest = project / "snap.duckdb"
        result = cli_runner.invoke(
            app,
            ["data", "sync", "--from", str(source_db), "--to", str(dest)],
        )
        assert result.exit_code == 0, result.stdout
        assert dest.exists()
        con = duckdb.connect(str(dest))
        try:
            assert con.execute("SELECT COUNT(*) FROM mart.dim_users").fetchone()[0] == 10
        finally:
            con.close()

    def test_cli_schema_filter(self, project, cli_runner, source_db):
        dest = project / "snap.duckdb"
        result = cli_runner.invoke(
            app,
            [
                "data",
                "sync",
                "--from", str(source_db),
                "--to", str(dest),
                "--schema", "mart",
            ],
        )
        assert result.exit_code == 0
        con = duckdb.connect(str(dest))
        try:
            schemas = [r[0] for r in con.execute(
                "SELECT DISTINCT table_schema FROM information_schema.tables "
                "WHERE table_schema NOT IN ('information_schema','pg_catalog','main') "
                "AND table_type = 'BASE TABLE'"
            ).fetchall()]
            # Only mart should be present (plus any system schemas filtered above)
            assert "mart" in schemas
            assert "raw" not in schemas
            assert "staging" not in schemas
        finally:
            con.close()

    def test_uses_tycoon_yml_sync_block(self, project, cli_runner, source_db):
        """When no CLI flags are passed, the command falls back to tycoon.yml's sync block."""
        dest = project / "data" / "snap.duckdb"
        (project / "tycoon.yml").write_text(
            f"name: test\n"
            f"version: 0.1.0\n"
            f"database:\n"
            f"  raw: data/raw.duckdb\n"
            f"  warehouse: data/warehouse.duckdb\n"
            f"sources: {{}}\n"
            f"sync:\n"
            f"  to: data/snap.duckdb\n"
            f"  sources:\n"
            f"    - from: {source_db}\n"
            f"      schemas: ['mart']\n"
        )
        # Re-rebind config to pick up the new tycoon.yml
        from tycoon.commands import sync_cmd as sync_mod
        from tycoon.config import TycoonConfig
        sync_mod.config = TycoonConfig(project_root=project)

        result = cli_runner.invoke(app, ["data", "sync"])
        assert result.exit_code == 0, result.stdout
        assert dest.exists()
