"""Observability — capture dlt + dbt run history in a dedicated metadata DuckDB.

Architecture
============

A separate, disposable DuckDB file at ``.tycoon/metadata.duckdb`` holds
tycoon's observability state: dlt load history (mirrored from each raw
database) and dbt invocation history (parsed from
``target/run_results.json``). This file is decoupled from the
user-facing raw + warehouse databases so it survives ``tycoon data
clean`` and can be queried directly::

    tycoon data query --db .tycoon/metadata.duckdb "SELECT * FROM dbt_runs ORDER BY started_at DESC"

Capture points
--------------

* ``capture_dlt``: called from the ingestion runner after each
  successful dlt load. Idempotently mirrors ``<schema>._dlt_loads`` and
  per-table ``_dlt_load_id`` row counts into the metadata DB.
* ``capture_dbt``: called from the ``tycoon data transform`` command
  after each ``run`` / ``test`` / ``build``. Parses
  ``target/run_results.json`` and inserts one row per invocation plus
  one row per node.

Display
-------

``export_to_parquet`` re-writes four Parquet files under
``data/parquet/_tycoon/``. The Rill dashboard YAMLs emitted by
``rill_generator.refresh_usage_dashboards`` point at those Parquets via
Rill's ``local_file`` connector.

All operations are best-effort: capture failures never propagate to
the caller. Ingestion and dbt invocations must not fail because of
observability bookkeeping.

Layout
------

* ``store``: the metadata file's path, schema, Parquet export and
  ``has_any_observability_data``.
* ``dlt_capture``: dlt load history and ``trace.pickle`` runs.
* ``dbt_capture``: dbt ``run_results.json`` and ``manifest.json``.

Callers import from this package; the submodules are an internal split.
"""

from __future__ import annotations

from tycoon.observability.dbt_capture import (
    capture_dbt,
    capture_dbt_manifest,
    capture_dbt_manifest_safe,
    capture_dbt_safe,
)
from tycoon.observability.dlt_capture import (
    capture_dlt,
    capture_dlt_safe,
    capture_dlt_trace,
    capture_dlt_trace_from_dict,
    capture_dlt_trace_safe,
)
from tycoon.observability.store import (
    ensure_schema,
    export_to_parquet,
    has_any_observability_data,
    metadata_db_path,
)

__all__ = [
    "capture_dbt",
    "capture_dbt_manifest",
    "capture_dbt_manifest_safe",
    "capture_dbt_safe",
    "capture_dlt",
    "capture_dlt_safe",
    "capture_dlt_trace",
    "capture_dlt_trace_from_dict",
    "capture_dlt_trace_safe",
    "ensure_schema",
    "export_to_parquet",
    "has_any_observability_data",
    "metadata_db_path",
]
