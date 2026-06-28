# Tycoon CLI Manifesto

> **Naming note.** This document was drafted in conversation, during which the author used `dbty` / `dbty-cli` as personal shorthand for **Database Tycoon** — the company behind this project. The tool itself is the **Tycoon CLI** (the `tycoon-cli` repository, distributed on PyPI as `database-tycoon`). Any occurrence of `dbty` below refers to this same tool; it is **not** a separate product, not a fork of dbt, and not affiliated with dlt. The shorthand is preserved in places where rewriting would obscure the original framing.

> A living document. Captures the philosophy and load-bearing design ideas behind the Tycoon CLI (the `tycoon-cli` / `database-tycoon` project). This is the **why** and the **shape**, not the implementation.

---

## 1. What dbty is

dbty is a **stack-aware control plane** for the modern data stack — built so that humans *and* analytics agents can introspect, reason about, and act on the stack through one uniform interface.

dbty is not an ingestion tool. dbty is not a transformation tool. dbty is not a BI tool. dbty is not a data platform. It is the layer that makes the existing tools in those categories addressable as a coherent whole.

### Control plane, not platform

The distinction is load-bearing, not cosmetic.

A **platform** is a thing users live inside. It owns the runtime, the storage, the auth, the scheduler, the UI. It absorbs the user's stack. To get value out of a platform you replatform onto it.

A **control plane** is a thing users (and agents) act *through*. It owns coordination, observation, and addressability. It does not own the runtimes underneath; it makes them legible and actionable as a single surface.

Adjacent tools (Dango and similar) are platform-shaped. dbty deliberately is not. If we collapse into platform-shape — bundling our own warehouse, our own auth, our own everything — we look like every other tool in the category and we break the BYOS promise in §2. Holding the control-plane shape is what differentiates dbty.

Concretely:
- A platform owns ingestion. A control plane orchestrates whoever owns ingestion.
- A platform stores the data. A control plane reads from wherever the data lives.
- A platform forces a UI. A control plane treats every surface (CLI, TUI, JSON, agent) as an equally valid rendering of the same model.
- A platform's strength is bundled features. A control plane's strength is uniform addressability.

## 2. The BYOS philosophy — Bring Your Own Stack

The user is not asked to port, rewrite, or replatform anything to use dbty.

- If you already have ingestion in **Fivetran**, dbty leverages it.
- If you already have ingestion in **Airbyte**, dbty leverages it.
- If you already have a **dlt project**, dbty leverages it.
- If you have **custom dlt sources or resources**, dbty leverages them via their entrypoint.
- If you have **nothing yet**, dbty can run dlt natively to get you moving.

dbty meets the stack where it already lives. It does not demand ownership of the ingestion runtime to be useful.

## 3. The thesis: a source is an abstraction, not a runtime

A **source** in dbty is an abstract object — a unified interface — not "a thing dbty runs."

Every concrete source, regardless of who executes it, answers the same questions:

