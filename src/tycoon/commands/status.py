"""tycoon data status — show health of each registered data source."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional

import duckdb
import typer
from rich.table import Table

from tycoon.config import config
from tycoon.utils.console import console, error, header, info


def _query_last_sync(raw_db: Path, schema: str) -> Optional[datetime.datetime]:
    """Return the timestamp of the last successful dlt load for a schema."""
    try:
        con = duckdb.connect(str(raw_db), read_only=True)
        row = con.execute(
            f"SELECT max(inserted_at) FROM {schema}._dlt_loads WHERE status = 0"
        ).fetchone()
        con.close()
        if row and row[0]:
            val = row[0]
            if isinstance(val, datetime.datetime):
                return val
            return datetime.datetime.fromisoformat(str(val))
    except Exception:
        pass
    return None


def _query_row_counts(raw_db: Path, schema: str) -> dict[str, int]:
    """Return {table: row_count} for all user tables in a schema."""
    counts: dict[str, int] = {}
    try:
        con = duckdb.connect(str(raw_db), read_only=True)
        tables = con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = ? AND table_name NOT LIKE '_dlt_%'",
            [schema],
        ).fetchall()
        for (table,) in tables:
            row = con.execute(f'SELECT count(*) FROM "{schema}"."{table}"').fetchone()
            counts[table] = row[0] if row else 0
        con.close()
    except Exception:
        pass
    return counts


def _freshness_label(last_sync: Optional[datetime.datetime]) -> tuple[str, str]:
    """Return (label, style) describing how fresh a sync is."""
    if last_sync is None:
        return "never", "red"

    # Make both timezone-naive for comparison
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    if last_sync.tzinfo is None:
        last_sync = last_sync.replace(tzinfo=datetime.timezone.utc)

    age = now - last_sync
    hours = age.total_seconds() / 3600

    if hours < 24:
        if hours < 1:
            mins = int(age.total_seconds() / 60)
            return f"{mins}m ago", "green"
        return f"{int(hours)}h ago", "green"
    if hours < 24 * 7:
        return f"{int(hours / 24)}d ago", "yellow"
    return f"{int(hours / 24)}d ago", "red"


def status_cmd() -> None:
    """Show freshness, last sync time, and row counts for each registered source."""
    if not config.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    sources = config.sources
    if not sources:
        info("No sources registered. Run [bold]tycoon data sources add[/bold] first.")
        return

    header("Data Status")

    raw_db = config.raw_db
    db_exists = raw_db.exists()

    table = Table(show_lines=True)
    table.add_column("Source", style="bold cyan")
    table.add_column("Type", style="dim")
    table.add_column("Last Sync")
    table.add_column("Freshness")
    table.add_column("Tables")
    table.add_column("Rows", justify="right")

    for name, src in sources.items():
        schema = src.schema_name

        if not db_exists:
            table.add_row(name, src.type, "—", "[red]never[/red]", "—", "—")
            continue

        last_sync = _query_last_sync(raw_db, schema)
        row_counts = _query_row_counts(raw_db, schema)

        sync_str = last_sync.strftime("%Y-%m-%d %H:%M") if last_sync else "—"
        fresh_label, fresh_style = _freshness_label(last_sync)
        tables_str = str(len(row_counts)) if row_counts else "—"
        total_rows = f"{sum(row_counts.values()):,}" if row_counts else "—"

        table.add_row(
            name,
            src.type,
            sync_str,
            f"[{fresh_style}]{fresh_label}[/{fresh_style}]",
            tables_str,
            total_rows,
        )

    console.print(table)
