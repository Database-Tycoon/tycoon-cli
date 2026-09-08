# Roadmap

_Last updated: 2026-09-04. This roadmap is the north star for tycoon-cli — the
direction we are building toward, reviewed at each sprint retro. The
[wish list](#wish-list) below it collects ideas we like but have not committed
to; things move from the wish list onto the roadmap, never silently the other
way._

## Who tycoon is for

**The dlt user.** You already think in dlt pipelines — or you're one
`tycoon init` away from starting to. tycoon gives that person a complete local
analytics stack (ingestion → DuckDB → dbt → dashboards → a catalog you can
walk through) with one pip install and no accounts, no Docker, no cloud bill.

Two supported ways in:

1. **Stock sources** — pick from the dlt verified sources (~40 of them);
   tycoon installs, configures, and runs them for you.
2. **Bring your own dlt project** — point tycoon at the pipelines you already
   wrote and let it run, observe, and catalog them
   ([#75](https://github.com/Database-Tycoon/tycoon-cli/issues/75)).

## What we are explicitly not building

- **Other query engines — today.** DuckDB is the engine. A Snowflake backend
  is potential future scope, not something we are building now.
- **Vendor ingestion runtimes.** No Airbyte or Fivetran execution inside
  tycoon. (A read-only Fivetran *observability* mode lives on the wish list.)
- **A hosted product.** tycoon is local-first. The one cloud target we do
  plan is MotherDuck, because it *is* DuckDB.

## Now — v0.2.1

- **Source catalog** ([#84](https://github.com/Database-Tycoon/tycoon-cli/issues/84)):
  a JSON manifest of verified sources plus a factory, so
  `tycoon data sources add` is driven by declared metadata instead of
  hand-written shims.
- **City stack, part 2** ([#206](https://github.com/Database-Tycoon/tycoon-cli/issues/206)):
  the simulation engine improvements (radial layout, planner consolidation,
  street thinning) and the five UI blockers from the 0.2.0 review.
- **Renderer test suite in CI**: the vendored `tests/tycoon_city` suite (41
  files) gates every PR.

## Next

- **Runtime re-architecture, M4–M7**
  ([#85](https://github.com/Database-Tycoon/tycoon-cli/issues/85),
  [#86](https://github.com/Database-Tycoon/tycoon-cli/issues/86),
  [#87](https://github.com/Database-Tycoon/tycoon-cli/issues/87),
  [#88](https://github.com/Database-Tycoon/tycoon-cli/issues/88)):
  a Runtime protocol so managed sources and bring-your-own dlt projects run
  through one interface, then pluggable destinations.
- **MotherDuck as the first cloud-runnable target** (after the runtime
  re-architecture lands): implement the existing backend spec against
  MotherDuck and test it aggressively end to end. If your stack runs on DuckDB
  locally, it should run on MotherDuck without ceremony.
- **uv-managed projects**: `tycoon init` scaffolds a real uv project;
  `sources add` installs a source's requirements into the managed venv
  automatically.

## AI & agents

tycoon's bet here is to be **the stack agents stand on**, not another agent:

- **Legible by design.** A tycoon project explains itself to coding and data
  agents: `AGENTS.md` ships with the package, run history and pipeline
  metadata are ordinary queryable tables, and every operation has a plain CLI
  contract an agent can drive and verify.
- **No required model.** tycoon never needs an API key to do its job. Where
  natural-language conveniences return (the `ask` layer was deliberately
  removed in v0.1.10 rather than half-maintained), they will run against an
  optional, user-configured OpenAI-compatible endpoint — LM Studio, Ollama,
  or any hosted API — and everything must keep working without one.
- **MCP is a research question, not a commitment.** Whether tycoon ships its
  own MCP server — catalog, lineage, and run history as first-class tools
  ([#142](https://github.com/Database-Tycoon/tycoon-cli/issues/142),
  [#143](https://github.com/Database-Tycoon/tycoon-cli/issues/143),
  [#202](https://github.com/Database-Tycoon/tycoon-cli/issues/202),
  [#203](https://github.com/Database-Tycoon/tycoon-cli/issues/203)) — gets a
  timeboxed spike first. Query-level MCP already exists in DuckDB and
  MotherDuck; we only build what those don't cover.

## Later

- The city renderer as the default way you *look at* your warehouse — CLI and
  visual as two views of the same catalog, toggling freely.
- A standalone documentation site.

## Wish list

Reviewed at retros; not scheduled, not promised.

- **DuckLake** layered physical storage (SQLite catalog)
  ([#73](https://github.com/Database-Tycoon/tycoon-cli/issues/73)) and DuckLake
  health checks in `doctor`
  ([#144](https://github.com/Database-Tycoon/tycoon-cli/issues/144)).
- **MotherDuck flights/dives**: render the pipeline city as a MotherDuck
  flight or dive.
- **Metadata-DB dashboards**: dashboards over tycoon's own run metadata.
- **Fivetran read-only operational mode**: API key in, connector health and
  reconstructed run logs out. Observability only — never a runtime.
- **Estuary ingestion** ([#80](https://github.com/Database-Tycoon/tycoon-cli/issues/80)):
  Flow as an alternative managed-ingestion vendor, mirrored Fivetran-style.
- **dbt Fusion**: adopt dbt Core v2 when dbt-duckdb and dagster-dbt support it
  ([#58](https://github.com/Database-Tycoon/tycoon-cli/issues/58)).
