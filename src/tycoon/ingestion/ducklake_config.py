"""Optional DuckLake / S3 destination configuration.

When the environment variables below are set, pipelines can be redirected
from the local DuckDB file to a remote DuckLake catalog backed by S3.

Usage
-----
Set the following environment variables before running any ``tycoon data sources run``
command:

    TYCOON_DUCKLAKE_CATALOG   — path to the DuckLake catalog file on S3,
                                e.g. ``s3://my-bucket/tycoon/catalog.ducklake``
    AWS_ACCESS_KEY_ID         — AWS credentials (or use instance role / profile)
    AWS_SECRET_ACCESS_KEY
    AWS_DEFAULT_REGION        — e.g. ``us-east-1``

If ``TYCOON_DUCKLAKE_CATALOG`` is not set the pipelines fall back to the local
DuckDB file defined in ``config.raw_db``.
"""

from __future__ import annotations

import os
from pathlib import Path

import dlt

from tycoon.config import config


def get_destination() -> dlt.destinations.duckdb | dlt.destinations.filesystem:  # type: ignore[name-defined]
    """Return the appropriate dlt destination.

    Returns a DuckLake-backed filesystem destination when
    ``TYCOON_DUCKLAKE_CATALOG`` is set, otherwise falls back to the local
    DuckDB file.
    """
    catalog_path = os.environ.get("TYCOON_DUCKLAKE_CATALOG")

    if catalog_path:
        # dlt's filesystem destination can target S3 when boto3 / s3fs is
        # installed.  The bucket root is derived from the catalog path prefix.
        bucket_url = _bucket_root(catalog_path)
        return dlt.destinations.filesystem(bucket_url=bucket_url)

    # Default: local DuckDB
    config.ensure_data_dir()
    return dlt.destinations.duckdb(str(config.raw_db))


def _bucket_root(catalog_path: str) -> str:
    """Extract the S3 bucket root from an s3:// catalog path.

    Example::

        _bucket_root("s3://my-bucket/tycoon/catalog.ducklake")
        # -> "s3://my-bucket"
    """
    if catalog_path.startswith("s3://"):
        parts = catalog_path[len("s3://"):].split("/", 1)
        return f"s3://{parts[0]}"
    # Local path fallback — return parent directory
    return str(Path(catalog_path).parent)


def is_ducklake_enabled() -> bool:
    """Return True if DuckLake mode is active (env var is set)."""
    return bool(os.environ.get("TYCOON_DUCKLAKE_CATALOG"))
