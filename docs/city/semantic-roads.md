---
title: Semantic roads — Apache Ossie (OSI) in the city
description: Design sketch mapping the semantic layer's join knowledge onto the road architecture, and how the city rewards filling in documentation and semantics
tags: [design, semantics, osi, roads, incentives]
related: [handover, city-json-v1, hud-design]
updated: '2026-08-06'
---

# Semantic roads — mapping Apache Ossie (OSI) into the city

Stephen's direction (2026-08-05): "we should be incentivizing and rewarding
people for filling in documentation, context, and semantics — map the join
knowledge from the semantic layer into the road architecture."

**Status (2026-08-06): the LOADER HALF is landed; the ROAD RENDERING is not.**

- **Landed.** `catalog/osi.py` reads an Apache Ossie YAML tolerantly (missing
  file → note, malformed section → absence + note, unknown keys ignored),
  discovered at the project root or via `tycoon.yml`'s `semantic_model:` key.
  `PipelineContext` carries `semantic_relationships` + `ai_context_by_key`,
  joined onto catalog keys case-insensitively with catalog spelling canonical.
  `city.json` gained a top-level `joins[]` and a per-object `semantic` block
  (additive, `version` still 1 — normative shapes in `docs/city-json-v1.md`).
  `demo-tycoon` ships the first real OSI file
  (`src/tycoon_city/demo/semantic.yml`), which is the fixture the rendering will
  be built against.
- **Not landed, and blocked on streets v5.** The join street itself — a road
  class distinct from lineage asphalt, direction signage pointing at the "one"
  side, the double-marked crossing for a composite key, and marking the
  existing street where a join's pair also has lineage. The data for every one
  of those decisions is on the wire now (`many`/`one`, `keys`, `composite`,
  `lineage_edge`); nothing renders it. Join affinity driving proximity is
  likewise still a layout question, not a loader one.
- **Also not landed:** metrics as landmarks (parsed and counted into a note —
  "N declared metrics (landmarks not yet rendered)"), `ai_context` as street
  signs and lobby directories, and the coverage gauges / achievements.

## What OSI/Ossie is (verified 2026-08-05)

The **Open Semantic Interchange** spec — donated to the Apache Software
Foundation, in the Apache Incubator since June 2026 as **Apache Ossie**
(Apache-2, YAML, vendor-neutral; Snowflake, dbt Labs, Salesforce, Preset et
al.). Its constructs, and the city surface each one wants:

| OSI construct | What it declares | City mapping (proposed) |
|---|---|---|
| **Dataset** | Business entity (fact/dim), fields, primary + unique keys | The building (already exists). PK/unique keys already render as the gold doorway |
| **Relationship** | FK join between datasets, **always many-to-one**, simple or composite keys | **A new road class: the JOIN street** — see below |
| **Metric** | Model-level measure, may span several datasets | A **civic landmark** (plaza/monument) sited among the datasets it spans |
| **Field** | Column, typed, possibly computed | The facade window (already exists) |
| **ai_context** | Optional annotations at EVERY level: instructions, synonyms, example queries | The **street signs and lobby directories** — the legibility layer |

## Direction refined (Stephen, same day): joins become the ROADS

Stephen's follow-up: "maybe the joins become the roads and the lineage becomes
bike paths." Adopted with one amendment — lineage as **freight rail**, not
bike paths, because the deciding rule is *which network each kind of measured
data belongs to*:

- **Joins = roads (commercial/commuter traffic).** Queries drive joins all
  day, ad-hoc. The OSI relationship grid is the street map; QUERY HISTORY is
  the traffic on it. Vanilla DuckDB has no query history — so the local
  version shows the paved grid only, while the MotherDuck/Snowflake versions
  light it with real query traffic. The engine versions differentiate on
  exactly this axis.
- **Lineage = freight rail (scheduled heavy transport).** Builds are
  scheduled and carry the compute load: `daily_load_s` becomes tonnage, the
  real-movement rule becomes "the night train ran", build replay is the
  freight schedule executing. A bike path undersells the thing that costs
  warehouse dollars.
- **Staging:** lineage keeps the primary network until an OSI file supplies
  the road grid; the inversion is the destination, not a flag-day change.
