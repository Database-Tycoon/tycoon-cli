"""tycoon data run-all — ingest all sources then build dbt models."""

from __future__ import annotations

import shutil
import time
from typing import Annotated, Optional

import typer

from tycoon.config import config
from tycoon.utils.console import console, error, header, info, next_steps, success, warn


def run_all_cmd(
    max_records: Annotated[
        Optional[int],
        typer.Option(
            "--max-records",
            "-n",
            help="Cap records fetched per resource (useful for testing).",
            show_default=False,
        ),
    ] = None,
    skip_ingest: Annotated[
        bool,
        typer.Option("--skip-ingest", help="Skip ingestion and only run dbt build."),
    ] = False,
    skip_transform: Annotated[
        bool,
        typer.Option("--skip-transform", help="Skip dbt build and only run ingestion."),
    ] = False,
    target: Annotated[
        str,
        typer.Option("--target", "-t", help="dbt target profile."),
    ] = "dev",
    notify: Annotated[
        bool,
        typer.Option(
            "--notify",
            help=(
                "Send a webhook notification on completion (success/failure). "
                "Requires $TYCOON_NOTIFY_WEBHOOK_URL; see `tycoon notify`."
            ),
        ),
    ] = False,
) -> None:
    """Ingest all registered sources then run dbt build."""
    if not config.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    start = time.time()
    header("Run All")

    def _emit(severity: str, message: str, **fields: str) -> None:
        """Best-effort webhook notification, gated by --notify and notify.severities."""
        if not notify:
            return
        from tycoon import notify as notify_mod

        project = config.project
        prefs = project.notify if project is not None else None
        allowed = prefs.severities if prefs is not None else ["success", "error"]
        if severity not in allowed:
            return
        label = prefs.label if prefs is not None else None
        if notify_mod.webhook_url() is None:
            warn(f"--notify set but ${notify_mod.WEBHOOK_ENV_VAR} is not configured — skipping notification.")
            return
        if not notify_mod.send(severity, message, fields or None, label=label):
            warn("Notification failed to send (continuing).")

    # 1. Ingest
    if not skip_ingest:
        from tycoon.ingestion.runner import run_source as _run_source

        sources = config.sources
        if not sources:
            error("No sources registered. Run [bold]tycoon data sources add[/bold] first.")
            raise typer.Exit(1)

        config.ensure_data_dir()
        total = len(sources)
        info(f"Ingesting {total} source{'s' if total != 1 else ''}...")
        if max_records is not None:
            info(f"Record cap: {max_records:,} per resource")

        for i, (name, source_config) in enumerate(sources.items(), 1):
            console.rule(f"[bold cyan]{i}/{total} — {name}")
            try:
                _pipeline, load_info = _run_source(
                    name=name,
                    source_config=source_config,
                    raw_db_path=config.raw_db,
                    max_records=max_records,
                )
                success(f"{name}: {load_info}")
            except Exception as exc:
                error(f"{name} failed: {exc}")
                _emit("error", f"run-all failed during ingest of '{name}'", stage="ingest", error=str(exc)[:300])
                raise typer.Exit(1) from exc
    else:
        info("Skipping ingestion (--skip-ingest)")

    # 2. Transform
    if not skip_transform:
        dbt = shutil.which("dbt")
        if not dbt:
            error("`dbt` not found on PATH. Is your virtual environment active?")
            _emit("error", "run-all failed: dbt not found on PATH", stage="transform")
            raise typer.Exit(1)

        project_dir = config.dbt_project_dir
        if not project_dir.exists():
            warn(f"dbt project not found at {project_dir} — skipping transform.")
        else:
            import subprocess
            console.rule("[bold cyan]dbt build")
            cmd = [dbt, "build", "--target", target, "--profiles-dir", str(project_dir)]
            console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
            result = subprocess.run(cmd, cwd=project_dir)
            if result.returncode != 0:
                error(f"dbt build failed (exit {result.returncode}).")
                _emit("error", "run-all failed during dbt build", stage="transform", exit_code=str(result.returncode))
                raise typer.Exit(result.returncode)
            success("dbt build complete.")
    else:
        info("Skipping transform (--skip-transform)")

    elapsed = time.time() - start
    console.rule("[bold green]Done")
    success(f"Finished in {elapsed:.1f}s")
    _emit("success", "run-all complete", elapsed=f"{elapsed:.1f}s", sources=str(len(config.sources)))
    next_steps(
        ("tycoon data status", "check source freshness and row counts"),
        ("tycoon start --only rill", "explore results in Rill"),
    )
