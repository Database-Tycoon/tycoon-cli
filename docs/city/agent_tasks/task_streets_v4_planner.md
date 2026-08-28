---
title: "Streets v4 — planner: legal endings, S7, module split"
description: Blueprint for the planner half of streets v4 — dressed road endings (apron/dock/plaza), the S7 no-naked-stub property, and the town_plan.py split
tags: [agent-task, streets-v4, planner]
related: [../road-grammar, specification_citizen_request_framework]
updated: '2026-08-05'
---

# Streets v4 planner — legal endings + S7 + split

**Read first:** `docs/road-grammar.md` (the design basis — Stephen approved),
`docs/handover.md` (repo laws + traps), `src/tycoon_city/sim/town_plan.py`.

## Scope (stage 1 only — no hierarchy widths, no district textures, no bulbs)

1. **Split `town_plan.py`** (658 lines, over the 500-line law). Suggested
   seam: rows/clustering (bands, affinity, footprints, cursor, highway) vs
   channels/routing (units, tracks, segment paths, lanes, endings). Keep
   `tycoon_city.sim.layout` re-exporting the full public API unchanged.
2. **Street features** — new `DagPlan.street_features` (tuple, sorted by
   (kind, x, y) for byte stability) of frozen dataclasses:
   `StreetFeature(kind: str, x: int, y: int, facing: str | None = None,
   w: int = 1, h: int = 1)`. Kinds this stage:
   - `"apron"` — at the last ROAD tile of every route endpoint that meets a
     non-source building; `facing` points at the building.
   - `"dock"` — same, but when the building is a depth-0 source or the
     plant (industrial read).
   - `"plaza"` — a paved forecourt pad where a street meets a 2x2 lot or a
     civic building (library/firehouse); w/h may be 2.
   Features are derived facts (route endpoints + lot metadata), never
   invented. Plaza tiles become ROAD-kind pavement (painted by the
   generator like lane tiles, grass-only guard).
3. **S7 property** (in the generator property sweep): every ROAD tile with
   exactly one orthogonal ROAD/LOT neighbour must carry (or be adjacent to)
   a street feature. A naked stub is a failing build. Mutation-check it:
   suppress feature emission and watch S7 fail; restore in-memory
   (`PYTHONDONTWRITEBYTECODE=1`, clear `__pycache__`).
4. **Wire through**: generator paints plaza pavement; `CityMap` carries
   `street_features`; `export/city_json.py` emits
   `street_features: [{kind, x, y, facing, w, h}]` (facing null when
   absent) — the shape is FROZEN, the renderer agent builds against it.
   Update `docs/city-json-v1.md` and regenerate the golden via
   `scripts/update_contract_golden.py` (deliberate, in the same commit).

## Laws (non-negotiable)

- Never push, never open PRs, never post outbound. Local commits only.
- No test touches `~/clients/dogfood` (read-only inspection to spike is OK).
- Facts only: features derive from routes/lots; nothing invented.
- Wrong-axis discipline: every new pin must be mutation-checked; fixtures
  must be able to fail (no alphabetical-luck fixtures).
- Spike first: render the plan with `scripts/spike_road_defects.py` (extend
  it to draw features) on `demo-tycoon` and `~/clients/dogfood` BEFORE and
  AFTER; look at the images.
- Files stay under ~500 lines. `uv run pytest` + `ruff` green at every
  commit. `docs/log.md` entry with Stephen's verbatim framing.

## Deliverable

Local commits on branch `feature/streets-v4-planner` in your own worktree.
Final report: what landed, test counts, mutation verdicts, spike-image
paths, anything deferred.
