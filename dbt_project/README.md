# dbt_project

This is the tycoon dbt project. It reads from raw DuckDB files produced by dlt and writes analysis-ready tables into `data/warehouse.duckdb`.

The dbt adapter is `dbt-duckdb`. Raw source databases are attached read-only via the dbt profile.

---

## Layer Structure

**staging** (`models/staging/<source>/`)

One subdirectory per source. Staging models clean the raw dlt schema: cast types, rename columns to snake_case, and apply basic null handling. They do not join across sources. Each model corresponds directly to one raw table from dlt.

**intermediate** (`models/intermediate/`)

Optional cross-source joins and reusable building blocks used by multiple mart models.

**marts** (`models/marts/<source>/` and `models/marts/reports/`)

Analysis-ready tables. Source-specific marts expose aggregated or enriched views of a single source. The `reports/` subdirectory contains cross-source report models (e.g., NYC transit report models).

**semantic** (`models/semantic/`)

Semantic layer definitions for use with Nao and Rill.

---

## Source Coverage

| Source | Staging Models | Mart Models |
|---|---|---|
| `github` | stg_github__commits, stg_github__issues, stg_github__pull_requests | github__issues, github__pull_requests, github__repo_activity |
| `slack` | stg_slack__channels, stg_slack__messages, stg_slack__users | slack__channel_activity, slack__user_activity |
| `stripe` | customer, invoice, product, subscription | (via dlt-hub passthrough — see below) |
| `hubspot` | companies, contacts, deals, tickets | (via dlt-hub passthrough — see below) |
| `notion` | stg_notion__databases, stg_notion__pages, stg_notion__users | notion__pages, notion__workspace_activity |

---

## dlt-hub Packages

Stripe and HubSpot transformations use pre-built dbt packages from dlt-hub, declared in `packages.yml`:

```yaml
packages:
  - git: "https://github.com/dlt-hub/dlt-dbt-stripe.git"
    revision: main
  - git: "https://github.com/dlt-hub/dlt-dbt-hubspot.git"
    revision: main
```

The staging models for these sources act as passthrough adapter views that align the raw dlt column names with the schema expected by the dlt-hub packages. Run `dbt deps` before running transformations if you have added or updated these packages.

---

## DuckDB-Specific Patterns

These patterns appear throughout the models and are standard for `dbt-duckdb`:

- **`TRY_CAST`** — used instead of `CAST` to avoid hard failures on dirty data (returns `NULL` on cast failure)
- **`epoch_ms()` / `to_timestamp()`** — dlt stores some timestamps as Unix epoch integers; these functions convert them to `TIMESTAMP`
- **`QUALIFY`** — used to filter window function results inline, avoiding subquery wrapping (e.g., deduplication with `ROW_NUMBER()`)
- **Read-only attachment** — raw DuckDB files are attached as read-only in the dbt profile to prevent accidental writes from transformation runs

---

## Running dbt

From the project root:

```bash
uv run dbt run --project-dir dbt_project --profiles-dir dbt_project
uv run dbt test --project-dir dbt_project --profiles-dir dbt_project
```

Or via the CLI:

```bash
tycoon data transform run
```
