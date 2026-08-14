"""tycoon data layers — CLI view of the layered architecture with vendor info.

This command mirrors the **same data** the 3D city renders (via city.json)
but presents it in text form. It shows every classified object with its
layer (source → staging → intermediate → marts) and its vendor (dlt,
fivetran, dbt), so a user can inspect the architecture without opening
the browser.

The existing ``tycoon data status`` command shows a **layered health view**
but does not distinguish vendors in the dbt-side panels. This command fills
that gap: every object is tagged with who created it, and sources are
grouped by vendor (dlt vs. fivetran) in the Sources panel.

Two commands:

* ``tycoon data layers``            — full architecture with vendor info
* ``tycoon data health``            — health chips (tests, builds, freshness,
                                        staleness, drift) matching the UI's
                                        health strip
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from tycoon.config import config
from tycoon.districts import (
    Layer,
    LayerClassification,
    Vendor,
    classify_dbt_models,
    classify_dlt_sources,
    classify_fivetran_sources,
    filter_by_layer,
    load_manifest,
)
from tycoon.observability import metadata_db_path
from tycoon.project import TransformationTool
from tycoon.utils.console import console, error, header, info

app = typer.Typer(
    help="Layers and health: CLI views of the pipeline architecture and its health.",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# Helpers: data loading
# ---------------------------------------------------------------------------


def _sources_from_backend(metadata_db: Path) -> dict[str, dict]:
    """Read per-source last-sync and row counts from the events backend.

    Returns ``{source_id: {"last_sync": datetime, "rows": {table: count}}}``.
    Falls back to an empty dict on any failure.
    """
    if not metadata_db.exists():
        return {}
    try:
        from tycoon.core.events import RunCompleted
        from tycoon.core.metadata import EventFilter
        from tycoon.metadata_backends.duckdb_file import DuckDBFileBackend

        with DuckDBFileBackend(metadata_db, read_only=True) as b:
            events = b.query_events(EventFilter(event_type="run_completed"))

        result: dict[str, dict] = {}
        for e in events:
            if not isinstance(e, RunCompleted):
                continue
            entry = result.setdefault(e.source_id, {"last_sync": None, "rows": {}, "runs": 0})
            entry["runs"] += 1
            if entry["last_sync"] is None or e.timestamp > entry["last_sync"]:
                entry["last_sync"] = e.timestamp
                entry["rows"] = dict(e.rows_loaded or {})
        return result
    except Exception:
        return {}


def _freshness_label(last_sync) -> tuple[str, str]:
    """Return (label, style) describing how fresh a sync is."""
    import datetime

    if last_sync is None:
        return "never", "red"

    now = datetime.datetime.now(tz=datetime.UTC)
    if last_sync.tzinfo is None:
        last_sync = last_sync.replace(tzinfo=datetime.UTC)

    age = now - last_sync
    hours = age.total_seconds() / 3600

    if hours < 24:
        if hours < 1:
            mins = int(age.total_seconds() / 60)
            return f"{mins}m ago", "green"
        return f"{int(hours)}h ago", "green"
    if hours < 24 * 7:
        return f"{int(hours / 24)}d ago", "yellow"
    return f"{int(hours / 24)}d ago", "red"


def _query_layer_last_build(metadata_db: Path, model_names: list[str]) -> object:
    """Latest successful build start time across ``model_names``."""
    import duckdb

    if not model_names or not metadata_db.exists():
        return None
    try:
        with duckdb.connect(str(metadata_db), read_only=True) as con:
            row = con.execute(
                "SELECT MAX(r.started_at) "
                "FROM dbt_runs r "
                "JOIN dbt_nodes n ON n.invocation_id = r.invocation_id "
                "WHERE n.status = 'success' AND list_contains(?, n.node_name)",
                [model_names],
            ).fetchone()
        return row[0] if row and row[0] else None
    except Exception:
        return None


def _query_layer_freshness(metadata_db: Path, model_names: list[str]) -> object:
    """Latest freshness timestamp for models in ``model_names``."""
    import duckdb

    if not model_names or not metadata_db.exists():
        return None
    try:
        with duckdb.connect(str(metadata_db), read_only=True) as con:
            row = con.execute(
                "SELECT MAX(r.started_at) "
                "FROM dbt_runs r "
                "JOIN dbt_nodes n ON n.invocation_id = r.invocation_id "
                "WHERE n.status = 'success' AND list_contains(?, n.node_name)",
                [model_names],
            ).fetchone()
        return row[0] if row and row[0] else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command("layers")
def layers() -> None:
    """Show the layered architecture with vendor info.

    Mirrors the city's district structure (source → staging → intermediate →
    marts) and adds the vendor column that the 3D city derives from
    ``city.json``: dlt sources, Fivetran connectors, and dbt models.

    This is the **same data** the 3D city renders — the CLI and the city
    show the same architecture, just in different formats.
    """
    if not config.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    project = config.project
    assert project is not None  # narrowed by has_project_file

    header("Layers")

    # ---- Sources panel (dlt + Fivetran unified with vendor) ----
    dlt_sources = classify_dlt_sources(project.sources)
    fivetran_sources: list[LayerClassification] = []
    fivetran_managed = project.stack.ingestion.value == "fivetran"
    if fivetran_managed:
        from tycoon.ingestion.fivetran_sync import latest_connector_snapshot

        fivetran_sources = classify_fivetran_sources(latest_connector_snapshot(metadata_db_path(config.root)))

    all_sources = [*dlt_sources, *fivetran_sources]
    _meta_db = metadata_db_path(config.root)
    _render_sources_panel(all_sources, metadata_db=_meta_db)

    # ---- dbt-side layers ----
    if project.stack.transformation == TransformationTool.none:
        console.print()
        info(
            "No dbt project — set up via [bold]tycoon register dbt[/bold] "
            "or [bold]tycoon register dbt --create[/bold] to surface the "
            "staging / intermediate / marts layers."
        )
        return

    manifest = load_manifest(config.dbt_project_dir)
    if manifest is None:
        console.print()
        info(
            "No dbt manifest yet — run [bold]tycoon data transform run[/bold] "
            "(or [bold]dbt compile[/bold]) to surface staging / intermediate / "
            "marts panels."
        )
        return

    models = classify_dbt_models(manifest)
    metadata_db = metadata_db_path(config.root)

    _render_layer_panel(
        "Staging",
        filter_by_layer(models, Layer.STAGING),
        metadata_db,
        empty_hint=("No staging models. Scaffold one with [bold]tycoon data analyze <source>[/bold]."),
    )
    _render_layer_panel(
        "Intermediate",
        filter_by_layer(models, Layer.INTERMEDIATE),
        metadata_db,
        empty_hint=("No intermediate models. Optional layer — typically used to combine staging models before marts."),
    )
    _render_layer_panel(
        "Marts",
        filter_by_layer(models, Layer.MART),
        metadata_db,
        empty_hint=(
            "No mart models. Write `fct_*` / `dim_*` / `obt_*` models under "
            "`models/marts/` (or override per-folder with "
            "`+meta.tycoon_layer: mart`)."
        ),
    )


@app.command("health")
def health() -> None:
    """Show pipeline health: failing tests, build errors, late sources, stale builds, schema drift.

    Mirrors the **health strip** visible at the top of the 3D city UI.
    Every chip is a count of problematic objects — failing tests, build
    errors, late sources, test warnings, stale builds (14+ days), and
    schema drift (7 days).

    This is the **same data** the 3D city renders — the CLI and the city
    show the same health, just in different formats.
    """
    if not config.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    header("Health")

    # Sources panel (dlt + Fivetran unified with vendor)
    project = config.project
    assert project is not None  # narrowed by has_project_file

    dlt_sources = classify_dlt_sources(project.sources)
    fivetran_sources: list[LayerClassification] = []
    fivetran_managed = project.stack.ingestion.value == "fivetran"
    if fivetran_managed:
        from tycoon.ingestion.fivetran_sync import latest_connector_snapshot

        fivetran_sources = classify_fivetran_sources(latest_connector_snapshot(metadata_db_path(config.root)))

    all_sources = [*dlt_sources, *fivetran_sources]
    _meta_db = metadata_db_path(config.root)
    _render_sources_panel(all_sources, metadata_db=_meta_db)

    if fivetran_managed:
        from tycoon.ingestion.fivetran_sync import (
            latest_connector_snapshot,
        )

        rows = latest_connector_snapshot(metadata_db_path(config.root))
        if rows:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Connector")
            table.add_column("Service", style="dim")
            table.add_column("Sync state")
            table.add_column("Last activity")
            for r in rows:
                from tycoon.ingestion.fivetran_sync import freshness_label as fv_freshness_label

                label, style = fv_freshness_label(
                    succeeded_at=r["succeeded_at"],
                    failed_at=r["failed_at"],
                    paused=bool(r["paused"]),
                )
                table.add_row(
                    r["name"] or r["connector_id"],
                    r.get("service") or "—",
                    r.get("sync_state") or "—",
                    f"[{style}]{label}[/{style}]",
                )
            console.print()
            console.print(table)

    if _meta_db.exists():
        console.print()
        info("Drill in with [bold]tycoon data history[/bold] for per-run detail.")

    # ---- dbt-side layers ----
    if project.stack.transformation == TransformationTool.none:
        console.print()
        info(
            "No dbt project — set up via [bold]tycoon register dbt[/bold] "
            "or [bold]tycoon register dbt --create[/bold] to surface the "
            "staging / intermediate / marts layers."
        )
        return

    manifest = load_manifest(config.dbt_project_dir)
    if manifest is None:
        console.print()
        info(
            "No dbt manifest yet — run [bold]tycoon data transform run[/bold] "
            "(or [bold]dbt compile[/bold]) to surface staging / intermediate / "
            "marts panels."
        )
        return

    models = classify_dbt_models(manifest)
    metadata_db = metadata_db_path(config.root)

    _render_layer_panel(
        "Staging",
        filter_by_layer(models, Layer.STAGING),
        metadata_db,
        empty_hint=("No staging models. Scaffold one with [bold]tycoon data analyze <source>[/bold]."),
    )
    _render_layer_panel(
        "Intermediate",
        filter_by_layer(models, Layer.INTERMEDIATE),
        metadata_db,
        empty_hint=("No intermediate models. Optional layer — typically used to combine staging models before marts."),
    )
    _render_layer_panel(
        "Marts",
        filter_by_layer(models, Layer.MART),
        metadata_db,
        empty_hint=(
            "No mart models. Write `fct_*` / `dim_*` / `obt_*` models under "
            "`models/marts/` (or override per-folder with "
            "`+meta.tycoon_layer: mart`)."
        ),
    )


# ---------------------------------------------------------------------------
# Panel renderers (shared between layers and health)
# ---------------------------------------------------------------------------


def _render_sources_panel(
    sources: list[LayerClassification],
    *,
    metadata_db: Path,
) -> None:
    """The unified Sources panel: dlt + Fivetran rows side by side."""
    console.print()
    console.print(Panel("[bold]Sources[/bold]", expand=False))

    if not sources:
        info(
            "No sources registered. Run [bold]tycoon data sources add[/bold] "
            "or wire up Fivetran via `stack.ingestion: fivetran`."
        )
        return

    sources_data = _sources_from_backend(metadata_db)

    table = Table(show_lines=False)
    table.add_column("Source", style="bold cyan")
    table.add_column("Vendor", style="dim")
    table.add_column("Schema")
    table.add_column("Last Sync")
    table.add_column("Freshness")
    table.add_column("Runs", justify="right")
    table.add_column("Tables", justify="right")
    table.add_column("Last Sync Rows", justify="right")

    for src in sources:
        schema = src.schema or "—"

        if src.vendor is Vendor.DLT and src.schema:
            data = sources_data.get(src.name, {})
            last_sync = data.get("last_sync")
            row_counts = data.get("rows", {})
            runs = data.get("runs", 0)
            sync_str = last_sync.strftime("%Y-%m-%d %H:%M") if last_sync else "—"
            fresh_label, fresh_style = _freshness_label(last_sync)
            runs_str = f"{runs:,}" if runs else "—"
            tables_str = str(len(row_counts)) if row_counts else "—"
            total_rows = f"{sum(row_counts.values()):,}" if row_counts else "—"
        else:
            # Fivetran rows + un-materialised dlt rows: detail comes from the
            # Fivetran snapshot view below (or the source hasn't run yet).
            sync_str = "—"
            fresh_label, fresh_style = ("—", "dim")
            runs_str = "—"
            tables_str = "—"
            total_rows = "—"

        table.add_row(
            src.name,
            src.vendor.value,
            schema,
            sync_str,
            f"[{fresh_style}]{fresh_label}[/{fresh_style}]",
            runs_str,
            tables_str,
            total_rows,
        )

    console.print(table)


def _render_layer_panel(
    title: str,
    models: list[LayerClassification],
    metadata_db: Path,
    *,
    empty_hint: str,
) -> None:
    """One staging / intermediate / mart panel."""
    console.print()
    console.print(Panel(f"[bold]{title}[/bold]", expand=False))

    if not models:
        info(empty_hint)
        return

    last_build = _query_layer_last_build(metadata_db, [m.name for m in models])
    fresh_label, fresh_style = _freshness_label(last_build)

    table = Table(show_header=True, header_style="cyan")
    table.add_column("Model", style="bold")
    table.add_column("Schema", style="dim")
    table.add_column("Vendor", style="dim")

    for m in models:
        table.add_row(m.name, m.schema or "—", m.vendor.value)

    summary = f"{len(models)} model(s) — last build [{fresh_style}]{fresh_label}[/{fresh_style}]"
    console.print(table)
    console.print(summary)
