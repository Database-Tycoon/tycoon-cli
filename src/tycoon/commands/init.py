"""tycoon init -- scaffold a new tycoon project."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Optional

import typer

from tycoon.project import BITool, IngestionTool, OrchestratorTool, StackConfig, WarehouseType
from tycoon.scaffolding.templates import (
    list_templates,
    scaffold_blank_project,
    scaffold_from_template,
)
from tycoon.utils.console import console, error, header, info, next_steps, success, warn


def _prompt_choice(prompt: str, options: list[str]) -> int:
    """Print a numbered menu and return the 1-based choice as an int."""
    for i, opt in enumerate(options, 1):
        console.print(f"  {i}) {opt}")
    while True:
        raw = typer.prompt(prompt)
        try:
            choice = int(raw)
            if 1 <= choice <= len(options):
                return choice
        except ValueError:
            pass
        warn(f"Please enter a number between 1 and {len(options)}.")


def _detect_existing(target: Path) -> dict:
    """Scan the working directory for signs of an existing pipeline."""
    found = {}
    if (target / "dbt_project.yml").exists():
        found["dbt_project"] = str(target / "dbt_project.yml")
    if (target / "profiles.yml").exists():
        found["profiles"] = str(target / "profiles.yml")
    duckdb_files = list(target.glob("**/*.duckdb")) + list((target / "data").glob("*.duckdb") if (target / "data").exists() else [])
    if duckdb_files:
        found["duckdb"] = str(duckdb_files[0])
    return found


def _run_wizard(target: Path, project_name: str) -> tuple[StackConfig, str | None, str | None]:
    """Run the interactive setup questionnaire.

    Returns (stack, existing_dbt_path, existing_warehouse_path).
    """
    detected = _detect_existing(target)
    if detected:
        info("Detected existing files:")
        for key, path in detected.items():
            console.print(f"  [dim]{key}:[/dim] {path}")
        console.print()

    has_pipeline = typer.confirm("Do you already have a data pipeline?", default=False)

    existing_dbt_path: str | None = None
    existing_warehouse_path: str | None = None

    if has_pipeline:
        # --- Ingestion ---
        console.print("\nWhat do you use for ingestion?")
        ingestion_choice = _prompt_choice("Choice", [
            "dlt (tycoon will manage it)",
            "Airbyte / Fivetran / Meltano (external — tycoon won't run it)",
            "None / I just have data I want to query",
        ])
        if ingestion_choice == 1:
            ingestion = IngestionTool.dlt
            ingestion_managed = True
        elif ingestion_choice == 2:
            console.print("\nWhich external tool?")
            ext_choice = _prompt_choice("Choice", ["Airbyte", "Fivetran", "Meltano"])
            ingestion = [IngestionTool.airbyte, IngestionTool.fivetran, IngestionTool.meltano][ext_choice - 1]
            ingestion_managed = False
        else:
            ingestion = IngestionTool.none
            ingestion_managed = False

        # --- Warehouse ---
        console.print("\nWhere is your data?")
        wh_choice = _prompt_choice("Choice", [
            "Local DuckDB file",
            "MotherDuck (cloud DuckDB)",
            "Snowflake",
            "BigQuery",
            "Other",
        ])
        wh_map = [
            WarehouseType.duckdb,
            WarehouseType.motherduck,
            WarehouseType.snowflake,
            WarehouseType.bigquery,
            WarehouseType.other,
        ]
        warehouse = wh_map[wh_choice - 1]

        if warehouse == WarehouseType.duckdb:
            default_path = detected.get("duckdb", "data/warehouse.duckdb")
            existing_warehouse_path = typer.prompt("Path to your DuckDB file", default=default_path)
        elif warehouse == WarehouseType.motherduck:
            md_name = typer.prompt("MotherDuck database name", default=project_name.replace("-", "_"))
            existing_warehouse_path = f"md:{md_name}"
        elif warehouse in (WarehouseType.snowflake, WarehouseType.bigquery, WarehouseType.redshift):
            info(f"Native {warehouse.value.title()} querying via `tycoon data db` is coming in 0.8.")
            info("tycoon will record your warehouse type and manage dbt against it using your profiles.yml.")

        # --- dbt ---
        console.print()
        has_dbt = typer.confirm("Do you have an existing dbt project?", default=bool(detected.get("dbt_project")))
        if has_dbt:
            default_dbt = detected.get("dbt_project", "")
            if default_dbt.endswith("dbt_project.yml"):
                default_dbt = str(Path(default_dbt).parent)
            existing_dbt_path = typer.prompt("Path to your dbt project directory", default=default_dbt or str(target.parent / f"{project_name}-dbt"))
            transformation_managed = False
        else:
            create_dbt = typer.confirm("Would you like tycoon to scaffold a dbt project?", default=True)
            if create_dbt:
                default_new_dbt = str(target.parent / f"{project_name}-dbt")
                existing_dbt_path = typer.prompt("Where should the dbt project live?", default=default_new_dbt)
                transformation_managed = True
            else:
                existing_dbt_path = None
                transformation_managed = False

        # --- BI Tool ---
        console.print()
        console.print("Do you have a BI / dashboard tool?")
        bi_choice = _prompt_choice("Choice", [
            "Rill (tycoon will manage it)",
            "Metabase / Looker / Tableau / other (external)",
            "None yet",
        ])
        if bi_choice == 1:
            bi = BITool.rill
            bi_managed = True
        elif bi_choice == 2:
            console.print()
            console.print("Which BI tool?")
            bi_ext_choice = _prompt_choice("Choice", ["Metabase", "Looker", "Tableau", "Other"])
            bi = [BITool.metabase, BITool.looker, BITool.tableau, BITool.other][bi_ext_choice - 1]
            bi_managed = False
        else:
            bi = BITool.none
            bi_managed = False

        # --- Orchestrator ---
        console.print()
        console.print("Do you have an orchestrator?")
        orch_choice = _prompt_choice("Choice", [
            "Dagster (tycoon will manage it)",
            "Airflow / Prefect / other (external)",
            "None / I'll run pipelines manually",
        ])
        if orch_choice == 1:
            orchestrator = OrchestratorTool.dagster
            orchestrator_managed = True
        elif orch_choice == 2:
            console.print()
            console.print("Which orchestrator?")
            orch_ext_choice = _prompt_choice("Choice", ["Airflow", "Prefect", "Other"])
            orchestrator = [OrchestratorTool.airflow, OrchestratorTool.prefect, OrchestratorTool.other][orch_ext_choice - 1]
            orchestrator_managed = False
        else:
            orchestrator = OrchestratorTool.none
            orchestrator_managed = False

        stack = StackConfig(
            ingestion=ingestion,
            ingestion_managed=ingestion_managed,
            warehouse=warehouse,
            transformation_managed=transformation_managed,
            bi=bi,
            bi_managed=bi_managed,
            orchestrator=orchestrator,
            orchestrator_managed=orchestrator_managed,
        )

    else:
        # Greenfield — pick warehouse
        console.print("\nWhere would you like to store your data?")
        wh_choice = _prompt_choice("Choice", [
            "Local DuckDB (zero-config)",
            "MotherDuck (cloud DuckDB — requires MOTHERDUCK_TOKEN)",
        ])
        if wh_choice == 2:
            md_name = typer.prompt("MotherDuck database name", default=project_name.replace("-", "_"))
            existing_warehouse_path = f"md:{md_name}"
            warehouse = WarehouseType.motherduck
        else:
            warehouse = WarehouseType.duckdb

        # dbt location
        console.print()
        default_new_dbt = str(target.parent / f"{project_name}-dbt")
        existing_dbt_path = typer.prompt("Where should the dbt project live?", default=default_new_dbt)

        # BI tool
        console.print("\nWhich BI / dashboard tool would you like to use?")
        bi_choice = _prompt_choice("Choice", [
            "Rill (tycoon will manage it — recommended)",
            "I'll connect my own BI tool",
            "None / skip",
        ])
        bi = BITool.rill if bi_choice == 1 else BITool.none
        bi_managed = bi_choice == 1

        # Orchestrator
        console.print("\nHow would you like to run your pipelines?")
        orch_choice = _prompt_choice("Choice", [
            "Dagster (tycoon will manage it — recommended)",
            "Manually via tycoon CLI commands",
        ])
        orchestrator = OrchestratorTool.dagster if orch_choice == 1 else OrchestratorTool.none
        orchestrator_managed = orch_choice == 1

        stack = StackConfig(
            ingestion=IngestionTool.dlt,
            ingestion_managed=True,
            warehouse=warehouse,
            transformation_managed=True,
            bi=bi,
            bi_managed=bi_managed,
            orchestrator=orchestrator,
            orchestrator_managed=orchestrator_managed,
        )

    return stack, existing_dbt_path, existing_warehouse_path


def _mode_next_steps(stack: StackConfig, existing_dbt_path: str | None) -> None:
    """Print next steps appropriate to the configured stack mode."""
    if not stack.ingestion_managed and existing_dbt_path:
        # BYO full pipeline
        next_steps(
            ("tycoon doctor", "verify your stack configuration"),
            ("tycoon data transform run", "run dbt transformations"),
            ("tycoon ask init", "set up the AI analytics agent"),
        )
    elif not stack.ingestion_managed:
        # Warehouse-only
        next_steps(
            ("tycoon doctor", "verify your stack configuration"),
            ("tycoon data transform run", "scaffold and run dbt models"),
            ("tycoon ask init", "set up the AI analytics agent"),
        )
    else:
        # Greenfield / dlt-managed
        next_steps(
            ("tycoon data sources catalog", "browse available data sources"),
            ("tycoon data sources add", "add your first data source"),
            ("tycoon ask init", "set up the AI analytics agent"),
        )


def init_cmd(
    template: Annotated[
        Optional[str],
        typer.Option(
            "--template",
            "-t",
            help="Template name to scaffold from.",
        ),
    ] = None,
    name: Annotated[
        Optional[str],
        typer.Option(
            "--name",
            "-n",
            help="Project name (defaults to current directory name).",
        ),
    ] = None,
    list_templates_flag: Annotated[
        bool,
        typer.Option(
            "--list-templates",
            help="List available templates and exit.",
        ),
    ] = False,
) -> None:
    """Initialize a new tycoon project in the current directory."""
    if list_templates_flag:
        templates = list_templates()
        if not templates:
            info("No templates available.")
        else:
            header("Available Templates")
            for t in templates:
                console.print(f"  - {t}")
        raise typer.Exit(0)

    target = Path.cwd()
    project_name = name or target.name

    if (target / "tycoon.yml").exists():
        warn("tycoon.yml already exists in this directory.")
        error("Use a different directory or remove the existing tycoon.yml first.")
        raise typer.Exit(1)

    header(f"Initializing tycoon project: {project_name}")

    if template:
        try:
            scaffold_from_template(target, template)
        except FileNotFoundError as exc:
            error(str(exc))
            raise typer.Exit(1)
        console.print()
        success(f"Project '{project_name}' initialized from template '{template}'!")
        next_steps(
            ("tycoon data sources catalog", "browse available data sources"),
            ("tycoon data sources add", "add your first data source"),
            ("tycoon ask init", "set up the AI analytics agent"),
        )
    else:
        stack, existing_dbt_path, existing_warehouse_path = _run_wizard(target, project_name)
        console.print()
        scaffold_blank_project(
            target,
            project_name,
            stack=stack,
            existing_dbt_path=existing_dbt_path,
            existing_warehouse_path=existing_warehouse_path,
        )
        console.print()
        success(f"Project '{project_name}' initialized successfully!")
        _mode_next_steps(stack, existing_dbt_path)
