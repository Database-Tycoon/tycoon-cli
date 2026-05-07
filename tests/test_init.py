"""Tests for `tycoon init` command and template scaffolding."""

from __future__ import annotations


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
        # Per-component wizard: ingestion=dlt, warehouse=local, dbt=create,
        # rill=create, llm=lm-studio, orchestrator=dagster
        result = cli_runner.invoke(
            app,
            ["init", "--name", "my-project"],
            input="1\n1\n1\n1\n1\n1\n",
        )
        assert result.exit_code == 0, f"init failed: {result.stdout}"
        assert (tmp_path / "tycoon.yml").exists()

    def test_wizard_llm_choice_persists_to_ask_block(
        self, cli_runner, tmp_path, monkeypatch
    ):
        """Wizard's LLM prompt should write `ask.llm.provider` to
        tycoon.yml so `tycoon register llm` doesn't have to re-prompt.
        Closes #7 §5b.

        Uses a nested ``isolated/`` subdir so ``_detect_existing``'s
        sibling-scan can't pick up dbt projects scaffolded by other
        tests sharing the pytest-tmp parent.
        """
        proj = tmp_path / "isolated" / "lm-proj"
        proj.mkdir(parents=True)
        monkeypatch.chdir(proj)
        # ingestion=dlt(1), warehouse=local(1), dbt=create(1), rill=create(1),
        # llm=lm-studio(1), orchestrator=dagster(1)
        result = cli_runner.invoke(
            app,
            ["init", "--name", "lm-proj"],
            input="1\n1\n1\n1\n1\n1\n",
        )
        assert result.exit_code == 0, f"init failed: {result.stdout}"
        data = yaml.safe_load((proj / "tycoon.yml").read_text())
        assert data.get("ask", {}).get("llm", {}).get("provider") == "lm-studio"

    def test_wizard_autodetects_running_ollama(
        self, cli_runner, tmp_path, monkeypatch
    ):
        """When Ollama's port is reachable at wizard time, skip the
        7-option menu and present a 1-keystroke confirmation. The user
        accepts → ask.llm.provider = ollama, no menu choice consumed."""
        from tycoon.commands import ask as ask_mod

        # Stub the probe: LM Studio dead, Ollama reachable.
        def stub_probe(url, _provider="lm-studio"):
            if "11434" in url:
                return (True, 1, None)
            return (False, 0, "no")

        monkeypatch.setattr(ask_mod, "_probe_local_llm", stub_probe)

        proj = tmp_path / "isolated" / "auto-ollama"
        proj.mkdir(parents=True)
        monkeypatch.chdir(proj)
        # 5 menu choices (ingest/warehouse/dbt/rill) + Y for Ollama detect
        # + 1 menu choice (orch). One fewer than the un-detected path.
        result = cli_runner.invoke(
            app,
            ["init", "--name", "auto-ollama"],
            input="1\n1\n1\n1\nY\n1\n",
        )
        assert result.exit_code == 0, result.stdout
        # The confirmation prompt fired (proves the short-circuit branch).
        assert "Detected" in result.stdout
        assert "Ollama" in result.stdout
        data = yaml.safe_load((proj / "tycoon.yml").read_text())
        assert data["ask"]["llm"]["provider"] == "ollama"

    def test_wizard_autodetect_decline_falls_through_to_menu(
        self, cli_runner, tmp_path, monkeypatch
    ):
        """User declines the auto-detect confirm → full 7-option menu
        appears as normal."""
        from tycoon.commands import ask as ask_mod

        # Stub: LM Studio reachable.
        def stub_probe(url, _provider="lm-studio"):
            if "1234" in url:
                return (True, 1, None)
            return (False, 0, "no")

        monkeypatch.setattr(ask_mod, "_probe_local_llm", stub_probe)

        proj = tmp_path / "isolated" / "decline"
        proj.mkdir(parents=True)
        monkeypatch.chdir(proj)
        # ingestion(1), warehouse(1), dbt(1), rill(1), Decline LM Studio (n),
        # then full menu — pick OpenAI (3), then orch(1).
        result = cli_runner.invoke(
            app,
            ["init", "--name", "decline"],
            input="1\n1\n1\n1\nn\n3\n1\n",
        )
        assert result.exit_code == 0, result.stdout
        data = yaml.safe_load((proj / "tycoon.yml").read_text())
        # User picked OpenAI from the menu after declining LM Studio.
        assert data["ask"]["llm"]["provider"] == "openai"

    def test_wizard_both_detected_both_have_models_shows_menu(
        self, cli_runner, tmp_path, monkeypatch
    ):
        """Both reachable, both have models — truly ambiguous, fall to menu."""
        from tycoon.commands import ask as ask_mod

        monkeypatch.setattr(ask_mod, "_probe_local_llm", lambda *_a, **_kw: (True, 1, None))

        proj = tmp_path / "isolated" / "both-loaded"
        proj.mkdir(parents=True)
        monkeypatch.chdir(proj)
        result = cli_runner.invoke(
            app,
            ["init", "--name", "both-loaded"],
            input="1\n1\n1\n1\n2\n1\n",
        )
        assert result.exit_code == 0, result.stdout
        assert "both runtimes" in result.stdout.lower()
        data = yaml.safe_load((proj / "tycoon.yml").read_text())
        assert data["ask"]["llm"]["provider"] == "ollama"

    def test_wizard_both_reachable_only_one_has_models_suggests_loaded(
        self, cli_runner, tmp_path, monkeypatch
    ):
        """Both reachable, only Ollama has models — auto-suggest Ollama
        (LM Studio would need a model install anyway)."""
        from tycoon.commands import ask as ask_mod

        def stub_probe(url, _provider="lm-studio"):
            if "11434" in url:
                return (True, 2, None)  # Ollama: 2 models loaded
            return (True, 0, None)  # LM Studio: 0 models loaded

        monkeypatch.setattr(ask_mod, "_probe_local_llm", stub_probe)

        proj = tmp_path / "isolated" / "tiebreak"
        proj.mkdir(parents=True)
        monkeypatch.chdir(proj)
        # Confirm Ollama with Y, then orchestrator(1).
        result = cli_runner.invoke(
            app,
            ["init", "--name", "tiebreak"],
            input="1\n1\n1\n1\nY\n1\n",
        )
        assert result.exit_code == 0, result.stdout
        assert "Detected" in result.stdout
        assert "Ollama" in result.stdout
        data = yaml.safe_load((proj / "tycoon.yml").read_text())
        assert data["ask"]["llm"]["provider"] == "ollama"

    def test_wizard_chains_ask_setup_when_provider_picked(
        self, cli_runner, tmp_path, monkeypatch
    ):
        """When the user picks a provider in the wizard AND nao_core
        is importable, `tycoon init` should:
          - write nao_config.yaml under .tycoon/nao/
          - refresh AGENTS.md at project root
          - seed exclude_schemas
        Without the user having to run `tycoon register llm` separately.
        """
        proj = tmp_path / "isolated" / "chained"
        proj.mkdir(parents=True)
        monkeypatch.chdir(proj)
        # ingest(1), warehouse(1), dbt(1), rill(1), llm=lm-studio(1), orch(1)
        result = cli_runner.invoke(
            app,
            ["init", "--name", "chained"],
            input="1\n1\n1\n1\n1\n1\n",
        )
        assert result.exit_code == 0, result.stdout

        # AI setup ran:
        assert (proj / ".tycoon" / "nao" / "nao_config.yaml").exists()
        assert (proj / "AGENTS.md").exists()

        # exclude_schemas was seeded.
        data = yaml.safe_load((proj / "tycoon.yml").read_text())
        excludes = data["ask"]["exclude_schemas"]
        assert "information_schema" in excludes
        assert "_tycoon" in excludes

        # Next steps should point at `tycoon ask chat` directly, not
        # `tycoon register llm` (since the chain already did that work).
        assert "tycoon ask chat" in result.stdout
        next_steps_section = result.stdout.split("What's next?")[-1] if "What's next?" in result.stdout else result.stdout
        assert "tycoon register llm" not in next_steps_section

    def test_wizard_skip_llm_doesnt_chain_ask_setup(
        self, cli_runner, tmp_path, monkeypatch
    ):
        """If user picks Skip on the LLM prompt, no ask setup should run
        — no nao_config.yaml, no AGENTS.md, no ask block in tycoon.yml."""
        proj = tmp_path / "isolated" / "no-chain"
        proj.mkdir(parents=True)
        monkeypatch.chdir(proj)
        # llm=skip(7)
        result = cli_runner.invoke(
            app,
            ["init", "--name", "no-chain"],
            input="1\n1\n1\n1\n7\n1\n",
        )
        assert result.exit_code == 0, result.stdout
        assert not (proj / ".tycoon" / "nao" / "nao_config.yaml").exists()
        assert not (proj / "AGENTS.md").exists()
        # next_steps should point at `tycoon register llm`, not chat
        assert "tycoon register llm" in result.stdout

    def test_wizard_llm_skip_omits_ask_block(
        self, cli_runner, tmp_path, monkeypatch
    ):
        """Choosing 'Skip' on the LLM prompt leaves the ask block out so
        `tycoon register llm <provider>` can later add it without a
        merge conflict against placeholder values."""
        proj = tmp_path / "isolated" / "skip-llm"
        proj.mkdir(parents=True)
        monkeypatch.chdir(proj)
        # ingestion=dlt(1), warehouse=local(1), dbt=create(1), rill=create(1),
        # llm=skip(7), orchestrator=dagster(1)
        result = cli_runner.invoke(
            app,
            ["init", "--name", "skip-llm"],
            input="1\n1\n1\n1\n7\n1\n",
        )
        assert result.exit_code == 0, f"init failed: {result.stdout}"
        data = yaml.safe_load((proj / "tycoon.yml").read_text())
        assert "ask" not in data


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

        out = _substitute_params(
            "{{ known }} vs {{ unknown }}", {"known": "yes"}
        )
        assert out == "yes vs {{ unknown }}"

    def test_scaffold_with_params_substitutes_in_tycoon_yml(
        self, cli_runner, tmp_path, monkeypatch
    ):
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

    def test_missing_required_param_errors_out_in_noninteractive(
        self, cli_runner, tmp_path, monkeypatch
    ):
        """When no --param is supplied and stdin is empty (CliRunner default),
        typer.prompt fails. We just need it to not silently succeed."""
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(
            app, ["init", "--template", "github-analytics"]
        )
        assert result.exit_code != 0

    def test_param_malformed_is_rejected(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(
            app,
            ["init", "--template", "github-analytics", "--param", "malformed"],
        )
        assert result.exit_code != 0

    def test_unknown_param_is_warned_but_not_fatal(
        self, cli_runner, tmp_path, monkeypatch
    ):
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
