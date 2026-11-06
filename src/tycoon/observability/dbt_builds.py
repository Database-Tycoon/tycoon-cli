"""Questions the layer views ask of the dbt run ledger."""

from __future__ import annotations

import datetime
from pathlib import Path

import duckdb


def latest_successful_build(metadata_db: Path, unique_ids: list[str]) -> datetime.datetime | None:
    """Start time of the newest run in which any node in ``unique_ids`` built successfully.

    ``dbt_nodes.node_name`` holds the dbt ``unique_id`` (``model.<project>.<name>``),
    so callers pass unique ids rather than bare model names: a bare name never
    matches, and every layer reads "last build never" after a green build (gh-390).

    ``capture_dbt`` writes a UTC-aware datetime into the naive ``started_at``
    column, which DuckDB stores as wall-clock time in its session time zone.
    Casting back to TIMESTAMPTZ in the same session recovers the real instant;
    reading the naive value as UTC would skew the age by the local UTC offset.
    """
    if not unique_ids or not metadata_db.exists():
        return None
    try:
        with duckdb.connect(str(metadata_db), read_only=True) as con:
            row = con.execute(
                "SELECT MAX(r.started_at)::TIMESTAMPTZ "
                "FROM dbt_runs r "
                "JOIN dbt_nodes n ON n.invocation_id = r.invocation_id "
                "WHERE n.status = 'success' AND list_contains(?, n.node_name)",
                [unique_ids],
            ).fetchone()
    except Exception:
        return None
    return row[0] if row else None
