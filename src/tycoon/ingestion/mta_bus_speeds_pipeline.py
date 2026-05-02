"""dlt pipeline for MTA bus segment speeds (data.ny.gov Socrata)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import dlt
import httpx

# MTA Bus Speeds dataset constants (NY State Socrata)
MTA_BUS_SPEEDS_DOMAIN = "data.ny.gov"
MTA_BUS_SPEEDS_DATASETS = {
    "2023-2024": "58t6-89vi",
    "2025": "kufs-yh3x",
}
SOCRATA_PAGE_SIZE = 50_000


def _socrata_pages(
    domain: str,
    dataset_id: str,
    max_records: int | None,
) -> Iterator[list[dict[str, Any]]]:
    """Paginate through a Socrata JSON endpoint and yield pages of records."""
    url = f"https://{domain}/resource/{dataset_id}.json"
    fetched = 0

    with httpx.Client(timeout=60) as client:
        offset = 0
        while True:
            limit = SOCRATA_PAGE_SIZE
            if max_records is not None:
                remaining = max_records - fetched
                if remaining <= 0:
                    break
                limit = min(limit, remaining)

            params = {
                "$limit": limit,
                "$offset": offset,
                "$order": ":id",
            }
            response = client.get(url, params=params)
            response.raise_for_status()
            page: list[dict[str, Any]] = response.json()

            if not page:
                break

            yield page
            fetched += len(page)
            offset += len(page)

            if len(page) < limit:
                break




@dlt.source(name="raw_mta_bus_speeds")
def mta_bus_speeds_source(
    years: list[str] | None = None,
    max_records: int | None = None,
) -> Iterator[Any]:
    """
    dlt source for MTA bus speeds. Creates one resource per year/dataset.

    If `years` is not provided, all available datasets will be ingested.
    """
    datasets_to_ingest = MTA_BUS_SPEEDS_DATASETS
    if years:
        datasets_to_ingest = {
            year_range: dataset_id
            for year_range, dataset_id in MTA_BUS_SPEEDS_DATASETS.items()
            if year_range in years
        }

    for year_range, dataset_id in datasets_to_ingest.items():
        # dlt resource names must be valid python identifiers
        resource_name = f"bus_segment_speeds_{year_range.replace('-', '_')}"

        yield dlt.resource(
            _socrata_pages(MTA_BUS_SPEEDS_DOMAIN, dataset_id, max_records),
            name=resource_name,
            write_disposition="replace",
        )


def run_pipeline(
    raw_db_path: Path,
    max_records: int | None = None,
    years: list[str] | None = None,
) -> tuple[dlt.Pipeline, Any]:
    """Create, run, and return the MTA bus speeds dlt pipeline."""
    raw_db_path.parent.mkdir(parents=True, exist_ok=True)

    pipeline = dlt.pipeline(
        pipeline_name="mta_bus_speeds",
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name="raw_mta_bus_speeds",
    )

    source = mta_bus_speeds_source(max_records=max_records, years=years)
    load_info = pipeline.run(source)
    return pipeline, load_info
