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


def _resolve_source_db(source_name: str) -> Path | None:
    """Find the raw DuckDB file for a named source, or None if not found.

    Priority:
      1. ``config.raw_db``, if it contains the ``raw_<name>`` schema
         (single-DB mode — current default for ``tycoon data sources run``).
      2. ``data/raw_<name>.duckdb`` (canonical per-source filename).
      3. Any other ``data/*.duckdb`` that contains the ``raw_<name>`` schema
         (covers externally-loaded or alternatively-named files).
    """
    normalized = source_name.replace("-", "_")
    source_schema = f"raw_{normalized}"

    if config.raw_db.exists() and _has_schema(config.raw_db, source_schema):
        return config.raw_db

    per_source = config.data_dir / f"raw_{normalized}.duckdb"
    if per_source.exists():
        return per_source

    if config.data_dir.exists():
        skip = {config.raw_db.resolve(), per_source.resolve()}
        for candidate in sorted(config.data_dir.glob("*.duckdb")):
            if candidate.resolve() in skip:
                continue
            if _has_schema(candidate, source_schema):
                return candidate

    return None


def _has_schema(db_path: Path, schema_name: str) -> bool:
    """Return True if the DuckDB file contains the given schema."""
    try:
        con = duckdb.connect(str(db_path), read_only=True)
        try:
            schemas = [
                r[0]
                for r in con.execute(
                    "SELECT DISTINCT schema_name FROM information_schema.schemata"
                ).fetchall()
            ]
        finally:
            con.close()
    except duckdb.Error:
        return False
    return schema_name in schemas


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
        resolved = _resolve_source_db(source)
        if resolved is None:
            error(f"No raw database found for source '{source}'.")
            info(f"Run 'tycoon data sources run {source}' to ingest data first.")
            raise typer.Exit(1)
        db_path = resolved
        label = f"raw ({source})"
    elif raw:
        db_path = config.raw_db
        label = "raw"
    else:
        db_path = config.local_db
        label = "warehouse"

    if not db_path.exists():
        error(f"Database not found at {db_path}")
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
    metadata: Annotated[
        bool,
        typer.Option(
            "--metadata",
            help="Also remove .tycoon/metadata.duckdb (observability history).",
        ),
    ] = False,
    all_: Annotated[
        bool,
        typer.Option(
            "--all",
            help=(
                "Remove raw + local databases and clean up the data directory. "
                "By default preserves .tycoon/metadata.duckdb; pass --metadata "
                "together with --all to wipe run history too."
            ),
        ),
    ] = False,
) -> None:
    """Remove database files (with confirmation).

    Run history in ``.tycoon/metadata.duckdb`` is preserved by default (even
    with ``--all``) so `tycoon data history` and the Rill observability
    dashboards survive routine data resets. Use ``--metadata`` to explicitly
    wipe it.
    """
    from tycoon.observability import metadata_db_path

    if not (raw or local or all_ or metadata):
        error("Specify at least one of --raw, --local, --metadata, or --all.")
        raise typer.Exit(1)

    targets: list[tuple[Path, str]] = []

    if raw or all_:
        targets.append((config.raw_db, "raw database"))
    if local or all_:
        targets.append((config.local_db, "local database"))
    if metadata:
        targets.append((metadata_db_path(config.root), "observability metadata DB"))

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

    if all_ and not metadata:
        meta = metadata_db_path(config.root)
        if meta.exists():
            info("[dim]Preserving observability metadata DB — pass --metadata to remove.[/dim]")

    # Confirm
    if not typer.confirm("Are you sure you want to delete these files?"):
        warn("Aborted.")
        raise typer.Exit(0)

    # Delete
    removed = 0
    deleted_paths: set[Path] = set()
    for path, _label in targets:
        wal_path = path.with_suffix(".duckdb.wal")
        if path.exists():
            path.unlink()
            removed += 1
        if wal_path.exists():
            wal_path.unlink()
        deleted_paths.add(path.resolve())

    if all_ and config.data_dir.exists():
        preserved = {metadata_db_path(config.root).resolve()} if not metadata else set()
        for item in config.data_dir.iterdir():
            resolved = item.resolve()
            if resolved in preserved:
                continue
            if item.is_file() and item.suffix in {".duckdb", ".wal"}:
                item.unlink()
                removed += 1

    success(f"Removed {removed} file(s)")
