"""Generic dlt pipeline runner for registered sources.

Runs a dlt pipeline for any source type registered in tycoon.yml.
For known source types (rest_api, sql_database, filesystem), it
dynamically constructs the appropriate dlt source. For NYC-transit
legacy pipelines, it delegates to the existing pipeline modules.
"""

from __future__ import annotations

import glob
import re
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import dlt

from tycoon.core.events import RunCompleted, RunFailed, RunStarted
from tycoon.ingestion.catalog import CATALOG
from tycoon.ingestion.source_manager import SOURCES_DIR, get_run_module_path, is_source_installed
from tycoon.project import SourceConfig

_UNEXPANDED_ENV_VAR = re.compile(r"\$\{[^}]+\}")


def _check_unexpanded_env_vars(source_config: SourceConfig) -> list[tuple[str, str]]:
    """Return (key, unexpanded_var) pairs for config values still containing ``${VAR}``.

    Both pieces are returned so callers don't need to re-run the regex
    (which loses the typed-Match → str narrowing). Scans both the flat
    ``config`` dict and each entry of the gh-224 multi-resource ``resources``
    list, since a resource's own path/file_glob carries the same
    machine-specific values the flat shape does.
    """
    out: list[tuple[str, str]] = []
    for key, value in source_config.config.items():
        if isinstance(value, str):
            match = _UNEXPANDED_ENV_VAR.search(value)
            if match is not None:
                out.append((key, match.group()))
    for i, resource in enumerate(source_config.resources or []):
        for field in ("path", "file_glob"):
            value = getattr(resource, field)
            match = _UNEXPANDED_ENV_VAR.search(value)
            if match is not None:
                out.append((f"resources[{i}].{field}", match.group()))
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
            f"Access denied for '{source_type}'. Your token may lack the required scopes or permissions."
        )
    if any(
        x in msg
        for x in (
            "connectionerror",
            "connection refused",
            "name or service not known",
            "failed to establish",
            "nodename nor servname provided",
        )
    ):
        return IngestionError(
            f"Could not reach the '{source_type}' API. Check your internet connection and verify the base URL."
        )
    if "timeout" in msg or "timed out" in msg:
        return IngestionError(
            f"Request to '{source_type}' timed out. The API may be slow or unreachable — try again later."
        )
    if "rate limit" in msg or "429" in msg:
        return IngestionError(f"Rate limited by '{source_type}' API. Wait a moment and try again.")

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


def _local_glob_matches_nothing(bucket_url: str, file_glob: str) -> bool:
    """Return True when a local filesystem glob matches no files.

    Only checks local paths (a plain path or a ``file://`` URL). Remote
    buckets (``s3://``, ``gs://``, ``az://``) aren't supported yet and are
    never reported as empty rather than guessed at. Issue #223.
    """
    local_dir = _local_fs_path(bucket_url)
    if local_dir is None:
        return False

    import glob as glob_module

    pattern = str(local_dir / file_glob)
    return not glob_module.glob(pattern, recursive=True)


def _local_fs_path(url: str) -> Path | None:
    """Return the local filesystem path ``url`` points at, or ``None`` if remote.

    A plain path and a ``file://`` URL are both local; any other scheme
    (``s3://``, ``gs://``, ``https://``) is remote.
    """
    if url.startswith("file://"):
        from urllib.parse import urlparse
        from urllib.request import url2pathname

        return Path(url2pathname(urlparse(url).path))
    if "://" in url:
        return None
    return Path(url).expanduser()


