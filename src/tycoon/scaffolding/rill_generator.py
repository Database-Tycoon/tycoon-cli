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

    # ------------------------------------------------------------------
    # 6. Refresh the global dlt + dbt usage dashboards if we have
    #    observability data captured. Idempotent; safe to call every time.
    # ------------------------------------------------------------------
    try:
        from tycoon.config import config

        generated.extend(
            refresh_usage_dashboards(project_root=config.root, rill_dir=output_dir)
        )
    except Exception:
        pass

    return generated


# ---------------------------------------------------------------------------
# Global "Tycoon Observability" dashboards — dlt + dbt run history, sourced
# from .tycoon/metadata.duckdb and surfaced in Rill via Parquet exports.
# ---------------------------------------------------------------------------


_USAGE_PARQUET_SUBDIR = "_tycoon"

_DLT_RUNS_SRC = "_tycoon_dlt_runs"
_DLT_ROWS_SRC = "_tycoon_dlt_rows_by_table"
_DLT_DASHBOARD = "_tycoon_dlt_usage"

_DBT_RUNS_SRC = "_tycoon_dbt_runs"
_DBT_NODES_SRC = "_tycoon_dbt_nodes"
_DBT_DASHBOARD = "_tycoon_dbt_usage"


def _dlt_runs_mv_yaml() -> str:
    return f"""\
type: metrics_view
model: {_DLT_RUNS_SRC}
title: dlt Loads
timeseries: inserted_at
measures:
  - expression: count(*)
    label: Total Loads
    format_d3: ','
  - expression: sum(case when status = 0 then 1 else 0 end)
    label: Successful Loads
    format_d3: ','
  - expression: avg(case when status = 0 then 1.0 else 0.0 end)
    label: Success Rate
    format_d3: '.0%'
dimensions:
  - column: source_schema
    label: Source Schema
  - column: status
    label: Status
  - column: load_id
    label: Load ID
  - column: schema_version_hash
    label: Schema Version
"""


def _dlt_rows_mv_yaml() -> str:
    return f"""\
type: metrics_view
model: {_DLT_ROWS_SRC}
title: Rows Loaded by Table
measures:
  - expression: sum(rows_loaded)
    label: Rows Loaded
    format_d3: ','
  - expression: count(distinct load_id)
    label: Load Count
    format_d3: ','
dimensions:
  - column: source_schema
    label: Source Schema
  - column: table_name
    label: Table
  - column: load_id
    label: Load ID
"""


def _dlt_dashboard_yaml() -> str:
    return f"""\
type: explore
title: dlt Usage
description: >
  Ingestion history mirrored from each source schema's _dlt_loads table.
  Row counts per load reflect rows currently present tagged with that
  _dlt_load_id; for replace/merge write dispositions, only the most
  recent load's counts are accurate.
metrics_view: {_DLT_RUNS_SRC}_mv
"""


def _dbt_runs_mv_yaml() -> str:
    return f"""\
type: metrics_view
model: {_DBT_RUNS_SRC}
title: dbt Runs
timeseries: started_at
measures:
  - expression: count(*)
    label: Total Runs
    format_d3: ','
  - expression: sum(case when success then 1 else 0 end)
    label: Successful Runs
    format_d3: ','
  - expression: avg(case when success then 1.0 else 0.0 end)
    label: Success Rate
    format_d3: '.0%'
  - expression: avg(elapsed_s)
    label: Avg Duration (s)
    format_d3: ',.2f'
  - expression: sum(models_ok)
    label: Models Built
    format_d3: ','
  - expression: sum(models_error)
    label: Model Errors
    format_d3: ','
  - expression: sum(tests_passed)
    label: Tests Passed
    format_d3: ','
  - expression: sum(tests_failed)
    label: Tests Failed
    format_d3: ','
dimensions:
  - column: command
    label: Command
  - column: target_name
    label: Target
  - column: dbt_version
    label: dbt Version
  - column: invocation_id
    label: Invocation ID
"""


def _dbt_nodes_mv_yaml() -> str:
    return f"""\
type: metrics_view
model: {_DBT_NODES_SRC}
title: dbt Nodes
measures:
  - expression: count(*)
    label: Node Runs
    format_d3: ','
  - expression: avg(execution_time_s)
    label: Avg Execution (s)
    format_d3: ',.2f'
  - expression: sum(execution_time_s)
    label: Total Execution (s)
    format_d3: ',.1f'
  - expression: sum(rows_affected)
    label: Rows Affected
    format_d3: ','
dimensions:
  - column: node_name
    label: Node
  - column: resource_type
    label: Resource Type
  - column: status
    label: Status
  - column: invocation_id
    label: Invocation ID
"""


