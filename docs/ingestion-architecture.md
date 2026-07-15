# Ingestion Architecture

## What you should walk away with

- Ingestion in tycoon is becoming tool-agnostic. dlt is the default, but Fivetran, Airbyte, and Estuary are all first-class options on the same path.
- Every source run will flow through a single protocol (`Runtime.run()`). Adding a new ingestion tool means implementing that protocol — nothing else changes.
- The same is true for destinations. MotherDuck and DuckLake plug in as implementations. Core and CLI don't change.
- The design test for every milestone is simple: `git diff main src/tycoon/core/` is empty.

---

## The problem with the current design

Today, ingestion is tightly coupled to dlt. `runner.py` calls dlt directly and returns dlt types (`Pipeline`, `LoadInfo`) into the CLI layer. Adding a source means editing three files: `catalog.py`, `source_manager.py`, and the `_SHIMS` dict. The `config` singleton is imported by 25+ files. There are no protocols, so there's no way to swap anything out without touching core logic.

This works fine for the dlt-only case. It breaks the moment you want to support Fivetran or MotherDuck without forking the entire command layer.

---

## The architecture we're building toward

```
tycoon.yml
  └─ runtimes:          ← which Runtime handles each source
  └─ metadata:          ← which MetadataBackend to write events to

tycoon data sources run <id>
  └─ Runtime.run()      ← dispatch through the protocol
       └─ emit events
            └─ MetadataBackend.record()   ← DuckDBFileBackend, MotherDuckMetadataBackend, ...

tycoon data status / history
  └─ MetadataBackend.query()   ← always reads from the backend, never raw dlt tables
```

Three protocols carry the whole thing:

**Runtime Protocol** — handles a source run end to end. Emits structured events (`RunCompleted`, `DbtRunCompleted`, etc.) that the MetadataBackend records. Any ingestion tool that can implement `run()` + `observe()` becomes a first-class tycoon source.

**Destination Protocol** — describes where data lands. `build_destination()` returns a Destination; the Runtime uses it without knowing what's underneath. DuckDB (local file), MotherDuck, DuckLake, and object storage are all Destination implementations.

**MetadataBackend Protocol** — where run history lives. `DuckDBFileBackend` is the default (`.tycoon/metadata.duckdb`). `MotherDuckMetadataBackend` stores it in the cloud. `tycoon data status` and `tycoon data history` read from whatever backend is configured — never from raw dlt tables.

---

## Runtime implementations

| Runtime | What it handles | How you attach it |
|---|---|---|
| `DltManagedRuntime` | tycoon-managed dlt sources (the default) | `tycoon attach dlt` |
| `DltProjectRuntime` tier 1 | your own dlt project, run as a subprocess | `tycoon attach dlt-project <path>` |
| `DltProjectRuntime` tier 2 | your project with a `tycoon_src.py` shim for status/history | `tycoon sources upgrade <id>` |
| `FivetranRuntime` | Fivetran connections via the existing `fivetran_client.py` | `tycoon attach fivetran` |
| `AirbyteRuntime` | Airbyte (skeleton in M7) | — |
| `EstuaryRuntime` | Estuary (skeleton in M7) | — |

The tier model for dlt projects is the practical answer to "I already have a dlt pipeline." Tier 1 is zero-friction — tycoon just runs it as a black box. Tier 2 opts into status and history by adding a small shim that emits events through the protocol. You upgrade when you want the observability, not before.

---

## Source catalog

Today: a hardcoded dict with 8 entries in `catalog.py`. Adding a source requires coordinated edits across three files.

Target: a `verified_sources.json` manifest covering ~40 dlt verified sources, loaded at runtime. `SourceFactory` handles config collection, handle building, and install checking for any source without per-source branching. `tycoon data sources catalog` reads from the manifest. `catalog.py` is deleted when M3 closes. (#84)

---

## How tycoon.yml evolves

Current shape:
```yaml
sources:
  my-github:
    type: github
    schema: raw_github
```

Target shape adds `runtimes:` and `metadata:` at the top level:
```yaml
runtimes:
  default: dlt-managed

metadata:
  backend: duckdb-file       # or motherduck

sources:
  my-github:
    type: github
    runtime_id: default
    schema: raw_github
```

Every source declares its `runtime_id`. The config singleton (`from tycoon.config import config`) is replaced with explicit `load_project()` injection at the command boundary. (#83)

---

## Milestone map

| # | Milestone | Status |
|---|---|---|
| [#82](https://github.com/Database-Tycoon/tycoon-cli/issues/82) | MetadataBackend protocol + DuckDBFileBackend | ✅ Done |
| [#83](https://github.com/Database-Tycoon/tycoon-cli/issues/83) | tycoon.yml schema + config singleton replacement | In progress |
| [#84](https://github.com/Database-Tycoon/tycoon-cli/issues/84) | Source catalog — JSON manifest + SourceFactory | In progress |
| [#85](https://github.com/Database-Tycoon/tycoon-cli/issues/85) | Runtime Protocol + DltManagedRuntime (`runner.py` retirement) | Upcoming |
| [#86](https://github.com/Database-Tycoon/tycoon-cli/issues/86) | DltProjectRuntime — tier 1 + tier 2 | Upcoming |
| [#87](https://github.com/Database-Tycoon/tycoon-cli/issues/87) | Alternative destinations (MotherDuck, DuckLake, object storage) | Upcoming |
| [#88](https://github.com/Database-Tycoon/tycoon-cli/issues/88) | Alternative ingestion modes (Fivetran, Airbyte, Estuary) | Upcoming |

The parent issue tracking all of this is [#81](https://github.com/Database-Tycoon/tycoon-cli/issues/81).

---

## What closes this project

From [#81](https://github.com/Database-Tycoon/tycoon-cli/issues/81):

- `runner.py` is deleted
- `tycoon data sources run` routes through `Runtime.run()`
- `tycoon data status` reads exclusively from the MetadataBackend
- `tycoon catalog` is driven by the JSON manifest
- The global `config` singleton is gone from the ingestion path
- All dlt-specific logic lives behind `DltManagedRuntime`
- `git diff main src/tycoon/core/` is empty after every milestone
