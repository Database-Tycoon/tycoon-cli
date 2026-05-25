"""Tests for `tycoon data sources` subcommands and source_installer."""

from __future__ import annotations

from pathlib import Path


from tycoon.cli import app
from tycoon.project import SourceConfig, TycoonProject, load_project, save_project


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_YML = """\
name: test-project
version: 0.1.0
database:
  raw: data/raw.duckdb
  warehouse: data/warehouse.duckdb
sources:
  nyc-dot:
    type: rest_api
    schema: raw_nyc_dot
    config:
      base_url: https://data.cityofnewyork.us/resource/
  my-db:
    type: sql_database
    schema: raw_db
    config:
      connection_string: postgresql://localhost/test
"""


def _setup_project(tmp_path: Path) -> None:
    """Write a tycoon.yml and pyproject.toml to tmp_path."""
    (tmp_path / "tycoon.yml").write_text(_SAMPLE_YML)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')


# ---------------------------------------------------------------------------
# CLI help / registration
# ---------------------------------------------------------------------------


class TestSourcesHelp:
    """Verify the sources sub-app is registered and help text works."""

    def test_sources_in_data_help(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "--help"])
        assert "sources" in result.stdout

    def test_sources_help_lists_subcommands(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "sources", "--help"])
        assert result.exit_code == 0
        for sub in ("list", "add", "remove", "catalog", "run"):
            assert sub in result.stdout, f"Expected subcommand '{sub}' in sources help"


# ---------------------------------------------------------------------------
# tycoon data sources list
# ---------------------------------------------------------------------------


