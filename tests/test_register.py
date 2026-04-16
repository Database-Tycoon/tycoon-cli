"""Tests for `tycoon register dbt` and `tycoon register rill`."""

from __future__ import annotations

from pathlib import Path

import yaml

from tycoon.cli import app


def _scaffold_tycoon_project(root: Path, name: str = "proj") -> Path:
    """Create a minimal tycoon.yml in `root` and return the yml path."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(exist_ok=True)
    (root / "pyproject.toml").write_text(f'[project]\nname = "{name}"\n')
    yml = root / "tycoon.yml"
    yml.write_text(
        yaml.dump(
            {
                "name": name,
                "version": "0.1.0",
                "database": {
                    "raw": "data/raw.duckdb",
                    "warehouse": "data/warehouse.duckdb",
                },
                "sources": {},
            }
        )
    )
    return yml


def _make_dbt_project(dbt_dir: Path, profile: str, duckdb_path: str) -> None:
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


def _reload_config(monkeypatch, project_root: Path) -> None:
    """Rebind the module-level `config` singletons so commands see the new project."""
    from tycoon.commands import register as register_mod
    from tycoon.config import TycoonConfig

    cfg = TycoonConfig(project_root=project_root)
    monkeypatch.setattr(register_mod, "config", cfg)


class TestRegisterDbt:

    def test_register_dbt_by_local_path(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        dbt_dir = tmp_path / "proj-dbt"
        _make_dbt_project(dbt_dir, "proj", str(project / "data" / "warehouse.duckdb"))

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "dbt", str(dbt_dir)], input="\n")
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load(yml.read_text())
        assert "dbt_project_dir" in data
        assert data["stack"]["transformation"] == "dbt"
        assert data["stack"]["transformation_managed"] is False

    def test_register_dbt_refuses_nonexistent_path(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "dbt", "/nowhere/does/not/exist"])
        assert result.exit_code != 0

    def test_register_dbt_refuses_dir_without_dbt_project_yml(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        empty = tmp_path / "not-a-dbt"
        empty.mkdir()
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "dbt", str(empty)])
        assert result.exit_code != 0

    def test_register_dbt_prompts_on_overwrite(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        data = yaml.safe_load(yml.read_text())
        data["dbt_project_dir"] = "old_dbt"
        yml.write_text(yaml.dump(data))

        dbt_dir = tmp_path / "proj-dbt"
        _make_dbt_project(dbt_dir, "proj", str(project / "data" / "warehouse.duckdb"))

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)

        # "n" = don't overwrite
        result = cli_runner.invoke(app, ["register", "dbt", str(dbt_dir)], input="n\n")
        assert result.exit_code == 0
        final = yaml.safe_load(yml.read_text())
        assert final["dbt_project_dir"] == "old_dbt"

    def test_register_dbt_offers_warehouse_alignment(self, cli_runner, tmp_path, monkeypatch):
        """If dbt project targets a different DuckDB, offer to adopt it."""
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")

        dbt_dir = tmp_path / "proj-dbt"
        divergent = tmp_path / "elsewhere" / "theirs.duckdb"
        _make_dbt_project(dbt_dir, "proj", str(divergent))

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)

        # First prompt: overwrite? (no existing → no prompt). Warehouse prompt: yes.
        result = cli_runner.invoke(app, ["register", "dbt", str(dbt_dir)], input="y\n")
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load((project / "tycoon.yml").read_text())
        assert data["database"]["warehouse"] == str(divergent)


class TestRegisterRill:

    def test_register_rill_by_local_path(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        rill_dir = tmp_path / "proj-rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\n")

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "rill", str(rill_dir)])
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load(yml.read_text())
        assert "rill_dir" in data
        assert data["stack"]["bi"] == "rill"
        assert data["stack"]["bi_managed"] is False

    def test_register_rill_refuses_dir_without_rill_yaml(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        empty = tmp_path / "not-a-rill"
        empty.mkdir()
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "rill", str(empty)])
        assert result.exit_code != 0
