"""Tests for `tycoon data sources` subcommands and source_installer."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from tycoon.cli import app
from tycoon.project import SourceConfig, TycoonProject, load_project, save_project


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_YML = """\
name: test-project
version: 0.1.0
database:
  raw: data/raw.duckdb
  warehouse: data/warehouse.duckdb
sources:
  nyc-dot:
    type: rest_api
    schema: raw_nyc_dot
    config:
      base_url: https://data.cityofnewyork.us/resource/
  my-db:
    type: sql_database
    schema: raw_db
    config:
      connection_string: postgresql://localhost/test
"""


def _setup_project(tmp_path: Path) -> None:
    """Write a tycoon.yml and pyproject.toml to tmp_path."""
    (tmp_path / "tycoon.yml").write_text(_SAMPLE_YML)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')


# ---------------------------------------------------------------------------
# CLI help / registration
# ---------------------------------------------------------------------------


class TestSourcesHelp:
    """Verify the sources sub-app is registered and help text works."""

    def test_sources_in_data_help(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "--help"])
        assert "sources" in result.stdout

    def test_sources_help_lists_subcommands(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "sources", "--help"])
        assert result.exit_code == 0
        for sub in ("list", "add", "remove", "catalog", "run"):
            assert sub in result.stdout, f"Expected subcommand '{sub}' in sources help"


# ---------------------------------------------------------------------------
# tycoon data sources list
# ---------------------------------------------------------------------------


class TestSourcesList:
    """Verify `tycoon data sources list` output."""

    def test_list_shows_sources(self, cli_runner, tmp_path, monkeypatch):
        _setup_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        # Reload config for the new cwd
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        result = cli_runner.invoke(app, ["data", "sources", "list"])
        assert result.exit_code == 0
        assert "nyc-dot" in result.stdout
        assert "rest_api" in result.stdout
        assert "raw_nyc_dot" in result.stdout

    def test_list_shows_empty_message(self, cli_runner, tmp_path, monkeypatch):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "tycoon.yml").write_text("name: empty\nsources: {}\n")
        monkeypatch.chdir(tmp_path)
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        result = cli_runner.invoke(app, ["data", "sources", "list"])
        assert result.exit_code == 0
        assert "no sources" in result.stdout.lower() or "tycoon" in result.stdout.lower()

    def test_list_errors_without_project(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        result = cli_runner.invoke(app, ["data", "sources", "list"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# tycoon data sources show
# ---------------------------------------------------------------------------


class TestSourcesShow:
    """Verify `tycoon data sources show <name>` output."""

    def test_show_existing_source(self, cli_runner, tmp_path, monkeypatch):
        _setup_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        # show is a subcommand of list: tycoon data sources list show <name>
        result = cli_runner.invoke(app, ["data", "sources", "list", "show", "nyc-dot"])
        assert result.exit_code == 0
        assert "rest_api" in result.stdout
        assert "raw_nyc_dot" in result.stdout
        assert "base_url" in result.stdout

    def test_show_nonexistent_source(self, cli_runner, tmp_path, monkeypatch):
        _setup_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        result = cli_runner.invoke(app, ["data", "sources", "list", "show", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "not found" in (result.stderr or "").lower()


# ---------------------------------------------------------------------------
# tycoon data sources remove
# ---------------------------------------------------------------------------


class TestSourcesRemove:
    """Verify `tycoon data sources remove <name>` behaviour."""

    def test_remove_with_confirmation(self, cli_runner, tmp_path, monkeypatch):
        _setup_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        result = cli_runner.invoke(app, ["data", "sources", "remove", "nyc-dot"], input="y\n")
        assert result.exit_code == 0
        assert "removed" in result.stdout.lower()

        # Verify it's gone from disk
        project = load_project(tmp_path)
        assert project is not None
        assert "nyc-dot" not in project.sources

    def test_remove_abort(self, cli_runner, tmp_path, monkeypatch):
        _setup_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        result = cli_runner.invoke(app, ["data", "sources", "remove", "nyc-dot"], input="n\n")
        assert result.exit_code == 1  # typer.confirm abort exits 1

        # Verify it's still there
        project = load_project(tmp_path)
        assert project is not None
        assert "nyc-dot" in project.sources

    def test_remove_nonexistent_source(self, cli_runner, tmp_path, monkeypatch):
        _setup_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        result = cli_runner.invoke(app, ["data", "sources", "remove", "nonexistent"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# SourceConfig model and round-trip
# ---------------------------------------------------------------------------


class TestSourceConfigModel:
    """Test SourceConfig creation and save/load round-trip."""

    def test_source_config_creation(self):
        src = SourceConfig(
            type="rest_api",
            schema="raw_test",
            config={"base_url": "https://example.com"},
        )
        assert src.type == "rest_api"
        assert src.schema_name == "raw_test"
        assert src.config["base_url"] == "https://example.com"
        assert src.tables is None

    def test_source_config_with_tables(self):
        src = SourceConfig(
            type="sql_database",
            schema="raw_db",
            config={"connection_string": "postgresql://localhost/test"},
            tables=["users", "orders"],
        )
        assert src.tables == ["users", "orders"]

    def test_add_source_round_trip(self, tmp_path):
        """Adding a source to a project and reloading preserves it."""
        project = TycoonProject(name="round-trip-test")
        project.sources["new-api"] = SourceConfig(
            type="rest_api",
            schema="raw_new_api",
            config={"base_url": "https://api.example.com"},
        )
        save_project(project, tmp_path)

        loaded = load_project(tmp_path)
        assert loaded is not None
        assert "new-api" in loaded.sources
        assert loaded.sources["new-api"].type == "rest_api"
        assert loaded.sources["new-api"].schema_name == "raw_new_api"
        assert loaded.sources["new-api"].config["base_url"] == "https://api.example.com"


# ---------------------------------------------------------------------------
# source_installer
# ---------------------------------------------------------------------------


class TestSourceInstaller:
    """Tests for the dlt extra installer utilities."""

    def test_is_dlt_extra_available_returns_bool(self):
        from tycoon.ingestion.source_installer import is_dlt_extra_available

        result = is_dlt_extra_available("rest_api")
        assert isinstance(result, bool)

    def test_is_dlt_extra_available_nonexistent(self):
        from tycoon.ingestion.source_installer import is_dlt_extra_available

        result = is_dlt_extra_available("totally_fake_source_type_xyz")
        assert result is False

    def test_dlt_extras_dict_has_known_types(self):
        from tycoon.ingestion.source_installer import DLT_EXTRAS

        assert "rest_api" in DLT_EXTRAS
        assert "sql_database" in DLT_EXTRAS
        assert "filesystem" in DLT_EXTRAS

    def test_install_dlt_extra_returns_bool(self):
        """Verify install_dlt_extra returns a bool (don't actually install)."""
        from tycoon.ingestion.source_installer import install_dlt_extra

        # We don't want to actually run pip in tests, but we can verify
        # the function signature and return type by mocking subprocess
        from unittest.mock import patch, MagicMock

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("tycoon.ingestion.source_installer.subprocess.run", return_value=mock_result):
            result = install_dlt_extra("rest_api")
            assert result is True

    def test_install_dlt_extra_failure(self):
        """Verify install_dlt_extra returns False on failure."""
        from tycoon.ingestion.source_installer import install_dlt_extra
        from unittest.mock import patch, MagicMock

        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("tycoon.ingestion.source_installer.subprocess.run", return_value=mock_result):
            result = install_dlt_extra("rest_api")
            assert result is False
