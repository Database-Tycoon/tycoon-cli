# Observability reference

Every dlt ingest and every dbt invocation captures into a local DuckDB at `.tycoon/metadata.duckdb`. This page documents every table tycoon writes there and how `tycoon data history` reads it back.

## File location

`.tycoon/metadata.duckdb` (relative to the project root).

The file is **fully disposable**. Delete it to reset the run history without touching your warehouse:

```bash
tycoon data clean --metadata
```

Tycoon recreates the schema on the next ingest / dbt run.

## When tables get written

| Captured by | Tables populated |
|---|---|
| `tycoon data sources run` | `dlt_runs`, `dlt_rows_by_table`, `dlt_trace_runs`, `dlt_trace_steps`, `dlt_trace_jobs` |
| `tycoon data transform run/test/build` | `dbt_runs`, `dbt_nodes`, `dbt_manifest_snapshots`, `dbt_schema_changes` |

`tycoon run dbt …` (passthrough) is **deliberately not** captured — see [`tycoon run`](../commands/run.md#observability-is-not-captured-for-tycoon-run) for the rationale.

## dlt tables

### `dlt_runs`

One row per dlt load.

| Column | Type | Notes |
|---|---|---|
| `source_schema` | VARCHAR | The `raw_<source>` schema name |
| `load_id` | VARCHAR | dlt's load_id (UUID-ish) |
| `status` | INTEGER | 0 = success, non-zero = failure |
| `inserted_at` | TIMESTAMP | When dlt finalized the load |
| `schema_version_hash` | VARCHAR | dlt's schema-version fingerprint |
| `captured_at` | TIMESTAMP | When tycoon mirrored the row in |

### `dlt_rows_by_table`

One row per (load_id, table) pair.

| Column | Type | Notes |
|---|---|---|
| `source_schema` | VARCHAR | |
| `table_name` | VARCHAR | |
| `load_id` | VARCHAR | Foreign key to `dlt_runs` |
| `rows_loaded` | BIGINT | |
| `captured_at` | TIMESTAMP | |

For `write_disposition: append`, this is exact. For `replace` / `merge`, only the most recent load's counts stay accurate (replacement loads overwrite the underlying table).

### `dlt_trace_runs` (v0.1.3+)

One row per dlt invocation, populated from `~/.dlt/pipelines/<name>/trace.pickle`.

| Column | Type | Notes |
|---|---|---|
| `pipeline_name` | VARCHAR | |
| `transaction_id` | VARCHAR | |
| `started_at` | TIMESTAMP | |
| `finished_at` | TIMESTAMP | |
| `duration_seconds` | DOUBLE | |
| `engine_version` | VARCHAR | dlt version that ran |
| `success` | BOOLEAN | |
| `exception` | VARCHAR | NULL on success |

### `dlt_trace_steps` (v0.1.3+)

Per-step timing breakdown.

| Column | Type | Notes |
|---|---|---|
| `transaction_id` | VARCHAR | Foreign key to `dlt_trace_runs` |
| `step_name` | VARCHAR | extract / normalize / load |
| `started_at` | TIMESTAMP | |
| `finished_at` | TIMESTAMP | |
| `duration_seconds` | DOUBLE | |

### `dlt_trace_jobs` (v0.1.3+)

Per-job byte sizes and elapsed times.

| Column | Type | Notes |
|---|---|---|
| `transaction_id` | VARCHAR | |
| `job_name` | VARCHAR | |
| `bytes_written` | BIGINT | |
| `elapsed_seconds` | DOUBLE | |
| `failed_message` | VARCHAR | NULL on success |

## dbt tables

### `dbt_runs`

One row per dbt invocation.

| Column | Type | Notes |
|---|---|---|
| `invocation_id` | VARCHAR | dbt's invocation_id |
| `command` | VARCHAR | run / test / build / docs |
| `started_at` | TIMESTAMP | |
| `elapsed_seconds` | DOUBLE | |
| `success` | BOOLEAN | |
| `models_ok` | INTEGER | |
| `models_error` | INTEGER | |
| `tests_passed` | INTEGER | |
| `tests_failed` | INTEGER | |
| `dbt_version` | VARCHAR | |
| `target_name` | VARCHAR | dev / prod / etc. |
| `captured_at` | TIMESTAMP | |

### `dbt_nodes`

One row per (model, test) per invocation.

| Column | Type | Notes |
|---|---|---|
| `invocation_id` | VARCHAR | Foreign key to `dbt_runs` |
| `node_name` | VARCHAR | |
| `resource_type` | VARCHAR | model / test / snapshot / seed |
| `status` | VARCHAR | |
| `execution_time_seconds` | DOUBLE | |
| `rows_affected` | BIGINT | NULL for tests |
| `compile_time_seconds` | DOUBLE | |
| `message` | VARCHAR | dbt's message (error text on failure, NULL on success) |

### `dbt_manifest_snapshots` (v0.1.3+)

One row per dbt invocation. Stores a fingerprint of `target/manifest.json` so subsequent invocations can compute schema diffs.

| Column | Type | Notes |
|---|---|---|
| `invocation_id` | VARCHAR | Foreign key to `dbt_runs` |
| `snapshot_at` | TIMESTAMP | |
| `manifest_fingerprint` | VARCHAR | Hash over per-node SQL checksums + column maps |
| `manifest_payload` | JSON | Compact representation: per-node SQL checksum + column name → type map |

### `dbt_schema_changes` (v0.1.3+)

One row per change detected when comparing the latest snapshot against the previous one.

| Column | Type | Notes |
|---|---|---|
| `invocation_id` | VARCHAR | The invocation whose snapshot revealed the change |
| `change_type` | VARCHAR | `model_added`, `model_removed`, `sql_changed`, `column_added`, `column_removed`, `column_type_changed` |
| `node_name` | VARCHAR | |
| `column_name` | VARCHAR | NULL for `model_*` and `sql_changed` |
| `old_value` | VARCHAR | NULL for adds; previous type for `column_type_changed`; previous SHA for `sql_changed` |
| `new_value` | VARCHAR | NULL for removes |
| `captured_at` | TIMESTAMP | |

The first snapshot in a project's history doesn't produce any rows here — there's nothing to diff against. From the second invocation onwards, every change is one row.

## Parquet exports

After every capture, tycoon re-exports the same data to Parquet under `data/parquet/_tycoon/`:

```
data/parquet/_tycoon/
├── dlt_runs.parquet
├── dlt_rows_by_table.parquet
├── dlt_trace_runs.parquet
├── dlt_trace_steps.parquet
├── dlt_trace_jobs.parquet
├── dbt_runs.parquet
├── dbt_nodes.parquet
├── dbt_manifest_snapshots.parquet
└── dbt_schema_changes.parquet
```

The auto-generated `_tycoon_dlt_usage` and `_tycoon_dbt_usage` Rill dashboards read these via Rill's `local_file` connector. The Parquet export is what keeps dashboards current without manual refresh.

## Surfaces over this data

| Surface | What it shows |
|---|---|
| `tycoon data history` | Recent runs (terminal table) |
| `tycoon data history show <id>` | Drilldown for one run |
| `tycoon data status` | Per-source freshness + run count |
| `tycoon doctor` | "metadata DB present, N dlt + M dbt runs captured" |
| `_tycoon_dlt_usage` (Rill dashboard) | Time-series of ingestion success / row counts |
| `_tycoon_dbt_usage` (Rill dashboard) | Time-series of dbt invocations |
| `tycoon data query --db .tycoon/metadata.duckdb "..."` | Direct SQL access to anything above |

## Direct SQL examples

### Recent failures

```bash
tycoon data query --db .tycoon/metadata.duckdb \
  "SELECT command, target_name, started_at, models_error, tests_failed
   FROM dbt_runs
   WHERE success = false
   ORDER BY started_at DESC
   LIMIT 10"
```

### Which models changed SQL between runs

```bash
tycoon data query --db .tycoon/metadata.duckdb \
  "SELECT node_name, count(*) AS times_changed
   FROM dbt_schema_changes
   WHERE change_type = 'sql_changed'
   GROUP BY node_name
   ORDER BY times_changed DESC"
```

### Largest dlt loads by bytes

```bash
tycoon data query --db .tycoon/metadata.duckdb \
  "SELECT pipeline_name, sum(bytes_written) AS total_bytes
   FROM dlt_trace_jobs
   GROUP BY pipeline_name
   ORDER BY total_bytes DESC"
```

## Best-effort capture

Every capture is wrapped in try/except — observability failures **never** break ingestion or dbt runs. A missing `trace.pickle` or `manifest.json` produces a no-op (the row just doesn't appear in the trace tables); the underlying tycoon command's exit code is authoritative.

If captures stop showing up, check:

1. `.tycoon/metadata.duckdb` exists and is writable
2. The tycoon command actually completed (look at its own exit code)
3. For dlt traces: `~/.dlt/pipelines/<pipeline>/trace.pickle` exists
4. For dbt manifests: `<dbt_project_dir>/target/manifest.json` exists after the run

## Related

- [`tycoon data history`](../commands/data/history.md)
- [`tycoon data clean`](../commands/data/query.md#clean-remove-warehouse-files) — `--metadata` flag
- [v0.1.3 release notes](../releases/v0.1.3.md) — observability v2 (trace + manifest) shipping notes
