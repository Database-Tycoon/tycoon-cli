"""tycoon register — attach an existing dbt or Rill project to tycoon.yml."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
import yaml

from tycoon.commands.init import (
    _clone_repo,
    _extract_dbt_duckdb_path,
)
from tycoon.config import config
from tycoon.project import (
    BITool,
    PROJECT_FILENAME,
    TransformationTool,
    WarehouseType,
)
from tycoon.utils.console import console, error, header, info, success, warn


app = typer.Typer(
    help="Attach an existing dbt or Rill project to the current tycoon.yml.",
    no_args_is_help=True,
)


def _resolve_path_or_url(source: str, default_clone_dest: Path) -> Path | None:
    """Accept a local path or a git URL. Clone if URL. Return resolved absolute path."""
    if source.startswith(("http://", "https://", "git@")):
        clone_here = typer.confirm(
            f"Clone into {default_clone_dest}?",
            default=True,
        )
        dest = default_clone_dest
        if not clone_here:
            dest = Path(
                typer.prompt("Where should the project be cloned?", default=str(default_clone_dest))
            ).expanduser().resolve()
        if not _clone_repo(source, dest):
            return None
        return dest

    path = Path(source).expanduser().resolve()
    if not path.exists():
        error(f"Path does not exist: {path}")
        return None
    return path


def _require_tycoon_yml() -> Path:
    """Resolve the tycoon.yml path, or bail if no project."""
    if not config.has_project_file:
        error(
            "No tycoon.yml found in the current project. "
            "Run `tycoon init` first, or cd into an existing tycoon project."
        )
        raise typer.Exit(1)
    return config.root / PROJECT_FILENAME


def _load_raw_tycoon_yml(path: Path) -> dict:
    """Load tycoon.yml as a raw dict (preserving unknown keys on write)."""
    raw = yaml.safe_load(path.read_text()) or {}
    if not isinstance(raw, dict):
        error(f"tycoon.yml is not a mapping: {path}")
        raise typer.Exit(1)
    return raw


def _write_raw_tycoon_yml(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


@app.command(name="dbt")
def register_dbt(
    source: Annotated[
        str,
        typer.Argument(help="Local path or GitHub URL of the dbt project to register."),
    ],
) -> None:
    """Attach an existing dbt project to the current tycoon.yml."""
    header("Register dbt project")

    yml_path = _require_tycoon_yml()
    raw = _load_raw_tycoon_yml(yml_path)

    existing_dbt = raw.get("dbt_project_dir")
    if existing_dbt:
        warn(f"tycoon.yml already has dbt_project_dir = {existing_dbt!r}.")
        if not typer.confirm("Overwrite it?", default=False):
            info("Aborted; no changes made.")
            raise typer.Exit(0)

    default_clone = config.root.parent / f"{raw.get('name', config.root.name)}-dbt"
    resolved = _resolve_path_or_url(source, default_clone)
    if resolved is None:
        raise typer.Exit(1)
    if not (resolved / "dbt_project.yml").exists():
        error(f"{resolved} does not contain a dbt_project.yml")
        raise typer.Exit(1)

    # Write path relative to tycoon.yml when possible, otherwise absolute
    try:
        import os
        rel = os.path.relpath(resolved, config.root)
        raw["dbt_project_dir"] = rel
    except ValueError:
        raw["dbt_project_dir"] = str(resolved)

    # Update stack to reflect "external dbt"
    stack = raw.setdefault("stack", {})
    stack["transformation"] = TransformationTool.dbt.value
    stack["transformation_managed"] = False

    # Warehouse alignment offer
    dbt_warehouse = _extract_dbt_duckdb_path(resolved)
    if dbt_warehouse:
        current_warehouse = raw.get("database", {}).get("warehouse", "")
        current_abs = (
            Path(current_warehouse).expanduser()
            if current_warehouse.startswith(("/", "~"))
            else config.root / current_warehouse
        )
        current_abs = current_abs.resolve() if current_abs.exists() or current_abs.is_absolute() else (config.root / current_warehouse).resolve()
        if str(current_abs) != dbt_warehouse:
            console.print()
            warn(
                f"Your dbt project targets {dbt_warehouse}, "
                f"but tycoon.yml has warehouse = {current_warehouse!r}."
            )
            if typer.confirm(f"Update warehouse to {dbt_warehouse}?", default=True):
                raw.setdefault("database", {})["warehouse"] = dbt_warehouse
                if raw["database"].get("raw", "") == current_warehouse:
                    raw["database"]["raw"] = dbt_warehouse
                stack["warehouse"] = WarehouseType.duckdb.value

    _write_raw_tycoon_yml(yml_path, raw)
    success(f"Registered dbt project at {resolved}")
    info(f"Updated {yml_path.name}.")


@app.command(name="rill")
def register_rill(
    source: Annotated[
        str,
        typer.Argument(help="Local path or GitHub URL of the Rill project to register."),
    ],
) -> None:
    """Attach an existing Rill project to the current tycoon.yml."""
    header("Register Rill project")

    yml_path = _require_tycoon_yml()
    raw = _load_raw_tycoon_yml(yml_path)

    existing_rill = raw.get("rill_dir")
    if existing_rill:
        warn(f"tycoon.yml already has rill_dir = {existing_rill!r}.")
        if not typer.confirm("Overwrite it?", default=False):
            info("Aborted; no changes made.")
            raise typer.Exit(0)

    default_clone = config.root.parent / f"{raw.get('name', config.root.name)}-rill"
    resolved = _resolve_path_or_url(source, default_clone)
    if resolved is None:
        raise typer.Exit(1)
    if not (resolved / "rill.yaml").exists():
        error(f"{resolved} does not contain a rill.yaml")
        raise typer.Exit(1)

    import os
    try:
        rel = os.path.relpath(resolved, config.root)
        raw["rill_dir"] = rel
    except ValueError:
        raw["rill_dir"] = str(resolved)

    stack = raw.setdefault("stack", {})
    stack["bi"] = BITool.rill.value
    stack["bi_managed"] = False

    _write_raw_tycoon_yml(yml_path, raw)
    success(f"Registered Rill project at {resolved}")
    info(f"Updated {yml_path.name}.")