def _split_single_file_path(path: str, file_glob: str) -> tuple[str, str]:
    """Turn a ``path`` that names one local file into ``(parent_dir, file_name)``.

    dlt's filesystem source treats ``bucket_url`` as a directory and
    evaluates ``file_glob`` underneath it, so a file passed as the bucket
    matches nothing and the run loads zero rows while reporting success.
    `tycoon data sources add filesystem` writes exactly that shape when the
    user answers the path prompt with a file. Issue #238.

    A glob alongside a file path is ambiguous (it can never match anything
    under a file), so it fails rather than guessing which one was meant.
    A ``file://`` URL counts as local. The file name comes back
    glob-escaped so a name like ``sales[1].csv`` matches only itself.
    Remote URLs and anything that isn't an existing local file pass through
    unchanged.
    """
    target = _local_fs_path(path)
    if target is None or not target.is_file():
        return path, file_glob
    if file_glob:
        raise IngestionError(
            f"Filesystem path {path!r} is a file, but file_glob {file_glob!r} is also set. "
            "path must be a directory when file_glob is set. Either point path at the "
            f"directory ({str(target.parent)!r}) and keep the glob, or remove file_glob "
            "to load just this file."
        )
    return str(target.parent), glob.escape(target.name)


def _unmatched_glob_message(table_name: str, bucket_url: str, file_glob: str) -> str:
    return f"'{table_name}': no files matched glob {file_glob!r} under {bucket_url!r}."


def _unmatched_local_globs(name: str, source_config: SourceConfig) -> list[str]:
    """Describe each local filesystem glob in ``source_config`` that matches no files.

    Mirrors the targets ``_build_filesystem_source`` builds, so the ledger
    can name what was skipped (gh-240). The flat shape is reported under
    the source's own name, which is the table it lands in.
    """
    if source_config.type != "filesystem":
        return []
    if source_config.resources:
        targets = [(r.table_name, r.path, r.file_glob, "") for r in source_config.resources]
    else:
        cfg = source_config.config
        bucket_url = cfg.get("bucket_url") or cfg.get("path") or ""
        targets = [(name, bucket_url, cfg.get("file_glob") or "", "**/*")]

    messages: list[str] = []
    for table_name, path, file_glob, default_glob in targets:
        try:
            bucket_url, file_glob = _split_single_file_path(path, file_glob)
        except IngestionError:
            continue
        file_glob = file_glob or default_glob
        if bucket_url and file_glob and _local_glob_matches_nothing(bucket_url, file_glob):
            messages.append(_unmatched_glob_message(table_name, bucket_url, file_glob))
    return messages


def _build_filesystem_resource(bucket_url: str, file_glob: str, table_name: str, default_glob: str = "") -> Any | None:
    """Build one named dlt resource for a single (bucket_url, file_glob) pair.

    For CSV, Parquet, and JSONL globs the raw file metadata stream is piped
    through the appropriate dlt transformer so that parsed rows are loaded
    into DuckDB rather than file-level metadata. Any other glob pattern
    falls back to the raw filesystem resource (file listings, not parsed
    rows) with a warning, since that's rarely what's actually wanted for a
    tycoon filesystem source. Issue #228.

    The resource is renamed to ``table_name`` before being returned: dlt's
    read_csv()/read_parquet()/read_jsonl() transformers otherwise always
    name their resource "read_csv"/"read_parquet"/"read_jsonl" regardless
    of input, which collides when more than one resource lands in the same
    schema. Issue #222.

    Lands with ``write_disposition="replace"`` so a second
    `tycoon data sources run` rewrites the raw table rather than appending.
    Matches the convention used by every other tycoon-shipped pipeline
    (nyc_dot, mta, mta_bus_speeds). Issue #22.

    A ``bucket_url`` naming a single local file is split into its parent
    directory plus the file name (issue #238). ``default_glob`` applies only
    when no glob was given and the path is a directory.

    Raises ``IngestionError`` if ``bucket_url`` or ``file_glob`` is empty.
    Returns ``None``, with a warning, when a local glob matches no files:
    running an empty resource under ``replace`` would truncate a table that
    already holds rows, so the resource is left out of the run instead.
    Issues #223 and #240.
    """
    bucket_url, file_glob = _split_single_file_path(bucket_url, file_glob)
    file_glob = file_glob or default_glob
    if not bucket_url or not file_glob:
        raise IngestionError(
            f"Resource '{table_name}' is missing a path or file_glob. "
            "Both are required, e.g. `path: data/input`, `file_glob: '*.csv'`."
        )

    if _local_glob_matches_nothing(bucket_url, file_glob):
        from tycoon.utils.console import warn

        warn(
            f"{_unmatched_glob_message(table_name, bucket_url, file_glob)} "
            "Nothing was loaded for it, and its existing table was left as it was."
        )
        return None

    from dlt.sources.filesystem import filesystem, read_csv, read_jsonl, read_parquet

    files = filesystem(bucket_url=bucket_url, file_glob=file_glob)

    glob_lower = file_glob.lower()
    if glob_lower.endswith(".csv") or glob_lower.endswith("*.csv"):
        piped = files | read_csv()
    elif glob_lower.endswith(".parquet") or glob_lower.endswith("*.parquet"):
        piped = files | read_parquet()
    elif glob_lower.endswith(".jsonl") or glob_lower.endswith("*.jsonl"):
        piped = files | read_jsonl()
    else:
        from tycoon.utils.console import warn

        warn(
            f"'{table_name}': file_glob {file_glob!r} isn't a recognized format "
            "(.csv, .parquet, .jsonl) for row-level parsing. Falling back to raw "
            "file metadata (path, size, modification time), not parsed rows."
        )
        piped = files

    piped.apply_hints(write_disposition="replace")
    return piped.with_name(table_name)


