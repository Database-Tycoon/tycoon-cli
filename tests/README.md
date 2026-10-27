# tests/

pytest test suite for the tycoon package.

---

## Running Tests

```bash
uv run pytest
```

### Recipe doctests (markdown blocks executed as subprocesses)

`tests/test_recipe_doctests.py` walks `README.md` and `docs/recipes/*.md` for marked code blocks and executes each via `bash -e -o pipefail`. The marker convention:

```markdown
<!-- tycoon-test: mode=offline -->
```bash
tycoon init --template csv-import --name demo
tycoon data sources run files
```

- `mode=offline` (default): runs on every PR via `ci.yml`. Must work without network or credentials.
- `mode=online`: runs only via `nightly-e2e.yml` (or `uv run pytest --run-online`). Real upstream APIs allowed.

Each block runs in a fresh `tmp_path` with `HOME` rebound, so caches don't leak into the dev environment. The block's commands run literally — there's no substitution layer.

Why subprocess? In-process Typer tests can't see PATH resolution, Rich rendering (the v0.1.6 `[extra]` bracket strip bug), stdout/stderr framing, or console-script wiring. The recipe harness + `test_e2e_demo_arc.py` close that gap.

### Real MotherDuck tests (scratch databases)

Tests that need a real MotherDuck catalog use the `motherduck_scratch_db` fixture from `tests/motherduck_scratch.py` (re-exported by `conftest.py`). With `MOTHERDUCK_TOKEN` set it creates `tycoon_e2e_scratch_<hex>`, yields its `md:` URL and drops it in a `finally` block. Without the token the test skips.

Mark such tests `e2e`, so they stay out of the default run, and put `motherduck` in the file or test name: the `motherduck-e2e` job in `e2e.yml` selects them with `pytest -m e2e -k motherduck`.

Maintainer setup for the `motherduck-e2e` job. Repository settings cannot be changed from a PR, so none of this exists until a maintainer does it, and the workflow is not safe to dispatch before then:

1. Create an environment named `motherduck-e2e` (Settings, Environments) before the first run. GitHub creates an unprotected environment if the name does not exist yet.
2. Restrict its deployment branches to `main` and `v*`, and optionally require a reviewer. `workflow_dispatch` runs the workflow file from whichever ref the dispatcher picks, so without the branch restriction anyone with write access can push a branch that prints the token and dispatch it.
3. Store the token as an environment secret named `MOTHERDUCK_TOKEN`, not a repository secret, so jobs outside the environment never see it.
4. Use a dedicated MotherDuck account or service-account token that cannot see any real catalog.

The job passes the token to the pytest step only. A cancelled or timed-out run skips the fixture's cleanup, so the same step then runs `python -m tests.motherduck_scratch`, which drops scratch databases older than 24 hours (by `md_information_schema.databases.created_ts`) through the same name check.

Safety rule: the helper refuses to create, alter or drop any database whose name does not start with `tycoon_e2e_scratch_` (`tests/test_motherduck_scratch.py` proves it, no token needed). Never point a test at a real catalog; use the fixture and drop the database it hands you.

### Snapshot tests for Rich CLI output

`tests/test_snapshots.py` uses [syrupy](https://github.com/syrupy-project/syrupy) to pin the exact rendered string of user-facing Rich output — install hints, doctor rows, common error paths. Golden files live in `tests/__snapshots__/test_snapshots.ambr`.

When a maintainer intentionally changes a user-facing string, regenerate the snapshot:

```bash
uv run pytest --snapshot-update tests/test_snapshots.py
git diff tests/__snapshots__/        # review the diff
```

A regression (someone re-introduces the `[extra]` bracket strip; someone changes a doctor row text without updating snapshots) fails the snapshot assertion with a clear diff. Reviewers see the change in PRs as a plain-text diff — much better signal than "a test broke and the maintainer rewrote the assertion."



Run a specific file:

```bash
uv run pytest tests/test_cli.py
```

Run with verbose output:

```bash
uv run pytest -v
```

---

## Test Coverage

| File | What It Tests |
|---|---|
| `test_cli.py` | CLI entrypoint, command registration, help output |
| `test_config.py` | Path resolution, project root detection, config loading |
| `test_project.py` | Pydantic model parsing and validation for `tycoon.yml` |
| `test_ingestion.py` | dlt pipeline runner, source loading, ingestion execution |
| `test_sources.py` | Catalog fetching, source install/remove, source manager state |
| `test_init.py` | Project scaffolding — directory structure and file generation |
| `test_check.py` | Project validation checks (config, dbt state, source connectivity) |
| `test_db_command.py` | DuckDB shell command invocation |
| `test_analyze.py` | dbt staging model and Rill dashboard scaffolding |
| `test_services.py` | Shared service layer (dbt runner, duckdb client) |
| `test_server.py` | FastAPI server routes and responses |
| `test_utils.py` | Shared utility functions |
| `test_constants.py` | Package constant values |
| `test_status.py` | Source freshness, last sync time, and row count display |
| `test_run_all.py` | Full pipeline run — ingest all sources then dbt build |
| `conftest.py` | Shared fixtures (temp project directories, mock configs) |

---

## Workflow Scenarios

These five scenarios represent the most common user journeys. Each maps to one or more test files and serves as the basis for integration-level test coverage.

---

### Scenario 1 — Greenfield First-Time Setup

A user with no existing data stack runs tycoon for the first time.

**Steps:**
```
tycoon init
tycoon data sources add rest_api
tycoon data sources run <name>
tycoon data transform run
tycoon data status
```

**Success conditions:**
- `tycoon.yml` is created with correct structure
- Source is registered under `sources:` in the config
- dlt pipeline runs without error and writes to `data/raw.duckdb`
- dbt build exits 0
- `tycoon data status` shows the source with a green freshness label and non-zero row count

**Test files:** `test_init.py`, `test_sources.py`, `test_ingestion.py`, `test_status.py`

---

### Scenario 2 — Daily Pipeline Refresh

A user with an existing project re-ingests all sources and rebuilds dbt models.

**Steps:**
```
tycoon data run-all
tycoon data status
```

**Success conditions:**
- All registered sources are ingested in sequence
- dbt build runs after ingestion completes
- `tycoon data status` reflects updated `Last Sync` timestamps
- `--skip-ingest` and `--skip-transform` flags correctly bypass each phase
- `--max-records` cap is applied to each source

**Test files:** `test_run_all.py`, `test_status.py`

---

### Scenario 3 — Add a New Source to an Existing Project

A user with a running project adds a second data source.

**Steps:**
```
tycoon data sources catalog
tycoon data sources add <type>          # registers source, auto-installs via dlt init
tycoon data sources run <name>
tycoon data analyze <name>              # scaffolds dbt staging models + Rill dashboard
```

**Success conditions:**
- Catalog lists all available source types
- `add` appends the new source to `tycoon.yml` without overwriting existing sources
- Ingestion for the new source writes to the correct schema
- `analyze` scaffolds dbt staging models and a Rill dashboard definition for the new source

**Test files:** `test_sources.py`, `test_ingestion.py`, `test_analyze.py`

---

### Scenario 4 — Environment Health Check and Debugging

A user troubleshoots a broken environment or investigates data quality issues.

**Steps:**
```
tycoon doctor
tycoon data status
tycoon data db query "SELECT count(*) FROM raw_github.issues"
```

**Success conditions:**
- `doctor` reports missing binaries, missing `tycoon.yml`, and uninstalled sources as warnings (not crashes)
- `tycoon data status` gracefully handles a missing or empty database (shows "never" / "—")
- `db query` executes SQL and returns results, or exits cleanly with an error message on bad SQL

**Test files:** `test_cli.py`, `test_status.py`, `test_db_command.py`

---

### Scenario 5 — Launch Dashboards and Services

A user starts the local service stack for exploration and then shuts it down.

**Steps:**
```
tycoon start --only rill
# or
tycoon start
tycoon stop
```

**Success conditions:**
- `--only rill` starts only the Rill process; other services are not launched
- Missing optional services (nao, dagster) are skipped with a warning, not a crash
- `tycoon stop` terminates all running managed processes
- Port conflicts are detected and reported before launch

**Test files:** `test_services.py`, `test_cli.py`
