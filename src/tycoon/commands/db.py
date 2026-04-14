"""tycoon data query / schema / clean — database inspection and querying."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import duckdb
import typer
from rich.table import Table

from tycoon.config import config
from tycoon.utils.console import console, header, info, success, error, warn, status_table
from tycoon.utils.duckdb_utils import db_file_size_mb, get_tables, get_row_count


def _resolve_source_db(source_name: str) -> Path:
    """Find the raw DuckDB file for a named source.

    Checks for the file at config.raw_db first (single-DB mode), then
    looks for data/raw_{source_name}.duckdb and data/{prefix}_raw.duckdb
    patterns in the data directory.
    """
    # If config.raw_db exists and has a schema matching this source, use it
    if config.raw_db.exists():
        try:
            con = duckdb.connect(str(config.raw_db), read_only=True)
            schemas = [r[0] for r in con.execute(
                "SELECT DISTINCT schema_name FROM information_schema.schemata"
            ).fetchall()]
            con.close()
            source_schema = f"raw_{source_name.replace('-', '_')}"
            if source_schema in schemas:
                return config.raw_db
        except duckdb.Error:
            pass

    # Look for per-source files in the data directory
    data_dir = config.data_dir
    if data_dir.exists():
        for pattern in [
            f"raw_{source_name.replace('-', '_')}.duckdb",
            f"*_raw.duckdb",
        ]:
            matches = sorted(data_dir.glob(pattern))
            for match in matches:
                try:
                    con = duckdb.connect(str(match), read_only=True)
                    schemas = [r[0] for r in con.execute(
                        "SELECT DISTINCT schema_name FROM information_schema.schemata"
                    ).fetchall()]
                    con.close()
                    source_schema = f"raw_{source_name.replace('-', '_')}"
                    if source_schema in schemas:
                        return match
                except duckdb.Error:
                    continue

    # Fallback: return the expected per-source path (caller will show error)
    return data_dir / f"raw_{source_name.replace('-', '_')}.duckdb"


# ---------------------------------------------------------------------------
# schema (was: stats)
# ---------------------------------------------------------------------------


def schema() -> None:
    """Show database tables, row counts, and file sizes."""
    header("Database Schema")

    rows: list[tuple[str, str, str]] = []

    for db_path, label in [(config.raw_db, "Raw"), (config.local_db, "Warehouse")]:
        size = db_file_size_mb(db_path)
        if size is not None:
            rows.append((f"{label} database", "OK", f"{size:.1f} MB"))
            tables = get_tables(db_path)
            rows.append(("  Tables", "", f"{len(tables)}"))
            for s, table in tables:
                count = get_row_count(db_path, s, table)
                rows.append((
                    f"  {s}.{table}",
                    "",
                    f"{count:,} rows" if count is not None else "empty",
                ))
        else:
            rows.append((f"{label} database", "WARN", "not found"))

    # Also scan for any other .duckdb files in the data directory
    data_dir = config.data_dir
    seen = {config.raw_db.resolve(), config.local_db.resolve()}
    if data_dir.exists():
        for db_file in sorted(data_dir.glob("*.duckdb")):
            if db_file.resolve() in seen:
                continue
            seen.add(db_file.resolve())
            size = db_file_size_mb(db_file)
            if size is not None:
                rows.append((db_file.name, "OK", f"{size:.1f} MB"))
                tables = get_tables(db_file)
                rows.append(("  Tables", "", f"{len(tables)}"))
                for s, table in tables:
                    count = get_row_count(db_file, s, table)
                    rows.append((
                        f"  {s}.{table}",
                        "",
                        f"{count:,} rows" if count is not None else "empty",
                    ))

    console.print(status_table(rows, title="Database Schema"))


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------


def query(
    sql: Annotated[str, typer.Argument(help="SQL query to execute.")],
    raw: Annotated[
        bool,
        typer.Option("--raw", help="Query the raw database instead of the warehouse."),
    ] = False,
    source: Annotated[
        str | None,
        typer.Option("--source", "-s", help="Query a specific source's raw database (e.g. pokeapi)."),
    ] = None,
    db: Annotated[
        Path | None,
        typer.Option("--db", help="Path to a DuckDB file to query directly."),
    ] = None,
) -> None:
    """Run a read-only SQL query against the warehouse, raw, or a source database."""
    if db:
        db_path = db
        label = db_path.name
    elif source:
        db_path = _resolve_source_db(source)
        label = f"raw ({source})"
    elif raw:
        db_path = config.raw_db
        label = "raw"
    else:
        db_path = config.local_db
        label = "warehouse"

    if not db_path.exists():
        error(f"Database not found at {db_path}")
        if source:
            info(f"Run 'tycoon data sources run {source}' to ingest data first.")
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
        if config.data_dir.exists():
            for item in config.data_dir.iterdir():
                if item.is_file() and item.suffix in {".duckdb", ".wal"}:
                    item.unlink()
                    removed += 1

    success(f"Removed {removed} file(s)")
