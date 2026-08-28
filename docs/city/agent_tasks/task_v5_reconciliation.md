---
title: Agent task — Streets v5 Reconciliation & Test Coverage
description: Blueprints and requirements for testing sim/town_v5_plan.py, verifying Properties S7/S8, reconciling v5 planner as default, and resolving precinct collinearity
tags: [streets-v5, planner, testing, reconciliation, agent-task]
related: [handover, road-grammar, semantic-roads]
updated: '2026-08-08'
---

# Task Blueprint: Streets v5 Reconciliation & Test Coverage

## 1. Overview & Goal

The Streets v5 planner (`sim/town_v5_plan.py`) is wired in behind `DATABASE_TYCOON_PLANNER=v5`. It delivers schema-clustered neighbourhoods and clean road geometry. However, `sim/town_v5_plan.py` currently has **zero unit test coverage**, and v4 remains the default planner.

This task reconciles Streets v5 into the codebase as a fully tested, verified, and production-ready planner.

---

## 2. Core Requirements & Test Assertions

### A. Unit Tests for `sim/town_v5_plan.py`
Create `tests/sim/test_town_v5_plan.py` covering:

1. **Property S7 (No Naked Stubs)**:
   * Assert every street feature's start and end points terminate at another street feature, an apron, a loading dock, or a plaza.
   * No raw un-terminated road segments exist in the generated `DagPlan`.
2. **Property S8 (Junction Spacing)**:
   * Use `sim/road_junctions.py` to assert no two junctions sit within `cell_size` of each other.
3. **Schema Clustering Uniformity**:
   * Assert that all blocks within a `Precinct` share the exact same schema.
   * Verify schema bands form clear gaps between neighboring districts.
4. **Deterministic Layout Generation**:
   * Assert identical catalog inputs yield byte-for-byte identical `DagPlan` outputs across execution runs.

### B. Planner Reconciliation & Default Cutover
1. Evaluate cutover of `v5` as default planner (`DATABASE_TYCOON_PLANNER=v5` default).
2. Reconcile `city.json` contract golden fixture in `tests/export/test_city_json.py`.
3. Verify byte stability and additive properties for version 1/version 2 city contract documents.

### C. Precinct Collinearity & Block Shape Stagger
1. Investigate splitting `sim/town_blocks.py` to vary block shapes *within* precincts while maintaining frontage by construction.
2. Reduce collinear lot share while preserving uniform precinct schema boundaries.

---

## 3. Verification Criteria

- `uv run pytest tests/sim/test_town_v5_plan.py` passes 100%.
- All 512+ existing Pytest tests pass cleanly.
- `npx tsc --noEmit` and Playwright E2E suite (`npm run e2e`) remain 100% green.
