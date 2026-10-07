"""Tests for TycoonConfig path resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from tycoon.config import TycoonConfig, display_target, load_config, redact_secrets, resolve_contained_path
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

    def test_resolve_contained_path_appends_runtime_remediation(self, tmp_path: Path):
        """A tycoon.yml already exists at runtime, so "point tycoon.yml at a
        path within it" is a real, actionable fix here — unlike at wizard
        prompt time, before one is written (gh-259 review)."""
        cfg = TycoonConfig(project_root=tmp_path / "codespace" / "proj")
        cfg.root.mkdir(parents=True)

        with pytest.raises(ValueError) as exc_info:
            cfg._resolve_contained_path(str(tmp_path / "unrelated"), "dbt_project_dir")

        message = str(exc_info.value)
        assert "security boundary" in message
        assert "point tycoon.yml at a path within it" in message


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
    not just a private `TycoonConfig` method.

    The inline/sibling/traversal acceptance-and-rejection cases are covered
    by `TestPathContainment` in test_project_validation.py, which reaches
    this same function through `TycoonConfig`'s one-line passthrough — kept
    here are only the cases unique to this level: the message's own wording
    (gh-259 review, to avoid two files needing an update if the boundary
    rule's cases change)."""

    def test_error_message_includes_the_given_field_name(self, tmp_path: Path):
        root = tmp_path / "proj"
        root.mkdir()
        with pytest.raises(ValueError, match="dbt project path"):
            resolve_contained_path("/etc/cron.d", root, "dbt project path")

    def test_error_message_explains_the_boundary(self, tmp_path: Path):
        """An out-of-bounds path (e.g. an existing project that lives in a
        completely unrelated part of the filesystem, not a sibling or a
        traversal attempt) should get an error that explains *why* it's
        rejected, stating the fact without prescribing a fix: `field` is a
        label for which caller raised this, not a remediation seam, and
        "point tycoon.yml at ..." only makes sense once one exists to point
        (gh-259 review). Callers append their own remediation — see
        TycoonConfig._resolve_contained_path's test for the runtime one."""
        root = tmp_path / "codespace" / "experiments"
        root.mkdir(parents=True)
        unrelated = tmp_path / "projects" / "dbt"
        unrelated.mkdir(parents=True)

        with pytest.raises(ValueError) as exc_info:
            resolve_contained_path(str(unrelated), root, "dbt project path")

        message = str(exc_info.value)
        assert "security boundary" in message
        assert str(root.parent) in message
        assert "Move the project" not in message
        assert "point tycoon.yml" not in message


class TestWarehouseTarget:
    def _config(self, tmp_path, warehouse: str):
        from tycoon.config import TycoonConfig

        (tmp_path / "tycoon.yml").write_text(f"name: test\nsources: {{}}\ndatabase:\n  warehouse: '{warehouse}'\n")
        return TycoonConfig(project_root=tmp_path)

    def test_motherduck_target_passes_through(self, tmp_path):
        cfg = self._config(tmp_path, "md:dogfood_dbt_prod")
        assert cfg.warehouse_target == "md:dogfood_dbt_prod"
        assert cfg.warehouse_is_motherduck
        assert cfg.local_db is None

    def test_local_target_resolves_under_root(self, tmp_path):
        cfg = self._config(tmp_path, "data/wh.duckdb")
        assert cfg.warehouse_target == str(tmp_path / "data" / "wh.duckdb")
        assert not cfg.warehouse_is_motherduck
        assert cfg.local_db == tmp_path / "data" / "wh.duckdb"

    def test_motherduck_raw_passes_through(self, tmp_path, capsys):
        (tmp_path / "tycoon.yml").write_text(
            "name: test\nsources: {}\ndatabase:\n  warehouse: 'md:x'\n  raw: 'md:x_raw?motherduck_token=SECRET123'\n"
        )
        cfg = TycoonConfig(project_root=tmp_path)
        assert cfg.raw_is_motherduck
        assert cfg.raw_target == "md:x_raw?motherduck_token=SECRET123"
        # Ingestion only writes local files, so the file path exits clearly.
        with pytest.raises(SystemExit):
            _ = cfg.raw_db
        out = capsys.readouterr()
        assert "MotherDuck (md:x_raw)" in out.out + out.err
        assert "SECRET123" not in out.out + out.err


class TestRedaction:
    @pytest.mark.parametrize(
        ("target", "shown"),
        [
            ("md:", "md:"),
            ("md:db", "md:db"),
            ("md:db?motherduck_token=x&saas_mode=true", "md:db"),
            ("/tmp/proj/data/warehouse.duckdb", "/tmp/proj/data/warehouse.duckdb"),
        ],
    )
    def test_display_target(self, target, shown):
        assert display_target(target) == shown

    def test_redact_secrets_in_error_text(self):
        msg = "IO Error: can't open 'md:db?motherduck_token=SECRET123&x=1' (motherduck_token=SECRET123)"
        out = redact_secrets(msg)
        assert "SECRET123" not in out
        assert "'md:db'" in out

    @pytest.mark.parametrize(
        ("text", "redacted"),
        [
            ("motherduck_token=abc123", "motherduck_token=***"),
            ("motherduck_token='abc123'", "motherduck_token='***'"),
            ('motherduck_token="abc123"', 'motherduck_token="***"'),
            ("SET motherduck_token = 'abc123'", "SET motherduck_token = '***'"),
            ("MotherDuck_Token='abc123'", "MotherDuck_Token='***'"),
            ("md:db?motherduck_token=abc123&saas_mode=true", "md:db"),
            (
                "Error: SET motherduck_token = 'abc123' failed (token expired)",
                "Error: SET motherduck_token = '***' failed (token expired)",
            ),
            ("motherduck_token=abc123&saas_mode=true", "motherduck_token=***&saas_mode=true"),
            ("access_token='abc123' was rejected", "access_token='abc123' was rejected"),
        ],
    )
    def test_redact_secrets_token_forms(self, text, redacted):
        assert redact_secrets(text) == redacted
