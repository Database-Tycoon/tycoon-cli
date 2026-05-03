"""Tests for `tycoon data analyze` command, dbt_generator, and rill_generator."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
import yaml

from tycoon.cli import app


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_db(tmp_path: Path) -> Path:
    """Create a minimal DuckDB database with a test schema and table."""
    db_path = tmp_path / "test.duckdb"
    con = duckdb.connect(str(db_path))
    con.execute("CREATE SCHEMA test_schema")
    con.execute(
        """
        CREATE TABLE test_schema.my_table (
            id INTEGER,
            name VARCHAR,
            amount DOUBLE,
            created_at TIMESTAMP,
            _dlt_load_id VARCHAR,
            _dlt_id VARCHAR
        )
        """
    )
    con.execute(
        "INSERT INTO test_schema.my_table VALUES "
        "(1, 'test', 99.5, '2024-01-01', 'x', 'y')"
    )
    con.close()
    return db_path


@pytest.fixture
def test_db_with_nested(tmp_path: Path) -> Path:
    """DB that also contains a nested dlt table (name with __) and internal tables."""
    db_path = tmp_path / "nested.duckdb"
    con = duckdb.connect(str(db_path))
    con.execute("CREATE SCHEMA s")
    con.execute(
        """
        CREATE TABLE s.orders (
            order_id INTEGER,
            customer VARCHAR,
            total FLOAT
        )
        """
    )
    # Nested table — should be excluded
    con.execute("CREATE TABLE s.orders__items (item_id INTEGER)")
    # dlt internal table — should be excluded
    con.execute("CREATE TABLE s._dlt_loads (load_id VARCHAR)")
    con.execute("CREATE TABLE s._dlt_pipeline_state (version_hash VARCHAR)")
    con.execute("CREATE TABLE s._dlt_version (engine_version INTEGER)")
    con.close()
    return db_path


# ---------------------------------------------------------------------------
# CLI: analyze --help
# ---------------------------------------------------------------------------


class TestAnalyzeHelp:
    """Verify the analyze command is registered and shows help."""

    def test_analyze_help_exits_zero(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "analyze", "--help"])
        assert result.exit_code == 0

    def test_analyze_help_shows_options(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "analyze", "--help"])
        assert "--rill" in result.stdout
        assert "--no-dbt" in result.stdout
        assert "--build" in result.stdout

    def test_analyze_appears_in_data_help(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "--help"])
        assert "analyze" in result.stdout


# ---------------------------------------------------------------------------
# dbt_generator: generate_staging_models
# ---------------------------------------------------------------------------


class TestGenerateStagingModels:
    """Unit tests for the dbt staging model generator."""

    def test_generates_sql_file(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "staging" / "my_source"
        result = generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )

        sql_files = [f for f in result.generated if f.endswith(".sql")]
        assert len(sql_files) == 1
        assert "stg_my_source__my_table.sql" in sql_files[0]

    def test_sql_file_contains_source_macro(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "staging"
        generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )

        sql_path = output_dir / "stg_my_source__my_table.sql"
        content = sql_path.read_text()
        assert "source('my_source', 'my_table')" in content

    def test_sql_file_contains_cte_structure(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "staging"
        generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )

        content = (output_dir / "stg_my_source__my_table.sql").read_text()
        assert "with source as" in content
        assert "cleaned as" in content
        assert "select * from cleaned" in content

    def test_generates_yaml_schema_file(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "staging"
        result = generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )

        yaml_files = [f for f in result.generated if f.endswith(".yml")]
        assert len(yaml_files) == 1
        assert "_my_source__models.yml" in yaml_files[0]

    def test_yaml_has_sources_and_models_sections(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "staging"
        generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )

        yaml_path = output_dir / "_my_source__models.yml"
        data = yaml.safe_load(yaml_path.read_text())
        assert "sources" in data
        assert "models" in data
        assert data["version"] == 2

    def test_yaml_sources_reference_correct_schema(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "staging"
        generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )

        data = yaml.safe_load((output_dir / "_my_source__models.yml").read_text())
        source = data["sources"][0]
        assert source["name"] == "my_source"
        assert source["schema"] == "test_schema"
        assert source["database"] == "raw"
        table_names = [t["name"] for t in source["tables"]]
        assert "my_table" in table_names

    def test_yaml_model_entry_references_stg_name(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "staging"
        generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )

        data = yaml.safe_load((output_dir / "_my_source__models.yml").read_text())
        model_names = [m["name"] for m in data["models"]]
        assert "stg_my_source__my_table" in model_names

    def test_dlt_internal_columns_excluded(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "staging"
        generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )

        sql_content = (output_dir / "stg_my_source__my_table.sql").read_text()
        assert "_dlt_load_id" not in sql_content
        assert "_dlt_id" not in sql_content

        yaml_data = yaml.safe_load((output_dir / "_my_source__models.yml").read_text())
        for model in yaml_data["models"]:
            col_names = [c["name"] for c in model.get("columns", [])]
            assert "_dlt_load_id" not in col_names
            assert "_dlt_id" not in col_names

    def test_dlt_internal_columns_not_in_yaml_columns(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "staging"
        generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )

        yaml_data = yaml.safe_load((output_dir / "_my_source__models.yml").read_text())
        model = yaml_data["models"][0]
        col_names = [c["name"] for c in model["columns"]]
        assert "id" in col_names
        assert "name" in col_names
        assert "amount" in col_names
        assert "created_at" in col_names

    def test_nested_tables_excluded(self, tmp_path: Path, test_db_with_nested: Path):
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "staging"
        result = generate_staging_models(
            raw_db_path=test_db_with_nested,
            schema_name="s",
            source_name="src",
            output_dir=output_dir,
        )

        file_names = [Path(f).name for f in result.generated]
        # orders should be included, orders__items should not
        assert any("stg_src__orders" in n for n in file_names)
        assert not any("items" in n for n in file_names)

    def test_dlt_internal_tables_excluded(self, tmp_path: Path, test_db_with_nested: Path):
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "staging"
        result = generate_staging_models(
            raw_db_path=test_db_with_nested,
            schema_name="s",
            source_name="src",
            output_dir=output_dir,
        )

        file_names = [Path(f).name for f in result.generated]
        assert not any("_dlt_" in n for n in file_names)

    def test_creates_output_directory(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "deep" / "nested" / "path"
        assert not output_dir.exists()
        generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )
        assert output_dir.is_dir()

    def test_generated_files_carry_sentinel(self, tmp_path: Path, test_db: Path):
        """Re-runs depend on the sentinel; first run must embed it."""
        from tycoon.scaffolding.dbt_generator import (
            SQL_SENTINEL,
            YAML_SENTINEL,
            generate_staging_models,
        )

        output_dir = tmp_path / "staging"
        generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )
        sql = (output_dir / "stg_my_source__my_table.sql").read_text()
        yml = (output_dir / "_my_source__models.yml").read_text()
        assert SQL_SENTINEL in sql
        assert YAML_SENTINEL in yml

    def test_rerun_preserves_hand_edited_file(self, tmp_path: Path, test_db: Path):
        """If the user removes the sentinel, the file is left alone on re-run."""
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "staging"
        generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )
        sql_path = output_dir / "stg_my_source__my_table.sql"
        # User takes ownership: removes the sentinel + hand-edits.
        hand_edited = "-- my custom version\nselect 42 as the_answer\n"
        sql_path.write_text(hand_edited)

        result = generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )
        # SQL was preserved; YAML was regenerated (still has sentinel).
        assert sql_path.read_text() == hand_edited
        assert str(sql_path) in result.skipped
        assert str(sql_path) not in result.generated

    def test_force_overwrites_hand_edited_file(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.dbt_generator import (
            SQL_SENTINEL,
            generate_staging_models,
        )

        output_dir = tmp_path / "staging"
        generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )
        sql_path = output_dir / "stg_my_source__my_table.sql"
        sql_path.write_text("-- hand-edited, no sentinel\nselect 42\n")

        result = generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
            force=True,
        )
        assert SQL_SENTINEL in sql_path.read_text()
        assert str(sql_path) in result.generated
        assert result.skipped == []

    def test_returns_generated_and_skipped(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.dbt_generator import GenerateResult, generate_staging_models

        output_dir = tmp_path / "staging"
        result = generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )
        assert isinstance(result, GenerateResult)
        assert all(isinstance(p, str) for p in result.generated)
        assert all(isinstance(p, str) for p in result.skipped)
        # First-time generation: nothing should be skipped.
        assert result.skipped == []
        assert result.generated, "should have generated at least one file"


# ---------------------------------------------------------------------------
# rill_generator: generate_rill_config
# ---------------------------------------------------------------------------


class TestGenerateRillConfig:
    """Unit tests for the Rill config generator.

    The current generator creates:
    - sources/{model_name}.yaml (type: source, connector: local_file)
    - metrics/{model_name}_mv.yaml (type: metrics_view)
    - dashboards/{model_name}.yaml (type: explore)
    - parquet files for each table
    """

    def test_creates_source_yaml(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )

        source_path = rill_dir / "sources" / "stg_my_source__my_table.yaml"
        assert source_path.exists()

    def test_source_yaml_uses_local_file_connector(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )

        content = (rill_dir / "sources" / "stg_my_source__my_table.yaml").read_text()
        assert "local_file" in content
        assert "parquet" in content

    def test_creates_metrics_view_yaml(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )

        mv_path = rill_dir / "metrics" / "stg_my_source__my_table_mv.yaml"
        assert mv_path.exists()
        content = mv_path.read_text()
        assert "metrics_view" in content

    def test_creates_explore_dashboard_yaml(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )

        dashboard_path = rill_dir / "dashboards" / "stg_my_source__my_table.yaml"
        assert dashboard_path.exists()
        content = dashboard_path.read_text()
        assert "explore" in content

    def test_metrics_view_has_count_measure(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )

        mv_path = rill_dir / "metrics" / "stg_my_source__my_table_mv.yaml"
        content = mv_path.read_text()
        assert "count(*)" in content

    def test_returns_list_of_paths(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        result = generate_rill_config(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )
        assert isinstance(result, list)
        assert all(isinstance(p, str) for p in result)

    def test_exports_parquet_files(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )

        parquet_dir = test_db.parent / "parquet" / "test_schema"
        assert (parquet_dir / "my_table.parquet").exists()


# ---------------------------------------------------------------------------
# Column type heuristics
# ---------------------------------------------------------------------------


class TestColumnTypeHeuristics:
    """Verify _classify_column maps SQL types to dimension/measure correctly.

    _classify_column(col_name, data_type) takes two arguments: the column name
    and the SQL data type.
    """

    def test_varchar_is_dimension(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        assert _classify_column("my_col", "VARCHAR") == "dimension"

    def test_text_is_dimension(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        assert _classify_column("my_col", "TEXT") == "dimension"

    def test_date_is_dimension(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        assert _classify_column("my_col", "DATE") == "dimension"

    def test_timestamp_is_dimension(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        assert _classify_column("my_col", "TIMESTAMP") == "dimension"

    def test_boolean_is_dimension(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        assert _classify_column("my_col", "BOOLEAN") == "dimension"

    def test_integer_is_sum_measure(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        assert _classify_column("count", "INTEGER") == "sum_measure"

    def test_bigint_is_sum_measure(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        assert _classify_column("total", "BIGINT") == "sum_measure"

    def test_float_is_avg_measure(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        assert _classify_column("score", "FLOAT") == "avg_measure"

    def test_double_is_avg_measure(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        assert _classify_column("amount", "DOUBLE") == "avg_measure"

    def test_decimal_is_avg_measure(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        assert _classify_column("price", "DECIMAL") == "avg_measure"

    def test_numeric_is_avg_measure(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        assert _classify_column("value", "NUMERIC") == "avg_measure"

    def test_parameterised_decimal_is_avg_measure(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        assert _classify_column("price", "DECIMAL(10,2)") == "avg_measure"

    def test_parameterised_varchar_is_dimension(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        assert _classify_column("label", "VARCHAR(255)") == "dimension"

    def test_case_insensitive(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        assert _classify_column("my_col", "varchar") == "dimension"
        assert _classify_column("count", "integer") == "sum_measure"
        assert _classify_column("amount", "double") == "avg_measure"

    def test_id_column_is_always_dimension(self):
        from tycoon.scaffolding.rill_generator import _classify_column

        # Even numeric types should be dimensions when column name ends with _id
        assert _classify_column("user_id", "INTEGER") == "dimension"
        assert _classify_column("id", "BIGINT") == "dimension"
        assert _classify_column("order_id", "INTEGER") == "dimension"


# ---------------------------------------------------------------------------
# Explore dashboard column classification integration
# ---------------------------------------------------------------------------


class TestExploreDashboardColumns:
    """Verify metrics_view YAML correctly classifies columns from test data."""

    def test_varchar_column_is_dimension(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )

        mv_path = rill_dir / "metrics" / "stg_my_source__my_table_mv.yaml"
        content = mv_path.read_text()
        assert "column: name" in content

    def test_double_column_is_avg_measure(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )

        mv_path = rill_dir / "metrics" / "stg_my_source__my_table_mv.yaml"
        content = mv_path.read_text()
        assert "avg(amount)" in content

    def test_dlt_columns_not_in_metrics_view(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )

        mv_path = rill_dir / "metrics" / "stg_my_source__my_table_mv.yaml"
        content = mv_path.read_text()
        assert "_dlt_load_id" not in content
        assert "_dlt_id" not in content


# ---------------------------------------------------------------------------
# CLI: analyze command errors
# ---------------------------------------------------------------------------


class TestAnalyzeCLIErrors:
    """Verify the analyze command fails gracefully when prerequisites are missing."""

    def test_analyze_fails_without_tycoon_yml(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(app, ["data", "analyze", "my-source"])
        assert result.exit_code != 0

    def test_analyze_fails_for_unknown_source(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "tycoon.yml").write_text(
            "name: test\nversion: 0.1.0\nsources: {}\n"
        )
        result = cli_runner.invoke(app, ["data", "analyze", "nonexistent-source"])
        assert result.exit_code != 0

    def test_analyze_fails_when_raw_db_missing(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        tycoon_yml = (
            "name: test\n"
            "version: 0.1.0\n"
            "database:\n"
            "  raw: data/raw.duckdb\n"
            "  warehouse: data/warehouse.duckdb\n"
            "sources:\n"
            "  my-src:\n"
            "    type: rest_api\n"
            "    schema: raw_my_src\n"
        )
        (tmp_path / "tycoon.yml").write_text(tycoon_yml)
        # Do NOT create the raw db
        result = cli_runner.invoke(app, ["data", "analyze", "my-src"])
        assert result.exit_code != 0

    def test_analyze_all_with_source_name_errors(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "tycoon.yml").write_text(
            "name: test\nversion: 0.1.0\nsources: {}\n"
        )
        from tycoon.commands import explore as explore_mod
        from tycoon.config import TycoonConfig
        monkeypatch.setattr(explore_mod, "config", TycoonConfig(project_root=tmp_path))

        result = cli_runner.invoke(app, ["data", "analyze", "my-source", "--all"])
        assert result.exit_code != 0
        combined = (result.stdout or "") + (result.stderr or "")
        assert "either a source name or --all" in combined

    def test_analyze_all_iterates_every_source(self, cli_runner, tmp_path, monkeypatch):
        """`--all` should generate staging for sources whose raw DB exists,
        and soft-skip the ones that don't."""
        monkeypatch.chdir(tmp_path)
        tycoon_yml = (
            "name: test\n"
            "version: 0.1.0\n"
            "database:\n"
            "  raw: data/raw.duckdb\n"
            "  warehouse: data/warehouse.duckdb\n"
            "sources:\n"
            "  src_a:\n"
            "    type: rest_api\n"
            "    schema: raw_src_a\n"
            "  src_b:\n"
            "    type: rest_api\n"
            "    schema: raw_src_b\n"
        )
        (tmp_path / "tycoon.yml").write_text(tycoon_yml)
        (tmp_path / "data").mkdir()
        # Only seed src_a's schema; src_b has no raw data.
        con = duckdb.connect(str(tmp_path / "data" / "raw.duckdb"))
        con.execute("CREATE SCHEMA raw_src_a")
        con.execute("CREATE TABLE raw_src_a.items (id INTEGER, name VARCHAR)")
        con.execute("INSERT INTO raw_src_a.items VALUES (1, 'a')")
        con.close()
        # Need a dbt project dir so output_dir parent is valid.
        (tmp_path / "dbt_project" / "models").mkdir(parents=True)

        from tycoon.commands import explore as explore_mod
        from tycoon.config import TycoonConfig
        monkeypatch.setattr(explore_mod, "config", TycoonConfig(project_root=tmp_path))

        result = cli_runner.invoke(app, ["data", "analyze", "--all"])
        assert result.exit_code == 0, result.stdout

        # src_a generated; src_b skipped (raw DB has no schema for it but
        # the DB file exists, so the path is "no eligible tables" — still
        # a soft-skip in --all mode).
        assert (
            tmp_path / "dbt_project" / "models" / "staging" / "src_a"
            / "stg_src_a__items.sql"
        ).exists()
        assert "src_a" in result.stdout
        assert "src_b" in result.stdout

    def test_analyze_interactive_prompt_does_not_crash(self, cli_runner, tmp_path, monkeypatch):
        """Regression: `tycoon data analyze` without a source argument must
        present an interactive prompt, not crash with AttributeError from a
        bad typer.Choice reference. See typer.Choice → click.Choice fix."""
        monkeypatch.chdir(tmp_path)
        tycoon_yml = (
            "name: test\n"
            "version: 0.1.0\n"
            "database:\n"
            "  raw: data/raw.duckdb\n"
            "  warehouse: data/warehouse.duckdb\n"
            "sources:\n"
            "  src_a:\n"
            "    type: rest_api\n"
            "    schema: raw_src_a\n"
        )
        (tmp_path / "tycoon.yml").write_text(tycoon_yml)
        (tmp_path / "data").mkdir()
        con = duckdb.connect(str(tmp_path / "data" / "raw.duckdb"))
        con.execute("CREATE SCHEMA raw_src_a")
        con.execute("CREATE TABLE raw_src_a.items (id INTEGER)")
        con.close()

        # Reload config for the analyze command
        from tycoon.commands import explore as explore_mod
        from tycoon.config import TycoonConfig
        monkeypatch.setattr(explore_mod, "config", TycoonConfig(project_root=tmp_path))

        # Supply "src_a" as the interactive choice
        result = cli_runner.invoke(app, ["data", "analyze", "--no-dbt"], input="src_a\n")
        # The key assertion: no AttributeError. Exit may be 0 or non-zero depending
        # on downstream behavior; we just need the prompt to not crash.
        assert not isinstance(result.exception, AttributeError), (
            f"typer.Choice regression: {result.exception!r}\n{result.stdout}"
        )


