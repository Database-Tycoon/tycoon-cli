# `tycoon start` / `tycoon stop`

Start and stop background services — Rill dashboards, Dagster orchestrator, Nao chat UI, and the optional tycoon web UI.

## `tycoon start`

```
tycoon start [OPTIONS]

Options:
  --only TEXT       Start only the named service (rill / dagster / nao / web)
  --no-open         Don't open a browser
  -h, --help        Show this message and exit
```

By default, `tycoon start` boots every service that's relevant to the project (based on `stack` in `tycoon.yml`):

| Service | Port | Started when |
|---|---|---|
| Rill | 9009 | `stack.bi = rill` |
| Dagster | 3000 | `stack.orchestrator = dagster` AND `tycoon[dagster]` extra installed |
| Nao | 5005 | `stack.transformation` set AND `tycoon[ask]` extra installed AND `.tycoon/nao/nao_config.yaml` exists |
| Web UI | 8080 | `tycoon[server]` extra installed |

Each service runs as a managed subprocess. PIDs are tracked under `.tycoon/run/` so `tycoon stop` finds them.

### Start one service

```bash
tycoon start --only rill
tycoon start --only dagster
tycoon start --only nao
tycoon start --only web
```

When you only need dashboards, `--only rill` saves a couple of seconds vs. starting everything.

### Browser auto-open

By default, the first started service opens in your browser. `--no-open` skips this — useful in headless environments.

## `tycoon stop`

```
tycoon stop [OPTIONS]

Options:
  --only TEXT       Stop only the named service
  -h, --help        Show this message and exit
```

Sends SIGTERM to every tracked PID and waits for clean shutdown. Stale PIDs (process already gone) are pruned silently.

```bash
tycoon stop                  # all services
tycoon stop --only rill      # one service
```

## Service detection

`tycoon start` skips services whose underlying tool isn't available:

- **Rill** — needs the `rill` binary on `$PATH` (`curl https://rill.sh | sh`)
- **Dagster** — needs `pip install 'database-tycoon[dagster]'`
- **Nao** — needs `pip install 'database-tycoon[ask]'` AND `tycoon register llm <provider>` to have run
- **Web UI** — needs `pip install 'database-tycoon[server]'`

If a service is missing its dependency, `tycoon start` prints a one-line note and continues with the others.

## Logs

Each service writes to `.tycoon/run/<service>.log`. Tail them while debugging:

```bash
tail -f .tycoon/run/rill.log
tail -f .tycoon/run/dagster.log
tail -f .tycoon/run/nao.log
```

## Related

- [`tycoon ask chat`](ask/index.md#ask-chat-the-web-ui) — direct way to launch just Nao with auto-init
- [`tycoon data analyze --rill`](data/analyze.md) — generate dashboards before `tycoon start --only rill`
- [Reference: tycoon.yml `stack` block](../reference/tycoon-yml.md#stack) — what services are scoped
