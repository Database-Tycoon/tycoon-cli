# `tycoon ask`

A natural-language query interface over your warehouse, powered by
[Nao](https://getnao.io). Tycoon scaffolds Nao's config, syncs context
from your warehouse + dbt project, and exposes that context to any
agent (Nao's own chat UI, Claude Code, Cursor, etc.).

!!! info "Optional extra"
    `tycoon ask` requires the `[ask]` extra:
    `pip install 'database-tycoon[ask]'`

## Subcommands at a glance

The `ask` namespace is the **analytics surface**: chat, sync data
context, query exposure. LLM provider configuration lives under
[`tycoon register llm`](../register.md#tycoon-register-llm) (symmetric
with `register dbt` and `register warehouse`).

| Command | What it does |
|---|---|
| `tycoon ask init` | Write `nao_config.yaml` from the active tycoon.yml's `ask.llm` block (project-bootstrap / recovery) |
| `tycoon ask sync` | Run `nao sync` — refresh DB schema + dbt context |
| `tycoon ask chat` | Open the Nao web UI on `:5005` |
| `tycoon ask context [...]` | Cat synced context to stdout (for piping into other agents) |
| `tycoon ask doctor` | Health check (config, dirs, warehouse auth, LLM endpoint) |
| `tycoon ask skills list / new` | Manage Nao skills (named SQL templates with descriptions) |
| `tycoon ask mcp list / add` | Manage MCP server config |

## The 30-second tour

```bash
# Once per project — register the LLM (this writes nao_config.yaml,
# AGENTS.md, scaffolds 8 nao dirs, and offers to pull a model).
tycoon register llm lm-studio
tycoon ask sync                # ~30s first time
tycoon ask doctor              # all green?

# Day-to-day
tycoon ask chat                # web UI
tycoon ask context --table dim_users | claude -p "explain this table"
```

`tycoon init` chains the register-llm step automatically if you pick a
provider in the wizard, so for net-new projects you can usually skip
the explicit `tycoon register llm` call.

## What `tycoon register llm` does

- Writes `ask.llm.provider` in `tycoon.yml` (and any `--base-url` /
  `--model` / `--api-key-env` overrides).
- Generates `.tycoon/nao/nao_config.yaml` from `tycoon.yml`. Translates `database.warehouse: md:my_catalog` to a `path: md:my_catalog` Nao DB entry, applies `ask.include_schemas` / `ask.exclude_schemas` filters, expands the `lm-studio` / `ollama` shortcuts to valid OpenAI-compat configs.
- Writes a default `.tycoon/nao/RULES.md` (or yours, if you set `ask.rules` in `tycoon.yml`).
- Creates **all eight directories** `nao sync` expects: `databases/`, `queries/`, `docs/`, `semantics/`, `repos/`, `agent/{tools,mcps,skills}`. Eliminates the `No such file or directory: 'repos'` crash class.
- Writes `.tycoon/nao/.gitignore` ignoring `databases/`, `repos/`, `db.sqlite*` — the directories that carry PII row-previews and machine-state.
- Writes `AGENTS.md` at the project root pointing coding agents at the synced context tree. Sentinel-marked so re-runs don't stomp user-authored AGENTS.md files.
- For local providers (`lm-studio`, `ollama`), probes the runtime and offers to pull the recommended model (Qwen 2.5 Coder 7B, ~4.7 GB).
- Seeds `ask.exclude_schemas` with conservative noise patterns (`information_schema`, `_tycoon`, `sqlmesh*`) when unset.

## Provider shortcuts

| Provider arg | Expands to |
|---|---|
| `lm-studio` | `provider: openai` + `base_url: http://localhost:1234/v1` + `api_key: lm-studio` (the placeholder is intentional — LM Studio ignores it) |
| `ollama` | `provider: openai` + `base_url: http://localhost:11434/v1` + `api_key: ollama` |
| `openai` | `provider: openai` (set `OPENAI_API_KEY` in your env) |
| `anthropic` | `provider: anthropic` (set `ANTHROPIC_API_KEY`) |
| `gemini` | `provider: gemini` (set `GEMINI_API_KEY`) |
| `mistral` | `provider: mistral` (set `MISTRAL_API_KEY`) |

`lm-studio` is the marquee shortcut: zero-config local LLM without an
account or API key.

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

## `ask init` — bootstrap Nao without re-prompting

Writes `.tycoon/nao/nao_config.yaml` from the active `tycoon.yml`'s
`ask.llm` block. Idempotent. **Doesn't prompt for any LLM details** —
that's [`tycoon register llm`](../register.md#tycoon-register-llm)'s job.

Use when:

- You hand-edited `ask.llm` in `tycoon.yml` (e.g. switched from
  `lm-studio` to `ollama`) and need Nao re-synced.
- You cloned a teammate's tycoon project — `tycoon.yml` ships with the
  team's LLM choice but `.tycoon/nao/` is gitignored, so locally
  there's no Nao config until you bootstrap it.
- A previous `tycoon register llm` succeeded at writing `tycoon.yml`
  but the chained Nao init didn't complete (transient FS error, etc).

```bash
tycoon ask init
# Writes nao_config.yaml + AGENTS.md from current tycoon.yml.

tycoon ask init --force
# Overwrite an existing nao_config.yaml (default skips the write).

tycoon ask init --no-refresh-agents-md
# Skip the AGENTS.md regen — useful if you've hand-edited it.
```

Bails with a clear error when `ask.llm` is absent from `tycoon.yml`:

```
ERROR No ask.llm block in tycoon.yml — run tycoon register llm <provider> first.
```

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

1. **`nao_config.yaml` exists** — fails if `tycoon register llm` (or `tycoon init` with an LLM picked) was never run.
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
