"""tycoon doctor — check the environment for potential issues."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from tycoon.config import config
from tycoon.project import BITool, IngestionTool, OrchestratorTool, TransformationTool, WarehouseType
from tycoon.utils.console import error, header, info, success, warn

console = Console()


def _check_tycoon_yml():
    """Check if tycoon.yml exists."""
    if config.has_project_file:
        success("`tycoon.yml` found.")
    else:
        error("`tycoon.yml` not found. Run `tycoon init` to create a new project.")


def _check_dbt_project():
    """Check if the dbt project exists, or report intentional skip."""
    project = config.project
    if project and project.stack.transformation == TransformationTool.none:
        info("dbt: skipped by choice (stack.transformation = none).")
        return

    if config.dbt_project_dir.exists() and (config.dbt_project_dir / "dbt_project.yml").exists():
        success("dbt project found.")
    else:
        warn(
            "dbt project not found. Run `tycoon init` to scaffold one, "
            "or point `dbt_project_dir` in tycoon.yml at an existing project."
        )


def _check_rill_project():
    """Check if the rill project exists, or report intentional skip."""
    project = config.project
    if project and project.stack.bi != BITool.rill:
        if project.stack.bi == BITool.none:
            info("Rill/BI: skipped by choice (stack.bi = none).")
        else:
            info(f"BI is {project.stack.bi.value} (not Rill); skipping Rill checks.")
        return

    if config.rill_dir.exists():
        success("Rill project found.")
    else:
        warn("Rill project not found. `tycoon data analyze --rill` will create it.")


_MOTHERDUCK_CACHE_CANDIDATES = (
    # Standard DuckDB token cache (~/.duckdb/stored_tokens)
    Path.home() / ".duckdb" / "stored_tokens",
    # MotherDuck-specific cache locations seen in the wild
    Path.home() / ".duckdb" / "motherduck_token",
    Path.home() / ".config" / "motherduck" / "token",
    Path.home() / "Library" / "Application Support" / "motherduck" / "token",
)


def _has_motherduck_oauth_cache() -> bool:
    """Heuristic: does a non-empty MotherDuck/DuckDB token cache exist on disk?

    We don't call ``duckdb.connect('md:')`` here because a miss would open a
    browser OAuth flow — way too aggressive for a diagnostic command. A
    cache-file probe is good enough to distinguish "user is logged in via
    OAuth" from "user has nothing configured". False negatives (cache in a
    non-standard location) still fall through to the existing error; users
    can export ``MOTHERDUCK_TOKEN`` to force-succeed.
    """
    for candidate in _MOTHERDUCK_CACHE_CANDIDATES:
        try:
            if candidate.exists() and candidate.stat().st_size > 0:
                return True
        except OSError:
            continue
    return False


def _check_motherduck_auth() -> None:
    """Report MotherDuck auth status. Recognizes both env-token and cached OAuth."""
    if os.environ.get("MOTHERDUCK_TOKEN"):
        success("MotherDuck auth: token (env MOTHERDUCK_TOKEN).")
        return
    if _has_motherduck_oauth_cache():
        success("MotherDuck auth: OAuth (cached session).")
        info("For CI / non-interactive use, export MOTHERDUCK_TOKEN.")
        return
    error(
        "MotherDuck auth: not configured. "
        "Export MOTHERDUCK_TOKEN, or run `duckdb -c \"ATTACH 'md:'\"` once "
        "to authenticate via browser OAuth."
    )


def _check_stack_config() -> None:
    """Stack-aware checks based on tycoon.yml stack configuration."""
    project = config.project
    if project is None:
        return

    stack = project.stack

    if stack.warehouse == WarehouseType.motherduck:
        _check_motherduck_auth()

    if stack.warehouse == WarehouseType.snowflake:
        missing = [v for v in ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"] if not os.environ.get(v)]
        if missing:
            warn(f"Snowflake env vars not set: {', '.join(missing)}")
        else:
            success("Snowflake credentials found.")

    if stack.warehouse == WarehouseType.bigquery:
        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and not os.environ.get("BIGQUERY_PROJECT"):
            warn("No BigQuery credentials detected (GOOGLE_APPLICATION_CREDENTIALS or BIGQUERY_PROJECT).")
        else:
            success("BigQuery credentials found.")

    if stack.ingestion == IngestionTool.none:
        info("Ingestion: skipped by choice (stack.ingestion = none).")
    elif stack.ingestion == IngestionTool.fivetran:
        _check_fivetran_credentials(stack)
    elif not stack.ingestion_managed:
        info(f"Ingestion is managed externally by {stack.ingestion.value}. Skipping ingestion checks.")
    elif stack.ingestion == IngestionTool.dlt:
        try:
            import dlt  # noqa: F401
            success("dlt is installed.")
        except ImportError:
            error("dlt not found. Run: pip install 'dlt[duckdb]'")

    if stack.bi == BITool.rill and stack.bi_managed:
        if not config.rill_dir.exists():
            warn("Rill project not found. Run `tycoon data analyze` to scaffold dashboards.")
        else:
            success("Rill project found.")
    elif not stack.bi_managed and stack.bi != BITool.none:
        info(f"BI is managed externally by {stack.bi.value}. Skipping Rill checks.")

    if stack.orchestrator == OrchestratorTool.none:
        info("Orchestrator: skipped by choice (stack.orchestrator = none).")
    elif stack.orchestrator == OrchestratorTool.dagster and stack.orchestrator_managed:
        if shutil.which("dagster"):
            success("Dagster is installed.")
        else:
            warn("Dagster not found. Run: pip install dagster dagster-webserver")
    elif not stack.orchestrator_managed:
        info(f"Orchestration is managed externally by {stack.orchestrator.value}.")

    if stack.transformation == TransformationTool.dbt and not stack.transformation_managed:
        from pathlib import Path
        dbt_dir = Path(project.dbt_project_dir)
        if not dbt_dir.is_absolute():
            dbt_dir = config.root / dbt_dir
        if dbt_dir.exists() and (dbt_dir / "dbt_project.yml").exists():
            success(f"External dbt project found at {project.dbt_project_dir}.")
        else:
            error(f"External dbt project not found at {project.dbt_project_dir}.")


def _check_fivetran_credentials(stack) -> None:
    """Validate Fivetran API creds + group_id can reach the API.

    Fires only when ``stack.ingestion = fivetran``. Doesn't pull
    connectors — just probes the group endpoint so we don't spam the
    API on every doctor run.
    """
    meta = stack.ingestion_metadata
    if meta is None:
        error(
            "stack.ingestion is fivetran but stack.ingestion_metadata is "
            "missing. Add api_key, api_secret, group_id."
        )
        return

    if not (meta.api_key and meta.api_secret and meta.group_id):
        error("Fivetran credentials incomplete: need api_key, api_secret, group_id.")
        return

    try:
        from tycoon.ingestion.fivetran_client import build_client_from_config
    except ImportError as exc:  # pragma: no cover — defensive
        warn(f"Fivetran client not importable: {exc}")
        return

    try:
        with build_client_from_config(meta) as client:
            if client.verify_credentials():
                success(f"Fivetran auth OK (group_id={meta.group_id}).")
            else:
                error(
                    f"Fivetran auth failed for group_id={meta.group_id}. "
                    "Check api_key/api_secret and that the group exists."
                )
    except Exception as exc:
        warn(f"Fivetran probe raised unexpectedly: {exc}")


def _check_dbt_profile() -> None:
    """Resolve + validate the active dbt profile, non-fatal."""
    project = config.project
    if project is None:
        return
    if project.stack.transformation == TransformationTool.none:
        info("dbt profile: skipped (stack.transformation = none).")
        return
    if not config.dbt_project_dir.exists():
        info("dbt profile: skipped (dbt project directory missing).")
        return

    from tycoon.commands.profiles import run_profile_checks

    # run_profile_checks returns 0/1 but emits its own success/warn/error
    # rows — we don't bubble the rc since doctor stays non-fatal overall.
    try:
        run_profile_checks()
    except Exception as exc:  # defensive: bad YAML shouldn't kill doctor
        warn(f"dbt profile check raised unexpectedly: {exc}")


def _check_osi() -> None:
    """Validate generated OSI YAML if present. Skips silently when absent."""
    project = config.project
    if project is None:
        return
    if project.stack.transformation == TransformationTool.none:
        return

    from tycoon.commands.semantics import run_osi_check

    try:
        run_osi_check()
    except Exception as exc:
        warn(f"OSI check raised unexpectedly: {exc}")


def _check_layer_coverage() -> None:
    """Every registered source should have at least one staging model.

    Non-fatal: emits ``info`` for healthy projects and ``warn`` listing
    any uncovered sources. Skips silently when ``transformation: none``
    or when the dbt manifest hasn't been compiled yet (the user gets a
    clearer signal from the dbt-project / observability checks).
    """
    project = config.project
    if project is None:
        return
    if project.stack.transformation == TransformationTool.none:
        return
    if not project.sources:
        return

    from tycoon.layers import (
        Layer,
        classify_dbt_models,
        classify_dlt_sources,
        filter_by_layer,
        load_manifest,
    )

    manifest = load_manifest(config.dbt_project_dir)
    if manifest is None:
        # Don't double-report — the dbt-project / observability rows
        # already nudge the user toward `tycoon data transform run`.
        return

    sources = classify_dlt_sources(project.sources)
    staging_models = filter_by_layer(classify_dbt_models(manifest), Layer.STAGING)
    staging_names = {m.name.lower() for m in staging_models}

    uncovered: list[str] = []
    for src in sources:
        # The convention is one or more `stg_<source>__<table>` models per
        # registered source. Treat any `stg_*<source>*` match as coverage.
        token = src.name.lower()
        if not any(token in name for name in staging_names):
            uncovered.append(src.name)

    if not uncovered:
        success(
            f"Layer coverage: every source ({len(sources)}) has at least "
            f"one staging model."
        )
        return

    warn(
        "Layer coverage: no staging model found for source(s): "
        + ", ".join(uncovered)
        + ". Scaffold with `tycoon data analyze <source>` or write "
        "models under `<dbt_project>/models/staging/`."
    )


def _check_observability() -> None:
    """Report whether run-history capture has fired at least once.

    Useful first-time diagnosis of "why are my dashboards empty?" — if
    the metadata DB doesn't exist or is empty, dlt/dbt have not yet
    triggered the capture hooks.
    """
    from tycoon.observability import has_any_observability_data, metadata_db_path

    meta = metadata_db_path(config.root)
    if not meta.exists():
        info(
            "Observability: metadata DB not yet created — "
            "run `tycoon data sources run` or `tycoon data transform run` to "
            "start capturing history."
        )
        return

    try:
        has_dlt, has_dbt = has_any_observability_data(meta)
    except Exception as exc:
        warn(f"Observability: metadata DB present but unreadable ({exc}).")
        return

    if not (has_dlt or has_dbt):
        info(
            "Observability: metadata DB exists but no runs captured yet — "
            "run `tycoon data sources run` or `tycoon data transform run`."
        )
        return

    import duckdb

    con = duckdb.connect(str(meta), read_only=True)
    try:
        dlt_count = 0
        dbt_count = 0
        if has_dlt:
            row = con.execute("SELECT count(*) FROM dlt_runs").fetchone()
            dlt_count = row[0] if row else 0
        if has_dbt:
            row = con.execute("SELECT count(*) FROM dbt_runs").fetchone()
            dbt_count = row[0] if row else 0
    finally:
        con.close()

    success(
        f"Observability: {dlt_count} dlt load(s), {dbt_count} dbt run(s) captured. "
        f"View with `tycoon data history`."
    )


def doctor_cmd() -> None:
    """Check the environment for potential issues."""
    header("Tycoon Doctor")

    with console.status("[bold green]Running checks...[/bold green]"):
        console.print(Panel("Checking for tycoon.yml...", expand=False))
        _check_tycoon_yml()

        console.print(Panel("Checking for dbt project...", expand=False))
        _check_dbt_project()

        console.print(Panel("Checking for Rill project...", expand=False))
        _check_rill_project()

        if config.has_project_file:
            console.print(Panel("Checking stack configuration...", expand=False))
            _check_stack_config()

            console.print(Panel("Checking dbt profile...", expand=False))
            _check_dbt_profile()

            console.print(Panel("Checking OSI semantic layer...", expand=False))
            _check_osi()

            console.print(Panel("Checking layer coverage...", expand=False))
            _check_layer_coverage()

            console.print(Panel("Checking observability...", expand=False))
            _check_observability()

    info("All checks complete.")
