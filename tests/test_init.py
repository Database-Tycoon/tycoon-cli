"""Tests for `tycoon init` command and template scaffolding."""

from __future__ import annotations

import yaml

from tycoon.cli import app
from tycoon.project import SCHEMA_VERSION, load_project
from tycoon.scaffolding.templates import list_templates, scaffold_blank_project


class TestInitHelp:
    """Verify the init command is registered and has help text."""

    def test_init_help_exits_zero(self, cli_runner):
        result = cli_runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "--template" in result.stdout
        assert "--name" in result.stdout
        assert "--list-templates" in result.stdout
        assert "--upgrade" in result.stdout

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

    def test_gitignore_excludes_metadata_duckdb(self, tmp_path, monkeypatch):
        """Regression: observability metadata DB must not get committed."""
        monkeypatch.chdir(tmp_path)
        scaffold_blank_project(tmp_path, "test-project")
        content = (tmp_path / ".gitignore").read_text()
        assert ".tycoon/metadata.duckdb" in content

    def test_scaffolded_yml_loads_with_load_project(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        scaffold_blank_project(tmp_path, "test-project")

        project = load_project(tmp_path)
        assert project is not None
        assert project.name == "test-project"
        assert project.database.raw == "data/raw.duckdb"

    def test_scaffold_with_explicit_warehouse_path_keeps_raw_distinct(self, tmp_path, monkeypatch):
        """Regression for #11: when the wizard returns a local DuckDB path,
        raw must NOT equal warehouse — dbt-duckdb would reject the double-attach."""
        from tycoon.project import StackConfig

        monkeypatch.chdir(tmp_path)
        scaffold_blank_project(
            tmp_path,
            "test-project",
            stack=StackConfig(),
            existing_warehouse_path="data/warehouse.duckdb",
        )

        data = yaml.safe_load((tmp_path / "tycoon.yml").read_text())
        assert data["database"]["warehouse"] == "data/warehouse.duckdb"
        assert data["database"]["raw"] == "data/raw.duckdb"
        assert data["database"]["raw"] != data["database"]["warehouse"]

    def test_blank_scaffold_via_cli(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Per-component wizard: ingestion=dlt, warehouse=local, dbt=create, rill=create
        result = cli_runner.invoke(
            app,
            ["init", "--name", "my-project"],
            input="1\n1\n1\n1\n",
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

    def test_template_scaffold_preserves_template_formatting(self, tmp_path, monkeypatch):
        """Stamping schema_version must not flatten the template's layout (#185)."""
        monkeypatch.chdir(tmp_path)
        from tycoon.scaffolding.templates import get_template_path, scaffold_from_template

        template_text = (get_template_path("nyc-transit") / "tycoon.yml").read_text()
        scaffold_from_template(tmp_path, "nyc-transit")
        scaffolded = (tmp_path / "tycoon.yml").read_text()

        # ruamel may re-indent sequence items, so compare stripped lines —
        # the point is that no content, comment, or blank separator is lost.
        scaffolded_lines = [line.strip() for line in scaffolded.splitlines()]
        for line in template_text.splitlines():
            assert line.strip() in scaffolded_lines

        assert scaffolded.count("\n\n") >= template_text.count("\n\n")

        data = yaml.safe_load(scaffolded)
        assert data["schema_version"] == SCHEMA_VERSION
        assert data["version"] == "0.1.0"
        assert "metadata" in data


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


class TestTemplateParameterization:
    """v0.1.3: templates declare parameters in template.yml and init
    substitutes them into tycoon.yml + other text files."""

    def test_load_parameters_returns_empty_for_template_without_metadata(self):
        """nyc-transit has no template.yml → loader returns []."""
        from tycoon.scaffolding.templates import load_template_parameters

        assert load_template_parameters("nyc-transit") == []

    def test_load_parameters_normalizes_github_analytics_entries(self):
        from tycoon.scaffolding.templates import load_template_parameters

        params = load_template_parameters("github-analytics")
        names = [p["name"] for p in params]
        assert names == ["owner", "repo"]
        for p in params:
            assert p["required"] is True
            assert p["description"]
            assert p["example"]

    def test_load_parameters_weather_station_has_four_params(self):
        from tycoon.scaffolding.templates import load_template_parameters

        names = [p["name"] for p in load_template_parameters("weather-station")]
        assert names == ["station_id", "office", "gridX", "gridY"]

    def test_substitute_params_replaces_braces(self):
        from tycoon.scaffolding.templates import _substitute_params

        out = _substitute_params(
            "hello {{ name }} and {{name}} plus {{  name  }}",
            {"name": "world"},
        )
        assert out == "hello world and world plus world"

    def test_substitute_params_leaves_unknown_placeholders_alone(self):
        from tycoon.scaffolding.templates import _substitute_params

        out = _substitute_params("{{ known }} vs {{ unknown }}", {"known": "yes"})
        assert out == "yes vs {{ unknown }}"

    def test_scaffold_with_params_substitutes_in_tycoon_yml(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(
            app,
            [
                "init",
                "--template",
                "github-analytics",
                "--param",
                "owner=acme",
                "--param",
                "repo=widgets",
            ],
        )
        assert result.exit_code == 0, result.stdout

        content = (tmp_path / "tycoon.yml").read_text()
        assert "acme" in content
        assert "widgets" in content
        assert "{{" not in content and "}}" not in content

    def test_template_yml_not_copied_to_target(self, cli_runner, tmp_path, monkeypatch):
        """template.yml is build metadata — must not land in the user's project."""
        monkeypatch.chdir(tmp_path)
        cli_runner.invoke(
            app,
            [
                "init",
                "--template",
                "github-analytics",
                "--param",
                "owner=a",
                "--param",
                "repo=b",
            ],
        )
        assert not (tmp_path / "template.yml").exists()

    def test_missing_required_param_errors_out_in_noninteractive(self, cli_runner, tmp_path, monkeypatch):
        """When no --param is supplied and stdin is empty (CliRunner default),
        typer.prompt fails. We just need it to not silently succeed."""
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(app, ["init", "--template", "github-analytics"])
        assert result.exit_code != 0

    def test_param_malformed_is_rejected(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(
            app,
            ["init", "--template", "github-analytics", "--param", "malformed"],
        )
        assert result.exit_code != 0

    def test_unknown_param_is_warned_but_not_fatal(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(
            app,
            [
                "init",
                "--template",
                "github-analytics",
                "--param",
                "owner=a",
                "--param",
                "repo=b",
                "--param",
                "bogus=xyz",
            ],
        )
        assert result.exit_code == 0
        # The unknown-param warning goes to stdout via the console helper
        assert "bogus" in result.stdout.lower() or "unknown parameter" in result.stdout.lower()


class TestUpgrade:
    """tycoon init --upgrade migrates tycoon.yml to the current schema version."""

    def test_upgrade_no_tycoon_yml_exits_nonzero(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(app, ["init", "--upgrade"])
        assert result.exit_code != 0

    def test_upgrade_migrates_outdated_yml(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "tycoon.yml").write_text("name: old-project\nversion: 1.0.0\n")

        result = cli_runner.invoke(app, ["init", "--upgrade"])

        assert result.exit_code == 0
        p = load_project(tmp_path)
        assert p is not None
        assert p.schema_version == SCHEMA_VERSION

    def test_upgrade_already_current_reports_up_to_date(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "tycoon.yml").write_text(
            f"name: current\nschema_version: {SCHEMA_VERSION}\n"
            "metadata:\n  backend: duckdb_file\n  path: .tycoon/metadata.duckdb\n"
        )

        result = cli_runner.invoke(app, ["init", "--upgrade"])

        assert result.exit_code == 0
        assert "up to date" in result.stdout

    def test_upgrade_future_schema_version_exits_nonzero_cleanly(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "tycoon.yml").write_text(f"name: future\nschema_version: {SCHEMA_VERSION + 1}\n")

        result = cli_runner.invoke(app, ["init", "--upgrade"])

        assert result.exit_code != 0
        assert "newer than this tycoon supports" in result.output
