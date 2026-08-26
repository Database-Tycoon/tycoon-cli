"""`tycoon-city` — the renderer's own console script — is a Typer app, so its
help renders the way `tycoon city --help` does.

Emmanuel, reviewing the city stack: `tycoon-city demo --help` rendered
argparse-style beside `tycoon city --help`'s Typer style and read like two
different tools. The script now points at `tycoon_city.cli:app`; the argparse
`main()`s stay for `python -m` and Docker, and both surfaces land in the same
`run…()` functions.

Lives in tests/ (not tests/tycoon_city/) so the default run collects it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from tycoon_city import webserve
from tycoon_city.cli import app
from tycoon_city.demo import cli as demo_cli

runner = CliRunner()


@pytest.fixture(autouse=True)
def _no_env(monkeypatch):
    for var in (webserve.DB_ENV, webserve.DIST_ENV, webserve.HOST_ENV, webserve.THEME_ENV, "PORT"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def fake_server(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(webserve, "run_server", lambda **kw: calls.append(kw) or 0)
    return calls


@pytest.fixture
def fake_demo(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(demo_cli, "run", lambda **kw: calls.append(kw) or 0)
    return calls


class TestHelpRendering:
    def test_root_help_is_typer_and_lists_both_commands(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout, "Typer/Click capitalise Usage; argparse's `usage:` is what this replaces"
        assert "demo" in result.stdout
        assert "serve" in result.stdout

    def test_serve_help_carries_the_server_options(self):
        result = runner.invoke(app, ["serve", "--help"])
        assert result.exit_code == 0
        for flag in ("--dist", "--theme", "--pricing", "--port", "--host"):
            assert flag in result.stdout, flag

    def test_help_renders_in_the_same_style_as_the_tycoon_command(self):
        """The actual complaint: `tycoon-city demo --help` beside `tycoon city
        --help` looked like two tools. `tycoon` renders plain (rich_markup_mode
        None) with a `-h` alias; the script must match, not merely be Typer."""
        for argv in (["--help"], ["demo", "--help"], ["serve", "-h"]):
            result = runner.invoke(app, argv)
            assert result.exit_code == 0, argv
            assert "╭" not in result.stdout, f"{argv}: Rich box rendering; `tycoon` renders plain"
            assert "-h, --help" in result.stdout, argv

    def test_demo_help_is_the_demos_own_and_typer(self):
        result = runner.invoke(app, ["demo", "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout
        assert "usage: " not in result.stdout
        assert "demo catalog" in result.stdout
        for flag in ("--port", "--host", "--theme", "--dist"):
            assert flag in result.stdout, flag
        # Serve-only surface must not leak into the demo's help: the catalog is
        # generated and free, so there is nothing to point --pricing at.
        assert "--pricing" not in result.stdout


class TestServe:
    def test_positional_path_and_options_reach_the_server(self, fake_server):
        result = runner.invoke(app, ["/tmp/x.duckdb", "--port", "8123", "--host", "0.0.0.0", "--theme", "default"])
        assert result.exit_code == 0, result.output
        [call] = fake_server
        assert call["db_path"] == "/tmp/x.duckdb"
        assert call["port"] == 8123
        assert call["host"] == "0.0.0.0"
        assert call["pricing"] is None
        assert call["dist"] is None

    def test_explicit_serve_form_is_the_same_command(self, fake_server):
        runner.invoke(app, ["serve", "/tmp/x.duckdb", "--port", "8123"])
        [call] = fake_server
        assert call["db_path"] == "/tmp/x.duckdb"
        assert call["port"] == 8123

    def test_options_before_the_path_still_route_to_serve(self, fake_server):
        runner.invoke(app, ["--port", "8123", "/tmp/x.duckdb"])
        [call] = fake_server
        assert call["db_path"] == "/tmp/x.duckdb"

    def test_db_path_falls_back_to_the_env_var(self, fake_server, monkeypatch):
        """Docker images set $DATABASE_TYCOON_DB instead of passing a path."""
        monkeypatch.setenv(webserve.DB_ENV, "/data/env.duckdb")
        monkeypatch.setenv("PORT", "8555")
        assert runner.invoke(app, []).exit_code == 0
        [call] = fake_server
        assert call["db_path"] == "/data/env.duckdb"
        assert call["port"] == 8555

    def test_no_database_anywhere_is_exit_1_with_the_reason(self):
        result = runner.invoke(app, [])
        assert result.exit_code == 1
        assert "no database" in result.output

    def test_server_exit_code_is_propagated(self, monkeypatch):
        monkeypatch.setattr(webserve, "run_server", lambda **kw: 1)
        assert runner.invoke(app, ["/tmp/x.duckdb"]).exit_code == 1


class TestDemo:
    def test_options_reach_the_demo_runner(self, fake_demo):
        result = runner.invoke(app, ["demo", "--port", "8199", "--dist", "/tmp/dist"])
        assert result.exit_code == 0, result.output
        [call] = fake_demo
        assert call["port"] == 8199
        assert call["host"] == webserve.DEFAULT_HOST
        assert call["theme"] == "default"
        assert call["dist"] == Path("/tmp/dist")

    def test_demo_does_not_start_the_ordinary_server(self, fake_demo, fake_server):
        runner.invoke(app, ["demo"])
        assert fake_demo and not fake_server

    def test_demo_exit_code_is_propagated(self, monkeypatch):
        monkeypatch.setattr(demo_cli, "run", lambda **kw: 1)
        assert runner.invoke(app, ["demo"]).exit_code == 1


class TestArgparseSurfacesStillLand:
    """`python -m tycoon_city.webserve [demo]` keeps working and shares the
    implementation — one demo, one server, two ways to type each."""

    def test_webserve_main_delegates_to_run_server(self, fake_server):
        assert webserve.main(["/tmp/x.duckdb", "--port", "8123"]) == 0
        [call] = fake_server
        assert call["db_path"] == "/tmp/x.duckdb"
        assert call["port"] == 8123

    def test_demo_main_delegates_to_run(self, fake_demo):
        assert demo_cli.main(["--port", "8199"]) == 0
        [call] = fake_demo
        assert call["port"] == 8199
