"""dlt pipeline for NYC DOT open data (Socrata)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import dlt
import httpx

# NYC DOT dataset constants (Socrata)
NYC_DOT_DOMAIN = "data.cityofnewyork.us"
DATASET_TRAFFIC_SPEEDS = "i4gi-tjb9"
DATASET_BUS_LANES = "ycrg-ses3"
DATASET_TRAFFIC_VOLUME = "7ym2-wayt"
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


@dlt.resource(name="traffic_speeds_nbe", write_disposition="replace")
def traffic_speeds_nbe(max_records: int | None = None) -> Iterator[dict[str, Any]]:
    """Yield records from the NYC DOT traffic speeds (NBE) dataset."""
    for page in _socrata_pages(NYC_DOT_DOMAIN, DATASET_TRAFFIC_SPEEDS, max_records):
        yield from page


@dlt.resource(name="bus_lanes", write_disposition="replace")
def bus_lanes(max_records: int | None = None) -> Iterator[dict[str, Any]]:
    """Yield records from the NYC DOT bus lanes dataset."""
    for page in _socrata_pages(NYC_DOT_DOMAIN, DATASET_BUS_LANES, max_records):
        yield from page


@dlt.resource(name="traffic_volume_counts", write_disposition="replace")
def traffic_volume_counts(max_records: int | None = None) -> Iterator[dict[str, Any]]:
    """Yield records from the NYC DOT traffic volume counts dataset."""
    for page in _socrata_pages(NYC_DOT_DOMAIN, DATASET_TRAFFIC_VOLUME, max_records):
        yield from page


@dlt.source(name="raw_nyc_dot")
def nyc_dot_source(max_records: int | None = None) -> list[Any]:
    """dlt source bundling all NYC DOT resources."""
    return [
        traffic_speeds_nbe(max_records=max_records),
        bus_lanes(max_records=max_records),
        traffic_volume_counts(max_records=max_records),
    ]


def run_pipeline(
    raw_db_path: Path,
    max_records: int | None = None,
) -> tuple[dlt.Pipeline, Any]:
    """Create, run, and return the NYC DOT dlt pipeline."""
    raw_db_path.parent.mkdir(parents=True, exist_ok=True)

    pipeline = dlt.pipeline(
        pipeline_name="nyc_dot",
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name="raw_nyc_dot",
    )

    load_info = pipeline.run(nyc_dot_source(max_records=max_records))
    return pipeline, load_info