# ---------------------------------------------------------------------------
# observability: capture_dlt + capture_dbt + refresh_usage_dashboards
# ---------------------------------------------------------------------------


def _make_dlt_db(
    tmp_path: Path,
    *,
    schemas: dict[str, list[tuple[str, int]]],
    include_schema_version_hash: bool = True,
) -> Path:
    """Build a DuckDB that looks like dlt writes to it.

    schemas maps schema_name -> list of (table_name, rows_per_current_load).
    Each schema gets a _dlt_loads row and the listed tables get that many
    rows tagged with the load_id.
    """
    db_path = tmp_path / "raw.duckdb"
    con = duckdb.connect(str(db_path))
    try:
        for i, (schema, tables) in enumerate(schemas.items()):
            con.execute(f'CREATE SCHEMA "{schema}"')
            svh_col = ", schema_version_hash VARCHAR" if include_schema_version_hash else ""
            con.execute(
                f'CREATE TABLE "{schema}"."_dlt_loads" ('
                f"load_id VARCHAR, status INTEGER, "
                f"inserted_at TIMESTAMP{svh_col}"
                f")"
            )
            load_id = f"load-{i + 1}"
            svh_val = ", 'hash-v1'" if include_schema_version_hash else ""
            con.execute(
                f'INSERT INTO "{schema}"."_dlt_loads" VALUES '
                f"('{load_id}', 0, '2026-04-01 10:00:00'{svh_val})"
            )
            for table, rows in tables:
                con.execute(
                    f'CREATE TABLE "{schema}"."{table}" '
                    f"(id INTEGER, _dlt_load_id VARCHAR)"
                )
                for r in range(rows):
                    con.execute(
                        f'INSERT INTO "{schema}"."{table}" VALUES ({r}, \'{load_id}\')'
                    )
    finally:
        con.close()
    return db_path


