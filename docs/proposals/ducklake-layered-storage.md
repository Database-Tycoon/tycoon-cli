# Decision record: DuckLake needs a SQLite-backed catalog

_Status (2026-11-02, checked against the `v0.2.4` branch): re-scoped from the June 2026 per-layer storage proposal. The architecture and phasing that used to live here now belong to milestone M6 ([#87][]), with [#122][] (`DuckLakeDestination`) as the implementing issue and [#350][] as the scaffold-default wish. This page keeps only what those issues need: the spike evidence, the lock model, and the validated dbt profile shape. The tracking issue is [#73][]._

## What this constrains

Whoever implements `DuckLakeDestination` (#122) should treat these as fixed:

1. **The catalog must be SQLite-backed.** The connection string tycoon generates defaults to `ducklake:sqlite:<path>`, never the bare `ducklake:<path>.ducklake` form. The DuckDB-backed default locks the catalog file to one process, which is the v0.1.3 conflict that made Rill unusable during ingest.
2. **dbt reads DuckLake through dbt-duckdb's native `attach:` block.** The shape below is validated on dbt-duckdb 1.10.1, the exact version `pyproject.toml` pins on `v0.2.4`. No custom plugin is needed.
3. **Quack and DuckLake do not compose.** `tycoon start` can keep its Quack path for the native `.duckdb` warehouse, but an attached DuckLake catalog is invisible to Quack clients. Do not plan on Quack as the live-reader story for a DuckLake target.

## What the spikes proved

Four spikes on 2026-06-21, verified against DuckDB 1.5.3, ducklake extension `e6a3bd0a`, Rill 0.86, dbt-duckdb 1.10.1 with dbt-core 1.11.8.

| # | Question | Result |
|---|---|---|
| 1 | Front DuckLake with Quack to dodge the lock? | No. They do not compose. Quack proxies a native `.duckdb`'s tables; an attached DuckLake catalog is invisible to Quack clients. |
| 2 | Which catalog backend actually locks? | The DuckDB-backed `.ducklake` file locks per process. The SQLite-backed catalog does not: a held-open `READ_ONLY` reader plus a continuous writer ran clean and the reader saw new snapshots. |
| 3 | Does the real Rill binary survive ingest on a SQLite catalog? | Yes. A Rill project on a `ducklake:sqlite:` catalog served live-growing counts (100 to 36,100) during ingest with 0 lock conflicts. |
| 4 | Does dbt work catalog-to-catalog? | Yes. `dbt run` read a `READ_ONLY` DuckLake catalog and materialized into a second DuckLake catalog (3 snapshots, correct data) purely via `profiles.yml` `attach:`. |

## The lock model

The lock is a property of the catalog metadata database, not of DuckLake or of SQLite.

- **DuckDB-backed catalog** (`ducklake:foo.ducklake`, the extension's default): a `.ducklake` file is a DuckDB database, and DuckDB locks a database file to one process. Two processes means `Conflicting lock`. This is what the original v0.1.3 probe hit. Its attach string had no `sqlite:` prefix, so it was DuckDB-backed while being labelled "SQLite-backed".
- **SQLite-backed catalog** (`ducklake:sqlite:foo.sqlite`): SQLite is built for multi-process access. Reader and writer coexist.
- **PostgreSQL-backed**: also multi-process safe, but it is a server, which breaks local-first.

The docs correction this called for already shipped: `docs/commands/data/analyze.md` was fixed by PR #195 in 0.2.0 ([#71][], closed). The Parquet bridge for Rill stays as a fallback but is no longer the only option.

## Validated dbt profile shape

dbt-duckdb 1.10's `Attachment` model accepts `is_ducklake` and `options`, which emit `DATA_PATH '...'`. Older dbt-duckdb rejects them with `extra fields not permitted`.

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
```

Models materialize with `{{ config(database='mart', schema='main') }}`; sources point at `database: raw`.

Two details the implementation must handle:

- A DuckLake catalog stores its `data_path` at creation, so re-attaching an existing catalog omits it. Only the catalog being created here (`mart`) specifies `data_path`.
- Default `generate_schema_name` turned `schema: main` into `main_main` in spike 4. Override it or set layer schemas deliberately.

## Still unproven

Every spike used a local `data_path`. `data_path: s3://...` is untested and belongs to [#124][] (`ObjectStorageDestination`) as much as to #122. Validate against a real bucket before claiming S3 support; MinIO would mean Docker, which is against local-first.

## Where the rest went

- Per-layer catalogs as the warehouse model: one line on [#350][], the scaffold wish list.
- `ingestion/ducklake_config.py`, which claims DuckLake but writes plain Parquet: [#72][], deleted by the MotherDuck roadmap.
- Layer-granular backup: [#31][].

[#31]: https://github.com/Database-Tycoon/tycoon-cli/issues/31
[#71]: https://github.com/Database-Tycoon/tycoon-cli/issues/71
[#72]: https://github.com/Database-Tycoon/tycoon-cli/issues/72
[#73]: https://github.com/Database-Tycoon/tycoon-cli/issues/73
[#87]: https://github.com/Database-Tycoon/tycoon-cli/issues/87
[#122]: https://github.com/Database-Tycoon/tycoon-cli/issues/122
[#124]: https://github.com/Database-Tycoon/tycoon-cli/issues/124
[#350]: https://github.com/Database-Tycoon/tycoon-cli/issues/350
