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


def _check_dbt_fusion():
    """Check if dbt-fusion is installed and warn the user."""
    if shutil.which("dbtf"):
        warn(
            "Found `dbtf` executable, which can conflict with `dbt`."
            " If you are not using dbt Fusion, you may want to uninstall it."
        )
    else:
        success("`dbtf` not found.")


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


def doctor_cmd() -> None:
    """Check the environment for potential issues."""
    header("Tycoon Doctor")

    with console.status("[bold green]Running checks...[/bold green]"):
        console.print(Panel("Checking for dbt-fusion...", expand=False))
        _check_dbt_fusion()

        console.print(Panel("Checking for tycoon.yml...", expand=False))
        _check_tycoon_yml()

        console.print(Panel("Checking for dbt project...", expand=False))
        _check_dbt_project()

        console.print(Panel("Checking for Rill project...", expand=False))
        _check_rill_project()

        if config.has_project_file:
            console.print(Panel("Checking stack configuration...", expand=False))
            _check_stack_config()

    info("All checks complete.")
