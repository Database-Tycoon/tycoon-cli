# `tycoon data query` / `schema` / `clean`

Three lightweight commands for inspecting and tearing down the warehouse without spinning up dbt or Rill.

## `query` — read-only SQL

```bash
tycoon data query "SELECT * FROM stg_widgets LIMIT 10"
```

Runs a SQL query against the warehouse and prints the result as a Rich table.

### Synopsis

```
tycoon data query SQL [OPTIONS]

Arguments:
  SQL  SQL query to execute

Options:
  --db PATH         Override which DuckDB to query. Default: warehouse
  --allow-writes    On MotherDuck, run statements other than read-only queries
  --source NAME     Query a source's raw schema (resolves to data/raw_<name>.duckdb
                    or main raw.duckdb's raw_<name> schema)
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
```

### Live warehouse via Quack (v0.1.9)

When a [Quack](../start.md#quack-the-live-multi-client-warehouse-v019) server is holding the warehouse — i.e. `tycoon start` is running — a plain warehouse query (no `--db` / `--source` / `--raw`) **attaches over Quack** instead of opening the file. You'll see the result labelled `warehouse (Quack)`. This is what lets you query the live warehouse while the rest of the stack is up, rather than hitting DuckDB's single-writer file lock. When no server is running, the command opens the file directly as before. It's automatic — there's no flag.

`--source` is a convenience for the common case of "show me the raw landed data". It walks tycoon's path resolution:

1. `config.raw_db` if it contains the `raw_<name>` schema (single-DB mode — current default)
2. `data/raw_<name>.duckdb` if the per-source file exists
3. Any other `data/*.duckdb` whose name matches the schema

### Limitations

- **DuckDB / MotherDuck only.** Snowflake / BigQuery / Redshift warehouses can be registered, but `query` doesn't dispatch to them yet. Carried forward as a known limitation.
- **Read-only by default.** A local file is opened with `read_only=True`. Use `tycoon run duckdb ...` for ad-hoc writes.
- **MotherDuck needs `--allow-writes` to write.** DuckDB cannot open an `md:` database read-only, so tycoon checks each statement first and runs only SELECT, WITH, `FROM tbl`-first queries, `TABLE tbl`, VALUES, set operations, DESCRIBE, SHOW, SUMMARIZE, PIVOT, UNPIVOT and EXPLAIN of those. Anything else, a statement tycoon cannot parse (including a query nested too deeply, or a schema-qualified `TABLE s.t`; write `SELECT * FROM s.t`), or any statement in a multi-statement input exits 1 before connecting, with `Refusing to run DROP against MotherDuck (md:x)` and the flag to pass.
- **The MotherDuck check is not a permission boundary.** It reads statement types only and does not inspect function calls inside a SELECT, so `SELECT nextval('s')` advances a sequence, `read_csv` reads a path or URL, and `FROM checkpoint()` runs, all without `--allow-writes`. It guards against accidental statements. Scope your token if you need more than that.
- **A SQL comment cannot start the argument.** `tycoon data query "-- note\nSELECT 1"` is read as an option; put `--` before it: `tycoon data query -- "-- note\nSELECT 1"`.

## `schema` — dump tables, row counts, sizes

```bash
tycoon data schema
```

Lists every table in the raw and warehouse databases, plus any other `.duckdb` file in the data directory, with row counts and DuckDB file size. Useful for "what's in this DB?" / "which tables have rows?" without writing SQL.

On a MotherDuck database (`database.warehouse: md:<name>`), row counts are estimates read from the catalog, printed as `~1,000 rows (estimate)`, because an exact `count(*)` per table is slow and spends compute. The estimate comes from DuckDB's table statistics and does not drop after deletes: a table that held 100,000 rows and lost half of them still shows `~100,000 rows (estimate)` where `--exact` shows `50,000 rows`. A view has no estimate and prints `view (use --exact to count)`; a table whose catalog reports no estimate prints `no estimate (use --exact to count)`. Pass `--exact` to count every table and view. Local DuckDB files always show exact counts.

### Synopsis

```
tycoon data schema [OPTIONS]

Options:
  --exact     Count rows exactly on a MotherDuck database instead of estimating
  -h, --help  Show this message and exit
```

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
