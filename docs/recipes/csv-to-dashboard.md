# Recipe: CSV files to a live dashboard

End-to-end walkthrough — drop a CSV, ingest it, transform it, and put it on a dashboard. Fully offline.

## Setup

```bash
mkdir analytics-demo && cd analytics-demo
tycoon init --template csv-import --name analytics-demo
```

The `csv-import` template ships:

- A `data/input/widgets.csv` sample
- A working `dbt_project/` with one staging model
- An empty `rill/` ready for dashboards

## 1. Drop your real CSVs

Replace the sample CSV with your own files:

```bash
cp ~/Downloads/orders.csv data/input/orders.csv
cp ~/Downloads/customers.csv data/input/customers.csv
```

By default, `tycoon.yml` has the `files` source configured to glob `data/input/*.csv`. Open `tycoon.yml` to confirm:

```yaml
sources:
  files:
    type: filesystem
    schema: raw_files
    config:
      bucket_url: data/input
      file_glob: "*.csv"
```

## 2. Ingest

```bash
tycoon data sources run files
```

Each `.csv` lands as a table under the `raw_files` schema in `data/raw.duckdb`. Quick sanity check:

```bash
tycoon data query --source files "SELECT count(*) FROM raw_files.orders"
tycoon data schema --db data/raw.duckdb
```

## 3. Generate staging models

```bash
tycoon data analyze files
```

This writes one staging model per CSV under `dbt_project/models/staging/`:

```
dbt_project/models/staging/
├── stg_files__orders.sql
├── stg_files__customers.sql
└── schema.yml
```

Each `.sql` is a typed `SELECT *` from the raw table — edit them to add filtering, renaming, casting. The default is "passthrough with `_dlt_*` columns excluded."

## 4. Build mart models (your business logic)

This is the part tycoon doesn't generate — it's your project. Add a mart model:

```bash
mkdir -p dbt_project/models/mart
cat > dbt_project/models/mart/fct_orders.sql <<'EOF'
SELECT
  o.order_id,
  o.customer_id,
  c.customer_name,
  o.order_total,
  o.order_date
FROM {{ ref('stg_files__orders') }} o
JOIN {{ ref('stg_files__customers') }} c USING (customer_id)
EOF
```

Run dbt:

```bash
tycoon data transform run
```

`fct_orders` lands in `data/warehouse.duckdb`'s `mart` schema. Inspect:

```bash
tycoon data query "SELECT * FROM mart.fct_orders LIMIT 10"
```

## 5. Generate dashboards

```bash
tycoon data analyze files --rill
```

Writes Rill `source / metrics_view / dashboard` YAMLs for every staging table. For mart-level dashboards (the more useful ones), hand-edit `rill/dashboards/fct_orders.yaml`:

```yaml
type: explore
display_name: "Orders by customer"
metrics_view: fct_orders_mv
```

## 6. Open the dashboard

```bash
tycoon start --only rill
```

Browse to `http://localhost:9009`. You'll see:

- Your auto-generated `stg_files__*` dashboards
- Your hand-customized `fct_orders` dashboard (if you wrote it)
- Two `_tycoon_*` dashboards showing pipeline health

## 7. Refresh

When the underlying CSVs change:

```bash
# Full rebuild
tycoon data run-all

# Or piecemeal
tycoon data sources run files
tycoon data transform run
```

Both update the warehouse, refresh the Parquet exports, and the open Rill dashboard reloads automatically.

## Add an AI agent (optional)

```bash
pip install 'database-tycoon[ask,server]'
tycoon register llm lm-studio         # zero-config local LLM
tycoon ask sync                       # ~30s, builds context
tycoon ask chat                       # http://localhost:5005
```

Now you can ask "which customer has the most orders this month?" in natural language. The LLM has read access to your warehouse, dbt models, and any rules you put in `.tycoon/nao/RULES.md`.

## Tear down

```bash
tycoon stop
rm -rf analytics-demo                 # tycoon writes nothing outside it
```

## Related

- [Templates: `csv-import`](../reference/templates.md#csv-import)
- [`tycoon data sources run`](../commands/data/sources.md)
- [`tycoon data analyze`](../commands/data/analyze.md)
- [`tycoon ask`](../commands/ask/index.md)
