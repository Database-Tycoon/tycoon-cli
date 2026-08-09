---
title: Pipeline City — engine bones design
description: Approved design for a SimCity-1-style, read-only engine that renders a DuckDB catalog as a living city, with early-2000s web-game presentation
tags: [design-spec, game-engine, pygame, duckdb, simcity]
related: [2026-08-03-city-foundation-design]
updated: '2026-08-03'
---

# Pipeline City — Engine Bones Design

**Status:** Approved 2026-07-19 (brainstorming session).
**One-liner:** A read-only **control screen** for a local `.duckdb` file: the
catalog renders as a SimCity-1-style living city, framed like a 2003 web game.

**Purpose:** utility over fun. This is a glanceable ops view of a database —
what exists, how big, how it connects — that happens to be drawn as a city.
The sim mechanics are status signals, not gameplay: unpowered = disconnected
from the lineage/arterial network, building density = object size, traffic =
data flow. Legibility beats game balance everywhere the two conflict.

## Goals

- A useful, glanceable, **read-only** city view generated from a DuckDB catalog:
  schemas → districts, tables/views → buildings, lineage → roads, the database
  itself → power plant, row counts → building density.
- SimCity 1 (Micropolis) supplies the **visual language only**. Every visual
  state is the output of a real **data function** over the catalog; the engine
  is an extensible function→visual mapping registry, not a game simulation.
- **Theme overlay without code changes:** all sprites, labels, colors, fonts,
  and schema→district rules live in a theme folder.
- Early-2000s web-game ("Neopets-era, not as cute") presentation: site-style
  chrome and page-based navigation.

### Design influences

SimCity 1 supplies the visual language and map model. **RollerCoaster Tycoon**
supplies the attraction framing: database objects are the "rides" — the Object
page reads like an RCT ride window (name, stats, status), and the Stats page
reads like RCT's ride list. Deeper RCT mechanics (guests, ratings) are
deferred; see Future.

**Terminology: data concepts as-is.** The city metaphor is visual and
mechanical only. All on-screen text uses the real data concepts — schema,
table, view, rows, database — never city euphemisms. A schema's area is
labeled "schema: staging", a building's page says "table" with a row count,
the plant is labeled as the database itself. (Themes *may* relabel concepts,
but the default theme does not.)

## Non-goals (v1)

- No player building/editing — the game is read-only.
- No MotherDuck/dbt/SQLMesh/API loaders (the `PipelineContext` seam is designed
  for them, but v1 ships only the local-file DuckDB loader).
- ~~No land value / pollution / crime / disasters / score (Micropolis
  "evaluation layer" — future).~~ **SUPERSEDED 2026-08-03** by the same
  decision as the bullet below.
- ~~**No functional city simulation.** No probabilistic growth/decay, no game
  state that is not a real data fact. If a visual can't be traced to a data
  function's output, it doesn't exist (decorative sprite-frame cycling aside).~~
  **SUPERSEDED 2026-08-03 per Stephen** — game mechanics are now wanted. See
  "Simulation layer" in
  [2026-08-03-city-foundation-design.md](2026-08-03-city-foundation-design.md).
  The rule held for the whole of v1 and shaped `sim/signals.py` and
  `sim/channels.py`; it is retained here as history, not deleted.
- No sound.

The read-only-catalog and no-player-editing rules above still stand: the game
never writes to the database, and the player does not place buildings.

## Success criterion

Run `pipeline-city path/to/db.duckdb --theme default`: schemas render as
districts, buildings grow with row count over the first minute, traffic flows
on lineage roads, pan/zoom works, clicking a building navigates to its detail
page. Pressing **R** re-reads the catalog (read-only) and updates the city in
place — new tables appear as new lots, changed row counts adjust target
density. Same file state always produces the same city.

## Architecture

Three decoupled layers; imports flow one way (`render → sim → catalog`):

```
pipeline-city/
  pyproject.toml            # uv-managed; deps: duckdb, pygame-ce
  src/pipeline_city/
    catalog/    # DuckDB → PipelineContext (read-only)
    sim/        # pure Python: grid, generator, tick engine (no pygame)
    render/     # pygame: chrome, screens, camera, sprites
    app.py      # CLI entry point
  themes/default/
    spritesheet.png
    theme.toml
  tests/
  docs/                     # OKF bundle
```

Files stay under ~500 lines; split by phase/module when approaching it.

## Layer 1: Catalog loader

- Opens the DuckDB file with `read_only=True`; zero write statements anywhere
  in the codebase.
- Emits a frozen `PipelineContext` dataclass:
  - **objects**: schema, name, kind (table/view), row count
  - **edges**: lineage pairs derived from `duckdb_dependencies()` and view SQL
    references, where derivable; objects without lineage are still valid
  - **totals**: object count, total rows, database name
- This schema is the adapter seam: MotherDuck/dbt manifest/API loaders later
  emit the same `PipelineContext` and nothing downstream changes.

## Layer 2: Signal engine (pure Python, no pygame imports)

### Map generation (once, at load)

