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
│ google_she…│ Spreadsheets    │ Tabs/ranges from a sheet │ sheets             │
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
- **google_sheets** — service-account key path, spreadsheet URL/ID, optional tab/range list
- **rest_api** — base URL, dataset list, optional auth header
- **filesystem** — directory path + glob pattern
- **sql_database** — connection string + table list

The new source is written to `tycoon.yml`'s `sources:` map. For non-native types, `add` also offers to install the dlt source files (one-time `dlt init <type>`). Where those files land depends on whether the project has its own `.venv`: a project with one gets its own `<project>/.tycoon/sources/`, a project without one still shares `~/.tycoon/sources/` across every tycoon project on the machine. A source installed into the shared location before a project picked up a `.venv` doesn't move on its own; `tycoon data sources migrate <type>` copies it into the project-local directory.

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

Catalog credentials default to `${ENV_VAR}` references in both modes — set the env var separately. Catalog-source files (`dlt init`-style downloads) and dlt extras are now installed automatically under `--no-prompt`, matching every other default in this command; a failed install fails the command and removes the source from `tycoon.yml` (or restores whatever `--force` was about to overwrite) rather than leaving it registered but unusable. The one exception: if the project has no `.venv`/`pyproject.toml` of its own yet, installing a source's own dependencies or a dlt extra is skipped rather than silently mutating the shared/ambient environment. Run `tycoon setup` first, or install the dependency manually.

### Google Sheets

Google Sheets pulls one or more tabs/ranges from a spreadsheet into DuckDB. The header row becomes typed columns. First cut is **full-refresh replace** per run — Sheets has no native incremental key.

**1. Get a service-account key (headless/cron-friendly).** Create a service account at [console.cloud.google.com/iam-admin/serviceaccounts](https://console.cloud.google.com/iam-admin/serviceaccounts), enable the **Google Sheets API** for the project, and download a JSON key. Then **share the spreadsheet** with the service-account's email (`...@....iam.gserviceaccount.com`) — read access is enough.

**2. Point tycoon at the key.** The credential defaults to the standard `${GOOGLE_APPLICATION_CREDENTIALS}` env var:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=~/keys/sheets-sa.json
```

**3. Register the source.** Interactively (`tycoon data sources add google_sheets`) you'll be prompted for the key path, the spreadsheet URL/ID, and an optional tab/range list. Non-interactively:

```bash
tycoon data sources add google_sheets \
  --name marketing-sheet \
  --config 'spreadsheet_url_or_id=https://docs.google.com/spreadsheets/d/<ID>/edit' \
  --config 'range_names=Sheet1,Q1 2026!A1:F' \
  --no-prompt
```

- **`spreadsheet_url_or_id`** — the full share URL or just the ID. Required.
- **`range_names`** — comma-separated tab names and/or A1 ranges. Leave blank to load **every** sheet in the spreadsheet.
- **`credentials_path`** — defaults to `${GOOGLE_APPLICATION_CREDENTIALS}`. Leave it blank to fall back to dlt's own credential resolution (env / `secrets.toml`), which is where the **OAuth / Application Default Credentials** path lives if you'd rather not use a service account.

**4. Ingest:** `tycoon data sources run marketing-sheet`. The first run downloads the dlt `google_sheets` verified source (to the project's own `.tycoon/sources/` if it has a `.venv`, otherwise the shared `~/.tycoon/sources/`), then loads into `raw_<name>` and auto-scaffolds a staging dbt model.

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
3. **Catalog sources**: `github`, `slack`, `stripe`, etc. require `<type>/` to be populated under the resolved sources dir (`<project>/.tycoon/sources/` once the project has its own `.venv`, otherwise the shared `~/.tycoon/sources/`), via `dlt init <type>` once through `tycoon data sources add`.
4. **Dynamic fallback** — `dlt.sources.<type>` import attempt.

If none match, you get a clear error pointing you at `tycoon data sources add <type>`. If the source is installed in the shared global directory but the project has since picked up its own `.venv`, the error points at `tycoon data sources migrate <type>` instead.

Project-local `.tycoon/sources/` holds the downloaded dlt source code itself, not just config, and nothing in a scaffolded project excludes `.tycoon/` from version control. The first `dlt init` into a given sources dir writes a `.gitignore` there that keeps secrets, credentials, and local `.duckdb` files out, but it doesn't exclude the downloaded source packages themselves, those are tracked and committed by default if the project is a git repo. Add `.tycoon/sources/` to the project's own `.gitignore` if you'd rather not commit that third-party code.

## Related

- [Reference: tycoon.yml `sources` block](../../reference/tycoon-yml.md#sources)
- [Reference: Templates](../../reference/templates.md) — every template ships pre-registered sources
- [`tycoon data run-all`](run-all.md) — ingest all sources, then dbt build, in one command
- [`tycoon data history`](history.md) — see what was ingested and when
