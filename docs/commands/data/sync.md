# `tycoon data sync`

Snapshot one or more cloud DuckDB sources into a single local DuckDB
file. Designed for offline-dev loops where running every query against
prod is slow / fragile / risky.

!!! info "v0.1.4+"
    `tycoon data sync` shipped in v0.1.4. See the
    [release notes](../../releases/v0.1.4.md) for the full design rationale.

## Quick start

```bash
# One-off: snapshot a MotherDuck catalog locally
tycoon data sync --from md:my_catalog --to ./data/snap.duckdb

# Use defaults from tycoon.yml's sync block (most common day-to-day)
tycoon data sync

# Filter what gets copied
tycoon data sync --from md:my_catalog --to ./snap.duckdb \
  --schema mart --tables 'dim_*,fct_*'

# Append rather than replace
tycoon data sync --from md:my_catalog --to ./snap.duckdb --mode append
```

## Synopsis

```
tycoon data sync [OPTIONS]

Options:
  --from TEXT    Source URL — repeatable. md:<catalog>, /path/to/other.duckdb
  --to PATH      Destination DuckDB file. Defaults to tycoon.yml's sync.to
  --schema TEXT  Filter to one schema (applied to every --from source)
  --tables TEXT  Glob filter for table names (e.g. 'mart.*,dim_*')
  --mode TEXT    replace (default) | append | skip-existing
  --help         Show this message and exit
```

## How it works

For each source URL:

1. ATTACH the source `READ_ONLY` to the destination DuckDB connection.
2. List its non-system tables, filtered by `schemas` + `tables` globs.
3. For each table, run the appropriate copy SQL based on `--mode`:
    - `replace` → `CREATE OR REPLACE TABLE schema.table AS SELECT * FROM src`
    - `append` → `INSERT INTO schema.table SELECT * FROM src` (creates if missing)
    - `skip-existing` → only copies tables that don't already exist locally
4. DETACH the source.

System schemas (`information_schema`, `pg_catalog`, `system`) are
**always** excluded regardless of glob filters — they're never useful
in a local snapshot.

Sources are always attached `READ_ONLY`. The sync command will never
mutate the source, even with `--mode append`.

## Modes explained

### `replace` (default)

Drops and recreates every matched table on each sync. The local
snapshot mirrors the source as of the moment of the run. This is the
right mode for the typical "pull a fresh dev baseline" workflow.

```bash
tycoon data sync --from md:prod_catalog --to ./dev.duckdb
```

After running, `./dev.duckdb` is identical to the source for every
table the filters matched.

### `append`

Adds rows on top of the existing destination. Useful for incremental
patterns where the source has only new data since the last sync. There
is **no deduplication** — re-running over the same source will produce
duplicate rows.

```bash
# Daily snapshot, accumulating
tycoon data sync --from md:events_catalog --to ./events.duckdb --mode append
```

If you want incremental-without-duplication, configure a partition
column upstream and filter the source view rather than relying on
this command.

### `skip-existing`

Copies only tables that don't already exist in the destination. Useful
for first-run-only seeding — you can re-run `tycoon data sync
--mode skip-existing` cheaply and it'll only fill in genuinely new
tables.

```bash
# Idempotent seeding
tycoon data sync --from md:my_catalog --to ./snap.duckdb --mode skip-existing
```

## Configuration via `tycoon.yml`

Save the defaults so day-to-day re-syncs are flag-free:

```yaml
sync:
  to: data/local_snapshot.duckdb
  mode: replace
  sources:
    - from: md:dogfood_dlt_prod
      schemas: ['*']
    - from: md:dogfood_dbt_prod
      schemas: ['mart']
      tables: ['dim_*', 'fct_*']
```

Then:

```bash
tycoon data sync             # uses the block above
```

When CLI flags are present, they fully override the config block. The
command warns you if you mix CLI `--from` with a config block (CLI
wins, but you lose per-source filters from the config).

## Filter precedence

When you pass `--schema` and/or `--tables` on the CLI:

- They apply to **every** `--from` source uniformly.
- `--tables` accepts a comma-separated list of fnmatch globs:
  `--tables 'dim_*,fct_*,raw_orders'`.
- For per-source filters, use the `tycoon.yml` `sync.sources[]` block.

## Examples

### Multi-source merge into one destination

```bash
tycoon data sync \
  --from md:dlt_prod \
  --from md:dbt_prod \
  --to ./merged.duckdb
```

If the two sources have non-overlapping schema names, both land cleanly.
If they overlap, `replace` mode means later sources win.

### Cross-test against a known-good baseline

```bash
# Save Sunday's prod state
tycoon data sync --from md:prod --to ./baselines/sunday.duckdb

# ... do dbt development ...

# Compare to baseline
duckdb ./baselines/sunday.duckdb -c "SELECT * FROM mart.fct_orders WHERE id = 12345;"
```

### Local-to-local copy

`--from` accepts any DuckDB-attachable URL, including local files:

```bash
tycoon data sync --from /path/to/another.duckdb --to ./consolidated.duckdb
```

## Errors and exit codes

| Exit | Reason |
|---|---|
| 0 | Sync completed successfully |
| 1 | No `--from` and no `sync.sources` in `tycoon.yml` |
| 1 | No `--to` and no `sync.to` in `tycoon.yml` |
| 1 | Unknown `--mode` value |
| 1 | DuckDB ATTACH failed (auth issue, file missing, etc.) |

The command prints a clear error message to stderr in each case. For
exit-1 due to ATTACH failures, the underlying DuckDB error is included
verbatim — these are usually self-explanatory (e.g. `Conflicting lock
is held` if Rill is currently serving the source file).

## What's deliberately not in v1

Per [issue #12](https://github.com/Database-Tycoon/tycoon-cli/issues/12),
v1 is intentionally narrow:

- **No reverse sync** (local → cloud). One-way only, prevents accidental
  prod mutation.
- **No incremental sync.** v1 is a baseline-snapshot tool, not a replica.
  Watermark-based incremental needs per-table config that's worth its
  own design pass.
- **No catalog rename / remap.** Source schema/table names are mirrored
  into the destination as-is.
- **`md:` and local DuckDB sources only.** Postgres / Snowflake /
  BigQuery follow as their respective DuckDB ATTACH stories settle.

## Related

- [`tycoon data clean`](../index.md#data-pipeline) — wipe the warehouse
  / snapshot file
- [`tycoon doctor`](../index.md#project) — checks `MOTHERDUCK_TOKEN`
  setup
- [Concepts → Two databases, two roles](../../getting-started/concepts.md#2-two-databases-two-roles)
- [Reference → `sync` block](../../reference/tycoon-yml.md#sync)
