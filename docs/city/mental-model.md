---
title: The city map, a mental model
description: What goes into `tycoon city`, what each thing on the map stands for and which city.json field it comes from, one worked example from tycoon.yml to screen, and a checklist for reviewing a city PR
tags: [city, mental-model, review, contract, renderer]
related: [guide, city-json-v1, run-json-v1, conventions, hud-design]
updated: '2026-09-29'
---

# The city map, a mental model

`tycoon city` draws your data stack as a town. This page is the short version
of how that works, written for a reviewer who has not read the renderer. It
answers three questions: what goes in, what each thing on the map stands for,
and what a given kind of change looks like on screen. The normative detail
lives in [`city-json-v1.md`](city-json-v1.md); the tour of the finished map is
[`guide.md`](guide.md).

## How the pieces fit

```
tycoon.yml + warehouse .duckdb + dbt target/ + .tycoon/metadata.duckdb
        |
        |  catalog/   read facts (read-only, never imports the tycoon package)
        v
   PipelineContext   objects, edges, tests, run history, freshness, OSI
        |
        |  sim/       lay it out (town_* planner) and derive visual state (signals, channels)
        v
     CityMap
        |
        |  export/    serialise, byte-stable
        v
     city.json       the contract, plus runs.json / meta.json beside it
        |
        |  web/src/   draw it (three.js); the shipped build is src/tycoon_city/web_dist/
        v
   what you see
```

Two rules hold the layers apart. Everything above `city.json` decides; the
renderer only draws what the document says and never re-derives a rule (which
district is foggy, which test counts as failing). And **unknown is its own
state everywhere**: a missing artifact becomes `null`, a named note in
`database.notes`, or an `unknown` milestone, and the renderer draws it as
plain full colour with no marker, never as stale or failed.

**What the city reads.** Only four things from a tycoon project
(`catalog/tycoon_project.py`):

- `database.warehouse` in `tycoon.yml`: the DuckDB file whose tables and views
  become buildings. Only the connected database is scanned, not attached ones.
- `dbt_project_dir`: `target/manifest.json` (declared lineage, descriptions,
  tests) and `target/sources.json` (freshness verdicts), when they exist.
- `metadata.path` or `.tycoon/metadata.duckdb`: run history from `dbt_runs`,
  `dbt_nodes`, `dlt_runs`, `dlt_rows_by_table` and `dbt_schema_changes`.
- An OSI `semantic.yml` at the root, or the one `semantic_model:` names.

It does not read the `sources:` block of `tycoon.yml`. A dlt source shows up
only as the tables it loaded, and only if those tables live in the warehouse
file. The dbt layer (`meta.tycoon_layer`) is not read either: layer shows
through the schema name and the lineage depth.

## What each thing on the map stands for

