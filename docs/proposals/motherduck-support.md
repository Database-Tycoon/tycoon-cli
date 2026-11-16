# MotherDuck end to end

_Status: roadmap agreed 2026-10-20 and tracked in [#429](https://github.com/Database-Tycoon/tycoon-cli/issues/429), the MotherDuck-only slice of milestone issue #87. DuckLake and object storage stay on #87._

## Goal

A project starts on local DuckDB files and can move each of its three targets, raw, warehouse and metadata, to MotherDuck when it chooses. The switch is a config change, not a re-init: `tycoon register warehouse --type motherduck` already rewrites `database.warehouse` to an `md:` catalog (and `database.raw` too, when both pointed at the same file), and `register warehouse --type duckdb` puts a project back on local paths. The work here is making the rest of the stack follow that switch.

Two things the switch does not do, and should not pretend to:

- It doesn't move data. Changing `database.raw` from a file to `md:` leaves the rows in the file. The next run starts fresh in MotherDuck, with dlt's incremental cursors reset. A local-to-cloud copy would be a separate feature.
- It doesn't move run history. Events recorded while local stay in `.tycoon/metadata.duckdb`. `metadata.backend` is chosen independently of the warehouse, so history can stay local while the warehouse is in the cloud, or the other way round.

## Where things stand

Since #296 (merged 2026-10-03) the warehouse side of the switch works. `TycoonConfig` in `src/tycoon/config.py` resolves `raw_target` and `warehouse_target` as connection strings, passes an `md:` string through verbatim, and `raw_db` exits with "this command only works with a local raw DuckDB file so far" instead of turning the string into a nonsense local path. `data query`, `data schema`, dbt profile generation, `doctor`'s auth check and `data sync` all handle MotherDuck.

What still assumes a local file, and therefore stops at that exit or at an `.exists()` check:

- Raw ingestion. `tycoon data sources run` and `run-all` pass `cfg.raw_db` into the runner, which builds every pipeline with `dlt.destinations.duckdb(str(raw_db_path))`: once in `ingestion/runner.py`, seven times in the shim templates in `source_manager.py`, and once in each legacy pipeline module.
- `tycoon data analyze` and the staging auto-scaffold that runs after a source finishes (`commands/explore.py`, `commands/sources.py`).
- OSI scaffolding: `semantics scaffold` exits with "MotherDuck isn't supported yet" and the auto-scaffold after `transform` skips (#298).
- Run history. `data status` and `data history` construct `DuckDBFileBackend(metadata_db_path(root))` by hand, as do the two event writers in `ingestion/runner.py` and `commands/transform.py`. `metadata.backend` is in the schema with one accepted value and nothing reads it.
- The MotherDuck dbt profile still ATTACHes the local `tycoon_meta` database (`scaffolding/templates.py`).

Two facts shape the order below.

dlt 1.26.0, the pinned version, ships `dlt.destinations.motherduck`, and `dlt.destinations.motherduck("md:x")` builds a destination with those credentials (verified locally). Raw ingestion into MotherDuck is therefore a swap of dlt destination class and does not depend on the Destination Protocol from #110 or on the M4 runtime rewrite. That protocol serves tycoon's own introspection and query needs (`analyze`, the auto-scaffold, OSI) and can land after ingestion works.

A `MotherDuckMetadataBackend` covers only the `events` and `snapshots` tables. The legacy capture path, which #381 split out of `observability.py` into `src/tycoon/observability/` (`dlt_capture.py`, `dbt_capture.py` and `store.py`), opens the local metadata file directly for dlt traces, dbt runs and manifest diffs, and `data status` still reads `dlt_runs` and `dbt_nodes` from it through `duckdb.connect`. No open issue retires that path. #116 deletes `runner.py`, `source_manager.py` and `ducklake_config.py` only, and #129 leaves `_query_run_counts` and `_query_layer_last_build` in `status.py` alone on the stated assumption that #116 covers them, so the gap is currently unowned. Until it has an owner, a project with `metadata.backend: motherduck` would keep half its history in a local file. So the backend lands as an opt-in next to the M4 work, and scaffolds only default to it afterwards.

## Phases

Each phase is one two-week release cycle and each task is one pull request within the eight-file cap from `CONTRIBUTING.md`. `CHANGELOG.md` counts as a file, so budget seven others. Later phases depend on earlier ones.

### Phase 0, v0.2.4: safety, then raw ingestion

| Issue | Change |
|---|---|
| #308 | One `is_motherduck()` helper that accepts `md:` and `motherduck:`, used wherever the code checks the prefix today |
| #310 | `data schema` reports estimated row counts on MotherDuck instead of an exact `count(*)` per table |
| #309 | `data query` refuses DDL and DML against MotherDuck unless asked |
| #430 | Raw ingestion builds `dlt.destinations.motherduck` for an `md:` raw database |
| #298 | OSI scaffolding reads a MotherDuck warehouse (already planned for v0.2.4; it joins Phase 1 if it slips) |
| #437 | A manual job in `.github/workflows/e2e.yml` that runs the `e2e`-marked MotherDuck tests against scratch databases, so #430 and every MotherDuck PR after it can be checked against a real catalog. Split out of #431 |

#308 goes first because the other three want the helper; without it, `build_destination()` in Phase 1 would hardcode `md:` one more time. The four Phase 0 PRs are stacked in that order with `gh stack`, branched from the v0.2.4 release branch once it opens.

#430 is the first change a user notices, and it has a second gate the original plan missed. After a load, `commands/sources.py` calls `cfg.raw_db` to auto-scaffold staging models, `_warn_if_legacy_filesystem_table_exists` calls `get_tables(raw_db_path)`, and `capture_dlt` checks `raw_db.exists()`. Each needs to skip cleanly on an `md:` target, with a one-line note, until Phase 1 routes it through a destination. The three legacy pipeline modules (`mta_pipeline.py`, `mta_bus_speeds_pipeline.py`, `nyc_dot_pipeline.py`) call `raw_db_path.parent.mkdir(...)`; #111 ports `_dispatch_legacy()` into `DltManagedRuntime` and keeps them, so they stay local-only behind the existing error. `ingestion/ducklake_config.py`, whose `get_destination()` was meant to do this routing and has no callers, is deleted in the same PR.

### Phase 1, v0.2.5: Destination Protocol

| Issue | Change |
|---|---|
| #110 | `Destination` protocol in `core/destination.py` (no duckdb import), `DuckDBDestination`, and `build_destination(target, root)` dispatching on `is_motherduck()`. Additive, no consumers. Moved from v0.3.0: it fits the "rewrite foundation" cycle and nothing in M4 needs it first |
| #118 | `MotherDuckDestination`, with `analyze_cmd`, `_analyze_all` and the post-run auto-scaffold routed through `build_destination()` |

`build_destination()` takes the resolved target string, not a warehouse-type value: `database.raw` and `database.warehouse` hold connection strings and the prefix is the signal. An `md:` connection can't be opened `read_only` (DuckDB refuses it for the in-memory database the connection starts from), so write protection on the MotherDuck side comes from the token's scope, as `data query` already documents.

### Phase 2, v0.3.0: run history in MotherDuck, opt in

| Issue | Change |
|---|---|
| #120 | `MotherDuckMetadataBackend`, same Protocol as `DuckDBFileBackend`, no `parent.mkdir()`, no `read_only`. The contract suite in `tests/test_metadata_contract.py` gains a `motherduck` fixture entry, skipped without `MOTHERDUCK_TOKEN`. `MetadataConfig.backend` becomes a `Literal` so an unknown value fails loudly |
| #129 | `open_metadata_backend(project, root)` in `metadata_backends/__init__.py`, used by the two readers and the two writers |

Where the catalog name lives for the metadata backend (`metadata.path` holding the `md:` string, or a new key) is decided in #120 and recorded there.

### Phase 3, v0.3.1: scaffolding and docs

| Issue | Change |
|---|---|
| #128 | MotherDuck dbt profiles stop ATTACHing `tycoon_meta`; a fresh MotherDuck scaffold from `tycoon init` writes `metadata.backend: motherduck`. Projects retrofitted with `register warehouse` are untouched |
| #431 | A recipe page for the local-to-MotherDuck path. The token-gated e2e job moved to Phase 0 as #437 |

Phase 3 depends on the legacy capture path having been retired, which no open issue currently covers (see the Phase 0 note above). If that work slips or stays unowned, #128's profile change can still ship and the `metadata.backend` default waits.

## Upgrade safety

Every phase must leave a project on local DuckDB files behaving exactly as before, and the tests for each PR should include that case alongside the MotherDuck one (see "Testing for upgrade safety" in `CONTRIBUTING.md`).

`metadata.backend` is an unvalidated string today. A `tycoon.yml` with `backend: motherduck` written by a newer tycoon would make an older tycoon silently use the local file. The `Literal` in Phase 2 means new code refuses unknown values; the release notes for that version should name it as the first version that understands the value.

## Verification

- `uv run pytest -q`, `uv run ruff check src tests` and `uv run ruff format --check src tests` before every commit, and CI green on each PR before the next layer in a stack is opened.
- No unit test needs a MotherDuck account. `duckdb.connect` and `dlt.pipeline` are mocked for the MotherDuck branches; the real-backend tests carry the `e2e` marker or skip without `MOTHERDUCK_TOKEN`.
- Manual end to end, with a token, at the close of each phase: `tycoon init` choosing MotherDuck, `tycoon data sources add rest_api`, `tycoon data sources run`, and the rows are in the `md:` catalog rather than a local file. From Phase 2, `tycoon data status` and `tycoon data history` read from the same catalog when `metadata.backend: motherduck` is set.

## Out of scope

DuckLake (#122), object storage (#124), `tycoon attach motherduck` (#126; `register warehouse --type motherduck` already covers that UX) and the DuckLake doctor checks (#144).
