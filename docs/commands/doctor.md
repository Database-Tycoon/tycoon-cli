# `tycoon doctor`

Health check for the tycoon environment — `tycoon.yml` validity, dbt / Rill presence, observability state, and warehouse auth. Use it any time something feels off.

## Synopsis

```
tycoon doctor [OPTIONS]

Options:
  --fix       Attempt to repair fixable problems. Currently: when the Python
              interpreter is out of range, build a project-local `.venv` on a
              supported interpreter (via uv) for you to activate.
  -h, --help  Show this message and exit.
```

Runs a series of checks and prints one panel per check. With `--fix`, doctor also attempts to repair the problems it knows how to fix (see [below](#fixing-problems-fix)).

## What it checks

The output is a sequence of `Checking ...` panels:

### 1. Python interpreter (v0.1.9)

Confirms the interpreter running tycoon is within the supported range, **`>=3.12,<3.14`** (mirrors `requires-python` in `pyproject.toml`).

- `OK Python 3.13 is in the supported range (>=3.12,<3.14).`
- `ERROR Python 3.11 is too old. ... tycoon setup --python 3.12.`
- `ERROR Python 3.14 is too new for tycoon's dbt stack (dbt-core / dbt-duckdb have no 3.14 wheels yet) ... tycoon setup --python 3.13.`

This is the first check because tycoon runs dbt out of the *same* interpreter it lives in (it resolves dbt at `Path(sys.executable).parent / "dbt"`). A too-new interpreter — notably 3.14, which has no dbt wheels — otherwise fails far from its cause, at `tycoon data transform run`, which is exactly how [#55](https://github.com/Database-Tycoon/tycoon-cli/issues/55) stayed invisible. Surfacing the mismatch here makes it the first thing you see. Environment-level, so it runs even without a `tycoon.yml`. When this check fails, [`tycoon doctor --fix`](#fixing-problems-fix) (or [`tycoon setup`](setup.md)) builds a corrected `.venv`.

### 2. Project environment

Reports whether this project has its own `.venv` (built by [`tycoon init`](init.md) or [`tycoon setup`](setup.md)), and whether tycoon is actually running from it, not just whether a `.venv` directory happens to exist:

- `OK Project environment: using its own .venv at <path>.` tycoon is running from this project's own `.venv`.
- `WARN Project environment: <path> exists, but tycoon is running from <other path> instead. Activate it with ... or run it directly with ....` The `.venv` has tycoon installed in it, but tycoon isn't executing from it, so a catalog source resolved against that `.venv`'s project-local directory can fail "not installed" with no earlier warning.
- `WARN Project environment: <path> works but has no tycoon in it, so tycoon runs from <other path>. That's the shared/tool model, which still works. To run tycoon from this project's .venv instead, run uv add database-tycoon here. ...` The `.venv` is a working environment (it has a `pyvenv.cfg` and its Python interpreter is still there), but tycoon is installed somewhere else, such as a uv tool. Nothing needs fixing. If you want tycoon in the project, `uv add database-tycoon` adds it to `pyproject.toml` and installs it into the existing `.venv` without rebuilding it. tycoon pins exact dbt, dlt and duckdb versions, so this can move those packages in your project. Without a `pyproject.toml`, the suggestion is `uv pip install --python <path> database-tycoon` instead.
- `WARN Project environment: <path> exists, but tycoon is running from <other path> instead, and <path> has no tycoon installed in it (empty or broken). Run tycoon setup --force to rebuild it.` The `.venv` can't run Python: it's an empty directory, a plain file, or a venv whose interpreter was removed. A failed or partial setup usually leaves it in this state.
- `WARN Project environment: this project doesn't have its own .venv yet ... Run tycoon setup to build one.` No `.venv` at all, so tycoon falls back to the older shared/ambient environment model.

Only runs when a `tycoon.yml` is present. Purely informational either way: doesn't affect doctor's overall pass/fail.

### 3. `tycoon.yml`

Confirms `tycoon.yml` exists in the current directory or a parent. Errors if not — with a hint to run `tycoon init`.

### 4. dbt project

If `stack.transformation = dbt`: confirms `dbt_project_dir` exists and contains `dbt_project.yml`. Reports a clean skip ("dbt: skipped by choice (stack.transformation = none)") if the user opted out of dbt.

### 5. Rill project

If `stack.bi = rill`: confirms `rill_dir` exists. Reports a skip if `bi: none` or a different BI tool is configured.

### 6. Warehouse auth

For DuckDB warehouses: nothing to check (no auth).

For MotherDuck warehouses (`md:<catalog>`): checks for either:

- `MOTHERDUCK_TOKEN` env var, or
- A cached OAuth token (one of `~/.duckdb/stored_tokens`, `~/.duckdb/motherduck_token`, `~/.config/motherduck/token`)

Reports `OK token (env)`, `OK OAuth (cached session)`, or `ERROR not configured`. Recognizing OAuth was added in v0.1.2.

For Snowflake / BigQuery / Redshift: warehouse auth lives in dbt's `profiles.yml` and isn't tycoon's concern. `doctor` skips these.

### 7. Layer coverage (v0.1.7)

When `stack.transformation = dbt` and a compiled dbt manifest exists, doctor verifies that every registered source in `tycoon.yml` has at least one staging model:

- `OK Layer coverage: every source (N) has at least one staging model.` — every dlt source has a `stg_*<source>*` model in the manifest.
- `WARN Layer coverage: no staging model found for source(s): X, Y. Scaffold with tycoon data analyze <source>...` — at least one source is uncovered.

Silently skipped when `transformation: none` or when the manifest hasn't been compiled yet (the dbt-project and observability rows already nudge the user to compile).

See [layered architecture](../recipes/layered-architecture.md) for the underlying classification rules.

### 8. Observability

Reports the state of `.tycoon/metadata.duckdb`:

- Not yet created → "metadata DB not yet created" (informational; created on first ingest)
- Empty → "metadata DB present but empty (capture hooks never fired)"
- Populated → `N dlt load(s), M dbt run(s) captured`

Useful when "my dashboards are empty" — usually it means observability hasn't fired yet.

## Fixing problems (`--fix`)

`tycoon doctor --fix` runs all the checks, then attempts to repair the ones it knows how to fix. Today that's the **Python interpreter** check:

- The running interpreter can't be swapped under tycoon's own feet, so the repair is to build a project-local `.venv` on a supported interpreter via `uv sync` and pin it with `.python-version`, the same flow as [`tycoon setup`](setup.md). Requires a `tycoon.yml` in the current directory, same as `setup`. You then `source .venv/bin/activate` and re-run.
- If `uv` isn't installed, `--fix` can't proceed and prints the one-line installer instead of running it.
- When the interpreter is already in range, `--fix` is a no-op.

`--fix` never lowers the bar: an unfixable check still reports its error.

## Exit codes

`tycoon doctor` always exits **0**, even when checks fail. The output is informational; nothing else in tycoon depends on doctor having a clean run.

If you want a CI-style fail-on-error mode, parse the output (`grep ERROR`) or rely on the underlying commands (`tycoon data sources run`, etc.) to fail directly.

## Related

- [Concepts → Observability is a side-effect of running](../getting-started/concepts.md#3-observability-is-a-side-effect-of-running)
- [Reference: tycoon.yml](../reference/tycoon-yml.md) — what doctor validates against
