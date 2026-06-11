# `tycoon notify`

Send a pipeline notification to a Slack or generic webhook. Added in v0.1.9 (#46).

## Why

An unattended `tycoon data run-all` used to print to the terminal and exit — there was no way to know a scheduled run succeeded or failed without watching it. `tycoon notify` (and `tycoon data run-all --notify`) closes that gap. Local-first: it just POSTs JSON to a webhook you configure. No daemon, no cloud.

## Setup

The webhook URL is read from an environment variable so the secret never lands in `tycoon.yml`:

```bash
export TYCOON_NOTIFY_WEBHOOK_URL="https://hooks.slack.com/services/T00/B00/xxxx"
```

- A **Slack** incoming-webhook URL (`hooks.slack.com/...`) gets a colour-coded attachment (green / red / blue by severity).
- Any **other** URL gets a generic JSON envelope: `{source, severity, message, color, fields, label?}`.

Non-secret preferences live in an optional `notify:` block in `tycoon.yml`:

```yaml
notify:
  severities: [success, error]   # which severities --notify emits (default)
  label: "prod refresh"          # optional source label in the payload
```

## Synopsis

```
tycoon notify SEVERITY MESSAGE [OPTIONS]

Arguments:
  SEVERITY   One of: success, error, info
  MESSAGE    Notification body

Options:
  -f, --field key=value   Extra fields to include (repeatable)
  --label TEXT            Override the payload label (default: notify.label)
  -h, --help              Show this message and exit
```

## Examples

```bash
# One-off
tycoon notify success "Daily refresh complete" -f rows=1234 -f elapsed=12.3s
tycoon notify error "Daily refresh failed: connection reset"

# Wired into a pipeline run (opt-in, off by default)
tycoon data run-all --notify
```

`tycoon data run-all --notify` emits a `success` notification when the run completes and an `error` notification (with the failing stage and a message tail) if ingestion or `dbt build` fails. Which severities fire is governed by `notify.severities`. The webhook is best-effort — a notification failure warns but never fails the pipeline.

## Severities

| Severity | Colour | Used for |
|---|---|---|
| `success` | green | pipeline finished — include row counts / elapsed |
| `error` | red | non-zero exit — include stage + error tail |
| `info` | blue | manual `tycoon notify` calls / recipe hooks |

## Out of scope (v1)

PagerDuty / OpsGenie / Discord / email transports, secrets-manager integrations, and anything requiring a running daemon. Webhook + Slack only for now.

## Related

- [`tycoon data run-all`](data/run-all.md) — the `--notify` producer
- [`tycoon schedule`](schedule.md) — schedule a `run-all --notify` to fire unattended
