"""Tests for TycoonConfig path resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from tycoon.config import TycoonConfig, load_config, resolve_contained_path
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
        (tmp_path / "tycoon.yml").write_text(f"name: future\nschema_version: {SCHEMA_VERSION + 1}\n")
        monkeypatch.chdir(tmp_path)

        errors = []
        monkeypatch.setattr("tycoon.config._error_console", lambda msg: errors.append(msg))

        with pytest.raises(SystemExit) as exc_info:
            load_config()

        assert exc_info.value.code == 1
        assert len(errors) == 1
        assert "newer than this tycoon supports" in errors[0]


class TestResolveContainedPath:
    """gh-259: `resolve_contained_path` is now a standalone function, shared
    by `TycoonConfig` (runtime) and the `tycoon init` wizard (prompt time),
    not just a private `TycoonConfig` method."""

    def test_inline_path_accepted(self, tmp_path: Path):
        root = tmp_path / "proj"
        root.mkdir()
        assert resolve_contained_path("dbt_project", root, "dbt_project_dir") == (root / "dbt_project").resolve()

    def test_sibling_path_accepted(self, tmp_path: Path):
        root = tmp_path / "proj"
        root.mkdir()
        assert resolve_contained_path("../proj-dbt", root, "dbt_project_dir") == (tmp_path / "proj-dbt").resolve()

    def test_traversal_beyond_parent_rejected(self, tmp_path: Path):
        root = tmp_path / "proj"
        root.mkdir()
        with pytest.raises(ValueError, match="outside the project's parent"):
            resolve_contained_path("../../../escape", root, "dbt_project_dir")

    def test_error_message_includes_the_given_field_name(self, tmp_path: Path):
        root = tmp_path / "proj"
        root.mkdir()
        with pytest.raises(ValueError, match="dbt project path"):
            resolve_contained_path("/etc/cron.d", root, "dbt project path")

    def test_error_message_explains_the_boundary_and_a_fix(self, tmp_path: Path):
        """An out-of-bounds path (e.g. an existing project that lives in a
        completely unrelated part of the filesystem, not a sibling or a
        traversal attempt) should get an error that explains *why* it's
        rejected and what to do, not just that it was rejected."""
        root = tmp_path / "codespace" / "experiments"
        root.mkdir(parents=True)
        unrelated = tmp_path / "projects" / "dbt"
        unrelated.mkdir(parents=True)

        with pytest.raises(ValueError) as exc_info:
            resolve_contained_path(str(unrelated), root, "dbt project path")

        message = str(exc_info.value)
        assert "security boundary" in message
        assert f"Move the project under {root.parent}" in message
