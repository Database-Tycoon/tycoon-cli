"""tycoon fire / firehouse / repair — CLI views of the city's fire-and-response system.

These commands read from the **same data sources** the 3D city renders: dbt
run artifacts for test results, the observability metadata DB for run history
and source freshness. They present that data in text form so a user can check
"what's burning?" or "what needs a contractor?" without opening the browser.

The city's vocabulary, kept exactly (see `web/src/ui/legend.ts` and the tour):
a failing test sets its building ON FIRE and the firehouse dispatches one red
**fire truck** per fire; a source past its freshness SLA is a **worn building**
that gets one amber **contractor van** (and fogs the districts it feeds). Both
fleets restate a measured, unresolved fact — a vehicle on the street means a
problem is AWAITING response, never that a fix is running.

Four commands:

* ``tycoon fire``            — what's burning right now (test_status = "fail")
* ``tycoon fire --run <id>`` — what was burning in a specific run (replay)
* ``tycoon repair``          — the contractor call sheet: sources past SLA
* ``tycoon firehouse``       — dispatch stats: station location, trucks and
                               vans on duty
"""

from __future__ import annotations

from pathlib import Path

import typer

from rich.panel import Panel
from rich.table import Table

from tycoon.config import config
from tycoon.observability import metadata_db_path
from tycoon.utils.console import console, error, header, info

