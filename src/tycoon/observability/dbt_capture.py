"""Record dbt invocations and manifest fingerprints in the metadata DuckDB."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from tycoon.observability.store import ensure_schema

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
    started_at = _earliest_started_at(results) or _parse_run_results_timestamp(metadata.get("generated_at"))

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
    captured_at = datetime.now(tz=UTC)

    con = duckdb.connect(str(metadata_db))
    try:
        pre = con.execute("SELECT 1 FROM dbt_runs WHERE invocation_id = ?", [invocation_id]).fetchone()
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
    captured_at = datetime.now(tz=UTC)
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

        prev_invocation_id, prev_fingerprint = _load_previous_fingerprint(con, exclude_invocation_id=invocation_id)
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
# Best-effort wrappers for call sites that must never raise
# ---------------------------------------------------------------------------


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


def capture_dbt_manifest_safe(
    metadata_db: Path,
    dbt_project_dir: Path,
) -> None:
    """Best-effort wrapper around capture_dbt_manifest; swallows all exceptions."""
    try:
        capture_dbt_manifest(metadata_db, dbt_project_dir)
    except Exception:
        pass
