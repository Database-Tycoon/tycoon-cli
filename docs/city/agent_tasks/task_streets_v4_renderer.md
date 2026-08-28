---
title: "Streets v4 — renderer: 3D street presence + dressed endings"
description: Blueprint for the renderer half of streets v4 — raised sidewalk curbs (kills the pasted-on look) and apron/dock/plaza ending treatments
tags: [agent-task, streets-v4, renderer]
related: [../road-grammar, task_streets_v4_planner]
updated: '2026-08-05'
---

# Streets v4 renderer — 3D presence + dressed endings

**Read first:** `docs/road-grammar.md`, `docs/handover.md` (traps: headless
recipe, port isolation, render-and-look), `web/src/scene/terrain.ts`.

## Scope

1. **3D street presence** (Stephen: streets "look flat/pasted"). New
   `web/src/scene/streetscape.ts`: thin raised sidewalk curbs as instanced
   geometry along every CLOSED edge of every road tile (adjacency computed
   client-side from the decoded RLE — same mask logic as terrain.ts's road
   variants; extract/share the mask helper rather than duplicating).
   Subtle: curb height ~0.03–0.05, light concrete colour; the road tile
   texture keeps its painted curb line so far views stay unchanged. Skip in
   `?flat=1` (pixel tests count exact colours).
2. **Dressed endings**, driven by `doc.street_features` — the FROZEN
   contract shape:
   `street_features: [{kind: "apron"|"dock"|"plaza", x, y, facing:
   "n"|"e"|"s"|"w"|null, w, h}]` (may be absent/empty in older docs — treat
   missing field as `[]`; unknown kinds are a no-op, forward-compatible).
   - `apron`: small paved ramp mesh from the road tile toward `facing`,
     plus a door mark on the building face it points at.
   - `dock`: striped loading-court quad (industrial), same orientation.
   - `plaza`: paved pad (w×h) with a lighter pavement tone — the
     terminated-vista forecourt.
3. **Zod contract update** in `web/src/contract.ts`: add `street_features`
   as OPTIONAL (default `[]`) so the existing fixtures keep validating
   until the planner side lands. Extend `web/e2e/fixtures/rich.city.json`
   BY HAND with 2–3 features (kinds/positions consistent with its real
   routes) and pin the rendering in `rich.spec.ts` via a
   `streetFeatureCount()`-style `__dbt` hook — note in a comment that the
   fixture regeneration recipe will replace the hand-added block once the
   planner emits real features.

## Laws (non-negotiable)

- Never push/PR/outbound. Local commits only, own branch, OWN WORKTREE and
  OWN VITE PORT (never 5173 — parallel checkouts must not share ports);
  copy untracked assets (`demo.duckdb`, `web/public/*`, `demo-tycoon/` if
  needed) into the worktree yourself.
- Render-and-look is mandatory: in-repo `web/e2e/shot.mjs` pattern against
  YOUR port; look at every screenshot; build-before-spec for geometry.
- `?flat=1` pixel counts must not change. `npx tsc --noEmit` + full
  Playwright suite green at every commit (run against your own port).
- Files under ~500 lines; `docs/log.md` entry.

## Deliverable

Local commits on branch `feature/streets-v4-renderer` in your own worktree.
Final report: what landed, spec counts, screenshot paths, any contract
questions for integration.
