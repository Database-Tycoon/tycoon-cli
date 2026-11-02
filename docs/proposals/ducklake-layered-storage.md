# Proposal: native DuckLake layered storage (SQLite-catalog)

_Status (2026-11-02, checked against the `v0.2.4` branch): drafted 2026-06-21 from a spike investigation (4 spikes, all passed) and tracked in [#73][] (open). This is a storage-engine proposal. It revives the DuckLake track deferred since v0.1.7 ([#31][], open) with new evidence, and builds on, rather than replaces, the shipped layer-aware data model ([#30][], closed): #30 delivered the logical layers, this adds an optional physical backing for them._

_Where it sits in the plan: the ingestion rewrite's milestone M6 ([#87][]) owns the DuckLake surface. On 2026-10-20 the [MotherDuck proposal](https://github.com/Database-Tycoon/tycoon-cli/blob/v0.2.4/docs/proposals/motherduck-support.md) split the MotherDuck-only slice out to [#429][] and left DuckLake and object storage on #87, with [#122][] (`DuckLakeDestination`) as the implementing issue and [#350][] (DuckLake as the opinionated scaffold default) as the open wish-list question this proposal informs. Read this document as the design evidence feeding those issues, not as an independent track: the phasing in "Proposed phasing" below predates the milestone and its sequencing belongs to M6. The spike findings, the corrected lock model and the validated dbt profile shape stand as written. The docs correction the spikes called for has already shipped ([#71][], closed 2026-10-05 via PR #195, released in 0.2.0), and the `dbt-duckdb` version floor the profile shape needs is already pinned (see "Validated dbt profile shape")._

## TL;DR

Give each warehouse layer its own DuckLake catalog (SQLite metadata file + Parquet data), composed in one DuckDB session via `ATTACH`. dbt reads the `raw` catalog read-only and materializes into the `mart` catalog. Point each layer's `data_path` at `s3://...` and the same setup becomes a local-first lakehouse on object storage: no catalog server, no Docker. This is the credible local-first answer to "can we serve something like Polaris locally?": you don't serve a catalog, you open one.

The investigation also surfaced a factual error in shipped docs about why the Parquet bridge for Rill exists. That error is fixed: the Parquet-bridge note in `docs/commands/data/analyze.md` (line 70 on `v0.2.4`) now carries a dated correction that cites this proposal.

## How we got here

Started from two user questions: "how are we integrating with S3?" and "can we serve something like Polaris locally?" Following the thread led to DuckLake (catalog-as-a-database, only data on object storage), which raised the old objection that killed DuckLake for Rill in v0.1.3: an exclusive-lock conflict while ingesting. We spiked it to find out whether that objection still holds.

## What the spikes proved

All scripts live in the session scratchpad (throwaway) and are reproducible; verified against DuckDB 1.5.3, ducklake ext `e6a3bd0a`, Rill 0.86, dbt-duckdb 1.10.1 / dbt-core 1.11.8.

| # | Question | Result |
|---|---|---|
| 1 | Front DuckLake with Quack to dodge the lock? | No. **They don't compose.** Quack proxies a native `.duckdb`'s tables, but an `ATTACH`ed DuckLake catalog is invisible to Quack clients. Treat Quack and DuckLake as orthogonal. |
| 2 | Which catalog backend actually locks? | **DuckDB-backed `.ducklake` locks** (process-exclusive file lock); **SQLite-backed does not**: a held-open READ_ONLY reader plus a continuous writer ran clean and the reader saw new snapshots. Deterministic across runs. |
| 3 | Does the real Rill binary survive ingest on a SQLite catalog? | Yes. A Rill project with `olap_connector: lake` on a `ducklake:sqlite:` catalog reconciled and served live-growing aggregation counts (100 to 36,100) during ingest, with 0 lock conflicts. |
| 4 | Does dbt work raw-catalog to mart-catalog end-to-end? | Yes. `dbt run` read a READ_ONLY `raw` DuckLake catalog and materialized a model into a `mart` DuckLake catalog (3 snapshots, correct data) purely via `profiles.yml` `attach:`. |

## The corrected lock model (now reflected in `analyze.md`)

Until PR #195, `docs/commands/data/analyze.md` said the Parquet bridge exists because *"SQLite-backed DuckLake catalogs hold an exclusive lock that breaks Rill-while-ingesting."* That was wrong on the backend. The lock is a property of the catalog metadata database, not of DuckLake or of SQLite:

- **DuckDB-backed catalog** (`ducklake:foo.ducklake`, the default): a `.ducklake` file *is* a DuckDB database, and DuckDB locks a database file to one process. Two processes means `Conflicting lock`. This is what the original v0.1.3 probe actually hit. Its attach string was `ducklake:.../catalog.ducklake` (no `sqlite:` prefix), so DuckDB-backed, while being labeled "SQLite-backed."
- **SQLite-backed catalog** (`ducklake:sqlite:foo.sqlite`): SQLite is built for multi-process access (shared read locks; brief exclusive lock only at commit). Reader and writer coexist.
- **PostgreSQL-backed**: also multi-process safe, but it's a server (breaks local-first).

**Consequence:** the Parquet bridge is not required for live Rill dashboards if the catalog is SQLite-backed. The bridge can remain as a fallback, but it stops being the only option. `analyze.md` now says exactly this.

## Proposed architecture

One DuckLake catalog per layer. Metadata (SQLite) stays local; data (Parquet) is local *or* on object storage, a one-line swap.

```
data/
  raw.sqlite     mart.sqlite          <- catalog metadata, always local (multi-process safe)
  raw_data/      mart_data/           <- Parquet; swap to s3://bucket/raw|mart/ via httpfs
```

Composed in one session:

```sql
INSTALL ducklake; LOAD ducklake; INSTALL sqlite; LOAD sqlite;
ATTACH 'ducklake:sqlite:data/raw.sqlite'  AS raw  (DATA_PATH 'data/raw_data/',  READ_ONLY);
ATTACH 'ducklake:sqlite:data/mart.sqlite' AS mart (DATA_PATH 'data/mart_data/');
-- a dbt model is just: CREATE TABLE mart.main.x AS SELECT ... FROM raw.main.y
```

### Validated dbt profile shape

dbt-duckdb 1.10.1's `Attachment` supports this natively (`path='ducklake:sqlite:...'`, `read_only`, `is_ducklake`, `options={data_path: ...}`, which emits `DATA_PATH '...'`):

```yaml
outputs:
  dev:
    type: duckdb
    path: ":memory:"
    schema: main
    extensions: [ducklake, sqlite, httpfs]
    attach:
      - path: "ducklake:sqlite:/abs/data/raw.sqlite"
        alias: raw
        read_only: true
        is_ducklake: true
      - path: "ducklake:sqlite:/abs/data/mart.sqlite"
        alias: mart
        is_ducklake: true
        options: { data_path: "/abs/data/mart_data/" }   # or "s3://bucket/mart/"
    # + a secrets: block for S3 creds when data_path goes remote
```

Models materialize with `{{ config(database='mart', schema='main') }}`; sources point at `database: raw`.

> **Why `raw` omits `data_path` but `mart` includes it.** A DuckLake catalog stores its `data_path` in metadata at creation time, so re-attaching an *existing* catalog doesn't need it. `raw` is pre-created by ingestion (dlt), so it re-attaches with just `read_only: true`; `mart` is created here, so it specifies `data_path`. Verified: re-attaching an existing `ducklake:sqlite:` catalog with no `data_path` resolves and reads correctly.

> **Version floor: native in dbt-duckdb 1.10 and later, not older.** The `is_ducklake` and `options` fields on `attach:` are declared on dbt-duckdb's `Attachment` model as of 1.10 and were exercised end-to-end on 1.10.1 in spike 4 (a real `dbt run` materialized into the mart catalog). On older dbt-duckdb the `Attachment` model rejects them (`extra fields not permitted`) and you'd need a custom `plugins:` adapter instead. The floor this asks for is already in place: `pyproject.toml` on `v0.2.4` pins `dbt-duckdb==1.10.1` exactly, so the implementation can rely on the syntax without adding a constraint.

### How it maps to the current code

Checked against `v0.2.4` on 2026-11-02.

| Today | Becomes |
|---|---|
| `DatabaseConfig`: two fixed fields `raw` / `warehouse` (`src/tycoon/project.py`, lines 286 to 290) | a named map of layers, each `{metadata path, data_path, read/write}` |
| `ingestion/ducklake_config.py`: misnamed, claims DuckLake but dumps plain Parquet via dlt's `filesystem` destination ([#72][], open; the [MotherDuck proposal](https://github.com/Database-Tycoon/tycoon-cli/blob/v0.2.4/docs/proposals/motherduck-support.md) has it deleted alongside #430, with no callers today) | a real per-layer `ATTACH 'ducklake:sqlite:...'`, which is #122's `DuckLakeDestination` |
| `observability_dbt.attach_metadata_to_profiles` (`src/tycoon/scaffolding/observability_dbt.py`, line 183): emits `{path, alias, read_only}` | emit the DuckLake attach list above |
| dlt destination writes a `raw.duckdb` file (`config.raw_db`) | dlt writes into the `raw` DuckLake catalog |

## Relationship to prior decisions

- **#30 (layer-aware data model) is orthogonal and complementary.** #30 is about *logical* layers: classification flowing from dbt folders / dlt / Fivetran, surfaced in `tycoon data status`, with no `layers:` block in `tycoon.yml` (classification authority lives in the tools). This proposal is about *physical* storage. They compose cleanly: the logical layers map onto physical DuckLake catalogs. This proposal must respect #30's "no classification config" principle. The only new config here is physical (which catalog file / data_path backs each layer), and even that can stay convention-derived.
- **#31 (DuckLake backup) gets simpler and is the natural home.** Backup becomes "snapshot the catalog SQLite DB + sync the Parquet prefix," per layer, which is cleaner than today's opaque `.duckdb`-file copy. The DuckLake docs flag two edges to design around: run compaction/cleanup *before* a manual backup (they rewrite/remove data files), and transactions after a metadata snapshot aren't recoverable from it. The `backup.skip_raw` / `backup.layers` shape from the #31 discussion still applies.
- **The Parquet-bridge rationale in `analyze.md` is corrected** (PR #195), without deleting the bridge.
- **#429 (MotherDuck end to end) is the sibling slice.** It moves raw, warehouse and metadata to `md:` catalogs behind `register warehouse --type motherduck`. The destination abstraction it introduces (#430 for raw ingestion) is the seam a `DuckLakeDestination` (#122) plugs into, so sequencing DuckLake after the MotherDuck phases avoids building the same routing twice.
- **#350 (DuckLake as the scaffold default)** is the open question of whether this becomes the default warehouse model. The "Default vs opt-in" recommendation below is this proposal's input to that decision.

## Open questions / decisions needed

1. **Default vs opt-in.** Is layered-DuckLake *the* warehouse model, or an opt-in "lakehouse mode"? Given no users yet (the project's no-legacy stance) there's no compat tax either way. **Recommendation:** prototype it *behind* the existing `raw`/`warehouse` abstraction so the CLI surface is unchanged, validate it carries the conference demo, then commit. #350 tracks the default question.
2. **Catalog backend default + graduation.** SQLite by default (local, multi-process). Document the swap to PostgreSQL / MotherDuck for multi-machine sharing: same Parquet, different metadata home. PostgreSQL catalog is explicitly later, not this work.
3. **Schema naming.** In spike 4, dbt turned `schema: main` into `main_main` (default `generate_schema_name` concatenates target + custom). The implementation must override `generate_schema_name` or set layer schemas deliberately.
4. **The one unproven leg: S3.** Every spike used a *local* `data_path`. `data_path: s3://...` is untested. MinIO would mean Docker (against local-first), so validate against a real bucket before claiming "S3-ready." This is a prerequisite to the S3 phase, and now a question for #124 (`ObjectStorageDestination`) as much as for this document.

## Non-goals

- Running or emulating Apache Polaris / an Iceberg REST catalog locally (server + Docker; against local-first).
- DuckLake to Iceberg interop / foreign engines (Spark/Trino/Snowflake on the same tables). Relevant only if multi-engine demand appears; out of scope here.
- PostgreSQL catalog backend (the multi-machine tier). Documented as the graduation path, not built now.

## Proposed phasing

Written 2026-06-21. M6 (#87) sets the actual order; this is the dependency shape the spikes suggest.

- **Phase 0 (done):** the three issues below were filed on 2026-06-22; `analyze.md` was corrected by PR #195 (0.2.0). The one Phase 0 item still open is #72, the misleading `ducklake_config.py`, which the MotherDuck roadmap deletes rather than renames.
- **Phase 1:** validate `data_path: s3://...` against a real bucket (the one open risk).
- **Phase 2:** a real `ducklake:sqlite:` ATTACH as a destination (#122), behind the existing `raw`/`warehouse` abstraction (opt-in).
- **Phase 3:** generalize `DatabaseConfig` to N layers; extend dbt profile generation; fix `generate_schema_name`.
- **Phase 4:** fold in backup (#31) and an optional Rill live-connector path (retire/relegate the Parquet bridge).

## Risks

- **DuckLake maturity.** Younger than Iceberg/Delta; pin versions and keep the plain-`.duckdb` path available as a fallback.
- **Single-machine ceiling.** SQLite catalog is local; multi-machine needs the PostgreSQL tier (documented, not built).
- **S3 unproven** (see Phase 1).
- **dbt schema-name generation** quirk (see decisions #3).

## Issues (filed 2026-06-22)

1. **[#71][]** (`documentation`, closed 2026-10-05 via PR #195): `analyze.md` mislabeled the DuckLake lock as SQLite-backed; it's the DuckDB-file backend. Real Rill 0.86 reads a `ducklake:sqlite:` catalog during ingest with no lock. (Evidence: spikes 2 and 3.)
2. **[#72][]** (`tech-debt`, open): `ingestion/ducklake_config.py` claims DuckLake but only dumps plain Parquet via dlt's `filesystem` destination. Make it actually `ATTACH 'ducklake:sqlite:...'`, rename it, or delete it (the MotherDuck roadmap chooses deletion).
3. **[#73][]** (`enhancement`, open): tracking issue for this physical-storage design (builds on the shipped #30, unblocks #31).

[#71]: https://github.com/Database-Tycoon/tycoon-cli/issues/71
[#72]: https://github.com/Database-Tycoon/tycoon-cli/issues/72
[#73]: https://github.com/Database-Tycoon/tycoon-cli/issues/73

[#30]: https://github.com/Database-Tycoon/tycoon-cli/issues/30
[#31]: https://github.com/Database-Tycoon/tycoon-cli/issues/31
[#87]: https://github.com/Database-Tycoon/tycoon-cli/issues/87
[#122]: https://github.com/Database-Tycoon/tycoon-cli/issues/122
[#350]: https://github.com/Database-Tycoon/tycoon-cli/issues/350
[#429]: https://github.com/Database-Tycoon/tycoon-cli/issues/429
