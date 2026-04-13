"""Auto-generate Rill sources, metrics views, and explore dashboards.

Architecture (Rill 0.83 + local_file connector):
  1. Export each raw table to a Parquet file under {data_dir}/parquet/{schema_name}/
  2. Write a Rill source YAML (type: source, connector: local_file) per table
  3. Write a metrics_view YAML referencing the source name
  4. Write an explore YAML referencing the metrics_view

File chain per table:
  sources/{model_name}.yaml  →  metrics/{model_name}_mv.yaml  →  dashboards/{model_name}.yaml

The olap_connector in rill.yaml is set to 'duckdb' (Rill's built-in in-memory OLAP).
"""

from __future__ import annotations

import re
from pathlib import Path

import duckdb


# ---------------------------------------------------------------------------
# dlt internal columns / tables — excluded from all Rill output
# ---------------------------------------------------------------------------

_DLT_INTERNAL_COLUMNS = {
    "_dlt_load_id",
    "_dlt_id",
    "_dlt_parent_id",
    "_dlt_list_idx",
}

_DLT_INTERNAL_TABLES = {
    "_dlt_loads",
    "_dlt_pipeline_state",
    "_dlt_version",
}


# ---------------------------------------------------------------------------
# Column type sets used for measure / dimension classification
# ---------------------------------------------------------------------------

_DIMENSION_TYPES = {
    "VARCHAR",
    "TEXT",
    "STRING",
    "CHAR",
    "BOOLEAN",
    "BOOL",
    "DATE",
    "TIMESTAMP",
    "TIMESTAMP WITH TIME ZONE",
    "TIMESTAMPTZ",
}

_SUM_MEASURE_TYPES = {
    "INTEGER",
    "INT",
    "INT4",
    "INT8",
    "BIGINT",
    "SMALLINT",
    "TINYINT",
    "HUGEINT",
    "UBIGINT",
    "UINTEGER",
    "USMALLINT",
    "UTINYINT",
}

