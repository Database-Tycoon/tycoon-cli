"""Observability — capture dlt + dbt run history in a dedicated metadata DuckDB.

Architecture
============

A separate, disposable DuckDB file at ``.tycoon/metadata.duckdb`` holds
tycoon's observability state: dlt load history (mirrored from each raw
database) and dbt invocation history (parsed from
``target/run_results.json``). This file is decoupled from the
user-facing raw + warehouse databases so it survives ``tycoon data
clean`` and can be queried directly::

    tycoon data query --db .tycoon/metadata.duckdb "SELECT * FROM dbt_runs ORDER BY started_at DESC"

Capture points
--------------

* ``capture_dlt``: called from the ingestion runner after each
  successful dlt load. Idempotently mirrors ``<schema>._dlt_loads`` and
  per-table ``_dlt_load_id`` row counts into the metadata DB.
* ``capture_dbt``: called from the ``tycoon data transform`` command
  after each ``run`` / ``test`` / ``build``. Parses
  ``target/run_results.json`` and inserts one row per invocation plus
  one row per node.

Display
-------

``export_to_parquet`` re-writes four Parquet files under
``data/parquet/_tycoon/``. The Rill dashboard YAMLs emitted by
``rill_generator.refresh_usage_dashboards`` point at those Parquets via
Rill's ``local_file`` connector.

All operations are best-effort: capture failures never propagate to
the caller. Ingestion and dbt invocations must not fail because of
observability bookkeeping.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
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
# dlt capture
# ---------------------------------------------------------------------------


def _dlt_schemas(con: duckdb.DuckDBPyConnection) -> list[str]:
    rows = con.execute(
        """
        SELECT DISTINCT table_schema
        FROM information_schema.tables
        WHERE table_name = '_dlt_loads'
        ORDER BY table_schema
        """
    ).fetchall()
    return [r[0] for r in rows]


def _dlt_loads_columns(con: duckdb.DuckDBPyConnection, schema: str) -> set[str]:
    rows = con.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = ? AND table_name = '_dlt_loads'
        """,
        [schema],
    ).fetchall()
    return {r[0] for r in rows}


_DLT_INTERNAL_TABLES = {"_dlt_loads", "_dlt_pipeline_state", "_dlt_version"}


def _dlt_user_tables(con: duckdb.DuckDBPyConnection, schema: str) -> list[str]:
    rows = con.execute(
        """
        SELECT DISTINCT table_name
        FROM information_schema.columns
        WHERE table_schema = ?
          AND column_name = '_dlt_load_id'
        ORDER BY table_name
        """,
        [schema],
    ).fetchall()
    return [
        r[0]
        for r in rows
        if r[0] not in _DLT_INTERNAL_TABLES
        and "__" not in r[0]
        and not r[0].startswith("_")
    ]


