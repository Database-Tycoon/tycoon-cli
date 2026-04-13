"""Dagster assets wrapping the tycoon dbt project.

Uses dagster-dbt to parse the dbt manifest and expose each model
as a Dagster asset with full lineage.
"""

from __future__ import annotations

from dagster_dbt import DbtCliResource, dbt_assets

from tycoon.dbt import dbt_project

dbt_project_assets = None

try:
    @dbt_assets(manifest=dbt_project.manifest_path)
    def dbt_project_assets(context, dbt: DbtCliResource):
        """Materialize all dbt models as Dagster assets."""
        yield from dbt.cli(["build"], context=context).stream()
except Exception:
    pass