def _write_run_results(
    dbt_project_dir: Path,
    *,
    invocation_id: str = "inv-1",
    command: str = "build",
    dbt_version: str = "1.9.0",
    target: str = "dev",
    success: bool = True,
    elapsed: float = 12.5,
    results: list[dict] | None = None,
) -> None:
    """Write a plausible target/run_results.json into a fake dbt project."""
    import json as _json

    default_results = [
        {
            "unique_id": "model.demo.stg_orders",
            "status": "success",
            "execution_time": 0.8,
            "timing": [
                {
                    "name": "compile",
                    "started_at": "2026-04-01T10:00:00.000Z",
                    "completed_at": "2026-04-01T10:00:00.100Z",
                },
                {
                    "name": "execute",
                    "started_at": "2026-04-01T10:00:00.100Z",
                    "completed_at": "2026-04-01T10:00:00.900Z",
                },
            ],
            "adapter_response": {"rows_affected": 1000},
            "message": None,
        },
        {
            "unique_id": "test.demo.not_null_stg_orders_id",
            "status": "pass",
            "execution_time": 0.1,
            "timing": [],
            "adapter_response": {},
            "message": None,
        },
    ]
    doc = {
        "metadata": {
            "dbt_version": dbt_version,
            "generated_at": "2026-04-01T10:00:01.000Z",
            "invocation_id": invocation_id,
        },
        "args": {"which": command, "target": target},
        "results": results if results is not None else default_results,
        "elapsed_time": elapsed,
        "success": success,
    }
    target_dir = dbt_project_dir / "target"
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "run_results.json").write_text(_json.dumps(doc))


