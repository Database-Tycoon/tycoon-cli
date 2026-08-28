---
title: Public add-on release plan
description: Task-by-task plan to clear the gates, rename off the dbt mark, ship a self-contained wheel, and wire `tycoon city` as an optional Tycoon CLI add-on
tags: [release, packaging, naming, plan, tycoon-cli]
related: [2026-08-09-tycoon-city-addon-design, handover]
updated: '2026-08-09'
---

# Public Add-on Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `pip install "database-tycoon[city]"` followed by `tycoon city` render a user's Tycoon project as a city, from a wheel that carries everything it needs, under names that embed no third-party trademark.

**Architecture:** Two distributions, one direction of dependency. `database-tycoon` (the CLI) gains an optional `[city]` extra and one thin command whose import of the city lives inside the function body. `database-tycoon-city` (module `database_tycoon`) ships the Vite bundle as committed package data. The city never imports the CLI; it keeps reading `tycoon.yml` off disk.

**Tech Stack:** Python 3.12+, hatchling, uv, pytest, ruff; TypeScript, Vite, Three.js, Playwright; Typer (CLI side).

## Global Constraints

- Module is `database_tycoon`. **No name of ours may contain the substring `dbt`.** Referential use of dbt stays wherever factual (reading dbt artifacts, prose, the `objects[].dbt` contract field, test names describing dbt behaviour).
- Console scripts: `tycoon-city`, `tycoon-city-serve`, `tycoon-city-export`.
- Environment variables: `DATABASE_TYCOON_*`.
- `city.json` stays **version 1**. No contract change in this plan. If a task appears to require one, stop and escalate.
- Source files stay under ~500 lines.
- Every new guard is mutation-tested: break the exact thing it names, watch it fail, restore from an in-memory copy — never `git checkout`. Run with `PYTHONDONTWRITEBYTECODE=1` and `__pycache__` cleared, plus one no-op control mutant that must survive.
- Python gate: `uv run pytest -q`, `uv run ruff format .` (touched paths only), `uv run ruff check .`. Web gate: `cd web && npx tsc --noEmit`, `npx playwright test`.
- **Nothing is pushed and nothing is published.** No `git push`, no `gh pr create`, no PyPI or TestPyPI upload. The plan ends at a local tag and built artifacts.
- Commit after every task. Branch is `feature/city-foundation`.

---

## Execution Order

Task 0 baseline-commits the existing tree, so every later diff is legible. Tasks 1–8 clear the gates, because a green suite is the oracle that proves the rename. Tasks 9–11 rename. Tasks 12–13 package. Task 14 wires the CLI. Task 15 builds the release candidate.

**Cut line:** if time runs short, drop Tasks 6 and 7 (the two e2e regressions) and record them as known issues. Do **not** drop Tasks 9–13 — a name becomes permanently expensive the moment it is published.

---

## Task 0: Baseline-commit the existing working tree

The tree carries ~128 uncommitted files — the phases 0, 1, 1b and 2 work, which
`docs/log.md` already narrates in detail. Without a baseline commit, the first
`git add -A` in Task 9 would sweep all of them into a commit labelled
"refactor: environment variables", making the rename unreviewable.

**Files:**
- Delete: `docs/project_blueprint.md` (**before** committing — it is currently
  staged, and it must never enter the history of a repo that is about to be
  made public)
- Commit: every tracked modification, addition and deletion in the tree

**Interfaces:**
- Produces: a clean `git status` for tracked files, so every later task's diff
  is legible. The seven untracked `web/src` files stay untracked until Task 3.

- [ ] **Step 1: Remove the leaked transcript from the index and the disk**

```bash
git restore --staged docs/project_blueprint.md 2>/dev/null || true
rm -f docs/project_blueprint.md
git status --porcelain docs/project_blueprint.md
```

Expected: no output — the file is neither staged nor present. It is raw model
output (channel tokens, a message addressed to the reader) whose content also
contradicts two closed decisions: read-only against the catalog, and
observation-only with no player verbs.

- [ ] **Step 2: Confirm what is about to be committed**

```bash
git add -A -- . ':!web/src/boot/setup.ts' ':!web/src/boot/hud.ts' \
  ':!web/src/boot/input.ts' ':!web/src/boot/loop.ts' \
  ':!web/src/scene/terrain_atlas.ts' ':!web/src/scene/terrain_flat.ts' \
  ':!web/src/ui/tour_stops.ts'
git status --porcelain | awk '{print substr($0,1,2)}' | sort | uniq -c
```

Expected: the seven `web/src` files remain `??`; everything else is staged.
They are deliberately held back so Task 3 can verify each one is imported
before tracking it.

- [ ] **Step 3: Confirm no secrets or large binaries are riding along**

```bash
git diff --cached --stat | tail -3
git diff --cached --name-only | grep -iE '\.env|secret|credential|\.pem|\.key$' || echo "no secret-shaped paths"
git diff --cached --name-only | xargs -I{} sh -c 'test -f "{}" && find "{}" -size +1M' 2>/dev/null || true
```

Anything a grep flags: stop and ask. Do not commit it.

- [ ] **Step 4: Commit the baseline**

```bash
git commit -m "$(cat <<'EOF'
baseline: the phases 0-2 working tree

Committed as one baseline so the release work that follows is reviewable
against it. This is the tree docs/log.md narrates in its 2026-08-06 and
2026-08-07 entries: Phase 0 (web split, contract seams, five real-catalog
correctness fixes), Phase 1 (run replay, budget/usage/weather, the OSI
loader), Phase 1b (the web halves), Phase 2 (lenses, achievements, the
demo cascade), plus the streets v5 planner behind its flag.

docs/project_blueprint.md is deliberately absent: it was raw model output
rather than a document, and its content contradicted read-only catalog
access and the observation-only decision.
EOF
)"
```

- [ ] **Step 5: Verify the tree is clean apart from the seven held-back files**

```bash
git status --porcelain
git log --oneline -1
```

Expected: exactly seven `??` lines, nothing else.

---

## Task 1: Fix the loader crash on freshness-without-manifest

`_enrich_freshness` dereferences `index.key_of` while `index` may be `None`. A project that ran `dbt source freshness` without a built manifest kills the whole load path — `/city.json`, `/healthz` and the exporter all fail.

