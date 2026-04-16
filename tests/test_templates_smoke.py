"""Smoke tests: `tycoon init --template X` should produce a valid project
that `tycoon doctor` accepts without errors.

These are init→doctor depth only — they don't run ingestion, dbt, or Rill.
Source-run smoke tests (which hit the network) live behind an @pytest.mark.e2e
marker (not present yet; will be added when we add network e2e infra).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tycoon.cli import app


TEMPLATES = ["csv-import", "github-analytics", "nyc-transit", "weather-station"]


@pytest.mark.parametrize("template", TEMPLATES)
class TestTemplateSmoke:

    def test_init_creates_tycoon_yml(self, template, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / template
        project.mkdir()
        monkeypatch.chdir(project)
        result = cli_runner.invoke(app, ["init", "--template", template])
        assert result.exit_code == 0, f"init --template {template} failed:\n{result.stdout}"
        assert (project / "tycoon.yml").exists()

    def test_tycoon_yml_parses_and_has_sources(self, template, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / template
        project.mkdir()
        monkeypatch.chdir(project)
        cli_runner.invoke(app, ["init", "--template", template])

        data = yaml.safe_load((project / "tycoon.yml").read_text())
        assert "name" in data
        assert "database" in data
        assert "sources" in data
        assert data["sources"], f"template {template} should define at least one source"

    def test_scaffolded_dirs_exist(self, template, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / template
        project.mkdir()
        monkeypatch.chdir(project)
        cli_runner.invoke(app, ["init", "--template", template])

        assert (project / "data").exists(), f"{template}: data/ not created"
        assert (project / "rill").exists(), f"{template}: rill/ not created"

    def test_doctor_runs_clean(self, template, cli_runner, tmp_path, monkeypatch):
        """After init, `tycoon doctor` should exit 0 (warnings ok, no errors)."""
        project = tmp_path / template
        project.mkdir()
        monkeypatch.chdir(project)
        init_result = cli_runner.invoke(app, ["init", "--template", template])
        assert init_result.exit_code == 0

        from tycoon.commands import doctor as doctor_mod
        from tycoon.config import TycoonConfig

        monkeypatch.setattr(doctor_mod, "config", TycoonConfig(project_root=project))

        doctor_result = cli_runner.invoke(app, ["doctor"])
        assert doctor_result.exit_code == 0, (
            f"doctor failed for template {template}:\n{doctor_result.stdout}"
        )
