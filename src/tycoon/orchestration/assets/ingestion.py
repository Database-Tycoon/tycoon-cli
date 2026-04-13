"""Dagster assets wrapping tycoon's dlt ingestion pipelines.

Each registered source in tycoon.yml becomes a Dagster asset that runs
the corresponding dlt pipeline. Assets are tagged for concurrency control
to respect DuckDB's single-writer constraint.
"""

from __future__ import annotations

from pathlib import Path

from dagster import (
    MaterializeResult,
    asset,
)

from tycoon.config import TycoonConfig
from tycoon.ingestion.runner import run_source


PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent


def _make_ingestion_asset(source_name: str):
    """Factory that creates a Dagster asset for a tycoon source."""

    @asset(
        name=f"raw_{source_name.replace('-', '_')}",
        group_name="ingestion",
        tags={"dagster/concurrency_key": "duckdb_writer"},
        description=f"Ingest raw data from '{source_name}' via dlt.",
    )
    def _ingest(context) -> MaterializeResult:
        cfg = TycoonConfig(project_root=PROJECT_DIR)
        source_config = cfg.sources[source_name]

        context.log.info(f"Running dlt pipeline for source: {source_name}")
        context.log.info(f"Type: {source_config.type} | Schema: {source_config.schema_name}")

        cfg.ensure_data_dir()
        _pipeline, load_info = run_source(
            name=source_name,
            source_config=source_config,
            raw_db_path=cfg.raw_db,
        )

        return MaterializeResult(
            metadata={
                "source_type": source_config.type,
                "schema": source_config.schema_name,
                "load_info": str(load_info),
            }
        )

    _ingest.__name__ = f"ingest_{source_name.replace('-', '_')}"
    return _ingest


def build_ingestion_assets() -> list:
    """Read tycoon.yml and build one asset per registered source."""
    cfg = TycoonConfig(project_root=PROJECT_DIR)
    if not cfg.has_project_file:
        return []
    return [_make_ingestion_asset(name) for name in cfg.sources]


ingestion_assets = build_ingestion_assets()