def _dbt_dashboard_yaml() -> str:
    return f"""\
type: explore
title: dbt Usage
description: >
  dbt invocation history parsed from target/run_results.json. One row per
  invocation in dbt_runs; one row per node (model/test/seed/snapshot) per
  invocation in dbt_nodes.
metrics_view: {_DBT_RUNS_SRC}_mv
"""


def _write_parquet_backed_source_set(
    parquet_paths: dict[str, Path],
    output_dir: Path,
    specs: list[tuple[str, str, str, str]],
) -> list[str]:
    """Write sources / metrics_view / dashboard YAMLs for a set of parquets.

    Each spec is (parquet_table_name, source_yaml_name,
    metrics_view_yaml, dashboard_yaml). source_yaml_name is the filename
    stem (also the metrics_view's `model:` reference). metrics_view_yaml
    is the full YAML body for the metrics view. dashboard_yaml is empty
    for source-only specs.
    """
    sources_dir = output_dir / "sources"
    metrics_dir = output_dir / "metrics"
    dashboards_dir = output_dir / "dashboards"
    for d in (sources_dir, metrics_dir, dashboards_dir):
        d.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    for table_name, src_name, mv_yaml, dashboard_yaml in specs:
        parquet_path = parquet_paths.get(table_name)
        if parquet_path is None:
            continue

        src_path = sources_dir / f"{src_name}.yaml"
        src_path.write_text(_generate_source_yaml(parquet_path))
        written.append(str(src_path))

        mv_path = metrics_dir / f"{src_name}_mv.yaml"
        mv_path.write_text(mv_yaml)
        written.append(str(mv_path))

        if dashboard_yaml:
            dashboard_filename = src_name.replace("_runs", "_usage")
            dashboard_path = dashboards_dir / f"{dashboard_filename}.yaml"
            dashboard_path.write_text(dashboard_yaml)
            written.append(str(dashboard_path))

    return written


def refresh_usage_dashboards(project_root: Path, rill_dir: Path) -> list[str]:
    """Re-export metadata.duckdb → Parquet and emit Rill dashboard YAMLs.

    Reads ``.tycoon/metadata.duckdb`` at ``project_root``, re-exports
    four Parquet files under ``data/parquet/_tycoon/``, and writes (or
    overwrites) the sources/metrics_view/explore YAMLs for the dlt and
    dbt usage dashboards. Dashboards without any captured data are
    skipped so Rill doesn't show empty explores.

    Safe to call from any post-capture path. No-ops if the Rill project
    directory doesn't exist yet.
    """
    from tycoon.observability import (
        export_to_parquet,
        has_any_observability_data,
        metadata_db_path,
    )

    if not rill_dir.exists():
        return []

    metadata_db = metadata_db_path(project_root)
    if not metadata_db.exists():
        return []

    has_dlt, has_dbt = has_any_observability_data(metadata_db)
    if not (has_dlt or has_dbt):
        return []

    parquet_dir = project_root / "data" / "parquet" / _USAGE_PARQUET_SUBDIR
    parquet_paths = export_to_parquet(metadata_db, parquet_dir)

    written: list[str] = [str(p) for p in parquet_paths.values()]

    if has_dlt:
        written.extend(
            _write_parquet_backed_source_set(
                parquet_paths,
                rill_dir,
                [
                    (
                        "dlt_runs",
                        _DLT_RUNS_SRC,
                        _dlt_runs_mv_yaml(),
                        _dlt_dashboard_yaml(),
                    ),
                    (
                        "dlt_rows_by_table",
                        _DLT_ROWS_SRC,
                        _dlt_rows_mv_yaml(),
                        "",
                    ),
                ],
            )
        )

    if has_dbt:
        written.extend(
            _write_parquet_backed_source_set(
                parquet_paths,
                rill_dir,
                [
                    (
                        "dbt_runs",
                        _DBT_RUNS_SRC,
                        _dbt_runs_mv_yaml(),
                        _dbt_dashboard_yaml(),
                    ),
                    (
                        "dbt_nodes",
                        _DBT_NODES_SRC,
                        _dbt_nodes_mv_yaml(),
                        "",
                    ),
                ],
            )
        )

    return written
