---
title: The city map, a mental model
description: How `tycoon city` turns a project into a map, which layer a city PR touches, a checklist for reviewing one, and what each thing on the map stands for with the city.json field it comes from
tags: [city, mental-model, review, contract, renderer]
related: [guide, city-json-v1, run-json-v1, conventions, hud-design]
updated: '2026-09-30'
---

# The city map, a mental model

`tycoon city` draws your data stack as a town. This page is for a reviewer
who knows dlt, dbt and DuckDB but has not read the renderer. The contract is
[`city-json-v1.md`](city-json-v1.md); the map tour, with HUD chips and
colours, is [`guide.md`](guide.md).

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
        |  export/    serialise
        v
     city.json       the contract, plus runs.json / meta.json beside it
        |
        |  web/src/   draw it (three.js); the shipped build is src/tycoon_city/web_dist/
        v
   what you see
```

Two rules hold the layers apart. Everything above `city.json` decides; the
renderer only draws the document and never re-derives a rule. And **unknown
is its own state**: a missing artifact becomes `null`, a note in
`database.notes` or an `unknown` milestone, drawn in plain full colour, never
as stale or failed.

**What the city reads** from a tycoon project (`catalog/tycoon_project.py`,
`catalog/osi.py`):

- From `tycoon.yml`, only `name`, `database.warehouse`, `dbt_project_dir`,
  `metadata.path` and `semantic_model`. Not `sources:`, not `meta.tycoon_layer`.
- The warehouse DuckDB file (connected database only): tables and views
  become buildings. A dlt source appears only as tables it loaded there.
- dbt `target/manifest.json` and `target/sources.json`, when present.
- Run history from `metadata.path`, default `.tycoon/metadata.duckdb`.
- `requests.json` at the root, when present (the `?crlf=1` requests panel).
- An OSI model: the file `semantic_model` names, else the first of
  `semantic.yml`, `semantic.yaml`, `osi.yml`, `osi.yaml` at the root.

## Which part a PR touches

| If the PR changes... | Expect in `city.json` | Expect on screen |
|---|---|---|
| `src/tycoon_city/catalog/` (what is read) | Different facts: objects, edges, `provenance`, tests, notes | Buildings or streets appear or vanish; markers change |
| `sim/signals.py`, `sim/channels.py` (fact to visual state) | Different `lots[]` values: `target_density`, `powered`, statuses, ages | Heights, colours, fires, cones, cranes; the layout does not move |
| `sim/town_*.py`, `sim/layout.py`, `sim/generator.py` (the planner) | Positions and routes only: `x`/`y`, `districts[]`, `grid.tiles_rle`, `edges[].route`, `street_features[]`. **It must not change any status** (`*_status`, `powered`, ages) | The city looks different, nothing changes colour (like the 0.2.1 ring planner) |
| `export/` (the wire format) | A contract change, on one of two surfaces: `city-json-v1.md` + golden `contract/fixtures/demo.city.json` + `web/src/contract.ts`, or `run-json-v1.md` + `web/src/contract_runs.ts` (runs documents) | Whatever the renderer does with it, if anything yet |
| `web/src/scene/` | Byte-identical | Pixels only. Only a render, looked at, shows whether it is right |
| `web/src/ui/` (HUD) | Byte-identical | Chips, panels, gauges, tour. Counts come from the document; a lens may reorder, never recount |
| `web/src/sim/`, `web/src/mechanics/` | Byte-identical | Motion only; must not feed back into derived state. `test_web_layering.py` checks `web/src/mechanics/` imports only (and on `v0.2.2` looks in the wrong directory, fixed by #249); `web/src/sim/` is unguarded ([#332](https://github.com/Database-Tycoon/tycoon-cli/issues/332)) |
| `src/tycoon_city/web_dist/` | None | The shipped bundle. Should be exactly a build of `web/` (`scripts/sync_web_bundle.py`); a CI check arrives with #252 |
| `src/tycoon/commands/city.py` | None | Flags and path handling of `tycoon city` only |

## Reading a city PR

1. **Find the layer** with the table above. A PR touching both `export/` and
   `web/src/scene/` is two changes; ask which one the description is about.
2. **Diff the document, not just the code.** The exporter reads the wall
   clock, so `last_build_age_s` and `schema_drift_age_s` change on every run
   (and `meta.json` by `generated_at`). Export one project on both branches
   and diff `city.json` without them:

    ```sh
    F='del(.. | .last_build_age_s?, .schema_drift_age_s?)'
    diff <(jq -S "$F" base/city.json) <(jq -S "$F" pr/city.json)
    ```

    A renderer-only PR gives an empty diff; a planner PR moves coordinates
    only. Zero-setup alternative: `uv run python
    scripts/update_contract_golden.py` rebuilds the golden from a catalog with
    no run history (no ages), then `git diff contract/`.
3. **Contract change?** A new, renamed or retyped key needs its whole
   surface (the `export/` row) in the same PR. The golden's diff is the
   contract change.
4. **Unknown stays unknown.** Watch for new code turning `null` into `0`,
   `false`, `clear` or `pass`, the bug class guarded hardest.
5. **Look at it.** For layout or visuals a green suite is not evidence
   ([`conventions.md`](conventions.md)); ask for before and after screenshots.
6. **Run the suites CI may skip.** `uv run pytest tests/tycoon_city`, and for
   `web/` changes
   `cd web && npx tsc --noEmit && npm run build && npm run demo-data && npm run e2e`.
7. **Bundle in step.** If `web/` changed, `web_dist/` is rebuilt in the same
   stack, or the wheel ships the old renderer.

## What each thing on the map stands for

Reference. Chip wording, glyphs and colours are in [`guide.md`](guide.md).

| Data-stack concept | On the map | `city.json` field | Derived in |
|---|---|---|---|
| The database | The power plant, in the civic core near the map centre; lines run out along the four compass directions, plus a western trunk with a stub per district | `plant`, POWER_LINE tiles in `grid.tiles_rle` | `sim/town_plan.py` (positions); `sim/generator.py` paints them |
| Schema | A district: a tinted ground rect with a name | `districts[]` | `sim/town_plan.py` |
| Schema's pipeline depth | Its ring: marts downtown, depth-0 sources on the outer ring. Not a field; it only moves the district | positions in `lots[]`, `districts[]` | `sim/town_precincts.py` |
| Schema name pattern | Building style (industrial, commercial or residential, per the theme's rules) | `lots[].zone_style` | theme `style_rules`, via `sim/generator.py` |
| Table or view | A building | `lots[]` + `objects[]`, joined on `object_key` / `key` | `sim/generator.py`, `export/blocks.py` |
| Estimated row count | Height (cube root, with a floor), from DuckDB's `estimated_size`; views count 0 and stand at minimum. `target_density` is a decade level, not the drawn height | `objects[].row_count`, `lots[].target_density` | `catalog/loader.py`, `web/src/scene/buildings.ts` |
| Biggest tables | A 2x2 footprint for the top decile of row counts (needs four non-empty objects) | `lots[].w`, `lots[].h` | `sim/town_rows.py` |
| `ref()` / `source()` or view SQL dependency | A street routed door to door | `edges[]` (`route`, `provenance`) | `catalog/`, `sim/town_plan.py` |
| Column-level lineage | Skybridges, for the selected building only | `edges[].columns` | `catalog/column_lineage.py` |
| Where a street ends | A plaza (2x2 lot or civic building), else a dock (depth-0 source), else an apron | `street_features[]` | `sim/town_streets.py` |
| Object with no lineage | A dimmed building; nothing is dimmed if the catalog has no lineage at all | `lots[].powered`, `database.has_known_edges` | `sim/signals.py` |
| dbt test | Fail: the building burns. Warn or pass: a roof marker. Declared but never run: no marker | `lots[].test_status`, `objects[].dbt.tests[].status` | `sim/signals.py` |
| Build error | Colour shifts toward red | `lots[].build_status` | `sim/signals.py` |
| Time since last build or load | Colour fades toward grey over about 30 days | `lots[].last_build_age_s` | `sim/signals.py`, `sim/channels.py` |
| Freshness SLA | warn/error: cone, boarded windows | `lots[].freshness_status` | `sim/signals.py` |
| Late source, downstream | Fog or overcast over the districts it feeds | `weather.cells[]` | `export/measured.py` |
| Schema drift | A crane for 7 days | `lots[].schema_drift_age_s` | `sim/signals.py` |
| Build cadence x cost | Road-load overlay and compute gauge | `edges[].daily_load_s`, `budget` | `export/measured.py` |
| Run appearances | Usage overlay; nothing for unmeasured | `objects[].usage` | `export/measured.py` |
| One dbt invocation | Run replay: buildings grow in order, failures ignite | `replay`, `runs/<id>.json` | `sim/build_replay.py`, `export/run_json.py` |
| Docs and test coverage | Library shelves, problems-panel gauges, achievements | `achievements.milestones[]` | `export/achievements.py` |
| Declared OSI join | Inspector only, today | `joins[]`, `objects[].semantic` | `catalog/osi.py` |
| Anything missing | Named in the notes popover | `database.notes` | `catalog/loader.py` |

## Worked example: what a data engineer would not guess

The `csv-import` template, built with the real CLI plus one failing test.

- **The dlt source table is off the map.** dlt loads into the raw DuckDB file;
  the city reads only the warehouse. The notes popover says so.
- **A skipped test shows as a pass.** dbt skipped the downstream test after
  the upstream failure, and the signal counts that as passing
  ([#329](https://github.com/Database-Tycoon/tycoon-cli/issues/329)).
- **tycoon's own metadata views are buildings.** The `stg_tycoon__*` and
  `dim_runs` views turn two models into twelve buildings.
- **No upstream on the map means depth 0.** `stg_widgets` reads the off-map
  source, so its street starts at a dock.

## Known gaps (v0.2.2, 2026-09-30)

- Vehicles and guests do not draw yet: the loop ticks them but never updates
  the meshes. Fixed by #250.
- Coverage gauges show 0% where coverage is unknown. Fixed by #251.
- `tests/tycoon_city` is not in the default `pytest` run; run it by hand until
  #256 lands.
