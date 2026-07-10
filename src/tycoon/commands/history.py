"""tycoon data history — terminal view of dlt + dbt run history.

Reads ``.tycoon/metadata.duckdb`` and prints a unified feed of recent
runs or a drilldown into a single invocation / load.

Two invocation modes:

* ``tycoon data history``          — list recent runs across both tools
* ``tycoon data history show <id>`` — per-run detail (short id prefix OK)
"""

from __future__ import annotations

import datetime
from pathlib import Path

import typer
from rich.table import Table

from tycoon.config import config
from tycoon.core.history import HistoryRepository, RunSummary
from tycoon.observability import metadata_db_path
from tycoon.utils.console import console, error, header, info


app = typer.Typer(
    help="Show dlt + dbt run history captured in .tycoon/metadata.duckdb.",
    invoke_without_command=True,
    no_args_is_help=False,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _metadata_or_exit() -> Path:
    """Return the metadata DB path, exiting with a hint if it doesn't exist."""
    meta = metadata_db_path(config.root)
    if not meta.exists():
        info(
            "No run history yet — metadata DB not found at "
            f"[dim]{meta.relative_to(config.root)}[/dim]. "
            "Run [bold]tycoon data sources run[/bold] or "
            "[bold]tycoon data transform run[/bold] to start capturing."
        )
        raise typer.Exit(0)
    return meta


def _fmt_ts(ts: datetime.datetime | None) -> str:
    if ts is None:
        return "—"
    if ts.tzinfo is not None:
        ts = ts.astimezone().replace(tzinfo=None)
    return ts.strftime("%Y-%m-%d %H:%M")


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(seconds, 60)
    return f"{int(minutes)}m{int(secs):02d}s"


def _short(id_value: str, n: int = 8) -> str:
    return id_value[:n] if id_value else "—"


# ---------------------------------------------------------------------------
# List view
# ---------------------------------------------------------------------------


def _render_history_table(runs: list[RunSummary]) -> Table:
    table = Table(show_lines=False)
    table.add_column("When", style="dim", no_wrap=True)
    table.add_column("Tool", style="bold")
    table.add_column("Ref", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    for s in runs:
        is_dbt = s.runtime_id == "dbt"
        tool_style = (
            "[bold magenta]dbt[/bold magenta]"
            if is_dbt
            else "[bold cyan]dlt[/bold cyan]"
        )
        status_str = "[green]✓[/green]" if s.status == "success" else "[red]✗[/red]"

        if is_dbt:
            cmd = s.command or "run"
            ref = f"{cmd} ({_short(s.run_id)})"
            detail = _fmt_duration(s.duration_seconds)
            if s.rows_total:
                detail += f" · {s.rows_total} models"
        else:
            ref = f"{s.source_id}/{_short(s.run_id)}"
            detail = f"{s.rows_total:,} rows"

        table.add_row(_fmt_ts(s.started_at), tool_style, ref, status_str, detail)

    return table


def _resolve_layer_models(layer: str) -> list[str]:
    """Translate ``--layer staging`` into the list of model names in that layer.

    Raises ``typer.Exit(1)`` on an unknown layer or when no dbt manifest is
    available. Returns the (possibly empty) list of model names otherwise.
    """
    from tycoon.layers import (
        Layer,
        classify_dbt_models,
        filter_by_layer,
        load_manifest,
    )

    try:
        layer_enum = Layer(layer.lower())
    except ValueError:
        valid = ", ".join(layer_value.value for layer_value in Layer)
        error(f"Invalid --layer '{layer}'. Use one of: {valid}.")
        raise typer.Exit(1)

    manifest = load_manifest(config.dbt_project_dir)
    if manifest is None:
        error(
            "No dbt manifest found. Run `tycoon data transform run` "
            "(or `dbt compile`) before filtering history by layer."
        )
        raise typer.Exit(1)

    return [m.name for m in filter_by_layer(classify_dbt_models(manifest), layer_enum)]


def _list_history(
    tool: str,
    limit: int,
    source: str | None = None,
    layer: str | None = None,
) -> None:
    # Resolve --layer BEFORE checking for the metadata DB so a typo in the
    # layer name surfaces with a clean exit(1) regardless of project state.
    layer_models = _resolve_layer_models(layer) if layer else None

    meta = _metadata_or_exit()

    from tycoon.metadata_backends.duckdb_file import DuckDBFileBackend

    try:
        with DuckDBFileBackend(meta, read_only=True) as b:
            repo = HistoryRepository(b)
            runs = repo.list_runs(limit=None)
    except Exception as exc:
        console.print(f"[dim]Warning: could not read run history ({exc})[/dim]")
        runs = []

    if tool == "dlt":
        runs = [r for r in runs if r.runtime_id != "dbt"]
    elif tool == "dbt":
        runs = [r for r in runs if r.runtime_id == "dbt"]

    if source is not None:
        runs = [r for r in runs if r.source_id == source and r.runtime_id != "dbt"]
    elif layer_models is not None:
        # --layer restricts to dbt runs only; per-model filtering requires
        # per-node event detail added in a later milestone.
        runs = [r for r in runs if r.runtime_id == "dbt"]

    runs = runs[:limit]

    if not runs:
        if layer_models is not None:
            info(
                f"No dbt invocations captured for the [bold]{layer}[/bold] "
                "layer yet."
            )
        elif source is not None:
            info(f"No dlt runs captured for source [bold]{source}[/bold].")
        else:
            info("No runs captured yet for the selected tool(s).")
        return

    title = "Run History"
    if source is not None:
        title += f" — {source}"
    elif layer_models is not None:
        title += f" — {layer} layer"
    header(title)
    console.print(_render_history_table(runs))
    console.print()
    info("Drill in with [bold]tycoon data history show <id>[/bold] (short prefix OK).")


# ---------------------------------------------------------------------------
# Show (drilldown) view
# ---------------------------------------------------------------------------


def _show_run(id_prefix: str) -> None:
    meta = _metadata_or_exit()

    from tycoon.metadata_backends.duckdb_file import DuckDBFileBackend

    try:
        with DuckDBFileBackend(meta, read_only=True) as b:
            repo = HistoryRepository(b)
            detail = repo.get_run(id_prefix)
    except Exception as exc:
        console.print(f"[dim]Warning: could not read run detail ({exc})[/dim]")
        detail = None

    if detail is None:
        error(
            f"No run matches prefix '{id_prefix}' (or prefix is ambiguous). "
            "Try [bold]tycoon data history[/bold] to list."
        )
        raise typer.Exit(1)

    s = detail.summary
    is_dbt = s.runtime_id == "dbt"

    if is_dbt:
        cmd = s.command or "run"
        header(f"dbt {cmd}: {s.run_id}")
    else:
        header(f"dlt load: {s.run_id}")

    status_str = "[green]success[/green]" if s.status == "success" else "[red]failed[/red]"
    console.print(f"  [bold]Source:[/bold] {s.source_id}")
    console.print(f"  [bold]Status:[/bold] {status_str}")
    console.print(f"  [bold]Started:[/bold] {_fmt_ts(s.started_at)}")
    console.print(f"  [bold]Duration:[/bold] {_fmt_duration(s.duration_seconds)}")

    if detail.error:
        console.print(f"  [bold]Error:[/bold] [red]{detail.error}[/red]")

    if detail.rows_by_table:
        rows_table = Table(title="Tables", show_lines=False)
        rows_table.add_column("Table", style="cyan")
        rows_table.add_column("Rows", justify="right")
        total = 0
        for tname, rcount in sorted(detail.rows_by_table.items()):
            rows_table.add_row(tname, f"{rcount:,}")
            total += rcount
        rows_table.add_row("[bold]Total[/bold]", f"[bold]{total:,}[/bold]")
        console.print(rows_table)
    elif not detail.error:
        console.print("\n[dim]No per-table detail captured for this run.[/dim]")


# ---------------------------------------------------------------------------
# Typer wiring
# ---------------------------------------------------------------------------


@app.callback()
def history_default(
    ctx: typer.Context,
    tool: str = typer.Option(
        "all", "--tool", "-t", help="Filter by tool: all, dlt, or dbt."
    ),
    limit: int = typer.Option(
        20, "--limit", "-n", help="Max rows to display (default 20)."
    ),
    source: str = typer.Option(
        None,
        "--source",
        "-s",
        help=(
            "Filter dlt runs to a specific source. Accepts the config name "
            "from tycoon.yml (e.g. 'pokeapi') or a literal source id. "
            "dbt runs are hidden when this flag is set."
        ),
    ),
    layer: str = typer.Option(
        None,
        "--layer",
        "-l",
        help=(
            "Restrict history to dbt runs, validated against the given "
            "layer (staging / intermediate / mart / snapshot / seed). "
            "Requires a compiled dbt manifest. Note: per-model filtering "
            "is not yet available — all dbt invocations are shown "
            "regardless of which models were touched (M1 limitation)."
        ),
    ),
) -> None:
    """List the most recent dlt + dbt runs captured in the metadata DB."""
    if ctx.invoked_subcommand is not None:
        return
    if tool not in ("all", "dlt", "dbt"):
        error(f"Invalid --tool '{tool}'. Use: all, dlt, dbt.")
        raise typer.Exit(1)
    if source and layer:
        error("Pass either --source or --layer, not both.")
        raise typer.Exit(1)
    _list_history(tool, limit, source=source, layer=layer)


@app.command("show")
def history_show(
    run_id: str = typer.Argument(
        ..., help="Load id (dlt) or event id (dbt). Short prefix OK."
    ),
) -> None:
    """Show per-table detail for a specific run."""
    _show_run(run_id)
