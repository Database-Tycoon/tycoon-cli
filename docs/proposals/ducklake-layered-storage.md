# Proposal: native DuckLake layered storage (SQLite-catalog)

_Status: drafted 2026-06-21 from a spike investigation (4 spikes, all green). **Not scheduled** and **not part of v0.1.10** (the security pass). This is a storage-engine proposal for a future minor. It revives the DuckLake track deferred since v0.1.7 ([#31][], open) with new evidence, and builds on — does not replace — the **already-shipped** layer-aware data model ([#30][], closed): #30 delivered the *logical* layers, this adds an optional *physical* backing for them._

## TL;DR

Give each warehouse layer its own **DuckLake catalog** (SQLite metadata file + Parquet data), composed in one DuckDB session via `ATTACH`. dbt reads the `raw` catalog read-only and materializes into the `mart` catalog. Point each layer's `data_path` at `s3://…` and the same setup becomes a local-first lakehouse on object storage — no catalog server, no Docker. This is the credible local-first answer to "can we serve something like Polaris locally?": you don't serve a catalog, you open one.

The investigation also **corrects a factual error in shipped docs** (`docs/commands/data/analyze.md:68`) about why the Parquet bridge for Rill exists.

## How we got here

Started from two user questions: "how are we integrating with S3?" and "can we serve something like Polaris locally?" Following the thread led to DuckLake (catalog-as-a-database, only data on object storage), which raised the old objection that killed DuckLake for Rill in v0.1.3 — an exclusive-lock conflict while ingesting. We spiked it to find out whether that objection still holds.

## What the spikes proved

All scripts live in the session scratchpad (throwaway) and are reproducible; verified against DuckDB 1.5.3, ducklake ext `e6a3bd0a`, Rill 0.86, dbt-duckdb 1.10.1 / dbt-core 1.11.8.

| # | Question | Result |
|---|---|---|
| 1 | Front DuckLake with Quack to dodge the lock? | ❌ **They don't compose.** Quack proxies a native `.duckdb`'s tables, but an `ATTACH`ed DuckLake catalog is invisible to Quack clients. Treat Quack and DuckLake as orthogonal. |
| 2 | Which catalog backend actually locks? | **DuckDB-backed `.ducklake` locks** (process-exclusive file lock); **SQLite-backed does not** — a held-open READ_ONLY reader + a continuous writer ran clean and the reader saw new snapshots. Deterministic across runs. |
| 3 | Does the **real Rill** binary survive ingest on a SQLite catalog? | ✅ A Rill project with `olap_connector: lake` on a `ducklake:sqlite:` catalog reconciled and served **live-growing** aggregation counts (100 → 36,100) during ingest, **0 lock conflicts**. |
| 4 | Does **dbt** work raw-catalog → mart-catalog end-to-end? | ✅ `dbt run` read a READ_ONLY `raw` DuckLake catalog and materialized a model **into** a `mart` DuckLake catalog (3 snapshots, correct data) purely via `profiles.yml` `attach:`. |

## The corrected lock model (supersedes `analyze.md:68`)

`docs/commands/data/analyze.md:68` says the Parquet bridge exists because *"SQLite-backed DuckLake catalogs hold an exclusive lock that breaks Rill-while-ingesting."* **This is wrong on the backend.** The lock is a property of the **catalog metadata database**, not of DuckLake or of SQLite:

- **DuckDB-backed catalog** (`ducklake:foo.ducklake`, the default) — a `.ducklake` file *is* a DuckDB database, and DuckDB locks a database file to one process. Two processes → `Conflicting lock`. **This is what the original v0.1.3 probe actually hit** — its attach string was `ducklake:.../catalog.ducklake` (no `sqlite:` prefix), i.e. DuckDB-backed, while being labeled "SQLite-backed."
- **SQLite-backed catalog** (`ducklake:sqlite:foo.sqlite`) — SQLite is built for multi-process access (shared read locks; brief exclusive lock only at commit). Reader + writer coexist.
- **PostgreSQL-backed** — also multi-process safe, but it's a server (breaks local-first).

**Consequence:** the Parquet bridge is **not required** for live Rill dashboards if the catalog is SQLite-backed. (The bridge can remain as a fallback, but it stops being the only option.)

## Proposed architecture

One DuckLake catalog per layer. Metadata (SQLite) stays local; data (Parquet) is local *or* on object storage — a one-line swap.

```
data/
  raw.sqlite     mart.sqlite          ← catalog metadata, always local (multi-process safe)
  raw_data/      mart_data/           ← Parquet — swap to s3://bucket/raw|mart/ via httpfs
```

Composed in one session:

```sql
INSTALL ducklake; LOAD ducklake; INSTALL sqlite; LOAD sqlite;
ATTACH 'ducklake:sqlite:data/raw.sqlite'  AS raw  (DATA_PATH 'data/raw_data/',  READ_ONLY);
ATTACH 'ducklake:sqlite:data/mart.sqlite' AS mart (DATA_PATH 'data/mart_data/');
-- a dbt model is just: CREATE TABLE mart.main.x AS SELECT ... FROM raw.main.y
```

### Validated dbt profile shape

dbt-duckdb 1.10.1's `Attachment` supports this natively (`path='ducklake:sqlite:…'`, `read_only`, `is_ducklake`, `options={data_path: …}` → emits `DATA_PATH '…'`):

```yaml
outputs:
  dev:
    type: duckdb
    path: ":memory:"
    extensions: [ducklake, sqlite, httpfs]
    attach:
      - path: "ducklake:sqlite:/abs/data/raw.sqlite"
        alias: raw
        read_only: true
        is_ducklake: true
      - path: "ducklake:sqlite:/abs/data/mart.sqlite"
        alias: mart
        is_ducklake: true
        options: { data_path: "/abs/data/mart_data/" }   # ← or "s3://bucket/mart/"
    # + a secrets: block for S3 creds when data_path goes remote
```

Models materialize with `{{ config(database='mart', schema='main') }}`; sources point at `database: raw`.

### How it maps to the current code

| Today | Becomes |
|---|---|
| `DatabaseConfig` — two fixed fields `raw` / `warehouse` (`src/tycoon/project.py:141`) | a named map of layers, each `{metadata path, data_path, read/write}` |
| `ingestion/ducklake_config.py` — **misnamed**: claims DuckLake, actually dumps plain Parquet via dlt's `filesystem` destination | a real per-layer `ATTACH 'ducklake:sqlite:…'` |
| `observability_dbt.attach_metadata_to_profiles` — emits `{path, alias, read_only}` | emit the DuckLake attach list above |
| dlt destination → `raw.duckdb` file (`config.raw_db`) | dlt writes into the `raw` DuckLake catalog |

## Relationship to prior decisions

- **#30 (layer-aware data model) is orthogonal and complementary.** #30 is about *logical* layers — classification flowing from dbt folders / dlt / Fivetran, surfaced in `tycoon data status`, with **no `layers:` block in `tycoon.yml`** (classification authority lives in the tools). This proposal is about *physical* storage. They compose cleanly: the logical layers map onto physical DuckLake catalogs. This proposal must **respect #30's "no classification config" principle** — the only new config here is physical (which catalog file / data_path backs each layer), and even that can stay convention-derived.
- **#31 (DuckLake backup) gets simpler and is the natural home.** Backup becomes "snapshot the catalog SQLite DB + sync the Parquet prefix," per layer — cleaner than today's opaque `.duckdb`-file copy. The DuckLake docs flag two edges to design around: run compaction/cleanup *before* a manual backup (they rewrite/remove data files), and transactions after a metadata snapshot aren't recoverable from it. The `backup.skip_raw` / `backup.layers` shape from the #31 discussion still applies.
- **Supersedes the Parquet-bridge rationale** in `analyze.md:68` (correct the doc), without necessarily deleting the bridge.

## Open questions / decisions needed

1. **Default vs opt-in.** Is layered-DuckLake *the* warehouse model, or an opt-in "lakehouse mode"? Given no users yet ([no-legacy stance]) there's no compat tax either way. **Recommendation:** prototype it *behind* the existing `raw`/`warehouse` abstraction so the CLI surface is unchanged, validate it carries the conference demo, then commit.
2. **Catalog backend default + graduation.** SQLite by default (local, multi-process). Document the swap to PostgreSQL / MotherDuck for multi-machine sharing — same Parquet, different metadata home. PostgreSQL catalog is explicitly **later**, not this work.
3. **Schema naming.** In spike 4, dbt turned `schema: main` into `main_main` (default `generate_schema_name` concatenates target + custom). The implementation must override `generate_schema_name` or set layer schemas deliberately.
4. **The one unproven leg: S3.** Every spike used a *local* `data_path`. `data_path: s3://…` is untested. MinIO would mean Docker (against local-first), so validate against a real bucket before claiming "S3-ready." **This is a prerequisite to the S3 phase.**

## Non-goals

- Running or emulating Apache Polaris / an Iceberg REST catalog locally (server + Docker; against local-first).
- DuckLake ↔ Iceberg interop / foreign engines (Spark/Trino/Snowflake on the same tables) — relevant only if multi-engine demand appears; out of scope here.
- PostgreSQL catalog backend (the multi-machine tier) — documented as the graduation path, not built now.

## Proposed phasing

- **Phase 0 (now, cheap):** file the issues below; correct `analyze.md:68`; rename/flag the misleading `ducklake_config.py`.
- **Phase 1:** validate `data_path: s3://…` against a real bucket (the one open risk).
- **Phase 2:** real `ducklake:sqlite:` ATTACH in `ducklake_config.py`, behind the existing `raw`/`warehouse` abstraction (opt-in).
- **Phase 3:** generalize `DatabaseConfig` to N layers; extend dbt profile generation; fix `generate_schema_name`.
- **Phase 4:** fold in backup (#31) and an optional Rill live-connector path (retire/relegate the Parquet bridge).

## Risks

- **DuckLake maturity** — younger than Iceberg/Delta; pin versions and keep the plain-`.duckdb` path available as a fallback.
- **Single-machine ceiling** — SQLite catalog is local; multi-machine needs the PostgreSQL tier (documented, not built).
- **S3 unproven** (see Phase 1).
- **dbt schema-name generation** quirk (see decisions #3).

## Issues (filed 2026-06-22)

1. **[#71][]** (`documentation`) — `analyze.md:68` mislabels the DuckLake lock as SQLite-backed; it's the DuckDB-file backend. Real Rill 0.86 reads a `ducklake:sqlite:` catalog during ingest with no lock. (Evidence: spikes 2 & 3.)
2. **[#72][]** (`tech-debt`) — `ingestion/ducklake_config.py` claims DuckLake but only dumps plain Parquet via dlt's `filesystem` destination — make it actually `ATTACH 'ducklake:sqlite:…'` or rename.
3. **[#73][]** (`enhancement`) — tracking issue for this physical-storage design (builds on the shipped #30, unblocks #31).

[#71]: https://github.com/Database-Tycoon/tycoon-cli/issues/71
[#72]: https://github.com/Database-Tycoon/tycoon-cli/issues/72
[#73]: https://github.com/Database-Tycoon/tycoon-cli/issues/73

[#30]: https://github.com/Database-Tycoon/tycoon-cli/issues/30
[#31]: https://github.com/Database-Tycoon/tycoon-cli/issues/31
