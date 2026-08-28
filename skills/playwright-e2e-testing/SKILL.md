---
name: playwright-e2e-testing
description: Guidelines for running and writing Playwright End-to-End (E2E) tests for Pipeline City frontend components, HUD interactions, and role lenses.
---

# Playwright E2E Testing Skill Guide

## 1. Running E2E Tests
- Navigation: `cd web`
- Run full suite: `npm run e2e` (or `npx playwright test`)
- Run visual screenshot utility: `node e2e/shot.mjs <out.png> [query]`
- Run replay shot utility: `node e2e/replayshot.mjs`

## 2. Test Fixtures & Route Interception
- Positive path tests are pinned by `web/e2e/rich.spec.ts` against `web/e2e/fixtures/rich.city.json` via route interception.
- When updating HUD or overlay components, verify `web/e2e/hud.spec.ts`, `web/e2e/interactions.spec.ts`, and `web/e2e/lens.spec.ts`.

## 3. TypeScript Type Safety
- Always run `npx tsc --noEmit` from `web/` before declaring frontend tasks complete.
