# `tycoon data transform`

Run dbt transformations against the warehouse. Four subcommands wrap the dbt CLI.

| Command | dbt equivalent |
|---|---|
| `tycoon data transform run` | `dbt run` |
| `tycoon data transform test` | `dbt test` |
| `tycoon data transform build` | `dbt build` |
| `tycoon data transform docs` | `dbt docs generate` + `dbt docs serve` |

Every invocation is captured into `.tycoon/metadata.duckdb` (the observability DB) and re-exports the auto-generated `_tycoon_dbt_*` Rill dashboards.

## Why not just use `dbt` directly?

You can — `tycoon run dbt ...` passes through. But `tycoon data transform` adds:

1. **dbt executable resolution** — uses the venv-colocated `dbt` so `pip install database-tycoon[ask]` doesn't shadow your system dbt.
2. **Profile resolution from `tycoon.yml`** — honors `dbt_profiles_dir` / `dbt_profile` / `dbt_target` from `tycoon.register dbt`'s persisted flags. CLI flags still win.
3. **Observability capture** — every run lands in `.tycoon/metadata.duckdb` for `tycoon data history`.
4. **Rill dashboard refresh** — re-exports the dbt-runs Parquet so the `_tycoon_dbt_usage` dashboard stays current.

## Common flags

All four subcommands share these:

```
-t, --target TEXT        dbt target name (dev / prod / ...). Default: tycoon.yml's
                         dbt_target, then dbt's own resolution
-s, --select TEXT        dbt model selection syntax (e.g. 'staging+', 'tag:nightly')
--full-refresh           Drop and recreate incremental models
-h, --help               Show this message and exit
```

## `run` — execute models

```bash
tycoon data transform run                          # all models
tycoon data transform run --select stg_widgets     # one model
tycoon data transform run --select staging+         # one model + descendants
tycoon data transform run --target prod             # specific target
tycoon data transform run --full-refresh            # rebuild incrementals
```

Equivalent to `dbt run` plus tycoon's observability bookkeeping.

## `test` — run dbt tests

```bash
tycoon data transform test                          # all tests
tycoon data transform test --select staging         # tests for a layer
```

Equivalent to `dbt test`. Pass / fail counts surface in `tycoon data history show <invocation_id>`.

## `build` — run + test together

```bash
tycoon data transform build                         # all models + tests
tycoon data transform build --select fct_orders+    # one model + descendants + their tests
```

Equivalent to `dbt build`. The recommended day-to-day command — combines `run` and `test` and stops if any test fails.

## `docs` — generate and serve dbt docs

```bash
tycoon data transform docs                          # default port 8081
tycoon data transform docs --port 9090
```

Wraps `dbt docs generate` followed by `dbt docs serve`. Press Ctrl-C to stop.

## Profile / target resolution

For each invocation, tycoon resolves the dbt CLI args in this order:

| What | Resolution |
|---|---|
| `--target` | CLI flag → `tycoon.yml`'s `dbt_target` → "dev" |
| `--profiles-dir` | `tycoon.yml`'s `dbt_profiles_dir` → `<dbt_project_dir>/profiles.yml` if co-located → none (dbt falls back to `~/.dbt/profiles.yml`) |
| `--profile` | `tycoon.yml`'s `dbt_profile` → none (dbt uses `dbt_project.yml`'s `profile:`) |

`tycoon register dbt --profiles-dir / --profile / --target` writes those keys into `tycoon.yml` so you don't pass them every invocation.

## Observability captured per run

`.tycoon/metadata.duckdb` accumulates one row per invocation in `dbt_runs` (target, version, duration, success counts) and one row per model/test in `dbt_nodes` (status, exec time, rows_affected). v0.1.3+ also captures the manifest fingerprint into `dbt_manifest_snapshots` and a "what changed" diff into `dbt_schema_changes`.

`tycoon data history show <invocation_id>` is the terminal view over all of this.

## Related

- [`tycoon register dbt`](../register.md#tycoon-register-dbt) — set `dbt_target` etc. for transform runs
- [`tycoon data history`](history.md) — drill into a past invocation
- [Reference: Observability tables](../../reference/observability.md) — full schema of `dbt_runs` / `dbt_nodes` / `dbt_manifest_snapshots`
- [Concepts → The CLI is a thin facade over real tools](../../getting-started/concepts.md#4-the-cli-is-a-thin-facade-over-real-tools)
