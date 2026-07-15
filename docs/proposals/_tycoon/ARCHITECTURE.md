# Tycoon CLI Architecture

> **Naming note.** This document was originally drafted using `dbty` / `dbty-cli` as shorthand for **Database Tycoon** and the Tycoon CLI. Names are now reconciled: the tool is **tycoon** (CLI command), `src/tycoon/` (package), `tycoon.yml` (manifest), `.tycoon/` (metadata dir).

> The structural counterpart to [MANIFESTO.md](./MANIFESTO.md). The manifesto says *why* and *what shape*. This document says *how it is built* — from the system boundary down to the source tree.
>
> Organised by the [C4 model](https://c4model.com/): four altitudes of zoom, each answering a different question. Diagrams are ASCII-first so the document is readable cold, in a terminal, by a human or an agent.

---

## Architectural commitments

These hold across every level. If a design choice violates one of these, it is wrong even if it works.

1. **Abstractions and consistent APIs are non-negotiable.** Every compartment in §7 of the manifesto exposes the same shape of interface. Every concrete backing — runtime, metadata store, destination, catalog source — slots in as an adapter behind that interface. New adapters cause zero core changes.
2. **The cockpit default principle holds in code too.** Every adapter point has a default backing that the beginner gets for free, and a pluggable seam where the user attaches their own. This is true for Runtime (default: dlt-native), for Destination (default: local DuckDB), for Metadata (default: local DuckDB file). The architecture must make the default path and the attached path indistinguishable from the caller's point of view.
3. **The model is canonical, not the rendering.** No Surface owns truth. The CLI is one renderer of the underlying model. The metadata store *is* the model. Every command resolves to "read or write the model"; the rendering is a thin transform on top.
4. **No private doors.** A future adapter (sling, Airbyte, dbt-cloud, MotherDuck-as-metadata-backing) must reach what it needs through the same interface the POC adapters use. Special cases are bugs.
5. **Control-plane shape, always.** tycoon addresses; it does not absorb. If a design choice has us *owning* something the user already has (their warehouse, their auth, their dbt project, their scheduler), it is platform-drift and we reject it. See manifesto §1.
6. **Scaffolding is silent, minimum, create-only, once.** When `attach` scaffolds, it writes the minimum, in the user's idiom, into empty space, exactly once. It never touches existing files. It is never exposed as its own verb. See manifesto §9.

---

## Level 1 — System Context

> Who and what does tycoon interact with? Where is the boundary?

### Actors and external systems

```
                        ┌─────────────────┐
                        │   User          │
                        │   (engineer,    │
                        │    analyst)     │
                        └────────┬────────┘
                                 │  CLI invocations
                                 ▼
                        ┌─────────────────────┐
                        │                     │      ┌─────────────────┐
        ┌───────────────│        tycoon         │◀────▶│ Analytics agent │
        │               │   (control plane)   │      │  (LLM client    │
        │               │                     │      │   via MCP/JSON) │
        │               └─────────────────────┘      └─────────────────┘
        │                  │     │     │     │
        │                  ▼     ▼     ▼     ▼
        │           ┌────────┐ ┌──────────┐ ┌────────────┐ ┌──────────┐
        │           │  dlt   │ │ Fivetran │ │  User's    │ │  User's  │
        │           │ (lib)  │ │  (API)   │ │  dlt       │ │  dbt     │
        │           │        │ │          │ │  project   │ │  project │
        │           └────┬───┘ └────┬─────┘ └─────┬──────┘ └─────┬────┘
        │                │          │             │              │
        │                │          │             │   ┌────────────┐ ┌────────────────┐
        │                │          │             │   │  User's    │ │  User's        │
        │                │          │             │   │  Rill /    │ │  Semantic      │
        │                │          │             │   │  BI tool   │ │  engine (post- │
        │                │          │             │   │            │ │  POC, optional)│
        │                │          │             │   └─────┬──────┘ └────────┬───────┘
        │                │          │             │         │                 │
        │                └──────────┴──────┬──────┴─────────┴─────────────────┘
        │                                  ▼
        │                       ┌────────────────────┐
        └──────────────────────▶│   Destination      │
                                │ (DuckDB / Snow /   │
                                │  BigQuery / ...)   │
                                └────────────────────┘
```

### What tycoon owns

- The coordination and observation layer between actors above.
- A small amount of bookkeeping (metadata events, source declarations, catalog snapshots, capability state).
- The Surfaces: CLI today, JSON output, MCP / TUI / web later — all renderings of the same model.

### What tycoon does not own (BYOS boundary)

- **The ingestion runtime.** dlt is a library tycoon calls; Fivetran is a service tycoon talks to.
- **The user's dlt project or dbt project.** tycoon wraps them via entrypoint; they remain authored, version-controlled, and owned by the user.
- **The Destination.** tycoon connects to it; it does not provision, host, or replatform it.
- **Authentication for the user's stack.** OAuth tokens, API keys, warehouse credentials — held by the user (env vars, their secret manager, the runtime's own config), referenced by tycoon.
- **A long-lived daemon process.** No background tycoon service. Every command is invocation-scoped. See Level 2.

