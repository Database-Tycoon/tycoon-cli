"""Tests for the `tycoon data db` subcommands."""

from __future__ import annotations

from tycoon.cli import app


class TestDbStats:

    def test_db_stats_runs(self, cli_runner):
        """data db stats should run even with no databases (shows WARN status)."""
        result = cli_runner.invoke(app, ["data", "db", "stats"])
        assert result.exit_code == 0
        # Should contain some output — either OK or WARN for databases
        assert len(result.stdout) > 0

    def test_db_stats_output_contains_database_labels(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "db", "stats"])
        output = result.stdout
        # Should mention Raw and Local databases (or equivalent labels)
        assert "Raw" in output or "raw" in output or "Local" in output or "local" in output


class TestDbQuery:

    def test_db_query_no_database_gives_error(self, cli_runner, tmp_config, monkeypatch):
        """query should fail gracefully when the database file does not exist."""
        monkeypatch.setattr("tycoon.commands.db.config", tmp_config)
        # Remove the local db if it somehow exists
        if tmp_config.local_db.exists():
            tmp_config.local_db.unlink()

        result = cli_runner.invoke(app, ["data", "db", "query", "SELECT 1"])
        assert result.exit_code != 0


class TestDbHelp:

    def test_db_help(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "db", "--help"])
        assert result.exit_code == 0
        assert "stats" in result.stdout
        assert "query" in result.stdout
        assert "clean" in result.stdout
