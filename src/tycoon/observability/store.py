"""The metadata DuckDB file: where it lives, its schema, and its Parquet export."""

from __future__ import annotations

from pathlib import Path

import duckdb

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_METADATA_SUBDIR = ".tycoon"
_METADATA_FILENAME = "metadata.duckdb"


def metadata_db_path(project_root: Path) -> Path:
    """Return the canonical metadata.duckdb path for a project."""
    return project_root / _METADATA_SUBDIR / _METADATA_FILENAME


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS dlt_runs (
    source_schema        VARCHAR NOT NULL,
    load_id              VARCHAR NOT NULL,
    status               INTEGER,
    inserted_at          TIMESTAMP,
    schema_version_hash  VARCHAR,
    captured_at          TIMESTAMP,
    PRIMARY KEY (source_schema, load_id)
);

CREATE TABLE IF NOT EXISTS dlt_rows_by_table (
    source_schema  VARCHAR NOT NULL,
    table_name     VARCHAR NOT NULL,
    load_id        VARCHAR NOT NULL,
    rows_loaded    BIGINT,
    captured_at    TIMESTAMP,
    PRIMARY KEY (source_schema, table_name, load_id)
);

CREATE TABLE IF NOT EXISTS dbt_runs (
    invocation_id   VARCHAR PRIMARY KEY,
    command         VARCHAR,
    started_at      TIMESTAMP,
    elapsed_s       DOUBLE,
    success         BOOLEAN,
    models_ok       INTEGER,
    models_error    INTEGER,
    tests_passed    INTEGER,
    tests_failed    INTEGER,
    dbt_version     VARCHAR,
    target_name     VARCHAR,
    captured_at     TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dbt_nodes (
    invocation_id     VARCHAR NOT NULL,
    node_name         VARCHAR NOT NULL,
    resource_type     VARCHAR,
    status            VARCHAR,
    execution_time_s  DOUBLE,
    rows_affected     BIGINT,
    compile_time_s    DOUBLE,
    message           VARCHAR,
    PRIMARY KEY (invocation_id, node_name)
);

CREATE TABLE IF NOT EXISTS dlt_trace_runs (
    transaction_id    VARCHAR PRIMARY KEY,
    pipeline_name     VARCHAR,
    started_at        TIMESTAMP,
    finished_at       TIMESTAMP,
    duration_s        DOUBLE,
    engine_version    INTEGER,
    success           BOOLEAN,
    exception         VARCHAR,
    captured_at       TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dlt_trace_steps (
    transaction_id  VARCHAR NOT NULL,
    step            VARCHAR NOT NULL,
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    duration_s      DOUBLE,
    step_exception  VARCHAR,
    PRIMARY KEY (transaction_id, step)
);

CREATE TABLE IF NOT EXISTS dlt_trace_jobs (
    transaction_id   VARCHAR NOT NULL,
    load_id          VARCHAR NOT NULL,
    job_id           VARCHAR NOT NULL,
    table_name       VARCHAR,
    file_format      VARCHAR,
    state            VARCHAR,
    file_size_bytes  BIGINT,
    elapsed_s        DOUBLE,
    failed_message   VARCHAR,
    created_at       TIMESTAMP,
    PRIMARY KEY (transaction_id, job_id)
);

CREATE TABLE IF NOT EXISTS dbt_manifest_snapshots (
    invocation_id       VARCHAR PRIMARY KEY,
    generated_at        TIMESTAMP,
    dbt_schema_version  VARCHAR,
    fingerprint_json    VARCHAR,
    captured_at         TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dbt_schema_changes (
    invocation_id       VARCHAR NOT NULL,
    prev_invocation_id  VARCHAR,
    change_type         VARCHAR NOT NULL,
    unique_id           VARCHAR NOT NULL,
    column_name         VARCHAR,
    old_value           VARCHAR,
    new_value           VARCHAR,
    captured_at         TIMESTAMP,
    PRIMARY KEY (invocation_id, change_type, unique_id, column_name)
);

CREATE TABLE IF NOT EXISTS fivetran_connectors (
    connector_id   VARCHAR NOT NULL,
    name           VARCHAR,
    service        VARCHAR,
    schema_name    VARCHAR,
    paused         BOOLEAN,
    sync_state     VARCHAR,
    setup_state    VARCHAR,
    update_state   VARCHAR,
    succeeded_at   TIMESTAMP,
    failed_at      TIMESTAMP,
    captured_at    TIMESTAMP NOT NULL,
    PRIMARY KEY (connector_id, captured_at)
);
"""


def ensure_schema(metadata_db: Path) -> None:
    """Create the metadata schema if it doesn't exist. Idempotent."""
    metadata_db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(metadata_db))
    try:
        con.execute(_SCHEMA_SQL)
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Parquet export
# ---------------------------------------------------------------------------

_EXPORT_TABLES = (
    "dlt_runs",
    "dlt_rows_by_table",
    "dbt_runs",
    "dbt_nodes",
    "dlt_trace_runs",
    "dlt_trace_steps",
    "dlt_trace_jobs",
    "dbt_manifest_snapshots",
    "dbt_schema_changes",
)


def export_to_parquet(metadata_db: Path, parquet_dir: Path) -> dict[str, Path]:
    """Re-export every observability table to a Parquet file.

    Empty tables still produce Parquet files (with schema preserved) so
    Rill sources don't 404 on first view.

    Returns a mapping of table name -> Parquet path.
    """
    if not metadata_db.exists():
        return {}

    parquet_dir.mkdir(parents=True, exist_ok=True)
    ensure_schema(metadata_db)

    out: dict[str, Path] = {}
    con = duckdb.connect(str(metadata_db), read_only=True)
    try:
        for table in _EXPORT_TABLES:
            path = parquet_dir / f"{table}.parquet"
            con.execute(f"COPY (SELECT * FROM {table}) TO '{path}' (FORMAT PARQUET)")
            out[table] = path
        return out
    finally:
        con.close()


def has_any_observability_data(metadata_db: Path) -> tuple[bool, bool]:
    """Return (has_dlt, has_dbt) based on row counts in the metadata DB."""
    if not metadata_db.exists():
        return False, False
    con = duckdb.connect(str(metadata_db), read_only=True)
    try:
        ensure_exists = con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()
        names = {r[0] for r in ensure_exists}
        dlt_rows = 0
        dbt_rows = 0
        if "dlt_runs" in names:
            row = con.execute("SELECT count(*) FROM dlt_runs").fetchone()
            dlt_rows = row[0] if row else 0
        if "dbt_runs" in names:
            row = con.execute("SELECT count(*) FROM dbt_runs").fetchone()
            dbt_rows = row[0] if row else 0
        return dlt_rows > 0, dbt_rows > 0
    finally:
        con.close()
