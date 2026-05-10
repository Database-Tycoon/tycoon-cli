"""Mirror Fivetran connector metadata into ``.tycoon/metadata.duckdb``.

When ``stack.ingestion = fivetran``, ``tycoon data fivetran sync`` calls
this. Each invocation writes one row per connector keyed on
``(connector_id, captured_at)`` so history accumulates over time —
``tycoon data history`` and ``tycoon data status`` read off the same
table.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from pathlib import Path

import duckdb

from tycoon.ingestion.fivetran_client import FivetranClient
from tycoon.observability import ensure_schema


@dataclass(frozen=True)
class SyncResult:
    captured_at: datetime.datetime
    connectors_seen: int
    paused: int
    healthy: int   # had a recent succeeded_at
    failing: int   # last touch was a failure
    new: int       # connectors not seen in any prior snapshot


def sync_fivetran_metadata(
    client: FivetranClient,
    metadata_db: Path,
) -> SyncResult:
    """Pull every connector and write one snapshot row each.

    Idempotent within a captured_at second — re-runs in the same second
    would attempt to insert duplicate PKs; we use INSERT OR REPLACE to
    keep the call safely retryable in tight loops.
    """
    ensure_schema(metadata_db)
    captured_at = datetime.datetime.now(tz=datetime.timezone.utc)
    connectors = client.list_connectors()

    healthy = paused = failing = new = 0

    con = duckdb.connect(str(metadata_db))
    try:
        prior_ids = {
            row[0]
            for row in con.execute(
                "SELECT DISTINCT connector_id FROM fivetran_connectors"
            ).fetchall()
        }
        for c in connectors:
            if c.connector_id not in prior_ids:
                new += 1
            if c.paused:
                paused += 1
            if c.succeeded_at and (
                not c.failed_at or c.succeeded_at > c.failed_at
            ):
                healthy += 1
            elif c.failed_at:
                failing += 1
            con.execute(
                "INSERT OR REPLACE INTO fivetran_connectors "
                "(connector_id, name, service, schema_name, paused, sync_state, "
                " setup_state, update_state, succeeded_at, failed_at, captured_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    c.connector_id,
                    c.name,
                    c.service,
                    c.schema_name,
                    c.paused,
                    c.sync_state,
                    c.setup_state,
                    c.update_state,
                    c.succeeded_at,
                    c.failed_at,
                    captured_at,
                ],
            )
    finally:
        con.close()

    return SyncResult(
        captured_at=captured_at,
        connectors_seen=len(connectors),
        paused=paused,
        healthy=healthy,
        failing=failing,
        new=new,
    )


def latest_connector_snapshot(metadata_db: Path) -> list[dict]:
    """Return the latest captured row per connector (used by data status).

    Empty list if the table doesn't exist or has no rows. Read-only —
    safe to call from any command without side effects.
    """
    if not metadata_db.exists():
        return []
    con = duckdb.connect(str(metadata_db), read_only=True)
    try:
        names = {
            row[0]
            for row in con.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main'"
            ).fetchall()
        }
        if "fivetran_connectors" not in names:
            return []
        rows = con.execute(
            "WITH latest AS ("
            "  SELECT connector_id, MAX(captured_at) AS captured_at "
            "  FROM fivetran_connectors GROUP BY connector_id"
            ") "
            "SELECT c.* FROM fivetran_connectors c "
            "JOIN latest l USING (connector_id, captured_at) "
            "ORDER BY c.name"
        ).fetchall()
        cols = [d[0] for d in con.description]
    finally:
        con.close()
    return [dict(zip(cols, r)) for r in rows]


def freshness_label(
    succeeded_at: datetime.datetime | None,
    failed_at: datetime.datetime | None,
    paused: bool,
) -> tuple[str, str]:
    """Return ``(label, rich_style)`` summarizing a connector's state.

    Mirrors the dlt-side freshness convention used by ``tycoon data
    status`` so the rendered tables look consistent across ingestion
    backends.
    """
    if paused:
        return "paused", "dim"
    last = _most_recent(succeeded_at, failed_at)
    if last is None:
        return "never", "red"

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    if last.tzinfo is None:
        last = last.replace(tzinfo=datetime.timezone.utc)
    age = now - last
    hours = age.total_seconds() / 3600
    style = (
        "green" if hours < 24 else
        "yellow" if hours < 24 * 7 else
        "red"
    )
    if hours < 1:
        label = f"{int(age.total_seconds() / 60)}m ago"
    elif hours < 24:
        label = f"{int(hours)}h ago"
    else:
        label = f"{int(hours / 24)}d ago"

    if failed_at and (not succeeded_at or failed_at > succeeded_at):
        return f"{label} (failed)", "red"
    return label, style


def _most_recent(*dates: datetime.datetime | None) -> datetime.datetime | None:
    candidates = [d for d in dates if d is not None]
    return max(candidates) if candidates else None
