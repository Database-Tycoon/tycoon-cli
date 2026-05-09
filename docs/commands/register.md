# `tycoon register`

Attach existing dbt, Rill, or warehouse components to a tycoon project. Use these when you already have a dbt project / Rill dashboards / cloud warehouse and want tycoon to orchestrate without scaffolding from scratch.

Three subcommands:

| Command | What it does |
|---|---|
| [`tycoon register dbt`](#tycoon-register-dbt) | Attach an existing dbt project (with profile flags) |
| [`tycoon register rill`](#tycoon-register-rill) | Attach an existing Rill project |
| [`tycoon register warehouse`](#tycoon-register-warehouse) | Switch warehouse type (DuckDB / MotherDuck) |

All three commands edit `tycoon.yml` in place and update `stack.<component>_managed` to `false` so tycoon stays out of the way of the existing project.

---

## `tycoon register dbt`

Attach an existing dbt project. Local path or GitHub URL.

### Synopsis

```
tycoon register dbt [OPTIONS] [SOURCE]

Arguments:
  [SOURCE]  Local path or GitHub URL of an existing dbt project.
            Required unless --create is set (in which case it overrides
            the default sibling path).

Options:
  --create               Bootstrap a new dbt project at ../<project>-dbt
                         (or [SOURCE] if given), wired to the active tycoon
                         warehouse, then register it
  --profiles-dir PATH    Directory containing profiles.yml (default:
                         <SOURCE>/profiles.yml, then ~/.dbt/profiles.yml)
  --profile NAME         Profile name within profiles.yml (default:
                         dbt_project.yml's `profile:` field)
  --target NAME          Target within the profile (default: profile's
                         `target:` field, then 'dev')
  --no-attach-metadata   Skip wiring `.tycoon/metadata.duckdb` into the
                         registered profile as `tycoon_meta`
  -h, --help             Show this message and exit
```

### Examples

```bash
# Register a sibling dbt project
tycoon register dbt ../my-existing-dbt-project

# Register from GitHub (clones into a sibling dir)
tycoon register dbt https://github.com/me/my-dbt-project

# Bootstrap a new dbt project (recovery path if you skipped dbt during
# `tycoon init` — sibling repo at ../<project>-dbt, profile points at
# whatever DuckDB/MotherDuck the tycoon project already uses)
tycoon register dbt --create

# Same, with an explicit location
tycoon register dbt --create ./dbt_project

# With non-default profile resolution
tycoon register dbt ../my-dbt \
  --profiles-dir ~/.config/dbt \
  --profile production_profile \
  --target prod
```

### `--create`: bootstrap a new dbt project

If you picked **Skip** on the dbt prompt during `tycoon init`, `--create`
is the recovery path. It writes a fresh `dbt_project.yml` + `profiles.yml`
(plus the standard `models/`, `analyses/`, etc. layout) at the target
location, then runs the same registration flow as if you'd handed it an
existing project.

The generated profile points at the same warehouse paths recorded in
`tycoon.yml`'s `database` block, so `tycoon data transform run` works
immediately without further configuration.

**Limitations:**

- DuckDB and MotherDuck warehouses only. For Snowflake/BigQuery, hand-author
  `dbt_project.yml` + `profiles.yml` and use plain `tycoon register dbt <path>` —
  the warehouse-alignment step picks up the cloud adapter from there.
- Refuses to overwrite an existing `dbt_project.yml`. If the target directory
  already has one, register it directly (drop the `--create` flag).
- Marks `stack.transformation_managed: true` (tycoon owns the project,
  same as the init wizard's "Create new" option). Plain
  `tycoon register dbt <path>` keeps `transformation_managed: false`.

### Profile resolution

The three profile flags (`--profiles-dir`, `--profile`, `--target`) mirror dbt's own CLI options. They control:

1. **Which `profiles.yml` to read.** The flag wins, then `<SOURCE>/profiles.yml` if co-located, then `~/.dbt/profiles.yml`.
2. **Which profile within that file.** The flag wins, then `dbt_project.yml`'s `profile:` field.
3. **Which target within the profile.** The flag wins, then the profile's `target:` field, then `"dev"`.

Anything you pass on the CLI is **persisted in `tycoon.yml`** under `dbt_profiles_dir` / `dbt_profile` / `dbt_target` so subsequent `tycoon data transform` runs reuse it automatically. Re-running `register dbt` without a flag clears the persisted value.

### Warehouse alignment

After resolving the dbt target, `register dbt` reads the adapter type and offers to align tycoon's `stack.warehouse` accordingly:

- **dbt-duckdb** → tycoon adopts the same `path:` (local DuckDB or `md:<catalog>` for MotherDuck)
- **dbt-snowflake / dbt-bigquery / dbt-redshift** → tycoon updates `stack.warehouse` to match the adapter type. `database.warehouse` (only meaningful for DuckDB / MotherDuck) is left alone for cloud adapters.

Snowflake registration also surfaces an account-mismatch warning if `tycoon.yml`'s `warehouse_connection.account` was previously recorded as a different value.

### `register dbt` writes

`tycoon.yml` gains:

```yaml
dbt_project_dir: ../my-dbt
dbt_profiles_dir: /path/to/profiles      # only if --profiles-dir was passed
dbt_profile: my_profile                   # only if --profile was passed
dbt_target: prod                          # only if --target was passed
stack:
  transformation: dbt
  transformation_managed: false
```

---

## `tycoon register rill`

Attach an existing Rill project. Local path or GitHub URL.

### Synopsis

```
tycoon register rill [OPTIONS] SOURCE

Arguments:
  SOURCE  Local path or GitHub URL of the Rill project to register
```

### Example

```bash
tycoon register rill ../my-dashboards
```

`register rill` validates that the source contains `rill.yaml` and updates `tycoon.yml`:

```yaml
rill_dir: ../my-dashboards
stack:
  bi: rill
  bi_managed: false
```

---

## `tycoon register warehouse`

Switch the warehouse type — local DuckDB ↔ MotherDuck — without re-running `init`.

### Synopsis

```
tycoon register warehouse [OPTIONS]

Options:
  --type TEXT       Warehouse type — 'duckdb' (or 'local') / 'motherduck' (or 'cloud')
  --path TEXT       For --type duckdb: local file path (default: data/warehouse.duckdb)
  --catalog TEXT    For --type motherduck: catalog name (becomes md:<catalog>)
  --no-prompt       Fail rather than prompt — for CI
  --force           Overwrite an existing warehouse without prompting
```

### Examples

```bash
# Interactive (prompts for everything)
tycoon register warehouse

# Non-interactive — fully scriptable
tycoon register warehouse --type motherduck --catalog my_catalog --no-prompt
tycoon register warehouse --type duckdb --path ./data/warehouse.duckdb --no-prompt

# Force-overwrite an existing warehouse setting
tycoon register warehouse --type motherduck --catalog new_catalog --force --no-prompt
```

### Behavior matrix

| `--type` set | Type-specific value set | `--no-prompt` | Result |
|---|---|---|---|
| ✓ | ✓ | any | No prompts (CI mode) |
| ✓ | — | absent | Prompts for the value |
| ✓ | — | `--no-prompt` | Fails fast |
| — | — | absent | Prompts for everything (default) |
| — | — | `--no-prompt` | Fails fast — `--type` is required |

### MotherDuck auth

When you set warehouse to `md:<catalog>`, `register warehouse` warns if `MOTHERDUCK_TOKEN` is not in the environment. It doesn't fail — OAuth is also valid (run `motherduck connect` once) and `tycoon doctor` will recognize either path.

---

## `tycoon register llm`

Wire tycoon's AI analytics agent up to an LLM provider. Symmetric with `register dbt` and `register warehouse` — one external resource, recorded in `tycoon.yml`, all setup chained off the registration call.

```bash
# Register a provider (writes tycoon.yml + nao_config.yaml +
# AGENTS.md, seeds exclude_schemas, offers model install).
tycoon register llm lm-studio

# No-arg form refreshes the existing setup against tycoon.yml — use
# this after editing the file by hand.
tycoon register llm

# Opt out of the post-register install offer (useful for scripts).
tycoon register llm ollama --skip-install
```

### Provider choices

| Provider | Local? | Notes |
|---|---|---|
| `lm-studio` | yes | OpenAI-compat at `http://localhost:1234/v1`. Recommended local option. |
| `ollama` | yes | OpenAI-compat at `http://localhost:11434/v1`. CLI-friendly. |
| `openai` | cloud | needs `OPENAI_API_KEY` |
| `anthropic` | cloud | needs `ANTHROPIC_API_KEY` |
| `gemini` | cloud | needs `GEMINI_API_KEY` |
| `mistral` | cloud | needs `MISTRAL_API_KEY` |

### What gets written

- `ask.llm` block in `tycoon.yml` (provider + optional model / base_url / api_key_env overrides)
- `.tycoon/nao/nao_config.yaml` — Nao runtime config
- `.tycoon/nao/{databases,queries,docs,semantics,repos,agent/{tools,mcps,skills}}/` — eight directories Nao expects
- `.tycoon/nao/RULES.md` — project rules surfaced to the agent
- `.tycoon/nao/.gitignore` — keeps PII previews + sync state out of git
- `AGENTS.md` at the project root — sentinel-marked pointer for coding agents
- `ask.exclude_schemas` seeded with conservative noise patterns (DuckDB internals, `_tycoon`, `sqlmesh*`) when unset

### Local model install

After registering LM Studio or Ollama, `register llm` probes the runtime and routes based on what it finds:

| State | LM Studio response | Ollama response |
|---|---|---|
| Reachable + ≥1 model loaded | "ready" message, no prompt | "ready" message, no prompt |
| Reachable + 0 loaded but ≥1 chat model **downloaded** | **Prompts to `lms load <model>`** — the auto-load offer (v0.1.5+). Hits in 5-30s, then chat is ready. Falls back to GUI hint if `lms` isn't on PATH or user declines. | (Ollama auto-loads on first request, so this state only matters if you genuinely have nothing pulled — see next row.) |
| Reachable + nothing downloaded | Prints LM Studio GUI download hint (Discover tab → search → download → load) | Prompts to `ollama pull qwen2.5-coder:7b` (~4.7 GB) |
| Unreachable | Warns + prints start-the-server hint; `tycoon.yml` already saved | Same |

The recommended model is the same across both runtimes: **Qwen 2.5 Coder 7B Instruct (Q4_K_M, ~4.7 GB)**. The auto-load offer prefers it when it's downloaded; otherwise picks the first chat-capable model (embeddings filtered out). See [Recipe: LM Studio local LLM](../recipes/lm-studio-local-llm.md) for the rationale.

The same auto-load offer fires from `tycoon ask chat` when you launch chat against a cold LM Studio — no need to switch back to `register llm`.

### Flags

```
--base-url     URL    Override the OpenAI-compat base URL (e.g. for an LM
                      Studio server on a non-default port).
--model        TEXT   Pin a specific model name; otherwise the runtime picks.
--api-key-env  TEXT   Env var holding the API key for cloud providers
                      (e.g. OPENAI_API_KEY). Ignored for local providers.
--skip-install        Skip the post-register model install offer.
```

### Auto-detection in `tycoon init`

If you skip the explicit `register llm` call and run `tycoon init`, the wizard probes the same ports and offers a one-keystroke "Detected Ollama running locally — use it? [Y/n]" confirm. Picking a provider in the wizard chains the same setup automatically.

---

## Related

- [Reference: tycoon.yml](../reference/tycoon-yml.md#stack) — `stack` block schema
- [Concepts → The CLI is a thin facade over real tools](../getting-started/concepts.md#4-the-cli-is-a-thin-facade-over-real-tools)
- [Issue #18](https://github.com/Database-Tycoon/tycoon-cli/issues/18) — register dbt profile flags (closed in v0.1.4)
- [Issue #19](https://github.com/Database-Tycoon/tycoon-cli/issues/19) — register warehouse flags (closed in v0.1.4)
