All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.9] - 2026-06-10

_Headline: Google Sheets source ([#52][]). Plus managed project-local `.venv` + `doctor --fix` ([#57][]), DuckDB Quack live warehouse ([#42][]), pipeline notifications ([#46][]), and scheduled runs ([#48][]). Layer-granular backup ([#31][]) is deferred — no backup track exists yet to make layer-aware (it depended on the deferred DuckLake path). Also closes two High-severity findings from a security review ([#60][], [#61][]). Cycle plan in [`docs/proposals/v0.1.9-scope.md`](docs/proposals/v0.1.9-scope.md)._

### Added

- **`tycoon schedule` — local cron-less scheduled runs** ([#48][]). Run any tycoon command on a timer via the platform-native scheduler — macOS launchd LaunchAgents, Linux `systemd --user` timers — with no daemon and no cloud. `tycoon schedule add <name> --command "data run-all" --at 04:00 [--cadence daily|hourly|weekly] [--notify]`, plus `list` / `remove` / `status` (which tails the run log). Output lands in `~/.local/share/tycoon/schedule/<name>/run.log`; scheduled runs execute from the project root so `tycoon.yml` resolves. `tycoon doctor` reports the count of installed schedules. Windows prints a Task Scheduler pointer (unsupported in v1). Pairs with `--notify` ([#46][]) so unattended runs report in.
- **Pipeline notifications — `tycoon notify` + `run-all --notify`** ([#46][]). A small local-first notification surface so unattended runs don't fail silently. `tycoon notify <success|error|info> <message> [-f key=val ...]` posts to a webhook read from `$TYCOON_NOTIFY_WEBHOOK_URL` (Slack incoming webhooks get a colour-coded attachment; any other URL gets a generic JSON envelope). `tycoon data run-all --notify` emits `success` on completion and `error` (with the failing stage) on failure — best-effort, so a notification problem never fails the pipeline. Non-secret prefs (which severities to emit, a source label) live in an optional `notify:` block in `tycoon.yml`; the URL never does. Webhook + Slack only for v1.
- **DuckDB Quack — live multi-client warehouse, folded into `tycoon start`** ([#42][]). When the [Quack](https://duckdb.org/quack/) extension is available (currently `core_nightly`), `tycoon start` also serves the warehouse over Quack's local RPC protocol on `:9494`, turning the single-writer DuckDB file into a multi-client server. No new commands or flags: a per-project token is generated once into `.tycoon/secrets.yml` (gitignored), and `tycoon data query` attaches over Quack automatically when the server is up (labelled `warehouse (Quack)`), falling back to direct file access otherwise. Skipped silently where the extension can't load. Opt-in by nature (core_nightly-only) and local-only. Coordinating standalone dbt writes against a served warehouse is a planned follow-up.
- **`tycoon setup` builds a managed project-local `.venv`** ([#57][]). The second piece of the managed-environment work: `tycoon setup` creates a `.venv` beside `tycoon.yml` on a supported interpreter via `uv venv --python` (uv auto-downloads a python-build-standalone CPython if the machine only has an unsupported one — zero manual installs), pins it with `.python-version`, and installs tycoon + its dbt/dlt/duckdb stack into it. Flags: `--python` (default 3.13), `--from` (install spec; `-e .` for dev checkouts), `--no-install`, `--force`, `--no-prompt`. If `uv` is absent it points at the standalone installer rather than running it. **`tycoon doctor --fix`** runs the same build flow when the interpreter check fails. Together with the v0.1.9 interpreter check, this closes the Python-version trap that produced [#55][].
- **Google Sheets data source** ([#52][]). `tycoon data sources add google_sheets` registers a spreadsheet as a first-class source — pulling tabs/ranges into DuckDB with the header row becoming typed columns. Auth is a Google service-account JSON key (headless/cron-friendly), defaulting to the standard `${GOOGLE_APPLICATION_CREDENTIALS}` env var; leaving the key blank falls back to dlt's own resolution (the OAuth / ADC path). Config is `spreadsheet_url_or_id` (required) and an optional comma-separated `range_names` (blank loads every sheet). Works under `--no-prompt` for scripted bootstrap. Per project convention the dlt `google_sheets` verified source isn't bundled — it's pulled on demand via `dlt init`. First cut is full-refresh replace per run (Sheets has no native incremental key).
- **`tycoon doctor` checks the Python interpreter version** ([#57][]). A new first check verifies the running interpreter is within tycoon's supported range (`>=3.12,<3.14`) and fails with an actionable hint otherwise — calling out that 3.14 has no dbt wheels yet and pointing at `uv venv --python 3.13`. tycoon runs dbt out of the same interpreter it lives in, so an out-of-range interpreter previously failed far from its cause at `data transform run` (this is how [#55][] stayed invisible). First sub-piece of the managed-`.venv` onboarding work; runs even without a `tycoon.yml`.

### Security

- **Fivetran credentials can no longer leak into a committed `tycoon.yml`** ([#60][]). `stack.ingestion_metadata.api_key` / `api_secret` are now `pydantic.SecretStr`, so they mask to `**********` in any `repr`/traceback, and their field docs steer you to `${FIVETRAN_API_SECRET}`-style env-var indirection (the loader already expands `${VAR}` before validation, keeping the literal secret out of the file). `save_project` now preserves the hand-authored `ingestion_metadata` block verbatim on round-trip — previously a `sources add` / `register` write would re-dump the *expanded* secret straight back into `tycoon.yml`. The scaffolded `.gitignore` also now excludes `.env`, `.dlt/secrets.toml`, and `**/profiles.yml` (the files that actually hold credentials); `tycoon.yml` stays committable as the shareable stack template.
- **SQL identifier injection in Rill export and `data schema` is closed** ([#61][]). Schema/table/column names sourced from `tycoon.yml` or introspected from a DuckDB file are now quoted via a shared `quote_identifier` helper before interpolation into SQL. Previously an attacker-crafted `schema:` value in a shared project could break out of the `COPY … TO` statement that `tycoon data analyze --rill` runs — and DuckDB's `COPY`/`INSTALL` can write files and load extensions, so this was a path to arbitrary file write, not just data disclosure. The export's destination-path literal is escaped too. (The broader `tycoon.yml` identifier/path validation layer is tracked in [#65][].)

### Fixed

- **Robustness polish from PR review** (PR [#59][]). `tycoon schedule add --command` now tolerates a redundant leading `tycoon` (so `"tycoon data run-all"` doesn't become `tycoon tycoon …`); Quack detection tries a plain `LOAD quack;` before the network `INSTALL … FROM core_nightly` for offline/cached use; `tycoon notify` swallows *any* webhook exception (not just `httpx.HTTPError`) so a malformed URL can't crash a pipeline; the Google Sheets service-account key is read as UTF-8 (Windows safety); and `tycoon notify --field` rejects an empty key.

[#31]: https://github.com/Database-Tycoon/tycoon-cli/issues/31
[#42]: https://github.com/Database-Tycoon/tycoon-cli/issues/42
[#46]: https://github.com/Database-Tycoon/tycoon-cli/issues/46
[#48]: https://github.com/Database-Tycoon/tycoon-cli/issues/48
[#52]: https://github.com/Database-Tycoon/tycoon-cli/issues/52
[#55]: https://github.com/Database-Tycoon/tycoon-cli/issues/55
[#57]: https://github.com/Database-Tycoon/tycoon-cli/issues/57
[#59]: https://github.com/Database-Tycoon/tycoon-cli/pull/59
[#60]: https://github.com/Database-Tycoon/tycoon-cli/issues/60
[#61]: https://github.com/Database-Tycoon/tycoon-cli/issues/61
[#65]: https://github.com/Database-Tycoon/tycoon-cli/issues/65

## [0.1.8] - 2026-05-30

_A small, focused release: live Fivetran status in `tycoon data status` ([#50][]) plus a Python-version guardrail ([#55][]) so dbt-incompatible interpreters (3.14) aren't silently selected. The Quack headline and the backup / operate-in-prod tracks planned in [`docs/proposals/v0.1.8-scope.md`](docs/proposals/v0.1.8-scope.md) continue toward a later cut. See [`docs/releases/v0.1.8.md`](docs/releases/v0.1.8.md) for the full narrative._

### Changed

- **`tycoon data status` reads Fivetran live, with write-through cache** ([#50][]). The Sources panel and Fivetran detail no longer render only the last `tycoon data fivetran sync` snapshot — `data status` now makes a live `list_connectors()` call on every run and writes the result through to `.tycoon/metadata.duckdb`, so the panel is fresh by default. On incomplete credentials, auth failure, or network error it warns and falls back to the last cached snapshot (non-fatal). Closes the v0.1.7 design Q3 deviation where freshness was bounded by the last manual sync. `tycoon data fivetran sync` stays as the cron-friendly bulk-populate command.

### Fixed

- **Cap `requires-python` at `<3.14`** ([#55][]). The floor was `>=3.12` with no ceiling, so on a machine whose default interpreter is Python 3.14 the environment resolved to 3.14 — where dbt-core 1.11.8 / dbt-duckdb 1.10.1 have no support yet, breaking `tycoon data transform run`. Now `>=3.12,<3.14` with a re-locked `uv.lock`, so a too-new interpreter is no longer selected (uv picks or fetches a compatible 3.12/3.13). Lift the ceiling once dbt ships 3.14 wheels.

[#50]: https://github.com/Database-Tycoon/tycoon-cli/issues/50
[#55]: https://github.com/Database-Tycoon/tycoon-cli/issues/55

## [0.1.7] - 2026-05-25

_The layered-architecture release. Tycoon learns the sources → staging → intermediate → marts mental model and surfaces it across `data status`, `doctor`, `semantics scaffold`, and `data history`. Plus the test-resilience second wave ([#39][], [#41][]) and non-interactive `data sources add` ([#44][]) to unblock online recipe doctests. See [`docs/releases/v0.1.7.md`](docs/releases/v0.1.7.md) for the full narrative._

### Added

- **Layer-aware data model** ([#30][]). New `tycoon.layers` module classifies every table tycoon governs into one of `source` / `staging` / `intermediate` / `mart` / `snapshot` / `seed` / `unclassified`. dbt-side classification flows from the manifest using folder convention (`models/staging/`, `models/intermediate/`, `models/marts/`, plus the `core/` and `published/` aliases) with per-model `meta.tycoon_layer` and per-folder `+meta.tycoon_layer` overrides. Source-side classification reads dlt's `sources:` block in `tycoon.yml` and Fivetran connector snapshots. No new `tycoon.yml` block — classification authority lives in the tools that own the objects.
- **`tycoon data status` becomes layer-organized** ([#30][]). The dlt and Fivetran panels collapse into a unified **Sources** panel (vendor column distinguishes the rows) joined by **Staging**, **Intermediate**, and **Marts** panels. Projects without dbt still see all four panels with empty-state hints pointing at `tycoon register dbt`.
- **`tycoon doctor` layer-coverage check** ([#30][]). New non-fatal row reports any registered source that has no staging model. Skips silently when `transformation: none` or the dbt manifest hasn't been compiled yet.
- **`tycoon data history --layer`** ([#30][]). New flag filters dbt invocations to those that touched at least one model in the named layer (staging / intermediate / mart / snapshot / seed). Mutually exclusive with `--source`. Requires a compiled dbt manifest.
- **`tycoon` dbt tag on auto-scaffolded observability models** ([#30][]). Every model produced by `tycoon data observability scaffold` (the `stg_tycoon__*` views + `dim_runs`) now carries `tags=['tycoon']` so you can run `dbt run --exclude tag:tycoon` (or `tycoon data transform run --exclude tag:tycoon`) when iterating on business logic without rebuilding tycoon's bookkeeping models.
- **`docs/recipes/layered-architecture.md`** — full mental-model recipe covering the four layers, classification rules, override mechanisms via `meta.tycoon_layer`, and a migration guide for projects with a flat `models/` directory.
- **Non-interactive `tycoon data sources add`** ([#44][]). New flags: `--name`, `--schema`, `--base-url`, `--resources`, `--connection-string`, `--path`, repeatable `--config key=value`, `--no-prompt`, and `--force` for scripted overwrite. Interactive mode is untouched — passing the new flags simply skips the corresponding prompts. Catalog credentials default to `${ENV_VAR}` references in both modes. Designed for CI / scripted bootstrap / online recipe doctests.
- **README PokéAPI quickstart re-enabled as an online recipe doctest** ([#44][]). The live-API arc is now marked `<!-- tycoon-test: mode=online -->` and runs under `nightly-e2e.yml`'s `--run-online` step. Surfaces upstream-API contract drift within 24 hours. The arc uses the new `--no-prompt` flag and scopes `dbt run` to `stg_pokeapi__*` so it cohabits cleanly with the csv-import template's own models.
- **Snapshot harness for rendered Rich CLI output** ([#41][]). New `tests/test_snapshots.py` (syrupy-backed) pins the exact string form of install hints, doctor rows, and common error paths. Golden files live in `tests/__snapshots__/`. Catches the class of bug (`[extra]` bracket strip, doctor row text drift, stale package names) that today's "some error appears" assertions miss. Update workflow: `uv run pytest --snapshot-update tests/test_snapshots.py` regenerates the goldens; the diff lands in the PR as plain-text changes a reviewer can read at a glance. v1 covers 11 anchored renders; full-screen panels with time-dependent fields deferred to v2 with a redactor pass.

### Changed

- **`tycoon semantics scaffold` switches mart discovery from prefix matching to layer classification** ([#30][]). Previously globbed for `mart_*` / `fct_*` / `dim_*` / `obt_*`; now reads the dbt manifest and respects per-model overrides. Falls back to the old prefix matcher (with a clear warning) when no manifest is available, so behaviour is preserved for unmigrated projects.

### Fixed

- _TBD._

[#30]: https://github.com/Database-Tycoon/tycoon-cli/issues/30
[#39]: https://github.com/Database-Tycoon/tycoon-cli/issues/39
[#40]: https://github.com/Database-Tycoon/tycoon-cli/issues/40
[#41]: https://github.com/Database-Tycoon/tycoon-cli/issues/41
[#44]: https://github.com/Database-Tycoon/tycoon-cli/issues/44

## [0.1.6] - 2026-05-18

_The dbt-shop polish release. Headline is OSI semantic-layer scaffolding ([#28][]); the supporting work makes the dbt side of tycoon behave the way an experienced dbt user expects. Adds first-class profile handling ([#27][]), Fivetran metadata read-out ([#26][], pulled forward from v0.2.x), in-CLI recovery paths for `init` skip-prompts ([#34][] / [#37][]), and a new subprocess-driven CI gate ([#40][]) that catches the class of bugs ([#32][] + Rich bracket strip) that escaped to PyPI in v0.1.5. See [`docs/releases/v0.1.6.md`](docs/releases/v0.1.6.md) for the full narrative._

### Added

- **Fivetran metadata read-out** ([#26][]). New `tycoon data fivetran sync` and `tycoon data fivetran list` commands. When `stack.ingestion = fivetran` in `tycoon.yml`, tycoon pulls connector metadata (id, schema, service, sync_state, succeeded_at, failed_at, paused) from the Fivetran Metadata API and snapshots it into `.tycoon/metadata.duckdb` under a new `fivetran_connectors` table. `tycoon data status` and `tycoon doctor` light up for projects that use Fivetran for ingestion. Read-only — tycoon does not *run* Fivetran. Originally targeted v0.2.x; pulled forward because the surface is small (no new install footprint — `httpx` is already a base dep). New typed `stack.ingestion_metadata` block in `tycoon.yml` carries `api_key`/`api_secret`/`group_id`.
- **`tycoon semantics` namespace** ([#28][]). New top-level command group: `scaffold` (generate `dbt_project/semantic/osi.yaml` from your warehouse marts, conforming to OSI v0.1.1) and `doctor` (validate against the vendored OSI v0.1.1 JSON Schema, hard exit code for CI). Conservative dial — datasets + dimensional fields are scaffolded; metrics + relationships are left empty for the user to fill in (OSI metrics are SQL expressions tycoon can't reasonably guess). Sentinel-protected with `--force` override, same pattern as `tycoon data analyze`. New optional `transform.auto_osi_scaffold` config key (default false) auto-emits the file after a successful `dbt run`/`build`. `tycoon doctor` includes a non-fatal OSI validation row when the file is present.
- **`tycoon profiles` namespace** ([#27][]). New top-level command group with three subcommands: `list` (every profile + targets + adapters, flagging the active one), `show NAME` (pretty-print a profile with secrets redacted), `doctor` (verify resolution + adapter matches `stack.warehouse`). Sits alongside `tycoon register` and `tycoon doctor` in the Project section.
- **`--profile` / `--profiles-dir` / `--target` flags** on every dbt-touching command — `tycoon data transform run/test/build/docs`. Flag names match dbt's CLI exactly. Resolution order: CLI flag → `tycoon.yml` → `<dbt_project_dir>/profiles.yml` → `$DBT_PROFILES_DIR` → `~/.dbt/profiles.yml`.
- **`tycoon doctor` now includes a non-fatal "dbt profile" check** that validates the resolved profile's adapter matches `stack.warehouse`, catching duckdb-vs-snowflake mismatches before a `dbt build` does.
- **`docs/recipes/existing-dbt-profile.md`** — recipe for using an existing `profiles.yml` from anywhere on disk (under `~/.dbt`, in a shared config repo, alongside an existing dbt project).
- **`tycoon register dbt --create`** ([#34][]). Recovery path for users who picked **Skip** on the dbt prompt during `tycoon init` — bootstraps a fresh dbt project at `../<project>-dbt` (or any path you pass) wired to the active tycoon warehouse, then registers it. Same scaffolder the init wizard uses (`_scaffold_dbt_project`) — produces a runnable `dbt_project.yml` + `profiles.yml` so `tycoon data transform run` works immediately. DuckDB and MotherDuck warehouses only; refuses to overwrite an existing `dbt_project.yml`. Marks `stack.transformation_managed: true` since tycoon owns the project.
- **`tycoon doctor` distinguishes the half-init state for nao** ([#38][]). When `tycoon.yml` has an `ask.llm` block but `.tycoon/nao/nao_config.yaml` is missing (or required dirs are absent), doctor now suggests `tycoon ask init` instead of `tycoon register llm`. Cold-start state (no `ask.llm` at all) still suggests `register llm`. The change avoids sending users into a re-prompt loop that overwrites nothing they wanted changed. Pairs with #37.
- **`tycoon ask init`** ([#37][]). Standalone idempotent project-bootstrap that writes `.tycoon/nao/nao_config.yaml` and `AGENTS.md` from the active `tycoon.yml`'s `ask.llm` block. Doesn't prompt for any LLM details — that's `tycoon register llm`'s job. Use when you hand-edited `ask.llm` in `tycoon.yml`, cloned a teammate's project (where `.tycoon/nao/` is gitignored), or `register llm` half-succeeded. `--force` overwrites an existing `nao_config.yaml`; `--no-refresh-agents-md` skips the `AGENTS.md` regen. Re-introduction of a removed-in-v0.1.5 surface with a different (cleaner) contract — the old version was a confusing alias for `register llm`; this one is purely the post-config write step. Refactor: `setup_ask_stack()` now delegates to a new `_init_nao_project()` helper, which all three init paths (`tycoon init`, `register llm`, and the new `ask init`) share — no body duplication.
- **Recipe doctest harness + demo-arc CI test** ([#40][]). New `tests/test_recipe_doctests.py` walks `README.md` and `docs/recipes/*.md` for `<!-- tycoon-test: mode=offline|online -->` markers and executes each marked bash block via subprocess (`bash -e -o pipefail` in a fresh tmp dir). Offline blocks run on every PR; online blocks gate on `--run-online` and run in `nightly-e2e.yml`. Plus `tests/test_e2e_demo_arc.py` — a subprocess-driven csv-import demo arc that shells out to the real `tycoon` binary (rather than Typer's in-process `CliRunner`), catching PATH / Rich rendering / console-script wiring bugs that earlier tests couldn't see. Closes the gate behind the two CI-escaped bugs in this cycle ([#32][] + Rich bracket strip). Subsumes [#33][]. Documents marker convention in `tests/README.md`. Follow-up [#44] tracks the non-interactive `sources add` flags that would let the README's PokéAPI quickstart come back as an online recipe block.

### Changed

- **dbt profile resolution centralized in `src/tycoon/dbt_profiles.py`** ([#27][]). Previously, only `tycoon register dbt` resolved profiles correctly; `tycoon data transform`, the Dagster `DbtCliResource`, and the FastAPI `/run/dbt` route all hardcoded `profiles_dir` to a path relative to the tycoon source tree (broken for installed users). Every dbt-touching surface now routes through one helper that matches dbt's own resolution.
- **`nao-core` bumped `0.1.8 → 0.1.11`** in the `[ask]` extra. Patch-level upstream — picks up the latest fixes from the nao-core team.

### Removed

- **Redundant `websockets==16.0` pin** dropped from the `[server]` extra. `uvicorn[standard]==0.46.0` already pulls websockets transitively as the protocol implementation behind fastapi's `WebSocket` class. Tycoon never imported `websockets` directly. No change to what gets installed; just removes our redundant declaration. Flagged during the v0.1.5 dependency audit.
- **Redundant `ibis-framework[duckdb]==12.0.0` pin** dropped from the `[ask]` extra. `nao-core` already lists `ibis-framework` in its requires, and tycoon never imported `ibis` directly. No change to what gets installed; just removes our redundant declaration. Flagged during the v0.1.5 dependency audit.

### Fixed

- **`register dbt --create` produced a project that failed `transform run` standalone.** Surfaced while writing the e2e coverage for [#34][]. The scaffolded `profiles.yml` ATTACHes `data/raw.duckdb` read-only, but if the user runs `tycoon data transform run` before any `tycoon data sources run` (no ingestion yet → no raw.duckdb on disk), dbt fails with `Cannot open database in read-only mode: database does not exist`. Real demo arc usually masks this because users ingest before transforming, but the recovery path from #34 hits it. Fix: `_scaffold_dbt_project` now pre-creates an empty DuckDB file at the raw path if missing (same pattern as the metadata DB it already pre-creates). Locked in with a new offline e2e test (`test_register_dbt_create_e2e`) that runs `register dbt --create` → `transform run` against an empty project and asserts exit 0 — would catch any future regression of this pair.
- **Install hints stripped the `[extra]` name from output.** Every `error()` / `warn()` / `info()` message that suggested `pip install 'database-tycoon[ask]'` (and similar for `[docs]` / `[dagster]`) rendered as `pip install 'database-tycoon'` — Rich was parsing `[ask]` as a style tag, finding no such style, and silently stripping the brackets. Users hitting these errors copied the broken command verbatim and missed the extra. Fixed by escaping the bracket (`\[ask]`) in all 7 user-facing strings; locked in with a regex-based regression test in `tests/test_cli_surface.py` that scans every `commands/*.py` for unescaped extras names. Bug was visible in `tycoon ask chat`, `tycoon register llm`, `tycoon init`, `tycoon start --only dagster`, and `tycoon docs serve/build` when the relevant extra wasn't installed.
- **rest_api ingestion was completely broken** ([#32][]). `tycoon data sources run pokeapi` (and any other rest_api source) failed with `Path '.': missing required fields {'client'}` because the runner cast tycoon's flat config shape directly to dlt's `RESTAPIConfig`, which expects `base_url` wrapped under `client` and `resources` as a list (not a comma-separated string). The fastest-path quickstart from the README was non-functional. Fixed by normalizing the flat shape into dlt's wrapped shape inside `_build_rest_api_source`, with a regression test that exercises the actual `rest_api_source` build (not just the schema).

[#26]: https://github.com/Database-Tycoon/tycoon-cli/issues/26
[#27]: https://github.com/Database-Tycoon/tycoon-cli/issues/27
[#28]: https://github.com/Database-Tycoon/tycoon-cli/issues/28
[#32]: https://github.com/Database-Tycoon/tycoon-cli/issues/32
[#33]: https://github.com/Database-Tycoon/tycoon-cli/issues/33
[#34]: https://github.com/Database-Tycoon/tycoon-cli/issues/34
[#37]: https://github.com/Database-Tycoon/tycoon-cli/issues/37
[#38]: https://github.com/Database-Tycoon/tycoon-cli/issues/38
[#40]: https://github.com/Database-Tycoon/tycoon-cli/issues/40
[#44]: https://github.com/Database-Tycoon/tycoon-cli/issues/44

## [0.1.5] - 2026-05-03

_Polish + correctness release. Closes [#7][] (4/6 → 6/6 sub-asks complete) and three bugs caught by new e2e coverage ([#22][], [#23][], [#24][]). Moves LLM config from `tycoon ask init` to `tycoon register llm` so the `ask` namespace is reserved for analytics endpoints. See [`docs/releases/v0.1.5.md`](docs/releases/v0.1.5.md) for the narrative._

### Added

- **`tycoon register llm <provider>`.** Symmetric with `register dbt` / `register warehouse` — points tycoon at an LLM runtime and writes the linkage to `tycoon.yml`. Six provider shortcuts (`lm-studio`, `ollama`, `openai`, `anthropic`, `gemini`, `mistral`). No-arg form refreshes setup against the existing provider. `--skip-install` bypasses the post-register model install offer; `--base-url`, `--model`, `--api-key-env` available for explicit overrides.
- **Auto-scaffold dbt staging models from dlt schema.** `tycoon data analyze` got a `--force` flag plus a `@generated by tycoon analyze` sentinel so re-runs skip user-edited files. Auto-triggers after `tycoon data sources run <name>` when no staging exists for the source yet. Project-wide opt-out via `transform.auto_scaffold: false`; per-call via `--no-scaffold`. Plus `--all` flag for multi-source scaffolding.
- **Local LLM probe + recommended model.** `tycoon ask doctor` and `tycoon ask chat` now distinguish "runtime unreachable" from "runtime up but 0 models loaded". The recommended model is **Qwen 2.5 Coder 7B Instruct (Q4_K_M, ~4.7 GB)** — same weights work via `ollama pull qwen2.5-coder:7b` and via LM Studio's Discover. Ollama auto-pulls; LM Studio auto-loads (see below).
- **LM Studio model auto-load.** When LM Studio is reachable but has chat models *downloaded* yet 0 *loaded* in memory, tycoon now offers to call `lms load <model>` automatically rather than punting users to the GUI. Triggers from both `tycoon register llm` and `tycoon ask chat`'s fail-fast — accepting the prompt loads the model in 5-30s and the user continues straight to chat. Falls back to the GUI hint if `lms` isn't on PATH (or at the standard `~/.cache/lm-studio/bin/lms` location). Prefers the recommended Qwen 2.5 Coder if downloaded; otherwise picks the first chat-capable model. Embeddings-only models are filtered out.
- **CLI surface stale-string sentinel.** New `tests/test_cli_surface.py` walks every `.py` under `src/tycoon/` and rejects any file containing a known-removed command name or wrong package name. The `_STALE_SUBSTRINGS` registry is one-line-extensible after future renames. Caught and prevented three classes of drift bugs that shipped in earlier RC builds: `tycoon ask init` references in user-facing strings, `pip install tycoon[ask]` (wrong package name; should be `database-tycoon[ask]`), and `tycoon start --only nao` warning users at the removed `tycoon ask init && tycoon ask sync`.
- **Wizard auto-detect.** `tycoon init`'s LLM prompt probes `:1234` (LM Studio) and `:11434` (Ollama). Exactly one runtime up → 1-keystroke `Use X? [Y/n]` confirm instead of the 7-option menu. Both up + only one has models → suggests the loaded one. Both up + both have models → menu (truly ambiguous).
- **`tycoon init` chains AI agent setup** automatically when the user picks an LLM in the wizard AND `nao_core` is importable. The chained call writes `nao_config.yaml`, refreshes `AGENTS.md`, seeds `ask.exclude_schemas`, and offers a model install — same flow as `tycoon register llm` would have. True one-command setup for users with the `[ask]` extra.
- **`ask.exclude_schemas` smart defaults ([#7][] §3).** When unset, `tycoon register llm` seeds with conservative noise patterns (`information_schema`, `pg_catalog`, `_tycoon`, `sqlmesh__main`, etc.). Idempotent — preserves user-set values.
- **csv-import mart layer.** `dbt_project/models/marts/fct_widget_summary.sql` + `schema.yml`. Demonstrates the staging→mart pattern; the offline e2e asserts mart values + runs `dbt test`.
- **Templates that declare `dbt_project_dir` but don't ship one now get one scaffolded** during `tycoon init --template <name>`. Previously only `csv-import` had a working dbt project on init.
- **`docs/reference/dependencies.md`** — per-package documentation of every pin in `pyproject.toml` (base + each extra + dev), what each package is used for at runtime, and an "install footprint" summary. Flags two pins (`websockets` in `[server]`, `ibis-framework[duckdb]` in `[ask]`) as candidates for removal in v0.1.6 since both are pulled transitively.

### Changed

- **Demoted `weather-station` and `github-analytics` templates.** They stay on disk so `tycoon init --template <name>` still works, but they no longer appear in `--list-templates` output, the docs landing pages, or the CI smoke matrix. Featured surface is now `csv-import` (offline) and `nyc-transit` (live).
- **Filesystem source CSV ingest now uses `replace` semantics** ([#22][]) — was previously `append`. Re-running `tycoon data sources run files` no longer doubles row counts.
- **`tycoon data sync` continues past broken views** ([#23][]). Views referencing unattached catalogs (e.g. dbt's `tycoon_meta`) are recorded in `SyncResult.skipped` and warned about; the sync proceeds for every other table.
- **`capture_dlt` rewritten to ATTACH `raw_db` from `meta_con`** ([#24][]). Avoids the same-process DuckDB connection-config conflict that silently zeroed out `dlt_runs` for filesystem sources. Single connection, no intra-process collision.
- **`ask doctor` LLM panel now FAILs when reachable + 0 models loaded** (was previously OK with `0 models loaded` in the detail). Same probe is run before `tycoon ask chat` launches — refuses to start a dead UI.
- **Wizard's LLM prompt always recommends a local provider first.** Added "AI agent" header note flagging that skipping leaves `tycoon ask chat` unavailable but the rest of tycoon works regardless.

### Removed

- **`tycoon ask init` and `tycoon ask install-model`.** Their surface moved entirely to `tycoon register llm`. The `ask` namespace is now reserved for analytics endpoints (chat, sync, context, doctor, skills, mcp). Read-only LLM probing stays in `ask doctor`.
- **e2e tests for the demoted templates** (`test_weather_station_e2e`, `test_github_analytics_e2e`).

### Fixed

- [#22][] — Filesystem source CSV ingest defaulted to `append` instead of `replace`. One-line fix in `_build_filesystem_source`.
- [#23][] — `tycoon data sync` failed entire run on any view referencing an unattached catalog. Per-table resilience.
- [#24][] — `capture_dlt` silently failed for filesystem source. ATTACH-based query path.
- **LM Studio probe was counting downloaded, not loaded models.** `_probe_local_llm` used the OpenAI-compat `/v1/models` endpoint which returns models on disk regardless of memory state. Switched to LM Studio's `/api/v0/models` which exposes per-model `state: loaded | not-loaded`. `tycoon ask doctor` and `tycoon ask chat`'s fail-fast now accurately distinguish "downloaded" from "ready to serve." Falls back to `/v1/models` for older LM Studio versions.
- **Stale references to removed commands across `src/tycoon/`.** Three user-facing strings still pointed at `tycoon ask init` (which v0.1.5 removed): the AGENTS.md auto-generated header, `tycoon start --only nao`'s warning, and the `_require_nao` install hint (which also had the wrong package name `tycoon[ask]` instead of `database-tycoon[ask]`). All fixed and locked in by the new stale-string sentinel test.
- **`scaffolding/templates.py` comment referenced the removed command.** Doesn't affect runtime, but caught for hygiene.

[#7]: https://github.com/Database-Tycoon/tycoon-cli/issues/7
[#22]: https://github.com/Database-Tycoon/tycoon-cli/issues/22
[#23]: https://github.com/Database-Tycoon/tycoon-cli/issues/23
[#24]: https://github.com/Database-Tycoon/tycoon-cli/issues/24

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
