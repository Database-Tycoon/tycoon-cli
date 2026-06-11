# `tycoon schedule`

Run a tycoon command on a timer using the platform-native scheduler — macOS **launchd**, Linux **systemd --user**. Local-first: no daemon, no cloud. Added in v0.1.9 (#48).

## Why

Once `tycoon data run-all` works, the next question is "how do I run this every morning?" Instead of hand-writing cron / launchd / systemd units, `tycoon schedule` wraps them in one command.

## Synopsis

```
tycoon schedule add NAME [OPTIONS]
tycoon schedule list
tycoon schedule remove NAME
tycoon schedule status NAME [-n LINES]
```

### `add` options

| Option | Default | Meaning |
|---|---|---|
| `-c, --command` | `data run-all` | The tycoon command to run (quote it: `"data run-all --notify"`) |
| `--at HH:MM` | `04:00` | Time of day (24h) |
| `--cadence` | `daily` | `daily` (at `--at`), `hourly` (at `--at`'s minute), or `weekly` |
| `--weekday` | `1` | Weekly cadence: 1=Mon … 7=Sun |
| `--notify` | off | Append `--notify` to the scheduled command |
| `--force` | off | Replace an existing schedule of the same name |

## Examples

```bash
# Daily refresh at 4am, with a Slack/webhook ping on completion
tycoon schedule add daily-refresh --command "data run-all" --at 04:00 --notify

# Every hour at :15
tycoon schedule add hourly-sync --command "data sources run github" --cadence hourly --at 00:15

# Mondays at 6am
tycoon schedule add weekly-rollup --command "data run-all" --cadence weekly --weekday 1 --at 06:00

tycoon schedule list
tycoon schedule status daily-refresh      # installed? + tail the run log
tycoon schedule remove daily-refresh       # unloads + deletes the unit files
```

## Where things live

| Platform | Unit file | Scheduler |
|---|---|---|
| macOS | `~/Library/LaunchAgents/com.databasetycoon.<name>.plist` | `launchctl load` |
| Linux | `~/.config/systemd/user/tycoon-<name>.{timer,service}` | `systemctl --user enable --now` |

Each scheduled run appends stdout/stderr to `~/.local/share/tycoon/schedule/<name>/run.log`; `tycoon schedule status` tails it. The scheduled command runs with its working directory set to your project root, so `tycoon.yml` resolves.

`tycoon doctor` reports the count of installed schedules.

## Windows

Not supported in v1. `tycoon schedule add` prints a clear message pointing you at Task Scheduler to run the equivalent `tycoon <command>`.

## Out of scope (v1)

- Distributed / cloud schedulers, anything needing a running tycoon daemon.
- Full cron expressions — start with `--at` + `--cadence daily/hourly/weekly`.
- Retry / auto-pause policies — a failed run is logged; the next run still fires.

## Related

- [`tycoon data run-all`](data/run-all.md) — the usual thing to schedule
- [`tycoon notify`](notify.md) — pair with `--notify` so scheduled runs report in
