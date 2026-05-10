# `tycoon.yml` reference

Every key in the project's config file, with defaults and worked
examples.

## Minimal example

```yaml
name: my-project
version: 0.1.0
database:
  raw: data/raw.duckdb
  warehouse: data/warehouse.duckdb
sources: {}
```

Anything not declared falls back to the defaults below.

## Top-level keys

| Key | Type | Default | Notes |
|---|---|---|---|
| `name` | string | `my-project` | Used in dlt pipeline names + Nao project name |
| `version` | string | `0.1.0` | Project's own version, free-form |
| `database` | block | see below | Where data lives |
| `sources` | map[name → source] | `{}` | Registered ingestion sources |
| `dbt_project_dir` | string | `dbt_project` | Path to dbt project root |
| `dbt_profiles_dir` | string | unset | Override the `profiles.yml` directory. See [dbt profiles](#dbt-profiles) below. |
| `dbt_profile` | string | unset | Profile name within `profiles.yml`. Defaults to the `profile:` field in `dbt_project.yml`. |
| `dbt_target` | string | unset | Target within the profile (`dev` / `prod` / ...). Defaults to the profile's own `target:`, then `dev`. |
| `rill_dir` | string | `rill` | Path to Rill project dir |
| `ask` | block | unset | AI agent (Nao) configuration |
| `sync` | block | unset | `tycoon data sync` defaults |
| `stack` | block | see below | Tool-by-tool stack toggle |

## `database`

```yaml
database:
  raw: data/raw.duckdb              # where dlt writes
  warehouse: data/warehouse.duckdb  # where dbt writes (or md:catalog)
```

| Key | Type | Default | Notes |
|---|---|---|---|
| `raw` | string | `data/raw.duckdb` | Always a local DuckDB file. Don't point at MotherDuck — dlt manages this. |
| `warehouse` | string | `data/warehouse.duckdb` | Local file or `md:<catalog>` for MotherDuck. |

For Snowflake / BigQuery / Redshift warehouses, the `warehouse` field
isn't load-bearing — dbt resolves the connection from
`dbt_project/profiles.yml`. Use `stack.warehouse: snowflake` (etc.) to
tell tycoon what kind of warehouse it's looking at.

## `sources`

A map keyed by source name. Each source is a block declaring its type
and config:

```yaml
sources:
  files:
    type: filesystem
    schema: raw_files
    config:
      bucket_url: data/input
      file_glob: "*.csv"

  github:
    type: rest_api
    schema: raw_github
    config:
      base_url: https://api.github.com
      datasets: [repos, issues, pulls]
```

| Key | Type | Default | Notes |
|---|---|---|---|
| `type` | string | (required) | Source type: `filesystem`, `rest_api`, `sql_database`, or any catalog source |
| `schema` | string | `raw_<name>` | Target schema name in the raw DB |
| `config` | dict | `{}` | Type-specific config passed through to dlt |
| `tables` | list[string] | unset | Optional table-name list (for `sql_database` and similar) |
| `dbt_package` | string | unset | Optional dbt package to install when this source is registered |

Source types not in `tycoon data sources catalog` need to be installed
via `tycoon data sources add <type>` first (it runs `dlt init`
under the hood and stages the source files in `~/.tycoon/sources/`).

## `ask`

Configures the AI agent (Nao). Optional — omitted when the `[ask]`
extra isn't installed.

```yaml
ask:
  llm:
    provider: lm-studio
    model: qwen2.5-coder-32b-instruct
  port: 5005
  include_schemas: [mart]
  exclude_schemas: [pg_catalog]
  rules: |
    Custom RULES.md content for the agent.
```

| Key | Type | Default | Notes |
|---|---|---|---|
| `llm` | block | unset | LLM provider config. See below. |
| `port` | int | `5005` | Port for `tycoon ask chat` web UI |
| `rules` | string | unset | Override the default RULES.md content |
| `include_schemas` | list[string] | `[]` | Glob filter — only these schemas exposed to Nao |
| `exclude_schemas` | list[string] | `[]` | Glob filter — these schemas hidden from Nao |
| `skills_dir` | string | `.tycoon/nao/agent/skills` | Custom path to skills folder |

### `ask.llm`

```yaml
ask:
  llm:
    provider: lm-studio              # shortcut → expands to OpenAI-compat
    base_url: http://localhost:1234/v1   # optional override
    model: qwen2.5-coder-32b-instruct    # optional override
    api_key_env: ANTHROPIC_API_KEY       # for cloud providers
```

| Key | Type | Default | Notes |
|---|---|---|---|
| `provider` | string | `openai` | Provider shortcut. `lm-studio` expands to OpenAI-compat at localhost:1234 with a placeholder api_key. Other shortcuts: `openai`, `anthropic`, `ollama`, `gemini`, `mistral`. |
| `model` | string | (provider default) | Override model name |
| `base_url` | string | (provider default) | OpenAI-compatible base URL — set automatically when `provider: lm-studio` |
| `api_key_env` | string | unset | Env var name (e.g. `ANTHROPIC_API_KEY`) holding the key. Tycoon writes `{{ env('VAR_NAME') }}` into nao_config.yaml so the key isn't committed. |

`tycoon register llm <provider>` is the easiest way to set the
provider shortcut from the command line; it edits this block in place
and runs the post-register setup (nao_config.yaml, AGENTS.md, model
install offer for local providers).

## `sync`

Configures defaults for `tycoon data sync` (cloud → local snapshots).
Optional.

```yaml
sync:
  to: data/local_snapshot.duckdb
  mode: replace
  sources:
    - from: md:my_catalog
      schemas: ['mart']
      tables: ['dim_*', 'fct_*']
    - from: md:another_catalog
      schemas: ['*']
```

| Key | Type | Default | Notes |
|---|---|---|---|
| `to` | string | `data/local_snapshot.duckdb` | Default destination DuckDB file |
| `mode` | string | `replace` | `replace` / `append` / `skip-existing` |
| `sources` | list[block] | `[]` | One block per remote source. Each carries its own filter globs. |

### `sync.sources[]`

```yaml
- from: md:my_catalog
  schemas: ['mart', 'staging']
  tables: ['*']
```

| Key | Type | Default | Notes |
|---|---|---|---|
| `from` | string | (required) | DuckDB-attachable URL: `md:<catalog>` for MotherDuck, `/path/to/other.duckdb` for a local file |
| `schemas` | list[string] | `["*"]` | fnmatch globs — which schemas to include |
| `tables` | list[string] | `["*"]` | fnmatch globs — which tables within selected schemas |

## `stack`

Tells tycoon which tools you use. Drives `tycoon doctor` checks,
`tycoon start` services, and template scaffolding.

```yaml
stack:
  ingestion: dlt
  ingestion_managed: true
  warehouse: duckdb               # or motherduck, snowflake, bigquery, redshift, other
  transformation: dbt
  transformation_managed: true    # tycoon scaffolds + manages this
  bi: rill                        # or metabase, looker, tableau, other, none
  bi_managed: true
  orchestrator: dagster           # or airflow, prefect, other, none
  orchestrator_managed: true
```

| Key | Type | Default | Notes |
|---|---|---|---|
| `ingestion` | enum | `dlt` | `dlt`, `airbyte`, `fivetran`, `meltano`, `none` |
| `warehouse` | enum | `duckdb` | `duckdb`, `motherduck`, `snowflake`, `bigquery`, `redshift`, `other` |
| `transformation` | enum | `dbt` | `dbt`, `none` |
| `bi` | enum | `rill` | `rill`, `metabase`, `looker`, `tableau`, `other`, `none` |
| `orchestrator` | enum | `dagster` | `dagster`, `airflow`, `prefect`, `other`, `none` |
| `<tool>_managed` | bool | `true` | If `true`, tycoon scaffolds + maintains this tool's project. If `false`, tycoon just records the path and stays out of the way. |

Setting any tool to `none` skips its scaffolding and `tycoon doctor`
checks. Setting `_managed: false` is for "I have my own dbt project
already, just point at it" workflows — used by `tycoon register dbt`
and friends.

## Environment variable interpolation

Any string value can reference an environment variable with `${VAR}`
syntax:

```yaml
sources:
  github:
    type: rest_api
    schema: raw_github
    config:
      base_url: https://api.github.com
      access_token: ${GITHUB_TOKEN}
```

Tycoon expands these at config-load time. Unexpanded `${VAR}` in any
field that gets passed to dlt produces a clear warning before the API
call ("Config key 'access_token' contains an unexpanded env var:
${GITHUB_TOKEN}").

## dbt profiles

Tycoon resolves a dbt profile every time it shells out to `dbt build` /
`dbt test` / `dbt docs` / `dbt run`. Resolution order matches dbt's own
CLI so anything that works for `dbt --profiles-dir foo` works for
`tycoon ... --profiles-dir foo`:

1. CLI flag — `--profiles-dir`, `--profile`, `--target` on
   `tycoon data transform run/test/build/docs` and `tycoon profiles
   list/show/doctor`.
2. `tycoon.yml` — `dbt_profiles_dir`, `dbt_profile`, `dbt_target`.
3. `<dbt_project_dir>/profiles.yml` (dbt 1.5+ co-located file).
4. `$DBT_PROFILES_DIR` env var.
5. `~/.dbt/profiles.yml` (dbt's default).

You generally don't need to touch any of the `tycoon.yml` fields —
co-located + `~/.dbt` covers most setups. Set `dbt_profiles_dir` only
when your profile lives somewhere unusual (e.g. you keep it under
version control in a separate `config/` directory).

Inspect what tycoon will use:

```bash
tycoon profiles list      # every profile + targets + adapters; flags the active one
tycoon profiles show      # pretty-print the active profile, secrets redacted
tycoon profiles doctor    # verify resolution + adapter matches stack.warehouse
```

`tycoon doctor` includes the `profiles doctor` check too, so you'll
catch a duckdb-vs-snowflake adapter mismatch before a `dbt build` does.

## `transform`

```yaml
transform:
  auto_scaffold: true             # default
  auto_osi_scaffold: false        # default — opt in once you're happy with OSI scaffolds
```

| Key | Type | Default | Notes |
|---|---|---|---|
| `auto_scaffold` | bool | `true` | After `tycoon data sources run <name>`, automatically run `tycoon data analyze` if no staging models exist for that source yet. |
| `auto_osi_scaffold` | bool | `false` | After a successful `tycoon data transform run/build`, auto-emit `dbt_project/semantic/osi.yaml` via `tycoon semantics scaffold`. Best-effort — never breaks the underlying transform on failure. See [the `tycoon semantics` docs](../commands/semantics.md). |

## Things that aren't in `tycoon.yml`

- **Secrets** — keep them in `.env` or your shell environment, then
  reference via `${VAR}` interpolation. Tycoon never asks you to put
  raw tokens in `tycoon.yml`.
- **Per-machine paths** — anything that varies between dev machines
  belongs outside the file. The defaults assume `./data`, `./dbt_project`,
  `./rill` relative to the project root, which works on every machine.
- **Run history** — that lives in `.tycoon/metadata.duckdb` (auto-gitignored
  in scaffolded projects).
- **Nao chat history** — `.tycoon/nao/db.sqlite`, also auto-gitignored.