class TestCaptureDlt:
    """Unit tests for observability.capture_dlt."""

    def test_no_op_when_raw_db_missing(self, tmp_path: Path):
        from tycoon.observability import capture_dlt

        assert capture_dlt(tmp_path / "meta.duckdb", tmp_path / "missing.duckdb") == 0

    def test_no_op_when_no_dlt_loads(self, tmp_path: Path):
        from tycoon.observability import capture_dlt

        raw = tmp_path / "raw.duckdb"
        con = duckdb.connect(str(raw))
        con.execute("CREATE SCHEMA plain")
        con.execute("CREATE TABLE plain.thing (id INTEGER)")
        con.close()

        meta = tmp_path / "meta.duckdb"
        capture_dlt(meta, raw)

        probe = duckdb.connect(str(meta), read_only=True)
        try:
            row = probe.execute("SELECT count(*) FROM dlt_runs").fetchone()
            assert row is not None and row[0] == 0
        finally:
            probe.close()

    def test_mirrors_loads_and_row_counts(self, tmp_path: Path):
        from tycoon.observability import capture_dlt

        raw = _make_dlt_db(
            tmp_path,
            schemas={
                "raw_src_a": [("items", 3), ("orders", 5)],
                "raw_src_b": [("events", 7)],
            },
        )
        meta = tmp_path / "meta.duckdb"
        capture_dlt(meta, raw)

        con = duckdb.connect(str(meta), read_only=True)
        try:
            runs = con.execute(
                "SELECT source_schema, load_id, status FROM dlt_runs ORDER BY source_schema"
            ).fetchall()
            assert runs == [
                ("raw_src_a", "load-1", 0),
                ("raw_src_b", "load-2", 0),
            ]

            rows = con.execute(
                "SELECT source_schema, table_name, rows_loaded "
                "FROM dlt_rows_by_table ORDER BY source_schema, table_name"
            ).fetchall()
            assert rows == [
                ("raw_src_a", "items", 3),
                ("raw_src_a", "orders", 5),
                ("raw_src_b", "events", 7),
            ]
        finally:
            con.close()

    def test_idempotent_repeated_captures(self, tmp_path: Path):
        from tycoon.observability import capture_dlt

        raw = _make_dlt_db(tmp_path, schemas={"s": [("t", 2)]})
        meta = tmp_path / "meta.duckdb"

        capture_dlt(meta, raw)
        capture_dlt(meta, raw)  # re-capture same loads → no duplicates

        con = duckdb.connect(str(meta), read_only=True)
        try:
            runs = con.execute("SELECT count(*) FROM dlt_runs").fetchone()
            assert runs is not None and runs[0] == 1
            rows = con.execute("SELECT count(*) FROM dlt_rows_by_table").fetchone()
            assert rows is not None and rows[0] == 1
        finally:
            con.close()

    def test_tolerates_missing_schema_version_hash(self, tmp_path: Path):
        from tycoon.observability import capture_dlt

        raw = _make_dlt_db(
            tmp_path,
            schemas={"raw_old": [("items", 1)]},
            include_schema_version_hash=False,
        )
        meta = tmp_path / "meta.duckdb"
        capture_dlt(meta, raw)

        con = duckdb.connect(str(meta), read_only=True)
        try:
            row = con.execute(
                "SELECT schema_version_hash FROM dlt_runs"
            ).fetchone()
            assert row is not None and row[0] is None
        finally:
            con.close()


