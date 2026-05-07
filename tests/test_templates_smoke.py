"""Smoke tests: `tycoon init --template X` should produce a valid project
that `tycoon doctor` accepts without errors.

These are init→doctor depth only — they don't run ingestion, dbt, or Rill.
Source-run smoke tests (which hit the network) live behind an @pytest.mark.e2e
marker (not present yet; will be added when we add network e2e infra).
"""

from __future__ import annotations


import pytest
import yaml

from tycoon.cli import app


TEMPLATES = ["csv-import", "nyc-transit"]


# Dummy parameter values for templates that declare parameters. Smoke tests
# don't care about the substituted values — they just need init to complete
# cleanly without blocking on a prompt.
_SMOKE_PARAMS: dict[str, list[str]] = {}


def _init_args(template: str) -> list[str]:
    return ["init", "--template", template, *_SMOKE_PARAMS.get(template, [])]


@pytest.mark.parametrize("template", TEMPLATES)
class TestTemplateSmoke:

    def test_init_creates_tycoon_yml(self, template, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / template
        project.mkdir()
        monkeypatch.chdir(project)
        result = cli_runner.invoke(app, _init_args(template))
        assert result.exit_code == 0, f"init --template {template} failed:\n{result.stdout}"
        assert (project / "tycoon.yml").exists()

    def test_tycoon_yml_parses_and_has_sources(self, template, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / template
        project.mkdir()
        monkeypatch.chdir(project)
        cli_runner.invoke(app, _init_args(template))

        data = yaml.safe_load((project / "tycoon.yml").read_text())
        assert "name" in data
        assert "database" in data
        assert "sources" in data
        assert data["sources"], f"template {template} should define at least one source"

    def test_scaffolded_dirs_exist(self, template, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / template
        project.mkdir()
        monkeypatch.chdir(project)
        cli_runner.invoke(app, _init_args(template))

        assert (project / "data").exists(), f"{template}: data/ not created"
        assert (project / "rill").exists(), f"{template}: rill/ not created"

    def test_doctor_runs_clean(self, template, cli_runner, tmp_path, monkeypatch):
        """After init, `tycoon doctor` should exit 0 (warnings ok, no errors)."""
        project = tmp_path / template
        project.mkdir()
        monkeypatch.chdir(project)
        init_result = cli_runner.invoke(app, _init_args(template))
        assert init_result.exit_code == 0

        from tycoon.commands import doctor as doctor_mod
        from tycoon.config import TycoonConfig

        monkeypatch.setattr(doctor_mod, "config", TycoonConfig(project_root=project))

        doctor_result = cli_runner.invoke(app, ["doctor"])
        assert doctor_result.exit_code == 0, (
            f"doctor failed for template {template}:\n{doctor_result.stdout}"
        )

    def test_no_unresolved_placeholders(self, template, cli_runner, tmp_path, monkeypatch):
        """After init, no `{{ param }}` placeholders should remain in tycoon.yml."""
        project = tmp_path / template
        project.mkdir()
        monkeypatch.chdir(project)
        cli_runner.invoke(app, _init_args(template))

        content = (project / "tycoon.yml").read_text()
        assert "{{" not in content and "}}" not in content, (
            f"{template}: unresolved placeholders remain in tycoon.yml:\n{content}"
        )