app = typer.Typer(
    help="Fire and response: CLI views of the city's fire-and-dispatch system.",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# Helpers: load data from the same sources the city reads
# ---------------------------------------------------------------------------


def _metadata_db() -> Path | None:
    """Return the metadata DB path, or None if it doesn't exist."""
    path = metadata_db_path(config.root)
    return path if path.exists() else None


def _failing_tests_from_run_results(path: Path) -> list[tuple[str, str]]:
    """Failing results from dbt's latest ``run_results.json``.

    Statuses live in ``run_results.json`` — ``manifest.json`` describes the
    project and never carries them (the same distinction the city's loader
    makes). Returns ``[(node_name, status), ...]`` for every result with
    ``status == 'fail'`` or ``status == 'error'``.
    """
    import json

    results_path = path / "target" / "run_results.json"
    if not results_path.exists():
        return []
    try:
        data = json.loads(results_path.read_text())
    except (OSError, json.JSONDecodeError):
        return []

    failing: list[tuple[str, str]] = []
    for result in data.get("results", []):
        status = str(result.get("status", "")).lower()
        if status in ("fail", "error"):
            unique_id = result.get("unique_id", "")
            name = unique_id.rsplit(".", 1)[-1] if unique_id else "(unknown)"
            failing.append((name, status))

    return failing


def _failing_tests_from_history(metadata_db: Path) -> list[tuple[str, str, str]]:
    """Failing test results from the metadata DB (latest run).

    Returns ``[(node_name, resource_type, status), ...]`` for every node with
    a failing status in the most recent invocation.
    """
    import duckdb

    if not metadata_db.exists():
        return []
    try:
        with duckdb.connect(str(metadata_db), read_only=True) as con:
            rows = con.execute(
                "SELECT node_name, resource_type, status "
                "FROM dbt_nodes "
                "WHERE invocation_id = (SELECT MAX(invocation_id) FROM dbt_runs) "
                "AND status IN ('fail', 'error')"
            ).fetchall()
        return [(name, res_type, status) for name, res_type, status in rows]
    except Exception:
        return []


def _source_freshness_from_history(metadata_db: Path) -> list[tuple[str, str, str | None]]:
    """Stale source results from the metadata DB.

    Returns ``[(source_name, freshness_status, last_loaded_at), ...]`` for
    sources with ``warn`` or ``error`` freshness.
    """
    import duckdb

    if not metadata_db.exists():
        return []
    try:
        with duckdb.connect(str(metadata_db), read_only=True) as con:
            rows = con.execute(
                "SELECT name, freshness_status, max_loaded_at "
                "FROM source_freshness "
                "WHERE freshness_status IN ('warn', 'error')"
            ).fetchall()
        return [(name, status, loaded) for name, status, loaded in rows]
    except Exception:
        return []


def _run_failures_from_history(metadata_db: Path, invocation_id: str) -> list[tuple[str, str, str]]:
    """Failing test results for a specific run (by invocation_id).

    Returns ``[(node_name, resource_type, status), ...]`` for every node with
    a failing status in the specified invocation.
    """
    import duckdb

    if not metadata_db.exists():
        return []
    try:
        with duckdb.connect(str(metadata_db), read_only=True) as con:
            rows = con.execute(
                "SELECT node_name, resource_type, status "
                "FROM dbt_nodes "
                "WHERE invocation_id = ? AND status IN ('fail', 'error')",
                [invocation_id],
            ).fetchall()
        return [(name, res_type, status) for name, res_type, status in rows]
    except Exception:
        return []


def _firehouse_info(city_path: Path) -> dict:
    """The station's map location from an exported city.json, if one exists."""
    import json

    if not city_path.exists():
        return {}
    try:
        data = json.loads(city_path.read_text())
        firehouse = data.get("firehouse")
        if firehouse:
            return {
                "x": firehouse.get("x"),
                "y": firehouse.get("y"),
            }
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _dispatch_stats_from_city(city_path: Path) -> dict:
    """Dispatch stats from an exported city.json.

    Counts lots with ``test_status == 'fail'`` (fires — one truck each) and
    ``freshness_status in ('warn', 'error')`` (repair calls — one contractor
    van each). These are the exact fleet-selection rules the renderer uses
    (`web/src/scene/firetrucks.ts`). No "unreachable" count: the contract
    carries no such field, and the current planner guarantees every lot
    fronts the one connected street network — the renderer independently
    re-checks by routing each vehicle over roads.
    """
    import json

    if not city_path.exists():
        return {}
    try:
        data = json.loads(city_path.read_text())
        lots = data.get("lots", [])

        fire_count = sum(1 for lot in lots if lot.get("test_status") == "fail")
        repair_count = sum(1 for lot in lots if lot.get("freshness_status") in ("warn", "error"))

        return {
            "fires": fire_count,
            "repairs": repair_count,
        }
    except (OSError, json.JSONDecodeError):
        return {}


def _human_age(seconds: float | None) -> str:
    """Convert seconds to a human-readable age string."""
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{int(seconds)}s ago"
    if seconds < 3600:
        return f"{int(seconds / 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds / 3600)}h ago"
    return f"{int(seconds / 86400)}d ago"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def fire(
    run: str | None = typer.Option(
        None,
        "--run",
        "-r",
        help="Show failures for a specific run (invocation ID prefix).",
    ),
) -> None:
    """Show what's burning: failing tests from the latest run.

    Each failing test sets its building ON FIRE in the 3D city (the legend's
    words) — the CLI and the city show the **same data**, just in different
    formats. A fire is a fact awaiting response, never a fix in progress.

    Use ``--run`` to inspect failures from a specific invocation instead of
    the standing (latest) state.
    """
    if not config.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    header("Fires")

    metadata_db = _metadata_db()
    dbt_dir = config.dbt_project_dir or config.root / "dbt_project"

    if run:
        # Specific run: match the given invocation-ID prefix, newest first.
        if not metadata_db:
            info("No metadata database found. Run [bold]tycoon data transform[/bold] to capture run history.")
            return

        import duckdb

        try:
            with duckdb.connect(str(metadata_db), read_only=True) as con:
                row = con.execute(
                    "SELECT invocation_id FROM dbt_runs WHERE invocation_id LIKE ? ORDER BY started_at DESC LIMIT 1",
                    [run + "%"],
                ).fetchone()
                if not row:
                    info(f"No run found matching '{run}'.")
                    return
                invocation_id = row[0]
        except Exception:
            info("Could not read run history.")
            return

        failures = _run_failures_from_history(metadata_db, invocation_id)

        if not failures:
            info("No failures in this run. All green. (No fires in the city.)")
            return

        table = Table(show_header=True, header_style="bold red")
        table.add_column("Model", style="bold")
        table.add_column("Type", style="dim")
        table.add_column("Status")

        for name, res_type, status in failures:
            table.add_row(name, res_type, f"[red]{status}[/red]")

        console.print(table)
        console.print()
        info(f"[red]{len(failures)}[/red] building(s) on fire in this run.")
        info("The run replay in the 3D city shows these same buildings burning.")
        return

    # Standing state: latest run's failures
    failures: list[tuple[str, str, str]] = []
    if metadata_db:
        failures = _failing_tests_from_history(metadata_db)

    if not failures:
        # Fallback: dbt's own run_results.json (no metadata ledger yet).
        if dbt_dir.exists():
            failures_from_artifacts = _failing_tests_from_run_results(dbt_dir)
            if failures_from_artifacts:
                table = Table(show_header=True, header_style="bold red")
                table.add_column("Model", style="bold")
                table.add_column("Status")

                for name, status in failures_from_artifacts:
                    table.add_row(name, f"[red]{status}[/red]")

                console.print(table)
                console.print()
                info(f"[red]{len(failures_from_artifacts)}[/red] building(s) on fire.")
                info("See them burning in the 3D city — a truck is dispatched per fire.")
                return

        info("No failures. All green. (No fires in the city.)")
        return

    table = Table(show_header=True, header_style="bold red")
    table.add_column("Model", style="bold")
    table.add_column("Type", style="dim")
    table.add_column("Status")

    for name, res_type, status in failures:
        table.add_row(name, res_type, f"[red]{status}[/red]")

    console.print(table)
    console.print()
    info(f"[red]{len(failures)}[/red] building(s) on fire.")
    info("Each has a fire truck en route in the 3D city — awaiting response, not being fixed.")


@app.command()
def firehouse() -> None:
    """Show dispatch stats: station location, trucks and vans on duty.

    Mirrors the firehouse and its two fleets in the 3D city: one red fire
    truck per burning building (failing test), one amber contractor van per
    stale source (freshness SLA warn/error). A vehicle on the street restates
    a measured, unresolved fact — it never means a fix is running.

    The station's map location comes from an exported ``city.json`` when one
    exists; the fleet counts fall back to the metadata DB otherwise, because
    they are facts about the data, not about the map.
    """
    if not config.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    header("Firehouse")

    city_path = config.root / "city.json"
    metadata_db = _metadata_db()

    # Station location — a map fact, so it needs an exported map.
    fh = _firehouse_info(city_path)
    if fh:
        console.print(Panel(f"Firehouse at ({fh['x']}, {fh['y']})", expand=False))
    else:
        info("No exported city.json, so no station coordinates — run [bold]tycoon city[/bold] to see it on the map.")

    # Dispatch stats from city.json
    stats = _dispatch_stats_from_city(city_path)
    if stats:
        console.print()
        console.print(Panel("[bold]Dispatch Stats[/bold]", expand=False))

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric")
        table.add_column("Count", justify="right")

        table.add_row("Fire trucks on duty (one per fire)", str(stats["fires"]))
        table.add_row("Contractor vans on duty (one per stale source)", str(stats["repairs"]))

        console.print(table)
        console.print()
        info("A vehicle on the street means a problem is awaiting response — never that a fix is running.")
        return

    # Fallback: compute from metadata DB
    if metadata_db:
        failures = _failing_tests_from_history(metadata_db)
        freshness = _source_freshness_from_history(metadata_db)

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric")
        table.add_column("Count", justify="right")

        table.add_row("Fire trucks on duty (one per fire)", str(len(failures)))
        table.add_row("Contractor vans on duty (one per stale source)", str(len(freshness)))

        console.print(table)
        console.print()
        info("A vehicle on the street means a problem is awaiting response — never that a fix is running.")
        return

    info("No data available. Run [bold]tycoon data transform[/bold] to capture data.")


@app.command()
def repair() -> None:
    """The contractor call sheet: stale sources past their freshness SLA.

    Mirrors the amber contractor vans in the 3D city — each source past its
    SLA (warn or error) gets one van dispatched, its building weathers to a
    worn facade, and the districts it feeds sit under fog. The CLI and the
    city show the **same data**, just in different formats; a van restates
    the SLA verdict, it never means a fix is running.
    """
    if not config.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    header("Repairs")

    metadata_db = _metadata_db()
    if not metadata_db:
        info("No metadata database found. Run [bold]tycoon data transform[/bold] to capture source freshness.")
        return

    freshness = _source_freshness_from_history(metadata_db)

    if not freshness:
        info("All sources within SLA. (No contractor vans dispatched, no fog over the districts.)")
        return

    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("Source", style="bold")
    table.add_column("Status")
    table.add_column("Last Loaded")

    for name, status, loaded in freshness:
        status_color = "yellow" if status == "warn" else "red"
        loaded_str = str(loaded) if loaded else "—"
        table.add_row(name, f"[{status_color}]{status}[/{status_color}]", loaded_str)

    console.print(table)
    console.print()
    info(f"[yellow]{len(freshness)}[/yellow] source(s) past SLA. One contractor van dispatched per call.")
    info("In the city: worn facades on these sources, fog over the districts they feed.")
