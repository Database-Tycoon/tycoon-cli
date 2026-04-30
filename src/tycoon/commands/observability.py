"""``tycoon data observability`` — first-class access to tycoon's metadata.

Issue #20. Two surfaces today:

- ``tycoon data observability scaffold`` — generate dbt staging models on
  top of ``.tycoon/metadata.duckdb`` and ATTACH the metadata DB into the
  project's dbt profile. After running, ``tycoon data transform run``
  builds the ``stg_tycoon__*`` views, ``tycoon ask sync`` exposes them
  to Nao, and the agent can answer "which dbt models failed last week?"
  without extra plumbing.
"""

from __future__ import annotations

import typer

from tycoon.config import config
from tycoon.utils.console import error, info, next_steps, success, warn


app = typer.Typer(help="Tycoon's observability metadata as first-class data.")


@app.command(name="scaffold")
def observability_scaffold(
    no_attach: bool = typer.Option(
        False,
        "--no-attach",
        help=(
            "Skip the profiles.yml ATTACH step. Use this if you've already "
            "wired the attach by hand or if your profile lives outside the "
            "dbt project dir."
        ),
    ),
    no_models: bool = typer.Option(
        False,
        "--no-models",
        help=(
            "Skip the staging-model generation. Useful for adding the ATTACH "
            "to existing-projects without touching their dbt models."
        ),
    ),
) -> None:
    """Generate dbt staging models for tycoon's observability metadata.

    Creates ``dbt_project/models/_tycoon/`` with one ``stg_tycoon__*.sql``
    view per metadata table, a ``dim_runs.sql`` mart unifying dlt + dbt
    timelines, and a ``_tycoon__schema.yml`` documenting every model.

    Also adds a ``tycoon_meta`` ATTACH entry to every duckdb output in
    the project's ``profiles.yml`` so the staging models can SELECT from
    the metadata DB without copying data.

    Idempotent — re-running overwrites the staging files but leaves the
    ATTACH alone if it's already present.
    """
    from tycoon.scaffolding.observability_dbt import (
        attach_metadata_to_profiles,
        scaffold_observability_models,
    )

    project = config.project
    if project is None:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    dbt_dir = config.dbt_project_dir
    if not dbt_dir.exists() or not (dbt_dir / "dbt_project.yml").exists():
        error(
            f"No dbt project at [bold]{dbt_dir}[/bold]. "
            "Run [bold]tycoon init[/bold] or [bold]tycoon register dbt <path>[/bold] first."
        )
        raise typer.Exit(1)

    if no_models and no_attach:
        warn("Both --no-models and --no-attach passed — nothing to do.")
        raise typer.Exit(0)

    # ---- 1. Staging models ----
    if not no_models:
        written = scaffold_observability_models(dbt_dir)
        info(f"Wrote {len(written)} files under [bold]{dbt_dir / 'models' / '_tycoon'}[/bold]:")
        for path in written:
            info(f"  {path.relative_to(dbt_dir)}")

    # ---- 2. profiles.yml ATTACH ----
    if not no_attach:
        # We resolve profiles.yml the same way `tycoon data transform` does.
        # Co-located profiles.yml is the common case for tycoon-scaffolded
        # projects; an explicit dbt_profiles_dir overrides.
        if project.dbt_profiles_dir:
            from pathlib import Path
            profiles_dir = Path(project.dbt_profiles_dir)
            if not profiles_dir.is_absolute():
                profiles_dir = (config.root / profiles_dir).resolve()
            profiles_yml = profiles_dir / "profiles.yml"
        else:
            profiles_yml = dbt_dir / "profiles.yml"

        if not profiles_yml.exists():
            warn(
                f"No [bold]profiles.yml[/bold] at {profiles_yml}. "
                "Skipping ATTACH wiring — add [bold]tycoon_meta[/bold] to your profile manually, "
                "or re-run after registering a profile path."
            )
        else:
            metadata_db = config.root / ".tycoon" / "metadata.duckdb"
            try:
                changed = attach_metadata_to_profiles(profiles_yml, metadata_db)
            except Exception as exc:
                error(f"Failed to update profiles.yml: {exc}")
                raise typer.Exit(1) from exc
            if changed:
                info(f"Added [bold]tycoon_meta[/bold] ATTACH to {profiles_yml.relative_to(config.root)}")
            else:
                info(f"[dim]profiles.yml already has the tycoon_meta ATTACH — nothing to do.[/dim]")

    success("Observability scaffolding complete.")
    next_steps(
        ("tycoon data transform run --select _tycoon", "build the staging views"),
        ("tycoon ask sync", "expose them to Nao"),
        ("tycoon data query \"SELECT * FROM stg_tycoon__dlt_runs LIMIT 5\"", "smoke-test"),
    )
