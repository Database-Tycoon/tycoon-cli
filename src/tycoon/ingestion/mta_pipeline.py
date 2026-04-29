"""dlt pipeline for MTA GTFS static feeds."""

from __future__ import annotations

import io
import zipfile
import csv
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import dlt
import httpx

# MTA GTFS feed URLs
MTA_GTFS_BASE_URL = "https://rrgtfsfeeds.s3.amazonaws.com"
MTA_GTFS_FEEDS = {
    "bronx": f"{MTA_GTFS_BASE_URL}/gtfs_bx.zip",
    "brooklyn": f"{MTA_GTFS_BASE_URL}/gtfs_b.zip",
    "manhattan": f"{MTA_GTFS_BASE_URL}/gtfs_m.zip",
    "queens": f"{MTA_GTFS_BASE_URL}/gtfs_q.zip",
    "staten_island": f"{MTA_GTFS_BASE_URL}/gtfs_si.zip",
    "mta_bus": f"{MTA_GTFS_BASE_URL}/gtfs_busco.zip",
}


def _download_zip(url: str) -> bytes:
    """Download a ZIP file from *url* and return raw bytes."""
    with httpx.Client(timeout=120, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.content


def _parse_csv_from_zip(zip_bytes: bytes, filename: str) -> list[dict[str, str]]:
    """Extract *filename* from a ZIP archive in memory and parse it as CSV."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        if filename not in zf.namelist():
            return []
        with zf.open(filename) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
            return list(reader)


@dlt.resource(name="gtfs_routes", write_disposition="replace")
def gtfs_routes(max_records: int | None = None) -> Iterator[dict[str, Any]]:
    """Yield rows from routes.txt across all MTA borough GTFS feeds."""
    fetched = 0
    for borough, url in MTA_GTFS_FEEDS.items():
        if max_records is not None and fetched >= max_records:
            break

        zip_bytes = _download_zip(url)
        rows = _parse_csv_from_zip(zip_bytes, "routes.txt")

        for row in rows:
            if max_records is not None and fetched >= max_records:
                break
            yield {**row, "_borough": borough}
            fetched += 1


@dlt.resource(name="gtfs_stops", write_disposition="replace")
def gtfs_stops(max_records: int | None = None) -> Iterator[dict[str, Any]]:
    """Yield rows from stops.txt across all MTA borough GTFS feeds."""
    fetched = 0
    for borough, url in MTA_GTFS_FEEDS.items():
        if max_records is not None and fetched >= max_records:
            break

        zip_bytes = _download_zip(url)
        rows = _parse_csv_from_zip(zip_bytes, "stops.txt")

        for row in rows:
            if max_records is not None and fetched >= max_records:
                break
            yield {**row, "_borough": borough}
            fetched += 1


@dlt.source(name="raw_mta")
def mta_source(max_records: int | None = None) -> list[Any]:
    """dlt source bundling MTA GTFS resources."""
    return [
        gtfs_routes(max_records=max_records),
        gtfs_stops(max_records=max_records),
    ]


def run_pipeline(
    raw_db_path: Path,
    max_records: int | None = None,
) -> tuple[dlt.Pipeline, Any]:
    """Create, run, and return the MTA GTFS dlt pipeline."""
    raw_db_path.parent.mkdir(parents=True, exist_ok=True)

    pipeline = dlt.pipeline(
        pipeline_name="mta_gtfs",
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name="raw_mta",
    )

    load_info = pipeline.run(mta_source(max_records=max_records))
    return pipeline, load_info
