"""Questions the layer views ask of the dbt run ledger."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from pathlib import Path

import duckdb


@dataclass(frozen=True)
class ModelBuild:
    """One model's standing in the ledger."""

    latest_status: str  # dbt's word for the node in the newest run that included it
    last_success: datetime.datetime | None  # start of the newest run where it built


def model_builds(metadata_db: Path, unique_ids: list[str]) -> dict[str, ModelBuild]:
    """Per model: its status in its newest run, and when it last built successfully.

    Models the ledger has never seen are absent from the result.

    ``dbt_nodes.node_name`` holds the dbt ``unique_id`` (``model.<project>.<name>``),
    so callers pass unique ids rather than bare model names: a bare name never
    matches, and every layer reads "never" after a green build (gh-390).

    ``capture_dbt`` writes a UTC-aware datetime into the naive ``started_at``
    column, which DuckDB stores as wall-clock time in its session time zone.
    Casting back to TIMESTAMPTZ in the same session recovers the real instant;
    reading the naive value as UTC would skew the age by the local UTC offset.
    """
    if not unique_ids or not metadata_db.exists():
        return {}
    try:
        with duckdb.connect(str(metadata_db), read_only=True) as con:
            rows = con.execute(
                "SELECT n.node_name, "
                "  arg_max(n.status, r.started_at), "
                "  (MAX(r.started_at) FILTER (WHERE n.status = 'success'))::TIMESTAMPTZ "
                "FROM dbt_runs r "
                "JOIN dbt_nodes n ON n.invocation_id = r.invocation_id "
                "WHERE list_contains(?, n.node_name) "
                "GROUP BY n.node_name",
                [unique_ids],
            ).fetchall()
    except Exception:
        return {}
    return {name: ModelBuild(latest_status=status or "", last_success=success) for name, status, success in rows}