class TestCaptureDbt:
    """Unit tests for observability.capture_dbt."""

    def test_no_op_when_run_results_missing(self, tmp_path: Path):
        from tycoon.observability import capture_dbt

        dbt_dir = tmp_path / "dbt"
        dbt_dir.mkdir()
        meta = tmp_path / "meta.duckdb"
        assert capture_dbt(meta, dbt_dir) is None

    def test_captures_invocation_and_nodes(self, tmp_path: Path):
        from tycoon.observability import capture_dbt

        dbt_dir = tmp_path / "dbt"
        dbt_dir.mkdir()
        _write_run_results(dbt_dir, invocation_id="abc-123", command="build")

        meta = tmp_path / "meta.duckdb"
        result = capture_dbt(meta, dbt_dir, command="build")
        assert result == "abc-123"

        con = duckdb.connect(str(meta), read_only=True)
        try:
            run = con.execute(
                "SELECT invocation_id, command, success, models_ok, tests_passed "
                "FROM dbt_runs"
            ).fetchone()
            assert run == ("abc-123", "build", True, 1, 1)

            nodes = con.execute(
                "SELECT node_name, resource_type, status, rows_affected "
                "FROM dbt_nodes ORDER BY node_name"
            ).fetchall()
            assert nodes == [
                ("model.demo.stg_orders", "model", "success", 1000),
                ("test.demo.not_null_stg_orders_id", "test", "pass", None),
            ]
        finally:
            con.close()

    def test_skips_duplicate_invocation(self, tmp_path: Path):
        from tycoon.observability import capture_dbt

        dbt_dir = tmp_path / "dbt"
        dbt_dir.mkdir()
        _write_run_results(dbt_dir, invocation_id="dup-1")

        meta = tmp_path / "meta.duckdb"
        assert capture_dbt(meta, dbt_dir) == "dup-1"
        assert capture_dbt(meta, dbt_dir) is None  # already captured

        con = duckdb.connect(str(meta), read_only=True)
        try:
            row = con.execute("SELECT count(*) FROM dbt_runs").fetchone()
            assert row is not None and row[0] == 1
        finally:
            con.close()

    def test_counts_failed_tests_and_model_errors(self, tmp_path: Path):
        from tycoon.observability import capture_dbt

        dbt_dir = tmp_path / "dbt"
        dbt_dir.mkdir()
        _write_run_results(
            dbt_dir,
            invocation_id="mixed-1",
            success=False,
            results=[
                {
                    "unique_id": "model.demo.ok_model",
                    "status": "success",
                    "execution_time": 0.5,
                    "timing": [],
                    "adapter_response": {"rows_affected": 10},
                },
                {
                    "unique_id": "model.demo.bad_model",
                    "status": "error",
                    "execution_time": 0.1,
                    "timing": [],
                    "adapter_response": {},
                    "message": "boom",
                },
                {
                    "unique_id": "test.demo.t1",
                    "status": "fail",
                    "execution_time": 0.1,
                    "timing": [],
                    "adapter_response": {},
                },
            ],
        )

        meta = tmp_path / "meta.duckdb"
        capture_dbt(meta, dbt_dir)

        con = duckdb.connect(str(meta), read_only=True)
        try:
            row = con.execute(
                "SELECT success, models_ok, models_error, tests_passed, tests_failed FROM dbt_runs"
            ).fetchone()
            assert row == (False, 1, 1, 0, 1)
        finally:
            con.close()


