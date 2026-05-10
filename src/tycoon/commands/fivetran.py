"""tycoon data fivetran — pull + display Fivetran connector metadata.

Lights up only when ``stack.ingestion = fivetran`` and
``stack.ingestion_metadata`` is populated. Two subcommands:

* ``sync`` — call the Fivetran Metadata API, write a snapshot row per
  connector into ``.tycoon/metadata.duckdb``.
* ``list`` — print the latest snapshot in a Rich table.
"""

from __future__ import annotations

import typer
from rich.table import Table

from tycoon.config import config
from tycoon.ingestion.fivetran_client import (
    FivetranAPIError,
    build_client_from_config,
)
from tycoon.ingestion.fivetran_sync import (
    freshness_label,
    latest_connector_snapshot,
    sync_fivetran_metadata,
)
from tycoon.observability import metadata_db_path
from tycoon.project import IngestionTool
from tycoon.utils.console import console, error, header, info, success, warn

app = typer.Typer(
    help="Pull connector + sync metadata from the Fivetran API.",
    no_args_is_help=True,
)


def _require_fivetran_configured() -> None:
    project = config.project
    if project is None:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    stack = project.stack
    if stack.ingestion != IngestionTool.fivetran:
        error(
            f"stack.ingestion is [bold]{stack.ingestion.value}[/bold]; this "
            "command requires [bold]fivetran[/bold]. Update tycoon.yml first."
        )
        raise typer.Exit(1)

    if stack.ingestion_metadata is None:
        error(
            "stack.ingestion_metadata is missing. Add an "
            "[bold]ingestion_metadata[/bold] block with api_key, api_secret, "
            "group_id under [bold]stack[/bold] in tycoon.yml."
        )
        raise typer.Exit(1)


@app.command()
def sync() -> None:
    """Pull connector metadata from Fivetran and snapshot it locally."""
    _require_fivetran_configured()
    header("Fivetran metadata sync")

    project = config.project
    assert project is not None and project.stack.ingestion_metadata is not None

    try:
        with build_client_from_config(project.stack.ingestion_metadata) as client:
            result = sync_fivetran_metadata(client, metadata_db_path(config.root))
    except FivetranAPIError as exc:
        error(f"Fivetran sync failed: {exc}")
        raise typer.Exit(1) from exc

    success(
        f"Captured {result.connectors_seen} connector(s) at "
        f"{result.captured_at.isoformat(timespec='seconds')}."
    )
    info(
        f"  Healthy: {result.healthy} · Failing: {result.failing} · "
        f"Paused: {result.paused} · New: {result.new}"
    )
    if result.connectors_seen == 0:
        warn(
            "No connectors found in this group. Check `group_id` in "
            "tycoon.yml's stack.ingestion_metadata block."
        )


@app.command(name="list")
def list_cmd() -> None:
    """Print the latest snapshot of every connector."""
    _require_fivetran_configured()
    header("Fivetran connectors")

    rows = latest_connector_snapshot(metadata_db_path(config.root))
    if not rows:
        info(
            "No snapshots yet. Run [bold]tycoon data fivetran sync[/bold] to "
            "fetch the current state."
        )
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Connector")
    table.add_column("Service", style="dim")
    table.add_column("Schema")
    table.add_column("Sync state")
    table.add_column("Last activity")

    for r in rows:
        label, style = freshness_label(
            succeeded_at=r["succeeded_at"],
            failed_at=r["failed_at"],
            paused=bool(r["paused"]),
        )
        sync_label = r.get("sync_state") or "—"
        if r.get("setup_state") and r["setup_state"] != "connected":
            sync_label = f"{sync_label} ({r['setup_state']})"
        table.add_row(
            r["name"] or r["connector_id"],
            r.get("service") or "—",
            r.get("schema_name") or "—",
            sync_label,
            f"[{style}]{label}[/{style}]",
        )
    console.print(table)
    console.print()
    info(
        "Snapshot history accumulates in `.tycoon/metadata.duckdb` — "
        "every `fivetran sync` adds one row per connector."
    )