### The boundary in one sentence

tycoon is the smallest piece of software that can answer "what is in your stack, what state is it in, and what can I do with it?" — without owning any of the stack itself.

---

## Level 2 — Containers

> What actually runs? Processes, libraries, data stores.

### Process model: single-process, invocation-scoped

The POC is one Python CLI process, invoked per command, terminated when the command returns. No daemon. No background scheduler. No long-lived server.

This is a deliberate choice. A daemon is platform-shape: it implies tycoon *runs the show*. An invocation-scoped CLI is control-plane-shape: tycoon acts when asked, observes what's there, writes its bookkeeping, exits.

```
   ┌─────────────────────────────────────────────────────────────┐
   │                  tycoon CLI process (per invocation)          │
   │                                                             │
   │   ┌─────────────┐    ┌──────────────┐   ┌───────────────┐   │
   │   │  Command    │───▶│  Core model  │──▶│   Surface     │   │
   │   │  dispatcher │    │  (compart-   │   │   renderer    │   │
   │   │             │    │   ments)     │   │  (CLI / JSON) │   │
   │   └─────────────┘    └──────┬───────┘   └───────────────┘   │
   │                             │                               │
   │                             ▼                               │
   │                  ┌────────────────────┐                     │
   │                  │  Adapter layer     │                     │
   │                  │  ─ Runtime         │                     │
   │                  │  ─ Destination     │                     │
   │                  │  ─ Metadata store  │                     │
   │                  │  ─ Catalog source  │                     │
   │                  └──┬───────┬─────┬───┘                     │
   └─────────────────────│───────│─────│─────────────────────────┘
                         │       │     │
                         ▼       ▼     ▼
                 (external systems and local files)
```

### Data stores

#### Metadata backend (substrate, abstract)

Metadata is an **abstract substrate** with a pluggable backing. The Metadata API is the same regardless of where events and snapshots live.

| Backing | Status | Notes |
|---|---|---|
| Local DuckDB file (`.tycoon/metadata.duckdb`) | **Default, POC.** | Cockpit default. tycoon's own bookkeeping; not the user's data. Lives in the project directory next to the tycoon manifest. |
| User's Destination (managed schema, e.g. `_tycoon_metadata.*`) | Designed-for, post-POC. | The "graduate to your warehouse" path. Attached explicitly; the user opts in. Same API, different driver. |

The Metadata API is designed against the second case from day one and *implemented* against the first. This is the architectural commitment that prevents a future rewrite: the contract holds for both backings; the POC just ships one driver.

#### Project manifest

A small declarative file at the project root (`tycoon.yml`) holding:

- attached Runtimes
- attached Destinations
- declared Sources (with Runtime binding and handle)
- environment profiles (Source→Runtime/Destination rebindings)
- the metadata backing choice (defaults to local file)

This is *configuration*, not *state*. State lives in the Metadata backend. The manifest is what the user (or `tycoon attach`) edits; it is human-readable and agent-editable.

