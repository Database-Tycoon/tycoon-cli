All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2026-04-30

_Closes four open issues from v0.1.3 (#7, #12, #17) plus three filed during the cycle (#18, #19, #20). Adds a MkDocs Material docs site with `tycoon docs serve`, plus a long list of UX improvements. See [`docs/releases/v0.1.4.md`](docs/releases/v0.1.4.md) for the narrative._

### Added

- **`tycoon data sync` — cloud → local DuckDB snapshots ([#12][]).** Pulls one or more DuckDB-attachable sources (`md:<catalog>` for MotherDuck or any `/path/to/other.duckdb` file) into a single local DuckDB file you can point dbt-dev / notebooks / agents at instead of prod. Three modes: `replace` (default; full overwrite per table), `append` (accumulate new rows), `skip-existing` (only fill in missing tables). Optional `sync:` block in `tycoon.yml` lets you save defaults so day-to-day re-syncs are just `tycoon data sync` with no flags. v1 ships with a deliberately narrow scope per the issue: `md:` and local-DuckDB sources, full replace per table, no incremental, one-direction-only (cloud → local; never reverse). Per-table summary printed on success (source URL, schema, table, row count).
- **`tycoon ask doctor` health check ([#7][]).** Validates the four most common breakage modes called out in the issue: missing `nao_config.yaml`, missing required directories, missing MotherDuck auth (token or OAuth), and an unreachable LM Studio endpoint when configured. Renders a Rich `status_table` with one row per check (OK / WARN / FAIL); exits non-zero on any FAIL so the command is CI-friendly.
- **`tycoon ask init --llm <provider>` ([#7][] §5).** Records an LLM provider shortcut in `tycoon.yml`'s `ask.llm.provider` field — `lm-studio`, `ollama`, `openai`, `anthropic`, `gemini`, `mistral`. The `lm-studio` shortcut is the marquee one: it expands to a valid OpenAI-compatible nao config pointed at `http://localhost:1234/v1` so users don't have to discover that "openai + custom base_url" is the LM Studio path. `LLMConfig` gains a `base_url` field for explicit overrides.
- **`tycoon ask init` now scaffolds every directory `nao sync` walks ([#7][] §4).** All eight required dirs (`databases/`, `queries/`, `docs/`, `semantics/`, `repos/`, `agent/{tools,mcps,skills}`) are created up front, eliminating the `No such file or directory: 'repos'` / `'databases'` crash class. Auto-generated `.tycoon/nao/.gitignore` keeps PII row-previews + sync artifacts out of version control by default ([#7][] §7).
- **`tycoon register dbt` profile flags ([#18][]).** Three new options mirror dbt's own CLI: `--profiles-dir`, `--profile`, `--target`. Each is persisted into `tycoon.yml` as `dbt_profiles_dir` / `dbt_profile` / `dbt_target` so subsequent `tycoon data transform` invocations reuse them automatically. The warehouse-alignment branch of `register dbt` now reads the right `outputs[]` entry rather than blindly walking dbt's default lookup.
- **`tycoon register warehouse` non-interactive flags ([#19][]).** Five new options make the command CI-scriptable: `--type duckdb|motherduck`, `--path PATH`, `--catalog NAME`, `--no-prompt`, `--force`. Aliases (`local` / `cloud` / `md`) accepted for either UX preference.
- **First-class observability metadata in dbt + Nao ([#20][]).** Tycoon's `.tycoon/metadata.duckdb` (already feeding Rill since v0.1.2) is now visible to dbt and to Nao. Every scaffolded dbt profile ATTACHes the metadata DB as `tycoon_meta` (READ_ONLY); `dbt_project/models/_tycoon/` ships nine `stg_tycoon__*` staging views (one per metadata table) plus a `dim_runs.sql` mart UNIONing dlt + dbt timelines. `tycoon ask sync` then exposes them to Nao automatically — no extra plumbing. New surfaces: `tycoon data observability scaffold` for retrofitting existing projects, `tycoon register dbt --no-attach-metadata` opt-out flag.
- **`tycoon docs serve` / `tycoon docs build`.** Wraps MkDocs Material so contributors have one command for local documentation. `serve` runs with hot reload on `:8000`; `build --strict` is the CI-friendly one-shot. New `[docs]` optional extra pulls in `mkdocs==1.6.1` + `mkdocs-material==9.5.49`.
- **MkDocs Material docs site at `docs/`.** ~30 user-facing pages organized into Getting started / Commands / Reference / Recipes / Releases. Local-first; `tycoon docs serve` is the entry point.
- **`-h` short alias for `--help`** across every command. Configured once on the root typer app; click propagates it to every sub-command.
- **CI/CD automation** — `ci.yml` gains three jobs (build + wheel install smoke, `mkdocs build --strict`, template scaffold + doctor matrix over the four built-in templates), new `nightly-e2e.yml` runs the no-credential live-API tests on a daily cron and auto-opens a GitHub issue on failure, and `publish.yml` gains a `preflight` job that asserts version-pin / CHANGELOG / release-notes coherence before any artifact builds. Removes most of the Claude-driven manual pre-release checklist.

### Changed

- **GitHub Actions runtime bumped to Node 24-compatible versions.** `actions/checkout` v4 → v6, `actions/upload-artifact` v4 → v7, `actions/download-artifact` v4 → v8, `astral-sh/setup-uv` v4 → v7 (the latest moving major tag — v8 ships as specific versions only). Node 20 was scheduled for removal from GitHub-hosted runners on September 16 2026, with the default flipping to Node 24 on June 2 2026; bumping early avoids the deprecation warning and removes any Node-20-only branch from the workflow paths.
- **Drop the "Tables" column from `tycoon data sources list`.** Always rendered `(all)` for the source types most users actually have (rest_api / filesystem) — meaningless noise. The underlying `tables:` field still exists on `SourceConfig` and shows up in the per-source `tycoon data sources show <name>` view.
- **Drop the `dbt-fusion` check from `tycoon doctor`.** Got its own panel and warned when `dbtf` was on `$PATH`, but the premise didn't survive scrutiny — `dbtf` is a separate binary, doesn't shadow `dbt`, they coexist fine. Singling out one specific competitor was disproportionate vs. the rest of doctor's checks.

### Fixed

- **Legacy NYC pipelines no longer ignore the runner-provided `raw_db_path` ([#17][]).** Three legacy pipeline modules (`nyc_dot_pipeline`, `mta_pipeline`, `mta_bus_speeds_pipeline`) were importing the global `tycoon.config.config` singleton and reading `config.raw_db` to set dlt's destination, instead of using the `raw_db_path` that the generic runner threads through for everything else. Worked fine in real CLI processes, but broke `tests/test_templates_e2e.py::test_nyc_transit_e2e` because `monkeypatch.setattr(sources_mod, "config", cfg)` rebinds the command-side reference but not the singleton the legacy modules saw. `_run_legacy` now passes `raw_db_path` through and each pipeline takes it as a required argument; the global-config dependency is gone from the three modules.
- **Repo `.gitignore` `data/` pattern was matching subdirectories anywhere.** Caused `docs/commands/data/` to be silently uncommitted across two earlier docs commits. Anchored to repo root (`/data/`). Also added `/rill/{sources,metrics,dashboards}/_tycoon_*` exclusions to the existing "this is the CLI source repo, not a tycoon project" block.
- **`docs/reference/observability.md` schema reference was wrong.** Several columns were mistyped (`elapsed_seconds` instead of the actual `elapsed_s`, `execution_time_seconds` vs `execution_time_s`, `bytes_written` vs `file_size_bytes`, etc.). Reconciled against the live captured schema. Same root cause caught a `dim_runs.sql` bug during e2e validation.

[#7]: https://github.com/Database-Tycoon/tycoon-cli/issues/7
[#12]: https://github.com/Database-Tycoon/tycoon-cli/issues/12
[#17]: https://github.com/Database-Tycoon/tycoon-cli/issues/17
[#18]: https://github.com/Database-Tycoon/tycoon-cli/issues/18
[#19]: https://github.com/Database-Tycoon/tycoon-cli/issues/19
[#20]: https://github.com/Database-Tycoon/tycoon-cli/issues/20

## [0.1.3] - 2026-04-28

_Scope tracked in [`docs/releases/v0.1.3.md`](docs/releases/v0.1.3.md). Five of seven planned themes landed: template parameterization, csv-import buildable dbt + offline e2e, dlt trace enrichment (observability v2a), dbt manifest schema-diff (observability v2b), and Snowflake/BigQuery warehouse alignment. The two XL items — one-command MotherDuck/Nao/LM Studio setup ([#7][]) and `tycoon data sync` ([#12][]) — are deferred to v0.1.4._

### Added

- **csv-import template now ships a buildable dbt project.** New `dbt_project/` under the template (with `dbt_project.yml`, `profiles.yml`, and a `models/staging/stg_widgets.sql` + `schema.yml`) gets copied verbatim into new projects by `tycoon init --template csv-import`. A sample `data/input/widgets.csv` is also bundled so `tycoon data sources run files && tycoon data transform run` works end-to-end without any manual setup.
- **Offline e2e coverage now includes `tycoon data transform run`.** The csv-import e2e test (which already gated on every PR via the `offline_e2e` marker) runs the full init → ingest → transform pipeline, asserts that `main.stg_widgets` contains the expected row count with the correct column types, and checks that observability captured a successful `dbt_runs` entry plus the corresponding `dbt_nodes` row. Catches integration regressions that unit tests can miss.
- **Template parameterization.** Templates can now declare runtime parameters via a new `template.yml` metadata file alongside `tycoon.yml`. Values are supplied with `tycoon init --template X --param name=value` (repeatable) or prompted interactively for any declared parameter that wasn't passed on the command line. `{{ name }}` placeholders (with or without whitespace) in `.yml/.yaml/.sql/.md/.txt` files get substituted at scaffold time. The `template.yml` metadata file itself is not copied into the target project — it's build-time metadata only.
- **`github-analytics` and `weather-station` templates now ship as real, runnable pipelines.** `github-analytics` declares `owner` + `repo` parameters; `weather-station` declares `station_id`, `office`, `gridX`, `gridY`. Both templates' `{{ placeholder }}` URLs get substituted at `tycoon init` time, so their `@pytest.mark.e2e` tests now run full ingestion against the live GitHub / NOAA APIs (with `--max-records 5` caps and `xfail`-on-upstream-flake semantics).
- **dlt trace enrichment (observability v2a).** After every successful ingest, tycoon now parses `~/.dlt/pipelines/<name>/trace.pickle` and enriches the metadata DB with three new tables: `dlt_trace_runs` (pipeline_name, transaction_id, started_at / finished_at / duration, engine_version, success + exception), `dlt_trace_steps` (extract / normalize / load per-step durations), and `dlt_trace_jobs` (per-job byte size + elapsed seconds + failed message). `tycoon data history show <load_id>` now surfaces pipeline duration, total bytes written, per-step timings, and a per-table bytes column alongside the existing row counts. New Parquet exports under `data/parquet/_tycoon/dlt_trace_{runs,steps,jobs}.parquet` are available for Rill dashboards. Capture is best-effort — a missing or malformed `trace.pickle` never breaks ingest.
- **Snowflake / BigQuery warehouse alignment.** `tycoon register dbt` now recognizes Snowflake, BigQuery, Redshift, and unknown-adapter profiles — not just DuckDB / MotherDuck as in v0.1.1 and v0.1.2. A new `_extract_dbt_warehouse_target` helper returns a structured `DbtWarehouseTarget` (adapter_type, identifier, display, details) so callers can reason about each adapter properly. When the dbt adapter type doesn't match `stack.warehouse`, registration offers to update `stack.warehouse`; `database.warehouse` (only meaningful for DuckDB / MotherDuck) is left alone for cloud adapters. Snowflake registration additionally warns when the dbt profile's `account` differs from a pre-recorded `warehouse_connection.account` in `tycoon.yml`.
- **dbt manifest schema-diff (observability v2b).** After every `tycoon data transform run/test/build`, tycoon snapshots `target/manifest.json` into a new `dbt_manifest_snapshots` table and diffs the fingerprint (per-node SQL checksum + column name→type map) against the previous snapshot, emitting one row per change into `dbt_schema_changes`. Five change types are recorded: `model_added`, `model_removed`, `sql_changed` (SHA mismatch), `column_added`, `column_removed`, `column_type_changed`. The first snapshot inserts with zero change rows (nothing to diff against). `tycoon data history show <invocation_id>` now appends a "Schema changes vs. previous run" table when any changes were recorded for that invocation. Both tables export to Parquet for Rill dashboards. Capture is best-effort — a missing or malformed `manifest.json` never breaks the dbt invocation.
- **Nao context surface for coding agents.** `tycoon ask init` and `tycoon ask sync` now also write an `AGENTS.md` at the project root pointing at the Nao-synced context tree (`.tycoon/nao/databases/**/{columns,preview}.md`, `.tycoon/nao/repos/dbt/`, `.tycoon/nao/RULES.md`). Coding agents (Claude Code, Cursor, Windsurf, etc.) that auto-read `AGENTS.md` get oriented to the project's data context for free. The generated file carries an `<!-- @generated by tycoon ask -->` sentinel; if it's missing on a pre-existing `AGENTS.md`, tycoon leaves the file alone and prints a hint instead of stomping user-authored content.
- **`tycoon ask context` subcommand** for piping Nao-synced context into any agent harness without launching the chat UI. `tycoon ask context` lists every synced table; `--table <name>` cats `columns.md` + `preview.md` for one table; `--schema <name>` does the same for every table in a schema; `--rules-only` cats `RULES.md`; `--include-dbt` appends synced dbt model SQL. Output is plain markdown on stdout so it composes cleanly: `tycoon ask context --table dim_users \| claude -p "explain this table"`.

### Changed

- `tycoon data history show <load_id>` (dlt drilldown) now renders pipeline duration, total bytes written, and a Steps table (extract/normalize/load durations) when a dlt trace is captured. The per-table row-count view gains a Bytes column.
- `tycoon data history show <invocation_id>` (dbt drilldown) now appends a "Schema changes vs. previous run" table below the Nodes table when a manifest-diff recorded changes for that invocation.
- `_extract_dbt_duckdb_path` is retained as a thin backwards-compatible shim over the new structured `_extract_dbt_warehouse_target`. Existing callers unchanged.
- Dependency bumps: `dlt[duckdb]` 1.25.0 → 1.26.0, `dagster` 1.13.0 → 1.13.2 (and the three sibling packages `dagster-webserver`, `dagster-dbt` 0.29.0 → 0.29.2, `dagster-dlt` 0.29.0 → 0.29.2), `nao-core` 0.1.7 → 0.1.8, `typer` 0.24.1 → 0.25.0, `uvicorn` 0.44.0 → 0.46.0, `pydantic` 2.13.2 → 2.13.3, `fastapi` 0.136.0 → 0.136.1.
- Rill 0.86 released the day this version shipped; the `rill_generator.py` module docstring is updated to reference 0.86, but the generator's output (Parquet bridge via `local_file` connector) is unchanged. Rill 0.86's "DuckLake live connector" was probed for v0.1.3 scope but deferred — SQLite-backed DuckLake catalogs hold an exclusive OS-level lock while attached, breaking the "Rill running while pipelines write" workflow that the Parquet bridge supports today.

### Fixed

- **`generate_rill_config` no longer accepts an unused `warehouse_db_path` param** (carried from v0.1.2 known issues). The function only introspects `raw_db_path`; the warehouse-path arg was a leftover. All call sites updated.
- **Type diagnostics in `src/tycoon/ingestion/runner.py` cleared** (carried from v0.1.2 known issues). The `rest_api_source` call now `cast`s its config to dlt's `RESTAPIConfig` typed dict; the env-var warning loop reads the matched `${VAR}` from `_check_unexpanded_env_vars` directly, eliminating the `# type: ignore[union-attr]` on the regex re-search.

[#7]: https://github.com/Database-Tycoon/tycoon-cli/issues/7
[#12]: https://github.com/Database-Tycoon/tycoon-cli/issues/12

## [0.1.2] - 2026-04-19

### Added

- **MotherDuck warehouse alignment**: `tycoon init` (wizard) and `tycoon register dbt` now detect when a registered dbt project targets `md:<name>` via its dbt-duckdb profile and offer to adopt that target as tycoon's warehouse — extending the DuckDB-only alignment check shipped in v0.1.1.
- **`tycoon register warehouse`**: new subcommand that prompts for cloud (MotherDuck) or local (DuckDB) and updates `database.warehouse` + `stack.warehouse` in `tycoon.yml`. For cloud, surfaces `MOTHERDUCK_TOKEN` setup guidance when the env var isn't set. Prompts before overwriting an existing warehouse.
- **`@pytest.mark.e2e` marker** registered in `pyproject.toml`, deselected from the default `pytest` run, plus `tests/test_templates_e2e.py` covering all four built-in templates (csv-import runs a full offline ingest with row-count assertion; nyc-transit hits live public APIs with record caps and an `xfail` on upstream flakes; github-analytics and weather-station are init-only pending template-side parameterization).
- **`.github/workflows/e2e.yml`**: manual-trigger-only CI workflow that runs `pytest -m e2e` with a `GITHUB_TOKEN` secret slot. No cron — runs only when someone clicks "Run workflow".
- **`.github/workflows/ci.yml`**: new PR + main-push gate that runs the full default pytest suite (unit + offline-e2e) plus `ruff check` on every change. Concurrency-gated so pushes cancel superseded runs. Closes the pre-v0.1.2 hole where tests only ran when someone remembered locally.
- **`offline_e2e` pytest marker**: the `csv-import` template test runs the full `init → sources add → sources run → row-count assertion` pipeline with no network or credentials, and is now included in the default `pytest` run. Live-API tests (`nyc-transit`, `github-analytics`, `weather-station`) stay behind the original `e2e` marker and the manual `e2e.yml` workflow.
- **Ruff configuration** in `pyproject.toml`: line length 120, target py312, per-file ignores for the two legitimate lint-exempt patterns (`cli.py`'s post-app command registration, test forward-reference annotations).
- **Test coverage gate in CI** via `pytest-cov`: baseline at v0.1.2 is ~65%; floor set at 60% in `[tool.coverage.report].fail_under` with ~5% headroom for routine drift. CI now fails PRs that drop coverage below the floor, uploads `coverage.xml` as an artifact on the 3.12 matrix leg, and the floor should ratchet upward 1–2 points per release as real tests get added.
- **FastAPI server tests** (11 new): `tests/test_server.py` now exercises every route via `TestClient` — `/`, `/health`, `/check-updates` (with mocked httpx for PyPI-unavailable + HTTP-error paths), `/api/status`, `/api/run/pipeline/{source_name}`, `/api/run/dbt` (including the 404 / 409 busy-state paths), plus the `/ws/logs/{run_id}` WebSocket (unknown-run-id and replay-then-close paths). SubprocessManager now has a state-transition test covering the `busy → not-busy` auto-transition when the underlying process exits.
- **Dagster orchestration smoke tests** (10 new): `tests/test_orchestration.py` covers the main failure mode (the legacy #13 / #4 `DagsterInvalidDefinitionError` class) — `defs` imports cleanly, `build_ingestion_assets` produces one asset per source, dashed source names are sanitized to valid Python identifiers, `get_dbt_resource` / `get_dlt_resource` factories return valid resources, and job selections don't mix AssetKey + AssetsDefinition incorrectly.
- **`CONTRIBUTING.md`**: dev setup, what CI gates on, test marker semantics, code conventions, and the release process. Onboarding doc for first-time contributors.
- **`.pre-commit-config.yaml`**: opt-in pre-commit hook running ruff (`--fix` mode) plus the standard pre-commit-hooks set (trailing whitespace, EOF, YAML, merge conflict, large-file check). Mirrors CI so lint failures are caught before commit instead of after PR open. Opt in with `uvx pre-commit install`.
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
