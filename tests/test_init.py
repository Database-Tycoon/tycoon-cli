"""Tests for `tycoon init` command and template scaffolding."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from tycoon.cli import app
from tycoon.project import load_project
from tycoon.scaffolding.templates import list_templates, scaffold_blank_project


class TestInitHelp:
    """Verify the init command is registered and has help text."""

    def test_init_help_exits_zero(self, cli_runner):
        result = cli_runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "--template" in result.stdout
        assert "--name" in result.stdout
        assert "--list-templates" in result.stdout

    def test_init_appears_in_top_level_help(self, cli_runner):
        result = cli_runner.invoke(app, ["--help"])
        assert "init" in result.stdout


class TestListTemplates:
    """Verify template listing works."""

    def test_list_templates_includes_nyc_transit(self):
        templates = list_templates()
        assert "nyc-transit" in templates

    def test_list_templates_via_cli(self, cli_runner):
        result = cli_runner.invoke(app, ["init", "--list-templates"])
        assert result.exit_code == 0
        assert "nyc-transit" in result.stdout


class TestBlankScaffold:
    """Verify blank project scaffolding."""

    def test_creates_tycoon_yml(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        scaffold_blank_project(tmp_path, "test-project")

        yml_path = tmp_path / "tycoon.yml"
        assert yml_path.exists()

        data = yaml.safe_load(yml_path.read_text())
        assert data["name"] == "test-project"
        assert "database" in data
        assert data["database"]["raw"] == "data/raw.duckdb"
        assert data["database"]["warehouse"] == "data/warehouse.duckdb"
        assert data["sources"] == {}

    def test_creates_data_directory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        scaffold_blank_project(tmp_path, "test-project")
        assert (tmp_path / "data").is_dir()

    def test_creates_dbt_project(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        scaffold_blank_project(tmp_path, "test-project")

        dbt_dir = tmp_path / "dbt_project"
        assert dbt_dir.is_dir()
        assert (dbt_dir / "dbt_project.yml").exists()
        assert (dbt_dir / "profiles.yml").exists()

    def test_creates_gitignore(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        scaffold_blank_project(tmp_path, "test-project")
        assert (tmp_path / ".gitignore").exists()

    def test_scaffolded_yml_loads_with_load_project(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        scaffold_blank_project(tmp_path, "test-project")

        project = load_project(tmp_path)
        assert project is not None
        assert project.name == "test-project"
        assert project.database.raw == "data/raw.duckdb"

    def test_blank_scaffold_via_cli(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Per-component wizard: ingestion=dlt, warehouse=local, dbt=create,
        # rill=create, orchestrator=dagster
        result = cli_runner.invoke(
            app,
            ["init", "--name", "my-project"],
            input="1\n1\n1\n1\n1\n",
        )
        assert result.exit_code == 0, f"init failed: {result.stdout}"
        assert (tmp_path / "tycoon.yml").exists()


class TestTemplateScaffold:
    """Verify template-based scaffolding."""

    def test_template_scaffold_creates_tycoon_yml(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(app, ["init", "--template", "nyc-transit"])
        assert result.exit_code == 0

        yml_path = tmp_path / "tycoon.yml"
        assert yml_path.exists()

        data = yaml.safe_load(yml_path.read_text())
        assert data["name"] == "nyc-transit-demo"
        assert "sources" in data
        assert "nyc-dot" in data["sources"]

    def test_template_scaffold_loads_with_load_project(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from tycoon.scaffolding.templates import scaffold_from_template

        scaffold_from_template(tmp_path, "nyc-transit")
        project = load_project(tmp_path)
        assert project is not None
        assert project.name == "nyc-transit-demo"
        assert "nyc-dot" in project.sources

    def test_template_creates_data_dir(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cli_runner.invoke(app, ["init", "--template", "nyc-transit"])
        assert (tmp_path / "data").is_dir()


class TestInitRefusesOverwrite:
    """Verify init refuses to overwrite existing tycoon.yml."""

    def test_refuses_when_tycoon_yml_exists(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "tycoon.yml").write_text("name: existing\n")

        result = cli_runner.invoke(app, ["init"])
        assert result.exit_code == 1
        assert "already exists" in result.stdout

    def test_refuses_with_template_when_tycoon_yml_exists(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "tycoon.yml").write_text("name: existing\n")

        result = cli_runner.invoke(app, ["init", "--template", "nyc-transit"])
        assert result.exit_code == 1


class TestInvalidTemplate:
    """Verify error handling for bad template names."""

    def test_invalid_template_name(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(app, ["init", "--template", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "not found" in (result.stderr or "").lower()
