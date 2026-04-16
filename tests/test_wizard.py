"""Tests for the tycoon init wizard: detection + per-component prompts."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tycoon.cli import app
from tycoon.commands.init import (
    DetectionResults,
    _detect_existing,
    _extract_dbt_duckdb_path,
)


# ---------------------------------------------------------------------------
# _detect_existing
# ---------------------------------------------------------------------------


class TestDetectExisting:
    """Detection tests always run against a subdir so `target.parent` is a
    controlled space (not the shared pytest session tmpdir)."""

    def test_empty_project_detects_nothing(self, tmp_path: Path) -> None:
        project = tmp_path / "p"
        project.mkdir()
        result = _detect_existing(project)
        assert isinstance(result, DetectionResults)
        assert not result.has_any()

    def test_detects_inline_dbt_project(self, tmp_path: Path) -> None:
        project = tmp_path / "p"
        project.mkdir()
        dbt_dir = project / "dbt_project"
        dbt_dir.mkdir()
        (dbt_dir / "dbt_project.yml").write_text("name: demo\n")

        result = _detect_existing(project)
        assert [item.path for item in result.dbt if item.kind == "inline"] == [dbt_dir]

    def test_detects_dbt_in_alt_inline_dirs(self, tmp_path: Path) -> None:
        project = tmp_path / "p"
        project.mkdir()
        (project / "transformation").mkdir()
        (project / "transformation" / "dbt_project.yml").write_text("name: demo\n")

        result = _detect_existing(project)
        inline = [item.path for item in result.dbt if item.kind == "inline"]
        assert inline == [project / "transformation"]

    def test_detects_inline_rill(self, tmp_path: Path) -> None:
        project = tmp_path / "p"
        project.mkdir()
        (project / "rill").mkdir()
        (project / "rill" / "rill.yaml").write_text("compiler: rillv1\n")

        result = _detect_existing(project)
        inline = [item for item in result.rill if item.kind == "inline"]
        assert len(inline) == 1

    def test_detects_sibling_dbt_project(self, tmp_path: Path) -> None:
        project = tmp_path / "my-project"
        project.mkdir()
        sibling = tmp_path / "my-project-dbt"
        sibling.mkdir()
        (sibling / "dbt_project.yml").write_text("name: demo\n")

        result = _detect_existing(project)
        sibling_hits = [item for item in result.dbt if item.kind == "sibling"]
        assert len(sibling_hits) == 1
        assert sibling_hits[0].path == sibling

    def test_warehouse_excludes_raw_dbs(self, tmp_path: Path) -> None:
        project = tmp_path / "p"
        project.mkdir()
        data = project / "data"
        data.mkdir()
        (data / "warehouse.duckdb").write_text("")
        (data / "raw.duckdb").write_text("")
        (data / "raw_pokeapi.duckdb").write_text("")
        (data / "pokeapi_raw.duckdb").write_text("")

        result = _detect_existing(project)
        warehouse_names = {item.path.name for item in result.warehouse}
        assert warehouse_names == {"warehouse.duckdb"}

    def test_hidden_siblings_ignored(self, tmp_path: Path) -> None:
        project = tmp_path / "my-project"
        project.mkdir()
        hidden = tmp_path / ".cache"
        hidden.mkdir()
        (hidden / "dbt_project.yml").write_text("name: bad\n")

        result = _detect_existing(project)
        assert len(result.dbt) == 0


# ---------------------------------------------------------------------------
# Wizard via CLI
# ---------------------------------------------------------------------------


class TestWizardGreenfield:

    def test_default_all_managed(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "green"
        project.mkdir()
        monkeypatch.chdir(project)
        # ingestion=dlt, warehouse=local, dbt=create, rill=create, orch=dagster
        result = cli_runner.invoke(
            app,
            ["init", "--name", "green"],
            input="1\n1\n1\n1\n1\n",
        )
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load((project / "tycoon.yml").read_text())
        assert data["stack"]["ingestion"] == "dlt"
        assert data["stack"]["ingestion_managed"] is True
        assert data["stack"]["transformation"] == "dbt"
        assert data["stack"]["transformation_managed"] is True
        assert data["stack"]["bi"] == "rill"
        assert data["stack"]["bi_managed"] is True
        assert data["stack"]["orchestrator"] == "dagster"

    def test_skip_every_optional_component(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "skippy"
        project.mkdir()
        monkeypatch.chdir(project)
        # ingestion=skip, warehouse=local, dbt=skip, rill=skip, orch=skip
        result = cli_runner.invoke(
            app,
            ["init", "--name", "skippy"],
            input="3\n1\n3\n3\n3\n",
        )
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load((project / "tycoon.yml").read_text())
        assert data["stack"]["ingestion"] == "none"
        assert data["stack"]["transformation"] == "none"
        assert data["stack"]["bi"] == "none"
        assert data["stack"]["orchestrator"] == "none"
        assert "dbt_project_dir" not in data
        assert "rill_dir" not in data

    def test_creates_dbt_at_sibling_path(self, cli_runner, tmp_path, monkeypatch):
        project_dir = tmp_path / "myproj"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)
        result = cli_runner.invoke(
            app,
            ["init", "--name", "myproj"],
            input="1\n1\n1\n1\n1\n",  # dbt "create" = sibling
        )
        assert result.exit_code == 0, result.stdout

        sibling = tmp_path / "myproj-dbt"
        assert sibling.exists()
        assert (sibling / "dbt_project.yml").exists()
        assert (sibling / "profiles.yml").exists()


class TestWizardDetection:

    def test_detected_dbt_listed_as_first_option(self, cli_runner, tmp_path, monkeypatch):
        """When a dbt project exists at a canonical location, wizard offers it as option 1."""
        project = tmp_path / "myproj"
        project.mkdir()
        # Pre-existing dbt project inline
        dbt = project / "dbt_project"
        dbt.mkdir()
        (dbt / "dbt_project.yml").write_text("name: mine\nversion: '1.0.0'\nconfig-version: 2\nprofile: mine\n")

        monkeypatch.chdir(project)
        # ingestion=dlt, warehouse=local, dbt=1 (detected), rill=1 (create), orch=1
        result = cli_runner.invoke(
            app,
            ["init", "--name", "myproj"],
            input="1\n1\n1\n1\n1\n",
        )
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load((project / "tycoon.yml").read_text())
        # Detected path should be recorded; transformation_managed should be False
        # because we're using an existing project rather than scaffolding.
        assert data["stack"]["transformation_managed"] is False


class TestExtractDbtDuckdbPath:
    """_extract_dbt_duckdb_path reads a dbt project's active profile and
    returns the DuckDB path (or None for non-DuckDB / missing configs)."""

    def _make_dbt_project(self, dbt_dir: Path, profile: str, duckdb_path: str) -> None:
        dbt_dir.mkdir(parents=True, exist_ok=True)
        (dbt_dir / "dbt_project.yml").write_text(
            yaml.dump({"name": profile, "profile": profile, "config-version": 2})
        )
        (dbt_dir / "profiles.yml").write_text(
            yaml.dump(
                {
                    profile: {
                        "target": "dev",
                        "outputs": {"dev": {"type": "duckdb", "path": duckdb_path}},
                    }
                }
            )
        )

    def test_returns_absolute_duckdb_path(self, tmp_path: Path) -> None:
        dbt_dir = tmp_path / "mydbt"
        wh = tmp_path / "warehouse.duckdb"
        self._make_dbt_project(dbt_dir, "mine", str(wh))
        result = _extract_dbt_duckdb_path(dbt_dir)
        assert result == str(wh)

    def test_resolves_relative_path_against_dbt_dir(self, tmp_path: Path) -> None:
        dbt_dir = tmp_path / "mydbt"
        self._make_dbt_project(dbt_dir, "mine", "../warehouse.duckdb")
        result = _extract_dbt_duckdb_path(dbt_dir)
        # dbt_dir/../warehouse.duckdb resolves to tmp_path/warehouse.duckdb
        assert result == str((tmp_path / "warehouse.duckdb").resolve())

    def test_returns_none_for_non_duckdb_target(self, tmp_path: Path) -> None:
        dbt_dir = tmp_path / "mydbt"
        dbt_dir.mkdir()
        (dbt_dir / "dbt_project.yml").write_text(
            yaml.dump({"name": "mine", "profile": "mine", "config-version": 2})
        )
        (dbt_dir / "profiles.yml").write_text(
            yaml.dump(
                {
                    "mine": {
                        "target": "prod",
                        "outputs": {"prod": {"type": "snowflake", "account": "x"}},
                    }
                }
            )
        )
        assert _extract_dbt_duckdb_path(dbt_dir) is None

    def test_returns_none_when_profiles_missing(self, tmp_path: Path) -> None:
        dbt_dir = tmp_path / "mydbt"
        dbt_dir.mkdir()
        (dbt_dir / "dbt_project.yml").write_text(
            yaml.dump({"name": "mine", "profile": "mine"})
        )
        # Don't write profiles.yml; and ensure ~/.dbt/profiles.yml doesn't exist here
        # (test may spuriously pass if user has one — but that's orthogonal)
        # We just assert *this* dir's check returns None given no local profiles.yml.
        # If the user has a matching ~/.dbt profile, the helper may still return
        # a value — that's by design.
        home_profile = Path.home() / ".dbt" / "profiles.yml"
        if home_profile.exists():
            pytest.skip("User has ~/.dbt/profiles.yml; can't assert None here")
        assert _extract_dbt_duckdb_path(dbt_dir) is None

    def test_returns_none_when_dbt_project_yml_missing(self, tmp_path: Path) -> None:
        dbt_dir = tmp_path / "empty"
        dbt_dir.mkdir()
        assert _extract_dbt_duckdb_path(dbt_dir) is None


class TestWizardSkipSemantics:

    def test_doctor_reports_skipped_components(self, cli_runner, tmp_path, monkeypatch):
        """After skipping dbt + rill + orch, `tycoon doctor` should say 'skipped by choice'."""
        project = tmp_path / "skippy"
        project.mkdir()
        monkeypatch.chdir(project)
        init_result = cli_runner.invoke(
            app,
            ["init", "--name", "skippy"],
            input="3\n1\n3\n3\n3\n",
        )
        assert init_result.exit_code == 0

        # Reload config so doctor sees the new tycoon.yml
        from tycoon.commands import doctor as doctor_mod
        from tycoon.config import TycoonConfig

        monkeypatch.setattr(doctor_mod, "config", TycoonConfig(project_root=project))

        doctor_result = cli_runner.invoke(app, ["doctor"])
        assert doctor_result.exit_code == 0
        out = doctor_result.stdout
        assert "skipped by choice" in out
