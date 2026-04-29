# Recipe: MotherDuck cloud + local snapshot

Use MotherDuck as the production warehouse, sync it locally for offline dev. The pattern that motivated `tycoon data sync` (issue #12).

## Why this setup

Three problems running every dev query against prod:

1. **Slow** — every query is a network round-trip
2. **Fragile** — upstream pipeline staleness silently blocks downstream tools
3. **Risky** — easy to accidentally mutate prod when the token's exported

A frozen local snapshot solves all three: dev queries are instant, the data is a known-good baseline immune to prod drift, and the snapshot is read-only no matter what the token has access to.

## Setup

### 1. Authenticate with MotherDuck

Either token-based:

```bash
export MOTHERDUCK_TOKEN=<your-token>     # get one at https://app.motherduck.com/token
```

Or OAuth (browser-based, recognized by `tycoon doctor` since v0.1.2):

```bash
motherduck connect
```

### 2. Initialize the project pointing at MotherDuck

```bash
mkdir cloud-demo && cd cloud-demo
tycoon init --template csv-import --name cloud-demo
tycoon register warehouse --type motherduck --catalog cloud_demo_prod --no-prompt
```

This sets `tycoon.yml`'s `database.warehouse: md:cloud_demo_prod` and `stack.warehouse: motherduck`.

For a fresh MotherDuck catalog, you'd typically create it from the MotherDuck UI or via `CREATE DATABASE cloud_demo_prod` from a DuckDB shell — tycoon doesn't create empty MotherDuck catalogs for you.

### 3. Verify

```bash
tycoon doctor
```

You should see `MotherDuck auth OK token (env)` (or `OAuth (cached session)`).

## Day-to-day: the sync pattern

### Configure default sources in `tycoon.yml`

```yaml
sync:
  to: data/local_snapshot.duckdb
  sources:
    - from: md:cloud_demo_prod
      schemas: ['mart']               # only mart schemas — staging is too churn-y
      tables: ['dim_*', 'fct_*']
```

Now `tycoon data sync` (no flags) snapshots prod into `data/local_snapshot.duckdb`.

### Pull a fresh dev baseline

```bash
tycoon data sync                       # uses the block above
```

Output:

```
> Syncing 1 source(s) → data/local_snapshot.duckdb (mode: replace)
  mart.dim_users        12,453 rows from md:cloud_demo_prod
  mart.fct_orders     1,205,331 rows from md:cloud_demo_prod
  mart.dim_products      4,210 rows from md:cloud_demo_prod
OK Synced 1,221,994 rows across 3 table(s) to data/local_snapshot.duckdb
```

### Use the snapshot for dev queries

For ad-hoc SQL, just point `--db` at the snapshot:

```bash
tycoon data query --db data/local_snapshot.duckdb \
  "SELECT count(*) FROM mart.fct_orders WHERE order_date >= '2026-01-01'"
```

For dbt dev, point your dev target at the snapshot. In `dbt_project/profiles.yml`:

```yaml
cloud_demo:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: data/local_snapshot.duckdb
    prod:
      type: duckdb
      path: md:cloud_demo_prod
      token: "{{ env_var('MOTHERDUCK_TOKEN') }}"
```

Then:

```bash
tycoon data transform run --target dev      # against snapshot, fast
tycoon data transform run --target prod     # against MotherDuck, when ready
```

You can also persist the dev/prod target choice in `tycoon.yml`:

```bash
tycoon register dbt ./dbt_project --target dev
```

This sets `dbt_target: dev` in `tycoon.yml`, so subsequent `tycoon data transform run` invocations default to dev (snapshot) without `--target`.

### When to re-sync

Re-run `tycoon data sync` whenever you want a fresh baseline. Some patterns:

- **Daily**: cron `0 7 * * * tycoon data sync` for an "as-of-this-morning" snapshot
- **On demand**: when the snapshot's gone stale enough to mislead you
- **Per-feature**: re-sync at the start of each new analytical question

The snapshot is intentionally allowed to go stale until you re-sync — that's the whole value prop.

## Sync mode cheat-sheet

```bash
tycoon data sync                                        # replace (default)
tycoon data sync --mode skip-existing                   # only fill in NEW tables
tycoon data sync --mode append                          # accumulate (no dedup!)
tycoon data sync --schema mart --tables 'dim_*'         # narrow filter
tycoon data sync --from md:other_catalog --to ./snap2.duckdb   # one-off sync to a different file
```

## Limits to know about

- **Pull-only**: there's no `tycoon data sync --reverse` for local → cloud. Deliberate, prevents accidental prod mutation. Use dlt or your existing prod pipeline for that direction.
- **Full replace per table**: no incremental sync in v1. Re-sync re-copies every matched table.
- **`md:` and local DuckDB only** for sources today. Snowflake / BigQuery / Postgres come later.
- **DuckLake catalogs**: only the `READ_ONLY` ATTACH path is verified. SQLite-backed DuckLake catalogs hold an exclusive lock that conflicts with concurrent Rill — see [Rill 0.86 architecture in the v0.1.3 release notes](../releases/v0.1.3.md).

## Related

- [`tycoon data sync`](../commands/data/sync.md) — full reference
- [`tycoon register warehouse`](../commands/register.md#tycoon-register-warehouse) — for the cloud setup step
- [Reference: tycoon.yml `sync` block](../reference/tycoon-yml.md#sync)
- [Issue #12](https://github.com/Database-Tycoon/tycoon-cli/issues/12) — original design doc
