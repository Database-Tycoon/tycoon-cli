"""tycoon data status — layer-organized health view.

As of v0.1.7, ``data status`` is the **layered** view of the project:

    Sources -> Staging -> Intermediate -> Marts

dlt sources and Fivetran connectors collapse into a unified **Sources**
panel (the ``Vendor`` column distinguishes them). The remaining panels
read from the dbt manifest via :mod:`tycoon.layers`. Projects with
``transformation: none`` still see the staging / intermediate / marts
panels — populated with empty-state hints pointing at
``tycoon register dbt``.

Per-mart freshness comes from the observability metadata DB (the
``dbt_runs`` / ``dbt_nodes`` tables). The Sources panel keeps the
existing per-source freshness + row-count detail.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Iterable, Optional

import typer
from rich.panel import Panel
from rich.table import Table

from tycoon.config import config
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
from tycoon.project import TransformationTool
from tycoon.utils.console import console, error, header, info, warn


# -- Freshness helpers ---------------------------------------------------------


def _sources_from_backend(metadata_db: Path) -> dict[str, dict]:
    """Read per-source last-sync and row counts from the events backend.

    Returns ``{source_id: {"last_sync": datetime, "rows": {table: count}}}``.
    Falls back to an empty dict on any failure (missing file, missing table,
    legacy schema without an events table).
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
            existing = result.get(e.source_id)
            if existing is None or e.timestamp > existing["last_sync"]:
                result[e.source_id] = {
                    "last_sync": e.timestamp,
                    "rows": dict(e.rows_loaded),
                }
        return result
    except Exception:
        return {}


def _query_run_counts(metadata_db: Path) -> dict[str, int]:
    """Return {source_schema: run_count} from the observability metadata DB."""
    import duckdb

    if not metadata_db.exists():
        return {}
    try:
        con = duckdb.connect(str(metadata_db), read_only=True)
        rows = con.execute(
            "SELECT source_schema, COUNT(*) FROM dlt_runs GROUP BY source_schema"
        ).fetchall()
        con.close()
        return {schema: count for schema, count in rows}
    except Exception:
        return {}


def _freshness_label(last_sync: Optional[datetime.datetime]) -> tuple[str, str]:
    """Return (label, style) describing how fresh a sync is."""
    if last_sync is None:
        return "never", "red"

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    if last_sync.tzinfo is None:
        last_sync = last_sync.replace(tzinfo=datetime.timezone.utc)

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


# -- Layer-build freshness ------------------------------------------------------


def _query_layer_last_build(
    metadata_db: Path, model_names: list[str]
) -> Optional[datetime.datetime]:
    """Latest successful build start time across ``model_names``."""
    import duckdb

    if not model_names or not metadata_db.exists():
        return None
    try:
        con = duckdb.connect(str(metadata_db), read_only=True)
        # IN clause via parameterised list — DuckDB supports list params.
        row = con.execute(
            "SELECT MAX(r.started_at) "
            "FROM dbt_runs r "
            "JOIN dbt_nodes n ON n.invocation_id = r.invocation_id "
            "WHERE n.status = 'success' AND list_contains(?, n.node_name)",
            [model_names],
        ).fetchone()
        con.close()
        return row[0] if row and row[0] else None
    except Exception:
        return None


# -- Panel renderers -----------------------------------------------------------


