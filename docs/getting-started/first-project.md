# Your first project

A 10-minute walkthrough that takes you from `tycoon init` to a queryable
warehouse with auto-generated dashboards. We'll use the `csv-import`
template because it runs entirely offline — no API keys, no network
calls.

## 1. Initialize

```bash
mkdir my-project && cd my-project
tycoon init --template csv-import --name my-project
```

You'll get:

```
my-project/
├── tycoon.yml              # the config you'll touch most
├── data/                   # DuckDB files + parquet exports
│   └── input/
│       └── widgets.csv     # bundled sample data
├── dbt_project/            # dbt models
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/staging/
│       └── stg_widgets.sql
├── rill/                   # Rill dashboards
│   └── rill.yaml
└── .gitignore
```

The `csv-import` template ships a working `dbt_project/` and a sample
CSV so the full pipeline runs end-to-end on a fresh install. The
`nyc-transit` template needs network access; `csv-import` does not.

## 2. Health check

```bash
tycoon doctor
```

Walks through tycoon.yml validity, dbt project presence, Rill setup,
and observability state. Use it any time something feels off.

## 3. Ingest

```bash
tycoon data sources run files
```

What happens:

1. Tycoon reads `tycoon.yml`, finds `sources.files` (a `filesystem`-type
   source pointed at `data/input/*.csv`).
2. Hands the config to dlt, which writes to `data/raw.duckdb` under
   schema `raw_files`.
3. Captures the run into `.tycoon/metadata.duckdb` (observability —
   `tycoon data history` shows it).

You'll see a summary like:

```
> Type: filesystem | Schema: raw_files
> Record cap: (none)
OK files load complete. Pipeline files load step completed in 0.08 seconds
1 load package(s) were loaded to destination duckdb and into dataset raw_files
```

Inspect what landed:

```bash
duckdb data/raw.duckdb -c "SELECT * FROM raw_files.widgets LIMIT 5;"
```

## 4. Transform

```bash
tycoon data transform run
```

Runs dbt against the warehouse. Models in `dbt_project/models/` build
into `data/warehouse.duckdb`. The default `csv-import` template includes
one staging model (`stg_widgets`) that lifts the raw CSV into a typed
table.

Inspect the result:

```bash
tycoon data query "SELECT * FROM stg_widgets;"
```

Or dump the schema:

```bash
tycoon data schema main
```

## 5. Generate dashboards

```bash
tycoon data analyze files --rill
```

Generates Rill source / metrics-view / dashboard YAML files for every
table in the `raw_files` schema. The `--rill` flag is opt-in because
not every project wants dashboards.

Open them:

```bash
tycoon start --only rill
```

Browse to `http://localhost:9009`. You'll see two auto-generated
dashboards regardless of your data:

- `_tycoon_dlt_usage` — ingestion freshness across all sources
- `_tycoon_dbt_usage` — dbt model run history

Plus one explore per table you ingested (e.g. `stg_files__widgets`).

## 6. Run history

```bash
tycoon data history                   # last 10 runs across dlt + dbt
tycoon data history show <id>          # drill into one run
```

The `history show` view tells you what changed. For a dlt run: pipeline
duration, total bytes written, per-step timings, per-table row counts.
For a dbt run: per-node status, execution time, and a "Schema changes
vs. previous run" table when columns shifted.

## 7. Tear down

```bash
tycoon stop                # stop any background services
rm -rf my-project          # tycoon writes nothing outside this directory
```

---

## Where to go next

- [Concepts](concepts.md) — what `tycoon.yml` actually models and how
  observability works.
- [Commands](../commands/index.md) — full reference for every command.
- [Reference: tycoon.yml](../reference/tycoon-yml.md) — every key in the
  config file.
- [Reference: Templates](../reference/templates.md) — what each template
  scaffolds and when to use it.