**Files:**
- Modify: `src/dbtycoon/catalog/loader.py:417-439`
- Test: `tests/catalog/test_loader_errors.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: no signature change. `_enrich_freshness(ctx, index, sources_json_path) -> tuple[dict, list[str]]` is unchanged.

- [ ] **Step 1: Write the failing test**

Add to `tests/catalog/test_loader_errors.py`:

```python
def test_freshness_without_a_manifest_does_not_crash(tmp_path):
    """sources.json can exist without manifest.json — `dbt source freshness`
    writes one and not the other. The freshness join must degrade to a note,
    not an AttributeError that kills the whole load."""
    from dbtycoon.catalog.loader import _enrich_freshness
    from dbtycoon.catalog.models import PipelineContext

    sources = tmp_path / "sources.json"
    sources.write_text(
        '{"results": [{"unique_id": "source.p.raw.orders", "status": "pass",'
        ' "max_loaded_at": "2026-08-09T00:00:00Z"}]}'
    )
    ctx = PipelineContext(database_name="db", objects=())

    freshness_by_key, notes = _enrich_freshness(ctx, None, sources)

    assert freshness_by_key == {}, "no manifest means no unique_id -> key map, so no verdicts land"
```

- [ ] **Step 2: Run it and watch it fail**

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/catalog/test_loader_errors.py::test_freshness_without_a_manifest_does_not_crash -q
```

Expected: `AttributeError: 'NoneType' object has no attribute 'key_of'`.

If `PipelineContext(...)` rejects those arguments, read its definition in `src/dbtycoon/catalog/models.py` and pass the fields it actually requires. Do not change the model.

- [ ] **Step 3: Fix it**

In `src/dbtycoon/catalog/loader.py`, replace the freshness join body:

```python
    canonical = canonical_keys({obj.key for obj in ctx.objects})
    freshness = read_source_freshness(sources_json_path) if sources_json_path else None
    if freshness and index is not None:
        for unique_id, verdict in freshness.items():
            key = canonical.get(index.key_of.get(unique_id, ""))
            if key is not None:
                freshness_by_key[key] = verdict
    elif index is not None and index.source_ids:
        notes.append("no source freshness snapshot (run `dbt source freshness`)")
```

The `and index is not None` is the fix; collapsing the `freshness = (...)` parentheses onto one line is what `ruff format` wants.

