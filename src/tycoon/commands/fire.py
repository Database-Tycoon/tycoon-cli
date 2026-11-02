"""tycoon fire / firehouse: CLI views of the city's fire-and-response system.

These commands read the **same data** the 3D city renders: the observability
metadata DB for run history, falling back to dbt's own ``run_results.json``.
They present it as text so a user can check "what's burning?" without opening
the browser.

The city's vocabulary, kept exactly (see `web/src/ui/legend.ts` and the tour):
a failing test sets its building ON FIRE and the firehouse dispatches one red
**fire truck** per fire. A truck on the street restates a measured, unresolved
fact: a problem is AWAITING response, never that a fix is running.

Three views:

* ``tycoon fire``:            what's burning right now (latest run)
* ``tycoon fire --run <id>``: what was burning in a specific run (replay)
* ``tycoon firehouse``:       dispatch stats: trucks on duty
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import typer
from rich.table import Table

from tycoon.config import TycoonConfig, load_config
from tycoon.observability import metadata_db_path
from tycoon.utils.console import console, error, header, info

_FIRE_STATUSES = ("fail", "error")


def _short_name(unique_id: str) -> str:
    """The name dbt gives a node, without its project prefix or a test's hash suffix.

    dbt ids read ``<type>.<project>.<name>`` for models and
    ``test.<project>.<name>.<hash>`` for tests, so the name is always the third
    segment when there is one.
    """
    parts = unique_id.split(".")
    return parts[2] if len(parts) > 2 else parts[-1]


def _fires_from_run_results(dbt_dir: Path) -> list[tuple[str, str]] | None:
    """Failing tests from dbt's own ``run_results.json``, or None when there is no run.

    Statuses live in ``run_results.json``; ``manifest.json`` describes the
    project and never carries them (the same distinction the city's loader
    makes). A model that errored is a build failure, not a fire: the city
    sets a building on fire only for a failing test (``blocks.py``).
    """
    results_path = dbt_dir / "target" / "run_results.json"
    if not results_path.exists():
        return None
    try:
        data = json.loads(results_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None

    fires: list[tuple[str, str]] = []
    for result in data.get("results", []):
        unique_id = str(result.get("unique_id", ""))
        status = str(result.get("status", "")).lower()
        if unique_id.startswith("test.") and status in _FIRE_STATUSES:
            fires.append((_short_name(unique_id), status))
    return fires


def _latest_invocation(metadata_db: Path, prefix: str = "") -> str | None:
    """The newest captured run whose invocation id starts with ``prefix``.

    Ordered by ``started_at``: invocation ids are random UUIDs, so their order
    says nothing about which run came last.
    """
    try:
        with duckdb.connect(str(metadata_db), read_only=True) as con:
            row = con.execute(
                "SELECT invocation_id FROM dbt_runs WHERE invocation_id LIKE ? ORDER BY started_at DESC LIMIT 1",
                [prefix + "%"],
            ).fetchone()
    except Exception:
        return None
    return row[0] if row else None


def _fires_in_run(metadata_db: Path, invocation_id: str) -> list[tuple[str, str]]:
    """Failing tests captured for one run, as ``[(name, status), ...]``."""
    try:
        with duckdb.connect(str(metadata_db), read_only=True) as con:
            rows = con.execute(
                "SELECT node_name, status FROM dbt_nodes "
                "WHERE invocation_id = ? AND resource_type = 'test' AND status IN ('fail', 'error') "
                "ORDER BY node_name",
                [invocation_id],
            ).fetchall()
    except Exception:
        return []
    return [(_short_name(name), status) for name, status in rows]


def _standing_fires(cfg: TycoonConfig) -> list[tuple[str, str]] | None:
    """Failing tests from the most recent run, or None when nothing has run yet."""
    metadata_db = metadata_db_path(cfg.root)
    if metadata_db.exists():
        latest = _latest_invocation(metadata_db)
        if latest:
            return _fires_in_run(metadata_db, latest)
    return _fires_from_run_results(cfg.dbt_project_dir)


def _require_project() -> TycoonConfig:
    cfg = load_config()
    if not cfg.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)
    return cfg


def _print_fires(fires: list[tuple[str, str]]) -> None:
    table = Table(show_header=True, header_style="bold red")
    table.add_column("Test", style="bold")
    table.add_column("Status")
    for name, status in fires:
        table.add_row(name, f"[red]{status}[/red]")
    console.print(table)
    console.print()


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
    words): the CLI and the city show the **same data**, just in different
    formats. A fire is a fact awaiting response, never a fix in progress.

    Use ``--run`` to inspect failures from a specific invocation instead of
    the standing (latest) state.
    """
    cfg = _require_project()
    header("Fires")

    if run:
        metadata_db = metadata_db_path(cfg.root)
        if not metadata_db.exists():
            info("No metadata database found. Run [bold]tycoon data transform run[/bold] to capture run history.")
            return
        invocation_id = _latest_invocation(metadata_db, run)
        if not invocation_id:
            info(f"No run found matching '{run}'.")
            return
        fires = _fires_in_run(metadata_db, invocation_id)
        if not fires:
            info("No failures in this run. All green. (No fires in the city.)")
            return
        _print_fires(fires)
        info(f"[red]{len(fires)}[/red] building(s) on fire in this run.")
        info("The run replay in the 3D city shows these same buildings burning.")
        return

    fires = _standing_fires(cfg)
    if not fires:
        info("No failures. All green. (No fires in the city.)")
        return
    _print_fires(fires)
    info(f"[red]{len(fires)}[/red] building(s) on fire.")
    info("Each has a fire truck en route in the 3D city, awaiting response, not being fixed.")


def firehouse() -> None:
    """Show dispatch stats: fire trucks on duty.

    Mirrors the firehouse in the 3D city: one red fire truck per burning
    building (failing test). A vehicle on the street restates a measured,
    unresolved fact; it never means a fix is running.
    """
    cfg = _require_project()
    header("Firehouse")

    fires = _standing_fires(cfg)
    if fires is None:
        info("No data available. Run [bold]tycoon data transform run[/bold] to capture a run.")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    table.add_column("Count", justify="right")
    table.add_row("Fire trucks on duty (one per fire)", str(len(fires)))
    console.print(table)
    console.print()
    info("A vehicle on the street means a problem is awaiting response, never that a fix is running.")