#### Credentials

Not owned by tycoon. References live in the manifest as env-var interpolations (`${FIVETRAN_API_KEY}`), TOML paths (`.dlt/secrets.toml`), or runtime-native handles. tycoon does not store secrets, and the architecture explicitly forbids a "tycoon secret store" — that would be platform-shape (see manifesto §6).

### External systems, summarized

- **dlt** — Python library imported in-process. Runs synchronously inside the CLI invocation.
- **Fivetran** — REST API. tycoon makes HTTP calls; nothing executes locally.
- **User's dlt project** — invoked via entrypoint. May run in-process or in a subprocess for isolation (open question, deferred to Level 3).
- **User's dbt project** — invoked as a subprocess (`dbt run ...`). Always out-of-process.
- **User's Rill project** (POC Presentation adapter) — invoked as a subprocess (`rill build` / `rill refresh ...`). Reads from the same Destination dbt writes to.
- **User's semantic engine** (post-POC) — dbt MetricFlow, Cube, Malloy, etc. Adapter-specific; either subprocess invocation or HTTP to a running engine.
- **Destination** — accessed via the relevant SDK/driver (duckdb, snowflake-connector-python, etc.).

### What is explicitly not a container

- No web server.
- No background worker.
- No message queue.
- No managed service of any kind.

These belong to platforms. If a feature in the future seems to need one, the architecture review starts with "can we model this as an invocation instead?"

---

## Level 3 — Components

> Inside the CLI process, what are the modules and what does each do?

This level translates the §7 compartments of the manifesto into code-level components, plus the supporting modules that make them work.

### The compartment-to-component map

| Manifesto compartment | Primary component | Responsibility |
|---|---|---|
| Source | `core.source` | Domain model of a Source: identity, runtime binding, handle, declared capabilities. Pure data + validation. |
| Runtime | `core.runtime` + `runtimes/*` adapters | The Runtime interface plus one concrete adapter per backing (dlt, fivetran, dlt-project). |
| Destination | `core.destination` + `destinations/*` adapters | The Destination interface plus drivers (duckdb default; others pluggable). |
| Transformation | `core.transformation` + `transformations/*` adapters | dbt-project wrapper for the POC. Runtime-shaped from day one so sqlmesh / dbt-cloud slot in as new adapter files. |
| Semantics | `core.semantics` + `semantics/*` adapters | **Post-POC.** The Semantics interface plus pluggable engines (dbt MetricFlow, Cube, Malloy, ...). Folder exists empty during POC so the dependency graph is honest. |
| Presentation | `core.presentation` + `presentations/*` adapters | The Presentation interface plus pluggable tools. **Rill is the POC adapter**; Metabase / Superset / Lightdash / Hex follow. |
| Catalog | `core.catalog` | Federated query layer over Runtime / Transformation / Semantics / Presentation offers and Project declarations. Cache-aware. |
| Metadata | `core.metadata` + `metadata_backends/*` | The Metadata API (events, snapshots, queries). DuckDB-file backing for POC; warehouse backing designed-for. |
| Surface | `surfaces/cli` + `surfaces/json` | CLI (Typer) and structured-JSON renderers over the core model. Future: `surfaces/mcp`, `surfaces/tui`. |

Supporting components (no manifesto compartment, but load-bearing):

| Component | Responsibility |
|---|---|
| `core.project` | Reads/writes the project manifest. Resolves environment bindings. The "what is configured" entrypoint. |
| `core.capabilities` | The capability model itself — what `can_run`, `can_backfill`, `can_introspect_schema`, etc. mean, and how adapters declare them. |
| `core.events` | The Metadata event schema. Every action emits one of these. Adapters do not invent event shapes. |
| `core.identifiers` | Naming, IDs, qualified references (e.g. `source:stripe@fivetran`). Stable string forms an agent can use as keys. |
| `core.scaffold` + `scaffolds/*` | The Scaffolder interface and per-target scaffolders. Invoked by `attach` on greenfield. Strictly create-only, never user-facing as its own verb. |
| `commands/*` | Command implementations (`add`, `list`, `attach`, `run`, `status`, ...). Thin: they parse intent, call the core, hand the result to a Surface. |

