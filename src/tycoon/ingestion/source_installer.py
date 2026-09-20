"""Install dlt extras and a catalog source's own requirements.txt on demand.

Both install paths go through uv, targeting the project's own `.venv` when
one exists (gh-262) and falling back to installing into the ambient
environment, exactly as before, when it doesn't (gh-264). Neither falls back
to plain `pip` if uv isn't on PATH, tycoon is uv-only end to end.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import shutil
import subprocess
from pathlib import Path

from tycoon.utils.console import error, info

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


def _require_uv() -> str | None:
    """Return the uv binary path, or None after printing the standard hint."""
    uv = shutil.which("uv")
    if uv is None:
        from tycoon.venv import UV_INSTALL_HINT

        error(
            "uv is not installed. tycoon uses uv to install source dependencies.\n"
            f"  Install it with:  {UV_INSTALL_HINT}"
        )
    return uv


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


def install_dlt_extra(source_type: str, python: str | None = None) -> bool:
    """Install the dlt extra for this source type via ``uv pip install``.

    ``python`` targets a specific interpreter (the project's own `.venv`,
    gh-264) with ``--python``; omitted, ``uv`` installs into whatever
    environment it resolves ambiently, unchanged from before gh-264.
    Returns True on success, False on failure (uv missing included).
    """
    extra_name = DLT_EXTRAS.get(source_type, source_type)
    # Pin to the already-installed dlt version so a runtime extra install
    # can't silently upgrade (or downgrade) dlt itself.
    dlt_version = importlib.metadata.version("dlt")
    package = f"dlt[{extra_name}]=={dlt_version}"

    if _require_uv() is None:
        return False

    cmd = ["uv", "pip", "install"]
    if python:
        cmd += ["--python", python]
    cmd.append(package)

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


def install_requirements(requirements_path: Path, python: str | None = None) -> bool:
    """Install exactly what a dlt-init'd source's requirements.txt lists.

    No filtering or second-guessing its contents, whatever dlt wrote is what
    gets installed (gh-264). ``python`` targets the project's own `.venv`
    the same way ``install_dlt_extra`` does. Returns True on success, False
    on failure (uv missing included).
    """
    if _require_uv() is None:
        return False

    cmd = ["uv", "pip", "install"]
    if python:
        cmd += ["--python", python]
    cmd += ["-r", str(requirements_path)]

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
