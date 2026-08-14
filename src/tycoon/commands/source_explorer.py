"""tycoon data sources explore — interactive source inspection.

Commands:

* ``tycoon data sources explore``          — list all sources with metadata
* ``tycoon data sources explore <name>``   — inspect schema, sample data, health
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import duckdb
import typer

from tycoon.config import load_config
from tycoon.ingestion.catalog import get_entry
from tycoon.utils.console import console, error, header, info, next_steps, warn
from tycoon.utils.duckdb_utils import quote_identifier

app = typer.Typer(
    help="Explore sources: inspect schema, sample data, and health.",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------


def _raw_db_tables(raw_db: Path, schema_name: str) -> list[dict]:
    """Return per-table metadata from the raw DuckDB database."""
    if not raw_db.exists():
        return []
    try:
        with duckdb.connect(str(raw_db), read_only=True) as con:
            rows = con.execute(
                "SELECT table_name, column_name, data_type "
                "FROM information_schema.columns "
                "WHERE table_schema = ? "
                "ORDER BY table_name, ordinal_position",
                [schema_name],
            ).fetchall()
        tables: dict[str, list[dict]] = {}
        for table_name, column_name, data_type in rows:
            tables.setdefault(table_name, []).append({"column": column_name, "type": data_type})
        return [{"table": t, "columns": cols} for t, cols in tables.items()]
    except Exception:
        return []


def _sample_rows(raw_db: Path, schema_name: str, table_name: str, limit: int = 10) -> list[dict] | None:
    """Return up to *limit* rows from ``schema.table``."""
    if not raw_db.exists():
        return None
    try:
        with duckdb.connect(str(raw_db), read_only=True) as con:
            quoted_table = quote_identifier(table_name)
            quoted_schema = quote_identifier(schema_name)
            rows = con.execute(
                f"SELECT * FROM {quoted_schema}.{quoted_table} LIMIT ?",
                [limit],
            ).fetchall()
        if not rows:
            return []
        desc = con.execute(
            f"SELECT * FROM {quoted_schema}.{quoted_table} LIMIT 1",
        ).description
        if not desc:
            return None
        columns = [d[0] for d in desc]
        return [dict(zip(columns, row)) for row in rows]
    except Exception:
        return None


def _source_health(raw_db: Path, schema_name: str) -> dict:
    """Return freshness / run info from the metadata DB."""
    meta_db = Path.cwd() / ".tycoon" / "metadata.duckdb"
    health: dict = {"runs": 0, "last_run": None, "last_status": None, "total_rows": 0}
    if not meta_db.exists():
        return health

    try:
        with duckdb.connect(str(meta_db), read_only=True) as con:
            row = con.execute(
                "SELECT COUNT(*), MAX(inserted_at), MAX(status), COALESCE(SUM(rows_loaded), 0) "
                "FROM dlt_runs WHERE source_schema = ?",
                [schema_name],
            ).fetchone()
            if row and row[0]:
                health["runs"] = row[0]
                health["last_run"] = str(row[1]) if row[1] else None
                health["last_status"] = row[2]
                health["total_rows"] = row[3]
    except Exception:
        pass
    return health


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def explore(
    source_name: Annotated[
        str | None,
        typer.Argument(help="Name of a registered source to inspect."),
    ] = None,
    sample: Annotated[
        int,
        typer.Option("--sample", "-n", help="Number of sample rows to show (default: 10)."),
    ] = 10,
) -> None:
    """Explore sources: inspect schema, sample data, and health.

    Without a source name, lists all registered sources with metadata.
    With a source name, shows schema, sample data, and health info.
    """
    cfg = load_config()
    if not cfg.has_project_file:
        error("No tycoon.yml found. Run 'tycoon init' first.")
        raise typer.Exit(1)

    sources = cfg.sources
    if not sources:
        error("No sources registered. Run 'tycoon data sources add' first.")
        raise typer.Exit(1)

    # No source name provided — list all sources
    if not source_name:
        _list_sources(sources)
        return

    # Source name provided — inspect it
    if source_name not in sources:
        error(f"Source '{source_name}' not found. Available: {', '.join(sources.keys()) or '(none)'}")
        raise typer.Exit(1)

    _inspect_source(cfg, source_name, sample)


# ---------------------------------------------------------------------------
# List all sources
# ---------------------------------------------------------------------------


def _list_sources(sources: dict[str, object]) -> None:
    """Display a table of all registered sources with catalog metadata."""
    header("Sources")

    from rich.table import Table

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("Type")
    table.add_column("Schema")
    table.add_column("Category")
    table.add_column("Resources", justify="right")

    for name, src_cfg in sources.items():
        catalog_entry = get_entry(src_cfg.type) if hasattr(src_cfg, "type") else None
        display_name = src_cfg.type
        schema = getattr(src_cfg, "schema_name", None) or "—"
        category = catalog_entry.category if catalog_entry else "—"
        resources = len(catalog_entry.resources) if catalog_entry and hasattr(catalog_entry, "resources") else "—"

        table.add_row(name, display_name, str(schema), category, str(resources))

    console.print(table)
    console.print()
    info("Drill in with 'tycoon data sources explore <name>' to inspect a source.")


# ---------------------------------------------------------------------------
# Inspect a single source
# ---------------------------------------------------------------------------


def _inspect_source(cfg: object, source_name: str, sample_limit: int) -> None:
    """Show schema, sample data, and health for a single source."""
    source_cfg = cfg.sources[source_name]
    schema_name = getattr(source_cfg, "schema_name", None)

    header(f"Source: {source_name}")
    info(f"Type: {source_cfg.type}")
    info(f"Schema: {schema_name}")

    # Catalog metadata
    catalog_entry = get_entry(source_cfg.type)
    if catalog_entry:
        info(f"Category: {catalog_entry.category}")
        if hasattr(catalog_entry, "description") and catalog_entry.description:
            info(f"Description: {catalog_entry.description}")
        if hasattr(catalog_entry, "resources") and catalog_entry.resources:
            info(f"Resources: {', '.join(catalog_entry.resources)}")

    # Schema inspection
    raw_db = cfg.raw_db
    if not raw_db.exists():
        warn(f"Raw database not found at {raw_db}. Run 'tycoon data sources run {source_name}' first.")
        next_steps(("Run the source", f"tycoon data sources run {source_name}"))
        return

    schema_data = _raw_db_tables(raw_db, schema_name)
    if not schema_data:
        warn(f"No tables found in schema '{schema_name}'.")
        next_steps(("Run the source", f"tycoon data sources run {source_name}"))
        return

    # Display schema
    from rich.table import Table

    console.print()
    console.print(("[bold]Schema[/bold]"))

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Table", style="bold")
    table.add_column("Columns", justify="right")
    table.add_column("Data Types")

    for td in schema_data:
        col_info = ", ".join(f"{c['column']}: {c['type']}" for c in td["columns"])
        table.add_row(td["table"], str(len(td["columns"])), col_info)

    console.print(table)

    # Sample data (first table only)
    if schema_data:
        first_table = schema_data[0]["table"]
        console.print()
        console.print(("[bold]Sample Data[/bold]"))
        rows = _sample_rows(raw_db, schema_name, first_table, sample_limit)
        if rows is None:
            warn(f"Could not read sample data from '{first_table}'.")
        elif not rows:
            info(f"'{first_table}' is empty.")
        else:
            from rich.panel import Panel
            from rich.table import Table as RichTable

            sample_table = RichTable(show_header=True, header_style="bold cyan", box=None)
            columns = list(rows[0].keys())
            for col in columns:
                sample_table.add_column(str(col))
            for row in rows:
                sample_table.add_row(*[str(v) for v in row.values()])
            console.print(Panel(sample_table, title=f"{first_table} (first {len(rows)} rows)"))

    # Health info
    console.print()
    console.print(("[bold]Health[/bold]"))
    health = _source_health(raw_db, schema_name)
    if health["runs"] == 0:
        warn("No runs recorded yet.")
        next_steps(("Run the source", f"tycoon data sources run {source_name}"))
    else:
        info(f"Total runs: {health['runs']}")
        info(f"Last status: {health['last_status']}")
        if health["last_run"]:
            info(f"Last run: {health['last_run']}")
        if health["total_rows"]:
            info(f"Total rows loaded: {health['total_rows']:,}")
