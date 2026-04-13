"""Install dlt extras on demand for registered source types."""

from __future__ import annotations

import importlib
import shutil
import subprocess

from tycoon.utils.console import info

# dlt pip extras for generic source types (rest_api, sql_database, filesystem).
# Catalog sources (github, slack, stripe, hubspot, notion) are NOT pip extras —
# they are downloaded on demand via `dlt init` by source_manager.py.
DLT_EXTRAS: dict[str, str] = {
    "rest_api": "rest_api",
    "sql_database": "sql_database",
    "filesystem": "filesystem",
    "airtable": "airtable",
    "chess": "chess",
    "facebook_ads": "facebook_ads",
    "google_analytics": "google_analytics",
    "google_sheets": "google_sheets",
    "jira": "jira",
    "mongodb": "mongodb",
    "pipedrive": "pipedrive",
    "salesforce": "salesforce",
    "shopify": "shopify",
    "zendesk": "zendesk",
}


def is_dlt_extra_available(source_type: str) -> bool:
    """Check if the dlt extra for this source type is importable.

    Attempts to import ``dlt.sources.<source_type>`` and returns True if
    the import succeeds, False otherwise.
    """
    module_name = f"dlt.sources.{source_type}"
    try:
        importlib.import_module(module_name)
        return True
    except (ImportError, ModuleNotFoundError):
        return False


def install_dlt_extra(source_type: str) -> bool:
    """Install the dlt extra for this source type.

    Prefers ``uv pip install`` if ``uv`` is on PATH, otherwise falls back
    to ``pip install``. Returns True on success, False on failure.
    """
    extra_name = DLT_EXTRAS.get(source_type, source_type)
    package = f"dlt[{extra_name}]"

    # Prefer uv, fall back to pip
    if shutil.which("uv"):
        cmd = ["uv", "pip", "install", package]
    else:
        cmd = ["pip", "install", package]

    info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False