### Adapter interface shapes (sketch, not final)

The architecture's heaviest commitment is the adapter contracts. Each is a Python Protocol (or ABC) with a small surface; concrete backings implement it. Note the symmetry between Runtime, Transformation, Semantics, and Presentation — they share the *shape* (`capabilities`, `catalog_offers`, `introspect`, `run`, `observe`) even though they point at different downstream artifacts.

```
Runtime          (Source-side execution)
  .id                              -> str
  .capabilities(source) -> set[Capability]
  .catalog_offers()     -> Iterable[CatalogOffer]      # what this Runtime can produce
  .introspect(source)   -> SchemaSnapshot               # current schema, freshness
  .run(source, opts)    -> RunHandle                    # raises CapabilityError if not granted
  .observe(run_handle)  -> Iterable[RunEvent]           # stream of structured events
  .read_state()         -> Iterable[RunRecord]          # historical runs (Fivetran API, dlt _dlt_loads)

TransformationAdapter   (warehouse → warehouse)
  .id                              -> str
  .capabilities(model)  -> set[Capability]
  .catalog_offers()     -> Iterable[ModelOffer]         # models the project exposes
  .introspect(model)    -> ModelSnapshot                # lineage upstream + downstream, freshness
  .run(model, opts)     -> RunHandle
  .observe(run_handle)  -> Iterable[RunEvent]

SemanticsAdapter (post-POC; warehouse → meaning)
  .id                              -> str
  .capabilities(metric) -> set[Capability]
  .catalog_offers()     -> Iterable[MetricOffer]        # metrics/dimensions/entities the engine exposes
  .introspect(metric)   -> MetricSnapshot               # upstream models, dimensions, joins
  .query(metric, opts)  -> QueryResult                  # the actual metric value(s)
  .observe(query_h)     -> Iterable[QueryEvent]

PresentationAdapter   (warehouse → consumed view)
  .id                              -> str
  .capabilities(view)   -> set[Capability]
  .catalog_offers()     -> Iterable[ViewOffer]          # dashboards / reports / notebooks
  .introspect(view)     -> ViewSnapshot                 # upstream models / metrics, freshness, deploy status
  .run(view, opts)      -> RunHandle                    # build / refresh / deploy
  .observe(run_handle)  -> Iterable[RunEvent]

Destination
  .id                              -> str
  .ping()                          -> HealthStatus
  .read(query)          -> Rows                         # SELECT path
  .write(table, rows)   -> WriteResult                  # used by Metadata-on-Destination backing
  .introspect()         -> WarehouseSchema              # lists schemas/tables for landing/freshness

MetadataBackend
  .append_event(event)             -> None
  .query_events(filter)            -> Iterable[Event]
  .upsert_snapshot(kind, key, blob)-> None
  .read_snapshot(kind, key)        -> blob | None
  # Same contract whether backing is local DuckDB file or user's Destination.

CatalogSource     (internal, not a user-facing adapter)
  .offers(scope)        -> Iterable[CatalogOffer]
  # One CatalogSource per attached Runtime / Transformation / Semantics / Presentation,
  # plus one for the Project (declared Sources / Models / Metrics / Views).
```

If a future symmetric compartment (e.g. data-quality testing tools — Great Expectations, Soda, Elementary) gets added, it inherits the same shape: `capabilities`, `catalog_offers`, `introspect`, `run`/`query`, `observe`. The shape is now load-bearing across four compartments — strong evidence that the abstraction is real, not coincidence.

### Component diagram (in-process)

