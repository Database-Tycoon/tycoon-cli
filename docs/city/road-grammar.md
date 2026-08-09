---
title: Road grammar — how a road network reads as a city
description: Research synthesis (real aerial morphology + city sims) and the resulting rules for streets — hierarchy, blocks, districts by layer, the legal-ending taxonomy (S7) and the junction-spacing rule (S8)
tags: [design, roads, streets-v4, streets-v5, research]
related: [semantic-roads, city-json-v1, handover]
updated: '2026-08-07'
---

# Road grammar

Stephen (2026-08-05): the roads are "getting a lot better" but still not
city-like, and *"there needs to be a clear definition for when and where a
road is allowed to end, and what that looks like."* He also flagged asphalt
plazas, flat/pasted streets, abrupt endings at buildings, and the network
shape itself. This page is the research answer (subagent sweep over real
urban morphology + SimCity 2000/3000/4, Cities: Skylines, Anno 1800,
Workers & Resources, TheoTown, Factorio city-block meta; sources in the
research transcript, 2026-08-05) and the rules streets v4 builds to.

## The seven themes that make a network read as a city from above

1. **Visible hierarchy with a step-down rule.** 2–3 road widths; thin roads
   always meet medium before thick. One continuous spine plus ribs is the
   single strongest city tell.
2. **Closed loops in the core, dead ends at the fringe.** All-dead-end
   networks read as plumbing diagrams. Dead-end density is itself a district
   signal: none = downtown, many = suburb.
3. **Small blocks (1:1–1:4 proportions) with buildings fronting the
   street.** Real blocks: Portland 200 ft square → Manhattan 264×900 ft.
   Big buildings consume whole blocks and are *ringed* by streets, never
   threaded through.
4. **District texture contrast.** Industrial = sparse wide straight roads,
   docks, big footprints. Commercial core = tight grid, buildings flush.
   Residential = narrow, curvy, cul-de-sacs. The road texture changes with
   the zone, not just the buildings.
5. **A single root/umbilical.** Anno's trading post, Cities: Skylines'
   outside highway connection, W&R's border crossing: the whole network
   drains to one entry. Disconnected subnetworks read as islands.
6. **Intentional junctions.** T-junctions dominate; 4-ways cluster in the
   core; wide roads cross at aligned right angles.
7. **Terminations are dressed, never raw.** Every road end gets a THING —
   bulb, plaza, dock, gate, apron. The naked stub is the one ending both
   real cities and sims avoid. Bonus: a street ending on-axis at a civic
   building (terminated vista) converts "dead end" into "grand design".

## The legal-ending taxonomy (answers Stephen's rule question)

A road tile with exactly one road neighbour must be one of:

| Ending | Used for | Visual treatment |
|---|---|---|
| **Driveway dock** | ordinary building ↔ street connection | half-tile apron against the face; entrance/garage on the facade (W&R "factory connection" pattern) |
| **Cul-de-sac bulb** | a small cluster of sibling leaves | widened round cap; buildings arranged around it (suburban read) |
| **Plaza terminator** | important leaves (marts), civic buildings | street widens into a 1×1–2×2 paved plaza against the building; the terminated-vista move |
| **Loading dock / yard** | source-layer tables, the power plant | striped truck court against the building's face (industrial read) |
| **Map-edge connection** | external sources/sinks (data arriving from outside the catalog) | road drawn full-width to the grid border and stopped — universally read as "continues elsewhere" |
| **Dead-end cap** | last resort only | the autotile 1-neighbour cap sprite; should be rare enough to be a smell |

Everything else must connect through (≥2 road neighbours). This becomes
property **S7** — a naked stub that is not one of the above is a failing
build, not a style opinion.

## The junction-spacing rule (property S8)

Stephen, 2026-08-07, after the road paint went on every tile: **"You can't
have two consecutive intersection tiles."**

Definitions, so the property is falsifiable: an **intersection** is a road
tile with **three or more** road neighbours (a T or a crossroads);
**consecutive** means orthogonally adjacent. Property **S8** — two
intersections orthogonally adjacent is a failing build.

S8 is the constructive form of the no-asphalt-plaza rule S7 could not
express. S7 polices road *ends*; nothing policed road *area*, so a
sufficiently tangled DAG could pave a solid field and every tile in it
passed S7 while the network stopped being a network. Under S8 that field is
illegal by construction: a contiguous paved area is nothing but mutually
adjacent intersections. It also matches the morphology finding in theme 6
above — real 4-ways are *punctuation between* street runs, never a texture.

Every junction therefore needs at least one non-intersection tile of street
between it and the next. That is what gives a network runs and blocks
instead of a plaza, and it puts a hard floor under block size: a block
cannot be thinner than one street tile plus its two junctions.

