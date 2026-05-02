# `tycoon ask`

A natural-language query interface over your warehouse, powered by
[Nao](https://getnao.io). Tycoon scaffolds Nao's config, syncs context
from your warehouse + dbt project, and exposes that context to any
agent (Nao's own chat UI, Claude Code, Cursor, etc.).

!!! info "Optional extra"
    `tycoon ask` requires the `[ask]` extra:
    `pip install 'database-tycoon[ask]'`

## Subcommands at a glance

| Command | What it does |
|---|---|
| `tycoon ask init [--llm <p>]` | Generate config + write AGENTS.md + scaffold 8 nao dirs |
| `tycoon ask sync` | Run `nao sync` — refresh DB schema + dbt context |
| `tycoon ask chat` | Open the Nao web UI on `:5005` |
| `tycoon ask context [...]` | Cat synced context to stdout (for piping into other agents) |
| `tycoon ask doctor` | Health check (config, dirs, warehouse auth, LLM endpoint) |
| `tycoon ask skills list / new` | Manage Nao skills (named SQL templates with descriptions) |
| `tycoon ask mcp list / add` | Manage MCP server config |

## The 30-second tour

```bash
# Once per project
tycoon ask init --llm lm-studio
tycoon ask sync                # ~30s first time
tycoon ask doctor              # all green?

# Day-to-day
tycoon ask chat                # web UI
tycoon ask context --table dim_users | claude -p "explain this table"
```

## What `ask init` actually does

- Generates `.tycoon/nao/nao_config.yaml` from your `tycoon.yml`. Translates `database.warehouse: md:my_catalog` to a `path: md:my_catalog` Nao DB entry, applies `ask.include_schemas` / `ask.exclude_schemas` glob filters, expands the `provider: lm-studio` shortcut to a valid OpenAI-compat config, and so on.
- Writes a default `.tycoon/nao/RULES.md` (or yours, if you set `ask.rules` in `tycoon.yml`).
- Creates **all eight directories** `nao sync` expects: `databases/`, `queries/`, `docs/`, `semantics/`, `repos/`, `agent/{tools,mcps,skills}`. Eliminates the `No such file or directory: 'repos'` crash class.
- Writes `.tycoon/nao/.gitignore` ignoring `databases/`, `repos/`, `db.sqlite*` — the directories that carry PII row-previews and machine-state.
- Writes `AGENTS.md` at the project root pointing coding agents at the synced context tree. Sentinel-marked so re-runs don't stomp user-authored AGENTS.md files.

## The `--llm <provider>` shortcut

`tycoon ask init --llm <provider>` updates `tycoon.yml`'s
`ask.llm.provider` field and regenerates the nao config in one shot.
Six shortcuts:

| `--llm` | Expands to |
|---|---|
| `lm-studio` | `provider: openai` + `base_url: http://localhost:1234/v1` + `api_key: lm-studio` (the placeholder is intentional — LM Studio ignores it) |
| `ollama` | `provider: ollama` |
| `openai` | `provider: openai` |
| `anthropic` | `provider: anthropic` |
| `gemini` | `provider: gemini` |
| `mistral` | `provider: mistral` |

`lm-studio` is the marquee shortcut: zero-config local LLM without an
account or API key. The other shortcuts just record the provider name;
you'll need to set `model` and `api_key_env` in `tycoon.yml` separately
for cloud providers.

## What `ask sync` does

Shells out to `nao sync` after rebinding tycoon's config and
environment. Nao introspects:

- **Your warehouse** — every table in every (filtered) schema. Writes a
  per-table `columns.md` and `preview.md` under
  `.tycoon/nao/databases/type=<engine>/database=<name>/schema=<schema>/table=<table>/`.
- **Your dbt project** — copies `models/**/*.sql` and
  `models/**/*.yml` into `.tycoon/nao/repos/dbt/`.
- **Your skills** — any markdown files under
  `.tycoon/nao/agent/skills/` are loaded as Nao agent skills.

The sync writes are idempotent — re-running just refreshes content.
First sync takes ~30s on a small warehouse; subsequent syncs are
faster.

After `sync`, `tycoon ask` also refreshes `AGENTS.md` so coding agents
that opened the project before the sync see updated paths.

## `ask chat` — the web UI

```bash
tycoon ask chat
# Starting Nao chat at http://localhost:5005
```

Auto-runs `init` and `sync` on first use if needed. Port resolves in
this order: `--port` flag > `tycoon.yml`'s `ask.port` > 5005.

## `ask context` — pipe context anywhere

The cat-command for the synced context. Output is plain markdown on
stdout, errors on stderr — composes cleanly with any other tool:

```bash
tycoon ask context                          # list synced tables
tycoon ask context --table dim_users        # cat columns.md + preview.md
tycoon ask context --schema mart            # all tables in a schema
tycoon ask context --rules-only             # cat RULES.md
tycoon ask context --include-dbt            # also append dbt model SQL

# Pipe into anything
tycoon ask context --table fct_orders | claude -p "what does this track?"
```

The full reference — all flags, exit codes, error paths — is on the
[`ask context`](#) page (lands in Phase 2).

## `ask doctor` — health check

Validates the four most common breakage modes:

1. **`nao_config.yaml` exists** — fails if `ask init` was never run.
2. **All eight required directories exist** — fails if any are missing.
3. **Warehouse auth** — for MotherDuck warehouses, checks `MOTHERDUCK_TOKEN`. Warns (not fails) if unset, since OAuth is also valid.
4. **LLM endpoint reachable** — when `provider: lm-studio` is configured, hits `<base_url>/models` to confirm LM Studio is running. Fails if unreachable.

Renders a Rich `status_table` with one row per check (OK / WARN /
FAIL). Exits non-zero on any FAIL so the command is CI-friendly.

```bash
tycoon ask doctor
# ┃ Component       ┃ Status ┃ Detail                                    ┃
# ┃ nao_config.yaml │ OK     │ /Users/me/proj/.tycoon/nao/nao_config.…  ┃
# ┃ nao directories │ OK     │ all 8 present                            ┃
# ┃ Warehouse       │ OK     │ local DuckDB (no auth)                   ┃
# ┃ LM Studio       │ OK     │ http://localhost:1234/v1 responded (2 …  ┃
```

## `ask skills` and `ask mcp`

For managing Nao's skill markdown files and MCP server config. Use
when you want to:

- Save a known-good SQL pattern as a reusable skill
- Add an MCP server (e.g. Metabase) that the chat UI can call

```bash
tycoon ask skills list
tycoon ask skills new my-monthly-report

tycoon ask mcp list
tycoon ask mcp add metabase
```

The full subcommand reference lands in Phase 2 of the docs.

## Where files live

```
.tycoon/nao/
├── nao_config.yaml             # generated from tycoon.yml (re-runnable)
├── RULES.md                    # project rules for the agent
├── .gitignore                  # auto-generated; PII protection
├── db.sqlite                   # Nao chat history
├── databases/                  # per-table columns.md + preview.md (gitignored)
├── repos/dbt/                  # synced dbt project (gitignored)
├── queries/   docs/   semantics/    # nao sync writes here as needed
└── agent/
    ├── skills/                 # markdown skill files
    ├── mcps/mcp.json           # MCP server config
    └── tools/                  # custom Nao agent tools
```

## Related

- [Concepts → AGENTS.md is a static pointer file](../../getting-started/concepts.md#5-agentsmd-is-a-static-pointer-file)
- [Concepts → The `ask context` cat-command composes with anything](../../getting-started/concepts.md#6-the-ask-context-cat-command-composes-with-anything)
- [Reference → `ask` block](../../reference/tycoon-yml.md#ask)
