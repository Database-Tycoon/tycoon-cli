"""Tests for `tycoon data query`, `tycoon data schema`, and `tycoon data clean`."""

from __future__ import annotations

from pathlib import Path

import duckdb

from tycoon.cli import app


class TestSchema:

    def test_schema_runs(self, cli_runner):
        """data schema should run even with no databases (shows WARN status)."""
        result = cli_runner.invoke(app, ["data", "schema"])
        assert result.exit_code == 0
        assert len(result.stdout) > 0

    def test_schema_output_contains_database_labels(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "schema"])
        output = result.stdout
        assert "Raw" in output or "raw" in output or "Warehouse" in output or "warehouse" in output


class TestQuery:

    def test_query_no_database_gives_error(self, cli_runner, tmp_config, monkeypatch):
        """query should fail gracefully when the database file does not exist."""
        monkeypatch.setattr("tycoon.commands.db.config", tmp_config)
        if tmp_config.local_db.exists():
            tmp_config.local_db.unlink()

        result = cli_runner.invoke(app, ["data", "query", "SELECT 1"])
        assert result.exit_code != 0

    def test_query_with_db_flag(self, cli_runner, tmp_path):
        """--db flag should query a specific DuckDB file."""
        db_path = tmp_path / "test.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute("CREATE TABLE t (id INTEGER, name VARCHAR)")
        con.execute("INSERT INTO t VALUES (1, 'alice'), (2, 'bob')")
        con.close()

        result = cli_runner.invoke(app, ["data", "query", "SELECT * FROM t", "--db", str(db_path)])
        assert result.exit_code == 0
        assert "alice" in result.stdout
        assert "bob" in result.stdout

    def test_query_with_source_flag(self, cli_runner, tmp_path, monkeypatch):
        """--source flag should find the right raw DB by schema introspection."""
        from tycoon.config import TycoonConfig

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "tycoon.yml").write_text("name: test\nsources: {}\n")
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        db_path = data_dir / "my_raw.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute("CREATE SCHEMA raw_myapi")
        con.execute("CREATE TABLE raw_myapi.items (id INTEGER, val VARCHAR)")
        con.execute("INSERT INTO raw_myapi.items VALUES (1, 'hello')")
        con.close()

        cfg = TycoonConfig(project_root=tmp_path)
        monkeypatch.setattr("tycoon.commands.db.config", cfg)

        result = cli_runner.invoke(app, ["data", "query", "SELECT * FROM raw_myapi.items", "--source", "myapi"])
        assert result.exit_code == 0
        assert "hello" in result.stdout


class TestDataHelp:

    def test_data_help_shows_query_schema_clean(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "--help"])
        assert result.exit_code == 0
        assert "query" in result.stdout
        assert "schema" in result.stdout
        assert "clean" in result.stdout

    def test_query_help_shows_source_and_db_flags(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "query", "--help"])
        assert result.exit_code == 0
        assert "--source" in result.stdout
        assert "--db" in result.stdout


class TestCleanMetadataPreservation:
    """tycoon data clean must preserve .tycoon/metadata.duckdb unless --metadata."""

    def _setup(self, tmp_path: Path, monkeypatch):
        from tycoon.config import TycoonConfig

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "tycoon.yml").write_text("name: test\nsources: {}\n")
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        meta_dir = tmp_path / ".tycoon"
        meta_dir.mkdir()

        # Seed raw + warehouse + metadata DBs
        raw = data_dir / "raw.duckdb"
        local = data_dir / "warehouse.duckdb"
        meta = meta_dir / "metadata.duckdb"
        for p in (raw, local, meta):
            duckdb.connect(str(p)).close()

        cfg = TycoonConfig(project_root=tmp_path)
        monkeypatch.setattr("tycoon.commands.db.config", cfg)
        return raw, local, meta

    def test_clean_all_preserves_metadata_by_default(self, tmp_path, monkeypatch, cli_runner):
        raw, local, meta = self._setup(tmp_path, monkeypatch)
        # Answer "y" to the confirm prompt
        result = cli_runner.invoke(app, ["data", "clean", "--all"], input="y\n")
        assert result.exit_code == 0
        assert not raw.exists()
        assert not local.exists()
        assert meta.exists(), "metadata.duckdb must survive --all by default"

    def test_clean_all_with_metadata_flag_wipes_metadata(
        self, tmp_path, monkeypatch, cli_runner
    ):
        raw, local, meta = self._setup(tmp_path, monkeypatch)
        result = cli_runner.invoke(
            app, ["data", "clean", "--all", "--metadata"], input="y\n"
        )
        assert result.exit_code == 0
        assert not raw.exists()
        assert not local.exists()
        assert not meta.exists()

    def test_clean_metadata_alone_removes_only_metadata(
        self, tmp_path, monkeypatch, cli_runner
    ):
        raw, local, meta = self._setup(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["data", "clean", "--metadata"], input="y\n")
        assert result.exit_code == 0
        assert raw.exists()
        assert local.exists()
        assert not meta.exists()

    def test_clean_help_mentions_metadata(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "clean", "--help"])
        assert result.exit_code == 0
        assert "--metadata" in result.stdout
