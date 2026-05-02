# `tycoon data analyze`

Scaffold dbt staging models (and optionally Rill dashboards) for a registered source. The shortcut between "I just ingested data" and "I have a typed view of it / a dashboard."

## Synopsis

```
tycoon data analyze SOURCE [OPTIONS]

Arguments:
  SOURCE   Name of a registered source

Options:
  --no-dbt          Don't generate dbt staging models
  --rill            Also generate Rill source / metrics_view / dashboard YAMLs
  -h, --help        Show this message and exit
```

## What it does

`analyze` introspects the source's schema in `data/raw.duckdb` and generates two things:

1. **dbt staging models** — one `stg_<source>__<table>.sql` per ingested table, plus a `schema.yml` documenting the columns. Lands under `dbt_project/models/staging/`.
2. **(Optional) Rill artifacts** — when `--rill` is passed, also generates:
   - `rill/sources/stg_<source>__<table>.yaml` (Rill source pointing at the Parquet export)
   - `rill/metrics/stg_<source>__<table>_mv.yaml` (metrics view with auto-derived dimensions + one count measure)
   - `rill/dashboards/stg_<source>__<table>.yaml` (explore dashboard)

## Examples

```bash
# Just dbt staging models
tycoon data analyze github

# dbt + Rill in one shot
tycoon data analyze github --rill

# Skip dbt (Rill only) — useful when you already wrote staging models by hand
tycoon data analyze github --no-dbt --rill
```

## Generated dbt staging structure

For source `github` with tables `issues`, `pull_requests`, `commits`:

```
dbt_project/models/staging/
├── stg_github__issues.sql
├── stg_github__pull_requests.sql
├── stg_github__commits.sql
└── schema.yml
```

Each `stg_*.sql` is a typed `SELECT *` from the raw schema, with `_dlt_*` internal columns excluded. Edit them to add typing, renaming, filtering — that's the whole point of staging.

`schema.yml` documents columns with their types pulled from DuckDB's `information_schema`. Run `dbt docs generate` (via `tycoon data transform docs`) to render the lineage.

## Generated Rill structure

For each table, `--rill` writes a 3-file chain:

```
rill/sources/stg_github__issues.yaml      # type: source, connector: local_file
rill/metrics/stg_github__issues_mv.yaml   # type: metrics_view, model: stg_github__issues
rill/dashboards/stg_github__issues.yaml   # type: explore, metrics_view: stg_github__issues_mv
```

The Parquet bridge is intentional — see [Rill 0.86 architecture in the v0.1.3 release notes](../../releases/v0.1.3.md) for the full rationale (TL;DR: SQLite-backed DuckLake catalogs hold an exclusive lock that breaks Rill-while-ingesting).

The auto-generated metrics view picks dimensions and measures heuristically:

- **Dimensions**: every `VARCHAR` / `BOOL` column
- **Measures**: a default `count(*)` plus `avg()` / `sum()` for `DOUBLE` / `BIGINT` columns

Customize the dashboards by hand-editing the YAML — `analyze` writes them, but won't overwrite an existing file. Re-running `analyze` skips files that already exist (with a warning) so your hand-edits are safe.

## After analyze

```bash
tycoon data transform run        # build the staging tables
tycoon start --only rill         # open the dashboards
```

## Related

- [`tycoon data sources run`](sources.md#run-ingest) — populate the raw layer first
- [Reference: Templates](../../reference/templates.md) — templates that come pre-analyzed
- [Reference: Observability tables](../../reference/observability.md) — auto-generated `_tycoon_*` dashboards