```
                         ┌─────────────────────────────────┐
                         │           commands/             │
                         │  add  attach  list  run  status │
                         └────────────────┬────────────────┘
                                          │
                                          ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │                              core/                                   │
   │                                                                      │
   │   project ──▶ source ──▶ capabilities                                │
   │                  │                                                   │
   │                  ▼                                                   │
   │   ┌─ runtime ──┐  ┌─ transformation ─┐  ┌─ semantics ─┐ ┌─ presentation ─┐
   │   │ (interface)│  │  (interface)     │  │ (interface) │ │  (interface)   │
   │   └─────┬──────┘  └────────┬─────────┘  └──────┬──────┘ └────────┬───────┘
   │         │                  │                   │                 │
   │         └──────┬───────────┴───────────┬───────┴─────────────────┘
   │                ▼                       ▼
   │           ┌─ destination ─┐      ┌─ catalog ─┐
   │           │  (interface)  │      │           │
   │           └───────┬───────┘      └─────┬─────┘
   │                   │                    │
   │                   └───────── events ◀──┴─── metadata (interface)
   │                                                                      │
   └────────────────────────────┬─────────────────────────────────────────┘
                                │
   ┌─────────────────┬──────────┴──────────┬──────────────────┐
   ▼                 ▼                     ▼                  ▼
┌──────────────┐ ┌─────────────────┐ ┌──────────────┐ ┌─────────────────┐
│  runtimes/   │ │ transformations/│ │  semantics/  │ │ presentations/  │
│ ─ dlt        │ │ ─ dbt           │ │ (empty in    │ │ ─ rill (POC)    │
│ ─ dlt_project│ │ ─ (sqlmesh,     │ │  POC; dbt_mf,│ │ ─ (metabase,    │
│ ─ fivetran   │ │    dbt_cloud..) │ │  cube, malloy│ │    superset..)  │
└──────────────┘ └─────────────────┘ │  to follow)  │ └─────────────────┘
                                     └──────────────┘

   ┌──────────────────┐    ┌─────────────────────────┐
   │  destinations/   │    │   metadata_backends/    │
   │  ─ duckdb        │    │   ─ duckdb_file (POC)   │
   │  ─ ...           │    │   ─ destination (later) │
   └──────────────────┘    └─────────────────────────┘
                                                  │
                        ┌─────────────────────────┴─────────────────┐
                        ▼                                           ▼
              ┌──────────────────┐                        ┌─────────────────┐
              │  surfaces/cli    │                        │ surfaces/json   │
              │  (Typer)         │                        │ (structured     │
              │                  │                        │  output)        │
              └──────────────────┘                        └─────────────────┘
```

### Component-level open questions

1. **dlt-project Runtime: in-process or subprocess?** In-process is faster and simpler but couples dlt versions; subprocess gives isolation at the cost of complexity. Likely subprocess for safety, but defer until we have a real user project to test against.
2. **Where does environment resolution happen?** `core.project` resolves Source→Runtime binding for the active environment, but the Source object itself probably shouldn't carry the resolution — it should carry the *declaration*, with resolution as a lookup. Confirm before Level 4.
3. **Catalog cache lifetime.** Per-invocation? Persisted in Metadata? Probably per-invocation for the POC (simpler, no staleness questions), persisted later with explicit refresh commands.
4. **Transformation's depth in the POC.** Manifesto says it's a compartment. Code-wise it might be thin enough in the POC to be a single module wrapping `dbt run` invocations and writing events. Revisit when Transformation gets its second backing (sqlmesh, dbt-cloud).

---

## Level 4 — Code (source tree)

> How is this organised on disk? Where does a contributor or an agent find their footing?

### Proposed top-level layout