class TestRefreshUsageDashboards:
    """Integration tests for rill_generator.refresh_usage_dashboards."""

    def test_no_op_when_rill_dir_missing(self, tmp_path: Path):
        from tycoon.observability import capture_dlt
        from tycoon.scaffolding.rill_generator import refresh_usage_dashboards

        raw = _make_dlt_db(tmp_path, schemas={"s": [("t", 1)]})
        # seed metadata
        capture_dlt(tmp_path / ".tycoon" / "metadata.duckdb", raw)

        result = refresh_usage_dashboards(
            project_root=tmp_path, rill_dir=tmp_path / "does_not_exist"
        )
        assert result == []

    def test_no_op_when_metadata_db_missing(self, tmp_path: Path):
        from tycoon.scaffolding.rill_generator import refresh_usage_dashboards

        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        assert refresh_usage_dashboards(project_root=tmp_path, rill_dir=rill_dir) == []

    def test_emits_only_dlt_dashboard_when_only_dlt_data(self, tmp_path: Path):
        from tycoon.observability import capture_dlt
        from tycoon.scaffolding.rill_generator import refresh_usage_dashboards

        raw = _make_dlt_db(tmp_path, schemas={"s": [("t", 2)]})
        capture_dlt(tmp_path / ".tycoon" / "metadata.duckdb", raw)

        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        refresh_usage_dashboards(project_root=tmp_path, rill_dir=rill_dir)

        assert (rill_dir / "dashboards" / "_tycoon_dlt_usage.yaml").exists()
        assert not (rill_dir / "dashboards" / "_tycoon_dbt_usage.yaml").exists()

        parquet_dir = tmp_path / "data" / "parquet" / "_tycoon"
        assert (parquet_dir / "dlt_runs.parquet").exists()
        assert (parquet_dir / "dlt_rows_by_table.parquet").exists()

    def test_emits_both_dashboards_when_both_data_present(self, tmp_path: Path):
        from tycoon.observability import capture_dbt, capture_dlt
        from tycoon.scaffolding.rill_generator import refresh_usage_dashboards

        meta = tmp_path / ".tycoon" / "metadata.duckdb"

        raw = _make_dlt_db(tmp_path, schemas={"s": [("t", 1)]})
        capture_dlt(meta, raw)

        dbt_dir = tmp_path / "dbt"
        dbt_dir.mkdir()
        _write_run_results(dbt_dir, invocation_id="both-1")
        capture_dbt(meta, dbt_dir)

        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        refresh_usage_dashboards(project_root=tmp_path, rill_dir=rill_dir)

        assert (rill_dir / "dashboards" / "_tycoon_dlt_usage.yaml").exists()
        assert (rill_dir / "dashboards" / "_tycoon_dbt_usage.yaml").exists()

        assert (rill_dir / "sources" / "_tycoon_dlt_runs.yaml").exists()
        assert (rill_dir / "sources" / "_tycoon_dbt_runs.yaml").exists()
        assert (rill_dir / "metrics" / "_tycoon_dbt_runs_mv.yaml").exists()
        assert (rill_dir / "metrics" / "_tycoon_dbt_nodes_mv.yaml").exists()

    def test_dashboard_yamls_reference_parquet_paths(self, tmp_path: Path):
        from tycoon.observability import capture_dlt
        from tycoon.scaffolding.rill_generator import refresh_usage_dashboards

        raw = _make_dlt_db(tmp_path, schemas={"s": [("t", 1)]})
        capture_dlt(tmp_path / ".tycoon" / "metadata.duckdb", raw)

        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        refresh_usage_dashboards(project_root=tmp_path, rill_dir=rill_dir)

        src_yaml = (rill_dir / "sources" / "_tycoon_dlt_runs.yaml").read_text()
        assert "local_file" in src_yaml
        assert "dlt_runs.parquet" in src_yaml
