# All commands and options

Every tycoon command on one scrollable page, with every flag. For
worked examples and rationale, follow the per-command page link in
each section header.

!!! tip "Conventions"
    - `[OPTIONS]` brackets mark optional flags
    - `<NAME>` (angle brackets) mark required values
    - Every command supports `-h` / `--help`

---

## Project

### [`tycoon init`](../commands/init.md)

```
tycoon init [OPTIONS]

Options:
  -t, --template TEXT      Template to scaffold from (csv-import,
                           nyc-transit)
  -n, --name TEXT          Project name (default: current directory name)
  --list-templates         List available templates and exit
  -p, --param TEXT         Template parameter in 'name=value' form (repeatable)
```

### [`tycoon register dbt`](../commands/register.md#tycoon-register-dbt)

```
tycoon register dbt [OPTIONS] SOURCE

Arguments:
  SOURCE                   Local path or GitHub URL of the dbt project

Options:
  --profiles-dir PATH      Directory containing profiles.yml
                           (default: <SOURCE>/profiles.yml, then ~/.dbt/profiles.yml)
  --profile NAME           Profile name within profiles.yml
                           (default: dbt_project.yml's `profile:` field)
  --target NAME            Target within the profile (default: profile's `target:`, then 'dev')
  --no-attach-metadata     Skip wiring `.tycoon/metadata.duckdb` as `tycoon_meta`
                           into the registered profile
```

### [`tycoon register rill`](../commands/register.md#tycoon-register-rill)

```
tycoon register rill [OPTIONS] SOURCE

Arguments:
  SOURCE                   Local path or GitHub URL of the Rill project
```

### [`tycoon register warehouse`](../commands/register.md#tycoon-register-warehouse)

```
tycoon register warehouse [OPTIONS]

Options:
  --type TEXT              duckdb / motherduck (or local / cloud / md aliases)
  --path TEXT              For --type duckdb: local file path
                           (default: data/warehouse.duckdb)
  --catalog TEXT           For --type motherduck: catalog name (becomes md:<NAME>)
  --no-prompt              Fail rather than prompt — for CI
  --force                  Overwrite an existing warehouse without prompting
```

### [`tycoon register llm`](../commands/register.md#tycoon-register-llm)

```
tycoon register llm [PROVIDER] [OPTIONS]

Arguments:
  PROVIDER                 lm-studio / ollama / openai / anthropic / gemini /
                           mistral. Omit to refresh setup against existing
                           ask.llm.provider.

Options:
  --base-url TEXT          Override the OpenAI-compat base URL
  --model TEXT             Pin a specific model name
  --api-key-env TEXT       Env var holding the API key (cloud providers)
  --skip-install           Skip the post-register model install offer
```

### [`tycoon doctor`](../commands/doctor.md)

```
tycoon doctor [OPTIONS]
```

No flags. Runs every check and prints one panel per check.

### [`tycoon docs serve`](../commands/docs.md)

```
tycoon docs serve [OPTIONS]

Options:
  -p, --port INTEGER       Port (default: 8000)
  --host TEXT              Bind interface (default: 127.0.0.1)
  --no-open                Don't try to open a browser
```

### [`tycoon docs build`](../commands/docs.md)

```
tycoon docs build [OPTIONS]

Options:
  --strict                 Fail on warnings (broken links, missing pages, etc.)
```

---

## Data pipeline

### [`tycoon data sources catalog`](../commands/data/sources.md#catalog-browse-available-source-types)

```
tycoon data sources catalog
```

No flags. Prints the catalog of available source types.

### [`tycoon data sources add`](../commands/data/sources.md#add-register-a-new-source)

```
tycoon data sources add [SOURCE_TYPE]

Arguments:
  [SOURCE_TYPE]            Source type — run 'tycoon data sources catalog'
                           to see all options. Prompts if not passed.
```

### [`tycoon data sources list`](../commands/data/sources.md#list-list-registered-sources)

```
tycoon data sources list
```

### [`tycoon data sources show`](../commands/data/sources.md#list-list-registered-sources)

```
tycoon data sources show NAME

Arguments:
  NAME                     Source name to drill into
```

### [`tycoon data sources run`](../commands/data/sources.md#run-ingest)

```
tycoon data sources run [SOURCE_NAME] [OPTIONS]

Arguments:
  [SOURCE_NAME]            Source to run (default: all)

Options:
  --max-records INTEGER    Cap rows per resource (cheap test runs)
```

### [`tycoon data sources remove`](../commands/data/sources.md#remove-unregister-a-source)

```
tycoon data sources remove NAME

Arguments:
  NAME                     Source to remove
```

### [`tycoon data transform run`](../commands/data/transform.md#run-execute-models)

```
tycoon data transform run [OPTIONS]

Options:
  -t, --target TEXT        dbt target (default: tycoon.yml's dbt_target, then 'dev')
  -s, --select TEXT        dbt model selection (e.g. 'staging+', 'tag:nightly')
  --full-refresh           Drop and recreate incremental models
```

### [`tycoon data transform test`](../commands/data/transform.md#test-run-dbt-tests)

```
tycoon data transform test [OPTIONS]

Options:
  -t, --target TEXT
  -s, --select TEXT
```

### [`tycoon data transform build`](../commands/data/transform.md#build-run-test-together)

```
tycoon data transform build [OPTIONS]

Options:
  -t, --target TEXT
  -s, --select TEXT
  --full-refresh
```

### [`tycoon data transform docs`](../commands/data/transform.md#docs-generate-and-serve-dbt-docs)

```
tycoon data transform docs [OPTIONS]

Options:
  -t, --target TEXT
  --port INTEGER           Port for dbt docs serve (default: 8081)
```

### [`tycoon data sync`](../commands/data/sync.md)

