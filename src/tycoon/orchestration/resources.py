"""Shared Dagster resources for tycoon pipelines."""

from __future__ import annotations

from pathlib import Path

from dagster_dbt import DbtCliResource
from dagster_dlt import DagsterDltResource


PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent


def get_dbt_resource() -> DbtCliResource:
    """DbtCliResource pointing at the tycoon dbt project."""
    dbt_project_dir = PROJECT_DIR / "dbt_project"
    return DbtCliResource(
        project_dir=str(dbt_project_dir),
        profiles_dir=str(dbt_project_dir),
        target="local",
    )


def get_dlt_resource() -> DagsterDltResource:
    """DagsterDltResource for running dlt pipelines."""
    return DagsterDltResource()