- [ ] **Step 4: Run it and watch it pass**

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/catalog/test_loader_errors.py -q
```

- [ ] **Step 5: Mutation-test the guard**

Delete ` and index is not None`, rerun, confirm the test fails with the AttributeError, then restore from your in-memory copy. Control mutant: change the note's wording; the test must still pass.

- [ ] **Step 6: Fix the line-length error**

`loader.py:357` is 103 chars. Wrap it:

```python
(runs, phase_d_notes) = _enrich_runs(ctx, index, info.metadata_db_path, nodes_by_key, tests_by_key)
```

- [ ] **Step 7: Confirm both gates**

```bash
uv run ruff format src/dbtycoon/catalog/loader.py
uv run ruff check .
```
Expected: `All checks passed!`

- [ ] **Step 8: Commit**

```bash
git add src/dbtycoon/catalog/loader.py tests/catalog/test_loader_errors.py
git commit -m "fix(loader): freshness without a manifest degrades to a note, not a crash"
```

---

## Task 2: Restore the web layering guard

The `main.ts` split moved `import { Guests } from "../mechanics/guests"` into the new `boot/setup.ts`. The composition root is now `boot/*`, but the guard's allowlist still names only `main.ts`.

**Files:**
- Modify: `tests/test_web_layering.py:42-56`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing.

- [ ] **Step 1: Confirm the failure and its cause**

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/test_web_layering.py -q
grep -rn "mechanics" web/src --include="*.ts" | grep -v "^web/src/mechanics/"
```

Expected: the test fails, and the only non-exempt importer is `web/src/boot/setup.ts`.

- [ ] **Step 2: Widen the allowlist to the real composition root**

Replace the allowlist and docstring in `test_nothing_below_main_imports_mechanics`:

```python
def test_nothing_below_main_imports_mechanics():
    """Only the composition root may know the simulated layer exists.

    The root is `main.ts` plus `boot/`: the 2026-08-08 split moved the wiring
    out of main.ts without changing what it is. scene/guest_layer.ts is
    presentation *for* mechanics and may read its types; nothing in the core
    sim, contract, ui or other scene modules may.
    """
    allowed = {"main.ts", "guest_layer.ts"}
    for file in WEB_SRC.rglob("*.ts"):
        if file.parent.name in {"mechanics", "boot"} or file.name in allowed:
            continue
        for target in _imports(file):
            assert "mechanics" not in target, (
                f"{file.relative_to(WEB_SRC)} imports '{target}' -- only the "
                "composition root (main.ts, boot/) and the guest presentation "
                "layer may"
            )
```

- [ ] **Step 3: Run it and watch it pass**

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/test_web_layering.py -q
```

- [ ] **Step 4: Mutation-test that the guard still bites**

Add `import { Guests } from "../mechanics/guests";` to the top of `web/src/ui/legend.ts`, rerun, confirm the test FAILS naming `ui/legend.ts`, then remove the line from your in-memory copy. A guard that exempts `boot/` must still catch `ui/`.

- [ ] **Step 5: Commit**

```bash
git add tests/test_web_layering.py
git commit -m "test(web): the composition root is main.ts plus boot/, so the layering guard says so"
```

---

## Task 3: Track the untracked source files and delete the corrupted blueprint

Seven load-bearing files under `web/src/` are untracked; committing without them yields a repo that cannot build. `docs/project_blueprint.md` is a leaked model transcript.

**Files:**
- Add: `web/src/boot/setup.ts`, `web/src/boot/hud.ts`, `web/src/boot/input.ts`, `web/src/boot/loop.ts`, `web/src/scene/terrain_atlas.ts`, `web/src/scene/terrain_flat.ts`, `web/src/ui/tour_stops.ts`
- Delete: `docs/project_blueprint.md`

- [ ] **Step 1: Confirm the seven files are untracked and not ignored**

```bash
git status --porcelain | grep '^??'
git check-ignore -v web/src/boot/setup.ts || echo "not ignored — safe to add"
```

- [ ] **Step 2: Confirm each is actually imported**

```bash
grep -rn "boot/setup\|boot/hud\|boot/input\|boot/loop\|terrain_atlas\|terrain_flat\|tour_stops" web/src --include="*.ts" | grep import
```

Expected: every one has at least one importer. If any has none, stop and ask — an unimported file may be dead code rather than a missed `git add`.

- [ ] **Step 3: Track them**

```bash
git add web/src/boot/setup.ts web/src/boot/hud.ts web/src/boot/input.ts \
        web/src/boot/loop.ts web/src/scene/terrain_atlas.ts \
        web/src/scene/terrain_flat.ts web/src/ui/tour_stops.ts
```

- [ ] **Step 4: Confirm the corrupted blueprint is gone and left no dangling references**

Task 0 already deleted `docs/project_blueprint.md`. Verify it stayed deleted and
that nothing links to it:

```bash
test -e docs/project_blueprint.md && echo "STILL PRESENT — stop" || echo "gone, as Task 0 left it"
grep -rn "project_blueprint" docs/ || echo "no dangling references"
```

It was never in `docs/index.md`, so no index edit is needed — the grep confirms that.

- [ ] **Step 5: Verify the build still passes with the newly tracked files**

```bash
cd web && npx tsc --noEmit && cd ..
```

- [ ] **Step 6: Commit**

```bash
git commit -m "chore: track the boot/terrain/tour modules; drop a leaked transcript

The seven web/src files were load-bearing but never added — main.ts,
terrain.ts and tour.ts all import them, so the tree did not build from a
clean clone. docs/project_blueprint.md was raw model output, including
channel tokens and a message to the reader, proposing agents that execute
SQL against the catalog — which contradicts read-only and observation-only."
```

---

## Task 4: Move the S7 check out of the request path

`plan_street_features` raises `ValueError` on an S7 violation. It is called by the live v4 planner, so a geometric property turns `/city.json` into a 500 and the exporter into a traceback. The exemption set is anchor tiles only, so a multi-tile plaza does not exempt its own remaining tiles.

**Files:**
- Modify: `src/dbtycoon/sim/town_streets.py:305-321`
- Test: `tests/sim/test_town_streets.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `find_naked_stubs(road_tiles, lot_tiles, features) -> tuple[tuple[int, int], ...]` — a pure detector returning violating tiles, sorted. Callers in Task 4 only; `plan_street_features` keeps its existing signature and stops raising.

- [ ] **Step 1: Write the failing test for the detector**

Add to `tests/sim/test_town_streets.py`:

```python
def test_find_naked_stubs_reports_a_degree_one_tile():
    from dbtycoon.sim.town_streets import find_naked_stubs

    # A three-tile spur: (2,0) touches only (1,0), so it is a naked stub.
    road = {(0, 0), (1, 0), (2, 0)}
    assert find_naked_stubs(road, set(), ()) == ((2, 0),)


def test_find_naked_stubs_exempts_every_tile_of_a_multi_tile_feature():
    """The old inline check exempted only a feature's anchor, so a 2x1 plaza
    reported its own second tile as a violation."""
    from dbtycoon.sim.town_streets import StreetFeature, find_naked_stubs

    road = {(0, 0), (1, 0), (2, 0)}
    plaza = StreetFeature(x=1, y=0, w=2, h=1, kind="plaza")
    assert find_naked_stubs(road, set(), (plaza,)) == ()


def test_planning_a_naked_stub_returns_features_instead_of_raising():
    """A geometry defect must never reach the request path as an exception."""
    from dbtycoon.sim.town_streets import plan_street_features

    features = plan_street_features({(0, 0), (1, 0), (2, 0)}, set())
    assert isinstance(features, tuple)
```

Read `StreetFeature`'s real field names in `town_streets.py` before running; if `kind` is spelled differently, match it. Do not change the dataclass.

- [ ] **Step 2: Run and watch them fail**

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/sim/test_town_streets.py -q -k naked_stub
```

Expected: ImportError for `find_naked_stubs`, and the third test raising `ValueError: S7 violation`.

- [ ] **Step 3: Extract the detector and stop raising**

In `src/dbtycoon/sim/town_streets.py`, replace the raising loop at the end of `plan_street_features` with a plain return, and add the detector beside it:

```python
def find_naked_stubs(
    road_tiles: set[tuple[int, int]],
    lot_tiles: set[tuple[int, int]],
    features: tuple[StreetFeature, ...],
) -> tuple[tuple[int, int], ...]:
    """Road tiles with exactly one orthogonal neighbour and no feature dressing
    them — property S7. Pure: it reports, it never raises. Every tile a feature
    covers is exempt, not just its anchor, because a 2x1 plaza dresses both of
    its tiles."""
    covered = {(f.x + dx, f.y + dy) for f in features for dx in range(f.w) for dy in range(f.h)}
    stubs = []
    for t in road_tiles:
        if t in covered:
            continue
        neighbours = sum(
            1
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))
            if (t[0] + dx, t[1] + dy) in road_tiles or (t[0] + dx, t[1] + dy) in lot_tiles
        )
        if neighbours == 1:
            stubs.append(t)
    return tuple(sorted(stubs))
```

- [ ] **Step 4: Run and watch them pass**

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/sim/test_town_streets.py -q
```

- [ ] **Step 5: Confirm no caller still expects the exception**

```bash
grep -rn "S7 violation" src tests
```

Expected: no hits in `src/`. If a test asserted the raise, rewrite it to assert `find_naked_stubs` is non-empty instead.

- [ ] **Step 6: Mutation-test the multi-tile exemption**

Change `for dx in range(f.w)` to `for dx in range(1)`, rerun, confirm `test_find_naked_stubs_exempts_every_tile_of_a_multi_tile_feature` fails, then restore. Control mutant: change the docstring; all tests must still pass.

- [ ] **Step 7: Commit**

```bash
git add src/dbtycoon/sim/town_streets.py tests/sim/test_town_streets.py
git commit -m "fix(sim): S7 is a detector, not an exception in the request path"
```

---

## Task 5: Make tour progress resume by stop id, and refresh the specs

The 2026-08-08 rewrite inserted `view`, `lenses`, `orphans` and `controls`. Progress is persisted as a **numeric index** (`tour.ts:113`), so every reader mid-tour silently jumped to a different stop, and three specs encode the old playlist.

**Files:**
- Modify: `web/src/ui/tour.ts:55-115`
- Modify: `web/e2e/tour.spec.ts:51-70`, `:161-176`, `:142`

**Interfaces:**
- Consumes: `TOUR_STOPS` from `web/src/ui/tour_stops.ts`, each with an `id: string`.
- Produces: persisted value is now a **stop id string**, not an index. Unknown or missing values start at 0.

- [ ] **Step 1: Read the real playlist order**

```bash
grep -n "id:" web/src/ui/tour_stops.ts
```

Write the ids down in order; the spec expectations in Step 4 must match what the demo fixture actually supports (absence stops like `no-lineage`, `quiet-city` and `weather-unknown` are skipped when the catalog contradicts them).

- [ ] **Step 2: Persist the stop id instead of the index**

In `web/src/ui/tour.ts`, replace the resume computation:

```typescript
    // Persist the stop's ID, not its index: inserting a stop must not move
    // every reader mid-tour to a different subject. An unknown ID — a stop
    // that was renamed or dropped — starts over rather than guessing.
    const savedId = restart ? null : saved;
    const resumedAt = savedId ? this.playlist.findIndex((s) => s.id === savedId) : 0;
    this.at = resumedAt >= 0 ? resumedAt : 0;
```

and wherever progress is written, store `this.playlist[this.at].id` rather than the number.

- [ ] **Step 3: Update the three stale specs**

In `web/e2e/tour.spec.ts`, replace the expected playlist in "the tour walks the city's core metaphors, in order" with the real order from Step 1. In "progress is persisted", two clicks from the first stop now land on the third id in that list — assert that id, and assert `?tour=restart` returns to the **first** id. Fix the "plain demo tour skips" expectations the same way.

- [ ] **Step 4: Run the tour specs**

```bash
cd web && npx playwright test tour.spec.ts --reporter=line && cd ..
```

Expected: all tour specs pass.

- [ ] **Step 5: Prove the persistence fix is not just a renumbering**

Add a spec asserting the point of the change:

```typescript
test("a persisted stop survives the playlist growing a stop before it", async ({ page }) => {
  await open(page, "?settle=1&lens=none&tour=1");
  await page.locator(".tour-next").click();
  const landed = await page.locator(".tour-card").getAttribute("data-stop");
  // Simulate an older/newer build whose playlist differs: an unknown id must
  // restart rather than silently land somewhere arbitrary.
  await page.evaluate(() => localStorage.setItem("tour-progress", "a-stop-that-no-longer-exists"));
  await open(page, "?settle=1&lens=none&tour=1");
  const after = await page.locator(".tour-card").getAttribute("data-stop");
  expect(after).not.toBe(landed);
});
```

Read the real `STORAGE_KEY` value from `tour.ts` and use it verbatim.

- [ ] **Step 6: Commit**

```bash
git add web/src/ui/tour.ts web/e2e/tour.spec.ts
git commit -m "fix(web): tour progress resumes by stop id, so inserting a stop moves nobody"
```

---

## Task 6: Diagnose and fix the lost selection across `R`

**This task is a diagnosis, not a known fix.** Two specs fail identically: `interactions.spec.ts:143` and `skybridges.spec.ts:42` both press `R` and find `selectedKey()` is `null`. The restore logic exists at `web/src/boot/hud.ts:315-317` and looks correct on its face, so the cause is not yet established. Follow superpowers:systematic-debugging.

**Files:**
- Investigate: `web/src/boot/hud.ts:286-320`, `web/src/boot/hooks.ts:120-140`
- Test: `web/e2e/interactions.spec.ts:143`, `web/e2e/skybridges.spec.ts:42`

- [ ] **Step 1: Reproduce in isolation**

```bash
cd web && npx playwright test interactions.spec.ts -g "R refreshes in place" --reporter=line
```

Expected: `Expected: "raw.orders" / Received: null`.

- [ ] **Step 2: Instrument the three candidate points**

Temporarily add to `web/src/boot/hud.ts` inside `refresh()`:

```typescript
      const keep = selected;
      console.log("[refresh] keep =", keep);
      ...
      console.log("[refresh] lots match =", next.lots.some((l) => l.object_key === keep));
      ...
      console.log("[refresh] restored =", selected);
```

Re-run with `--headed` off but capture console output by adding to the spec temporarily:
`page.on("console", (m) => console.log("PAGE:", m.text()));`

- [ ] **Step 3: Read the three values and pick the branch**

- `keep` is `null` → the click never registered a selection; the bug is in `select`/picking wiring after the split, in `boot/input.ts` or `picking.setTargets`.
- `keep` is set but `lots match` is `false` → the refetched document differs from the mounted one; compare `object_key` values in `./city.json`.
- `keep` set, `lots match` true, `restored` set, but the spec still sees `null` → the hook reads a different source than `selected`; inspect `selectedKey` in `boot/hooks.ts:136` and what `deps.selectedKey` closes over.

- [ ] **Step 4: Write a failing unit-level guard before fixing**

Whatever branch Step 3 identifies, the fix gets a test that fails first. If the cause is the hook reading a stale closure, the guard belongs in `hooks.ts`'s own spec; if it is the restore condition, extend `interactions.spec.ts`.

- [ ] **Step 5: Fix, then re-run both specs**

```bash
cd web && npx playwright test interactions.spec.ts skybridges.spec.ts --reporter=line
```

Expected: both pass. They fail identically today, so one fix should clear both — if only one clears, the second has a separate cause and gets its own diagnosis.

- [ ] **Step 6: Remove the instrumentation and commit**

```bash
git add web/src/boot/hud.ts web/e2e/
git commit -m "fix(web): selection survives an R refresh after the boot/ split"
```

---

## Task 7: Resolve the README's v5 contradiction

`README.md:109` describes v4's column placement; `README.md:320` claims "The v5 city-foundation planner ships today" and mentions "depth rings". v5 is flag-gated behind `DATABASE_TYCOON_PLANNER=v5`, and the ring layout is retired.

**Files:**
- Modify: `README.md:316-325`

- [ ] **Step 1: Rewrite the streets bullet to state what actually ships**

```markdown
- **Streets are mid-rewrite.** What ships by default is the v4 planner:
  lineage-driven layout in depth columns, schema bands, and POWER_LINE
  arterials. The v5 planner — schema-clustered neighbourhoods on a lattice
  that satisfies the junction-spacing rule by construction — is available
  behind `DATABASE_TYCOON_PLANNER=v5` and is not yet the default. The next
  geometry phase is planned behind a spike gauntlet: every geometry change
  gets rendered and looked at before a test is written for it, because four
  spec-first attempts at this were wrong.
```

- [ ] **Step 2: Confirm no other stale layout claims**

```bash
grep -n "ring\|ships today\|in columns" README.md
```

Line 109's "in columns" is correct for the default planner and stays. Any remaining "ring" reference must go — the ring layout is retired and stays retired.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: the README says which planner actually ships"
```

---

## Task 8: Green gate checkpoint

**No code changes.** This is the oracle the rename depends on.

- [ ] **Step 1: Clear stale bytecode and run the Python gate**

```bash
find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

Expected: all pass, 0 failures.

- [ ] **Step 2: Run the web gate to completion**

```bash
cd web && npx tsc --noEmit && npx playwright test --reporter=line 2>&1 | tail -20
```

Expected: every spec passes and the run **finishes** — do not accept a timed-out run as evidence. If it exceeds 25 minutes, raise the timeout rather than sampling.

- [ ] **Step 3: Record the counts**

Write the exact pytest and Playwright totals into `docs/log.md`. These two numbers are what Task 11 compares against to prove the rename changed nothing.

- [ ] **Step 4: Commit**

```bash
git add docs/log.md
git commit -m "docs: record the green baseline before the rename"
```

---

## Task 9: Rename the environment variables and console scripts

The unambiguous half of the rename, done first because these strings cannot be confused with the module name.

**Files:**
- Modify: `pyproject.toml`, `src/dbtycoon/webserve.py:84-86`, `Dockerfile`, `README.md`, and every file matching the greps below.

**Interfaces:**
- Produces: env vars `DATABASE_TYCOON_DB`, `_HOST`, `_THEME`, `_PLANNER`, `_WEB_DIST`, `_DOGFOOD`, `_WEB_PORT`; scripts `tycoon-city`, `tycoon-city-serve`, `tycoon-city-export`.

- [ ] **Step 1: Inventory before touching anything**

```bash
grep -rIn "DBTYCOON_\|DBT_WEB_PORT" . 2>/dev/null | grep -vE 'node_modules|\.git/|/dist/|__pycache__|\.ruff_cache|\.pytest_cache|test-results' | wc -l
```

Record the number. Step 4 verifies it reaches zero.

- [ ] **Step 2: Replace the environment variables**

```bash
FILES=$(grep -rIl "DBTYCOON_\|DBT_WEB_PORT" . 2>/dev/null | grep -vE 'node_modules|\.git/|/dist/|__pycache__|\.ruff_cache|\.pytest_cache|test-results')
perl -pi -e 's/DBT_WEB_PORT/DATABASE_TYCOON_WEB_PORT/g; s/DBTYCOON_/DATABASE_TYCOON_/g' $FILES
```

`DBT_WEB_PORT` is replaced **first**: it is the sharpest exposure, because `DBT_*` is dbt's own environment-variable namespace and a reader would fairly take it for a dbt variable.

- [ ] **Step 3: Replace the console script names**

```bash
FILES=$(grep -rIl "dbtycoon-serve\|dbtycoon-export" . 2>/dev/null | grep -vE 'node_modules|\.git/|/dist/|__pycache__')
perl -pi -e 's/dbtycoon-serve/tycoon-city-serve/g; s/dbtycoon-export/tycoon-city-export/g' $FILES
```

Then in `pyproject.toml`, rename the bare `dbtycoon` script entry to `tycoon-city` (its target module path changes in Task 10, not here).

- [ ] **Step 4: Verify nothing is left**

```bash
grep -rIn "DBTYCOON_\|DBT_WEB_PORT\|dbtycoon-serve\|dbtycoon-export" . 2>/dev/null | grep -vE 'node_modules|\.git/|/dist/|__pycache__|\.ruff_cache|\.pytest_cache|test-results'
```

Expected: no output.

- [ ] **Step 5: Run the full gate**

```bash
find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q && uv run ruff check .
```

Expected: the same totals as Task 8. A drop means a test referenced an old variable name by string.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: environment variables and scripts carry no dbt substring

DBT_WEB_PORT was the sharpest exposure — DBT_* is dbt's own env-var
namespace, so a reader would fairly take it for a dbt variable."
```

---

## Task 10: Rename the Python module to `database_tycoon`

**Files:**
- Move: `src/dbtycoon/` → `src/database_tycoon/`
- Modify: `pyproject.toml`, `Dockerfile`, every Python import, every doc reference.

**Interfaces:**
- Produces: the importable package `database_tycoon`. Every later task imports from it.

- [ ] **Step 1: Move the package with git so history follows**

```bash
git mv src/dbtycoon src/database_tycoon
```

- [ ] **Step 2: Rewrite Python import references**

```bash
FILES=$(grep -rIl "dbtycoon" . 2>/dev/null | grep -vE 'node_modules|\.git/|/dist/|__pycache__|\.ruff_cache|\.pytest_cache|test-results')
perl -pi -e 's/\bdbtycoon\b/database_tycoon/g' $FILES
```

This rewrites `from dbtycoon…`, `import dbtycoon`, `src/dbtycoon/` paths and `dbtycoon.webserve:main` alike. It also rewrites bare `dbtycoon` in prose and shell examples, which is wrong — Step 3 fixes those.

- [ ] **Step 3: Correct the shell-invocation sites**

`database_tycoon` is the *module*; the *command* is `tycoon-city`. Anywhere the old text was a command line, the replacement must be the script name:

```bash
grep -rIn "database_tycoon demo\|database_tycoon \./\|-t database_tycoon\|run.*database_tycoon\b" README.md Dockerfile docs/ CLAUDE.md
```

Fix each hit by hand: `database_tycoon demo` → `tycoon-city demo`, the Docker image tag `-t database_tycoon` → `-t tycoon-city`, and so on. Read each line and decide module-or-command; do not blanket-replace.

- [ ] **Step 4: Verify the package name landed in packaging**

```bash
grep -n "packages\|scripts" -A4 pyproject.toml | head -20
```

Expected: `packages = ["src/database_tycoon"]` and three `tycoon-city*` scripts pointing at `database_tycoon.*`.

- [ ] **Step 5: Reinstall and run the full gate**

```bash
uv sync
find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q && uv run ruff check . && uv run ruff format --check .
```

Expected: the Task 8 totals, exactly. The contract golden must still reproduce:

```bash
uv run python scripts/update_contract_golden.py && git diff --exit-code contract/fixtures/demo.city.json
```

Expected: `unchanged`, clean diff. The golden contains zero occurrences of the old name, so any change here is a real regression.

- [ ] **Step 6: Confirm nothing named dbtycoon survives**

```bash
grep -rIn "dbtycoon" . 2>/dev/null | grep -vE 'node_modules|\.git/|/dist/|__pycache__|\.ruff_cache|\.pytest_cache|test-results'
```

Expected: no output.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor: the module is database_tycoon

dbt is a trademark of dbt Labs; no name of ours should embed it. The
distribution name database-tycoon-city is unchanged, and referential use
of dbt stays wherever it is factual."
```

---

## Task 11: Rename the browser verification seam

`window.__dbt` is our abbreviation of *Database Tycoon*, which is exactly the collision to avoid: it reads as dbt. 240 uses across `web/src` and `web/e2e`, plus the `DbtHooks` type and `__dbtRefresh`.

**Files:**
- Modify: `web/src/boot/hooks.ts`, `web/src/main.ts:81`, `web/src/boot/hud.ts:310,337`, `web/src/ui/run_panel.ts:95`, every `web/e2e/*.spec.ts` and `web/e2e/*.mjs`, `web/index.html` if it references the global.

**Interfaces:**
- Produces: `window.__tycoonCity` (was `__dbt`), `window.__tycoonCityRefresh` (was `__dbtRefresh`), type `TycoonCityHooks` (was `DbtHooks`).

- [ ] **Step 1: Inventory**

```bash
grep -rIn "__dbt\|DbtHooks" web/ --include="*.ts" --include="*.mjs" --include="*.html" | grep -v node_modules | wc -l
```

Record the number.

- [ ] **Step 2: Replace, longest identifier first**

```bash
FILES=$(grep -rIl "__dbt\|DbtHooks" web/ --include="*.ts" --include="*.mjs" --include="*.html" | grep -v node_modules)
perl -pi -e 's/__dbtRefresh/__tycoonCityRefresh/g; s/\bDbtHooks\b/TycoonCityHooks/g; s/__dbt\b/__tycoonCity/g' $FILES
```

`__dbtRefresh` must be replaced before `__dbt`, or the shorter pattern corrupts it.

- [ ] **Step 3: Verify nothing is left and the types still resolve**

```bash
grep -rIn "__dbt\|DbtHooks" web/ --include="*.ts" --include="*.mjs" --include="*.html" | grep -v node_modules
cd web && npx tsc --noEmit && cd ..
```

Expected: no grep output, clean tsc.

- [ ] **Step 4: Run the full web suite**

```bash
cd web && npx playwright test --reporter=line 2>&1 | tail -20 && cd ..
```

Expected: the Task 8 Playwright total, unchanged. The seam is what the whole suite drives, so any rename miss shows up immediately.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(web): the verification seam is window.__tycoonCity

__dbt was our abbreviation of Database Tycoon, which is precisely the
collision worth avoiding — it reads as dbt."
```

---

## Task 12: Ship the web bundle inside the wheel

Today the wheel installs a server with no front end; `README.md:50` names this as "The honest limit". This is what makes a public `pip install` mean anything.

**Files:**
- Create: `scripts/sync_web_bundle.py`
- Create: `src/database_tycoon/web_dist/` (committed build output)
- Modify: `src/database_tycoon/webserve.py:89-92`
- Test: `tests/test_web_bundle.py`

**Interfaces:**
- Produces: `_default_dist() -> Path | None` with a four-step resolution order. `scripts/sync_web_bundle.py` is invoked by Task 15.

- [ ] **Step 1: Write the sync script**

Create `scripts/sync_web_bundle.py`:

```python
#!/usr/bin/env python3
"""Build the web bundle and copy it into the package as shipped data.

`web/public/` holds gitignored dev data (a demo city.json); the server
generates /city.json itself, so the release bundle must be built without it.
The Dockerfile does the same `rm -rf public` for the same reason.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
TARGET = ROOT / "src" / "database_tycoon" / "web_dist"


def main() -> int:
    public = WEB / "public"
    stashed = None
    if public.is_dir():
        stashed = WEB / "public.stashed"
        shutil.move(str(public), str(stashed))
    try:
        subprocess.run(["npm", "run", "build"], cwd=WEB, check=True)
    finally:
        if stashed is not None:
            shutil.move(str(stashed), str(public))

    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(WEB / "dist", TARGET)
    leaked = TARGET / "city.json"
    if leaked.exists():
        leaked.unlink()
        print(f"removed dev data that rode along: {leaked}", file=sys.stderr)
    print(f"synced {sum(1 for _ in TARGET.rglob('*') if _.is_file())} files to {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Write the failing guard tests**

Create `tests/test_web_bundle.py`:

```python
"""The wheel must carry its own front end.

`packages = ["src/database_tycoon"]` ships non-Python files inside the
package, so the bundle rides along — but only if it is actually there. A data
file that does not ship is the classic version of this bug, which is why this
resolves through importlib.resources rather than through the checkout.
"""

from importlib import resources


def test_the_packaged_bundle_exists_and_has_an_entry_point():
    bundle = resources.files("database_tycoon") / "web_dist"
    assert bundle.is_dir(), "no packaged web bundle — run scripts/sync_web_bundle.py"
    assert (bundle / "index.html").is_file(), "the bundle has no index.html to serve"


def test_the_packaged_bundle_carries_no_dev_catalog():
    """web/public/city.json is a developer's demo catalog. Shipping it would
    bake a stale city into the wheel that the server would then serve as fact."""
    bundle = resources.files("database_tycoon") / "web_dist"
    assert not (bundle / "city.json").is_file(), "dev data rode along into the package"
```

- [ ] **Step 3: Run and watch them fail**

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/test_web_bundle.py -q
```

Expected: the first test fails — no `web_dist` yet.

- [ ] **Step 4: Build the bundle**

```bash
uv run python scripts/sync_web_bundle.py
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/test_web_bundle.py -q
```

Expected: both pass.

- [ ] **Step 5: Teach the server to find the packaged bundle**

Replace `_default_dist` in `src/database_tycoon/webserve.py`:

```python
def _default_dist() -> Path | None:
    """Where the web bundle lives, most specific first.

    A repo checkout's `web/dist` wins over the packaged copy on purpose: a
    developer rebuilding the front end must see their build, and a committed
    bundle must never shadow it mid-iteration. An installed wheel has no
    checkout, so it falls through to the packaged copy.
    """
    repo = Path(__file__).resolve().parents[2] / "web" / "dist"
    if repo.is_dir():
        return repo
    packaged = Path(__file__).resolve().parent / "web_dist"
    return packaged if packaged.is_dir() else None
```

`--dist` and `$DATABASE_TYCOON_WEB_DIST` are already checked ahead of this in `main()`; do not duplicate them here.

- [ ] **Step 6: Mutation-test both guards**

Rename `src/database_tycoon/web_dist/index.html` aside, confirm the first test fails, restore. Copy any file to `src/database_tycoon/web_dist/city.json`, confirm the second test fails, delete it. Control mutant: touch a file's mtime; both tests must still pass.

- [ ] **Step 7: Un-ignore the bundle and commit it**

Confirm nothing ignores the new path:

```bash
git check-ignore -v src/database_tycoon/web_dist/index.html || echo "not ignored"
git add src/database_tycoon/web_dist scripts/sync_web_bundle.py tests/test_web_bundle.py src/database_tycoon/webserve.py
git commit -m "feat(packaging): the wheel carries its own web bundle

Closes the 'honest limit' README.md:50 names: pip install produced a
server with no front end. web/dist wins over the packaged copy in a
checkout so a developer's rebuild is never shadowed."
```

---

## Task 13: Add the trademark notice

**Files:**
- Modify: `THIRD-PARTY.md`, `README.md`

- [ ] **Step 1: Add the notice to both files**

Append to `THIRD-PARTY.md` and add near the top of `README.md`:

```markdown
## Trademarks

dbt is a trademark of dbt Labs, Inc. DuckDB is a trademark of DuckDB
Foundation. This project is independent and is not affiliated with,
sponsored by, or endorsed by dbt Labs or DuckDB Foundation. It reads the
artifacts these tools produce; the names are used only to say so.
```

Check DuckDB's actual trademark holder before asserting it; if unclear, name only dbt Labs.

- [ ] **Step 2: Commit**

```bash
git add THIRD-PARTY.md README.md
git commit -m "docs: name the trademarks we reference and disclaim affiliation"
```

---

## Task 14: Wire `tycoon city` into the CLI

**This task is in a different repository:** `~/Projects/localhost-stack` (`Database-Tycoon/tycoon-cli`). Branch it: `git checkout -b feature/city-addon`.

**Files:**
- Create: `src/tycoon/commands/city.py`
- Modify: `src/tycoon/cli.py:94-119`, `pyproject.toml`
- Test: `tests/test_city_command.py`

**Interfaces:**
- Consumes: `database_tycoon.webserve.main(argv)` from Task 10, and `tycoon.config._find_project_root()` / `tycoon.project.load_project(root)`.
- Produces: `city_cmd(port, host)` registered as `tycoon city`.

- [ ] **Step 1: Verify the root can be resolved without the config singleton**

```bash
cd ~/Projects/localhost-stack
python -c "from tycoon.config import _find_project_root; print(_find_project_root())"
```

`_find_project_root()` walks up from CWD for `tycoon.yml` or `pyproject.toml` and is a module-level function with no singleton construction. If importing it triggers config loading or `SystemExit`, fall back to reimplementing the eight-line walk-up inside `city.py` rather than importing it — the city's own `tycoon_project.py` documents why that caution exists.

- [ ] **Step 2: Write the failing tests**

Create `tests/test_city_command.py`:

```python
"""`tycoon city` is an optional add-on: the CLI must work without it installed."""

import subprocess
import sys


def test_city_appears_in_help():
    out = subprocess.run([sys.executable, "-m", "tycoon", "--help"], capture_output=True, text=True)
    assert "city" in out.stdout


def test_missing_package_names_the_install_command(monkeypatch, tmp_path):
    """A missing optional dependency is a one-line instruction, not a traceback."""
    import builtins

    from tycoon.commands.city import city_cmd

    real_import = builtins.__import__

    def deny(name, *args, **kwargs):
        if name.startswith("database_tycoon"):
            raise ImportError("No module named 'database_tycoon'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", deny)
    monkeypatch.chdir(tmp_path)

    try:
        city_cmd(port=8000, host="127.0.0.1")
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError("a missing add-on must exit non-zero")
```

- [ ] **Step 3: Run and watch them fail**

```bash
uv run pytest tests/test_city_command.py -q
```

Expected: ImportError — `tycoon.commands.city` does not exist.

- [ ] **Step 4: Write the command**

Create `src/tycoon/commands/city.py`:

```python
"""tycoon city — render this project as a city.

An optional add-on: `pip install "database-tycoon[city]"`. The import lives
inside the function on purpose, so the CLI's startup never depends on the
add-on being installed and a missing package is one line of advice rather
than a traceback at import time.
"""

from __future__ import annotations

import typer

from tycoon.utils.console import error


def city_cmd(
    port: int = typer.Option(8000, help="Port to serve the city on."),
    host: str = typer.Option("127.0.0.1", help="Interface to bind."),
) -> None:
    """Render this Tycoon project as an interactive 3D city."""
    try:
        from database_tycoon.webserve import main as serve
    except ImportError:
        error('The city add-on is not installed.\n  pip install "database-tycoon[city]"')
        raise typer.Exit(code=1) from None

    from tycoon.config import _find_project_root

    root = _find_project_root()
    raise typer.Exit(code=serve([str(root), "--port", str(port), "--host", host]))
```

Read `webserve.main`'s real argument parser before writing this line: it must receive the flags it actually defines. Read `tycoon.utils.console` for the real error helper name.

- [ ] **Step 5: Register it**

In `src/tycoon/cli.py`, add `from tycoon.commands.city import city_cmd` beside the other command imports, and register it the way `doctor_cmd` and `run_cmd` are registered (read those lines; they use `app.command()`, not `add_typer`).

- [ ] **Step 6: Add the optional extra**

In `pyproject.toml`:

```toml
[project.optional-dependencies]
city = ["database-tycoon-city>=0.1.0"]
docs = [
    "mkdocs==1.6.1",
    "mkdocs-material==9.5.49",
]
```

- [ ] **Step 7: Run the tests and the CLI's own suite**

```bash
uv run pytest tests/test_city_command.py -q && uv run pytest -q
```

Expected: new tests pass, existing suite unchanged.

- [ ] **Step 8: Commit**

```bash
git add src/tycoon/commands/city.py src/tycoon/cli.py pyproject.toml tests/test_city_command.py
git commit -m "feat: tycoon city renders the project as a city, via an optional add-on"
```

---

## Task 15: Build and verify the release candidate

**No pushing, no publishing.** This task ends at a local tag and verified artifacts.

- [ ] **Step 1: Confirm the bundle is not stale**

```bash
cd ~/Projects/pipeline-city
uv run python scripts/sync_web_bundle.py
git diff --exit-code src/database_tycoon/web_dist/
```

Expected: clean. A dirty tree means the committed bundle was stale — commit the rebuild and note why.

- [ ] **Step 2: Run every gate one final time**

```bash
find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q
uv run ruff check . && uv run ruff format --check .
cd web && npx tsc --noEmit && npx playwright test --reporter=line 2>&1 | tail -5 && cd ..
```

- [ ] **Step 3: Build the artifacts**

```bash
uv build
ls -la dist/
```

Expected: one `.whl` and one `.tar.gz` for `database_tycoon_city-0.1.0`.

- [ ] **Step 4: Prove the wheel is self-contained**

```bash
python3 -m venv /tmp/rc-check
/tmp/rc-check/bin/pip install --quiet dist/database_tycoon_city-0.1.0-py3-none-any.whl
/tmp/rc-check/bin/python -c "
from importlib import resources
b = resources.files('database_tycoon') / 'web_dist'
assert b.is_dir() and (b / 'index.html').is_file(), 'the wheel has no front end'
print('bundle ships:', sum(1 for _ in b.rglob('*') if _.is_file()), 'files')
"
/tmp/rc-check/bin/tycoon-city --help
```

Expected: the bundle count prints and `--help` works. **This is the assertion the whole release exists to make** — that a fresh install has a front end.

- [ ] **Step 5: Prove the add-on path end-to-end**

```bash
/tmp/rc-check/bin/pip install --quiet -e ~/Projects/localhost-stack
cd ~/clients/dogfood && /tmp/rc-check/bin/tycoon city --port 8123 &
sleep 8 && curl -sf http://127.0.0.1:8123/healthz && echo " — healthz OK"
curl -sf http://127.0.0.1:8123/ | head -c 200
kill %1
```

Read-only against dogfood, as the standing rule requires. If `tycoon city` cannot resolve the root, that is Step 1 of Task 14 failing late — fall back to the subprocess form.

- [ ] **Step 6: Tag both repositories**

```bash
cd ~/Projects/pipeline-city && git tag -a v0.1.0 -m "database-tycoon-city 0.1.0 — first public release candidate"
cd ~/Projects/localhost-stack && git log --oneline -1
```

Do **not** tag the CLI: its version bump belongs to its own release cycle, and this branch only adds an optional extra.

- [ ] **Step 7: Write the release notes and the draft PR bodies**

Create `docs/release-notes-0.1.0.md` with: what it is, the install line for both the standalone and add-on paths, the known issues (the CRLF-gated defects from the 2026-08-09 review, plus anything cut at the cut line), and the trademark notice. Add it to `docs/index.md` and `docs/log.md` in the same commit, per the OKF rules.

Write the two PR titles and bodies into the same file under a "Draft PRs" heading. Do not run `gh`.

- [ ] **Step 8: Commit and hand back**

```bash
git add docs/release-notes-0.1.0.md docs/index.md docs/log.md
git commit -m "docs: 0.1.0 release notes and draft PR bodies"
git log --oneline -12
git status --short
```

Report to Stephen: the tag, the artifact paths, the verification output from Steps 4 and 5, and an explicit list of anything cut. **Then stop.** Pushing, publishing and opening PRs are his calls.

---

## Self-Review

**Spec coverage.** Component 1 (naming) → Tasks 9, 10, 11. Component 2 (self-contained wheel) → Task 12. Component 3 (add-on seam) → Task 14. Component 4 (gates) → Tasks 1–8. Component 5 (release candidate) → Task 15. Trademark posture → Tasks 9–11, 13. Testing strategy → the mutation steps in Tasks 1, 2, 4, 12 and the new guards in Tasks 12 and 14.

**Known gap, deliberate.** Task 6 is a diagnosis rather than a fix, because the cause is not established and inventing one would be worse than admitting it. Its steps name the exact commands, the three candidate branches and how to tell them apart.

**Type consistency.** `find_naked_stubs` (Task 4) is used only in Task 4. `_default_dist` (Task 12) keeps its `Path | None` return. `__tycoonCity` / `TycoonCityHooks` (Task 11) are used consistently in Tasks 11 and 15. `database_tycoon.webserve.main(argv)` (Task 10) is consumed by Task 14 Step 4 and Task 15 Step 4.