def capture_dlt(metadata_db: Path, raw_db: Path) -> int:
    """Mirror new dlt loads from raw_db into metadata.duckdb.

    Reads every schema's ``_dlt_loads`` table plus per-table
    ``_dlt_load_id`` row counts and inserts them into the metadata DB
    using ``ON CONFLICT DO NOTHING`` — safe to call repeatedly; only
    new loads produce new rows.

    Implementation note (issue #24): we ATTACH ``raw_db`` from
    ``meta_con`` rather than opening a second python-level connection,
    because DuckDB rejects intra-process opens of the same file with
    mismatched config — and capture typically runs immediately after a
    ``dlt.pipeline.run`` whose destination connection is still alive
    with whatever config dlt picked. ATTACH coexists fine with that
    open handle.

    Returns the number of newly-captured load entries.
    """
    if not raw_db.exists():
        return 0

    ensure_schema(metadata_db)

    meta_con = duckdb.connect(str(metadata_db))
    raw_alias = "_tycoon_raw_capture"
    new_loads = 0

    def q(name: str) -> str:
        # Quote a SQL identifier; capture handles arbitrary user-named
        # schemas/tables coming back from information_schema.
        return '"' + name.replace('"', '""') + '"'

    try:
        meta_con.execute(f"ATTACH '{raw_db}' AS {q(raw_alias)} (READ_ONLY)")
        try:
            captured_at = datetime.now(tz=timezone.utc)

            schema_rows = meta_con.execute(
                """
                SELECT DISTINCT table_schema
                FROM information_schema.tables
                WHERE table_catalog = ? AND table_name = '_dlt_loads'
                ORDER BY table_schema
                """,
                [raw_alias],
            ).fetchall()
            schemas = [r[0] for r in schema_rows]

            for schema in schemas:
                col_rows = meta_con.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_catalog = ?
                      AND table_schema = ?
                      AND table_name = '_dlt_loads'
                    """,
                    [raw_alias, schema],
                ).fetchall()
                cols = {r[0] for r in col_rows}
                svh_expr = (
                    '"schema_version_hash"'
                    if "schema_version_hash" in cols
                    else "NULL"
                )

                loads = meta_con.execute(
                    f"""
                    SELECT
                        load_id,
                        status,
                        inserted_at,
                        {svh_expr} AS schema_version_hash
                    FROM {q(raw_alias)}.{q(schema)}.{q("_dlt_loads")}
                    """
                ).fetchall()

                for load_id, status, inserted_at, svh in loads:
                    meta_con.execute(
                        """
                        INSERT INTO dlt_runs
                          (source_schema, load_id, status, inserted_at,
                           schema_version_hash, captured_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT DO NOTHING
                        """,
                        [schema, load_id, status, inserted_at, svh, captured_at],
                    )
                    new_loads += 1

                # Per-table row counts. Filter to user-named tables
                # (skip dlt internals + nested-table mangled names).
                table_rows = meta_con.execute(
                    """
                    SELECT DISTINCT table_name
                    FROM information_schema.columns
                    WHERE table_catalog = ?
                      AND table_schema = ?
                      AND column_name = '_dlt_load_id'
                    ORDER BY table_name
                    """,
                    [raw_alias, schema],
                ).fetchall()
                user_tables = [
                    r[0]
                    for r in table_rows
                    if r[0] not in _DLT_INTERNAL_TABLES
                    and "__" not in r[0]
                    and not r[0].startswith("_")
                ]

                for table in user_tables:
                    per_load = meta_con.execute(
                        f"""
                        SELECT _dlt_load_id, COUNT(*) AS rows_loaded
                        FROM {q(raw_alias)}.{q(schema)}.{q(table)}
                        WHERE _dlt_load_id IS NOT NULL
                        GROUP BY _dlt_load_id
                        """
                    ).fetchall()
                    for load_id, rows_loaded in per_load:
                        meta_con.execute(
                            """
                            INSERT INTO dlt_rows_by_table
                              (source_schema, table_name, load_id,
                               rows_loaded, captured_at)
                            VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT DO NOTHING
                            """,
                            [schema, table, load_id, rows_loaded, captured_at],
                        )

            return new_loads
        finally:
            meta_con.execute(f"DETACH {q(raw_alias)}")
    finally:
        meta_con.close()


# ---------------------------------------------------------------------------
# dbt capture
# ---------------------------------------------------------------------------


def _parse_run_results_timestamp(ts: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp from dbt's run_results.json."""
    if not ts:
        return None
    try:
        cleaned = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def _resource_type_from_unique_id(unique_id: str) -> str:
    """dbt unique_id is '<resource_type>.<project>.<name>'. Return resource_type."""
    return unique_id.split(".", 1)[0] if "." in unique_id else ""


def _earliest_started_at(results: list[dict]) -> datetime | None:
    """Find the earliest 'started_at' across every node's timing list."""
    earliest: datetime | None = None
    for res in results:
        for timing in res.get("timing", []) or []:
            ts = _parse_run_results_timestamp(timing.get("started_at"))
            if ts is None:
                continue
            if earliest is None or ts < earliest:
                earliest = ts
    return earliest


def _timing_duration(result: dict, name: str) -> float | None:
    """Return the duration in seconds of a named timing ('compile' / 'execute')."""
    for t in result.get("timing", []) or []:
        if t.get("name") != name:
            continue
        started = _parse_run_results_timestamp(t.get("started_at"))
        completed = _parse_run_results_timestamp(t.get("completed_at"))
        if started and completed:
            return (completed - started).total_seconds()
    return None


def capture_dbt(
    metadata_db: Path,
    dbt_project_dir: Path,
    command: str | None = None,
) -> str | None:
    """Parse run_results.json and insert one invocation + one row per node.

    Returns the invocation_id on successful capture, or None if
    run_results.json is missing / malformed / duplicate.
    """
    results_path = dbt_project_dir / "target" / "run_results.json"
    if not results_path.exists():
        return None

    try:
        data = json.loads(results_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None

    metadata = data.get("metadata", {}) or {}
    args = data.get("args", {}) or {}
    results = data.get("results", []) or []

    invocation_id = metadata.get("invocation_id")
    if not invocation_id:
        return None

    dbt_version = metadata.get("dbt_version")
    target_name = args.get("target")
    cmd = command or args.get("which") or args.get("rpc_method") or "unknown"
    success = data.get("success")
    elapsed = data.get("elapsed_time")
    started_at = _earliest_started_at(results) or _parse_run_results_timestamp(
        metadata.get("generated_at")
    )

    models_ok = models_error = tests_passed = tests_failed = 0
    for res in results:
        status = (res.get("status") or "").lower()
        resource_type = _resource_type_from_unique_id(res.get("unique_id", ""))
        if resource_type == "model":
            if status == "success":
                models_ok += 1
            elif status == "error":
                models_error += 1
        elif resource_type == "test":
            if status == "pass":
                tests_passed += 1
            elif status in ("fail", "error", "warn"):
                tests_failed += 1

    ensure_schema(metadata_db)
    captured_at = datetime.now(tz=timezone.utc)

    con = duckdb.connect(str(metadata_db))
    try:
        pre = con.execute(
            "SELECT 1 FROM dbt_runs WHERE invocation_id = ?", [invocation_id]
        ).fetchone()
        if pre is not None:
            return None  # already captured

        con.execute(
            """
            INSERT INTO dbt_runs
              (invocation_id, command, started_at, elapsed_s, success,
               models_ok, models_error, tests_passed, tests_failed,
               dbt_version, target_name, captured_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                invocation_id,
                cmd,
                started_at,
                elapsed,
                success,
                models_ok,
                models_error,
                tests_passed,
                tests_failed,
                dbt_version,
                target_name,
                captured_at,
            ],
        )

        for res in results:
            unique_id = res.get("unique_id", "")
            adapter = res.get("adapter_response") or {}
            rows_affected = adapter.get("rows_affected")
            con.execute(
                """
                INSERT INTO dbt_nodes
                  (invocation_id, node_name, resource_type, status,
                   execution_time_s, rows_affected, compile_time_s, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING
                """,
                [
                    invocation_id,
                    unique_id,
                    _resource_type_from_unique_id(unique_id),
                    res.get("status"),
                    res.get("execution_time"),
                    rows_affected,
                    _timing_duration(res, "compile"),
                    res.get("message"),
                ],
            )

        return invocation_id
    finally:
        con.close()


# ---------------------------------------------------------------------------
# dlt trace capture (trace.pickle → dlt_trace_runs / _steps / _jobs)
# ---------------------------------------------------------------------------


def _trace_pickle_path(pipeline_name: str, pipelines_dir: Path | None = None) -> Path:
    """Return the canonical trace.pickle path for a dlt pipeline."""
    base = pipelines_dir if pipelines_dir is not None else Path.home() / ".dlt" / "pipelines"
    return base / pipeline_name / "trace.pickle"


def _load_trace_dict(pipeline_name: str, pipelines_dir: Path | None = None) -> dict | None:
    """Unpickle trace.pickle and normalize to the asdict() form.

    dlt serializes ``PipelineTrace`` objects to ``trace.pickle`` — we convert
    to a plain dict so the rest of the pipeline operates on simple types and
    tests can construct synthetic inputs without importing dlt internals.
    """
    import pickle

    path = _trace_pickle_path(pipeline_name, pipelines_dir)
    if not path.exists():
        return None
    try:
        with path.open("rb") as f:
            obj = pickle.load(f)
    except (OSError, pickle.UnpicklingError, EOFError, AttributeError):
        return None

    to_dict = getattr(obj, "asdict", None)
    if callable(to_dict):
        try:
            return to_dict()
        except Exception:
            return None
    return obj if isinstance(obj, dict) else None


def _coerce_ts(value) -> datetime | None:
    """Trace timestamps arrive as either datetime objects or ISO strings."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _duration_s(start, finish) -> float | None:
    s = _coerce_ts(start)
    f = _coerce_ts(finish)
    if s is None or f is None:
        return None
    return (f - s).total_seconds()


def _derive_success_and_exception(steps: list[dict]) -> tuple[bool, str | None]:
    """A trace is successful when no step raised. First exception wins."""
    first_exc: str | None = None
    for step in steps:
        exc = step.get("step_exception")
        if exc:
            # dlt stores exceptions as strings already; truncate defensively
            first_exc = str(exc)[:2000]
            break
    return (first_exc is None), first_exc


def capture_dlt_trace_from_dict(metadata_db: Path, trace: dict) -> str | None:
    """Insert one dlt trace (as returned by ``PipelineTrace.asdict()``).

    Idempotent: re-calling with the same ``transaction_id`` is a no-op.
    Returns the transaction_id on capture, None on skip.
    """
    transaction_id = trace.get("transaction_id")
    if not transaction_id:
        return None

    ensure_schema(metadata_db)
    con = duckdb.connect(str(metadata_db))
    try:
        pre = con.execute(
            "SELECT 1 FROM dlt_trace_runs WHERE transaction_id = ?",
            [transaction_id],
        ).fetchone()
        if pre is not None:
            return None

        steps = trace.get("steps") or []
        started = _coerce_ts(trace.get("started_at"))
        finished = _coerce_ts(trace.get("finished_at"))
        duration = _duration_s(trace.get("started_at"), trace.get("finished_at"))
        success, exception = _derive_success_and_exception(steps)
        captured_at = datetime.now(tz=timezone.utc)

        con.execute(
            """
            INSERT INTO dlt_trace_runs
              (transaction_id, pipeline_name, started_at, finished_at,
               duration_s, engine_version, success, exception, captured_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                transaction_id,
                trace.get("pipeline_name"),
                started,
                finished,
                duration,
                trace.get("engine_version"),
                success,
                exception,
                captured_at,
            ],
        )

        for step in steps:
            step_name = step.get("step") or "unknown"
            con.execute(
                """
                INSERT INTO dlt_trace_steps
                  (transaction_id, step, started_at, finished_at,
                   duration_s, step_exception)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING
                """,
                [
                    transaction_id,
                    step_name,
                    _coerce_ts(step.get("started_at")),
                    _coerce_ts(step.get("finished_at")),
                    _duration_s(step.get("started_at"), step.get("finished_at")),
                    (str(step.get("step_exception"))[:2000]
                     if step.get("step_exception") else None),
                ],
            )

            if step_name not in ("load", "run"):
                continue
            step_info = step.get("step_info") or {}
            packages = step_info.get("load_packages") or []
            for pkg in packages:
                load_id = pkg.get("load_id")
                if not load_id:
                    continue
                for job in pkg.get("jobs") or []:
                    job_id = job.get("job_id") or job.get("file_id")
                    if not job_id:
                        continue
                    con.execute(
                        """
                        INSERT INTO dlt_trace_jobs
                          (transaction_id, load_id, job_id, table_name,
                           file_format, state, file_size_bytes, elapsed_s,
                           failed_message, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT DO NOTHING
                        """,
                        [
                            transaction_id,
                            load_id,
                            job_id,
                            job.get("table_name"),
                            job.get("file_format"),
                            job.get("state"),
                            job.get("file_size"),
                            job.get("elapsed"),
                            job.get("failed_message"),
                            _coerce_ts(job.get("created_at")),
                        ],
                    )

        return transaction_id
    finally:
        con.close()


def capture_dlt_trace(
    metadata_db: Path,
    pipeline_name: str,
    pipelines_dir: Path | None = None,
) -> str | None:
    """Load ``~/.dlt/pipelines/<name>/trace.pickle`` and capture it.

    Returns the transaction_id on capture, None if the trace is missing or
    already present in the metadata DB.
    """
    trace = _load_trace_dict(pipeline_name, pipelines_dir)
    if trace is None:
        return None
    return capture_dlt_trace_from_dict(metadata_db, trace)


# ---------------------------------------------------------------------------
# dbt manifest capture (manifest.json → fingerprint + schema diff)
# ---------------------------------------------------------------------------

_FINGERPRINTED_RESOURCE_TYPES = {"model", "seed", "snapshot"}

# DuckDB PRIMARY KEY columns must be NOT NULL. Use an empty string as a
# sentinel for change rows whose natural column_name is N/A (model-level
# changes like model_added / model_removed / sql_changed).
_NO_COLUMN_SENTINEL = ""


def _extract_manifest_fingerprint(manifest: dict) -> dict[str, dict]:
    """Reduce a dbt manifest to the minimum needed for a schema diff.

    Returns ``{unique_id: {checksum, resource_type, columns: {name: type}}}``.
    Non-model/seed/snapshot nodes are dropped to keep the fingerprint small.
    """
    nodes = manifest.get("nodes") or {}
    out: dict[str, dict] = {}
    for unique_id, node in nodes.items():
        if not isinstance(node, dict):
            continue
        resource_type = node.get("resource_type")
        if resource_type not in _FINGERPRINTED_RESOURCE_TYPES:
            continue
        checksum_val = ""
        checksum_obj = node.get("checksum") or {}
        if isinstance(checksum_obj, dict):
            checksum_val = checksum_obj.get("checksum") or ""
        columns_raw = node.get("columns") or {}
        columns: dict[str, str] = {}
        if isinstance(columns_raw, dict):
            for col_name, col in columns_raw.items():
                if isinstance(col, dict):
                    columns[col_name] = col.get("data_type") or ""
                else:
                    columns[col_name] = ""
        out[unique_id] = {
            "resource_type": resource_type,
            "checksum": checksum_val,
            "columns": columns,
        }
    return out


def _diff_fingerprints(
    prev: dict[str, dict] | None,
    curr: dict[str, dict],
) -> list[dict]:
    """Return a list of change records between two fingerprints.

    Each record is a flat dict with keys ``change_type``, ``unique_id``,
    ``column_name`` (or ''), ``old_value`` / ``new_value`` (or None).
    Returns an empty list when ``prev`` is None (first capture has nothing
    to diff against).
    """
    if prev is None:
        return []

    changes: list[dict] = []
    prev_ids = set(prev)
    curr_ids = set(curr)

    for uid in sorted(curr_ids - prev_ids):
        changes.append(
            {
                "change_type": "model_added",
                "unique_id": uid,
                "column_name": _NO_COLUMN_SENTINEL,
                "old_value": None,
                "new_value": curr[uid].get("resource_type"),
            }
        )
    for uid in sorted(prev_ids - curr_ids):
        changes.append(
            {
                "change_type": "model_removed",
                "unique_id": uid,
                "column_name": _NO_COLUMN_SENTINEL,
                "old_value": prev[uid].get("resource_type"),
                "new_value": None,
            }
        )

    for uid in sorted(prev_ids & curr_ids):
        p = prev[uid]
        c = curr[uid]
        p_sum = p.get("checksum") or ""
        c_sum = c.get("checksum") or ""
        if p_sum != c_sum:
            changes.append(
                {
                    "change_type": "sql_changed",
                    "unique_id": uid,
                    "column_name": _NO_COLUMN_SENTINEL,
                    "old_value": p_sum[:64] or None,
                    "new_value": c_sum[:64] or None,
                }
            )

        p_cols = p.get("columns") or {}
        c_cols = c.get("columns") or {}
        p_col_set = set(p_cols)
        c_col_set = set(c_cols)
        for col in sorted(c_col_set - p_col_set):
            changes.append(
                {
                    "change_type": "column_added",
                    "unique_id": uid,
                    "column_name": col,
                    "old_value": None,
                    "new_value": c_cols[col] or None,
                }
            )
        for col in sorted(p_col_set - c_col_set):
            changes.append(
                {
                    "change_type": "column_removed",
                    "unique_id": uid,
                    "column_name": col,
                    "old_value": p_cols[col] or None,
                    "new_value": None,
                }
            )
        for col in sorted(p_col_set & c_col_set):
            if p_cols[col] != c_cols[col]:
                changes.append(
                    {
                        "change_type": "column_type_changed",
                        "unique_id": uid,
                        "column_name": col,
                        "old_value": p_cols[col] or None,
                        "new_value": c_cols[col] or None,
                    }
                )

    return changes


def _load_previous_fingerprint(
    con: duckdb.DuckDBPyConnection,
    exclude_invocation_id: str,
) -> tuple[str | None, dict[str, dict] | None]:
    """Return (prev_invocation_id, fingerprint) of the most recent snapshot."""
    row = con.execute(
        """
        SELECT invocation_id, fingerprint_json
        FROM dbt_manifest_snapshots
        WHERE invocation_id <> ?
        ORDER BY COALESCE(generated_at, captured_at) DESC
        LIMIT 1
        """,
        [exclude_invocation_id],
    ).fetchone()
    if row is None:
        return None, None
    prev_id, fp_json = row
    if not fp_json:
        return prev_id, None
    try:
        return prev_id, json.loads(fp_json)
    except (json.JSONDecodeError, TypeError):
        return prev_id, None


def capture_dbt_manifest(
    metadata_db: Path,
    dbt_project_dir: Path,
) -> tuple[str, int] | None:
    """Snapshot ``target/manifest.json`` and write its diff vs. the previous
    snapshot into ``dbt_schema_changes``.

    Returns ``(invocation_id, changes_recorded)`` on capture, or None when
    the manifest is missing / malformed / already snapshotted.
    """
    manifest_path = dbt_project_dir / "target" / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None

    metadata = manifest.get("metadata") or {}
    invocation_id = metadata.get("invocation_id")
    if not invocation_id:
        return None

    fingerprint = _extract_manifest_fingerprint(manifest)
    ensure_schema(metadata_db)
    captured_at = datetime.now(tz=timezone.utc)
    generated_at = _parse_run_results_timestamp(metadata.get("generated_at"))
    dbt_schema_version = metadata.get("dbt_schema_version")

    con = duckdb.connect(str(metadata_db))
    try:
        pre = con.execute(
            "SELECT 1 FROM dbt_manifest_snapshots WHERE invocation_id = ?",
            [invocation_id],
        ).fetchone()
        if pre is not None:
            return None

        prev_invocation_id, prev_fingerprint = _load_previous_fingerprint(
            con, exclude_invocation_id=invocation_id
        )
        changes = _diff_fingerprints(prev_fingerprint, fingerprint)

        con.execute(
            """
            INSERT INTO dbt_manifest_snapshots
              (invocation_id, generated_at, dbt_schema_version,
               fingerprint_json, captured_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                invocation_id,
                generated_at,
                dbt_schema_version,
                json.dumps(fingerprint, sort_keys=True),
                captured_at,
            ],
        )

        for change in changes:
            con.execute(
                """
                INSERT INTO dbt_schema_changes
                  (invocation_id, prev_invocation_id, change_type, unique_id,
                   column_name, old_value, new_value, captured_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT DO NOTHING
                """,
                [
                    invocation_id,
                    prev_invocation_id,
                    change["change_type"],
                    change["unique_id"],
                    change["column_name"],
                    change["old_value"],
                    change["new_value"],
                    captured_at,
                ],
            )

        return invocation_id, len(changes)
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
            con.execute(
                f"COPY (SELECT * FROM {table}) TO '{path}' (FORMAT PARQUET)"
            )
            out[table] = path
        return out
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Best-effort wrappers for call sites that must never raise
# ---------------------------------------------------------------------------


def capture_dlt_safe(metadata_db: Path, raw_db: Path) -> None:
    """Best-effort wrapper around capture_dlt; swallows all exceptions."""
    try:
        capture_dlt(metadata_db, raw_db)
    except Exception:
        pass


def capture_dbt_safe(
    metadata_db: Path,
    dbt_project_dir: Path,
    command: str | None = None,
) -> None:
    """Best-effort wrapper around capture_dbt; swallows all exceptions."""
    try:
        capture_dbt(metadata_db, dbt_project_dir, command)
    except Exception:
        pass


def capture_dlt_trace_safe(
    metadata_db: Path,
    pipeline_name: str | None,
    pipelines_dir: Path | None = None,
) -> None:
    """Best-effort wrapper around capture_dlt_trace; swallows all exceptions.

    A ``None`` pipeline_name is a no-op — the runner may not always know the
    pipeline name (legacy paths) and we'd rather skip the enrichment than
    crash the ingest.
    """
    if not pipeline_name:
        return
    try:
        capture_dlt_trace(metadata_db, pipeline_name, pipelines_dir)
    except Exception:
        pass


def capture_dbt_manifest_safe(
    metadata_db: Path,
    dbt_project_dir: Path,
) -> None:
    """Best-effort wrapper around capture_dbt_manifest; swallows all exceptions."""
    try:
        capture_dbt_manifest(metadata_db, dbt_project_dir)
    except Exception:
        pass


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
