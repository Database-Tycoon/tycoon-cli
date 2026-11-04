"""Mirror dlt load history and run traces into the metadata DuckDB."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import duckdb

from tycoon.observability.store import ensure_schema

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
    return [r[0] for r in rows if r[0] not in _DLT_INTERNAL_TABLES and "__" not in r[0] and not r[0].startswith("_")]


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
            captured_at = datetime.now(tz=UTC)

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
                svh_expr = '"schema_version_hash"' if "schema_version_hash" in cols else "NULL"

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
                    if r[0] not in _DLT_INTERNAL_TABLES and "__" not in r[0] and not r[0].startswith("_")
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
        captured_at = datetime.now(tz=UTC)

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
                    (str(step.get("step_exception"))[:2000] if step.get("step_exception") else None),
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
# Best-effort wrappers for call sites that must never raise
# ---------------------------------------------------------------------------


def capture_dlt_safe(metadata_db: Path, raw_db: Path) -> None:
    """Best-effort wrapper around capture_dlt; swallows all exceptions."""
    try:
        capture_dlt(metadata_db, raw_db)
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
