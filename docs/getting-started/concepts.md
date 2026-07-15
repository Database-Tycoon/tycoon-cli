# Concepts

Four ideas that explain how tycoon thinks. Read this once and the rest
of the docs make more sense.

## 1. `tycoon.yml` is the source of truth

Everything tycoon does flows from one file in your project root.
`tycoon.yml` declares:

- **Where data lives** — local DuckDB paths, MotherDuck catalogs, etc.
- **What sources to ingest** — REST APIs, files, SQL databases, custom
  dlt sources.
- **What stack you use** — dbt vs none, Rill vs Metabase vs none.
  Each toggle is a `stack.<component>` key.
- **Optional features** — local snapshots (`sync:`), template
  parameters at scaffold time.

Every command resolves paths and behavior through this file. If you
edit it by hand, the next command picks up the change — there's no
state to invalidate.

See [Reference: tycoon.yml](../reference/tycoon-yml.md) for the full
schema.

## 2. Two databases, two roles

Tycoon assumes a clean separation between **raw** and **warehouse**:

- **`data/raw.duckdb`** — what dlt ingests into. One schema per source
  (`raw_files`, `raw_nyc_dot`, etc.). dlt owns it; tycoon doesn't
  modify the raw data.
- **`data/warehouse.duckdb`** — what dbt transforms into. Models are
  organized into staging / mart / etc. schemas per dbt convention.

Cloud variants:

- `database.warehouse: md:my_catalog` — MotherDuck catalog (the warehouse).
- `database.raw: data/raw.duckdb` (kept local) + `warehouse: md:...` —
  hybrid setup; cheap raw landing zone, cloud-shared transformation
  layer.

Both files are disposable. Delete them and re-run `tycoon data run-all`
to rebuild from sources.

## 3. Observability is a side-effect of running

Every dlt ingest and every dbt invocation auto-captures into
`.tycoon/metadata.duckdb`:

| Table | Captured by | What's in it |
|---|---|---|
| `dlt_runs` | `tycoon data sources run` | One row per dlt load (load_id, schema, status, started_at) |
| `dlt_rows_by_table` | dlt capture | One row per (load_id, table) — row counts |
| `dlt_trace_runs` / `dlt_trace_steps` / `dlt_trace_jobs` | dlt capture (v0.1.3+) | Per-step durations, per-job byte sizes |
| `dbt_runs` | `tycoon data transform run` | One row per dbt invocation (target, version, duration, success) |
| `dbt_nodes` | dbt capture | One row per model/test (status, exec time, rows affected) |
| `dbt_manifest_snapshots` | dbt capture (v0.1.3+) | One row per invocation, full manifest fingerprint |
| `dbt_schema_changes` | dbt capture (v0.1.3+) | One row per (added, removed, retyped) column or model |

`tycoon data history` and `tycoon data history show <id>` are terminal
views over this DB. The auto-generated Rill dashboards
(`_tycoon_dlt_usage`, `_tycoon_dbt_usage`) read from Parquet exports of
the same data.

The metadata DB is **fully disposable** — `tycoon data clean --metadata`
nukes it without touching the warehouse. Tycoon recreates it on the
next ingest / dbt run.

## 4. The CLI is a thin facade over real tools

`tycoon data sources run` shells out to dlt. `tycoon data transform run`
shells out to dbt. `tycoon start --only rill` shells out to
`rill start`.

Tycoon's job is to:

1. Read `tycoon.yml` and figure out what to invoke
2. Pass the right arguments to the underlying tool
3. Capture the result into the observability DB
4. Optionally re-export Parquet so dashboards stay current

You can always drop down to the underlying tool with `tycoon run <tool>
<args>`:

```bash
tycoon run dbt run --select stg_widgets
tycoon run dlt --version
tycoon run rill validate
```

This dispatches to the venv-colocated binary so you don't have to remember
which tool ships its CLI under what name.

---

## Want to go deeper?

- [Reference: tycoon.yml](../reference/tycoon-yml.md) — every key in the
  config file
- [Reference: Templates](../reference/templates.md) — what each template
  scaffolds
- [`tycoon data sync`](../commands/data/sync.md) — the cloud-→-local
  snapshot story
