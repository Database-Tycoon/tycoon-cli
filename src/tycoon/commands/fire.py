"""tycoon fire / firehouse / repair — CLI views of the city's fire-and-response system.

These commands read from the **same data sources** the 3D city renders: the dbt
manifest for test results, the observability metadata DB for run history and
source freshness. They present that data in text form so a user can check
"what's burning?" or "what needs repair?" without opening the browser.

Four commands:

* ``tycoon fire``            — what's failing right now (test_status = "fail")
* ``tycoon fire --run <id>`` — what was failing in a specific run (replay)
* ``tycoon repair``          — what sources are past their SLA (freshness)
* ``tycoon firehouse``       — dispatch stats: firehouse location, engines on
                               duty, vans on duty, unreachable buildings
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


def _failing_tests_from_manifest(path: Path) -> list[tuple[str, str]]:
    """Failing test results from the latest dbt manifest.

    Returns ``[(object_key, test_name), ...]`` for every test with
    ``status == 'fail'`` or ``status == 'error'``.
    """
    import json

    manifest_path = path / "target" / "manifest.json"
    if not manifest_path.exists():
        return []
    try:
        data = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError):
        return []

    results = data.get("nodes", {})
    results.update(data.get("sources", {}))
    results.update(data.get("metrics", {}))

    failing: list[tuple[str, str]] = []
    for unique_id, node in results.items():
        status = node.get("status", "").lower()
        if status in ("fail", "error"):
            # Get the model name from the node
            name = node.get("name", unique_id)
            # Get the test name if this is a test node
            test_name = node.get("test_name") or node.get("name", "")
            failing.append((name, test_name))

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


def _firehouse_info(metadata_db: Path) -> dict:
    """Firehouse dispatch info from the city.json (if available).

    Returns a dict with firehouse location and dispatch stats.
    """
    import json

    city_path = config.root / "city.json"
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
    """Dispatch stats from the city.json.

    Counts buildings with ``test_status == 'fail'`` (fires) and
    ``freshness_status in ('warn', 'error')`` (needs repair).
    """
    import json

    if not city_path.exists():
        return {}
    try:
        data = json.loads(city_path.read_text())
        lots = data.get("lots", [])

        fire_count = sum(1 for lot in lots if lot.get("test_status") == "fail")
        repair_count = sum(1 for lot in lots if lot.get("freshness_status") in ("warn", "error"))
        unreachable = sum(1 for lot in lots if lot.get("unreachable", False))

        return {
            "fires": fire_count,
            "repairs": repair_count,
            "unreachable": unreachable,
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

    Mirrors the red flames visible in the 3D city. Each failing test
    corresponds to a building on fire in the city — the CLI and the city
    show the **same data**, just in different formats.

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
        # Specific run: look up the invocation ID
        if not metadata_db:
            info("No metadata database found. Run [bold]tycoon data transform[/bold] to capture run history.")
            return

        import duckdb

        try:
            with duckdb.connect(str(metadata_db), read_only=True) as con:
                row = con.execute("SELECT invocation_id FROM dbt_runs ORDER BY started_at DESC LIMIT 1").fetchone()
                if not row:
                    info("No runs recorded yet.")
                    return
                invocation_id = row[0]
        except Exception:
            info("Could not read run history.")
            return

        failures = _run_failures_from_history(metadata_db, invocation_id)

        if not failures:
            info("No failures in this run. All green. (No flames in the city.)")
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
        info("See the red flames on the corresponding buildings in the 3D city.")
        return

    # Standing state: latest run's failures
    failures: list[tuple[str, str, str]] = []
    if metadata_db:
        failures = _failing_tests_from_history(metadata_db)

    if not failures:
        # Fallback: try manifest
        if dbt_dir.exists():
            failures_from_manifest = _failing_tests_from_manifest(dbt_dir)
            if failures_from_manifest:
                table = Table(show_header=True, header_style="bold red")
                table.add_column("Model", style="bold")
                table.add_column("Test")

                for name, test_name in failures_from_manifest:
                    table.add_row(name, test_name)

                console.print(table)
                console.print()
                info(f"[red]{len(failures_from_manifest)}[/red] building(s) on fire.")
                info("See the red flames on the corresponding buildings in the 3D city.")
                return

        info("No failures. All green. (No flames in the city.)")
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
    info("See the red flames on the corresponding buildings in the 3D city.")


@app.command()
def firehouse() -> None:
    """Show dispatch stats: firehouse location, engines and vans on duty.

    Mirrors the firehouse building and dispatch fleets (FireTrucks +
    RepairVans) visible in the 3D city. Shows:

    - Firehouse location (from city.json)
    - Red engines on duty (count of failing tests)
    - Amber vans on duty (count of stale sources)
    - Unreachable buildings (orphaned objects with no road access)
    """
    if not config.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    header("Firehouse")

    city_path = config.root / "city.json"
    metadata_db = _metadata_db()

    # Firehouse location
    fh = _firehouse_info(city_path)
    if fh:
        console.print(Panel(f"Firehouse at ({fh['x']}, {fh['y']})", expand=False))
    else:
        info("No firehouse defined (city.json missing or no firehouse key).")

    # Dispatch stats from city.json
    stats = _dispatch_stats_from_city(city_path)
    if stats:
        console.print()
        console.print(Panel("[bold]Dispatch Stats[/bold]", expand=False))

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric")
        table.add_column("Count", justify="right")

        table.add_row("Red engines on duty", str(stats["fires"]))
        table.add_row("Amber vans on duty", str(stats["repairs"]))
        table.add_row("Unreachable buildings", str(stats["unreachable"]))

        console.print(table)
        return

    # Fallback: compute from metadata DB
    if metadata_db:
        failures = _failing_tests_from_history(metadata_db)
        freshness = _source_freshness_from_history(metadata_db)

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric")
        table.add_column("Count", justify="right")

        table.add_row("Red engines on duty", str(len(failures)))
        table.add_row("Amber vans on duty", str(len(freshness)))
        table.add_row("Unreachable buildings", "0")

        console.print(table)
        return

    info("No data available. Run [bold]tycoon data transform[/bold] to capture data.")


@app.command()
def repair() -> None:
    """Show what needs repair: stale sources past their freshness SLA.

    Mirrors the amber repair vans visible in the 3D city. Each source past
    its SLA (warn or error) gets an amber van dispatched — the CLI and the
    city show the **same data**, just in different formats.
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
        info("All sources within SLA. (No amber vans dispatched.)")
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
    info(f"[yellow]{len(freshness)}[/yellow] source(s) past SLA. Amber vans dispatched.")
    info("See the amber vans on the corresponding sources in the 3D city.")
