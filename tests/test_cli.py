"""CLI integration tests — verify help text and subcommand registration."""

from __future__ import annotations

import pytest
from tycoon.cli import app


class TestCLIHelp:
    """Verify top-level help and subcommand availability."""

    def test_help_exits_zero(self, cli_runner):
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_help_contains_expected_commands(self, cli_runner):
        result = cli_runner.invoke(app, ["--help"])
        output = result.stdout
        for cmd in ("init", "data", "start", "stop", "run", "doctor", "ask"):
            assert cmd in output, f"Expected command '{cmd}' in help output"

    def test_version_flag_prints_version(self, cli_runner):
        result = cli_runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "tycoon" in result.stdout

    def test_doctor_help(self, cli_runner):
        result = cli_runner.invoke(app, ["doctor", "--help"])
        assert result.exit_code == 0

    def test_data_help_lists_subcommands(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "--help"])
        assert result.exit_code == 0
        output = result.stdout
        for sub in ("sources", "transform", "db", "analyze"):
            assert sub in output, f"Expected data subcommand '{sub}' in help output"

    def test_data_sources_help(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "sources", "--help"])
        assert result.exit_code == 0
        output = result.stdout
        for sub in ("list", "add", "run", "catalog"):
            assert sub in output, f"Expected sources subcommand '{sub}' in help output"

    def test_start_help(self, cli_runner):
        result = cli_runner.invoke(app, ["start", "--help"])
        assert result.exit_code == 0

    def test_stop_help(self, cli_runner):
        result = cli_runner.invoke(app, ["stop", "--help"])
        assert result.exit_code == 0
