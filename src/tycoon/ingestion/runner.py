"""Generic dlt pipeline runner for registered sources.

Runs a dlt pipeline for any source type registered in tycoon.yml.
For known source types (rest_api, sql_database, filesystem), it
dynamically constructs the appropriate dlt source. For NYC-transit
legacy pipelines, it delegates to the existing pipeline modules.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import dlt

from tycoon.ingestion.catalog import CATALOG
from tycoon.ingestion.source_manager import SOURCES_DIR, get_run_module_path, is_source_installed
from tycoon.project import SourceConfig

_UNEXPANDED_ENV_VAR = re.compile(r"\$\{[^}]+\}")


def _check_unexpanded_env_vars(source_config: SourceConfig) -> list[tuple[str, str]]:
    """Return (key, unexpanded_var) pairs for config values still containing ``${VAR}``.

    Both pieces are returned so callers don't need to re-run the regex
    (which loses the typed-Match → str narrowing).
    """
    out: list[tuple[str, str]] = []
    for key, value in source_config.config.items():
        if isinstance(value, str):
            match = _UNEXPANDED_ENV_VAR.search(value)
            if match is not None:
                out.append((key, match.group()))
    return out


class IngestionError(RuntimeError):
    """Raised by the runner with a user-friendly message already set."""


def _classify_error(exc: Exception, source_type: str) -> IngestionError:
    """Convert a raw dlt/requests exception into a friendly IngestionError."""
    msg = str(exc).lower()

    if any(x in msg for x in ("401", "unauthorized", "bad credentials", "invalid token", "invalid api key")):
        return IngestionError(
            f"Authentication failed for '{source_type}'. "
            "Check that your API token or key is correct and hasn't expired."
        )
    if any(x in msg for x in ("403", "forbidden", "permission denied", "insufficient scope")):
        return IngestionError(
            f"Access denied for '{source_type}'. "
            "Your token may lack the required scopes or permissions."
        )
    if any(x in msg for x in ("connectionerror", "connection refused", "name or service not known",
                               "failed to establish", "nodename nor servname provided")):
        return IngestionError(
            f"Could not reach the '{source_type}' API. "
            "Check your internet connection and verify the base URL."
        )
    if "timeout" in msg or "timed out" in msg:
        return IngestionError(
            f"Request to '{source_type}' timed out. "
            "The API may be slow or unreachable — try again later."
        )
    if "rate limit" in msg or "429" in msg:
        return IngestionError(
            f"Rate limited by '{source_type}' API. Wait a moment and try again."
        )

    return IngestionError(str(exc))


# Legacy pipeline modules keyed by source name (NYC transit demo)
_LEGACY_PIPELINES: dict[str, str] = {
    "nyc-dot": "tycoon.ingestion.nyc_dot_pipeline",
    "mta-gtfs": "tycoon.ingestion.mta_pipeline",
    "mta-bus-speeds": "tycoon.ingestion.mta_bus_speeds_pipeline",
}


def _build_rest_api_source(source_config: SourceConfig) -> Any:
    """Build a dlt source for a generic REST API.

    Translates tycoon's flat config shape (as written by ``tycoon data
    sources add rest_api``) into the wrapped ``RESTAPIConfig`` shape
    that dlt's ``rest_api_source`` expects. Specifically:

    - ``base_url`` at the top level moves under ``client.base_url``.
    - A comma-separated ``resources`` string becomes a list. Existing
      lists pass through unchanged.
    - Already-wrapped ``client: {...}`` blocks are left alone — users
      who hand-author the full dlt shape don't get re-wrapped.

    See issue #32 for the bug this fixes.
    """
    from typing import cast

    from dlt.sources.rest_api import rest_api_source
    from dlt.sources.rest_api.typing import RESTAPIConfig

    cfg = _normalize_rest_api_config(source_config.config)
    return rest_api_source(cast(RESTAPIConfig, cfg))


def _normalize_rest_api_config(raw: dict[str, Any]) -> dict[str, Any]:
    """Transform tycoon's flat config into dlt's RESTAPIConfig shape.

    Pure function — no I/O, no dlt imports — so the unit test can
    exercise it without spinning up a real source.
    """
    cfg: dict[str, Any] = {**raw}

    if "client" not in cfg:
        if "base_url" in cfg:
            cfg["client"] = {"base_url": cfg.pop("base_url")}

    resources = cfg.get("resources")
    if isinstance(resources, str):
        cfg["resources"] = [r.strip() for r in resources.split(",") if r.strip()]
    return cfg


def _build_sql_database_source(source_config: SourceConfig) -> Any:
    """Build a dlt source for a SQL database."""
    from dlt.sources.sql_database import sql_database

    cfg = source_config.config
    connection_string = cfg.get("connection_string", "")
    tables = source_config.tables
    if tables:
        return sql_database(connection_string, table_names=tables)
    return sql_database(connection_string)


def _build_filesystem_source(source_config: SourceConfig) -> Any:
    """Build a dlt source for filesystem (local, S3, GCS).

    For CSV and Parquet globs the raw file metadata stream is piped through
    the appropriate dlt transformer so that parsed rows are loaded into
    DuckDB rather than file-level metadata.  Any other glob pattern falls
    back to the raw filesystem source.

    All piped resources land with ``write_disposition="replace"`` so a
    second `tycoon data sources run` rewrites the raw table rather than
    appending. Matches the convention used by every other tycoon-shipped
    pipeline (nyc_dot, mta, mta_bus_speeds). Issue #22.
    """
    from dlt.sources.filesystem import filesystem, read_csv, read_parquet

    cfg = source_config.config
    bucket_url = cfg.get("bucket_url", cfg.get("path", "."))
    file_glob = cfg.get("file_glob", "**/*")

    files = filesystem(bucket_url=bucket_url, file_glob=file_glob)

    glob_lower = file_glob.lower()
    if glob_lower.endswith(".csv") or glob_lower.endswith("*.csv"):
        piped = files | read_csv()
        piped.apply_hints(write_disposition="replace")
        return piped
    if glob_lower.endswith(".parquet") or glob_lower.endswith("*.parquet"):
        piped = files | read_parquet()
        piped.apply_hints(write_disposition="replace")
        return piped

    return files


def _capture_and_refresh_safe(
    raw_db_path: Path,
    pipeline: dlt.Pipeline | None = None,
) -> None:
    """Best-effort dlt observability capture + Rill dashboard refresh.

    Mirrors new dlt loads into ``.tycoon/metadata.duckdb``, enriches with
    trace.pickle details when ``pipeline`` is known, and (if the project has
    a Rill directory) re-exports the usage Parquets + YAMLs. Silently
    no-ops on any failure — ingestion must never break because of
    observability bookkeeping.
    """
    try:
        from tycoon.config import config
        from tycoon.observability import (
            capture_dlt_safe,
            capture_dlt_trace_safe,
            metadata_db_path,
        )
        from tycoon.scaffolding.rill_generator import refresh_usage_dashboards

        meta = metadata_db_path(config.root)
        capture_dlt_safe(meta, raw_db_path)
        pipeline_name = getattr(pipeline, "pipeline_name", None) if pipeline else None
        capture_dlt_trace_safe(meta, pipeline_name)
        refresh_usage_dashboards(project_root=config.root, rill_dir=config.rill_dir)
    except Exception:
        pass


_NATIVE_BUILDERS = {
    "rest_api": _build_rest_api_source,
    "sql_database": _build_sql_database_source,
    "filesystem": _build_filesystem_source,
}


def run_source(
    name: str,
    source_config: SourceConfig,
    raw_db_path: Path,
    max_records: int | None = None,
    **kwargs: Any,
) -> tuple[dlt.Pipeline, Any]:
    """Run a dlt pipeline for a registered source.

    Dispatch order:

    1. **Legacy pipelines** (keyed by source *name*, e.g. ``nyc-dot``)
       delegate to their bespoke module.
    2. **Native builders** (``rest_api`` / ``sql_database`` /
       ``filesystem``) are part of dlt core — they don't need a
       ``dlt init`` step, so they take precedence over the catalog
       check. These types *also* appear in the catalog for browsing
       purposes, but on a fresh machine
       ``~/.tycoon/sources/<type>/`` doesn't exist and the catalog
       path would wrongly error with "not installed".
    3. **Catalog sources** (``github`` / ``stripe`` / ``slack`` etc.)
       require ``dlt init`` to have populated
       ``~/.tycoon/sources/<type>/``; we run them from there.
    4. **Dynamic fallback**: try ``dlt.sources.<type>`` directly.

    Returns (pipeline, load_info).
    """
    # 1. Legacy pipeline delegation (keyed by source name)
    if name in _LEGACY_PIPELINES:
        pipeline, load_info = _run_legacy(
            name, raw_db_path=raw_db_path, max_records=max_records, **kwargs
        )
        _capture_and_refresh_safe(raw_db_path, pipeline=pipeline)
        return pipeline, load_info

    # 2. Native builders win over the catalog path. These types ship with
    #    dlt core and don't need an `~/.tycoon/sources/<type>/` install.
    source_type = source_config.type
    if source_type not in _NATIVE_BUILDERS and source_type in CATALOG:
        # 3. Catalog source dispatch — load from ~/.tycoon/sources/
        pipeline, load_info = _run_catalog(
            source_type, name, source_config, raw_db_path, max_records
        )
        _capture_and_refresh_safe(raw_db_path, pipeline=pipeline)
        return pipeline, load_info

    # Generic pipeline
    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )

    builders = _NATIVE_BUILDERS

    builder = builders.get(source_type)
    if builder is None:
        # Try dynamic import: dlt.sources.<source_type>
        try:
            import importlib

            mod = importlib.import_module(f"dlt.sources.{source_type}")
            source_fn = getattr(mod, source_type, None)
            if source_fn is None:
                raise ImportError(f"No callable '{source_type}' in dlt.sources.{source_type}")
            dlt_source = source_fn(**source_config.config)
        except ImportError as exc:
            raise RuntimeError(
                f"Unknown source type '{source_type}'. "
                f"Install with: tycoon sources add {source_type}"
            ) from exc
    else:
        dlt_source = builder(source_config)

    load_info = pipeline.run(dlt_source)
    _capture_and_refresh_safe(raw_db_path, pipeline=pipeline)
    return pipeline, load_info


def _run_legacy(
    name: str,
    raw_db_path: Path,
    max_records: int | None = None,
    **kwargs: Any,
) -> tuple[dlt.Pipeline, Any]:
    """Run a legacy NYC transit pipeline by importing its module."""
    import importlib

    module_path = _LEGACY_PIPELINES[name]
    mod = importlib.import_module(module_path)
    return mod.run_pipeline(raw_db_path=raw_db_path, max_records=max_records, **kwargs)


def _run_catalog(
    source_type: str,
    name: str,
    source_config: SourceConfig,
    raw_db_path: Path,
    max_records: int | None = None,
) -> tuple[dlt.Pipeline, Any]:
    """Load a catalog source from ~/.tycoon/sources/ and run its pipeline."""
    import importlib

    if not is_source_installed(source_type):
        raise IngestionError(
            f"Source '{source_type}' is not installed. "
            f"Run: tycoon data sources add {source_type}"
        )

    # Warn about unexpanded env vars before hitting the API
    bad_pairs = _check_unexpanded_env_vars(source_config)
    if bad_pairs:
        from tycoon.utils.console import warn
        for key, var in bad_pairs:
            warn(
                f"Config key '{key}' contains an unexpanded env var: {var}\n"
                f"  Set it with: export {var[2:-1]}=<your-value>"
            )

    # Add ~/.tycoon/sources/ to sys.path so dlt-init'd packages are importable
    sources_str = str(SOURCES_DIR)
    if sources_str not in sys.path:
        sys.path.insert(0, sources_str)

    module_path = get_run_module_path(source_type)
    mod = importlib.import_module(module_path)

    try:
        pipeline, load_info = mod.run_pipeline(name, source_config, raw_db_path, max_records=max_records)
    except IngestionError:
        raise
    except Exception as exc:
        raise _classify_error(exc, source_type) from exc

    # Surface any partial job failures (e.g. one resource 401'd)
    try:
        load_info.raise_on_failed_jobs()
    except Exception as exc:
        raise _classify_error(exc, source_type) from exc

    return pipeline, load_info
