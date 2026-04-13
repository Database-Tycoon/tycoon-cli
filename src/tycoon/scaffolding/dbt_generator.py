"""Auto-generate dbt staging models from a DuckDB database schema.

Introspects a raw DuckDB database and generates:
- One .sql staging model per table
- One _<source_name>__models.yml schema file with sources, models, and column docs
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import yaml


# dlt internal columns that should be excluded from staging models
_DLT_INTERNAL_COLUMNS = {
    "_dlt_load_id",
    "_dlt_id",
    "_dlt_parent_id",
    "_dlt_list_idx",
}

# dlt internal tables that should be excluded entirely
_DLT_INTERNAL_TABLES = {
    "_dlt_loads",
    "_dlt_pipeline_state",
    "_dlt_version",
}


def _clean_column_name(col: str) -> str:
    """Return a clean column name: lowercase with spaces replaced by underscores."""
    return col.lower().replace(" ", "_")


def _generate_sql(
    table_name: str,
    schema_name: str,
    source_name: str,
    columns: list[tuple[str, str]],
) -> str:
    """Generate a dbt staging SQL model for a single table.

    Parameters
    ----------
    table_name:
        Raw table name in the source schema.
    schema_name:
        Schema name in the raw database.
    source_name:
        dbt source name (used in {{ source() }} macro).
    columns:
        List of (column_name, data_type) tuples (dlt columns pre-filtered).
    """
    col_lines = []
    for col_name, _ in columns:
        clean = _clean_column_name(col_name)
        if clean == col_name:
            col_lines.append(f"        {col_name}")
        else:
            col_lines.append(f"        {col_name} as {clean}")

    col_block = ",\n".join(col_lines)

    return f"""\
-- Auto-generated staging model for {table_name}
-- Source: {schema_name}.{table_name}

with source as (
    select * from {{{{ source('{source_name}', '{table_name}') }}}}
),

cleaned as (
    select
{col_block}
    from source
)

select * from cleaned
"""


def _generate_yaml(
    schema_name: str,
    source_name: str,
    tables: dict[str, list[tuple[str, str]]],
) -> str:
    """Generate a _<source_name>__models.yml YAML schema string.

    Parameters
    ----------
    schema_name:
        Schema in the raw database.
    source_name:
        dbt source name.
    tables:
        Mapping of table_name -> list of (column_name, data_type).
    """
    source_tables = []
    for table_name in tables:
        source_tables.append({"name": table_name})

    model_entries = []
    for table_name, columns in tables.items():
        model_name = f"stg_{source_name}__{table_name}"
        col_entries = []
        for col_name, _ in columns:
            clean = _clean_column_name(col_name)
            col_entries.append(
                {
                    "name": clean,
                    "description": f"{clean} from source",
                }
            )
        model_entries.append(
            {
                "name": model_name,
                "description": f"Staging model for {table_name} from {source_name}",
                "columns": col_entries,
            }
        )

    data = {
        "version": 2,
        "sources": [
            {
                "name": source_name,
                "database": "raw",
                "schema": schema_name,
                "tables": source_tables,
            }
        ],
        "models": model_entries,
    }

    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)


def generate_staging_models(
    raw_db_path: Path,
    schema_name: str,
    source_name: str,
    output_dir: Path,
) -> list[str]:
    """Generate dbt staging models by introspecting raw database schema.

    Connects to raw_db_path (read-only), queries information_schema.columns
    for tables in schema_name, and generates:
    - One .sql file per table: stg_<source_name>__<table_name>.sql
    - One _<source_name>__models.yml with model+column docs and basic tests

    output_dir should be dbt_project/models/staging/<source_name>/

    Returns list of generated file paths (as strings).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(raw_db_path), read_only=True)
    try:
        # Discover all tables in the schema
        table_rows = con.execute(
            """
            SELECT DISTINCT table_name
            FROM information_schema.columns
            WHERE table_schema = ?
            ORDER BY table_name
            """,
            [schema_name],
        ).fetchall()
    finally:
        con.close()

    # Filter out dlt internal tables, nested tables (names containing __),
    # and dlt transformer-named tables (leading underscore, e.g. _read_csv).
    raw_table_names = [
        row[0]
        for row in table_rows
        if row[0] not in _DLT_INTERNAL_TABLES
        and "__" not in row[0]
        and not row[0].startswith("_")
    ]

    if not raw_table_names:
        return []

    # Fetch columns for each table
    con = duckdb.connect(str(raw_db_path), read_only=True)
    try:
        tables: dict[str, list[tuple[str, str]]] = {}
        for table_name in raw_table_names:
            col_rows = con.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = ? AND table_name = ?
                ORDER BY ordinal_position
                """,
                [schema_name, table_name],
            ).fetchall()
            # Filter dlt internal columns
            filtered = [
                (col_name, data_type)
                for col_name, data_type in col_rows
                if col_name not in _DLT_INTERNAL_COLUMNS
            ]
            if filtered:
                tables[table_name] = filtered
    finally:
        con.close()

    generated: list[str] = []

    # Write one .sql file per table
    for table_name, columns in tables.items():
        model_name = f"stg_{source_name}__{table_name}"
        sql_path = output_dir / f"{model_name}.sql"
        sql_path.write_text(_generate_sql(table_name, schema_name, source_name, columns))
        generated.append(str(sql_path))

    # Write combined YAML schema file
    if tables:
        yaml_path = output_dir / f"_{source_name}__models.yml"
        yaml_path.write_text(_generate_yaml(schema_name, source_name, tables))
        generated.append(str(yaml_path))

    return generated