def _build_filesystem_source(source_config: SourceConfig) -> Any:
    """Build a dlt source for filesystem (local, S3, GCS).

    If ``source_config.resources`` is set (gh-224's multi-resource shape),
    builds one named resource per entry and returns them as a list — dlt's
    ``pipeline.run()`` accepts a list of resources directly, the same shape
    dlt's own ``readers()`` source uses to bundle multiple resources.

    Otherwise falls back to the older flat ``config.path``/``config.file_glob``
    shape via ``_build_filesystem_resource`` with a placeholder name: the
    caller (``run_source``) renames the single-resource result after the
    tycoon source's own name regardless, since the flat shape has no
    per-resource table name to use instead. Reusing that helper here (rather
    than duplicating the CSV/Parquet dispatch) also gets this path the same
    validation and zero-match warning as the multi-resource shape (gh-223).

    Resources whose local glob matches no files are dropped, so this returns
    ``None`` (flat shape) or an empty list when nothing is left to load
    (gh-240).
    """
    if source_config.resources:
        built = [_build_filesystem_resource(r.path, r.file_glob, r.table_name) for r in source_config.resources]
        return [resource for resource in built if resource is not None]

    cfg = source_config.config
    bucket_url = cfg.get("bucket_url") or cfg.get("path") or ""
    file_glob = cfg.get("file_glob") or ""
    return _build_filesystem_resource(bucket_url, file_glob, "resource", default_glob="**/*")


# Table names dlt's read_csv()/read_parquet() produced before this fix
# renamed the resource after the tycoon source. Both the current dlt
# behavior ("read_csv") and the underscore-prefixed name the shipped
# csv-import template originally shipped with ("_read_csv", an older dlt
# version's naming) are checked, since an existing project's frozen table
# could be either depending on which dlt version it last ran against.
_LEGACY_FILESYSTEM_TABLE_NAMES = frozenset({"read_csv", "read_parquet", "_read_csv", "_read_parquet"})


def _warn_if_legacy_filesystem_table_exists(raw_db_path: Path, schema_name: str, new_name: str) -> None:
    """Warn once per run if a pre-fix generic table still exists alongside
    the newly-renamed one.

    Existing projects on the old flat config shape silently start writing
    to a new table name after this fix (Issue #222); their dbt models still
    select the old, now-frozen table, and dbt keeps succeeding against
    stale data with no error anywhere. This can't be fixed automatically
    (the old table is data, not something safe to drop unprompted), so the
    best available mitigation is surfacing it loudly, every run, until the
    legacy table is gone (the user has renamed or dropped it).
    """
    from tycoon.utils.duckdb_utils import get_tables

    legacy_present = {
        table
        for schema, table in get_tables(raw_db_path)
        if schema == schema_name and table in _LEGACY_FILESYSTEM_TABLE_NAMES
    }
    if not legacy_present:
        return

    from tycoon.utils.console import warn

    for legacy_table in sorted(legacy_present):
        warn(
            f"'{schema_name}.{legacy_table}' still exists from before this project's filesystem sources were "
            f"renamed. New rows now land in '{schema_name}.{new_name}' instead; '{legacy_table}' will not "
            "receive new data. If a dbt model still selects from it, update it to use the new name, then drop "
            f"'{schema_name}.{legacy_table}'."
        )


