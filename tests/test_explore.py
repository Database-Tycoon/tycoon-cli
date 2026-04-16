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
        generated = generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )

        sql_files = [f for f in generated if f.endswith(".sql")]
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
        generated = generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )

        yaml_files = [f for f in generated if f.endswith(".yml")]
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
        generated = generate_staging_models(
            raw_db_path=test_db_with_nested,
            schema_name="s",
            source_name="src",
            output_dir=output_dir,
        )

        file_names = [Path(f).name for f in generated]
        # orders should be included, orders__items should not
        assert any("stg_src__orders" in n for n in file_names)
        assert not any("items" in n for n in file_names)

    def test_dlt_internal_tables_excluded(self, tmp_path: Path, test_db_with_nested: Path):
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "staging"
        generated = generate_staging_models(
            raw_db_path=test_db_with_nested,
            schema_name="s",
            source_name="src",
            output_dir=output_dir,
        )

        file_names = [Path(f).name for f in generated]
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

    def test_returns_list_of_paths(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.dbt_generator import generate_staging_models

        output_dir = tmp_path / "staging"
        result = generate_staging_models(
            raw_db_path=test_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=output_dir,
        )
        assert isinstance(result, list)
        assert all(isinstance(p, str) for p in result)


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

        warehouse_db = tmp_path / "warehouse.duckdb"
        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            warehouse_db_path=warehouse_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )

        source_path = rill_dir / "sources" / "stg_my_source__my_table.yaml"
        assert source_path.exists()

    def test_source_yaml_uses_local_file_connector(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        warehouse_db = tmp_path / "warehouse.duckdb"
        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            warehouse_db_path=warehouse_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )

        content = (rill_dir / "sources" / "stg_my_source__my_table.yaml").read_text()
        assert "local_file" in content
        assert "parquet" in content

    def test_creates_metrics_view_yaml(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        warehouse_db = tmp_path / "warehouse.duckdb"
        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            warehouse_db_path=warehouse_db,
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

        warehouse_db = tmp_path / "warehouse.duckdb"
        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            warehouse_db_path=warehouse_db,
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

        warehouse_db = tmp_path / "warehouse.duckdb"
        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            warehouse_db_path=warehouse_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )

        mv_path = rill_dir / "metrics" / "stg_my_source__my_table_mv.yaml"
        content = mv_path.read_text()
        assert "count(*)" in content

    def test_returns_list_of_paths(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        warehouse_db = tmp_path / "warehouse.duckdb"
        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        result = generate_rill_config(
            raw_db_path=test_db,
            warehouse_db_path=warehouse_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )
        assert isinstance(result, list)
        assert all(isinstance(p, str) for p in result)

    def test_exports_parquet_files(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        warehouse_db = tmp_path / "warehouse.duckdb"
        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            warehouse_db_path=warehouse_db,
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

        warehouse_db = tmp_path / "warehouse.duckdb"
        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            warehouse_db_path=warehouse_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )

        mv_path = rill_dir / "metrics" / "stg_my_source__my_table_mv.yaml"
        content = mv_path.read_text()
        assert "column: name" in content

    def test_double_column_is_avg_measure(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        warehouse_db = tmp_path / "warehouse.duckdb"
        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            warehouse_db_path=warehouse_db,
            schema_name="test_schema",
            source_name="my_source",
            output_dir=rill_dir,
        )

        mv_path = rill_dir / "metrics" / "stg_my_source__my_table_mv.yaml"
        content = mv_path.read_text()
        assert "avg(amount)" in content

    def test_dlt_columns_not_in_metrics_view(self, tmp_path: Path, test_db: Path):
        from tycoon.scaffolding.rill_generator import generate_rill_config

        warehouse_db = tmp_path / "warehouse.duckdb"
        rill_dir = tmp_path / "rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\nolap_connector: duckdb\n")
        generate_rill_config(
            raw_db_path=test_db,
            warehouse_db_path=warehouse_db,
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
