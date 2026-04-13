"""tycoon db — database inspection, querying, and cleanup."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import duckdb
import typer
from rich.table import Table

from tycoon.config import config
from tycoon.utils.console import console, header, info, success, error, warn, status_table
from tycoon.utils.duckdb_utils import db_file_size_mb, get_tables, get_row_count

app = typer.Typer(
    help="Database inspection, querying, and cleanup.",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------


@app.command()
def stats() -> None:
    """Show database file sizes, table counts, and row counts."""
    header("Database Statistics")

    rows: list[tuple[str, str, str]] = []

    for db_path, label in [(config.raw_db, "Raw"), (config.local_db, "Local")]:
        size = db_file_size_mb(db_path)
        if size is not None:
            rows.append((f"{label} database", "OK", f"{size:.1f} MB"))
            tables = get_tables(db_path)
            rows.append((f"  Tables", "", f"{len(tables)}"))
            for schema, table in tables:
                count = get_row_count(db_path, schema, table)
                rows.append((
                    f"  {schema}.{table}",
                    "",
                    f"{count:,} rows" if count is not None else "empty",
                ))
        else:
            rows.append((f"{label} database", "WARN", "not found"))

    console.print(status_table(rows, title="Database Statistics"))


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------


@app.command()
def query(
    sql: Annotated[str, typer.Argument(help="SQL query to execute.")],
    raw: Annotated[
        bool,
        typer.Option("--raw", help="Query the raw database instead of local."),
    ] = False,
) -> None:
    """Run a read-only SQL query against the local (or raw) database."""
    db_path = config.raw_db if raw else config.local_db
    label = "raw" if raw else "local"

    if not db_path.exists():
        error(f"The {label} database does not exist at {db_path}")
        raise typer.Exit(1)

    try:
        con = duckdb.connect(str(db_path), read_only=True)
        result = con.execute(sql)
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()
        con.close()
    except duckdb.Error as exc:
        error(f"Query failed: {exc}")
        raise typer.Exit(1) from exc

    # Build Rich table
    table = Table(title=f"Query Results ({label} db)", show_lines=True)
    for col in columns:
        table.add_column(col, style="cyan")
    for row in rows:
        table.add_row(*(str(v) for v in row))

    console.print(table)
    info(f"{len(rows)} row(s) returned")


# ---------------------------------------------------------------------------
# clean
# ---------------------------------------------------------------------------


@app.command()
def clean(
    raw: Annotated[
        bool,
        typer.Option("--raw", help="Remove the raw database and its WAL file."),
    ] = False,
    local: Annotated[
        bool,
        typer.Option("--local", help="Remove the local database and its WAL file."),
    ] = False,
    all_: Annotated[
        bool,
        typer.Option("--all", help="Remove both databases and clean up data directory."),
    ] = False,
) -> None:
    """Remove database files (with confirmation)."""
    if not (raw or local or all_):
        error("Specify at least one of --raw, --local, or --all.")
        raise typer.Exit(1)

    targets: list[tuple[Path, str]] = []

    if raw or all_:
        targets.append((config.raw_db, "raw database"))
    if local or all_:
        targets.append((config.local_db, "local database"))

    # Show what will be deleted
    header("Database Cleanup")
    for path, label in targets:
        wal_path = path.with_suffix(".duckdb.wal")
        exists = path.exists()
        wal_exists = wal_path.exists()
        if exists or wal_exists:
            size = db_file_size_mb(path)
            info(f"{label}: {size:.1f} MB" if size else f"{label}: WAL only")
        else:
            warn(f"{label}: not found (nothing to remove)")

    # Confirm
    if not typer.confirm("Are you sure you want to delete these files?"):
        warn("Aborted.")
        raise typer.Exit(0)

    # Delete
    removed = 0
    for path, label in targets:
        wal_path = path.with_suffix(".duckdb.wal")
        if path.exists():
            path.unlink()
            removed += 1
        if wal_path.exists():
            wal_path.unlink()

    if all_:
        # Clean up any other stale files in the data directory
        # (only remove files, not subdirectories, to be safe)
        if config.data_dir.exists():
            for item in config.data_dir.iterdir():
                if item.is_file() and item.suffix in {".duckdb", ".wal"}:
                    item.unlink()
                    removed += 1

    success(f"Removed {removed} file(s)")
