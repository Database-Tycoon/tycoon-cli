"""tycoon fire / firehouse: CLI views of the city's fire-and-response system.

These commands read the same data the 3D city renders: the observability
metadata DB for run history, falling back to dbt's own ``run_results.json``.
They present it as text so a user can check what is failing without opening
the browser.

The city's rule, kept exactly (see `web/src/ui/legend.ts` and the tour): a
failing test sets its building on fire and the firehouse dispatches one fire
truck per fire. A truck restates a measured, unresolved fact: a problem is
awaiting response, never that a fix is running. A model that failed to build
is not a fire, so these commands point at ``tycoon data history`` for those
instead of reporting the build as healthy.

The standing state folds every captured run down to each test's newest
result, as the city's run history does (``node_results`` in
``tycoon_city/catalog/run_history.py``): a ``dbt run`` that ran no tests
leaves the last test results standing.

Three views:

* ``tycoon fire``:            failing tests now (each test's newest result)
* ``tycoon fire --run <id>``: failing tests in one run (replay)
* ``tycoon firehouse``:       dispatch stats: trucks on duty
"""

from __future__ import annotations

import datetime
import json
from dataclasses import dataclass
from pathlib import Path

import duckdb
import typer
from rich.markup import escape
from rich.table import Table

from tycoon.config import TycoonConfig, load_config
from tycoon.observability import metadata_db_path
from tycoon.utils.console import console, error, header, info, warn

_FIRE_STATUSES = ("fail", "error")

# How long before its DbtRunCompleted event a run's dbt_runs row may have been
# captured. Both are written by one `tycoon data transform` call, capture
# first, with only the Rill dashboard refresh in between.
_EVENT_CAPTURE_WINDOW = datetime.timedelta(minutes=10)


@dataclass(frozen=True)
class _Findings:
    """Failing tests, plus models that failed to build, for one view."""

    fires: list[tuple[str, str]]
    models_errored: int = 0


def _short_name(unique_id: str) -> str:
    """The name dbt gives a node, without its project prefix or a test's hash suffix.

    dbt ids read ``<type>.<project>.<name>`` for models and
    ``test.<project>.<name>.<hash>`` for tests, so the name is always the third
    segment when there is one.
    """
    parts = unique_id.split(".")
    return parts[2] if len(parts) > 2 else parts[-1]


