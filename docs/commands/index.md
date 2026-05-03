# Commands

Every command tycoon ships, organized by section. Click into any
command for full reference.

## Project

| Command | What it does |
|---|---|
| `tycoon init` | Scaffold a new project from a template |
| `tycoon register dbt <path>` | Attach an existing dbt project to `tycoon.yml` |
| `tycoon register rill <path>` | Attach an existing Rill project |
| `tycoon register warehouse` | Switch the warehouse (DuckDB / MotherDuck) |
| `tycoon doctor` | Check the environment for issues |

## Data pipeline

| Command | What it does |
|---|---|
| `tycoon data sources add` | Register a new source interactively |
| `tycoon data sources catalog` | Browse available source types |
| `tycoon data sources list` | List registered sources |
| `tycoon data sources run [name]` | Ingest one source (or all) |
| `tycoon data sources remove <name>` | Remove a registered source |
| `tycoon data transform run` | dbt run |
| `tycoon data transform test` | dbt test |
| `tycoon data transform build` | dbt build |
| **[`tycoon data sync`](data/sync.md)** | **Cloud → local DuckDB snapshots (v0.1.4+)** |
| `tycoon data query <sql>` | Query the warehouse |
| `tycoon data schema [schema]` | Dump schema info |
| `tycoon data history` | Recent dlt + dbt runs |
| `tycoon data history show <id>` | Drill into one run |
| `tycoon data status` | Source freshness + capture counts |
| `tycoon data analyze <source>` | Scaffold dbt staging + (optional) Rill dashboards |
| `tycoon data run-all` | Ingest all sources, then `dbt build` |
| `tycoon data clean` | Remove warehouse files (preserves observability metadata by default) |

## AI analytics ([`tycoon ask`](ask/index.md))

LLM provider configuration lives under `tycoon register llm` — see
[Register](register.md). `tycoon ask` is reserved for analytics
endpoints.

| Command | What it does |
|---|---|
| `tycoon register llm <provider>` | Configure an LLM, write `nao_config.yaml`, scaffold dirs, offer model install |
| `tycoon ask sync` | Run `nao sync` — refresh DB + dbt context |
| `tycoon ask chat` | Open the Nao web UI |
| `tycoon ask context` | Cat synced context to stdout for piping into agents |
| `tycoon ask doctor` | Health check for the ask stack |
| `tycoon ask skills list/new` | Manage Nao skills |
| `tycoon ask mcp list/add` | Manage MCP servers |

## Services

| Command | What it does |
|---|---|
| `tycoon start` | Start Rill, Dagster, Nao, web UI |
| `tycoon start --only <svc>` | Start one specific service |
| `tycoon stop` | Stop all services |

## Tool passthrough

| Command | What it does |
|---|---|
| `tycoon run dlt ...` | Pass through to dlt CLI |
| `tycoon run dbt ...` | Pass through to dbt CLI |
| `tycoon run rill ...` | Pass through to Rill CLI |
| `tycoon run dagster ...` | Pass through to Dagster CLI |

## Help anywhere

Every command supports `--help`:

```bash
tycoon data sync --help
tycoon register llm --help
tycoon doctor --help
```

## Documented in detail

The pages below are in-depth references with examples and edge cases.
Other commands are documented inline via `--help`.

- [`tycoon data sync`](data/sync.md) — cloud-→-local snapshots
- [`tycoon ask`](ask/index.md) — the AI agent surface

More command pages land in the next docs phase.
