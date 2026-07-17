"""Download and manage dlt verified sources on demand.

Sources are installed into ~/.tycoon/sources/ via `dlt init`, then a thin
_run.py shim is written alongside the source package to bridge dlt's native
API with tycoon's run_pipeline(name, source_config, raw_db_path, max_records)
interface.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tycoon.utils.console import info

SOURCES_DIR = Path.home() / ".tycoon" / "sources"

# Per-source shim: imports from the dlt-init'd package, maps tycoon config keys
# to the dlt source function's parameters, and exposes run_pipeline().
_SHIMS: dict[str, str] = {
    "github": """\
from __future__ import annotations
from pathlib import Path
from typing import Any
import dlt
from github import github_reactions

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    source = github_reactions(
        owner=cfg.get("owner", ""),
        name=cfg.get("repo", ""),
        access_token=cfg.get("access_token", ""),
    )
    if max_records:
        source = source.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(source)
""",
    "slack": """\
from __future__ import annotations
from pathlib import Path
from typing import Any
import dlt
from slack_source import slack_source

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    channel_ids = cfg.get("channel_ids", "")
    channels = [c.strip() for c in channel_ids.split(",") if c.strip()] or None
    source = slack_source(
        access_token=cfg.get("access_token", ""),
        channels=channels,
    )
    if max_records:
        source = source.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(source)
""",
    "stripe_analytics": """\
from __future__ import annotations
from pathlib import Path
from typing import Any
import dlt
from stripe_analytics import stripe_source

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    source = stripe_source(
        stripe_secret_key=cfg.get("stripe_secret_key", ""),
    )
    if max_records:
        source = source.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(source)
""",
    "hubspot": """\
from __future__ import annotations
from pathlib import Path
from typing import Any
import dlt
from hubspot import hubspot

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    source = hubspot(api_key=cfg.get("api_key", ""))
    if max_records:
        source = source.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(source)
""",
    "notion": """\
from __future__ import annotations
from pathlib import Path
from typing import Any
import dlt
from notion import notion_databases

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    raw_ids = cfg.get("database_ids", "")
    database_ids = [d.strip() for d in raw_ids.split(",") if d.strip()] or None
    source = notion_databases(
        database_ids=database_ids,
        api_key=cfg.get("api_key", ""),
    )
    if max_records:
        source = source.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(source)
""",
    "google_sheets": """\
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import dlt
from google_sheets import google_spreadsheet

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    spreadsheet = cfg.get("spreadsheet_url_or_id", "")
    raw_ranges = cfg.get("range_names", "")
    range_names = [r.strip() for r in raw_ranges.split(",") if r.strip()] or None

    # Service-account key: read the JSON and hand dlt the parsed dict, which it
    # coerces into GcpServiceAccountCredentials. If the path is empty/missing we
    # pass nothing, letting dlt fall back to its own resolution (env / secrets).
    kwargs: dict[str, Any] = {"spreadsheet_url_or_id": spreadsheet}
    if range_names:
        kwargs["range_names"] = range_names
    creds_path = cfg.get("credentials_path", "")
    if creds_path:
        key_file = Path(creds_path).expanduser()
        if key_file.is_file():
            kwargs["credentials"] = json.loads(key_file.read_text(encoding="utf-8"))

    source = google_spreadsheet(**kwargs)
    if max_records:
        source = source.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(source)
""",
    "rest_api": """\
from __future__ import annotations
from typing import Any
import dlt
from dlt.sources.rest_api import rest_api_source

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    base_url = cfg.get("base_url", "https://pokeapi.co/api/v2/")
    raw_resources = cfg.get("resources", "pokemon,berry,type")
    resource_names = [r.strip() for r in raw_resources.split(",") if r.strip()]
    source = rest_api_source({
        "client": {"base_url": base_url},
        "resources": resource_names,
    })
    if max_records:
        source = source.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(source)
""",
    "filesystem": """\
