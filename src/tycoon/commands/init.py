"""tycoon init -- scaffold a new tycoon project."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml

from tycoon.project import (
    BITool,
    IngestionTool,
    OrchestratorTool,
    StackConfig,
    TransformationTool,
    WarehouseType,
)
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


@dataclass
class DetectedItem:
    """An auto-detected stack component on disk."""

    path: Path
    kind: str  # "inline" (inside target) | "sibling" (sibling of target)


@dataclass
class DetectionResults:
    """Structured output of `_detect_existing`."""

    dbt: list[DetectedItem] = field(default_factory=list)
    rill: list[DetectedItem] = field(default_factory=list)
    warehouse: list[DetectedItem] = field(default_factory=list)

    def has_any(self) -> bool:
        return bool(self.dbt or self.rill or self.warehouse)


# Canonical inline subdirs to probe
_DBT_INLINE_DIRS = ("dbt_project", "dbt", "transformation")
_RILL_INLINE_DIRS = ("rill", "dashboards")


def _detect_existing(target: Path) -> DetectionResults:
    """Scan the target directory (and its siblings) for existing stack components.

    Looks for:
      - dbt: ``<target>/<subdir>/dbt_project.yml`` for canonical subdirs, plus
        ``dbt_project.yml`` in the target root, and any sibling directory of
        ``target`` that contains a ``dbt_project.yml``.
      - rill: ``<target>/<subdir>/rill.yaml`` and sibling dirs.
      - warehouse: any ``<target>/data/*.duckdb`` that doesn't look like a raw
        ingestion DB (names starting with ``raw_`` or ending in ``_raw``).
    """
    results = DetectionResults()

    # dbt — target root (rare but possible)
    if (target / "dbt_project.yml").exists():
        results.dbt.append(DetectedItem(path=target, kind="inline"))

    # dbt — canonical inline subdirs
    for sub in _DBT_INLINE_DIRS:
        candidate = target / sub
        if (candidate / "dbt_project.yml").exists():
            results.dbt.append(DetectedItem(path=candidate, kind="inline"))

    # rill — canonical inline subdirs
    for sub in _RILL_INLINE_DIRS:
        candidate = target / sub
        if (candidate / "rill.yaml").exists():
            results.rill.append(DetectedItem(path=candidate, kind="inline"))

    # warehouse — data/*.duckdb (excluding files that look like raw ingestion DBs)
    data_dir = target / "data"
    if data_dir.exists():
        for db_file in sorted(data_dir.glob("*.duckdb")):
            name = db_file.stem
            if name.startswith("raw_") or name.endswith("_raw") or name == "raw":
                continue
            results.warehouse.append(DetectedItem(path=db_file, kind="inline"))

    # Siblings — walk one level up, check dirs that look relevant
    parent = target.parent
    if parent.exists() and parent != target:
        for sibling in sorted(parent.iterdir()):
            if not sibling.is_dir() or sibling == target or sibling.name.startswith("."):
                continue
            if (sibling / "dbt_project.yml").exists():
                results.dbt.append(DetectedItem(path=sibling, kind="sibling"))
            if (sibling / "rill.yaml").exists():
                results.rill.append(DetectedItem(path=sibling, kind="sibling"))

    return results


@dataclass
class WizardResult:
    """Output of the init wizard."""

    stack: StackConfig
    dbt_path: str | None = None  # where dbt project lives (None => skipped)
    rill_path: str | None = None  # where Rill project lives (None => skipped)
    warehouse_path: str | None = None  # DuckDB path or cloud conn string


def _print_section(title: str) -> None:
    console.print()
    console.print(f"[bold cyan]── {title} ──────────────────[/bold cyan]")


def _clone_repo(url: str, dest: Path) -> bool:
    """git clone <url> into <dest>. Returns True on success."""
    import subprocess

    if dest.exists():
        warn(f"{dest} already exists; leaving it alone.")
        return True
    try:
        subprocess.run(["git", "clone", url, str(dest)], check=True)
        success(f"Cloned into {dest}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        error(f"git clone failed: {exc}")
        return False


def _prompt_register_project(component: str, default_sibling: Path) -> str | None:
    """Shared sub-flow for "register existing" — returns absolute path string or None on failure."""
    raw = typer.prompt(
        f"Local path or GitHub URL for your {component} project",
        default="",
    ).strip()
    if not raw:
        warn("No path provided; treating this component as skipped.")
        return None

    if raw.startswith(("http://", "https://", "git@")):
        clone_here = typer.confirm(
            f"Clone into {default_sibling}?",
            default=True,
        )
        dest = default_sibling if clone_here else Path(
            typer.prompt(f"Where should the {component} project be cloned?", default=str(default_sibling))
        ).expanduser().resolve()
        if not _clone_repo(raw, dest):
            return None
        return str(dest)

    path = Path(raw).expanduser().resolve()
    if not path.exists():
        warn(f"Path {path} does not exist; treating this component as skipped.")
        return None
    return str(path)


def _prompt_ingestion() -> tuple[IngestionTool, bool]:
    _print_section("Ingestion")
    console.print("How do you load data into your warehouse?")
    choice = _prompt_choice("Choice", [
        "dlt — tycoon manages it (scaffolds and runs dlt pipelines)",
        "External (Airbyte / Fivetran / Meltano / custom) — tycoon records only",
        "Skip — no ingestion configured",
    ])
    if choice == 1:
        return IngestionTool.dlt, True
    if choice == 2:
        sub = _prompt_choice("Which external tool?", ["Airbyte", "Fivetran", "Meltano", "Custom"])
        tool = [IngestionTool.airbyte, IngestionTool.fivetran, IngestionTool.meltano, IngestionTool.none][sub - 1]
        # "Custom" falls through to IngestionTool.none since we don't have a generic 'external' enum value,
        # but managed=False still signals tycoon won't run it.
        return tool, False
    return IngestionTool.none, False


def _prompt_warehouse(project_name: str) -> tuple[WarehouseType, str]:
    _print_section("Warehouse")
    console.print("Where should your data live?")
    choice = _prompt_choice("Choice", [
        "Local DuckDB at ./data/warehouse.duckdb  [recommended]",
        "Use an existing DuckDB file (provide path)",
        "Cloud — MotherDuck / Snowflake / BigQuery",
    ])
    if choice == 1:
        return WarehouseType.duckdb, "data/warehouse.duckdb"
    if choice == 2:
        raw = typer.prompt("Path to your DuckDB file", default="data/warehouse.duckdb")
        return WarehouseType.duckdb, raw
    # Cloud
    cloud_sub = _prompt_choice("Cloud warehouse", ["MotherDuck", "Snowflake", "BigQuery"])
    if cloud_sub == 1:
        md_name = typer.prompt("MotherDuck database name", default=project_name.replace("-", "_"))
        return WarehouseType.motherduck, f"md:{md_name}"
    if cloud_sub == 2:
        info("Snowflake: tycoon will write your dbt profile; query/schema commands are DuckDB-only for now.")
        return WarehouseType.snowflake, ""
    info("BigQuery: tycoon will write your dbt profile; query/schema commands are DuckDB-only for now.")
    return WarehouseType.bigquery, ""


def _prompt_dbt(
    target: Path,
    project_name: str,
    detected: DetectionResults,
) -> tuple[TransformationTool, bool, str | None]:
    """Returns (tool, managed, path)."""
    _print_section("dbt (transformation)")
    console.print("How should tycoon handle dbt?")

    options: list[str] = []
    detected_paths: list[Path] = [d.path for d in detected.dbt]
    for item in detected.dbt:
        options.append(f"Use detected project at {item.path} ({item.kind})")

    default_new = target.parent / f"{project_name}-dbt"
    options.append(f"Create new dbt project at {default_new} (sibling repo)")
    options.append("Register existing project (local path or GitHub URL)")
    options.append("Skip — `tycoon data transform` becomes a no-op")

    choice = _prompt_choice("Choice", options)

    # Detected
    if choice <= len(detected_paths):
        return TransformationTool.dbt, False, str(detected_paths[choice - 1])
    # Create new (sibling)
    if choice == len(detected_paths) + 1:
        return TransformationTool.dbt, True, str(default_new)
    # Register existing
    if choice == len(detected_paths) + 2:
        registered = _prompt_register_project("dbt", default_new)
        if registered:
            return TransformationTool.dbt, False, registered
        return TransformationTool.none, False, None
    # Skip
    return TransformationTool.none, False, None


def _prompt_rill(
    target: Path,
    detected: DetectionResults,
) -> tuple[BITool, bool, str | None]:
    """Returns (tool, managed, path)."""
    _print_section("Rill (BI)")
    console.print("How should tycoon handle Rill?")

    options: list[str] = []
    detected_paths: list[Path] = [d.path for d in detected.rill]
    for item in detected.rill:
        options.append(f"Use detected project at {item.path} ({item.kind})")

    default_new = target / "rill"
    options.append(f"Create new inline at {default_new}")
    options.append("Register existing project (local path)")
    options.append("Skip — `tycoon data analyze --rill` becomes a no-op")

    choice = _prompt_choice("Choice", options)

    # Detected
    if choice <= len(detected_paths):
        return BITool.rill, False, str(detected_paths[choice - 1])
    # Create new (inline)
    if choice == len(detected_paths) + 1:
        return BITool.rill, True, str(default_new)
    # Register
    if choice == len(detected_paths) + 2:
        registered = _prompt_register_project("Rill", default_new)
        if registered:
            return BITool.rill, False, registered
        return BITool.none, False, None
    # Skip
    return BITool.none, False, None


def _extract_dbt_duckdb_path(dbt_project_dir: Path) -> str | None:
    """Extract the DuckDB path from a dbt project's active profile.

    Returns an absolute path string, or None if:
    - ``dbt_project.yml`` missing or unreadable
    - no ``profiles.yml`` in the project dir or ``~/.dbt/``
    - the target's ``type`` is not ``duckdb``
    """
    try:
        project_yml = yaml.safe_load((dbt_project_dir / "dbt_project.yml").read_text())
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(project_yml, dict):
        return None
    profile_name = project_yml.get("profile")
    if not profile_name:
        return None

    for candidate in (
        dbt_project_dir / "profiles.yml",
        Path.home() / ".dbt" / "profiles.yml",
    ):
        if not candidate.exists():
            continue
        try:
            profiles = yaml.safe_load(candidate.read_text())
        except (OSError, yaml.YAMLError):
            continue
        if not isinstance(profiles, dict):
            continue
        profile = profiles.get(profile_name)
        if not isinstance(profile, dict):
            continue
        target_name = profile.get("target", "dev")
        target = profile.get("outputs", {}).get(target_name, {})
        if not isinstance(target, dict) or target.get("type") != "duckdb":
            return None
        path = target.get("path")
        if not path:
            return None
        abs_path = Path(path)
        if not abs_path.is_absolute():
            abs_path = (dbt_project_dir / abs_path).resolve()
        return str(abs_path)
    return None


def _maybe_align_warehouse(wizard_warehouse_path: str, dbt_project_dir: Path) -> str:
    """Warn if the dbt project targets a different DuckDB than the wizard's
    warehouse choice. Prompt to adopt the dbt path."""
    dbt_path = _extract_dbt_duckdb_path(dbt_project_dir)
    if not dbt_path:
        return wizard_warehouse_path

    user_abs = Path(wizard_warehouse_path).expanduser()
    if not user_abs.is_absolute():
        user_abs = (Path.cwd() / user_abs).resolve()
    else:
        user_abs = user_abs.resolve()

    if str(user_abs) == dbt_path:
        return wizard_warehouse_path

    console.print()
    warn(
        f"Your dbt project targets [bold]{dbt_path}[/bold], "
        f"but you chose [bold]{wizard_warehouse_path}[/bold] for the warehouse."
    )
    info("If these diverge, dbt writes to one file and `tycoon data query` reads from another.")
    adopt = typer.confirm(
        f"Use the dbt project's path ({dbt_path}) as tycoon's warehouse?",
        default=True,
    )
    if adopt:
        success(f"Adopted {dbt_path} as the warehouse.")
        return dbt_path
    return wizard_warehouse_path


def _prompt_orchestrator() -> tuple[OrchestratorTool, bool]:
    _print_section("Orchestrator")
    console.print("How should tycoon handle scheduling?")
    choice = _prompt_choice("Choice", [
        "Dagster — tycoon manages it (runs `dagster dev`, auto-generates assets)",
        "External (Airflow / Prefect / Dagster Cloud / other) — tycoon records only",
        "Skip — I'll run pipelines manually via tycoon CLI",
    ])
    if choice == 1:
        return OrchestratorTool.dagster, True
    if choice == 2:
        sub = _prompt_choice("Which external orchestrator?", ["Airflow", "Prefect", "Other"])
        tool = [OrchestratorTool.airflow, OrchestratorTool.prefect, OrchestratorTool.other][sub - 1]
        return tool, False
    return OrchestratorTool.none, False


def _run_wizard(target: Path, project_name: str) -> WizardResult:
    """Run the interactive setup questionnaire, per-component.

    Order follows the data flow: ingestion → warehouse → dbt → rill → orchestrator.
    """
    detected = _detect_existing(target)
    if detected.has_any():
        info("Detected existing components:")
        for item in detected.dbt:
            console.print(f"  [dim]dbt   [{item.kind}]:[/dim] {item.path}")
        for item in detected.rill:
            console.print(f"  [dim]rill  [{item.kind}]:[/dim] {item.path}")
        for item in detected.warehouse:
            console.print(f"  [dim]warehouse [{item.kind}]:[/dim] {item.path}")
        console.print()

    ingestion, ingestion_managed = _prompt_ingestion()
    warehouse, warehouse_path = _prompt_warehouse(project_name)
    transformation, transformation_managed, dbt_path = _prompt_dbt(target, project_name, detected)

    # Alignment check: if dbt project wasn't just scaffolded by us, see if it
    # targets a different DuckDB than the user chose for the warehouse.
    if (
        transformation == TransformationTool.dbt
        and not transformation_managed
        and dbt_path
        and warehouse == WarehouseType.duckdb
    ):
        warehouse_path = _maybe_align_warehouse(warehouse_path, Path(dbt_path))

    bi, bi_managed, rill_path = _prompt_rill(target, detected)
    orchestrator, orchestrator_managed = _prompt_orchestrator()

    stack = StackConfig(
        ingestion=ingestion,
        ingestion_managed=ingestion_managed,
        warehouse=warehouse,
        transformation=transformation,
        transformation_managed=transformation_managed,
        bi=bi,
        bi_managed=bi_managed,
        orchestrator=orchestrator,
        orchestrator_managed=orchestrator_managed,
    )
    return WizardResult(
        stack=stack,
        dbt_path=dbt_path,
        rill_path=rill_path,
        warehouse_path=warehouse_path,
    )


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
        result = _run_wizard(target, project_name)
        console.print()
        scaffold_blank_project(
            target,
            project_name,
            stack=result.stack,
            existing_dbt_path=result.dbt_path,
            existing_warehouse_path=result.warehouse_path,
            existing_rill_path=result.rill_path,
        )
        console.print()
        success(f"Project '{project_name}' initialized successfully!")
        _mode_next_steps(result.stack, result.dbt_path)
