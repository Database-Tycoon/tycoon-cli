"""tycoon data layers: CLI view of the layered architecture with vendor info.

This command mirrors the **same data** the 3D city renders (via city.json)
but presents it in text form. It shows every classified object with its
layer (source → staging → intermediate → marts) and its vendor (dlt,
fivetran, dbt), so a user can inspect the architecture without opening
the browser.

The existing ``tycoon data status`` command shows a **layered health view**
but does not distinguish vendors in the dbt-side panels. This command fills
that gap: every object is tagged with who created it, and sources are
grouped by vendor (dlt vs. fivetran) in the Sources panel.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from tycoon.config import load_config
from tycoon.layers import (
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
from tycoon.observability.dbt_builds import latest_successful_build
from tycoon.project import TransformationTool
from tycoon.utils.console import console, error, header, info

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


def _freshness_label(last_sync: datetime.datetime | None) -> tuple[str, str]:
    """Return (label, style) describing how fresh a sync is."""
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


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------


def layers() -> None:
    """Show the layered architecture with vendor info.

    Layers are the city's RINGS: marts build downtown against the civic
    core, intermediate and staging ring outward from it, and sources sit on
    the outskirts. (Districts are a different thing on the map: one plate
    per schema.) This command lists the same objects ring by ring and adds
    the vendor each one comes from: dlt sources, Fivetran connectors, and
    dbt models.

    This is the **same data** the 3D city renders; the CLI and the city
    show the same architecture, just in different formats.
    """
    cfg = load_config()
    if not cfg.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    project = cfg.project
    assert project is not None  # narrowed by has_project_file

    header("Layers")
    metadata_db = metadata_db_path(cfg.root)

    # ---- Sources panel (dlt + Fivetran unified with vendor) ----
    dlt_sources = classify_dlt_sources(project.sources)
    fivetran_sources: list[LayerClassification] = []
    if project.stack.ingestion.value == "fivetran":
        from tycoon.ingestion.fivetran_sync import latest_connector_snapshot

        fivetran_sources = classify_fivetran_sources(latest_connector_snapshot(metadata_db))

    _render_sources_panel([*dlt_sources, *fivetran_sources], metadata_db=metadata_db)

    # ---- dbt-side layers ----
    if project.stack.transformation == TransformationTool.none:
        console.print()
        info(
            "No dbt project; set up via [bold]tycoon register dbt[/bold] "
            "or [bold]tycoon register dbt --create[/bold] to surface the "
            "staging / intermediate / marts layers."
        )
        return

    manifest = load_manifest(cfg.dbt_project_dir)
    if manifest is None:
        console.print()
        info(
            "No dbt manifest yet; run [bold]tycoon data transform run[/bold] "
            "(or [bold]dbt compile[/bold]) to surface staging / intermediate / "
            "marts panels."
        )
        return

    models = classify_dbt_models(manifest)

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
        empty_hint=("No intermediate models. Optional layer, typically used to combine staging models before marts."),
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
# Panel renderers
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

    last_build = latest_successful_build(metadata_db, [m.identifier.removeprefix("dbt:") for m in models])
    fresh_label, fresh_style = _freshness_label(last_build)

    table = Table(show_header=True, header_style="cyan")
    table.add_column("Model", style="bold")
    table.add_column("Schema", style="dim")
    table.add_column("Vendor", style="dim")

    for m in models:
        table.add_row(m.name, m.schema or "—", m.vendor.value)

    summary = f"{len(models)} model(s), last build [{fresh_style}]{fresh_label}[/{fresh_style}]"
    console.print(table)
    console.print(summary)