```
tycoon data sync [OPTIONS]

Options:
  --from TEXT              Source URL (repeatable). md:<catalog> or local .duckdb
  --to PATH                Destination DuckDB file (default: tycoon.yml's sync.to)
  --schema TEXT            Filter to one schema (applied to every --from source)
  --tables TEXT            Glob filter for table names (e.g. 'mart.*,dim_*')
  --mode TEXT              replace (default) | append | skip-existing
```

### [`tycoon data query`](../commands/data/query.md#query-read-only-sql)

```
tycoon data query SQL [OPTIONS]

Arguments:
  SQL                      SQL query (read-only by default)

Options:
  --db PATH                Override which DuckDB to query (default: warehouse)
  --source NAME            Query a source's raw schema
```

### [`tycoon data schema`](../commands/data/query.md#schema-dump-tables-row-counts-sizes)

```
tycoon data schema [SCHEMA] [OPTIONS]

Arguments:
  [SCHEMA]                 Optional schema filter

Options:
  --db PATH                Override which DuckDB to inspect
```

### [`tycoon data clean`](../commands/data/query.md#clean-remove-warehouse-files)

```
tycoon data clean [OPTIONS]

Options:
  --all                    Also remove rill/tmp, dbt target/, dbt_packages/, logs/
  --metadata               Remove .tycoon/metadata.duckdb
                           (preserved by default, even with --all)
```

### [`tycoon data history`](../commands/data/history.md)

```
tycoon data history [OPTIONS]

Options:
  --tool TEXT              Filter to dlt or dbt (default: both)
  --limit INTEGER          Number of recent runs (default: 10)
```

### [`tycoon data history show`](../commands/data/history.md#show-id-drill-into-one-run)

```
tycoon data history show ID

Arguments:
  ID                       Load id (dlt) or invocation id (dbt). Short prefix OK.
```

### [`tycoon data status`](../commands/data/status.md)

```
tycoon data status
```

No flags. Per-source freshness, row counts, and capture history.

### [`tycoon data analyze`](../commands/data/analyze.md)

```
tycoon data analyze SOURCE [OPTIONS]

Arguments:
  SOURCE                   Name of a registered source

Options:
  --no-dbt                 Don't generate dbt staging models
  --rill                   Also generate Rill source / metrics_view / dashboard YAMLs
```

### [`tycoon data run-all`](../commands/data/run-all.md)

```
tycoon data run-all [OPTIONS]

Options:
  --max-records INTEGER    Cap rows per source
  --skip-dbt               Don't run dbt build after ingest
  --skip-on-error          Continue past failed sources
```

### `tycoon data observability scaffold`

```
tycoon data observability scaffold [OPTIONS]

Options:
  --no-attach              Skip the profiles.yml ATTACH wiring
  --no-models              Skip the staging-model generation
```

Generates `dbt_project/models/_tycoon/` (nine `stg_tycoon__*` views + `dim_runs` mart) and ATTACHes `.tycoon/metadata.duckdb` as `tycoon_meta` in the dbt profile. Idempotent.

---

## AI agent

LLM provider configuration lives under `tycoon register llm` (see the
Project section above). The `tycoon ask` namespace is reserved for
analytics endpoints — chat, sync data context, query exposure.

### [`tycoon ask sync`](../commands/ask/index.md#what-ask-sync-does)

```
tycoon ask sync [OPTIONS]

Options:
  --reinit                 Regenerate nao_config.yaml before syncing
```

### [`tycoon ask chat`](../commands/ask/index.md#ask-chat-the-web-ui)

```
tycoon ask chat [OPTIONS]

Options:
  --port INTEGER           Port override (default: tycoon.yml's ask.port, then 5005)
```

### [`tycoon ask context`](../commands/ask/index.md#ask-context-pipe-context-anywhere)

```
tycoon ask context [OPTIONS]

Options:
  -t, --table TEXT         Filter to a single table name
  -s, --schema TEXT        Filter to a single schema name
  --include-dbt            Also dump synced dbt model SQL
  --rules-only             Only print RULES.md
```

### [`tycoon ask doctor`](../commands/ask/index.md#ask-doctor-health-check)

```
tycoon ask doctor
```

No flags. Renders OK / WARN / FAIL panel per check. Exits non-zero on any FAIL.

### `tycoon ask skills list / new`

```
tycoon ask skills list

tycoon ask skills new NAME

Arguments:
  NAME                     Skill name (used as filename and frontmatter name)
```

### `tycoon ask mcp list / add`

```
tycoon ask mcp list

tycoon ask mcp add SERVER

Arguments:
  SERVER                   MCP server name to add (currently: metabase)
```

---

## Services

### [`tycoon start`](../commands/start.md)

```
tycoon start [OPTIONS]

Options:
  --only TEXT              Start only the named service: rill, dagster, nao, web
  --no-open                Don't open a browser
```

### [`tycoon stop`](../commands/start.md#tycoon-stop)

```
tycoon stop [OPTIONS]

Options:
  --only TEXT              Stop only the named service
```

---

## Tools

### [`tycoon run`](../commands/run.md)

```
tycoon run TOOL [TOOL_ARGS...]

Tools:
  dlt                      The dlt CLI
  dbt                      The dbt CLI
  rill                     The Rill CLI
  dagster                  The Dagster CLI
  nao                      The Nao CLI (when [ask] extra is installed)
  duckdb                   The DuckDB CLI (when installed externally)
```

All arguments after `TOOL` are forwarded verbatim. tycoon does not interpret them.

---

## Top-level

### `tycoon --version`

```
tycoon --version
tycoon -V
```

Print version and exit.

### `tycoon -h` / `--help`

Show help. Works at every level:

```bash
tycoon -h
tycoon data -h
tycoon data sync -h
tycoon ask doctor -h
```