def _emit_event_safe(metadata_db: Path | None, event: Any) -> None:
    """Append an event to the metadata backend; silently no-ops on any failure."""
    if metadata_db is None:
        return
    try:
        from tycoon.metadata_backends.duckdb_file import DuckDBFileBackend

        with DuckDBFileBackend(metadata_db) as b:
            b.append_event(event)
    except Exception:
        pass


def _last_run_replace_tables(pipeline: Any) -> tuple[bool, list[str]]:
    """Find the resources in the pipeline's last extract that used ``replace``.

    Reads the per-resource hints dlt records in the extract trace; a resource
    that yielded nothing still has hints there. dlt stores
    ``write_disposition`` either as a string or as a dict with a
    ``disposition`` key. Returns whether any resource used ``replace``, plus
    the table each such resource writes: its ``table_name`` hint, or the
    resource name, through the schema's naming convention, which is how the
    normalize row counts are keyed. A dynamic (callable) table name can't be
    resolved, so it only counts toward the first value. An unreadable trace
    counts as no ``replace``.
    """
    try:
        step_metrics = pipeline.last_trace.last_extract_info.metrics
    except Exception:
        return False, []
    try:
        normalize = pipeline.default_schema.naming.normalize_table_identifier
    except Exception:
        normalize = None
    used_replace = False
    tables: list[str] = []
    for metrics in step_metrics.values():
        for m in metrics:
            for resource_name, hints in (m.get("hints") or {}).items():
                if resource_name.startswith("_dlt"):
                    continue
                disposition = hints.get("write_disposition")
                if isinstance(disposition, dict):
                    disposition = disposition.get("disposition")
                if disposition != "replace":
                    continue
                used_replace = True
                table = hints.get("table_name") or resource_name
                if isinstance(table, str):
                    tables.append(normalize(table) if normalize else table)
    return used_replace, tables


def _build_run_completed(
    name: str, pipeline: Any, load_info: Any, elapsed: float, warnings: list[str] | None = None
) -> RunCompleted:
    """Build a RunCompleted event from dlt pipeline trace + load_info.

    ``zero_rows`` is set when the run could have emptied a table: a
    ``replace`` resource loaded zero rows, even if another resource in the
    same run loaded some (its table is named in ``warnings``), or the whole
    run loaded nothing and a resource used ``replace`` or a glob matched no
    files (``warnings`` names each such glob). An append, merge, or
    incremental run with no new records is a normal sync and stays
    unflagged (gh-240).
    """
    rows_by_table: dict[str, int] = {}
    try:
        ni = pipeline.last_trace.last_normalize_info
        rows_by_table = {t: c for t, c in (ni.row_counts or {}).items() if not t.startswith("_dlt")}
    except Exception:
        # No normalize trace (the run extracted nothing, or the trace could
        # not be read) leaves rows_by_table empty, which reads as zero rows.
        pass
    loaded_nothing = not any(rows_by_table.values())
    used_replace, replace_tables = _last_run_replace_tables(pipeline)
    warnings = list(warnings or [])
    zero_rows = loaded_nothing and (bool(warnings) or used_replace)
    for table in dict.fromkeys(replace_tables):
        if not rows_by_table.get(table):
            zero_rows = True
            warnings.append(f"'{table}' loaded 0 rows with write_disposition 'replace', so its table is now empty.")
    loads_ids = getattr(load_info, "loads_ids", []) or []
    return RunCompleted(
        source_id=name,
        runtime_id="dlt-managed",
        load_id=loads_ids[0] if loads_ids else "",
        duration_seconds=round(elapsed, 2),
        rows_loaded=rows_by_table,
        tables_created=list(rows_by_table),
        tables_updated=[],
        zero_rows=zero_rows,
        warnings=warnings,
    )