_AVG_MEASURE_TYPES = {
    "FLOAT",
    "FLOAT4",
    "FLOAT8",
    "DOUBLE",
    "REAL",
    "DECIMAL",
    "NUMERIC",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _title_label(name: str) -> str:
    """Convert a snake_case column name to a Title Case label."""
    return name.replace("_", " ").title()


def _classify_column(col_name: str, data_type: str) -> str:
    """Return 'dimension', 'sum_measure', 'avg_measure', or 'skip'."""
    upper_type = data_type.upper().split("(")[0].strip()

    # ID / key columns are dimensions regardless of numeric type
    if col_name.lower().endswith("_id") or col_name.lower() == "id":
        return "dimension"

    if upper_type in _DIMENSION_TYPES:
        return "dimension"

    if upper_type in _SUM_MEASURE_TYPES:
        return "sum_measure"

    if upper_type in _AVG_MEASURE_TYPES:
        return "avg_measure"

    # Fallback: treat unknown types as dimensions so nothing is silently dropped
    return "dimension"


# ---------------------------------------------------------------------------
# YAML generators
# ---------------------------------------------------------------------------


def _generate_source_yaml(parquet_path: Path) -> str:
    """Return a Rill source YAML string pointing at a local Parquet file."""
    return f"""\
type: source
connector: local_file
path: {parquet_path}
"""


def _generate_metrics_view_yaml(
    model_name: str,
    columns: list[tuple[str, str]],
) -> str:
    """Return a Rill metrics_view YAML string.

    Parameters
    ----------
    model_name:
        The Rill source name (= the source YAML filename without .yaml).
    columns:
        List of (column_name, data_type) tuples with dlt columns pre-filtered.
    """
    measures_lines: list[str] = []
    dimensions_lines: list[str] = []

    # Always add a record count measure first
    measures_lines += [
        "- expression: count(*)",
        "  label: Records",
        "  format_d3: ','",
    ]

    for col_name, data_type in columns:
        classification = _classify_column(col_name, data_type)
        label = _title_label(col_name)

        if classification == "dimension":
            dimensions_lines += [
                f"- column: {col_name}",
                f"  label: {label}",
            ]
        elif classification == "sum_measure":
            measures_lines += [
                f"- expression: sum({col_name})",
                f"  label: Total {label}",
                "  format_d3: ','",
            ]
        elif classification == "avg_measure":
            measures_lines += [
                f"- expression: avg({col_name})",
                f"  label: Avg {label}",
                "  format_d3: ',.2f'",
            ]

    measures_block = "\n".join(f"  {line}" for line in measures_lines)
    # If no dimensions were classified, omit the block rather than emit empty
    if dimensions_lines:
        dimensions_block = "\n".join(f"  {line}" for line in dimensions_lines)
        dims_section = f"dimensions:\n{dimensions_block}\n"
    else:
        dims_section = ""

    return f"""\
type: metrics_view
model: {model_name}
measures:
{measures_block}
{dims_section}"""


def _generate_explore_yaml(
    source_name: str,
    table_name: str,
    metrics_view_name: str,
) -> str:
    """Return a Rill explore YAML string."""
    return f"""\
type: explore
title: {source_name} / {table_name}
metrics_view: {metrics_view_name}
"""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def generate_rill_config(
    raw_db_path: Path,
    warehouse_db_path: Path,
    schema_name: str,
    source_name: str,
    output_dir: Path,
) -> list[str]:
    """Generate Rill sources, metrics views, and explore dashboards.

    output_dir is the rill/ project directory.

    Creates:
    - {raw_db_path.parent}/parquet/{schema_name}/{table}.parquet — one per table
    - sources/{model_name}.yaml — reads from the parquet file via local_file connector
    - metrics/{model_name}_mv.yaml — metrics view
    - dashboards/{model_name}.yaml — explore dashboard

    Also sets olap_connector: duckdb in rill.yaml if it exists.

    Returns list of generated file paths.
    """
    generated: list[str] = []

    # ------------------------------------------------------------------
    # 1. Introspect raw.duckdb for this schema
    # ------------------------------------------------------------------
    con = duckdb.connect(str(raw_db_path), read_only=True)
    try:
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

    # Filter out dlt internal tables, nested child tables (names with __),
    # and dlt transformer-named tables (leading underscore, e.g. _read_csv).
    raw_table_names = [
        row[0]
        for row in table_rows
        if row[0] not in _DLT_INTERNAL_TABLES
        and "__" not in row[0]
        and not row[0].startswith("_")
    ]

    if not raw_table_names:
        return generated

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
            filtered = [
                (col_name, data_type)
                for col_name, data_type in col_rows
                if col_name not in _DLT_INTERNAL_COLUMNS
                and not col_name.startswith("_dlt_")
            ]
            if filtered:
                tables[table_name] = filtered
    finally:
        con.close()

    if not tables:
        return generated

    # ------------------------------------------------------------------
    # 2. Export tables to Parquet
    # ------------------------------------------------------------------
    parquet_dir = raw_db_path.parent / "parquet" / schema_name
    parquet_dir.mkdir(parents=True, exist_ok=True)

    table_parquet_paths: dict[str, Path] = {}

    export_con = duckdb.connect(str(raw_db_path), read_only=True)
    try:
        for table_name, columns in tables.items():
            parquet_path = parquet_dir / f"{table_name}.parquet"
            non_dlt_cols = [col for col, _ in columns]
            col_list = ", ".join(f'"{c}"' for c in non_dlt_cols)
            export_con.execute(
                f"""
                COPY (SELECT {col_list} FROM {schema_name}."{table_name}")
                TO '{parquet_path}' (FORMAT PARQUET)
                """
            )
            table_parquet_paths[table_name] = parquet_path
    finally:
        export_con.close()

    # ------------------------------------------------------------------
    # 3. Create Rill subdirectories
    # ------------------------------------------------------------------
    sources_dir = output_dir / "sources"
    metrics_dir = output_dir / "metrics"
    dashboards_dir = output_dir / "dashboards"

    for d in (sources_dir, metrics_dir, dashboards_dir):
        d.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 4. Write source / metrics_view / explore YAMLs per table
    # ------------------------------------------------------------------
    for table_name, columns in tables.items():
        model_name = f"stg_{source_name}__{table_name}"
        metrics_view_name = f"{model_name}_mv"
        parquet_path = table_parquet_paths[table_name]

        # Source YAML
        source_path = sources_dir / f"{model_name}.yaml"
        source_path.write_text(_generate_source_yaml(parquet_path))
        generated.append(str(source_path))

        # Metrics view YAML
        mv_path = metrics_dir / f"{metrics_view_name}.yaml"
        mv_path.write_text(_generate_metrics_view_yaml(model_name, columns))
        generated.append(str(mv_path))

        # Explore YAML
        explore_path = dashboards_dir / f"{model_name}.yaml"
        explore_path.write_text(
            _generate_explore_yaml(source_name, table_name, metrics_view_name)
        )
        generated.append(str(explore_path))

    # ------------------------------------------------------------------
    # 5. Update rill.yaml to set olap_connector: duckdb
    # ------------------------------------------------------------------
    rill_yaml_path = output_dir / "rill.yaml"
    if rill_yaml_path.exists():
        content = rill_yaml_path.read_text()
        updated = re.sub(r"olap_connector:.*", "olap_connector: duckdb", content)
        if updated != content:
            rill_yaml_path.write_text(updated)

    return generated
