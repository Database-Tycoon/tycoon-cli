"""Shared dbt project definition for use by Dagster and CLI commands."""

from __future__ import annotations

from pathlib import Path

from dagster_dbt import DbtProject

# Assumes this file is in src/tycoon/
# So __file__.parent.parent.parent is the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt_project"

# This is a "vanilla" DbtProject, not to be confused with the Dagster resource.
# It's used to parse the dbt project and find models.
dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    profiles_dir=DBT_PROJECT_DIR,
    target="local",
)
try:
    dbt_project.prepare_if_dev()
except Exception:
    pass