```
src/tycoon/
  __init__.py
  __main__.py                 # entrypoint: `python -m tycoon`
  cli.py                      # Typer app, top-level command groups

  core/
    __init__.py
    project.py                # manifest read/write, environment resolution
    source.py                 # Source dataclass + validation
    runtime.py                # Runtime protocol + capability declarations
    destination.py            # Destination protocol
    catalog.py                # federated query layer
    metadata.py               # MetadataBackend protocol + Metadata API
    events.py                 # event schema (Pydantic models)
    capabilities.py           # Capability enum + capability set helpers
    identifiers.py            # qualified IDs, parsing, formatting
    transformation.py         # TransformationAdapter protocol
    semantics.py              # SemanticsAdapter protocol (post-POC; interface lives in POC)
    presentation.py           # PresentationAdapter protocol
    errors.py                 # CapabilityError, AdapterError, etc.

  runtimes/
    __init__.py               # adapter registry
    dlt_native.py             # dlt verified sources, in-process
    dlt_project.py            # user's dlt project, entrypoint-driven
    fivetran.py               # Fivetran REST API client

  transformations/
    __init__.py               # adapter registry
    dbt.py                    # POC: local dbt project subprocess
    # sqlmesh.py, dbt_cloud.py, ... (post-POC)

  semantics/
    __init__.py               # adapter registry (empty in POC; folder exists so layering is honest)
    # dbt_metricflow.py, cube.py, malloy.py, ... (post-POC)

  presentations/
    __init__.py               # adapter registry
    rill.py                   # POC: local Rill project subprocess
    # metabase.py, superset.py, lightdash.py, hex.py, ... (post-POC)

  destinations/
    __init__.py               # adapter registry
    duckdb.py                 # default local DuckDB
    # snowflake.py, bigquery.py, ... (post-POC)

  metadata_backends/
    __init__.py               # adapter registry
    duckdb_file.py            # POC default, .tycoon/metadata.duckdb
    destination.py            # writes into the user's Destination (designed-for, not POC)

  surfaces/
    __init__.py
    cli/
      __init__.py
      source.py               # `tycoon source ...`
      runtime.py              # `tycoon runtime ...` (advanced only, hidden from beginner)
      catalog.py              # `tycoon catalog ...`
      attach.py               # `tycoon attach ...`
      run.py                  # `tycoon run ...`
      status.py
    json/
      __init__.py
      schemas.py              # the JSON shapes agents consume
      render.py               # core-model -> JSON

  commands/                   # alternative: collapse into surfaces/cli; see open Qs

  scaffolds/
    __init__.py               # scaffolder registry
    manifest.py               # writes the greenfield tycoon.yml + .tycoon/ directory
    dlt_native.py             # writes a minimal starter dlt source skeleton
    dbt.py                    # writes a minimal dbt_project.yml + dirs (POC)
    rill.py                   # writes a minimal Rill project (POC)
    # All scaffolders: create-only, idiom-native, never mutate existing files.

  templates/
    tycoon.yml.jinja          # consumed by scaffolds/manifest.py
    # Per-adapter templates live next to their scaffolder in scaffolds/_templates/

tests/
  unit/
  integration/
  e2e/

docs/
  ...

MANIFESTO.md
ARCHITECTURE.md               # this document
README.md
pyproject.toml
```

### Layering rules (enforced)

These are the dependency rules that keep the architecture honest. They are checked manually for now; we may codify them with `import-linter` or similar later.

| Layer | Can import |
|---|---|
| `core/` | Only stdlib + Pydantic + Jinja (for `core.scaffold` template loading). **Never** `runtimes/`, `transformations/`, `semantics/`, `presentations/`, `destinations/`, `metadata_backends/`, `scaffolds/`, `surfaces/`. |
| `runtimes/`, `transformations/`, `semantics/`, `presentations/`, `destinations/`, `metadata_backends/`, `scaffolds/` | `core/` + their specific third-party clients. **Never** each other. **Never** `surfaces/`. |
| `surfaces/` | `core/` + adapter registries (to invoke). **Never** the inside of an adapter. |
| `cli.py` / `__main__.py` | Anything. The composition root. |

This is the same dependency-direction rule as Dango's layered hierarchy, but tighter — adapters cannot reach across to each other, and Surfaces cannot reach into adapter internals.

### Where new things go (the "no private doors" test)