def _render_sources_panel(
    sources: list[LayerClassification],
    *,
    metadata_db: Path,
    run_counts: dict[str, int],
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
    table.add_column("Rows", justify="right")

    for src in sources:
        schema = src.schema or "—"

        if src.vendor is Vendor.DLT and src.schema:
            data = sources_data.get(src.name, {})
            last_sync = data.get("last_sync")
            row_counts = data.get("rows", {})
            runs = run_counts.get(src.schema, 0)
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


def _live_refresh_fivetran(client, metadata_db: Path) -> tuple[bool, Optional[str]]:
    """Pull connectors live and write them through to the metadata cache.

    Returns ``(refreshed, warning)``. ``refreshed`` is True when the live
    ``list_connectors()`` call succeeded and the snapshot table was
    updated. On any API/network failure we return ``(False, <warning>)``
    and leave the cache untouched, so the caller falls back to the last
    good snapshot. Never raises — ``data status`` stays non-fatal.
    """
    from tycoon.ingestion.fivetran_client import FivetranAPIError
    from tycoon.ingestion.fivetran_sync import sync_fivetran_metadata

    try:
        sync_fivetran_metadata(client, metadata_db)
        return True, None
    except FivetranAPIError as exc:
        return False, f"Fivetran API unreachable ({exc})"
    except Exception as exc:  # network down / unexpected — stay non-fatal
        return False, f"Fivetran live read failed ({exc})"


def _refresh_fivetran_cache(project) -> None:
    """Live-read Fivetran on every ``data status`` and write through to cache.

    The Sources panel and Fivetran detail both render from the cached
    snapshot; refreshing it here makes the panel live-by-default (closes
    the v0.1.7 design Q3 deviation, where freshness was bounded by the
    last ``tycoon data fivetran sync``). Incomplete creds / API / network
    failures warn and leave the existing snapshot in place.
    """
    meta = project.stack.ingestion_metadata
    if meta is None or not (meta.api_key and meta.api_secret and meta.group_id):
        warn(
            "Fivetran credentials incomplete — showing last cached snapshot. "
            "Add api_key, api_secret, group_id to refresh live."
        )
        return

    from tycoon.ingestion.fivetran_client import build_client_from_config

    metadata_db = metadata_db_path(config.root)
    try:
        with build_client_from_config(meta) as client:
            _refreshed, warning = _live_refresh_fivetran(client, metadata_db)
    except Exception as exc:  # client construction failure — stay non-fatal
        warning = f"Fivetran client error ({exc})"
    if warning:
        warn(f"{warning} — showing last cached snapshot.")


def _render_fivetran_detail() -> None:
    """Service / sync-state detail on top of the unified Sources panel."""
    from tycoon.ingestion.fivetran_sync import (
        freshness_label as fv_freshness_label,
        latest_connector_snapshot,
    )

    rows = latest_connector_snapshot(metadata_db_path(config.root))
    if not rows:
        info(
            "Fivetran detail: no metadata captured yet. Run "
            "[bold]tycoon data fivetran sync[/bold] to populate."
        )
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Connector")
    table.add_column("Service", style="dim")
    table.add_column("Sync state")
    table.add_column("Last activity")
    for r in rows:
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


def _render_layer_panel(
    title: str,
    models: Iterable[LayerClassification],
    metadata_db: Path,
    *,
    empty_hint: str,
) -> None:
    """One staging / intermediate / mart panel."""
    console.print()
    console.print(Panel(f"[bold]{title}[/bold]", expand=False))

    listed = list(models)
    if not listed:
        info(empty_hint)
        return

    last_build = _query_layer_last_build(metadata_db, [m.name for m in listed])
    fresh_label, fresh_style = _freshness_label(last_build)

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Model", style="bold")
    table.add_column("Schema", style="dim")

    for m in listed:
        table.add_row(m.name, m.schema or "—")

    summary = (
        f"{len(listed)} model(s) — last build "
        f"[{fresh_style}]{fresh_label}[/{fresh_style}]"
    )
    console.print(table)
    console.print(summary)


# -- Top-level command ---------------------------------------------------------


def status_cmd() -> None:
    """Show the layered architecture: sources -> staging -> intermediate -> marts."""
    if not config.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    project = config.project
    assert project is not None  # narrowed by has_project_file

    header("Data Status")

    # ---- Sources panel (dlt + Fivetran unified) ----
    dlt_sources = classify_dlt_sources(project.sources)
    fivetran_sources: list[LayerClassification] = []
    fivetran_managed = project.stack.ingestion.value == "fivetran"
    if fivetran_managed:
        from tycoon.ingestion.fivetran_sync import latest_connector_snapshot

        # Live API read with write-through to the cache; falls back to the
        # last snapshot (with a warning) on auth/network failure.
        _refresh_fivetran_cache(project)
        fivetran_sources = classify_fivetran_sources(
            latest_connector_snapshot(metadata_db_path(config.root))
        )

    all_sources = [*dlt_sources, *fivetran_sources]
    _meta_db = metadata_db_path(config.root)
    run_counts = _query_run_counts(_meta_db)
    _render_sources_panel(
        all_sources, metadata_db=_meta_db, run_counts=run_counts
    )
    if fivetran_managed:
        _render_fivetran_detail()

    if run_counts:
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
        empty_hint=(
            "No staging models. Scaffold one with "
            "[bold]tycoon data analyze <source>[/bold]."
        ),
    )
    _render_layer_panel(
        "Intermediate",
        filter_by_layer(models, Layer.INTERMEDIATE),
        metadata_db,
        empty_hint=(
            "No intermediate models. Optional layer — typically used to "
            "combine staging models before marts."
        ),
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
