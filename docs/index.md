---
hide:
  - navigation
---

# Database Tycoon

A local-first analytics CLI that adapts to your existing data stack.

```bash
pip install database-tycoon
tycoon init --template csv-import
tycoon data run-all
```

---

## What is tycoon?

Tycoon is a single command-line tool that orchestrates a local analytics
pipeline — ingestion, transformation, dashboards, and an AI agent — across
the tools you already use:

- **[dlt](https://dlthub.com)** for ingestion (REST APIs, files, SQL databases, your own dlt sources)
- **[dbt](https://getdbt.com)** for transformation (with first-class duckdb, MotherDuck, Snowflake, BigQuery, and Redshift support)
- **[DuckDB](https://duckdb.org)** for the warehouse (or MotherDuck, when you want it in the cloud)
- **[Rill](https://rilldata.com)** for dashboards
- **[Nao](https://getnao.io)** for natural-language queries via the LLM of your choice (LM Studio, Ollama, Claude, OpenAI, ...)
- **[Dagster](https://dagster.io)** for orchestration

You write one `tycoon.yml`. Tycoon scaffolds, configures, and runs the rest.

## Why local-first?

Every part of the stack runs on your laptop. You can demo, develop, or
debug a full pipeline without an internet connection or a cloud
account. When you're ready to push to a cloud warehouse, the same
commands work — `tycoon.yml` just points somewhere else.

This isn't a "demo" or a "starter project" — it's a production tool
that happens to be friendly to operate offline. Pipelines built with
tycoon run identically on a laptop and on a cloud VM.

## What's in this docs site?

<div class="grid cards" markdown>

-   :material-rocket-launch: **[Getting started](getting-started/installation.md)**

    ---

    Install tycoon, scaffold a first project, and walk through ingestion
    → transformation → dashboards → AI agent end-to-end.

-   :material-console: **[Commands](commands/index.md)**

    ---

    Reference for every `tycoon ...` command. Each page documents the
    flags, behavior, and worked examples.

-   :material-book-open-page-variant: **[Reference](reference/tycoon-yml.md)**

    ---

    The `tycoon.yml` schema, built-in templates, observability tables,
    and environment variables.

-   :material-tag: **[Releases](releases/v0.1.5.md)**

    ---

    Per-release narrative notes — what shipped, what didn't, and why.

</div>

## A note on this site

These docs are written for tycoon **v0.1.5**. Anything called out as
"deferred to v0.2.0" links to a tracking issue on the
[GitHub repo](https://github.com/Database-Tycoon/tycoon-cli/issues).
The `releases/` section carries the canonical change history.

The site is built with
[MkDocs Material](https://squidfunk.github.io/mkdocs-material/);
the source markdown lives in `docs/` of the
[tycoon-cli repo](https://github.com/Database-Tycoon/tycoon-cli/tree/main/docs).