- **Layout implication (real design work, not paint):** buildings are placed
  by lineage depth today. Joins-as-roads wants join AFFINITY to drive
  proximity (what's queried together lives together) while lineage keeps the
  west→east flow axis — join affinity inside the schema bands is the obvious
  first step.

## The original sketch (superseded in hierarchy, mappings still valid)

### The core distinction: join streets are not lineage streets

Today every road asserts *data moved here at build time* (lineage), carries
real traffic and compute load. An OSI relationship asserts something
different: *these two buildings are formally joinable* — infrastructure that
exists whether or not anything drove on it today. The two must stay visually
and semantically distinct:

- **Lineage streets** (existing): asphalt; traffic (real movement), road-heat
  (compute load) live here. Unchanged.
- **Join streets** (new): a lighter grade of connection — proposed as marked
  crossings/boulevards in a distinct tint, never carrying vehicles or load
  (no data flows across a declared join; a build does). Direction signage
  points to the "one" side (many-to-one is the spec's invariant). Composite
  keys read as a double-marked crossing. They will often be *intra-column*
  (fact↔dim in the same layer), which the loop-edge routing already supports
  geometrically.
- A join street whose pair ALSO has lineage upgrades the existing street
  (markings on the asphalt) rather than adding a parallel road.

## The incentive layer: semantics build the city out of the dirt

The reward mechanic Stephen wants falls out of rendering *absence* as
underdevelopment — all measured facts, no invented points, consistent with
the observation-platform rules:

| Semantic act | City consequence |
|---|---|
| Join known only from SQL scanning | Dirt track (visibly unpaved) |
| Relationship declared in OSI | The join street is paved and marked |
| `ai_context` added (synonyms, instructions) | Street signs appear; the building gets a nameplate/lobby directory |
| Column described | Window lights up (already shipped) |
| Metric defined | Landmark rises on its plaza |
| Coverage milestones | Achievements — "every mart reachable by paved road", "old town fully signed" — each a *count of real declared artifacts*, surfaced in the problems panel's coverage gauges |

This is the same thesis as the cost/skill-build vision: the city makes an
invisible virtue (documentation) visible and cumulative, so filling it in
*feels* like building.

## Data path (when built)

1. Loader accepts an OSI YAML (project-root convention or `tycoon.yml` key),
   parsed tolerant-by-construction like the manifest reader; missing file →
   note ("no semantic model — joins from lineage only"), never an error.
2. `PipelineContext` gains `semantic_relationships` + `ai_context_by_key`,
   joined onto catalog keys case-insensitively (catalog spelling canonical —
   same law as the manifest join).
3. Contract: additive top-level `joins[]` array (decided — see the open
   questions below), plus per-object `semantic` block. Every addition null-safe
   and counted when absent.
4. dbt's semantic layer exports toward OSI (dbt Labs is a member), so dogfood
   can eventually feed this from MetricFlow definitions.

## Open questions for Stephen before building

- ~~Separate `joins[]` array vs folding onto `edges[]`?~~ **Answered
  2026-08-06: a separate top-level `joins[]` array.** The question answers
  itself the moment you write down what each array claims. An `edges[]` entry
  asserts *data moved here at build time* — it carries traffic, a route, a
  `daily_load_s`. A join asserts *these two are formally joinable*, which is
  true whether or not a build ever ran between them. Folding would force one of
  two bad outcomes for the case the question itself names: invent an edge for a
  dim that is joined constantly and never built from the fact (a road implying
  data movement that never happens, and a route the planner would then have to
  lay), or leave that join with nowhere to live — and that join is the whole
  point, because it is the dirt track that documentation is supposed to pave.
  Two smaller reasons confirm it: a join is many-to-one, so it needs `many`/`one`
  where an edge has `src`/`dst`, and folding would silently change what
  existing clients see in `edges[]`. The pairs that DO have both stay
  reconciled by `joins[].lineage_edge`, which names the edge in its own
  direction so the renderer marks that street instead of laying a parallel one.
- Do achievements live in-app or start as coverage gauges only?
- Which real project supplies the first OSI file — dogfood via dbt exports,
  or a hand-written one for demo-tycoon?