- Fixed tile grid, default 128×128; scales up for large catalogs.
- RNG seeded from the database name → deterministic: same file, same city.
- Each schema becomes a contiguous **district**; zone type assigned by
  `theme.toml` matching rules (defaults: `raw|source|land*` → industrial,
  `stag*|int*` → commercial, `mart*|serve|analytics|main` → residential,
  plus a fallback).
- Each object becomes a zoned lot. **Target density** (levels 1–8) = row-count
  percentile within the catalog.
- Roads: one arterial network connecting districts; streets from lineage
  edges; objects without lineage get a street to the arterial.
- One power plant (the database), power lines along arterials.

### Signal engine (no game simulation)

The core is a **data-function registry**. A data function computes a real
value per object or edge from the `PipelineContext`; a mapping table binds
each function to a visual channel. v1 ships three:

1. **row_count** → building density (levels 1–8 by percentile).
2. **lineage_reachability** — is the object connected to the database root
   through the lineage/road network? → powered/unpowered visual state.
3. **edge_volume** — endpoint row counts per lineage edge → traffic rate on
   that road.

New data functions (freshness, run status, query counts — from future loaders
and APIs) register the same way and bind to visual channels without engine
changes. Visual *state* changes only when data changes (load or R-refresh).

A fixed timestep (10 ticks/sec, decoupled from render fps) drives
**presentation animation only**: buildings tween stepwise from current to
real target density (the city visibly "builds up" on first load), vehicles
advance along roads at their edge's real rate, sprite frames cycle. Animation
never alters state; state comes only from data functions.

## Layer 3: Rendering, chrome, and navigation

### Renderer

- pygame-ce; 16×16 tiles blitted from the theme sprite sheet at 2–3× integer
  zoom. Camera pan (drag / arrow keys) and wheel zoom.
- Animation via sprite-frame cycling (traffic, smoke, water).

### Era chrome (Neopets-era web-game presentation)

- The window is framed like a 2003 web-game page: banner header with the
  theme's logo text, **left sidebar nav** with chunky beveled buttons, and a
  status strip (database name, object count, total rows styled like a currency
  counter). Beveled borders, flat bright panels, table-style layouts,
  era-appropriate fonts. All of it themed via `theme.toml`.

### Page-based navigation (no floating panels)

- **Map** — the living city; main screen.
- **Object page** — clicking a building navigates to a full detail page
  (name, schema, kind, row count, powered status, density, upstream/downstream
  lineage) with a back link.
- **Stats** — table page listing schemas and their objects (real names,
  kinds, row counts), high-scores-board style.
- Sidebar links switch screens; the sim keeps ticking on every screen.
- Input surface v1: pan, zoom, click, navigate, refresh (R), quit.

## Theming

- A theme is one folder: `spritesheet.png` + `theme.toml`.
- `theme.toml` holds: sprite-name → sheet coordinates; display labels for
  engine concepts (defaults are the data terms as-is: schema, table, view,
  rows, database — themes may override); UI strings, colors, fonts, logo text;
  schema→zone-style matching rules (visual only).
- Ships with `themes/default/` (committed placeholder pixel art — SimCity-1
  meets 2003 Flash portal, not pastel) so it runs out of the box.
- Missing sprite → magenta placeholder tile + logged warning, never a crash.
- Re-theming = new folder + `--theme` flag; no code edits.

## Error handling

- Missing/invalid database path → clear one-line message, no traceback.
- File locked by a writer → plain-language explanation.
- Catalogs over a cap (500 objects) → truncated to the largest N with a
  visible warning; never silent.
- Objects with no derivable lineage render and power normally.

## Testing

- pytest: catalog loader against temp fixture DBs created in-test; generator
  determinism (same seed → identical map, golden-file check); signal-engine
  invariants (every visual channel's value traces to a registered data
  function; unreachable object renders unpowered; density tween stops exactly
  at the row-count-derived target; refresh with unchanged data changes no
  state).
- Headless renderer smoke test (`SDL_VIDEODRIVER=dummy`): boot, tick 100
  frames, quit clean.
- Lint/format with ruff.

## Future (explicitly deferred)

- MotherDuck connection (dogfood as a demo city), dbt manifest / SQLMesh
  adapters.
- Evaluation-layer mechanics (land value, pollution/staleness, disasters =
  pipeline failures).
- Web renderer reusing the sim core (databasetycoon.com demo potential).
- Tick-state snapshots into DuckDB for "city analytics in SQL" content.
- RCT-style mechanics: guests (query/consumer activity) wandering paths to
  attractions; per-object ratings (an excitement/intensity/nausea analogue,
  e.g. freshness/size/complexity) once richer metrics are loadable.
- Anticipated data functions (confirmed interest, in no order): freshness/
  staleness (timestamp-valued), run/job status (status-valued), query
  activity/usage, data-quality/test results. v1 data functions are
  float-valued; richer value types enter via the registry seam, not v1.
- Anticipated entity kinds beyond table/view: dashboards/exposures, semantic
  models, metrics — future `PipelineContext` object kinds rendered as new
  building families.
- Auto-refresh polling deliberately deferred: usage mode is
  launch-to-inspect, so manual R-refresh is sufficient for now.
