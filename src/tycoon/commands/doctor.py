"""tycoon doctor — check the environment for potential issues."""

from __future__ import annotations

import os
import shutil

from rich.console import Console
from rich.panel import Panel

from tycoon.config import config
from tycoon.project import BITool, IngestionTool, OrchestratorTool, WarehouseType
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
    """Check if the dbt project exists and is configured correctly."""
    if config.dbt_project_dir.exists() and (config.dbt_project_dir / "dbt_project.yml").exists():
        success("dbt project found.")
    else:
        error("dbt project not found or is missing `dbt_project.yml`.")


def _check_rill_project():
    """Check if the rill project exists."""
    if config.rill_dir.exists():
        success("Rill project found.")
    else:
        warn("Rill project not found. `tycoon data analyze` will create it.")


def _check_stack_config() -> None:
    """Stack-aware checks based on tycoon.yml stack configuration."""
    project = config.project
    if project is None:
        return

    stack = project.stack

    if stack.warehouse == WarehouseType.motherduck:
        if os.environ.get("MOTHERDUCK_TOKEN"):
            success("MOTHERDUCK_TOKEN is set.")
        else:
            error("MOTHERDUCK_TOKEN is not set. MotherDuck connections will fail.")

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

    if not stack.ingestion_managed:
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

    if stack.orchestrator == OrchestratorTool.dagster and stack.orchestrator_managed:
        if shutil.which("dagster"):
            success("Dagster is installed.")
        else:
            warn("Dagster not found. Run: pip install dagster dagster-webserver")
    elif not stack.orchestrator_managed and stack.orchestrator != OrchestratorTool.none:
        info(f"Orchestration is managed externally by {stack.orchestrator.value}.")

    if not stack.transformation_managed:
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
