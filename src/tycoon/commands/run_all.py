"""tycoon data run-all — ingest all sources then build dbt models."""

from __future__ import annotations

import shutil
import time
from typing import Annotated, Optional

import typer

from tycoon.config import config
from tycoon.utils.console import ai_hint, console, error, header, info, next_steps, success, warn


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
) -> None:
    """Ingest all registered sources then run dbt build."""
    if not config.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    start = time.time()
    header("Run All")

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
                ai_hint(f"help me debug the {name} ingestion")
                raise typer.Exit(1) from exc
    else:
        info("Skipping ingestion (--skip-ingest)")

    # 2. Transform
    if not skip_transform:
        dbt = shutil.which("dbt")
        if not dbt:
            error("`dbt` not found on PATH. Is your virtual environment active?")
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
                raise typer.Exit(result.returncode)
            success("dbt build complete.")
    else:
        info("Skipping transform (--skip-transform)")

    elapsed = time.time() - start
    console.rule("[bold green]Done")
    success(f"Finished in {elapsed:.1f}s")
    next_steps(
        ("tycoon data status", "check source freshness and row counts"),
        ("tycoon start --only rill", "explore results in Rill"),
    )
