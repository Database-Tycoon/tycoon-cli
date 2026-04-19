All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-04-19

### Added

- **MotherDuck warehouse alignment**: `tycoon init` (wizard) and `tycoon register dbt` now detect when a registered dbt project targets `md:<name>` via its dbt-duckdb profile and offer to adopt that target as tycoon's warehouse — extending the DuckDB-only alignment check shipped in v0.1.1.
- **`tycoon register warehouse`**: new subcommand that prompts for cloud (MotherDuck) or local (DuckDB) and updates `database.warehouse` + `stack.warehouse` in `tycoon.yml`. For cloud, surfaces `MOTHERDUCK_TOKEN` setup guidance when the env var isn't set. Prompts before overwriting an existing warehouse.
- **`@pytest.mark.e2e` marker** registered in `pyproject.toml`, deselected from the default `pytest` run, plus `tests/test_templates_e2e.py` covering all four built-in templates (csv-import runs a full offline ingest with row-count assertion; nyc-transit hits live public APIs with record caps and an `xfail` on upstream flakes; github-analytics and weather-station are init-only pending template-side parameterization).
- **`.github/workflows/e2e.yml`**: manual-trigger-only CI workflow that runs `pytest -m e2e` with a `GITHUB_TOKEN` secret slot. No cron — runs only when someone clicks "Run workflow".
- **`.github/workflows/ci.yml`**: new PR + main-push gate that runs the full default pytest suite (unit + offline-e2e) plus `ruff check` on every change. Concurrency-gated so pushes cancel superseded runs. Closes the pre-v0.1.2 hole where tests only ran when someone remembered locally.
- **`offline_e2e` pytest marker**: the `csv-import` template test runs the full `init → sources add → sources run → row-count assertion` pipeline with no network or credentials, and is now included in the default `pytest` run. Live-API tests (`nyc-transit`, `github-analytics`, `weather-station`) stay behind the original `e2e` marker and the manual `e2e.yml` workflow.
- **Ruff configuration** in `pyproject.toml`: line length 120, target py312, per-file ignores for the two legitimate lint-exempt patterns (`cli.py`'s post-app command registration, test forward-reference annotations).
- **`tycoon data history`**: terminal view of recent dlt + dbt runs from `.tycoon/metadata.duckdb`, for users who don't want to spin up Rill. `tycoon data history` lists the most recent N runs across both tools (`--tool dlt|dbt|all`, `--limit N`). `tycoon data history show <id>` drills into a specific run — per-table row counts for dlt loads, per-node status/duration/rows for dbt invocations. Short id prefixes are supported (`show deadbeef` resolves `deadbeef-cafe-…`); ambiguous prefixes error out with the candidates listed.
- **`tycoon data status` adds a Runs column** sourced from the observability metadata DB, showing the total number of captured dlt loads per source. When any source has run history, a `Drill in with tycoon data history` hint is printed beneath the table. Falls back gracefully (column shows `—`) when the metadata DB doesn't exist yet.
- **`tycoon doctor` now reports observability capture health**: a new "Checking observability..." panel prints one of three states — (a) metadata DB not yet created, (b) metadata DB present but empty (capture hooks never fired), or (c) `N dlt load(s), M dbt run(s) captured`. Makes it trivial to diagnose "my dashboards are empty" without spelunking through `.tycoon/`.
- **Scaffolded `.gitignore` now excludes `.tycoon/metadata.duckdb*`**, so new projects don't accidentally commit their observability run history when they `git add .`.
- **`tycoon data clean` learns `--metadata`**: a new flag for explicitly wiping `.tycoon/metadata.duckdb`. By default — including when `--all` is passed — the observability metadata DB is **preserved**, so routine `tycoon data clean --all` cycles don't nuke run history. The command now prints a `Preserving observability metadata DB — pass --metadata to remove.` hint when `--all` skips it.
- **Tycoon observability: dlt + dbt run history with auto-generated Rill dashboards** ([#13]).
  - **New metadata store** at `.tycoon/metadata.duckdb` — four tables (`dlt_runs`, `dlt_rows_by_table`, `dbt_runs`, `dbt_nodes`), disposable (delete the file to reset), directly queryable via `tycoon data query --db .tycoon/metadata.duckdb "..."`. All writes use `INSERT ... ON CONFLICT DO NOTHING` so captures are idempotent.
  - **dlt capture** wired into the ingestion runner: after every successful `tycoon data sources run`, mirrors each source schema's `_dlt_loads` rows plus per-table `_dlt_load_id` row counts into the metadata DB.
  - **dbt capture** wired into `tycoon data transform run/test/build`: parses `target/run_results.json` after each invocation, inserting one row into `dbt_runs` plus one row per model/test into `dbt_nodes` (status, execution_time, rows_affected, compile_time, message). `tycoon run dbt …` passthrough is deliberately *not* hooked — keeps the generic runner tool-agnostic.
  - **`_tycoon_dlt_usage` dashboard** — timeseries on `inserted_at`. Measures: total loads, success rate, rows loaded. Dimensions: source schema, table, status, load_id, schema_version_hash.
  - **`_tycoon_dbt_usage` dashboard** — timeseries on `started_at`. Measures: total runs, success rate, avg duration, models built, model errors, tests passed/failed, rows affected. Dimensions: command, target, dbt version, invocation_id, resource_type (on the nodes view).
  - **Parquet re-export** under `data/parquet/_tycoon/` after every capture, so Rill's `local_file` connector always sees current data without a manual rescaffold. Dashboards materialize only when their backing table is non-empty — new projects don't start with empty explores.
  - **Safety**: every capture + refresh is wrapped in try/except; observability failures never break ingestion or dbt runs.
  - **Caveats carried forward**: dlt per-load row counts derive from `count(*) GROUP BY _dlt_load_id` — exact for `write_disposition=append`, best-effort for `replace` / `merge` (only the most recent load's counts stay accurate). dlt byte sizes + per-job durations (via `trace.json`) and dbt schema-diff via `manifest.json` snapshotting are deferred to a follow-up.
  - **Internals**: new module `src/tycoon/observability.py` (schema, `capture_dlt`, `capture_dbt`, `export_to_parquet`, best-effort wrappers). New `rill_generator.refresh_usage_dashboards(project_root, rill_dir)` reads metadata.duckdb, re-exports the four Parquets, and writes source/metrics_view/dashboard YAMLs — invoked from `generate_rill_config`, the ingestion runner, and the transform command.

### Changed

- **`tycoon doctor` now recognizes MotherDuck OAuth** ([#3]). Previously it only checked `MOTHERDUCK_TOKEN`, producing a false-negative `ERROR` for users authenticated via browser OAuth. `doctor` now reports one of: `token (env)`, `OAuth (cached session)`, or `not configured` — and only errors in the last case. README gained a short "MotherDuck authentication" section documenting both paths.
- Init wizard's warehouse-alignment branch now fires when the chosen warehouse is either DuckDB or MotherDuck. If the adopted dbt-side target changes warehouse type (local ↔ `md:*`), `stack.warehouse` is updated to match.
- **`build_nao_config` renames `accessors` → `templates`** ([#9]) to match nao-core 0.1.7's config schema. The old key emitted a `FutureWarning` on every `nao sync` / `nao chat` invocation.
- Default scaffolded `.gitignore` now covers `.tycoon/nao/db.sqlite*`, `.tycoon/nao/databases/`, `.tycoon/nao/repos/` to keep Nao's sync artifacts (which contain row-preview samples) out of version control.
- Dependency bumps: `rich` 14.3.3 → 15.0.0, `dlt[duckdb]` 1.24.0 → 1.25.0, `duckdb` 1.5.1 → 1.5.2, `pydantic` 2.12.5 → 2.13.2, `fastapi` 0.135.3 → 0.136.0, `dagster` 1.12.20 → 1.13.0, `dagster-webserver` 1.12.20 → 1.13.0, `dagster-dbt` 0.28.20 → 0.29.0, `dagster-dlt` 0.28.20 → 0.29.0, `nao-core` 0.0.59 → 0.1.7, `pytest` (dev) 9.0.2 → 9.0.3.

### Fixed

- **`tycoon init` no longer emits `raw == warehouse`** ([#11]). The wizard's "Local DuckDB at `./data/warehouse.duckdb`" branch previously pointed both `database.raw` and `database.warehouse` at the same file; `tycoon data transform run` then failed with `Unique file handle conflict: Cannot attach "raw"` because dbt-duckdb can't attach a single file twice. Scaffolding now keeps `raw` sibling-distinct (defaults to `data/raw.duckdb`).
- **`tycoon ask sync` / `ask chat` no longer fail with `No module named nao_core.__main__`** ([#6]). `nao-core` ships a `nao` console script but no `__main__.py`; tycoon now resolves the venv-colocated `nao` binary (mirroring the `dbt` executable helper) instead of invoking `python -m nao_core`.
- **`build_nao_config` passes `md:<catalog>` URLs through verbatim** ([#5]). Previously the warehouse path was unconditionally run through `os.path.relpath`, producing garbage like `../../md:my_catalog` that breaks the Nao DuckDB connector. Local file paths still relative-ized.
- **`ask.include_schemas` is now glob-expanded to `<name>.*`** ([#10]). Nao's filter runs `fnmatch` against `schema.table` strings, so bare schema names like `mart` silently matched nothing and every table was filtered out. Already-qualified patterns (anything containing `.`, `*`, or `?`) are left alone.
- **Nao's chat SQLite database now lives at `.tycoon/nao/db.sqlite`** ([#8]) instead of inside the venv (`nao_core/bin/db.sqlite`). Chat history and local user accounts now survive `uv sync`, venv rebuilds, and tycoon upgrades. Wired via the `DB_URI` env var set in `_nao_env`.

[0.1.2]: https://github.com/Database-Tycoon/tycoon-cli/releases/tag/v0.1.2
[#3]: https://github.com/Database-Tycoon/tycoon-cli/issues/3
[#5]: https://github.com/Database-Tycoon/tycoon-cli/issues/5
[#6]: https://github.com/Database-Tycoon/tycoon-cli/issues/6
[#8]: https://github.com/Database-Tycoon/tycoon-cli/issues/8
[#9]: https://github.com/Database-Tycoon/tycoon-cli/issues/9
[#10]: https://github.com/Database-Tycoon/tycoon-cli/issues/10
[#11]: https://github.com/Database-Tycoon/tycoon-cli/issues/11
[#13]: https://github.com/Database-Tycoon/tycoon-cli/issues/13

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
- **`tycoon register dbt <path-or-url>`** and **`tycoon register rill <path-or-url>`** — attach an existing dbt or Rill project to a tycoon.yml without re-running `tycoon init`. Supports local paths and GitHub URLs (with clone-on-register). Prompts before overwriting an already-registered component.
- **Warehouse-alignment check**: when a registered dbt project targets a different DuckDB than tycoon's warehouse (via its `profiles.yml`), the wizard / `tycoon register dbt` warns and offers to adopt the dbt path — preventing the "dbt writes here, `tycoon data query` reads there" silent-divergence footgun.
- Template smoke tests in the pytest suite: init + doctor validate cleanly for all four built-in templates (`csv-import`, `github-analytics`, `nyc-transit`, `weather-station`).

### Fixed

- `tycoon doctor` no longer falsely claims that `tycoon data analyze` creates a missing dbt project; now directs users to `tycoon init` (or to point `dbt_project_dir` at an existing project).
- `server/check-updates` now queries the correct PyPI package (`database-tycoon`) and uses `httpx` instead of `requests`.
- `tycoon data transform` now falls back to `~/.dbt/profiles.yml` when a registered external dbt project has no co-located `profiles.yml`, instead of forcing `--profiles-dir` to the project root.
- Fixed a crash in `tycoon data analyze` and `tycoon data sources run` when invoked without a source argument: the interactive "pick a source" prompt referenced `typer.Choice`, which doesn't exist at runtime. Now uses `click.Choice`. Regression test added.

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