**Baseline when the rule was set** (v4 planner, measured — the rule fails
everywhere today, so it is an acceptance criterion for the v5 router rather
than a regression guard on v4):

| Catalog | Road tiles | Intersections | Violating adjacent pairs | Largest intersection clump |
|---|---|---|---|---|
| demo (10 objects) | 70 | 47 (67%) | 76 | 47 — the whole network is one clump |
| dogfood (42 objects) | 833 | 601 (72%) | 984 | 207 |

A 207-tile contiguous intersection is the paved plaza, stated as a number.
The detector is deliberately cheap — degree over the road tile set, then
connected components of the tiles with degree ≥ 3 — so it can run as a
property test and as a spike metric from the same code.

## How the grammar maps onto the warehouse (the data-viz double duty)

- **Road width = downstream dependency count.** Heavily-depended-on flow
  gets the 2-tile avenue; ordinary lineage 1-tile streets; single-consumer
  spurs get alley treatment. The step-down rule (alley → street → avenue,
  never alley → avenue) is enforced, and width is *measured*, not styled.
- **District texture by layer.** Sources/staging = industrial grammar
  (sparse, wide, dock terminations). Intermediate/core = downtown grammar
  (tight grid, the only place 4-ways are common; diamond dependencies
  reconverge into visible closed block loops). Marts = suburban grammar
  (cul-de-sacs, plazas for the big ones). Raw → refined reads as
  factory district → downtown → suburbs.
- **One root.** The ingestion point renders as the map-edge umbilical the
  widest road drains to; the plant/utility strip is its natural home.
  Orphan subgraphs stay visibly islanded — broken lineage should LOOK
  broken.
- **Civic buildings as vista terminators.** Firehouse/library/plant sit at
  the axial ends of straight streets — endings they legitimize for free.

## Status

Stage 1 SHIPPED 2026-08-05 (two Opus worktree agents, planner + renderer,
merged): legal endings apron/dock/plaza as derived contract facts, property
S7 (naked stub = failing build), 3D sidewalk curbs, dressed-ending
rendering, and the town_plan split.

**Stage 2 — streets v5, the blocks-first pivot — is being built through a
spike-render gauntlet** (2026-08-06): every stage is judged by re-rendering
the fixture contact sheet and LOOKING, and no test is written before its PNG
is accepted. Three rounds have run, all in `scripts/spike_*.py` +
`sim/town_blocks.py` / `sim/town_zoning.py`; **`plan_dag_layout` is still
untouched and nothing here is wired into the contract.**

Proven so far, on the 38-fixture bench:

- **Precincts** (schema band × depth, promoted to rectangular land, laid
  west→east by depth) hold the raw→marts flow reading in the land itself, and
  the whole lattice is decided in block/line indices with exactly one
  prefix-sum conversion to tiles at the end — which is what will make
  hierarchy widths cheap.
- **Texture by depth reads as texture**, once density stopped coming from an
  internal lattice: industrial 4×2, downtown 2×2, suburban 2×4 with one
  cul-de-sac stub. Round 1's plus-sign-of-road-around-four-one-tile-lots was
  the circuit board this document's theme 4 warns about, and looking is what
  caught it.
- **Column wrapping**: depth columns wrap at a shared `isqrt(land)` height
  (aspect median 1.40 → 1.20, worst 4.20 → 1.85), so a wide catalog stops
  drawing a ribbon.
- **Zoning: every lot fronts a street BY CONSTRUCTION** (blocks are at most
  two cells deep on the short axis). Measured on all 38 fixtures: lots with no
  frontage 0, unzoned interior cells 0, roads threaded through a lot 0 — big
  lots consume a whole block and are ringed, never threaded, exactly as theme 3
  requires. `cell_size = 2` is the accepted default.

Still open, and in this order:

- **Arterials and surfaces** (spike 3) — routing, the dirt/paved/join
  distinction, and whether the sprawl signal survives the pivot.
- **Hierarchy widths** (spike 4, theme 1, the must-have) — the step-down rule
  and `WIDTH_MEASURE`: carriers vs downstream-closure, **Stephen picks from the
  side-by-side PNGs**.
- **The legal-ending taxonomy attaching to doors** — the apron/dock/plaza
  endings above are v4 facts derived from route endpoints; in v5 they have to
  re-attach to lot frontage, and S7 has to extend over dirt. Cul-de-sac bulbs
  and the map-edge umbilical are still unbuilt.
- **Block fill.** Pavement is 60% at cell 1 and 40% at cell 2, and the second
  number is only better because the lots are bigger — a one-tile lot bought
  with a one-tile street is a 1:1 trade whatever the block shape. Decided
  2026-08-06: fix it with **variable-size blocks**, not by merging thin bands,
  because districts must stay 1:1 with schemas.
