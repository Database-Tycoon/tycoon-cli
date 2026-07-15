# `tycoon start` / `tycoon stop`

Start and stop background services — Rill dashboards and the Quack warehouse server.

## `tycoon start`

```
tycoon start [OPTIONS]

Options:
  --only TEXT       Only start the named service(s) (rill / quack). Repeatable.
  --skip TEXT       Start everything except the named service(s). Repeatable.
  -h, --help        Show this message and exit
```

By default, `tycoon start` boots both services:

| Service | Port | Started when |
|---|---|---|
| Rill | 9009 | the `rill` binary is on `$PATH` |
| Quack | 9494 | the DuckDB **Quack** extension is available (`core_nightly`) |

Each service runs as a managed subprocess. PIDs are tracked under `.tycoon/run/` so `tycoon stop` finds them.

### Quack — the live, multi-client warehouse (v0.1.9)

When the [DuckDB Quack](https://duckdb.org/quack/) extension is available, `tycoon start` also serves your warehouse over Quack's local RPC protocol on `:9494`. This turns the single-writer DuckDB file into a multi-client server: while the stack is up, `tycoon data query` (and any other local Quack client) reads the **live** warehouse instead of failing on the file lock. It's all on `localhost` — no cloud, no copies.

There's nothing new to learn — it folds into the commands you already run:

- A per-project access token is generated once into `.tycoon/secrets.yml` (gitignored).
- [`tycoon data query`](data/query.md) attaches over Quack automatically when the server is up, and falls back to opening the file directly when it isn't.
- It's skipped silently on machines where the extension can't load (it currently ships only in DuckDB's `core_nightly`).

> **Note:** Quack holds the warehouse file while it's serving. Running a separate writer against the same file — e.g. a standalone `tycoon data transform run` (dbt) in another terminal — will conflict. Stop the stack (`tycoon stop`) before bulk dbt writes. Coordinating dbt automatically is a planned follow-up.

### Start one service

```bash
tycoon start --only rill
tycoon start --only quack
tycoon start --skip quack    # everything except Quack
```

When you only need dashboards, `--only rill` saves a couple of seconds vs. starting everything.

## `tycoon stop`

```
tycoon stop [SERVICES]...

Arguments:
  SERVICES...       Specific server(s) to stop. Defaults to all (rill, quack).
```

Sends SIGTERM to every tracked PID and waits for clean shutdown. If the PID file is missing, it falls back to finding the processes by port.

```bash
tycoon stop                  # all services
tycoon stop rill             # one service
```

## Service detection

`tycoon start` skips services whose underlying tool isn't available:

- **Rill** — needs the `rill` binary on `$PATH` (`curl https://rill.sh | sh`)
- **Quack** — needs the DuckDB Quack extension to be loadable (currently `core_nightly` only)

If a service is missing its dependency, `tycoon start` prints a one-line note and continues with the others.

## Logs

Server output streams into the terminal running `tycoon start` — keep that session visible while debugging.

## Related

- [`tycoon data analyze --rill`](data/analyze.md) — generate dashboards before `tycoon start --only rill`
- [Reference: tycoon.yml `stack` block](../reference/tycoon-yml.md#stack) — what services are scoped