def _findings_from_run_results(dbt_dir: Path) -> _Findings | None:
    """Failing tests from dbt's own ``run_results.json``, or None when there is no run.

    Statuses live in ``run_results.json``; ``manifest.json`` describes the
    project and never carries them (the same distinction the city's loader
    makes).
    """
    results_path = dbt_dir / "target" / "run_results.json"
    if not results_path.exists():
        return None
    try:
        data = json.loads(results_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None

    fires: list[tuple[str, str]] = []
    models_errored = 0
    for result in data.get("results", []):
        unique_id = str(result.get("unique_id", ""))
        status = str(result.get("status", "")).lower()
        if unique_id.startswith("test.") and status in _FIRE_STATUSES:
            fires.append((_short_name(unique_id), status))
        elif unique_id.startswith("model.") and status == "error":
            models_errored += 1
    return _Findings(sorted(fires), models_errored)


def _standing_findings_from_metadata(metadata_db: Path) -> _Findings | None:
    """Each node's newest captured result, or None when no run is captured."""
    newest = (
        "SELECT n.node_name, arg_max(n.status, r.started_at) AS status "
        "FROM dbt_nodes n JOIN dbt_runs r ON r.invocation_id = n.invocation_id "
        "WHERE n.resource_type = ? GROUP BY n.node_name"
    )
    try:
        with duckdb.connect(str(metadata_db), read_only=True) as con:
            if con.execute("SELECT COUNT(*) FROM dbt_runs").fetchone()[0] == 0:
                return None
            tests = con.execute(
                f"SELECT node_name, status FROM ({newest}) WHERE status IN ('fail', 'error') ORDER BY node_name",
                ["test"],
            ).fetchall()
            models = con.execute(f"SELECT COUNT(*) FROM ({newest}) WHERE status = 'error'", ["model"]).fetchone()
    except Exception:
        return None
    return _Findings([(_short_name(name), status) for name, status in tests], models[0] if models else 0)


def _standing_findings(cfg: TycoonConfig) -> _Findings | None:
    """What is failing now, or None when nothing has run yet."""
    metadata_db = metadata_db_path(cfg.root)
    if metadata_db.exists():
        findings = _standing_findings_from_metadata(metadata_db)
        if findings is not None:
            return findings
    return _findings_from_run_results(cfg.dbt_project_dir)


def _invocations_by_prefix(metadata_db: Path, prefix: str) -> list[str]:
    """Captured invocation ids starting with ``prefix``, newest first.

    ``starts_with`` rather than ``LIKE``: a ``%`` or ``_`` in the prefix is a
    character to match, not a wildcard.
    """
    try:
        with duckdb.connect(str(metadata_db), read_only=True) as con:
            rows = con.execute(
                "SELECT invocation_id FROM dbt_runs WHERE starts_with(invocation_id, ?) ORDER BY started_at DESC",
                [prefix],
            ).fetchall()
    except Exception:
        return []
    return [row[0] for row in rows]


def _invocation_for_history_id(metadata_db: Path, prefix: str) -> list[str]:
    """Map the id `tycoon data history` prints for a dbt run to its invocation id.

    History lists the ``DbtRunCompleted`` event, whose id is not dbt's
    invocation id. The same transform call captures the run into ``dbt_runs``
    moments before it writes the event, so the match is the run with the same
    command captured most recently before the event. Returns a list so an
    ambiguous history prefix can be reported as such.
    """
    try:
        from tycoon.core.events import DbtRunCompleted
        from tycoon.core.metadata import EventFilter
        from tycoon.metadata_backends.duckdb_file import DuckDBFileBackend

        with DuckDBFileBackend(metadata_db, read_only=True) as backend:
            events = backend.query_events(EventFilter(event_type="dbt_run_completed"))
        matches = [e for e in events if isinstance(e, DbtRunCompleted) and e.event_id.startswith(prefix)]
        if len(matches) != 1:
            return [e.event_id for e in matches]
        event = matches[0]
        with duckdb.connect(str(metadata_db), read_only=True) as con:
            # captured_at holds a UTC-aware value written into a naive column;
            # the cast in the same session recovers the instant (see dbt_builds).
            rows = con.execute(
                "SELECT invocation_id, captured_at::TIMESTAMPTZ FROM dbt_runs WHERE command = ?",
                [event.command],
            ).fetchall()
    except Exception:
        return []
    earliest = event.timestamp - _EVENT_CAPTURE_WINDOW
    candidates = [(at, inv) for inv, at in rows if at is not None and earliest <= at <= event.timestamp]
    return [max(candidates)[1]] if candidates else []


def _resolve_run(metadata_db: Path, ref: str) -> str | None:
    """The invocation id ``ref`` names, from either id kind. Exits on an ambiguous prefix."""
    matches = _invocations_by_prefix(metadata_db, ref)
    if not matches:
        matches = _invocation_for_history_id(metadata_db, ref)
    if len(matches) > 1:
        shown = ", ".join(m[:12] for m in matches[:5])
        error(f"'{escape(ref)}' matches {len(matches)} runs ({shown}). Use a longer prefix.")
        raise typer.Exit(1)
    return matches[0] if matches else None


def _run_findings(metadata_db: Path, invocation_id: str) -> tuple[_Findings, str]:
    """Failing tests and model errors in one run, plus the run's command."""
    try:
        with duckdb.connect(str(metadata_db), read_only=True) as con:
            rows = con.execute(
                "SELECT node_name, status FROM dbt_nodes "
                "WHERE invocation_id = ? AND resource_type = 'test' AND status IN ('fail', 'error') "
                "ORDER BY node_name",
                [invocation_id],
            ).fetchall()
            run = con.execute(
                "SELECT COALESCE(models_error, 0), command FROM dbt_runs WHERE invocation_id = ?",
                [invocation_id],
            ).fetchone()
    except Exception:
        return _Findings([]), "dbt"
    fires = [(_short_name(name), status) for name, status in rows]
    models_errored, command = run if run else (0, None)
    return _Findings(fires, models_errored), command or "dbt"


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


def _report_model_errors(models_errored: int, scope: str) -> None:
    """Point at run history when models failed: the fire view never shows them."""
    if models_errored:
        warn(
            f"{models_errored} model(s) failed to build {scope}. "
            "Model failures are not fires; see [bold]tycoon data history[/bold]."
        )


def fire(
    run: str | None = typer.Option(
        None,
        "--run",
        "-r",
        help="Show failing tests in one run. Takes a run id (or prefix) from tycoon data history or from this command.",
    ),
) -> None:
    """Show failing tests, the fires in the 3D city.

    Without --run, each test counts by its newest result across all captured
    runs, so a later run that ran no tests (dbt run) leaves earlier failures
    standing. This matches the city.

    Models that failed to build are not fires; when there are any, the output
    says so and points at tycoon data history.
    """
    cfg = _require_project()
    header("Fires")

    if run:
        metadata_db = metadata_db_path(cfg.root)
        if not metadata_db.exists():
            info("No metadata database found. Run [bold]tycoon data transform run[/bold] to capture run history.")
            return
        invocation_id = _resolve_run(metadata_db, run)
        if not invocation_id:
            info(f"No run found matching '{escape(run)}'. List runs with [bold]tycoon data history[/bold].")
            return
        findings, command = _run_findings(metadata_db, invocation_id)
        info(f"Run: dbt {escape(command)} ({invocation_id[:8]})")
        if findings.fires:
            _print_fires(findings.fires)
            info(f"[red]{len(findings.fires)}[/red] failing test(s) in this run.")
            info("The run replay in the 3D city shows these same buildings burning.")
        else:
            info("No failing tests in this run.")
        _report_model_errors(findings.models_errored, "in this run")
        return

    findings = _standing_findings(cfg)
    if findings is None or not findings.fires:
        info("No failing tests.")
    else:
        _print_fires(findings.fires)
        info(f"[red]{len(findings.fires)}[/red] failing test(s).")
        info("Each is a building on fire in the 3D city, with a truck awaiting response, not being fixed.")
    if findings is not None:
        _report_model_errors(findings.models_errored, "in their latest run")


def firehouse() -> None:
    """Count fire trucks on duty: one per failing test.

    Counts the same failing tests as tycoon fire (each test's newest result).
    In the 3D city each one sends a fire truck from the firehouse; a truck
    means a problem awaits a response, never that a fix is running.
    """
    cfg = _require_project()
    header("Firehouse")

    findings = _standing_findings(cfg)
    if findings is None:
        info("No data available. Run [bold]tycoon data transform run[/bold] to capture a run.")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    table.add_column("Count", justify="right")
    table.add_row("Fire trucks on duty (one per failing test)", str(len(findings.fires)))
    console.print(table)
    console.print()
    info("A vehicle on the street means a problem is awaiting response, never that a fix is running.")
    _report_model_errors(findings.models_errored, "in their latest run")
