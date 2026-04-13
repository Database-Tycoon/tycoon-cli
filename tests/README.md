# tests/

pytest test suite for the tycoon package.

---

## Running Tests

```bash
uv run pytest
```

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