from __future__ import annotations
from pathlib import Path
from typing import Any
import re
import dlt
from dlt.sources.filesystem import filesystem, read_csv

def run_pipeline(name, source_config, raw_db_path, max_records=None):
    cfg = source_config.config
    path = Path(cfg.get("path", "")).expanduser()

    # If path is a single CSV file, use its parent dir as bucket and filename as glob.
    # If path is a directory (or glob pattern), use it directly.
    if path.suffix.lower() == ".csv" and path.is_file():
        bucket_url = str(path.parent)
        file_glob = path.name
        # Use the filename stem as table name (e.g. "sales_data" from "sales_data.csv")
        table_name = re.sub(r"[^a-z0-9]+", "_", path.stem.lower()).strip("_") or "data"
    else:
        bucket_url = str(path)
        file_glob = "**/*.csv"
        table_name = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "data"

    resource = (filesystem(bucket_url=bucket_url, file_glob=file_glob) | read_csv()).with_name(table_name)
    if max_records:
        resource = resource.add_limit(max_records)
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(resource)
""",
}

# Sources that ship with dlt itself — no `dlt init` needed.
_BUILTIN_SOURCES: set[str] = {"rest_api", "filesystem"}

# Maps catalog source type → dlt init source name (they sometimes differ)
_DLT_INIT_NAME: dict[str, str] = {
    "github": "github",
    "slack": "slack",
    "stripe": "stripe_analytics",
    "hubspot": "hubspot",
    "notion": "notion",
    "google_sheets": "google_sheets",
}


def is_source_installed(source_type: str) -> bool:
    """Return True if the source package AND its _run.py shim are both present."""
    if source_type in _BUILTIN_SOURCES:
        return (SOURCES_DIR / source_type / "_run.py").exists()
    dlt_name = _DLT_INIT_NAME.get(source_type, source_type)
    source_pkg = SOURCES_DIR / dlt_name
    return (
        source_pkg.is_dir()
        and (source_pkg / "__init__.py").exists()
        and (source_pkg / "_run.py").exists()
    )


def install_source(source_type: str) -> bool:
    """Install a source and write its _run.py shim.

    For built-in dlt sources (rest_api, filesystem) this just writes the shim.
    For verified sources it runs `dlt init <source> duckdb` only if the package
    isn't already present, then always writes the _run.py shim.

    Returns True on success, False on failure.
    """
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    if source_type in _BUILTIN_SOURCES:
        shim = _SHIMS.get(source_type)
        if shim:
            shim_dir = SOURCES_DIR / source_type
            shim_dir.mkdir(exist_ok=True)
            (shim_dir / "_run.py").write_text(shim)
        return True

    dlt_name = _DLT_INIT_NAME.get(source_type, source_type)
    source_pkg = SOURCES_DIR / dlt_name

    # Only run `dlt init` if the package isn't already downloaded.
    # Re-running dlt init with captured stdin on an existing package can fail
    # when dlt prompts "overwrite?" with no tty to answer.
    if not (source_pkg.is_dir() and (source_pkg / "__init__.py").exists()):
        info(
            f"Downloading verified source '{dlt_name}' from dlt-hub/verified-sources "
            f"(github.com) into {SOURCES_DIR} — this code runs during ingestion."
        )
        result = subprocess.run(
            [sys.executable, "-m", "dlt", "init", dlt_name, "duckdb"],
            cwd=SOURCES_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return False

    # Always (re)write the shim — idempotent.
    shim = _SHIMS.get(dlt_name)
    if shim:
        shim_path = source_pkg / "_run.py"
        shim_path.write_text(shim)

    return True


def get_run_module_path(source_type: str) -> str:
    """Return the dotted module path for the _run shim, e.g. 'github._run'."""
    if source_type in _BUILTIN_SOURCES:
        return f"{source_type}._run"
    dlt_name = _DLT_INIT_NAME.get(source_type, source_type)
    return f"{dlt_name}._run"
