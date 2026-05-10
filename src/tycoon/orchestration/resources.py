"""Shared Dagster resources for tycoon pipelines."""

from __future__ import annotations

from pathlib import Path

from dagster_dbt import DbtCliResource
from dagster_dlt import DagsterDltResource

from tycoon.config import config
from tycoon.dbt_profiles import resolve_profile


def get_dbt_resource() -> DbtCliResource | None:
    """DbtCliResource pointing at the active tycoon project's dbt project.

    Resolves ``profiles_dir`` / ``target`` via :func:`resolve_profile`, so
    Dagster runs inherit the same profile tycoon's CLI uses. Returns
    ``None`` when no ``tycoon.yml`` is available.
    """
    project = config.project
    if project is None:
        return None

    project_root = config.root
    dbt_project_dir = Path(project.dbt_project_dir)
    if not dbt_project_dir.is_absolute():
        dbt_project_dir = (project_root / dbt_project_dir).resolve()
    if not dbt_project_dir.exists():
        return None

    resolved = resolve_profile(
        project_root=project_root,
        dbt_project_dir=dbt_project_dir,
        project_dbt_profiles_dir=project.dbt_profiles_dir,
        project_dbt_profile=project.dbt_profile,
        project_dbt_target=project.dbt_target,
    )

    profiles_dir = resolved.profiles_yml.parent if resolved is not None else dbt_project_dir
    target = resolved.target if resolved is not None else (project.dbt_target or "dev")

    return DbtCliResource(
        project_dir=str(dbt_project_dir),
        profiles_dir=str(profiles_dir),
        target=target,
    )


def get_dlt_resource() -> DagsterDltResource:
    """DagsterDltResource for running dlt pipelines."""
    return DagsterDltResource()
