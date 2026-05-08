"""Top-level Dagster Definitions for the tycoon code location."""

from __future__ import annotations

from dagster import (
    Definitions,
    define_asset_job,
)

from tycoon.orchestration.assets.ingestion import ingestion_assets
from tycoon.orchestration.assets.rill import rill_build
from tycoon.orchestration.assets.transforms import dbt_project_assets
from tycoon.orchestration.resources import get_dbt_resource, get_dlt_resource


all_assets = [rill_build]
all_jobs = []

if dbt_project_assets is not None:
    all_assets.append(dbt_project_assets)

if ingestion_assets:
    all_assets.extend(ingestion_assets)

    ingestion_job = define_asset_job(
        name="ingestion_job",
        selection=[a.key for a in ingestion_assets],
        description="Ingest all registered sources sequentially.",
        config={
            "execution": {
                "config": {
                    "multiprocess": {
                        "max_concurrent": 1,
                    }
                }
            }
        },
    )
    all_jobs.append(ingestion_job)

    if dbt_project_assets is not None:
        transform_job = define_asset_job(
            name="transform_job",
            selection=[dbt_project_assets],
            description="Build all dbt models.",
        )
        all_jobs.append(transform_job)

        full_pipeline_job = define_asset_job(
            name="full_pipeline_job",
            selection=ingestion_assets + [dbt_project_assets],
            description="Run full pipeline: ingest all sources then build dbt models.",
        )
        all_jobs.append(full_pipeline_job)

resources: dict = {"dlt": get_dlt_resource()}
if dbt_project_assets is not None:
    dbt_resource = get_dbt_resource()
    if dbt_resource is not None:
        resources["dbt"] = dbt_resource

defs = Definitions(
    assets=all_assets,
    jobs=all_jobs,
    resources=resources,
)
