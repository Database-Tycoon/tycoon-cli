---
name: reading-project-state
description: Use when checking what state a tycoon project is in — pipeline/source status, recent ingestion or dbt run history, row counts, table freshness — and especially when a script or CI job needs machine-readable output (no tycoon command has a --json flag).
license: MIT
compatibility: Requires the tycoon CLI (pip install database-tycoon) inside a tycoon project (tycoon.yml present)
metadata:
  author: database-tycoon
  tier: users
---

# Reading project state

## For humans (Rich tables, not parseable)

| Command | Shows |
|---|---|
| `tycoon data status` | Layered view: Sources → Staging → Intermediate → Marts, with freshness |
| `tycoon data history [-t dlt\|dbt] [-n N] [-s SOURCE]` | Recent runs (default 20) |
| `tycoon data history show <RUN_ID>` | One run: status, duration, error, per-table row counts (short id prefix OK) |
| `tycoon data schema` | Tables, row counts, file sizes across raw + warehouse (no arguments) |

Marts panels appear only after a dbt manifest exists (run dbt at least once).

## For scripts (machine-readable)

**There is no `--json` flag anywhere.** The programmatic surface is the
observability database at `.tycoon/metadata.duckdb`, queried through tycoon
(which handles locks):

```bash
tycoon data query --db .tycoon/metadata.duckdb \
  "SELECT source, status, started_at, rows_loaded
   FROM dlt_runs ORDER BY started_at DESC LIMIT 20"
```

Tables: `dlt_runs`, `dlt_rows_by_table`, `dbt_runs`, `dbt_nodes`,
`dbt_manifest_snapshots`, `dbt_schema_changes`, `fivetran_connectors`.
Discover columns with `DESCRIBE <table>`.

`tycoon data query` also reaches the other databases:

```bash
tycoon data query "SELECT count(*) FROM marts.my_table"   # warehouse
tycoon data query --raw "SELECT * FROM raw_pokeapi.pokemon LIMIT 5"
tycoon data query -s pokeapi "SHOW TABLES"                # one source's schema
```

Queries are read-only. Warehouse queries route through Quack automatically
while `tycoon start` is running, so they work even when the file is locked.

## Modeling state inside dbt

`tycoon data observability scaffold` generates `models/_tycoon/` staging
models over the metadata DB and ATTACHes it as `tycoon_meta` in profiles.yml
— use this when dashboards should show pipeline health.

## Cleanup gotcha

`tycoon data clean --all` deletes the raw and warehouse files but
**preserves** `.tycoon/metadata.duckdb` (run history) unless `--metadata` is
passed too.
