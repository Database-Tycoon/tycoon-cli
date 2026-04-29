# `tycoon doctor`

Health check for the tycoon environment — `tycoon.yml` validity, dbt / Rill / Dagster / Nao presence, observability state, and warehouse auth. Use it any time something feels off.

## Synopsis

```
tycoon doctor [OPTIONS]
```

No flags. Just runs a series of checks and prints one panel per check.

## What it checks

The output is a sequence of `Checking ...` panels:

### 1. `tycoon.yml`

Confirms `tycoon.yml` exists in the current directory or a parent. Errors if not — with a hint to run `tycoon init`.

### 2. dbt project

If `stack.transformation = dbt`: confirms `dbt_project_dir` exists and contains `dbt_project.yml`. Reports a clean skip ("dbt: skipped by choice (stack.transformation = none)") if the user opted out of dbt.

### 3. Rill project

If `stack.bi = rill`: confirms `rill_dir` exists. Reports a skip if `bi: none` or a different BI tool is configured.

### 4. Dagster

If the `[dagster]` extra is installed: confirms the `dagster` binary is on `$PATH`. The orchestrator is optional — most projects don't need it.

### 5. Warehouse auth

For DuckDB warehouses: nothing to check (no auth).

For MotherDuck warehouses (`md:<catalog>`): checks for either:

- `MOTHERDUCK_TOKEN` env var, or
- A cached OAuth token (one of `~/.duckdb/stored_tokens`, `~/.duckdb/motherduck_token`, `~/.config/motherduck/token`)

Reports `OK token (env)`, `OK OAuth (cached session)`, or `ERROR not configured`. Recognizing OAuth was added in v0.1.2.

For Snowflake / BigQuery / Redshift: warehouse auth lives in dbt's `profiles.yml` and isn't tycoon's concern. `doctor` skips these.

### 6. Observability

Reports the state of `.tycoon/metadata.duckdb`:

- Not yet created → "metadata DB not yet created" (informational; created on first ingest)
- Empty → "metadata DB present but empty (capture hooks never fired)"
- Populated → `N dlt load(s), M dbt run(s) captured`

Useful when "my dashboards are empty" — usually it means observability hasn't fired yet.

## Exit codes

`tycoon doctor` always exits **0**, even when checks fail. The output is informational; nothing else in tycoon depends on doctor having a clean run.

If you want a CI-style fail-on-error mode, `tycoon ask doctor` is the per-feature equivalent for the AI agent stack and *does* exit non-zero on any FAIL row. For other surfaces, parse the output (`grep ERROR`) or rely on the underlying commands (`tycoon data sources run`, etc.) to fail directly.

## Related

- [`tycoon ask doctor`](ask/index.md#ask-doctor-health-check) — the same shape for the ask stack
- [Concepts → Observability is a side-effect of running](../getting-started/concepts.md#3-observability-is-a-side-effect-of-running)
- [Reference: tycoon.yml](../reference/tycoon-yml.md) — what doctor validates against
