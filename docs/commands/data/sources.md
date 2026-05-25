# `tycoon data sources`

Manage data ingestion sources. Five subcommands.

| Command | What it does |
|---|---|
| `tycoon data sources catalog` | Browse available source types |
| `tycoon data sources add [TYPE]` | Register a new source (interactive) |
| `tycoon data sources list` | List sources registered in this project |
| `tycoon data sources run [NAME]` | Ingest one source (or all) |
| `tycoon data sources remove NAME` | Remove a registered source |

## `catalog` — browse available source types

Lists every source type tycoon knows how to ingest, with the dlt resources it ships:

```bash
tycoon data sources catalog
```

Output:

```
                        Source Catalog
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Type       ┃ Category        ┃ Description              ┃ Tables             ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ github     │ Developer Tools │ Issues, PRs, commits     │ issues, ...        │
│ slack      │ Communication   │ Channels, users, ...     │ channels, ...      │
│ stripe     │ Payments        │ Customers, ...           │ customers, ...     │
│ rest_api   │ Generic         │ Any REST API             │ pokemon, ...       │
│ filesystem │ Generic         │ Local CSV / Parquet      │ files              │
└────────────┴─────────────────┴──────────────────────────┴────────────────────┘
```

These are *types*, not project-named sources. Pick one and `tycoon data sources add <type>` will create an instance.

The catalog ships in tycoon — it doesn't reach out anywhere. Native types (`rest_api`, `filesystem`, `sql_database`) are part of dlt core. Non-native types (`github`, `slack`, `stripe`, etc.) require a one-time `dlt init` step that `add` runs for you.

## `add` — register a new source

```bash
tycoon data sources add                # browse + pick interactively
tycoon data sources add github          # skip the type-pick step
```

`add` walks you through three prompts:

1. **Type** (skipped if you passed it as an argument)
2. **Source name** — your project-local identifier. Default: `my-<type>` for catalog types, or auto-derived for some sources (e.g. `pokeapi` for the demo rest_api).
3. **Schema name** — where the raw data lands in DuckDB. Default: `raw_<source_name>`.

Then type-specific config:

- **github** — repo owner + name, optional access token env var name
- **slack** — workspace + bot token env var name
- **rest_api** — base URL, dataset list, optional auth header
- **filesystem** — directory path + glob pattern
- **sql_database** — connection string + table list

The new source is written to `tycoon.yml`'s `sources:` map. For non-native types, `add` also offers to install the dlt source files (one-time `dlt init <type>` to `~/.tycoon/sources/`).

### Non-interactive mode (`--no-prompt`)

For CI, scripted bootstrap, or online recipe doctests, pass `--no-prompt` and the required type-specific flags. The command skips every prompt and fails fast if a required value is missing.

```bash
# rest_api — base URL is required, --resources optional
tycoon data sources add rest_api \
  --base-url https://api.example.com/v1/ \
  --resources widgets,gadgets \
  --no-prompt

# sql_database — name is required (no auto-naming rule)
tycoon data sources add sql_database \
  --name warehouse-pg \
  --schema raw_pg \
  --connection-string '${DATABASE_URL}' \
  --no-prompt

# filesystem
tycoon data sources add filesystem \
  --path ./data/inbox/*.csv \
  --no-prompt
```

Flag reference:

| Flag | Purpose |
|---|---|
| `--no-prompt` | Skip every prompt; required values come from flags |
| `--name <id>` | Source name (auto-derived for `rest_api` / `filesystem` from the URL/path) |
| `--schema <id>` | Raw schema name (auto-derived if omitted) |
| `--base-url <url>` | Required for `rest_api` under `--no-prompt` |
| `--resources <csv>` | Comma-separated resource list for `rest_api` |
| `--connection-string <s>` | Required for `sql_database` under `--no-prompt`. Use `${ENV_VAR}` for secrets |
| `--path <p>` | Required for `filesystem` under `--no-prompt` |
| `--config key=value` | Extra config pairs. Repeatable. Overrides type-specific flags |
| `--force` | Overwrite an existing source with the same name without confirming |

Catalog credentials default to `${ENV_VAR}` references in both modes — set the env var separately. Catalog-source files (`dlt init`-style downloads) are not auto-installed under `--no-prompt`; run `tycoon data sources catalog install <type>` separately if you need them.

## `list` — list registered sources

```bash
tycoon data sources list
```

Shows every source in the project's `tycoon.yml`:

```
                  Registered Sources
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Name           ┃ Type       ┃ Schema             ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ nyc-dot        │ rest_api   │ raw_nyc_dot        │
│ mta-gtfs       │ filesystem │ raw_mta            │
└────────────────┴────────────┴────────────────────┘
```

`tycoon data sources show <name>` drills into one source — full config, including the `tables:` filter list (if set) and the dlt-resource detail.

## `run` — ingest

```bash
tycoon data sources run                       # all sources
tycoon data sources run github                # one source
tycoon data sources run github --max-records 50  # cheap test runs
```

For each source:

1. Reads its config from `tycoon.yml`
2. Hands the config to dlt (or the bespoke pipeline module for legacy NYC sources)
3. Writes to `data/raw.duckdb` under the source's schema
4. Captures the load into `.tycoon/metadata.duckdb` (observability)
5. Refreshes the auto-generated `_tycoon_dlt_*` Rill dashboards

`--max-records` caps row count per resource — useful for development.

`run` warns loudly if any config field still contains an unexpanded `${VAR}`:

```
WARN  Config key 'access_token' contains an unexpanded env var: ${GITHUB_TOKEN}
        Set it with: export GITHUB_TOKEN=<your-value>
```

## `remove` — unregister a source

```bash
tycoon data sources remove github
```

Removes the named source from `tycoon.yml`. Does **not** drop the existing schema in `data/raw.duckdb` — use `tycoon data clean` to wipe data.

## Pipeline dispatch model

The runner picks how to ingest each source in this order:

1. **Legacy pipeline modules** (keyed by source name) — currently `nyc-dot`, `mta-gtfs`, `mta-bus-speeds`. These have hand-tuned dlt code in `tycoon.ingestion.<name>_pipeline`.
2. **Native dlt builders** — `rest_api`, `sql_database`, `filesystem` ship with dlt core.
3. **Catalog sources** — `github`, `slack`, `stripe`, etc. require `~/.tycoon/sources/<type>/` to be populated (run `dlt init <type>` once via `tycoon data sources add`).
4. **Dynamic fallback** — `dlt.sources.<type>` import attempt.

If none match, you get a clear error pointing you at `tycoon data sources add <type>`.

## Related

- [Reference: tycoon.yml `sources` block](../../reference/tycoon-yml.md#sources)
- [Reference: Templates](../../reference/templates.md) — every template ships pre-registered sources
- [`tycoon data run-all`](run-all.md) — ingest all sources, then dbt build, in one command
- [`tycoon data history`](history.md) — see what was ingested and when
