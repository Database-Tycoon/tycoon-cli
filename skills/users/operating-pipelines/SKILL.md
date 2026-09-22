---
name: operating-pipelines
description: Use when running a tycoon project unattended or operating it day to day — scheduling recurring pipeline runs (cron/launchd/systemd), webhook notifications on success or failure, one-command full refreshes, snapshotting a cloud warehouse to a local DuckDB file for offline work, or resetting local databases without losing run history.
license: MIT
compatibility: Requires the tycoon CLI (pip install database-tycoon) inside a tycoon project (tycoon.yml present)
metadata:
  author: database-tycoon
  tier: users
---

# Operating pipelines

## One-command refresh

```bash
tycoon data run-all [-n N] [--skip-ingest | --skip-transform] [-t TARGET] [--notify]
```

Ingests every source, then `dbt build`. Default target is `dev`. **Profile
caveat:** `run-all` only looks for `profiles.yml` inside the dbt project
directory — if your profile lives in `~/.dbt`, use the two explicit steps
instead (see the diagnosing-projects skill).

## Scheduling (launchd on macOS, systemd-user on Linux)

```bash
tycoon schedule add nightly --command "data run-all" --at 06:00 --notify
tycoon schedule list
tycoon schedule status nightly [-n LINES]   # installed? + log tail
tycoon schedule remove nightly
```

- `--cadence daily` (default, at `--at`) | `hourly` (at `--at`'s minute) |
  `weekly` (`--weekday 1..7`, 1=Mon).
- `--notify` appends `--notify` to the scheduled command; `--force` replaces
  an existing schedule of the same name.
- These are OS-level user timers — they run without a terminal but only
  while the machine is awake and the user is logged in.

## Notifications

The webhook URL comes from the **`$TYCOON_NOTIFY_WEBHOOK_URL`** env var —
nothing fires without it. Slack incoming-webhook URLs get a colored
attachment; any other URL gets a generic JSON envelope.

```bash
tycoon notify success "backfill done" -f rows=1200 --label prod
tycoon notify error "ingest failed"            # severities: success|error|info
```

`tycoon.yml`'s `notify:` block filters which severities send and sets a
default label. `data run-all --notify` wires the same surface into pipeline
runs automatically.

## Cloud → local snapshots (offline work)

```bash
tycoon data sync --from md:my_catalog --to data/offline.duckdb \
  --schema marts --tables 'fct_*' --mode replace
```

- `--from` is repeatable: `md:<catalog>` (MotherDuck) or a path to another
  `.duckdb` file. Defaults come from `tycoon.yml`'s `sync:` block, so a bare
  `tycoon data sync` works once that's configured.
- `--mode`: `replace` (default) | `append` | `skip-existing`.

## Resetting local data

```bash
tycoon data clean --all        # raw + warehouse files (asks to confirm)
```

Run history in `.tycoon/metadata.duckdb` is **preserved by default, even
with `--all`** — `data history` and observability dashboards survive routine
resets. Pass `--metadata` only when you truly want history gone. Selective:
`--raw` / `--local` remove one database (and its WAL) each.
