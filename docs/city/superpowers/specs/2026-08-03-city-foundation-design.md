---
title: Pipeline City — city foundation design
description: Approved design replacing the unconditional road grid with catalog-scaled districts, lineage-driven roads, and honest powered state
tags: [design-spec, generator, layout, lineage, pygame, duckdb, roadmap]
related: [2026-07-19-pipeline-city-bones-design]
updated: '2026-08-04'
---

# Pipeline City — City Foundation Design

**Status:** Approved 2026-08-03 (brainstorming session). Amended the same day
with the Phase 2 roadmap below, after reviewing
[PGSimCity](https://nikolays.github.io/PGSimCity/) as a reference project.
**One-liner:** Replace the unconditional road grid with districts sized to the
catalog and placed by lineage depth, so the map's structure carries data
meaning instead of wallpaper.

**Branch:** `feature/city-foundation`, branched from `main` after
`feature/engine-bones` fast-forwarded into it at `142e4fc`.

## Why

The engine bones work shipped a legible renderer on top of a generator that
ignores the catalog. Three defects follow from that, all confirmed in code.

**The road grid is wallpaper.** `generate_city` lays a road down every odd
column across the full 112x112 built area, unconditionally, whatever the
catalog holds (`sim/generator.py:40-44`). Seven objects produce roughly
fifty-six full-height corridors and seven buildings. The README claims "roads
are lineage"; they are not. A previous session diagnosed this and compensated
in the camera rather than the generator — see the docstring at
`app.py:28-39`, which states the problem plainly and works around it.

**Power lines never exist.** `TileKind.POWER_LINE` is defined
(`sim/tiles.py:13`), mapped to a sprite (`render/tilemap.py:10`), and listed
in the map legend (`render/screens.py:56`). No code places one. The legend
advertises a tile the map never draws.

**Drag-to-pan is fictional.** The README documents it and the status strip
prints `arrows/drag pan` (`render/chrome.py:7`). No `MOUSEMOTION` handler
exists anywhere in `src/`. Dragging does nothing.

A fourth defect is subtler and costs a whole visual channel. `powered` binds
to `LineageReachability`, which seeds its traversal from every object with no
incoming edge (`sim/signals.py:42-44`). Every node of an acyclic graph traces
back to some source, so every object is always reachable and always powered.
Only a dependency cycle can dim a building, and DuckDB does not produce one.
The demo proves the cost: `raw.events` has no upstream and no downstream, yet
renders fully powered at density 8/8.

## Goals

- Size the map from the catalog rather than a constant.
- Cluster each schema into a district whose area scales with its object count
  and whose distance from the plant equals its lineage depth.
- Build roads that mean something: arterials from the database, streets inside
  districts, lineage paths between them.
- Bind `powered` to a function that can return false.
- Fix drag-to-pan, and place the power-line tile the legend promises.
- Preserve determinism: one catalog state yields one map.

## Non-goals

- **All sprite work.** Stephen is drawing his own tiles later. The default
  spritesheet is untouched, and `scripts/make_default_theme.py` is not edited.
  Every sprite this design needs already exists in the committed sheet.
- Road connection variants (autotiling). Deferred with the rest of the art;
  adding the sprite-name contract later costs one neighbour lookup in
  `draw_tiles`.
- Overlay modes, isometric projection, level-of-detail, minimap, search,
  Stats and Object page redesign, font work, sprite-scaling caches.

## Design

### `sim/layout.py` (new)

Pure geometry. Imports no pygame, and reads the catalog only through
`PipelineContext`. The existing no-pygame guard test covers it.

```
compute_depths(ctx) -> dict[str, int]
```
Lineage depth. Objects with no incoming edge are depth 0; each successor is one
deeper than its deepest predecessor.

**Amended 2026-08-03 (implemented, commits `99cf8a6`/`71a69b5`).** The original
text specified Kahn's algorithm with cycle members taking `max_depth + 1`. That
shipped, and review found it violated a property the map depends on: depth could
*decrease* across an edge. With `a→x`, `c⇄d`, `c→x` it produced
`{a: 0, x: 1, c: 2, d: 2}` — `x` is a successor of `c` at a lower depth, which
draws as a backward-pointing edge. Anything downstream of a cycle also collapsed
onto the cycle's shared depth.

The implementation is now iterative Tarjan SCC detection, condensation to a DAG,
and a single Kahn pass over the condensation. Members of one strongly connected
component share a depth. The guaranteed invariant: for every known edge
`(src, dst)`, `depth[dst] > depth[src]`, unless `src` and `dst` are mutually
reachable, where they may be equal. A naive relax-to-fixed-point pass cannot
deliver this — it never terminates on a cycle — which is why condensation is
required rather than merely convenient.

Per Stephen's ruling the same day, an unfed cycle is a **source at depth 0**: a
component with no incoming edge from outside genuinely is one, and `max_depth + 1`
was hang-avoidance rather than design.

```
isolated_keys(ctx) -> set[str]
```
Objects with no edge in either direction.

```
plan_districts(ctx, depths) -> list[DistrictPlan]
```
One `DistrictPlan` per schema, carrying `schema`, `ring`, and a rectangular
footprint. A schema's ring is the modal depth of its objects; ties break to
the lowest depth, keeping the result deterministic.

~~Within a ring, districts occupy evenly spaced angular slots ordered by schema
name.~~ **Amended 2026-08-04 (implemented, `9085ebc`).** Districts occupy
**per-district angular sectors** — each claims `asin(claim / r)` of the ring and
the radius is found by bisection — ordered by schema name. This reduces exactly
to evenly spaced slots when every district is the same size (verified to 2.8e-16),
so it generalises the original rule rather than replacing it. It matters when
sizes are skewed: a catalog of one 401-object schema plus 99 single-object
schemas needs grid **220** with sectors versus **1393** under the original
formula. Sectors are not uniformly smaller — an asymmetric ring can widen the
bounding box even as the radius shrinks — but the net is strongly positive.

A district holding `n` objects gets a footprint of `2 * ceil(sqrt(n)) + 1`
tiles per side. ~~Lots sit on even cells and streets on odd cells.~~
**Corrected 2026-08-04:** lots sit on **odd/odd** local cells and every other
cell is street. (The original wording contradicted the implementation plan and
the shipped code; odd/odd is correct, and Task 3 lays tiles against it.) The
street grid interleaves with the lots either way, so every lot borders a street
by construction rather than by luck.

**The ring-radius formula in this spec was wrong and has been replaced.** It
bounded **Euclidean** distance between district centres, but overlap between
axis-aligned squares is a **Chebyshev** condition — so it was short by a factor
of √2 and produced genuinely overlapping districts, including on this spec's own
500-object case. The remedy this spec originally suggested (adding 1 to the
circumference term) does not fix it either; a `+1` cannot repair a missing `×√2`.
The shipped formula applies √2 to every clearance term, uses the exact chord
`2r·sin(π/count)` instead of a small-angle approximation that always
understates, allows one tile for polar-to-grid rounding, and folds the plant in
as the first link of the inter-ring clearance chain — without which the plant
could land *inside* a district. √2 is both sufficient and minimal: equality
holds on a pure diagonal, so nothing smaller is safe.

A district's **entry point** is the footprint tile nearest the plant. The
arterial terminates there and joins that district's street grid.

```
grid_size(plans) -> int
```
The bounding box of every planned district plus a margin. Grid size becomes a
result of the catalog rather than a separate heuristic: seven objects yield a
village, five hundred yield a city.

256 tiles is a **soft** target, not a clamp. When the natural bounding box
exceeds it, `plan_districts` compacts — shrinking inter-ring spacing before
street margins — and re-measures. If geometry still will not fit, the grid
grows past the target. Placing a district outside the grid to honour a size
cap would break the containment invariant, so size yields to correctness.

### `sim/generator.py` (rewritten)

The column loop at lines 40-44 is deleted. `generate_city` becomes:

1. Allocate tiles at `LayoutPlan.grid`.
2. Lay **district streets** as a grid confined to each footprint, so every lot
   has a road neighbour.
3. Place each district's lots on odd/odd cells inside that district's
   footprint, ordered by object key.
4. Place the plant at `LayoutPlan.plant_xy`.
5. Lay **arterials** as `manhattan_path` from the plant to each district's
   entry point, written as `TileKind.POWER_LINE`, over `GRASS` only.
6. Lay **lineage roads** as `manhattan_path` between lots whose edge crosses a
   district boundary, written as `TileKind.ROAD`, over `GRASS` only.

Superseded in place (2026-08-04, Task 3 as built): three corrections above.
**Odd/odd, not even/even** — the same contradiction already corrected elsewhere
in this spec; odd/odd is what makes every lot strictly interior to its footprint
and so guarantees all four of its neighbours are streets. **Streets before
lots** — the sequence is in fact slack, since the two cell sets are disjoint and
steps 5-6 only write over `GRASS`; what is load-bearing is the `GRASS` guard,
not the order. **The plant is at `plant_xy`, not the grid centre** — `plan_layout`
puts it at the ring system's origin, which lands off-centre whenever the
districts sit to one side of it (the demo catalog puts it at (37, 6) of a
42-tile grid).

Arterials carry `POWER_LINE` rather than `ROAD` for two reasons: it places the
tile the legend already promises, and it separates trunk from street, which
matches the README's claim that the database feeds every table and view. A
tile holds one kind, so the trunk stops being a road — an accepted trade.

Random water is removed. Twenty scattered single tiles (`generator.py:94-98`)
read as rendering artifacts, and water is decoration best decided alongside
the new tiles.

Removing water leaves the generator with no randomness at all, so the `seed`
parameter drops from both `generate_city` and `refresh`, along with the
`rng = random.Random(seed)` local that ruff would otherwise flag as unused
(F841). Callers in `app.py:68` and `app.py:84` currently pass
`ctx.database_name` and are updated with the signature. `Engine` keeps its own
`random.Random` for presentation traffic; that is unaffected.

`refresh` keeps the rest of its contract: regenerate deterministically, carry
presentation density across for surviving lots so buildings do not snap.

### `sim/signals.py`

Add `LineageParticipation`: `1.0` when an object has at least one edge in
either direction, `0.0` otherwise. Rebind `VisualChannel.POWERED` to it in
`DEFAULT_BINDINGS`.

`LineageReachability` stays registered. It is a valid function and the
registry is the extension seam; it gains a comment recording that it is
always true on an acyclic graph and therefore unfit as the default binding.

### `render/tilemap.py`

`_dim_overlay` allocates a `Surface` per unpowered tile per frame
(`tilemap.py:67`). Dimming was unreachable before and is now live, putting
that allocation on the hot path. Cache the overlay in a module-level dict
keyed by size.

No other rendering change. Sprite lookup, scaling, and draw order stand.

### `render/screens.py` — drag versus click

`MapScreen` gains `MOUSEMOTION` and `MOUSEBUTTONUP` handling:

- `MOUSEBUTTONDOWN` records the press position and starts a drag; it no longer
  opens an object.
- `MOUSEMOTION` with the button held pans the camera by the frame delta.
- `MOUSEBUTTONUP` opens the object under the cursor only when total travel
  since press stays under four pixels.

Moving the open off `MOUSEBUTTONDOWN` (`screens.py:83`) is required, not
cosmetic: without it every drag ending over a building opens that building.

### `render/camera.py`

~~Clamp `offset` to the map bounds on `pan` and `center_on_tiles`. A
catalog-sized map is small enough to pan off entirely, which the 128-constant
map hid.~~ **Amended 2026-08-04 (implemented, Task 5).** Clamping is **cut**
along with drag-to-pan: both are throwaway ahead of the planned 3D renderer, and
neither is what stopped the map being viewable. Three other camera changes are,
and they shipped instead:

- **A third zoom level, `zoom = 1` (16px per tile).** Measured: the viewport is
  864x672, so the two existing levels showed 27x21 tiles (32px) and 18x14 (48px)
  while the *demo* catalog already plans a 42x42 grid. The city never fit at any
  level. 16px shows 54x42. `ZOOM_MIN`/`ZOOM_MAX` are now named and `zoom_in` /
  `zoom_out` step one level at a time instead of snapping between two.
- **The camera is sized to the viewport, not the window.** It was constructed
  `Camera(1024, 768)` while the map is drawn into the 864x672 rect left between
  banner, sidebar and status strip, so it centred and zoom-fitted against 160
  columns of chrome it never draws a tile on.
- **`frame_tiles` chooses the zoom from the content, then centres**, and the
  content now includes the plant. Centring alone cannot frame a bounding box
  wider than the current zoom shows.

**Measured limit, for whoever picks up the renderer.** `zoom = 1` makes the demo
fit whole (42x42 inside 54x42) and puts the plant on screen for every catalog
shape *except* the straight-line one below. It does **not** make a typical
warehouse fit: 21 schemas / 84 objects plans an 85x85 grid, of which 54x42 is
31% of the area — 1 of 21 districts and 4 of 84 lots in frame. Fitting 85 tiles
needs ~10px per tile and 250 needs ~3.4px, which `zoom` cannot express while it
is an integer multiplier on a 16px `TILE`. Deliberately not built here: a
fractional tile size is a real refactor of `world_to_screen`, `screen_to_tile`
and every `TILE * zoom` site, and this camera is scheduled for replacement.

**The straight-line exception is a layout defect, not a camera one.**
`layout._angles` returns exactly pi for a district alone on its ring, so a
pipeline with one schema per lineage depth — the commonest data shape — lays its
districts in a horizontal line with the plant pinned at one end instead of
ringing it. The bounding box then grows two tiles per schema while the plant
stays at its edge, so the frame keeps the middle of the line and loses the
landmark. Three schemas still fit; **five do not**. Measured on a 10-schema
chain: a 121x121 grid for 20 objects, 5 of 10 districts in frame, plant off
screen. Recorded as a fails-when-fixed test in
`tests/test_framing.py::test_a_long_linear_pipeline_loses_the_plant_off_the_frame`.

## Data flow

```
load_catalog -> ctx
  -> compute_depths / isolated_keys
  -> plan_districts -> grid_size
  -> generate_city
  -> Engine.apply(ctx, DEFAULT_BINDINGS)   # density, powered, edge_rates
  -> screens draw
```

`apply_signals` remains the only writer of visual state. Layout decides where
things sit; signals decide how they look. Neither reaches into the other.

## Determinism

Every ordering derives from sorted schema names and object keys, as today.
Ring assignment, angular slots, and lot placement introduce no randomness, and
dropping random water retires the generator's only random source. Identical
catalog state yields an identical map.

## Edge cases

- **Empty catalog:** plant only, no districts, no crash.
- **One object, one schema:** a single ring-0 district.
- **Every object isolated:** districts still plan and place, and no lineage
  roads are drawn. ~~Every building renders unpowered.~~ **Amended 2026-08-03
  (implemented, `30a73d0`):** every building renders **lit**, with a
  `no lineage detected` note in the status strip. A catalog with no known edges
  anywhere means "we have no lineage information", which is a different fact
  from "this object is an orphan" and must not render identically. Lineage is
  derived only from view SQL, so a tables-only DuckDB file has no edges at all —
  under the original rule it opened as an entirely dark city, a worse failure
  mode than the one the powered channel was introduced to fix. Orphans still
  render unpowered whenever the catalog has at least one known edge.
- **Cyclic lineage:** ~~cycle members take `max_depth + 1` and land in an outer
  ring.~~ **Amended 2026-08-03:** members of a strongly connected component
  share a depth, and an unfed cycle is a source at depth 0 — so it lands on the
  **innermost** ring, beside genuine source tables, not an outer one. Do not
  build ring placement against the superseded promise. Consequence recorded for
  later: cycles are now indistinguishable from sources by depth alone. If they
  should be conspicuous on the map, depth is the wrong channel; the SCC pass
  already computes component membership, so a dedicated cycle signal is cheap.
- **Catalog at the 500-object loader cap:** compaction runs and districts pack
  tighter. ~~The grid settles at or near the 256 soft target instead of
  sprawling.~~ **Corrected 2026-08-04 (measured):** the 256 target is
  *unreachable* for wide rings and the grid legitimately overshoots it — 500
  single-object schemas reach **905**, 100 five-object schemas reach **369**.
  The smallest single-ring district count that breaches 256 is about 140
  one-object schemas. This is safe, because containment is structural: a miss
  inflates the grid rather than breaking geometry. **Nothing may assume
  `grid <= GRID_SOFT_MAX`.** Tightening it needs square/Chebyshev ring packing
  (roughly 1.8× denser), which is not implemented.
- **Schema whose object count exceeds its ring's angular slot:** the footprint
  wins; the ring radius grows to accommodate it.

## Testing

Existing generator tests assert the old grid and are rewritten. That is
expected work, not collateral damage.

New coverage:

- Depth on a linear chain, a diamond, an isolated node, and a cycle.
- `isolated_keys` on mixed catalogs.
- District plans do not overlap and stay inside the grid.
- District area increases with object count; ring index equals modal depth.
- **Every lot neighbours a road or arterial tile** — the reachability
  invariant that the deleted grid used to guarantee by brute force. Shipped
  stronger, because this version cannot fail: **all four** orthogonal
  neighbours of every lot are `ROAD`, and the plant reaches every lot by flood
  fill over the network. The weak form survives moving lots onto even cells,
  where a corner lot borders open grass.
- Isolated objects render unpowered; connected objects render powered.
- Grid size scales with object count; a 500-object catalog compacts toward the
  256 soft target, and districts stay inside the grid even when it is exceeded.
- Drag versus click discrimination, driven by synthetic pygame events.
- Camera clamping refuses to scroll past the map edge.
- Determinism: two generations from one context produce identical maps.

The headless smoke test and the no-pygame guard both stand.

## Phase 2 roadmap: time and flow

Not in scope here. Recorded so the direction survives outside a transcript.

**The gap.** Pipeline City renders a static structural inventory: what exists,
how big, what depends on what. Reference projects that hold attention render a
dynamic system instead — PGSimCity's subject is queues filling, pages going
dirty, WAL flushing, checkpoints spiking, vacuum falling behind, and its
scenarios ("Cache thrash", "Checkpoint storm") are stories about change over
time. Rendering polish does not close that gap. A prettier static map is still
a static map.

**The opening.** The dynamic system this project already owns is the pipeline
run. A dbt or SQLMesh build propagating through the DAG, freshness decaying
between runs, tests going red, incremental loads landing rows — that is the
analogue of WAL and checkpoints, and it is unclaimed. The engine-bones spec
already lists the ingredients as future data functions; Phase 2 promotes them
from footnote to subject.

### Prerequisites, in order

1. **Richer data-function value types.** Every v1 function returns
   `dict[str, float]` (`sim/signals.py:11`). Freshness is timestamp-valued and
   run status is enum-valued. The registry seam absorbs this, but the
   `DataFunction` protocol and `apply_signals` both need to handle non-float
   values before any Phase 2 function can exist.
2. ~~**A metadata source beyond the catalog.**~~ **ANSWERED 2026-08-04 per
   Stephen: the Tycoon CLI is the backend.** DuckDB's catalog carries no
   freshness or run history, so `PipelineContext` cannot answer "when did this
   last build?" from a bare `.duckdb` file. It does not have to — Stephen's
   Tycoon CLI (`~/Projects/localhost-stack`, package `database_tycoon`, console
   script `tycoon`) already lays down per-project config and an observability
   store, and Pipeline City should read them rather than inventing a source.

   **`tycoon.yml`** in each managed repo supplies `database.warehouse` (so the
   db path stops being a CLI argument), `dbt_project_dir`, `rill_dir`, declared
   `sources` with their target schemas, and a `stack` block naming the
   ingestion / warehouse / transformation / BI / orchestrator tools plus a
   `*_managed` flag for each.

   **`.tycoon/metadata.duckdb`** — owned by `src/tycoon/observability.py`, its
   schema pinned by `tests/test_metadata_contract.py` — holds twelve tables.
   The ones that matter here, verified against `~/clients/dogfood` on
   2026-08-04:

   | Table | Supplies |
   |---|---|
   | `dbt_nodes` | per-node `status`, `execution_time_s`, `rows_affected` — 244 rows in dogfood: 120 model successes, 123 test passes, **1 test failure** |
   | `dbt_runs` | `started_at`, `command`, `models_ok`/`models_error`, `tests_passed`/`tests_failed`, `target_name` — 4 real runs |
   | `dbt_manifest_snapshots` | manifest fingerprints over time |
   | `dbt_schema_changes` | `change_type`, `column_name`, `old_value`, `new_value` |
   | `dlt_runs`, `dlt_rows_by_table`, `dlt_trace_*` | ingestion telemetry |
   | `fivetran_connectors` | `sync_state`, `succeeded_at`, `failed_at`, `paused` |
   | `events`, `snapshots` | generic event log and keyed blobs |

   Every Phase 2 visual channel has a direct source: run status from
   `dbt_nodes.status`, freshness from `dbt_runs.started_at`, build propagation
   from `execution_time_s` walked in lineage order, test results from the
   `resource_type = 'test'` rows. The ingestion tables additionally describe
   entities that do not exist in the catalog at all, which is the "anticipated
   entity kinds" item from the engine-bones spec.

   **It also fixes a root cause rather than a symptom.** Lineage is currently
   parsed from view SQL only, which is why a tables-only catalog has no edges
   and why the all-lit fallback exists. `dbt_project_dir` leads to
   `target/manifest.json`, whose `depends_on` covers models materialised as
   tables. That is real lineage for the case the current loader cannot see, and
   it retires the "derive table lineage" option that was previously judged
   near-impossible from the catalog alone.

   This is the second `PipelineContext` loader the engine-bones spec designed
   the seam for. It does not block Phase 1: layout, generation and signals are
   all upstream of where the context comes from.
3. **A written channel contract.** Before any sprite work, state what each
   visual channel means and which data function drives it: footprint and
   height, colour, dimming, animation. Sprite work done against a contract
   survives; sprite work that invents its own semantics has to be redrawn.

### Design tension to resolve first

Colour is currently spent on zone style — industrial, commercial, residential
— assigned by regex over schema names (`theme.toml` `style_rules`). That is the
most valuable channel carrying the least meaningful variable. Phase 2 wants
colour for state that changes: freshness, run status, test results. Reassigning
it means schema identity moves to another channel (the existing district label
chips, or footprint shape). Decide this before drawing tiles, not after.

### New visual channels

- **Tint** bound to run status or test results.
- **Flow** along lineage roads, replaying a build in dependency order, replacing
  the current random-walk traffic (`sim/traffic.py`) with motion that means
  throughput.
- **Decay** bound to freshness, so a mart nobody rebuilt visibly ages.

### Named scenarios

Reproducible situations that each teach one failure mode, and each double as a
short clip or post: *the stale mart*, *the orphaned view*, *the fan-out that
costs you*, *the model nobody queries*.

### Renderer direction: 3D, per Stephen 2026-08-03

**This supersedes an earlier draft of this section that ruled 3D out.** That
draft was wrong on two counts: it treated "do not copy the reference project"
as if it barred the medium, and it enforced the engine-bones framing of a
"control screen rather than a game" after Stephen had begun calling this a
game. Free orbit and fly cameras are the style he is aiming for, and the
project's north star moves with him.

What survives the change, because it sits upstream of rendering: `layout.py`,
depth rings, district footprints, lineage roads, the `powered` rebinding, and
the deleted grid. All of it produces plain data a 3D renderer consumes as
readily as a 2D one.

What a 3D renderer costs: `render/` is replaced, not extended. pygame-ce is a
2D blitter with no path to perspective. The `sim/` test suite and its
no-pygame guard are unaffected — the seam that makes the swap tractable is the
one already enforced, that simulation never imports the renderer.

Two Phase 1 items become throwaway if 3D lands soon, and should be cut rather
than built twice:

- **Drag-to-pan** (`render/screens.py`) — an orbit controller replaces it.
- **Camera clamping** (`render/camera.py`) — likewise.

Cutting both leaves the phantom `POWER_LINE` as Phase 1's only remaining bug
fix, and 3D improves that outcome: an arterial becomes masts and catenary
rather than a flat grey tile.

One trade to design against rather than ignore: perspective reads a DAG less
precisely than top-down, because occlusion and foreshortening fight
edge-tracing. Mitigations to build in from the start — highlight-on-select for
a node's upstream and downstream, and a snap-to-top-down hotkey for when
precise lineage reading matters.

Stack undecided as of this amendment. Candidates, cheapest first: isometric
2.5D in pygame (rejected if free orbit is required, since it only offers fixed
90-degree rotation steps), Ursina on Panda3D (Python, keeps `uv` and pytest,
built-in orbit and fly controllers, voxel-native), Panda3D or raylib or
ModernGL directly (more control, no advantage until custom shaders), and a
web Three.js renderer fed by a JSON `CityMap` emitted from the Python CLI
(costs a second language, but yields a shareable URL and realises the
"databasetycoon.com demo potential" already listed in the engine-bones spec).

### Still not wanted

Walk mode and audio: charm for a teaching toy, noise for an operational view.

### Deployment target, per Stephen 2026-08-04

**Near goal: containerized, with DuckDB.** The app should run as a container
against a DuckDB catalog — local file, mounted volume, or MotherDuck.

**Later goal: Snowflake.** Snowpark Container Services or the Native App
Framework, explicitly deferred. Worth knowing for the eventual design:
Snowflake is a *richer* backend than a bare DuckDB file, not a lesser one —
`SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES` gives real server-side lineage for
tables as well as views, and `ACCESS_HISTORY` is a direct source for the
query-activity ("guests") mechanic.

**An unresolved tension, recorded rather than settled.** Stephen chose Ursina
first with a Three.js port later. Ursina is a desktop OpenGL application: to
containerize it you need Xvfb plus VNC or noVNC streaming to reach a browser,
which is workable but heavy and laggy. A web renderer in a container is the
natural fit, and it is also the only option that can ever reach Snowflake. So
both deployment goals pull toward Three.js while the current renderer decision
points at Ursina. Not a blocker — `sim/` is renderer-agnostic and Phase 1 is
upstream of the choice — but the two will have to be reconciled before
containerization is more than a wrapper.

One cheap intermediate exists and is worth remembering: `scripts/screenshot.py`
already renders headlessly via the SDL dummy driver, so the *current* pygame
code can be containerized today to serve rendered stills over HTTP. Not
interactive, but deployable with almost no work, and useful for a
databasetycoon.com demo before any renderer port.

## Simulation layer: game mechanics, per Stephen 2026-08-03

**This supersedes the engine-bones non-goal "No functional city simulation."**
That rule was Stephen's own correction on 2026-07-19 and governed all of v1; it
shaped `sim/signals.py` and `sim/channels.py` and is what killed the guest and
rating mechanics at the time. Stephen has now reversed it: guests as query
consumers, per-object ratings, growth and decay, and scoring are wanted.

### The consequence that must be designed for

`apply_signals` is documented as the only writer of visual state and as
idempotent (`sim/channels.py:37-42`). Game mechanics introduce a second source
of truth that evolves on its own clock. Left to tangle, the two destroy the
project's most valuable property: the ability to say which numbers on screen
are facts about the warehouse and which are invented. A reference project's
credibility came from exactly that discipline — declaring plainly that it
models rather than emulates, and disclosing its simplifications.

So the layers stay hard-separated:

- **Derived state** — computed from the catalog by a registered data function,
  idempotent, unchanged by the passage of time. Row counts, lineage, freshness,
  run status. Today's `signals.py` plus `channels.py`, untouched in character.
- **Simulated state** — evolves on tick from a seed and does not correspond to
  any warehouse fact. Guests, ratings, growth, decay, score. A new module,
  `sim/mechanics.py`, with its own state object and its own tick.

A `Lot` carries both. Nothing in `mechanics.py` may write a derived field, and
nothing in `channels.py` may read a simulated one. A guard test enforces the
direction, in the same spirit as the existing no-pygame guard.

### Provenance in the UI is mandatory

Every value the inspector shows is labelled measured or simulated — for
example `rows: 250,000 (measured)` beside `rating: 6.2 (simulated)`. This is
not decoration. It is what allows the project to be a game and remain
trustworthy as a view of a real warehouse, and it should be stated in the
README the way the reference project states its own boundaries.

### Determinism is redefined

The current guarantee, in this spec and the README, is that one catalog state
yields one map. Growth, decay, and scoring break it. The honest replacement:
**identical catalog, seed, and tick count yield identical state.** Layout and
derived state keep the strict old guarantee; only the simulated layer depends
on elapsed ticks.

The README's "The same file state always produces the same city" becomes false
on the day mechanics ship and must change with it.

### Sequencing

Mechanics are the last phase, not the first. They depend on the layout being
meaningful (Phase 1), on a renderer that can show them (the Ursina work), and
on the derived/simulated split above. Building them earlier means inventing
game state to decorate a map that still misrepresents the catalog.

## Deferred

Unchanged from the engine-bones spec, plus the art deferred here: road
autotiling, grass noise, drop shadows, and a table-versus-view distinction.

Overlay modes and Phase 2 above are the same bet from two directions — an
overlay selector is how a viewer chooses which data function drives colour, and
Phase 2 supplies functions worth choosing between. `LineageParticipation` adds
a third bindable function toward that end. Wayfinding (search and jump-to-object
on `/`, a help overlay, keyboard navigation) is cheap, independent of both, and
becomes necessary well before the 500-object loader cap.