- **Adding a new Runtime** (e.g. sling, Airbyte): one new file in `runtimes/`. No changes to `core/`. If `core/` needs to change, the Runtime interface is wrong and we fix the interface first.
- **Adding a new Transformation adapter** (e.g. sqlmesh, dbt-cloud): one new file in `transformations/`. Same rule.
- **Adding a new Semantics adapter** (e.g. dbt MetricFlow, Cube, Malloy): one new file in `semantics/`. Same rule.
- **Adding a new Presentation adapter** (e.g. Metabase, Superset, Lightdash, Hex): one new file in `presentations/`. Same rule.
- **Adding a new Scaffolder** (e.g. for sqlmesh or Metabase greenfield setup): one new file in `scaffolds/`. Same rule. Invoked silently by `attach`, never exposed as its own command.
- **Adding a new Metadata backing** (e.g. MotherDuck-as-metadata): one new file in `metadata_backends/`. No changes to `core/metadata.py`'s public API.
- **Adding a new Surface** (e.g. MCP server): one new package in `surfaces/`. Reads the same core model, renders differently. Zero adapter changes.
- **Adding a new command verb** (e.g. `tycoon backfill`): a new module in `surfaces/cli/`. Calls into `core/`. The core may grow a new method, but it grows the same method for every adapter type simultaneously.

This is the architectural acceptance test from manifesto §8 made concrete at the file level. The pattern is the same across four adapter folders (`runtimes/`, `transformations/`, `semantics/`, `presentations/`) — which is exactly what makes the abstraction worth its weight.

### Code-level open questions

1. **`commands/` vs. `surfaces/cli/` for command files.** Both are defensible. `surfaces/cli/` puts CLI logic inside the Surface boundary (cleaner under the manifesto). `commands/` reads more naturally to contributors. Lean toward `surfaces/cli/`; revisit after a few commands exist.
2. **Adapter registration mechanism.** Entry points (pluggable, future-friendly) or static imports (simpler, current). Probably static for the POC; entry points when a third party wants to ship an adapter.
3. **Where the project manifest schema lives.** Inside `core/project.py` as Pydantic models, or in a separate `core/schema/` package. Defer until the manifest grows beyond ~5 fields.
4. **Python import name.** The CLI command is `tycoon` and the package is `src/tycoon/`. The PyPI distribution is `database-tycoon`. Confirm that `import tycoon` is the right ergonomic choice, or whether `database_tycoon` (matching PyPI) should be canonical with `tycoon` as the alias.

---

## How to use this document

- **When starting a new feature**, identify which compartment(s) it touches in §7 of the manifesto, then which components in Level 3 here. If a feature touches `core/` and a specific adapter, the feature is likely splittable into a contract change (in `core/`) and an adapter change (in the adapter).
- **When adding a new adapter**, jump to Level 4's "no private doors" test. If the answer is "this needs a change to `core/`," the interface is the bug, not the adapter.
- **When reviewing a PR**, the layering rules in Level 4 are checkable by eye. Imports flowing the wrong way are an architectural smell, not a style nit.

## Status

This document reflects the architectural conversation as of 2026-06-18, paired with [MANIFESTO.md](./MANIFESTO.md). Levels 1 and 2 are decisions we've taken; Levels 3 and 4 are sketches with named open questions, to be sharpened as we build the CLI surface and the first adapters.

Open architectural threads:
- The exact Runtime / Transformation / Semantics / Presentation interface signatures (Level 3 sketches need to become actual Protocols, with shared shape where possible — see "common adapter shape" question below).
- Metadata event schema (named in §3 manifesto open threads).
- The capability model — how an adapter declares what a Source *could* do vs. what it *currently can* do given clearance.
- Subprocess isolation for `dlt-project` Runtime.
- **Common adapter shape.** Runtime, Transformation, Semantics, Presentation share `capabilities`, `catalog_offers`, `introspect`, `run`/`query`, `observe`. Do we factor a `Adapter` base Protocol they all extend, or keep them as four independent interfaces that happen to be symmetric? Premature unification can be worse than honest duplication. Defer until we have at least one adapter in each folder.
- Transformation has a real POC adapter (dbt); Semantics has an interface only (no adapters in POC) — confirm the empty `semantics/` folder approach beats deferring the interface entirely.
- Whether Presentation's lineage-introspection capability (what does this dashboard read?) should resolve through Destination introspection or through the Presentation adapter's native API. Probably the latter (Rill knows its own lineage best); confirm with the first Rill adapter.