- **Identity** — what is this, what does it represent, where does its data land?
- **Runtime** — which engine owns execution (dlt, Fivetran, Airbyte, external dlt project, custom)?
- **Handle** — the opaque pointer the runtime needs (a dlt pipeline, a Fivetran connector_id, an Airbyte connection_id, a path to a user's project, a Python entrypoint).
- **Capabilities** — what can dbty actually do with this source right now? (`can_run`, `can_backfill`, `can_introspect_schema`, `can_stream_logs`, ...)
- **Metadata** — schema, freshness, last run, row counts, lineage. Always answerable.
- **Data** — a uniform way to read the data once landed (warehouse-mediated).
- **Run** — execute, *if clearance allows*. The implementation differs by materialization.

`run()` is a **capability**, not a method every source must implement. Clearance — having the entrypoint or the API credentials — determines whether the capability is live for a given source. Fivetran and Airbyte are not outside dbty's reach for execution; the ingestion code simply runs elsewhere while the act of triggering and observing it lives in dbty.

### The capability matrix

| Concrete source | Pull data | Pull metadata | Execute `run()` |
|---|---|---|---|
| Native dlt source (dbty-managed) | yes | yes | yes |
| User's custom dlt source / resource | yes | yes | yes |
| User's existing dlt project | yes | yes | yes |
| Fivetran connector | yes (warehouse-side) | yes (API) | yes (trigger via API) |
| Airbyte connection | yes (warehouse-side) | yes (API) | yes (trigger via API) |

Same interface across all of them. Different implementations behind it. An agent asks the same questions and gets typed answers regardless of which row it's looking at.

## 4. Metadata and context are load-bearing from day zero

If dbty is the layer humans and agents act through, then metadata is not a downstream concern — it is the substrate.

This means:

- **Every action a source takes** (run, backfill, schema change, error, retry) emits a structured event into a metadata store dbty owns.
- **Every read** (status, schema, freshness, lineage, capability) hits that store, or falls back to the runtime's API through a uniform adapter.
- **Rendering for humans and agents is derived from one model.** What the CLI prints, what the TUI shows, and what the agent receives as JSON come from the same source of truth — they are not three branches.
- **The metadata store is event-shaped, not just snapshot-shaped** — so questions like "what changed since last sync" and "what is the current state" are both answerable.

The control plane is only as useful as the context it can produce on demand.

## 5. Agent-latchability as a design constraint

dbty is built so that any analytics agent can latch on and figure out how to use it without bespoke per-tool integration. The implications — to be developed further:

- Every command is machine-introspectable; structured output is not optional.
- The Source model is self-describing — an agent can ask "what can I do with this source?" and receive a capability list, not have to encode per-type rules.
- The CLI is a typed API surface. The human UX is a thin rendering layer on top of it.

(Section 5 is an anchor — the full shape of agent-latchability is a conversation still in progress.)

## 6. What this rules in, and what it rules out

**In:**
- A unified `Source` abstraction with pluggable runtime adapters.
- A first-class metadata substrate that captures events, schemas, and lineage.
- Read paths and write paths through the same interface, regardless of who runs the ingest.
- Native dlt as one runtime among several — neither privileged nor required.

**Out:**
- Forcing users to port from Fivetran/Airbyte/their own dlt setup.
- "Source type" being conflated with "source runtime" (today's catalog implicitly does this).
- Ad-hoc, per-command output shapes that an agent has to special-case.
- A metadata system that is bolted on after `run` rather than threaded through every action.
- Drift toward platform-shape: bundling our own warehouse, our own auth surface, our own scheduler runtime, our own UI as the primary surface. These belong to the user's stack, not to dbty.
- Defining our own metrics, dashboards, or semantic models. dbty does not author business definitions, dashboards, or metric DSLs. It addresses whichever Semantics and Presentation tools the user has.

## 7. The compartments

If dbty is a control plane, the compartments are not features — they are the **nouns the plane addresses**. Each is a distinct mental model, a distinct interface, and a distinct lifecycle. Compartmentalization is the discipline that keeps the plane legible to humans and to agents.

There are nine compartments, plus one cross-cutting modifier. Two of them — Semantics and Presentation — are post-POC but named here because they are part of the end-to-end shape and the lineage graph cannot resolve without them.

### 7.1 Source

A declared lineage anchor. "Data from system X lands at warehouse location Y, owned by runtime Z." A Source owns its **identity**, its **runtime binding**, its **handle**, its **capabilities**, and its observed **schema** and **freshness**.

A Source does *not* own the warehouse, the transformations, or the dashboards. It is a node in a graph, not a system.

### 7.2 Runtime

The execution backend behind a Source. A Runtime is an adapter that implements the capability set on behalf of whatever's actually doing the work.

A Source has exactly one Runtime. A Runtime can back many Sources.

The POC ships two Runtimes and three modes — see §8.

Runtime as a separate compartment is what makes BYOS workable. It is also what makes environments-as-rebinding (§7.7) possible.

### 7.3 Destination

The warehouse or lakehouse a Source lands into. DuckDB, MotherDuck, Snowflake, BigQuery, Postgres, and so on.

Sources point at Destinations. Transformations read from and write into Destinations. Critically, dbty does not *run* a Destination — it addresses one.

### 7.4 Transformation

The user's dbt project (or projects). What models exist, what they depend on, what's stale, what just ran.

Transformation is tightly coupled to Destination (a dbt run targets one). It is loosely coupled to Source (a Source's landing is a Transformation's raw input). Under BYOS, dbty does not own dbt any more than it owns Fivetran — it addresses whatever the user has.

### 7.5 Semantics (post-POC)

The compartment that owns *meaning*. Metrics, dimensions, entities, joins — the business definitions of "active user," "MRR," "session." Semantics reads from a Destination (or from Transformation outputs landed in a Destination) and exposes a queryable model of what the numbers *mean*.

Under BYOS, dbty does not define metrics. It addresses whichever semantic engine the user has — dbt's semantic layer (MetricFlow), Cube, Malloy, LookML, SDF semantics — through a Runtime-shaped adapter. The user's metric definitions stay where they live; dbty federates over them.

Semantics owns: the declared metrics/dimensions/entities, the lineage from Transformation models to semantic objects, the capability to **query a metric** through the user's engine, and schema introspection for downstream Presentation tools.

Semantics does *not* own: the metric definitions themselves (they live in the user's semantic project), the query engine (dbty proxies through), dashboard rendering (that is Presentation).

POC posture: deferred. The compartment is named so the long-term shape stays honest and so the lineage graph has somewhere to resolve through. A future POC milestone may add a first adapter (likely dbt MetricFlow or Cube). The Semantics interface is a Runtime-shaped adapter contract, same shape as §7.2 — see §7.10.

### 7.6 Presentation (post-POC for non-CLI surfaces; POC includes the warehouse-anchored read path)

The compartment that owns how landed data is *consumed* — dashboards, metrics views, reports, notebooks, embedded analytics. Presentation reads from a Destination (and, when present, from Semantics) and surfaces views the user (or an agent) interacts with.

Under BYOS, dbty does not own dashboards. It addresses whichever presentation tool the user has — Rill (the POC adapter), then Metabase, Superset, Lightdash, Hex, etc. Each is a Runtime-shaped adapter.

Presentation owns: the declared dashboards/reports/notebooks, their dependencies on Transformation and Semantics objects, the capability to **trigger a refresh or build**, and the lineage answer for "what depends on this Source / this metric."

Presentation does *not* own: the dashboard rendering itself (the user's tool does that), the metric definitions (those are Semantics), the warehouse data (that is Destination).

POC posture: a thin first adapter for Rill is in scope as the canonical example. The compartment is named alongside Transformation because they are structurally symmetric — both read from a Destination, both have a user-owned project, both have a `run`/`refresh`-shaped verb, both need pluggable runtimes. Separating them is the choice that keeps "produces warehouse state" and "consumes warehouse state" from collapsing into a single hand-wavy concept.

### 7.7 Metadata

The substrate every other compartment writes to and reads from. Event-shaped, not just snapshot-shaped.

Every action — a sync ran, a schema drifted, a model failed, a backfill was requested — flows through Metadata. Every read — current schema, last freshness, lineage from this Source to that dashboard — resolves through Metadata.

Metadata is not a feature users add to. It is the connective tissue that makes the other compartments legible. It is the substrate the agent thinks through.

### 7.8 Catalog

The queryable index of sources, presented uniformly across two phases of their lifecycle:

- **Runtime Catalog** — what each attached Runtime *offers*. The dlt verified-sources registry. The user's available Fivetran connectors. The resources discoverable inside the user's dlt project. Answered by asking each Runtime.
- **Project Catalog** — what this project has *declared*. The union of all configured Sources, each carrying its Runtime binding.

Same model, two phases. Browsing "what could I add" and "what's here" share a query shape so an agent uses the same call for both.

Catalog is a thin compartment by design. It is a **federated query layer** over the Runtimes (for offers) and the Project (for declarations). It has no curated marketplace of its own and no store of "all the sources dbty knows about in the world" — that would be platform-shape. It federates over what's actually connected.

Two behaviors worth pinning down:

- A Source the user has declared in Fivetran shows up in the Project Catalog automatically when its Runtime is attached, but with an **`unmanaged` flag** until the user explicitly claims it. dbty can read its metadata and place it in lineage; it will not trigger it. This preserves BYOS — the user already declared it in Fivetran, dbty does not require a second declaration to make it visible.
- The Catalog API supports a **scoped mode** so the basic user's view ("offers from the Runtimes I've attached, hiding the Runtime dimension") and the agent's view ("the full federated answer") are the same API with different filters. See §10.

### 7.9 Surface

The renderings of the model. CLI, JSON, TUI, web UI, MCP server for agents.

No Surface is privileged. Each is a view over the same underlying model. The CLI is not the "real" dbty with everything else being decoration; the JSON is not "machine output" with the CLI being canonical. They are equal renderings, and the model — not any single Surface — is canonical.

This is the architectural commitment that makes agent-latchability tractable.

### 7.10 Environment (cross-cutting)

Environment is not a compartment. It is a **modifier** that lives across Source and Destination, and it answers a single question:

> When I am running in *this* environment, which Runtime does each Source resolve to, and which Destination am I pointed at?

The same `stripe_payments` Source can be bound to a Fivetran Runtime in `prod` and to a `dlt-native` Runtime (pulling a fixture or sampled subset) in `dev`. The Source's identity, its downstream consumers, and its place in the lineage graph do not change. Only the binding does.

Without this, mixed-runtime stacks force users to declare every Source twice and keep them manually in sync. With it, environments become a binding concern instead of a duplication concern — and the lineage graph stays whole across local dev, CI, and production.

### Map

```
   ┌─────────────────────────────────────────────────────┐
   │     Surfaces   (CLI / JSON / TUI / Web / MCP)       │
   └─────────────────────────────────────────────────────┘
                           │
   ┌─────────────────────────────────────────────────────┐
   │                Metadata substrate                   │
   │       (events, schemas, lineage, capabilities)      │
   └─────────────────────────────────────────────────────┘
        │                  │                  │             │              │
   ┌────────┐        ┌─────────────┐    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │ Source │──────▶│ Destination │◀──│Transformation│  │  Semantics   │  │ Presentation │
   └────────┘        └─────────────┘    └──────────────┘  │ (post-POC)   │  │ (Rill = POC) │
        │ ▲              ▲   ▲                            └──────┬───────┘  └──────┬───────┘
        │ │              │   │                                   │                 │
        │ │              │   └───────────────────────────────────┘                 │
        │ │              └─────────────────────────────────────────────────────────┘
        │ │      ┌──────────────────────────────────────┐
        │ └──────│ Catalog  (federated query layer:     │
        │        │   Runtime offers + Project declared) │
        │        └──────────────────────────────────────┘
   ┌─────────┐
   │ Runtime │   dlt-native | dlt-project | fivetran | (sling, airbyte, ...)
   └─────────┘     for Source, Transformation, Semantics, Presentation alike

        ▲
        │
   Environment rebinds Source→Runtime and selects Destination per profile.
```

End-to-end, the lineage flows: **Source → Destination ← Transformation → (Destination ← Semantics) → Presentation.** The control plane addresses every link without owning any of them.

### Open compartmentalization questions

These are intentionally unresolved and named here so they don't get silently re-decided:

1. **Destination — first-class or property of Environment?** It is first-class here because Transformation needs to address it independently and most users have multiple (dev DuckDB + prod Snowflake). The Environment view is plausible; revisit if it causes friction.
2. **Transformation as a single compartment vs. a Runtime-shaped thing.** Today it is one compartment, but BYOS suggests Transformation may itself need pluggable runtimes (dbt-local, dbt-cloud, sqlmesh) at some point. Defer until we have a second example.
3. **Where ad-hoc Operations live.** Trigger a backfill, request a schema diff, ask an agent to draft a model — these cross compartments. Currently treated as verbs on Source/Transformation rather than their own compartment. Revisit if the cross-cutting surface gets noisy.

---

## 8. POC scope: two tools, three modes

The full §7 abstraction is the destination, not the starting point. The POC is deliberately narrow so the seams it forces into existence are real, not hypothetical.

### Two tools

The POC ships exactly two Runtime adapters:

- **dlt** — execution lives inside dbty's process (or a subprocess dbty controls).
- **Fivetran** — execution lives in Fivetran; dbty triggers and observes via API.

That pair is intentional. dlt is the only thing dbty truly *executes*; Fivetran is the canonical example of *delegated* execution. Together they exercise both ends of the capability spectrum — local-runnable and not-local-runnable — and force the Runtime interface to honestly model the difference. An abstraction designed against one example is a fiction.

### Three modes

From those two tools, three Source modes emerge:

1. **`dlt-native`** — dbty runs a dlt source or resource. We own the shim, or the user supplied an entrypoint to their own dlt code. `run_local = yes`.
2. **`dlt-project`** — dbty wraps a user's existing dlt project (BYOS for dlt users). dbty invokes the user's entrypoint; the project remains the user's. `run_local = yes`.
3. **`fivetran`** — dbty observes and triggers a Fivetran connector via the Fivetran API. `run = delegated`, `run_local = no`. Schema, freshness, and lineage are pulled via the API and resolved against the user's warehouse.

These three exercise the abstraction across the dimensions that matter:
- runtime owned by dbty vs. owned by the user vs. owned by a third party
- local-runnable vs. delegated execution
- schema discoverable via dlt vs. via Fivetran's API vs. via warehouse introspection

### Out of scope for the POC

Sling, Airbyte (cloud and OSS), custom-entrypoint Runtimes beyond dlt, dbt-cloud as a Transformation runtime, MCP surface, web Surface. All deliberately deferred — but the Runtime interface designed for the POC must be the same interface those future adapters slot into. No private door for sling/Airbyte to use later that the POC adapters didn't.

### Design discipline for the POC

The POC's only architectural job, beyond working, is to **produce a Runtime interface that future adapters can implement without modification to the core**. Concretely:

- The capability model is declared on the Runtime, not hardcoded in commands.
- Every Surface (CLI, JSON for agents) reads the same model and does not branch on Runtime.
- Metadata events are runtime-shaped uniformly — a Fivetran sync completion and a dlt run completion are the same event with different payloads, not two different code paths.
- No Runtime gets a special case in the core. If Fivetran needs something, it needs it through the interface, and dlt-native gets the same hook.

If we can add a hypothetical `sling` Runtime later by writing one adapter and zero core changes, the POC succeeded. If we can't, the POC's interface is wrong and we fix it before more Runtimes pile on.

### POC user experience: dlt-only by default

Even though the POC builds two Runtimes, the beginner UX is **dlt-only**. Fivetran is reachable only after an explicit `dbty attach fivetran`. See §10 for the principle this enforces.

The two-Runtime architecture is what the POC *proves out*. The one-Runtime cockpit is what the beginner *sees*. These are not the same thing, and conflating them produces either a half-finished platform or a beautiful CLI that breaks the moment a second Runtime arrives.

---

## 9. Progressive disclosure: the cockpit, not the hangar

The goal is to give a beginner the confidence that they can fly a jet — or drive a V12 — with little to no experience. That confidence does not come from being shown the whole hangar. It comes from a small, intelligible cockpit, with the assurance that the same cockpit is the entry into the sophisticated one when they're ready.

dbty's architecture is the full §7 compartments on day one. dbty's *user-facing surface area* starts much smaller and expands only through actions the user takes.

### The three altitudes

- **Day one — beginner, no inventory.** `dbty attach` (or `dbty init` as an alias) in an empty project. dbty picks the Runtime: dlt-native. dbty picks the Destination: local DuckDB. The Catalog the user browses is just dlt's verified sources plus REST API and Filesystem as escape hatches. The user never sees the word *Runtime*. They see *sources*. They pick one, it works.
- **Day thirty — intermediate, has existing things.** The user attaches a second Runtime: `dbty attach dlt-project ./path` to wrap an existing project. The Catalog becomes a union. The Runtime column shows up in `dbty source list` for the first time, because now there is something to distinguish. One more dial revealed. Not the whole panel.
- **Day ninety — sophisticated, multi-Runtime.** `dbty attach fivetran` pulls in their workspace. The Catalog is now a federated view across three Runtimes. Fivetran connectors show up auto-discovered, marked `unmanaged`, until the user claims them. The full cockpit is visible — and earned, because the user encountered each compartment as it became necessary.

### What this commits the architecture to

Progressive disclosure is a UX promise. It only holds if three things are true under the surface:

1. **Defaults are first-class.** A Runtime can be a default. A Destination can be a default. Code paths cleanly resolve "if no Runtime is named, use dlt-native; if no Destination is named, use the project's local DuckDB." Defaults are not fallbacks bolted onto error paths — they are a feature of the Project that the basic user benefits from invisibly.
2. **The Catalog API supports a scoped mode.** The same federated query layer answers two questions with a filter parameter: "offers from the Runtimes I've attached, hiding the Runtime dimension" (the beginner's view) and "the full federated answer" (the agent's view). One API, not two.
3. **Commands degrade gracefully.** `dbty source add github` works for the beginner without them naming a Runtime, because there is exactly one attached and it can offer github. The same command in a multi-Runtime project disambiguates by asking. The control plane *infers* when it can, and *asks* when it can't. It never *requires* the user to name a dimension they don't yet know exists.

### The non-negotiables

- The basic user never has to learn the word *Runtime*.
- The sophisticated user never feels constrained by the basic user's affordances.
- The model is canonical; what the user sees is a rendering of it.

If a feature breaks any of these three, it is wrong even if it works.

### `attach`, not `init`

Under this principle, `attach` is the dominant verb of the control plane. `init` is an alias for the greenfield case where attaching means binding to defaults. The distinction matters because *init* implies dbty *creates*; *attach* implies dbty *connects*. A control plane connects.

### Scaffolding: the silent first move

When `attach` is invoked against a greenfield directory — or against a Runtime / Transformation / Presentation that the user has not yet set up — `attach` scaffolds the minimum required state silently, then performs the attach. The user types `dbty attach` once; the scaffold happens invisibly underneath. There is no `dbty scaffold` verb. The beginner never learns the word.

Scaffolding operates under a strict charter:

1. **Minimum only.** A scaffolder writes only what is strictly needed for the next user action to succeed. Nothing aspirational. Nothing "best-practices." Nothing the user did not ask for.
2. **In the user's idiom.** If the scaffolder is for dbt, it writes dbt-shaped files. If it is for Rill, it writes Rill-shaped files. dbty does not wrap them in a dbty-shaped envelope. The user gets a project their tool of choice recognises natively.
3. **Strictly create-only.** A scaffolder writes new files in empty space. It never edits, appends to, or merges into the user's existing files. If the relevant artifacts already exist, `attach` discovers and binds to them instead of scaffolding — the scaffold step is skipped, not partially run.
4. **Once.** Re-running `attach` does not re-scaffold. Scaffolding is one-shot, greenfield-only. Subsequent attaches *attach*; they do not mutate.

These rules are what keep scaffolding from drifting into config-management, which is the failure mode where scaffolding tools become platforms.

---

## 10. Status of this document

This manifesto reflects the design conversation as of 2026-06-18. The control-plane framing is aligned with founders' direction (a LinkedIn announcement co-authored by Karl and Jason names this positioning publicly). It is the starting point for:

1. An inventory and diagnosis pass on the current `tycoon-cli` codebase against this thesis.
2. A design proposal for the Source / Runtime / Catalog / Metadata interfaces.
3. An in-flight migration plan — changing the engine while the plane keeps flying.

Open threads to develop further:
- The full shape of agent-latchability (Section 5).
- How `run()` clearance is modeled, declared, and revoked.
- The metadata event schema and the read/write API over it.
- Whether the command surface beyond sources also needs to be agent-shaped, or just the source surface for now.
- The exact shape of the Catalog scoped-mode filter and how the unmanaged-flag transition (claim/unclaim) is modeled.
- Presentation adapter shape — confirmed structurally symmetric to Transformation; Rill is the POC adapter.
- Semantics adapter shape and timing — when the first semantic-engine adapter (likely dbt MetricFlow or Cube) lands, and whether a "semantic API as a Surface" rendering (a unified `/metric?name=...` endpoint federated over the user's engine) earns its place on the roadmap.
