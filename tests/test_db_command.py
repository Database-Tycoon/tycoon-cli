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