| Data-stack concept | On the map | `city.json` field | Derived in |
|---|---|---|---|
| The database | The power plant, with power lines from the western utility strip | `plant`, POWER_LINE tiles in `grid.tiles_rle` | `sim/generator.py` |
| Schema | A district: a tinted ground rect with a name chip | `districts[]` (`schema`, `x`, `y`, `w`, `h`) | `sim/town_plan.py` |
| Schema's pipeline depth | Its ring: deepest schemas (marts) downtown, depth-0 sources on the outer ring. Not a field: it only moves the district | positions in `lots[]` and `districts[]` | `sim/town_precincts.py` |
| Schema name pattern | Building style: a name matching `raw`, `source` or `land` is industrial; `stag` or `int`, commercial; `mart`, `serve`, `analytics` or `main`, residential (default theme; unmatched is residential) | `lots[].zone_style` | theme `style_rules`, resolved in `sim/generator.py` |
| Table or view (raw table, dbt model) | A building | `lots[]` + `objects[]`, joined on `object_key` / `key` | `sim/generator.py`, `export/blocks.py` |
| Row count | Height, drawn from the real count (cube root, with a floor), so views, which measure 0 rows, stand at the minimum. `target_density` is the contract's decade level (1 to 8); the 3D renderer uses it for guest attraction, not height | `objects[].row_count`, `lots[].target_density` | `web/src/scene/buildings.ts`, `sim/channels.py` |
| Biggest tables | A 2x2 footprint for the top decile of this catalog's row counts (needs at least four non-empty objects) | `lots[].w`, `lots[].h` | `sim/town_rows.py` |
| dbt `ref()` / `source()` or view SQL dependency | A street routed door to door | `edges[]` (`route`, `provenance` is `manifest`, `duckdb` or `view_sql`) | `catalog/`, `sim/town_plan.py` |
| Column-level lineage | Gold skybridges, shown for the selected building only | `edges[].columns` | `catalog/column_lineage.py` |
| Where a street ends | A dock (street leaves a depth-0 source), a plaza (2x2 lot or civic building), else an apron | `street_features[]` | `sim/town_streets.py` |
| Object with no lineage at all | A dimmed building. If the catalog has no lineage anywhere, nothing is dimmed | `lots[].powered`, `database.has_known_edges` | `sim/signals.py` |
| dbt test, failing | The building is on fire; a fire truck drives from the firehouse; a health chip `● N tests failing` | `lots[].test_status` = `fail`, `objects[].dbt.tests[].status` | `sim/signals.py` (`TestStatus`) |
| dbt test, warning or passing | A marker over the roof: amber for warn, small green for pass | `lots[].test_status` = `warn` / `pass` | same |
| dbt test, declared but never run | No marker at all (not drawn as passing) | `test_status` null, test `status` null | same |
| Build error | Colour shifted toward red; chip `✕ N build errors` | `lots[].build_status` = `error` | `sim/signals.py` (`BuildStatus`) |
| Time since last build (dbt node, or the dlt load of the table's schema) | Colour fades toward grey over about 30 days; chip `◐ N not built in 14d+` | `lots[].last_build_age_s` | `sim/signals.py` (`LastBuildAt`) |
| Recent build or load | Vehicles on the street into that building, fading over the hour after the build | `last_build_age_s` of the edge's `dst`, `edges[].rate` | `web/src/sim/traffic.ts` |
| Freshness SLA (`dbt source freshness`) | warn/error: a cone marker, boarded windows, an amber repair van; chip `▲ N sources late` | `lots[].freshness_status` | `sim/signals.py` |
| Late source, downstream | Fog (error) or overcast (warn) over the districts it feeds, not its own | `weather.cells[]` | `export/measured.py` |
| Schema drift (columns came or went) | A crane over the roof for 7 days; chip `⌂ N changed shape in 7d` | `lots[].schema_drift_age_s` | `sim/signals.py` |
| Build cadence x cost | Road-load overlay (`T`) and the compute gauge | `edges[].daily_load_s`, `budget` | `export/measured.py` |
| Run appearances | Usage overlay (`U`): beacon, flat ring, grey lid, or nothing for unmeasured | `objects[].usage` | `export/measured.py` |
| One dbt invocation | Run replay: buildings grow in order, failures ignite, dbt-skipped models dim | `replay`, `runs/<id>.json` | `sim/build_replay.py`, `export/run_json.py` |
| Docs and test coverage | The public library's shelves, the problems-panel gauges (`P`), six achievements | `achievements.milestones[]`, `objects[].columns[].description` | `export/achievements.py` |
| Declared OSI join | Inspector only, today (join streets are Phase 3) | `joins[]`, `objects[].semantic` | `catalog/osi.py` |
| Queries against a building | Guests (spheres) walking out from the plant and back, red if the building has a failing test or build error. Off unless `?guests=1`, and flagged as simulated | none; read from `lots[]` | `web/src/mechanics/guests.ts` |
| Anything missing | Named in the footer's notes popover and the legend | `database.notes` | `catalog/loader.py` |

Three caveats for v0.2.2:

- **Vehicles and guests do not draw yet.** The animation loop ticks their
  simulations but never updates the meshes. The fix is PR #250, open against
  `v0.2.2`. The table above describes the intended behaviour.
- **Coverage gauges can show 0% where the truth is unknown.** The client
  schema strips the `achievements` block, so the gauges, the library panel
  and its tour stop recompute coverage from raw fields. PR #251 makes them
  honour `state: "unknown"`.
- **`tests/tycoon_city` is not in the default `pytest` run** (see `addopts`
  in `pyproject.toml`). Run `uv run pytest tests/tycoon_city` by hand until
  PR #256 lands.

## Input to outcome: one worked example

Built from the `csv-import` template with the real CLI on 2026-09-29. Nothing
here was written by hand except the trimming.

**Input.** `tycoon init -t csv-import` gives this `tycoon.yml` (abridged) and a
dbt project with two models: `stg_widgets` (a table over the source, tests
`unique` and `not_null` on `widget_id`) and `fct_widget_summary` (a one-row
aggregate over `stg_widgets`, test `not_null` on `widget_count`).

```yaml
database:
  raw: data/files_raw.duckdb
  warehouse: data/files_warehouse.duckdb
dbt_project_dir: dbt_project
sources:
  files:
    type: filesystem
    schema: raw_files
    config:
      path: data/input
      file_glob: "*.csv"
```

Then `tycoon data run-all` to load the CSV, a test added so the example has
something to show (`accepted_values` on `stg_widgets.widget_name`, which 8 of
the 10 rows fail), `tycoon data transform build`, and
`tycoon-city-export . out/`.

**The document** (`out/city.json`, trimmed to the two models):

```json
{
  "database": { "name": "files_warehouse", "object_count": 12, "has_known_edges": true },
  "districts": [ { "schema": "main", "x": 9, "y": 6, "w": 8, "h": 11 } ],
  "lots": [
    { "object_key": "main.fct_widget_summary", "x": 13, "y": 7, "w": 1, "h": 1,
      "zone_style": "residential", "target_density": 1, "powered": true,
      "build_status": "skipped", "test_status": "pass", "freshness_status": null },
    { "object_key": "main.stg_widgets", "x": 15, "y": 7, "w": 1, "h": 1,
      "zone_style": "residential", "target_density": 2, "powered": true,
      "build_status": "success", "test_status": "fail", "freshness_status": null }
  ],
  "edges": [
    { "src": "main.stg_widgets", "dst": "main.fct_widget_summary", "rate": 1.0,
      "provenance": "manifest", "route": [[15, 6], [14, 6], [13, 6]] }
  ],
  "street_features": [ { "kind": "dock", "x": 15, "y": 6, "facing": "s", "w": 1, "h": 1 } ],
  "achievements": { "milestones": [
    { "id": "fires_out", "state": "unmet", "have": 1, "need": 2, "short": ["main.stg_widgets"] }
  ] }
}
```

**What you see, and why:**

- **One district, `main`.** The template sets no custom schema, so every model
  lands in `main`, which the default theme styles residential.
- **No building for the CSV source.** dlt wrote `raw_files.files` into
  `files_raw.duckdb`, not the warehouse file, so it is off the map. The notes
  popover says `1 upstream sources outside this catalog`. That also makes
  `stg_widgets` a depth-0 building on this map, so its street leaves from a
  loading dock.
- **Twelve buildings, not two.** The other ten are views tycoon adds to every
  dbt project (`stg_tycoon__*`, `dim_runs`) over its own run metadata. Most are
  dimmed: no lineage in or out on this map.
- **`stg_widgets` is on fire** (`test_status: fail`), short (10 rows), and a
  fire truck drives out from the firehouse to the street beside it. The health strip
  reads `● 1 test failing`; clicking it flies there.
- **`fct_widget_summary` stands at minimum height (1 row) with a green
  marker, untinted and not burning.**
  dbt skipped it and its test after the failure upstream. Outside run replay
  a skipped build has no standing mark (only `error` tints), and the test
  signal counts a skipped test as passing, hence `test_status: pass`. Replay
  the run and it dims behind the fire.
- **One street joins them**, three tiles from `stg_widgets`'s dock to
  `fct_widget_summary`'s door. Its vehicles (after PR #250) run only in the
  hour after a build.
- **No weather, no budget figure, several unknown achievements.** No
  `dbt source freshness` snapshot, fewer than two builds per object, and no
  semantic model: each is named in the notes rather than drawn as fine.

## Which part a PR touches

| If the PR changes... | Expect in `city.json` | Expect on screen |
|---|---|---|
| `src/tycoon_city/catalog/` (what is read) | Different facts: objects, edges, `provenance`, tests, notes | Buildings or streets appear or vanish; markers change |
| `sim/signals.py`, `sim/channels.py` (fact to visual state) | Different `lots[]` values: `target_density`, `powered`, statuses, ages | Heights, colours, fires, cones, cranes change; the layout does not |
| `sim/town_*.py`, `sim/layout.py`, `sim/generator.py` (the planner) | Same keys; moved `x`/`y`, `districts[]`, `grid.tiles_rle`, `edges[].route`, `street_features[]` | The city looks different; no status changes. Like the 0.2.1 ring planner |
| `export/` (the wire format) | A contract change. Must touch `city-json-v1.md`, the golden `contract/fixtures/demo.city.json` and `web/src/contract.ts` together | Whatever the renderer does with the new field, if anything yet |
| `web/src/scene/` | Byte-identical | Pixels only. Only a render, looked at, shows whether it is right |
| `web/src/ui/` (HUD) | Byte-identical | Chips, panels, gauges, tour. Counts must come from the document; a lens may reorder, never recount |
| `web/src/sim/`, `web/src/mechanics/` | Byte-identical | Motion (vehicles, trucks, guests). Must not feed back into derived state (`tests/tycoon_city/test_web_layering.py`) |
| `src/tycoon_city/web_dist/` | None | The shipped bundle. Should be exactly a build of `web/` (`scripts/sync_web_bundle.py`); a CI check for that arrives with PR #252 |
| `src/tycoon/commands/city.py` | None | Flags and path handling of `tycoon city` only |

## Reading a city PR

1. **Find the layer.** Use the table above. A PR that touches both `export/`
   and `web/src/scene/` is two changes; ask which one the description is
   about.
2. **Diff the document, not just the code.** Run `tycoon-city-export` on the
   same project on both branches and diff the two `city.json` files. A
   renderer-only PR should produce no diff; a planner PR should move
   coordinates and nothing else.
3. **Contract change?** Any new, renamed or retyped key needs
   `city-json-v1.md`, the regenerated golden (`scripts/update_contract_golden.py`)
   and `web/src/contract.ts` in the same PR. Read the golden's diff: it is the
   contract change.
4. **Unknown stays unknown.** Look for new code that turns a `null` into `0`,
   `false`, `clear` or `pass`. That is the bug class this project guards
   hardest.
5. **Look at it.** For layout or visuals, a green suite is not evidence
   ([`conventions.md`](conventions.md)). Ask for a before and after screenshot,
   or open `tycoon city` on a known project.
6. **Run the suites that CI may skip.** `uv run pytest tests/tycoon_city`, and
   for `web/` changes
   `cd web && npx tsc --noEmit && npm run build && npm run demo-data && npm run e2e`.
7. **Bundle in step.** If `web/` changed, `web_dist/` should be rebuilt in the
   same stack, or the wheel ships the old renderer.
