# `tycoon data run-all`

Ingest all registered sources, then run `dbt build`. The "rebuild everything" command.

## Synopsis

```
tycoon data run-all [OPTIONS]

Options:
  -n, --max-records INTEGER  Cap records fetched per resource (useful for testing)
  --skip-ingest              Skip ingestion and only run dbt build
  --skip-transform           Skip dbt build and only run ingestion
  -t, --target TEXT          dbt target profile  [default: dev]
  --notify                   Send a webhook notification on completion (success/failure)
  --fail-on-empty            Fail when a local glob matches no files or a replace load brings in zero rows
  -h, --help                 Show this message and exit
```

## When to use it

Use cases:

- **First-time setup** — ingest + build in one command after `tycoon init`.
- **Cron-driven refresh** — `0 4 * * * tycoon data run-all` for a daily 4am rebuild.
- **CI smoke test** — combined with `--max-records 10`, exercises the full pipeline cheaply.

For a single source, prefer `tycoon data sources run <name>` + `tycoon data transform run` so you control what re-runs.

## Behavior

For each source in `tycoon.yml`'s `sources:` map:

1. Runs the same ingest as `tycoon data sources run <name>` (with `--max-records` if set).
2. If a source fails, the command stops there and exits 1. Sources after it don't run, and neither does `dbt build`.

After every source has run:

3. Runs `dbt build` against `--target` (skipped with `--skip-transform`). `--skip-ingest` skips step 1 and only builds.

With `--fail-on-empty`, a source whose local glob matches no files, or that loads zero rows with `replace`, counts as a failed source, so the command exits 1 before `dbt build` runs. See [`tycoon data sources run`](sources.md#run-ingest) for the details.

If `dbt build` fails, the command exits non-zero. Any test failures from `dbt build` show up in `tycoon data history show <invocation_id>`.

## Examples

```bash
# Full rebuild, abort on first error
tycoon data run-all

# Cheap cron-friendly refresh
tycoon data run-all --max-records 1000

# Just the ingest layer (skip dbt)
tycoon data run-all --skip-transform

# Just dbt build
tycoon data run-all --skip-ingest
```

## What it doesn't do

- **No Rill dashboard refresh as a separate step.** That happens automatically as part of each ingest + dbt run via the observability hooks. After `run-all`, dashboards are current.
- **No source ordering.** Sources run in the order they appear in `tycoon.yml`. There's no inter-source dependency model — that lives in dbt.
- **No retries, and no skipping a failed source.** If a source fails, fix it and re-run.
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