class TestSourcesList:
    """Verify `tycoon data sources list` output."""

    def test_list_shows_sources(self, cli_runner, tmp_path, monkeypatch):
        _setup_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        # Reload config for the new cwd
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        result = cli_runner.invoke(app, ["data", "sources", "list"])
        assert result.exit_code == 0
        assert "nyc-dot" in result.stdout
        assert "rest_api" in result.stdout
        assert "raw_nyc_dot" in result.stdout

    def test_list_shows_empty_message(self, cli_runner, tmp_path, monkeypatch):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "tycoon.yml").write_text("name: empty\nsources: {}\n")
        monkeypatch.chdir(tmp_path)
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        result = cli_runner.invoke(app, ["data", "sources", "list"])
        assert result.exit_code == 0
        assert "no sources" in result.stdout.lower() or "tycoon" in result.stdout.lower()

    def test_list_errors_without_project(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        result = cli_runner.invoke(app, ["data", "sources", "list"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# tycoon data sources show
# ---------------------------------------------------------------------------


class TestSourcesShow:
    """Verify `tycoon data sources show <name>` output."""

    def test_show_existing_source(self, cli_runner, tmp_path, monkeypatch):
        _setup_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        # show is a subcommand of list: tycoon data sources list show <name>
        result = cli_runner.invoke(app, ["data", "sources", "list", "show", "nyc-dot"])
        assert result.exit_code == 0
        assert "rest_api" in result.stdout
        assert "raw_nyc_dot" in result.stdout
        assert "base_url" in result.stdout

    def test_show_nonexistent_source(self, cli_runner, tmp_path, monkeypatch):
        _setup_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        result = cli_runner.invoke(app, ["data", "sources", "list", "show", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "not found" in (result.stderr or "").lower()


# ---------------------------------------------------------------------------
# tycoon data sources remove
# ---------------------------------------------------------------------------


class TestSourcesRemove:
    """Verify `tycoon data sources remove <name>` behaviour."""

    def test_remove_with_confirmation(self, cli_runner, tmp_path, monkeypatch):
        _setup_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        result = cli_runner.invoke(app, ["data", "sources", "remove", "nyc-dot"], input="y\n")
        assert result.exit_code == 0
        assert "removed" in result.stdout.lower()

        # Verify it's gone from disk
        project = load_project(tmp_path)
        assert project is not None
        assert "nyc-dot" not in project.sources

    def test_remove_abort(self, cli_runner, tmp_path, monkeypatch):
        _setup_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        result = cli_runner.invoke(app, ["data", "sources", "remove", "nyc-dot"], input="n\n")
        assert result.exit_code == 1  # typer.confirm abort exits 1

        # Verify it's still there
        project = load_project(tmp_path)
        assert project is not None
        assert "nyc-dot" in project.sources

    def test_remove_nonexistent_source(self, cli_runner, tmp_path, monkeypatch):
        _setup_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        from tycoon.config import config
        config.__init__(project_root=tmp_path)

        result = cli_runner.invoke(app, ["data", "sources", "remove", "nonexistent"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# SourceConfig model and round-trip
# ---------------------------------------------------------------------------


class TestSourceConfigModel:
    """Test SourceConfig creation and save/load round-trip."""

    def test_source_config_creation(self):
        src = SourceConfig(
            type="rest_api",
            schema="raw_test",
            config={"base_url": "https://example.com"},
        )
        assert src.type == "rest_api"
        assert src.schema_name == "raw_test"
        assert src.config["base_url"] == "https://example.com"
        assert src.tables is None

    def test_source_config_with_tables(self):
        src = SourceConfig(
            type="sql_database",
            schema="raw_db",
            config={"connection_string": "postgresql://localhost/test"},
            tables=["users", "orders"],
        )
        assert src.tables == ["users", "orders"]

    def test_add_source_round_trip(self, tmp_path):
        """Adding a source to a project and reloading preserves it."""
        project = TycoonProject(name="round-trip-test")
        project.sources["new-api"] = SourceConfig(
            type="rest_api",
            schema="raw_new_api",
            config={"base_url": "https://api.example.com"},
        )
        save_project(project, tmp_path)

        loaded = load_project(tmp_path)
        assert loaded is not None
        assert "new-api" in loaded.sources
        assert loaded.sources["new-api"].type == "rest_api"
        assert loaded.sources["new-api"].schema_name == "raw_new_api"
        assert loaded.sources["new-api"].config["base_url"] == "https://api.example.com"


# ---------------------------------------------------------------------------
# source_installer
# ---------------------------------------------------------------------------


class TestSourceInstaller:
    """Tests for the dlt extra installer utilities."""

    def test_is_dlt_extra_available_returns_bool(self):
        from tycoon.ingestion.source_installer import is_dlt_extra_available

        result = is_dlt_extra_available("rest_api")
        assert isinstance(result, bool)

    def test_is_dlt_extra_available_nonexistent(self):
        from tycoon.ingestion.source_installer import is_dlt_extra_available

        result = is_dlt_extra_available("totally_fake_source_type_xyz")
        assert result is False

    def test_dlt_extras_dict_has_known_types(self):
        from tycoon.ingestion.source_installer import DLT_EXTRAS

        assert "rest_api" in DLT_EXTRAS
        assert "sql_database" in DLT_EXTRAS
        assert "filesystem" in DLT_EXTRAS

    def test_install_dlt_extra_returns_bool(self):
        """Verify install_dlt_extra returns a bool (don't actually install)."""
        from tycoon.ingestion.source_installer import install_dlt_extra

        # We don't want to actually run pip in tests, but we can verify
        # the function signature and return type by mocking subprocess
        from unittest.mock import patch, MagicMock

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("tycoon.ingestion.source_installer.subprocess.run", return_value=mock_result):
            result = install_dlt_extra("rest_api")
            assert result is True

    def test_install_dlt_extra_failure(self):
        """Verify install_dlt_extra returns False on failure."""
        from tycoon.ingestion.source_installer import install_dlt_extra
        from unittest.mock import patch, MagicMock

        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("tycoon.ingestion.source_installer.subprocess.run", return_value=mock_result):
            result = install_dlt_extra("rest_api")
            assert result is False


# ---------------------------------------------------------------------------
# Auto-scaffold (`_maybe_auto_scaffold` — used by `data sources run`)
# ---------------------------------------------------------------------------


class TestAutoScaffold:
    """Unit tests for the post-ingest auto-scaffold helper."""

    def _seed_raw_db(self, path: Path, schema: str, table: str) -> None:
        """Write a tiny DuckDB with one schema-qualified table."""
        import duckdb

        path.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(path))
        try:
            con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            con.execute(f"CREATE TABLE {schema}.{table} (id INTEGER, name VARCHAR)")
            con.execute(f"INSERT INTO {schema}.{table} VALUES (1, 'a'), (2, 'b')")
        finally:
            con.close()

    def _bind_config(self, monkeypatch, project_root: Path) -> None:
        from tycoon.commands import sources as sources_mod
        from tycoon.config import TycoonConfig

        cfg = TycoonConfig(project_root=project_root)
        monkeypatch.setattr(sources_mod, "config", cfg)

    def test_no_dbt_project_is_noop(self, tmp_path: Path, monkeypatch):
        from tycoon.commands.sources import _maybe_auto_scaffold

        _setup_project(tmp_path)
        self._bind_config(monkeypatch, tmp_path)
        # No dbt_project/ directory exists.

        sc = SourceConfig(type="rest_api", schema="raw_nyc_dot", config={})
        _maybe_auto_scaffold("nyc-dot", sc, scaffold=True)
        # No exception, no files written. Nothing to assert beyond "didn't raise."

    def test_skips_when_source_already_referenced(self, tmp_path: Path, monkeypatch):
        from tycoon.commands.sources import _maybe_auto_scaffold

        _setup_project(tmp_path)
        # Hand-written staging model already references the source.
        models = tmp_path / "dbt_project" / "models" / "staging"
        models.mkdir(parents=True)
        (models / "stg_existing.sql").write_text(
            "select * from {{ source('nyc-dot', 'i4gi-tjb9') }}\n"
        )
        self._seed_raw_db(tmp_path / "data" / "raw.duckdb", "raw_nyc_dot", "i4gi_tjb9")
        self._bind_config(monkeypatch, tmp_path)

        sc = SourceConfig(type="rest_api", schema="raw_nyc_dot", config={})
        _maybe_auto_scaffold("nyc-dot", sc, scaffold=True)

        # No nyc-dot subdirectory was created.
        assert not (models / "nyc-dot").exists()

    def test_generates_when_dbt_exists_and_no_prior_reference(
        self, tmp_path: Path, monkeypatch
    ):
        from tycoon.commands.sources import _maybe_auto_scaffold

        _setup_project(tmp_path)
        (tmp_path / "dbt_project" / "models").mkdir(parents=True)
        self._seed_raw_db(tmp_path / "data" / "raw.duckdb", "raw_nyc_dot", "i4gi_tjb9")
        self._bind_config(monkeypatch, tmp_path)

        sc = SourceConfig(type="rest_api", schema="raw_nyc_dot", config={})
        _maybe_auto_scaffold("nyc-dot", sc, scaffold=True)

        sql = tmp_path / "dbt_project" / "models" / "staging" / "nyc-dot" / "stg_nyc-dot__i4gi_tjb9.sql"
        assert sql.exists()
        assert "source('nyc-dot', 'i4gi_tjb9')" in sql.read_text()

    def test_no_scaffold_flag_skips(self, tmp_path: Path, monkeypatch):
        from tycoon.commands.sources import _maybe_auto_scaffold

        _setup_project(tmp_path)
        (tmp_path / "dbt_project" / "models").mkdir(parents=True)
        self._seed_raw_db(tmp_path / "data" / "raw.duckdb", "raw_nyc_dot", "i4gi_tjb9")
        self._bind_config(monkeypatch, tmp_path)

        sc = SourceConfig(type="rest_api", schema="raw_nyc_dot", config={})
        _maybe_auto_scaffold("nyc-dot", sc, scaffold=False)

        assert not (tmp_path / "dbt_project" / "models" / "staging" / "nyc-dot").exists()

    def test_config_opt_out_skips(self, tmp_path: Path, monkeypatch):
        from tycoon.commands.sources import _maybe_auto_scaffold

        # tycoon.yml with transform.auto_scaffold: false
        (tmp_path / "tycoon.yml").write_text(
            _SAMPLE_YML + "transform:\n  auto_scaffold: false\n"
        )
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "dbt_project" / "models").mkdir(parents=True)
        self._seed_raw_db(tmp_path / "data" / "raw.duckdb", "raw_nyc_dot", "i4gi_tjb9")
        self._bind_config(monkeypatch, tmp_path)

        sc = SourceConfig(type="rest_api", schema="raw_nyc_dot", config={})
        _maybe_auto_scaffold("nyc-dot", sc, scaffold=True)

        assert not (tmp_path / "dbt_project" / "models" / "staging" / "nyc-dot").exists()


# ---------------------------------------------------------------------------
# tycoon data sources add — non-interactive (v0.1.7, #44)
# ---------------------------------------------------------------------------


class TestSourcesAddNoPrompt:
    """`--no-prompt` mode for scripted / CI / online-doctest bootstrap.

    These tests run the command end-to-end via CliRunner without ever
    feeding stdin. A regression where any prompt sneaks back in shows
    up as a hang or an EOF error.
    """

    def _bind(self, tmp_path: Path, monkeypatch):
        """Set up an empty project + bind config to tmp_path."""
        body = (
            "name: test\n"
            "version: 0.1.0\n"
            "database:\n"
            "  raw: data/raw.duckdb\n"
            "  warehouse: data/warehouse.duckdb\n"
            "sources: {}\n"
        )
        (tmp_path / "tycoon.yml").write_text(body)
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        from tycoon.commands import sources as sources_mod
        from tycoon.config import TycoonConfig

        cfg = TycoonConfig(project_root=tmp_path)
        monkeypatch.setattr(sources_mod, "config", cfg)
        return cfg

    def test_rest_api_with_base_url_auto_derives_name_and_schema(
        self, cli_runner, tmp_path, monkeypatch
    ):
        self._bind(tmp_path, monkeypatch)
        result = cli_runner.invoke(
            app,
            [
                "data", "sources", "add", "rest_api",
                "--base-url", "https://pokeapi.co/api/v2/",
                "--resources", "pokemon,berry,type",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0, result.output

        project = load_project(tmp_path)
        # Auto-derived name from the URL host (pokeapi.co -> pokeapi).
        assert "pokeapi" in project.sources
        src = project.sources["pokeapi"]
        assert src.type == "rest_api"
        assert src.schema_name == "raw_pokeapi"
        assert src.config["base_url"] == "https://pokeapi.co/api/v2/"
        assert src.config["resources"] == "pokemon,berry,type"

    def test_rest_api_missing_base_url_errors(
        self, cli_runner, tmp_path, monkeypatch
    ):
        self._bind(tmp_path, monkeypatch)
        result = cli_runner.invoke(
            app, ["data", "sources", "add", "rest_api", "--no-prompt"]
        )
        assert result.exit_code == 1
        # error() writes to stderr
        assert "--base-url is required" in (result.stderr or result.output)

    def test_sql_database_with_connection_string(
        self, cli_runner, tmp_path, monkeypatch
    ):
        self._bind(tmp_path, monkeypatch)
        result = cli_runner.invoke(
            app,
            [
                "data", "sources", "add", "sql_database",
                "--name", "warehouse-pg",
                "--schema", "raw_pg",
                "--connection-string", "${DATABASE_URL}",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0, result.output
        project = load_project(tmp_path)
        assert "warehouse-pg" in project.sources
        assert project.sources["warehouse-pg"].config["connection_string"] == "${DATABASE_URL}"

    def test_sql_database_requires_name_when_no_prompt(
        self, cli_runner, tmp_path, monkeypatch
    ):
        """sql_database has no auto-naming rule — --name is required."""
        self._bind(tmp_path, monkeypatch)
        result = cli_runner.invoke(
            app,
            [
                "data", "sources", "add", "sql_database",
                "--connection-string", "postgres://x",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 1
        assert "--name is required" in (result.stderr or result.output)

    def test_no_prompt_without_source_type_errors(
        self, cli_runner, tmp_path, monkeypatch
    ):
        self._bind(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["data", "sources", "add", "--no-prompt"])
        assert result.exit_code == 1
        assert "requires a source type" in (result.stderr or result.output)

    def test_duplicate_without_force_errors(
        self, cli_runner, tmp_path, monkeypatch
    ):
        self._bind(tmp_path, monkeypatch)
        cli_runner.invoke(
            app,
            [
                "data", "sources", "add", "rest_api",
                "--base-url", "https://api.x.com/",
                "--no-prompt",
            ],
        )
        result = cli_runner.invoke(
            app,
            [
                "data", "sources", "add", "rest_api",
                "--base-url", "https://api.x.com/",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 1
        assert "--force" in (result.stderr or result.output)

    def test_force_overwrites_existing(
        self, cli_runner, tmp_path, monkeypatch
    ):
        self._bind(tmp_path, monkeypatch)
        cli_runner.invoke(
            app,
            [
                "data", "sources", "add", "rest_api",
                "--base-url", "https://api.x.com/v1/",
                "--no-prompt",
            ],
        )
        result = cli_runner.invoke(
            app,
            [
                "data", "sources", "add", "rest_api",
                "--base-url", "https://api.x.com/v2/",
                "--no-prompt", "--force",
            ],
        )
        assert result.exit_code == 0, result.output
        project = load_project(tmp_path)
        # Newer base_url wins.
        assert project.sources["x"].config["base_url"] == "https://api.x.com/v2/"

    def test_config_pairs_merge_into_source_config(
        self, cli_runner, tmp_path, monkeypatch
    ):
        self._bind(tmp_path, monkeypatch)
        result = cli_runner.invoke(
            app,
            [
                "data", "sources", "add", "rest_api",
                "--base-url", "https://api.x.com/",
                "--config", "headers={'Accept':'application/json'}",
                "--config", "timeout=30",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0, result.output
        project = load_project(tmp_path)
        src = project.sources["x"]
        assert src.config["timeout"] == "30"
        assert "headers" in src.config

    def test_invalid_config_pair_errors(
        self, cli_runner, tmp_path, monkeypatch
    ):
        self._bind(tmp_path, monkeypatch)
        result = cli_runner.invoke(
            app,
            [
                "data", "sources", "add", "rest_api",
                "--base-url", "https://api.x.com/",
                "--config", "missing_equals_sign",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 1
        assert "Invalid --config" in (result.stderr or result.output)
