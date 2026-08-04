---
name: adding-data-sources
description: Use when adding, configuring, or running a data source in a tycoon project — REST APIs, SQL databases, files (CSV/Parquet), or catalog sources like GitHub, Stripe, Slack, Notion, Google Sheets; when an ingestion run must be scripted with no prompts (CI); when credentials or record caps are involved; or when a source run fails with "not installed" or missing-config errors.
license: MIT
compatibility: Requires the tycoon CLI (pip install database-tycoon) inside a tycoon project (tycoon.yml present)
metadata:
  author: database-tycoon
  tier: users
---

# Adding data sources

tycoon registers sources in `tycoon.yml` and runs them through dlt. Three
source types are native builders (`rest_api`, `sql_database`, `filesystem`);
everything else (github, stripe, slack, notion, google_sheets, hubspot) comes
from the source catalog and needs a one-time install.

## Quick reference

| Command | Purpose |
|---|---|
| `tycoon data sources catalog` | Show the built-in source catalog |
| `tycoon data sources add [TYPE]` | Register a source (interactive without flags) |
| `tycoon data sources list` | Registered sources |
| `tycoon data sources list show <NAME>` | One source's config, secrets masked |
| `tycoon data sources run <NAME> [-n N]` | Ingest one source; `-n` caps records **per resource** |
| `tycoon data sources run-all [-n N]` | Ingest every source sequentially |
| `tycoon data sources remove <NAME>` | Unregister (asks for confirmation) |

## Scripted (CI-safe) example — REST API end to end

```bash
tycoon data sources add rest_api \
  --base-url https://pokeapi.co/api/v2/ \
  --resources pokemon,berry \
  --no-prompt
tycoon data sources run pokeapi -n 100      # name auto-derived from hostname
tycoon data analyze pokeapi                  # scaffold dbt staging models (safe to re-run)
tycoon data transform run --select 'stg_pokeapi__*'
```

Generated staging models are named `stg_<source>__<table>.sql` under
`models/staging/<source>/` — select them with `--select 'stg_<source>__*'`.

## Where the data lands

One `data/raw.duckdb` file per **project** (not per source), with one DuckDB
schema per source: `raw_<source_name>` (hyphens become underscores). The dbt
warehouse is a separate file, `data/warehouse.duckdb`. Confirm with
`tycoon data schema` (takes no arguments).

## `--no-prompt` rules

- The source TYPE must be passed positionally.
- Each native type requires its key flag or the command exits 1:
  `rest_api` → `--base-url` · `sql_database` → `--connection-string` ·
  `filesystem` → `--path`.
- `--name`/`--schema` are auto-derived only for `rest_api` (hostname's second
  label, e.g. `pokeapi`) and `filesystem` (file stem). For every other type
  `--name` is required under `--no-prompt`.
- Extra settings pass as repeatable `--config key=value`.

## Credentials

Catalog sources default credential fields to `${ENV_VAR}` references stored in
`tycoon.yml` — the secret itself is never written. Export the variable before
running. An unexpanded `${VAR}` produces a **warning** then a failing API
call, not an upfront error, so check env vars first when a run 401s.

## Catalog sources need a one-time install

github/stripe/slack/notion/google_sheets/hubspot require dlt's source files in
`~/.tycoon/sources/<type>/`. `tycoon data sources add <type>` offers the
install interactively. **Trap:** some error messages suggest
`tycoon data sources catalog install <type>` — that subcommand does not
exist. The recovery path is re-running `tycoon data sources add <type>`
without `--no-prompt` and accepting the install.

## After a successful run

tycoon auto-scaffolds dbt staging models for the source if a dbt project
exists and nothing references the source yet. Opt out per-call with
`--no-scaffold`, or project-wide with `transform.auto_scaffold: false` in
`tycoon.yml`.
