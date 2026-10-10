# `tycoon data query` / `schema` / `clean`

Three lightweight commands for inspecting and tearing down the warehouse without spinning up dbt or Rill.

## `query` — read-only SQL

```bash
tycoon data query "SELECT * FROM stg_widgets LIMIT 10"
```

Runs a SQL query against the warehouse and prints the result as a Rich table, or as CSV, JSON or Markdown with `--format`.

### Synopsis

```
tycoon data query SQL [OPTIONS]

Arguments:
  SQL  SQL query to execute

Options:
  --db PATH         Override which DuckDB to query. Default: warehouse
  --source NAME     Query a source's raw schema (resolves to data/raw_<name>.duckdb
                    or main raw.duckdb's raw_<name> schema)
  -f, --format      table (default), csv, json or markdown
  -h, --help        Show this message and exit
```

### Examples

```bash
# Default — query the warehouse (data/warehouse.duckdb)
tycoon data query "SELECT count(*) FROM mart.fct_orders"

# Query the raw layer for a specific source
tycoon data query --source github "SELECT * FROM raw_github.issues LIMIT 5"

# Query the metadata DB (observability)
tycoon data query --db .tycoon/metadata.duckdb \
  "SELECT command, started_at, success FROM dbt_runs ORDER BY started_at DESC LIMIT 5"

# Query a synced snapshot
tycoon data query --db ./snap.duckdb "SHOW ALL TABLES"

# Rows only, for a script or notebook
tycoon data query --format csv "SELECT * FROM mart.fct_orders" > orders.csv
tycoon data query --format json "SELECT * FROM mart.fct_orders LIMIT 5" | jq '.[0]'
```

### Output formats

`--format` (or `-f`) picks how the rows come back:

| Format | Output |
|---|---|
| `table` | The default. A Rich table with a title and a `N row(s) returned` line. |
| `csv` | A header line, then one line per row. NULL is an empty field. |
| `json` | A JSON array with one object per row, keyed by column name. NULL is `null`, `DECIMAL` values are numbers, and dates, timestamps and other types are strings. |
| `markdown` | A GitHub-flavored Markdown table, ready to paste into an issue or a doc. |

`csv`, `json` and `markdown` print the rows and nothing else, so the output can go straight into a file or another tool. Errors still go to stderr.

In `table` format, a result too wide for the terminal (one where some column couldn't show its full name) prints one block per row instead, with each column name beside its value, like `psql`'s expanded display. A result that fits keeps the usual column layout.

### Live warehouse via Quack (v0.1.9)

When a [Quack](../start.md#quack-the-live-multi-client-warehouse-v019) server is holding the warehouse — i.e. `tycoon start` is running — a plain warehouse query (no `--db` / `--source` / `--raw`) **attaches over Quack** instead of opening the file. You'll see the result labelled `warehouse (Quack)`. This is what lets you query the live warehouse while the rest of the stack is up, rather than hitting DuckDB's single-writer file lock. When no server is running, the command opens the file directly as before. It's automatic — there's no flag.

`--source` is a convenience for the common case of "show me the raw landed data". It walks tycoon's path resolution:

1. `config.raw_db` if it contains the `raw_<name>` schema (single-DB mode — current default)
2. `data/raw_<name>.duckdb` if the per-source file exists
3. Any other `data/*.duckdb` whose name matches the schema

### Limitations

- **DuckDB / MotherDuck only.** Snowflake / BigQuery / Redshift warehouses can be registered, but `query` doesn't dispatch to them yet. Carried forward as a known limitation.
- **Read-only by default.** The command opens the file with `read_only=True`. Use `tycoon run duckdb ...` for ad-hoc writes.

## `schema` — dump tables, row counts, sizes

```bash
tycoon data schema                          # raw database, warehouse, other data/*.duckdb files
tycoon data schema --warehouse              # the warehouse only
tycoon data schema --schema main_marts      # one schema
tycoon data schema --raw --schema 'raw_*'   # schemas matching a glob, in the raw database
tycoon data schema --include-dlt            # also list dlt's _dlt_* tables
```

Lists the tables in the raw database and the warehouse, with row counts and each DuckDB file's size. Any other `.duckdb` file in `data/` is listed too. Useful for "what's in this DB?" and "which tables have rows?" without writing SQL.

### Synopsis

```
tycoon data schema [OPTIONS]

Options:
  --schema TEXT    Only show schemas matching this name or glob
  --raw            Only show the raw database
  --warehouse      Only show the warehouse
  --include-dlt    Also show dlt's _dlt_* bookkeeping tables
  -h, --help       Show this message and exit
```

### Narrowing the output

- `--raw` and `--warehouse` each pick one database, the same split as `data query --raw`. Passing either one leaves out the other `data/*.duckdb` files. Pass both to see the raw database and the warehouse without those extra files.
- `--schema` takes a schema name or a shell-style glob (`*`, `?`, `[...]`). Matching ignores case. Quote a glob so your shell doesn't expand it. If nothing matches, the command says so.
- dlt keeps bookkeeping tables such as `_dlt_loads` and `_dlt_version` in every dataset it loads. They're left out by default, and the `Tables` line says how many were hidden. `--include-dlt` lists them.

On a MotherDuck database, each listed table costs one `count(*)` query, and tables left out by these options aren't counted, so a narrow `--schema` is also cheaper.

## `clean` — remove warehouse files

```bash
tycoon data clean                       # default: removes data/*.duckdb except metadata
tycoon data clean --all                 # also wipes scaffolded files (rill/, dbt target/)
tycoon data clean --metadata            # explicitly remove .tycoon/metadata.duckdb
```

### Synopsis

```
tycoon data clean [OPTIONS]

Options:
  --all          Also remove rill/tmp, dbt target/, dbt_packages/, logs/
  --metadata     Remove .tycoon/metadata.duckdb (preserved by default, even with --all)
  -h, --help     Show this message and exit
```

### What gets cleaned by default

- `data/raw.duckdb`, `data/warehouse.duckdb`, and any other `data/*.duckdb` files
- Per-source raw DuckDBs (`data/raw_*.duckdb`)
- Parquet exports under `data/parquet/`

### What's preserved

- `.tycoon/metadata.duckdb` — observability run history. Pass `--metadata` to remove explicitly.
- `tycoon.yml` — your config.
- `dbt_project/` source files — only `target/` and `dbt_packages/` are removed (and only with `--all`).
- `rill/` source files — only `rill/tmp/` is removed (and only with `--all`).

The `--metadata` carve-out exists because routine `tycoon data clean --all` cycles shouldn't nuke run history; you usually want to wipe data without losing the "what changed yesterday" trail.

### Why preserve metadata.duckdb?

It's the source of truth for `tycoon data history`, the auto-generated Rill dashboards (`_tycoon_dlt_usage` / `_tycoon_dbt_usage`), and the schema-diff captures from v0.1.3. Re-ingesting after `clean` will append new rows to the existing tables — `tycoon data history` keeps showing yesterday's runs alongside today's.

If you genuinely want a fresh start: `tycoon data clean --all --metadata`.

## Related

- [`tycoon data history`](history.md) — terminal view over `metadata.duckdb`
- [`tycoon data sync`](sync.md) — pull a fresh snapshot from a cloud warehouse
- [Reference: tycoon.yml `database` block](../../reference/tycoon-yml.md#database)
