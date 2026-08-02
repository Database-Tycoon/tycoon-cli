"""Tests for TycoonConfig path resolution."""

from __future__ import annotations

from pathlib import Path

from tycoon.config import TycoonConfig, load_config
from tycoon.project import SCHEMA_VERSION


class TestTycoonConfig:
    def test_finds_project_root_from_pyproject(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        cfg = TycoonConfig(project_root=tmp_path)
        assert cfg.root == tmp_path

    def test_raw_db_path(self, tmp_config):
        assert tmp_config.raw_db.name == "raw.duckdb"
        assert tmp_config.raw_db.parent == tmp_config.data_dir

    def test_local_db_path(self, tmp_config):
        assert tmp_config.local_db.name == "warehouse.duckdb"
        assert tmp_config.local_db.parent == tmp_config.data_dir

    def test_ensure_data_dir_creates_directory(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        cfg = TycoonConfig(project_root=tmp_path)
        # Remove data dir if it was created by fixture
        data_dir = cfg.data_dir
        if data_dir.exists():
            data_dir.rmdir()
        assert not data_dir.exists()
        cfg.ensure_data_dir()
        assert data_dir.exists()

    def test_paths_relative_to_project_root(self, tmp_config):
        assert tmp_config.data_dir == tmp_config.root / "data"
        assert tmp_config.dbt_project_dir == tmp_config.root / "dbt_project"
        assert tmp_config.rill_dir == tmp_config.root / "rill"


class TestLoadConfigSchemaWarning:
    """T2-4: load_config warns via console when tycoon.yml schema_version is stale."""

    def test_warns_when_schema_version_absent(self, tmp_path, monkeypatch):
        (tmp_path / "tycoon.yml").write_text("name: old-project\n")
        monkeypatch.chdir(tmp_path)

        calls = []
        monkeypatch.setattr("tycoon.config._warn_console", lambda msg: calls.append(msg))

        load_config()

        assert len(calls) == 1
        assert "tycoon init --upgrade" in calls[0]

    def test_warns_when_schema_version_old(self, tmp_path, monkeypatch):
        (tmp_path / "tycoon.yml").write_text(f"name: old\nschema_version: {SCHEMA_VERSION - 1}\n")
        monkeypatch.chdir(tmp_path)

        calls = []
        monkeypatch.setattr("tycoon.config._warn_console", lambda msg: calls.append(msg))

        load_config()

        assert len(calls) == 1

    def test_no_warning_when_current(self, tmp_path, monkeypatch):
        (tmp_path / "tycoon.yml").write_text(f"name: current\nschema_version: {SCHEMA_VERSION}\n")
        monkeypatch.chdir(tmp_path)

        calls = []
        monkeypatch.setattr("tycoon.config._warn_console", lambda msg: calls.append(msg))

        load_config()

        assert calls == []

    def test_no_warning_without_tycoon_yml(self, tmp_path, monkeypatch):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n')
        monkeypatch.chdir(tmp_path)

        calls = []
        monkeypatch.setattr("tycoon.config._warn_console", lambda msg: calls.append(msg))

        load_config()

        assert calls == []

    def test_errors_and_exits_when_schema_version_future(self, tmp_path, monkeypatch):
        """load_config must error and exit for a schema_version newer than SCHEMA_VERSION.

        The gate lives here (not in load_project) so the import-time singleton
        never raises and --help / init --upgrade remain reachable.
        """
        import pytest

        (tmp_path / "tycoon.yml").write_text(f"name: future\nschema_version: {SCHEMA_VERSION + 1}\n")
        monkeypatch.chdir(tmp_path)

        errors = []
        monkeypatch.setattr("tycoon.config._error_console", lambda msg: errors.append(msg))

        with pytest.raises(SystemExit) as exc_info:
            load_config()

        assert exc_info.value.code == 1
        assert len(errors) == 1
        assert "newer than this tycoon supports" in errors[0]
