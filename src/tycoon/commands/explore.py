"""tycoon data analyze — auto-scaffold dbt staging models."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Annotated, Optional

import click
import typer

from tycoon.config import config
from tycoon.utils.console import ai_hint, error, header, info, success, warn


def analyze_cmd(
    source_name: Annotated[
        Optional[str],
        typer.Argument(help="Name of the registered source to analyze."),
    ] = None,
    no_dbt: Annotated[
        bool,
        typer.Option(
            "--no-dbt",
            help="Skip dbt staging model generation.",
        ),
    ] = False,
    build: Annotated[
        bool,
        typer.Option(
            "--build",
            help="Run dbt build on the generated staging models after scaffolding.",
        ),
    ] = False,
    rill: Annotated[
        bool,
        typer.Option(
            "--rill",
            help=(
                "Generate Rill sources, metrics views, and explore dashboards "
                "for the source (exports tables to Parquet, uses local_file connector)."
            ),
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help=(
                "Overwrite hand-edited staging files (those whose tycoon "
                "sentinel has been removed). Without --force, such files "
                "are skipped with a warning."
            ),
        ),
    ] = False,
    all_sources: Annotated[
        bool,
        typer.Option(
            "--all",
            help=(
                "Analyze every registered source. Sources whose raw DB "
                "doesn't exist yet are skipped with a warning rather than "
                "failing the run. Mutually exclusive with the source-name "
                "argument."
            ),
        ),
    ] = False,
) -> None:
    """Auto-scaffold dbt staging models for a registered source.

    Introspects the raw DuckDB database for the given source, generates dbt
    staging models, then optionally builds the staging layer with dbt.
    """
    from tycoon.scaffolding.dbt_generator import generate_staging_models
    from tycoon.utils.duckdb_utils import get_tables

    # 1. Verify tycoon.yml exists
    if not config.has_project_file:
        error("No tycoon.yml found. Run 'tycoon init' first.")
        raise typer.Exit(1)

    # 2. Resolve which source(s) we're analyzing.
    sources = config.sources
    if all_sources:
        if source_name:
            error("Pass either a source name or --all, not both.")
            raise typer.Exit(1)
        if not sources:
            error("No sources registered in tycoon.yml. Run 'tycoon data sources add' first.")
            raise typer.Exit(1)
        _analyze_all(force=force, no_dbt=no_dbt, rill=rill, build=build)
        return

    if not source_name:
        if not sources:
            error("No sources found in tycoon.yml. Run 'tycoon sources add' first.")
            raise typer.Exit(1)
        source_name = typer.prompt(
            "Choose a source to analyze",
            type=click.Choice(list(sources.keys())),
            show_choices=True,
        )

    if source_name not in sources:
        error(
            f"Source '{source_name}' not found in tycoon.yml. "
            f"Available: {', '.join(sources.keys()) or '(none)'}"
        )
        raise typer.Exit(1)

    source_cfg = sources[source_name]
    schema_name = source_cfg.schema_name

    header(f"Analyzing: {source_name}")
    info(f"Schema: {schema_name}")

    # 3. Verify raw database exists and has data for this schema
    raw_db = config.raw_db
    if not raw_db.exists():
        error(
            f"Raw database not found at {raw_db}. "
            f"Run 'tycoon data sources run {source_name}' first."
        )
        raise typer.Exit(1)

    all_tables = get_tables(raw_db)
    schema_tables = [t for s, t in all_tables if s == schema_name]
    if not schema_tables:
        error(
            f"No tables found for schema '{schema_name}' in {raw_db}. "
            f"Run 'tycoon data sources run {source_name}' first."
        )
        raise typer.Exit(1)

    info(f"Found {len(schema_tables)} table(s) in schema '{schema_name}'")

    all_generated: list[str] = []

    # 4. Generate dbt staging models
    if not no_dbt:
        info("Generating dbt staging models...")
        staging_dir = config.dbt_project_dir / "models" / "staging" / source_name
        try:
            result = generate_staging_models(
                raw_db_path=raw_db,
                schema_name=schema_name,
                source_name=source_name,
                output_dir=staging_dir,
                force=force,
            )
            all_generated.extend(result.generated)
            if result.generated:
                success(f"Generated {len(result.generated)} dbt file(s) in {staging_dir}")
                for f in result.generated:
                    info(f"  {Path(f).name}")
            elif not result.skipped:
                warn("No dbt staging models generated (no eligible tables found).")
            if result.skipped:
                warn(
                    f"Skipped {len(result.skipped)} hand-edited file(s) "
                    f"(sentinel removed). Re-run with --force to overwrite:"
                )
                for f in result.skipped:
                    warn(f"  {Path(f).name}")
        except Exception as exc:
            error(f"dbt generation failed: {exc}")
            raise typer.Exit(1) from exc
    else:
        info("Skipping dbt staging model generation (--no-dbt)")

    # 5. Generate Rill dashboards (opt-in via --rill)
    if rill:
        from tycoon.scaffolding.rill_generator import generate_rill_config
        from tycoon.scaffolding.templates import scaffold_rill_dir

        rill_dir = config.rill_dir
        if not rill_dir.exists():
            info(f"Rill project not found; scaffolding at {rill_dir}")
            scaffold_rill_dir(rill_dir)

        info("Generating Rill sources, metrics views, and dashboards...")
        try:
            rill_files = generate_rill_config(
                raw_db_path=raw_db,
                schema_name=schema_name,
                source_name=source_name,
                output_dir=rill_dir,
            )
            all_generated.extend(rill_files)
            if rill_files:
                success(f"Generated {len(rill_files)} Rill file(s) in {rill_dir}")
                for f in rill_files:
                    info(f"  {f}")
            else:
                warn("No Rill files generated (no eligible tables found).")
        except Exception as exc:
            error(f"Rill generation failed: {exc}")
            raise typer.Exit(1) from exc
    else:
        info("Skipping Rill dashboard generation (pass --rill to enable)")

    # 6. Print summary
    from tycoon.utils.console import console

    console.print()
    success(
        f"Explore scaffolding complete — "
        f"{len(all_generated)} file(s) generated for source '{source_name}'"
    )
    # 7. Optionally run dbt build
    if build:
        if no_dbt:
            warn("--build has no effect when --no-dbt is set.")
        else:
            from tycoon.commands.transform import _dbt_executable

            info("Running dbt build --select staging...")
            dbt_dir = config.dbt_project_dir
            result = subprocess.run(
                [_dbt_executable(), "build", "--select", "staging",
                 "--profiles-dir", str(dbt_dir)],
                cwd=str(dbt_dir),
                check=False,
            )
            if result.returncode != 0:
                error("dbt build failed. Check the dbt logs above for details.")
                raise typer.Exit(result.returncode)
            success("dbt build completed successfully.")

    ai_hint(f"improve the staging models for {source_name}")


def _analyze_all(*, force: bool, no_dbt: bool, rill: bool, build: bool) -> None:
    """Iterate every registered source and analyze each.

    Soft-skips sources whose raw DB doesn't exist yet. ``--rill`` and
    ``--build`` apply per-source. Single summary at the end.
    """
    from tycoon.scaffolding.dbt_generator import generate_staging_models

    sources = config.sources
    header(f"Analyzing all sources ({len(sources)})")

    total_generated: list[str] = []
    total_skipped: list[str] = []
    skipped_sources: list[str] = []

    for src_name, src_cfg in sources.items():
        info(f"  → {src_name} (schema: {src_cfg.schema_name})")
        raw_db = config.raw_db
        if not raw_db.exists():
            warn(
                f"    Skipping {src_name} — raw DB not found at {raw_db}. "
                f"(run `tycoon data sources run {src_name}` first)"
            )
            skipped_sources.append(src_name)
            continue

        if no_dbt:
            continue

        staging_dir = config.dbt_project_dir / "models" / "staging" / src_name
        try:
            result = generate_staging_models(
                raw_db_path=raw_db,
                schema_name=src_cfg.schema_name,
                source_name=src_name,
                output_dir=staging_dir,
                force=force,
            )
        except Exception as exc:
            warn(f"    {src_name}: generation failed — {exc}")
            skipped_sources.append(src_name)
            continue

        total_generated.extend(result.generated)
        total_skipped.extend(result.skipped)
        if result.generated:
            success(f"    Generated {len(result.generated)} dbt file(s)")
        elif not result.skipped:
            warn(f"    No staging models generated for {src_name} (no eligible tables).")

    success(
        f"Analyzed {len(sources) - len(skipped_sources)} of {len(sources)} sources, "
        f"generated {len(total_generated)} dbt file(s) total"
    )
    if total_skipped:
        warn(
            f"Skipped {len(total_skipped)} hand-edited file(s) (sentinel removed). "
            f"Re-run with --force to overwrite."
        )

    # Note: --rill and --build aren't yet wired for --all to keep the
    # initial surface small. File a follow-up issue if needed.
    if rill or build:
        warn("--rill and --build are not yet supported with --all; skipped.")
