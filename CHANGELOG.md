All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-04-16

### Changed

- Flattened `tycoon data db <sub>` into top-level `tycoon data <sub>`:
  - `tycoon data db stats` → `tycoon data schema` (also reports any extra `.duckdb` files found in `data/`)
  - `tycoon data db query` → `tycoon data query`
  - `tycoon data db clean` → `tycoon data clean`
- `tycoon init` (without `--template`) now runs a per-component wizard that walks through ingestion, warehouse, dbt, Rill, and orchestrator individually. Each prompt describes what tycoon will do for each option and explicitly includes "skip" where it makes sense.

### Added

- `tycoon data query --source <name>` — query a specific source's raw database, with auto-resolution between the shared `raw.duckdb` (single-DB mode) and per-source `data/raw_<name>.duckdb` files. Closes [#1].
- `tycoon data query --db <path>` — query any DuckDB file directly.
- `tycoon data analyze --rill` now scaffolds the Rill project directory on demand if it doesn't exist, instead of silently skipping.
- `GET /health` endpoint on the internal server.
- `tycoon init` auto-detects existing dbt and Rill projects in common inline locations (`./dbt_project/`, `./dbt/`, `./transformation/`, `./rill/`, `./dashboards/`) and in sibling directories (e.g. `../<name>-dbt/`), and offers them as an explicit "use this" option in the wizard.
- Option to register an existing dbt project by local path or GitHub URL during `tycoon init`; remote URLs are cloned into a sibling directory.
- `TransformationTool` enum and `stack.transformation` field in `tycoon.yml` so "skip dbt" is a first-class, recorded choice (not an inferred state).
- `tycoon doctor` now reports "skipped by choice" for components the user intentionally turned off during init, instead of warning about them.

### Fixed

- `tycoon doctor` no longer falsely claims that `tycoon data analyze` creates a missing dbt project; now directs users to `tycoon init` (or to point `dbt_project_dir` at an existing project).
- `server/check-updates` now queries the correct PyPI package (`database-tycoon`) and uses `httpx` instead of `requests`.
- `tycoon data transform` now falls back to `~/.dbt/profiles.yml` when a registered external dbt project has no co-located `profiles.yml`, instead of forcing `--profiles-dir` to the project root.

[0.1.1]: https://github.com/Database-Tycoon/tycoon-cli/releases/tag/v0.1.1
[#1]: https://github.com/Database-Tycoon/tycoon-cli/issues/1

## [0.1.0] - 2026-04-09

### Added

#### Core CLI
- `tycoon init` — scaffold a new project with templates: `csv-import`, `github-analytics`, `nyc-transit`, `weather-station`
- `tycoon doctor` — environment diagnostics (checks dbt, Rill, warehouse config, and stack config)
- `tycoon check-updates` — check PyPI for a newer version of the package

#### Data Pipeline
- `tycoon data sources catalog` — browse available source integrations
- `tycoon data sources add <type>` — interactively register a source; auto-installs dlt packages on demand
- `tycoon data sources list` — list all registered sources
- `tycoon data sources show <name>` — inspect a registered source
- `tycoon data sources run <name>` — ingest a source via dlt into DuckDB
- `tycoon data sources run-all` — ingest all registered sources
- `tycoon data sources status` — show freshness and row counts per source
- `tycoon data transform run` — run `dbt build`
- `tycoon data analyze <source>` — auto-scaffold dbt staging models from raw schema; `--rill` flag generates Rill dashboards
- `tycoon data db query <sql>` — query the local DuckDB warehouse directly

#### Services
- `tycoon start` / `tycoon stop` — start/stop Rill, Dagster, Nao, and DuckDB UI
- `tycoon run <tool>` — passthrough runner for `dbt`, `dlt`, `rill`, and `dagster`

#### AI Queries (requires `tycoon[ask]`)
- `tycoon ask init` — initialize the natural language query index
- `tycoon ask sync` — sync the index with the current warehouse schema
- `tycoon ask chat` — natural language queries via Nao (Ollama supported, no API key needed)

#### Source Catalog (downloaded on demand via dlt)
- `rest_api` — any REST API; defaults to PokéAPI demo (no credentials needed)
- `filesystem` — CSV and Parquet files from local paths
- `github` — commits, issues, pull requests, repositories
- `slack` — channels, messages, users
- `stripe` — customers, invoices, products, subscriptions
- `hubspot` — companies, contacts, deals, tickets
- `notion` — databases, pages, users

#### Optional Extras
- `tycoon[dagster]` — Dagster orchestration with full asset graph
- `tycoon[ask]` — Nao + Ibis for natural language querying

### Known Limitations
- Snowflake and BigQuery warehouses are not yet supported (planned for a future release)
- `tycoon start --only rill` requires a `rill/` project directory initialized with `rill init`

[0.1.0]: https://github.com/Database-Tycoon/tycoon-cli/releases/tag/v0.1.0