def _complete_run(
    metadata_db: Path | None,
    name: str,
    pipeline: Any,
    load_info: Any,
    elapsed: float,
    warnings: list[str] | None = None,
    *,
    fail_on_empty: bool = False,
) -> None:
    """Record a finished run as RunCompleted, or fail it under ``fail_on_empty``.

    Building and emitting the event is best-effort, so observability code
    never fails a successful pipeline run. The one deliberate failure is a
    zero-row run with ``fail_on_empty`` set: the ``IngestionError`` reaches
    ``run_source``'s handler, which records ``RunFailed`` instead (gh-240).
    """
    try:
        event = _build_run_completed(name, pipeline, load_info, elapsed, warnings)
    except Exception:
        return
    if fail_on_empty and event.zero_rows:
        raise IngestionError(f"'{name}' loaded 0 rows, and --fail-on-empty is set.")
    _emit_event_safe(metadata_db, event)


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


def _keep_first_rows(max_rows: int) -> Callable[[Any], bool]:
    seen = 0

    def keep(_row: Any) -> bool:
        nonlocal seen
        seen += 1
        return seen <= max_rows

    return keep


def _cap_records_per_resource(dlt_source: Any, max_records: int) -> None:
    """Cap each resource of a built source at ``max_records`` rows. gh-239.

    dlt's ``add_limit`` alone can't deliver that: by default it counts
    yields (pages, file chunks, SQL batches), with ``count_rows=True`` it
    still lets the final page through untrimmed, and on a transformer such
    as a filesystem ``files | read_csv()`` pipe it is a logged no-op. So
    ``add_limit(count_rows=True)`` stops paginated reads early (and becomes a
    SQL ``LIMIT`` for ``sql_database``), and a row filter trims the last
    page to the exact count. A filesystem transformer still parses its
    whole input; only the filter caps what lands.
    """
    from dlt.extract import DltSource

    if isinstance(dlt_source, DltSource):
        resources = list(dlt_source.resources.selected.values())
    elif isinstance(dlt_source, list):
        resources = dlt_source
    else:
        resources = [dlt_source]

    for resource in resources:
        if not resource.is_transformer:
            resource.add_limit(max_records, count_rows=True)
        resource.add_filter(_keep_first_rows(max_records))


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
    *,
    fail_on_empty: bool = False,
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

    Returns (pipeline, load_info). ``load_info`` is ``None`` when the
    source had nothing to load (every local glob matched no files), in
    which case the pipeline never ran and no table was touched.

    With ``fail_on_empty``, a local glob that matches no files raises
    ``IngestionError`` before anything loads, and a run that loads zero
    rows in a way that can empty a table (see ``_build_run_completed``)
    raises after it; both record ``RunFailed`` rather than
    ``RunCompleted``. Orchestrated runs rely on the exit code (gh-240).
    """
    _started = time.monotonic()

    _metadata_db: Path | None = None
    try:
        from tycoon.config import config as _cfg
        from tycoon.observability import metadata_db_path

        _metadata_db = metadata_db_path(_cfg.root)
    except Exception:
        pass

    _emit_event_safe(_metadata_db, RunStarted(source_id=name, runtime_id="dlt-managed"))

    try:
        # 1. Legacy pipeline delegation (keyed by source name)
        if name in _LEGACY_PIPELINES:
            pipeline, load_info = _run_legacy(name, raw_db_path=raw_db_path, max_records=max_records, **kwargs)
            load_info.raise_on_failed_jobs()
            _capture_and_refresh_safe(raw_db_path, pipeline=pipeline)
            _complete_run(
                _metadata_db, name, pipeline, load_info, time.monotonic() - _started, fail_on_empty=fail_on_empty
            )
            return pipeline, load_info

        # 2. Native builders win over the catalog path. These types ship with
        #    dlt core and don't need an `~/.tycoon/sources/<type>/` install.
        source_type = source_config.type
        if source_type not in _NATIVE_BUILDERS and source_type in CATALOG:
            # 3. Catalog source dispatch — load from ~/.tycoon/sources/
            pipeline, load_info = _run_catalog(source_type, name, source_config, raw_db_path, max_records)
            _capture_and_refresh_safe(raw_db_path, pipeline=pipeline)
            _complete_run(
                _metadata_db, name, pipeline, load_info, time.monotonic() - _started, fail_on_empty=fail_on_empty
            )
            return pipeline, load_info

        # Warn about unexpanded env vars before building the source. Native
        # builders (filesystem, sql_database, rest_api) skip the catalog
        # path entirely, so this can't rely on _run_catalog's check.
        bad_pairs = _check_unexpanded_env_vars(source_config)
        if bad_pairs:
            from tycoon.utils.console import warn

            for key, var in bad_pairs:
                warn(
                    f"Config key '{key}' contains an unexpanded env var: {var}\n"
                    f"  Set it with: export {var[2:-1]}=<your-value>"
                )

        # Generic pipeline
        pipeline = dlt.pipeline(
            pipeline_name=name,
            destination=dlt.destinations.duckdb(str(raw_db_path)),
            dataset_name=source_config.schema_name,
        )

        legacy_rename = False
        unmatched_globs: list[str] = []
        builder = _NATIVE_BUILDERS.get(source_type)
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
                    f"Unknown source type '{source_type}'. Install with: tycoon sources add {source_type}"
                ) from exc
        else:
            unmatched_globs = _unmatched_local_globs(name, source_config)
            if fail_on_empty and unmatched_globs:
                raise IngestionError(
                    " ".join(unmatched_globs) + " --fail-on-empty is set, so nothing was loaded and no table changed."
                )
            dlt_source = builder(source_config)
            if dlt_source is None or (isinstance(dlt_source, list) and not dlt_source):
                # Running dlt with nothing extracted still applies "replace"
                # to known tables and empties them, so skip the run (gh-240).
                _emit_event_safe(
                    _metadata_db,
                    RunCompleted(
                        source_id=name,
                        runtime_id="dlt-managed",
                        duration_seconds=round(time.monotonic() - _started, 2),
                        zero_rows=True,
                        warnings=unmatched_globs,
                    ),
                )
                return pipeline, None
            legacy_rename = source_type == "filesystem" and not isinstance(dlt_source, list)
            if legacy_rename:
                # dlt's read_csv()/read_parquet() transformers always name
                # their resource "read_csv"/"read_parquet", so two filesystem
                # sources sharing a schema collide into the same table unless
                # renamed after the tycoon source itself. Issue #222.
                #
                # Multi-resource sources (gh-224) come back as a list of
                # resources already named after their own table_name; only
                # the older single-resource shape still needs renaming here.
                # See _build_filesystem_source and _build_filesystem_resource.
                dlt_source = dlt_source.with_name(name)

        # 0 means no cap, matching the catalog shims' `if max_records:`.
        if max_records:
            _cap_records_per_resource(dlt_source, max_records)

        load_info = pipeline.run(dlt_source)
        load_info.raise_on_failed_jobs()
        if legacy_rename:
            _warn_if_legacy_filesystem_table_exists(raw_db_path, source_config.schema_name, name)
        _capture_and_refresh_safe(raw_db_path, pipeline=pipeline)
        _complete_run(
            _metadata_db,
            name,
            pipeline,
            load_info,
            time.monotonic() - _started,
            unmatched_globs,
            fail_on_empty=fail_on_empty,
        )
        return pipeline, load_info

    except Exception as exc:
        _emit_event_safe(_metadata_db, RunFailed(source_id=name, runtime_id="dlt-managed", error=str(exc)))
        raise


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
        raise IngestionError(f"Source '{source_type}' is not installed. Run: tycoon data sources add {source_type}")

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
