# `tycoon data run-all`

Ingest all registered sources, then run `dbt build`. The "rebuild everything" command.

## Synopsis

```
tycoon data run-all [OPTIONS]

Options:
  --max-records INTEGER    Cap rows per source (passed to every source's run)
  --skip-dbt               Don't run dbt build after ingest
  --skip-on-error          Continue past failed sources instead of aborting
  -h, --help               Show this message and exit
```

## When to use it

Use cases:

- **First-time setup** — ingest + build in one command after `tycoon init`.
- **Cron-driven refresh** — `0 4 * * * tycoon data run-all` for a daily 4am rebuild.
- **CI smoke test** — combined with `--max-records 10`, exercises the full pipeline cheaply.

For a single source, prefer `tycoon data sources run <name>` + `tycoon data transform run` so you control what re-runs.

## Behavior

For each source in `tycoon.yml`'s `sources:` map:

1. Calls `tycoon data sources run <name>` (with `--max-records` if set).
2. If a source fails:
    - **Default**: aborts immediately.
    - **`--skip-on-error`**: prints the failure and continues to the next source.

After all sources run (or all that survived `--skip-on-error`):

3. Calls `tycoon data transform build` (skipped with `--skip-dbt`).

If `dbt build` fails, the command exits non-zero. Any test failures from `dbt build` show up in `tycoon data history show <invocation_id>`.

## Examples

```bash
# Full rebuild, abort on first error
tycoon data run-all

# Cheap cron-friendly refresh
tycoon data run-all --max-records 1000

# Resilient daily refresh — survive a single flaky source
tycoon data run-all --skip-on-error

# Just the ingest layer (skip dbt)
tycoon data run-all --skip-dbt
```

## What it doesn't do

- **No Rill dashboard refresh as a separate step.** That happens automatically as part of each ingest + dbt run via the observability hooks. After `run-all`, dashboards are current.
- **No source ordering.** Sources run in the order they appear in `tycoon.yml`. There's no inter-source dependency model — that lives in dbt.
- **No retries.** If a source fails and you don't pass `--skip-on-error`, you re-run after fixing.
- **No partial-source selection.** `run-all` runs every source. Use `tycoon data sources run <name>` for targeted runs.

## Observability

Every source ingest and the final `dbt build` are captured into `.tycoon/metadata.duckdb` exactly as if you'd run them individually. `tycoon data history` will show one entry per source plus one for the dbt build.

## Notifications (`--notify`)

For unattended runs, `--notify` posts a webhook notification on completion: `success` when the run finishes, `error` (with the failing stage and a message tail) if ingestion or `dbt build` fails. Set `$TYCOON_NOTIFY_WEBHOOK_URL` first; which severities fire is governed by the `notify.severities` block in `tycoon.yml`. The webhook is best-effort — a notification failure warns but never fails the run. See [`tycoon notify`](../notify.md) for setup and payload shapes.

```bash
export TYCOON_NOTIFY_WEBHOOK_URL="https://hooks.slack.com/services/..."
tycoon data run-all --notify
```

## Related

- [`tycoon data sources run`](sources.md#run-ingest) — single-source ingest
- [`tycoon data transform build`](transform.md#build-run-test-together) — dbt build alone
- [`tycoon data history`](history.md) — review what `run-all` did
- [`tycoon notify`](../notify.md) — the notification surface `--notify` uses
- [`tycoon schedule`](../schedule.md) — run `run-all --notify` on a timer
