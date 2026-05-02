# `tycoon data history`

Terminal view over tycoon's observability DB. Every dlt ingest and every dbt invocation captures into `.tycoon/metadata.duckdb`; `history` is how you read it back without writing SQL.

## Synopsis

```
tycoon data history [OPTIONS]
tycoon data history show <id> [OPTIONS]

Options (history):
  --tool TEXT      Filter to dlt or dbt (default: both)
  --limit INTEGER  Number of recent runs to show (default: 10)
  -h, --help       Show this message and exit
```

## `history` — recent runs

```bash
tycoon data history                  # last 10 across dlt + dbt
tycoon data history --tool dlt --limit 25
tycoon data history --tool dbt
```

Output:

```
                            Recent runs
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Tool     ┃ ID                 ┃ Started             ┃ Status ┃ Detail ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ dlt      │ deadbeef-cafe-...  │ 2026-04-29 09:15:12 │ ok     │ ...    │
│ dbt      │ inv-abcdefgh-...   │ 2026-04-29 09:18:41 │ ok     │ ...    │
└──────────┴────────────────────┴─────────────────────┴────────┴────────┘
```

`history` is a quick "did the pipeline actually run, and when" check. For details on a specific run, use `show`.

## `show <id>` — drill into one run

```bash
tycoon data history show deadbeef           # short prefix is fine
tycoon data history show deadbeef-cafe-001
tycoon data history show inv-abcdefgh
```

Auto-detects whether the ID is a dlt load or a dbt invocation by ID format. Short prefixes are accepted as long as they're unambiguous; ambiguous prefixes error with the candidate list.

### dlt drilldown

For a dlt load, `show` prints:

- Pipeline metadata: `pipeline_name`, `transaction_id`, `started_at`, `finished_at`, **duration**
- **Total bytes** written across all jobs
- **Steps** table: extract / normalize / load timings
- **Tables** table: per-table row count + bytes column
- Engine version + success/exception flag

The byte counts and per-step timings come from dlt's `trace.pickle`, captured by v0.1.3's observability v2a. Captures are best-effort — a missing trace file falls back to the row-count-only view.

### dbt drilldown

For a dbt invocation, `show` prints:

- Invocation metadata: command, target, dbt version, duration, success
- **Counts**: models built, model errors, tests passed, tests failed
- **Nodes** table: one row per model/test with status + exec time + rows affected
- **Schema changes vs. previous run** table (if any) — model adds/removes, SQL hash changes, column adds/removes/type changes

The schema-changes table comes from v0.1.3's observability v2b. It's only populated when there's a previous snapshot to diff against — the first invocation in a project's history shows nothing here.

## What feeds the history

| Captured from | Tables in `metadata.duckdb` |
|---|---|
| `tycoon data sources run` | `dlt_runs`, `dlt_rows_by_table`, `dlt_trace_runs`, `dlt_trace_steps`, `dlt_trace_jobs` |
| `tycoon data transform run/test/build` | `dbt_runs`, `dbt_nodes`, `dbt_manifest_snapshots`, `dbt_schema_changes` |

`tycoon run dbt ...` (passthrough) is **deliberately not** captured — it would fire on every ad-hoc `dbt show` / `dbt compile`, polluting the history. Only `tycoon data transform <cmd>` triggers a capture.

## Why isn't dashboards just the same as history?

The `_tycoon_dlt_usage` and `_tycoon_dbt_usage` Rill dashboards read the same data. They're better for trend lines (success rate over time, average duration); `history` is better for "what happened in this specific run." Both surfaces stay current — every capture also re-exports the Parquet files Rill reads.

## Reset

```bash
tycoon data clean --metadata          # wipe metadata.duckdb
```

Run history is recreated on the next ingest / dbt run. The metadata DB is fully disposable.

## Related

- [Concepts → Observability is a side-effect of running](../../getting-started/concepts.md#3-observability-is-a-side-effect-of-running)
- [Reference: Observability tables](../../reference/observability.md) — full schema
- [`tycoon data status`](status.md) — freshness summary that complements history
