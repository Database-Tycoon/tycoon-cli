# data/

This directory holds all DuckDB database files for the project. It is listed in `.gitignore` and is not committed to the repository.

---

## Files

### Raw databases (dlt output)

One file per source, written by dlt ingestion pipelines:

```
raw_<source>.duckdb
```

Examples:

```
raw_github.duckdb
raw_slack.duckdb
raw_stripe.duckdb
```

These files contain the raw schema as produced by dlt, including dlt metadata tables (`_dlt_loads`, `_dlt_pipeline_state`). They are attached **read-only** in the dbt profile to prevent transformation runs from writing back to the raw layer.

### Warehouse database (dbt output)

```
warehouse.duckdb
```

Written by dbt transformation runs. This is the single database read by Rill dashboards and Nao AI queries. All mart and report models land here.

---

## Naming Convention

| File | Written by | Read by |
|---|---|---|
| `raw_<source>.duckdb` | `tycoon data sources run <source>` | dbt (read-only attach) |
| `warehouse.duckdb` | `tycoon data transform run` | Rill, Nao, `tycoon data db` |

---

## Notes

- Do not manually edit or delete these files while a pipeline or dbt run is in progress.
- To reset a source, delete its raw DuckDB file and re-run ingestion.
- To reset the warehouse, delete `warehouse.duckdb` and re-run `tycoon data transform run`.
- The `tycoon data db` command opens an interactive DuckDB shell on `warehouse.duckdb`.
