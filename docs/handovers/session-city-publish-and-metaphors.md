# Session Handover — City Publish, PR Stack Repair, Metaphor Audit

**Date:** 2026-08-14 → 2026-08-15
**Follows:** [session-tycoon-city-sync.md](session-tycoon-city-sync.md)

## What was done, in order

1. **Finished the sync session's merge** (`df48e6e`): staged the resolved
   conflicts, replaced the fixture stub with the real
   `tycoon_city.demo.factory` re-export, fixed six carried-over test files'
   `parents[N]` anchors, regenerated the golden, redefined `districts` in
   `docs/city/city-json-v1.md`. 560 → green.
2. **Radial inversion** (`32155a5`): gold/mart downtown, int ring, sources
   on the periphery. Ring index = schema longest-chain depth over the
   cross-schema graph (`layout.longest_chain_depths`), inverted; within-ring
   ties break on fan-out desc, member count desc, name. Routing improved:
   median route 229 → 36 tiles on dogfood. Details: `docs/city/log.md`.
3. **Published and repaired the PR stack** (Stephen authorized):
   `feat/city-addon` fast-forwarded to `1fc3e97`+; PRs #206/#207 on
   `Database-Tycoon/tycoon-cli` had committed conflict markers and
   main-based non-stacked heads — both rebuilt as true stacks
   (#206 = engine + sim slice `4c08a31`, #207 = sim + data-cli slice).
4. **Metaphor audit of the data-cli layer** (`023a663` on `feat/data-cli`):
   vocabulary aligned with the renderer (fire trucks / contractor vans /
   worn facades / fog), the fleet honesty rule stated everywhere, fake
   "unreachable" stat removed, `tycoon.districts` → `tycoon.layers`
   (district = schema plate; layers = rings), three bugs fixed
   (`fire --run` ignored, manifest-vs-run_results statuses, doubled
   sub-app invocations), docs pages added. Verified live on dogfood.

## State at wrap-up

- **All three PRs green**: #205 → #206 → #207, awaiting Stephen's review
  and merge in that order. The contract calls inside: the regenerated
  golden and the `districts` redefinition.
- **Local branch** `feature/city-ring-planner-sync` = remote
  `feat/city-addon` (same lineage, pushed).
- **`stash@{0}`** ("WIP on (no branch): 17bd3d3") is the pre-session merge
  stash — fully superseded by the committed resolution; safe to drop.
- **Worktree** `.worktrees/try-datacli` (clean, at `023a663`) kept for
  trying the new commands:
  `uv run --project .worktrees/try-datacli tycoon fire` from the repo root.

## Open items

- **Live fire on dogfood**: `assert_toggl_deel_hours_variance` is failing —
  the Toggl↔Deel hours reconciliation test. Look before the weekly close.
- Five `sqlmesh__*` districts (frozen layer) still render on the map —
  filter or keep is an open call.
- `database-tycoon-city` PyPI publish before the CLI lockfile refresh
  (pre-existing plan, deliberately left to a human — see
  `docs/city/handover.md`).
- The `v0.1.0` tag re-point (pre-existing, also left to a human).

## Running the city

```bash
uv run tycoon city          # this project's catalog (serves on :8000)
```

Demo catalog: see the corrected command in
[session-tycoon-city-sync.md](session-tycoon-city-sync.md).
