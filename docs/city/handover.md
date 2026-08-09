---
title: Session handover
description: What Database Tycoon is, where it stands at the 0.1.0 release candidate, what to do next in order, and the traps this repo has already sprung
tags: [handover, onboarding, state]
related: [log, release-notes-0.1.0, city-json-v1, run-json-v1, road-grammar, semantic-roads, agent_tasks/index]
updated: '2026-08-09'
---

# Session handover — Database Tycoon

Written for a session starting cold. Read this, then `docs/log.md` (newest
entries first — it is unusually detailed and is the real record).

## What this is

A data catalog rendered as a SimCity-style 3D city, and — per Stephen,
2026-08-05 — **"ultimately a game to see if engineers can keep the city
flowing efficiently."** The observation platform is the honest foundation:
schemas → districts (banded neighbourhoods), tables/views → buildings,
**lineage → literal streets** (the road network IS the DAG), builds → freight
on those streets, failing tests → **buildings on fire**, the database → the
power plant, plus a civic strip (public library = context inventory,
firehouse = fire-response dispatch). Read-only against the catalog, always.

Named **Database Tycoon**; directory still `~/Projects/pipeline-city`
(folder rename deferred); distribution `database-tycoon-city`, module
`tycoon_city`, scripts `tycoon-city`/`tycoon-city-serve` and `tycoon-city-export`.
"Pipeline City" is retired — never reintroduce it. The Tycoon CLI
(`~/Projects/localhost-stack`, module `tycoon`) is a different product:
read its artifacts off disk, never import it.

**The 1.0 target, decided 2026-08-06** (`~/.claude/plans/fancy-wiggling-clarke.md`,
a 24-question planning interview): *a fun UI for data teams*. Audience is a
public OSS launch plus a conference/video demo — but **the success test
Stephen chose is that he uses it weekly on his own client catalogs**, so
real-catalog robustness outranks launch glitter whenever they compete.

## Current state (2026-08-09 — a 0.1.0 release candidate exists)

**Read this block first — it is the newest state.** Everything below it is
still true as history, but predates the release work.

- **There is a tagged release candidate.** Nothing is pushed and nothing is
  published. Read [`release-notes-0.1.0.md`](release-notes-0.1.0.md) first —
  it carries both install paths, the known issues, and the draft PR bodies.
- **The whole tree is committed.** The ~128 uncommitted files that this
  document used to warn about were baselined in `2968461`; `git status` is
  clean, and `ruff check` and `ruff format --check` both pass over everything.
- **555 pytest (1 skipped) + 128 Playwright green**, `npx tsc --noEmit` clean,
  and the `city.json` golden reproduces byte-for-byte.
- **Every name of ours that embedded `dbt` is gone** — module, scripts, env
  vars, Docker tag, browser global, localStorage keys. `dbt` survives only
  referentially: prose about the tool, the `objects[].dbt` contract field,
  and identifiers naming dbt's own data (`dbt_nodes`, `dbt_manifest`). The
  module is now **`tycoon_city`**; the distribution stays
  `database-tycoon-city`; scripts are `tycoon-city`, `-serve`, `-export`;
  env vars are `DATABASE_TYCOON_*`.
- **The wheel is self-contained.** `src/tycoon_city/web_dist/` is committed
  package data, so `pip install` yields a server with a front end — the
  "honest limit" the README used to name is closed. Rebuild it with
  `scripts/sync_web_bundle.py`; that is a release step, not an automated
  guard.
- **`tycoon city` exists in the Tycoon CLI**, on branch `feat/city-addon` cut
  from a local `v0.2.0`, itself cut from `tycoon-cli/main`. Its CI cannot pass
  until `database-tycoon-city` is on PyPI: `uv lock --check` fails on the
  unresolvable `city` extra, and three workflows run `uv sync --all-extras`.
  **Publish the city first, refresh the CLI lockfile, then the CLI PR.**
- **The local `v0.1.0` tag points at `ea1bdbf`, two commits behind.** It needs
  re-pointing before publish; that was deliberately left to a human.
- Three regressions from the earlier `main.ts` → `boot/` split were found and
  fixed here, all invisible to a green suite: district labels never rendered
  (`labels.render` was dropped), every `R` refresh mounted a duplicate city,
  and a getter-only assignment threw inside a swallowing `catch` so refresh
  silently aborted half-way.
- **v4 is still the default planner** and the `city.json` golden is still frozen
  against it. v5 runs only under the env flag.
- **35 pytest in `sim/town_v5_plan.py`** (was ZERO). 32 pass. 3 S8 tests
  document a KNOWN FINDING: the handover claims "S8 holds by construction"
  (0 violations on dogfood), but on small fixture catalogs S8 violations DO
  occur (large intersection clumps of 10–26 tiles). This is catalog-scale
  dependent — the property may hold at production scale. The 3 failing tests
  are marked as documented findings, not bugs. See `test_town_v5_plan.py`
  lines 106–142.
- `sim/road_junctions.py` (the S8 detector) is pure, tested, mutation-checked
  and **deliberately unwired** — same status `town_endings.py` has.
- ~~The working tree carries ~50 uncommitted files with 19 ruff errors.~~
  **Resolved 2026-08-09**: baselined in `2968461`, and the lint errors are
  fixed. The CRLF defects those files carried are still real but sit behind
  `?crlf=1` — see the release notes' known issues.

### The one thing Stephen still wants and has NOT got

His original words, 2026-08-07: *"The buildings cant be lined up linearly like
that... Find ways to randomly cluster them so most of the buildings have a
fairly similar median radius from each other."*

v5 answers the ROADS but not that. Measured on dogfood: the collinearity share
(lots in a run of 4+ sharing an edge line) is **0.86 under v5 against 0.56 under
v4** — the neighbourhoods read as neighbourhoods, but rows *inside* a precinct
still line up. It traces to a documented invariant: `Precinct` promises *"every
block of a precinct is the same shape; the variation is between precincts, which
is what keeps the district reading uniform."* That promise IS the rows.

Two dead ends already measured, so do not re-run them: jittering lots inside
their block puts 16 lots on top of each other and 17 in the carriageway; blue
noise over the precinct, 11 and 33 of 42. Staggering whole neighbourhoods does
nothing (0.87) because the collinearity is inside a precinct, not between them.
The live proposal is to vary block shape WITHIN a precinct while frontage holds
by construction — which requires splitting `town_blocks.py` (489 lines against
the 500-line law) first, and is **waiting on Stephen** because it breaks that
invariant.

## Phase history (2026-08-06, after phases 0, 1, 1b and 2)

- Today's tree is the linear phase history: baseline snapshot → Phase 0
  (web split / contract seams / loader fixes) → Phase 1 → Phase 1b → Phase 2,
  with each workstream's own `w/…` worktree branch still around. **Nothing is
  pushed** — 125 commits ahead of `main` when the 1.0 plan was written, plus
  today's (the push question is *closed*, not open — see below).
- As of that date: 465 pytest (1 skipped) + 102 Playwright green (today's
  counts are 510 and 118 — see the current-state block above).
- The contract golden reproduces byte-for-byte from a fresh export.
  `city.json` is still **version 1**: everything added today was additive.
- Two contract documents now: `docs/city-json-v1.md` (byte-stable) and the new
  `docs/run-json-v1.md` (`/runs.json`, `/runs/<id>.json` — id- and
  timestamp-bearing, therefore deliberately NOT byte-stable and with no golden).

**Streets v5 is drivable now:** `DATABASE_TYCOON_PLANNER=v5 uv run tycoon-city <src>`
selects the schema-clustered, S8-clean planner (`sim/town_v5_plan.py`). Unset,
v4 runs and the golden is unaffected. Accepted on sight by Stephen 2026-08-07
("this is a lot better now"), so v5 geometry may now earn tests; it has NONE
yet. See the 2026-08-07 log entries for the measured before/after and the three
known gaps.

**Running it.** Demo: `uv run python scripts/make_demo_tycoon.py && uv run
tycoon-city demo-tycoon/` → :8000 shows everything at once, and the demo project
now contains a **real failure cascade** (an errored `stg_customers`, three
skipped downstream models, one skip that is not downstream) so run replay has
something to replay. Real thing: `uv run tycoon-city "$DATABASE_TYCOON_DOGFOOD"`
— point that at a real tycoon project (locally, the dogfood pipeline); it is the
standing acceptance test, weekly, and the same variable
`tests/catalog/test_load_context.py` reads for its opt-in canary. Dev loop: `cd web && npm run dev` → :5173
(`DATABASE_TYCOON_WEB_PORT` for parallel worktrees); ad-hoc screenshots via
`node e2e/shot.mjs <out.png> [query]`, street-level via `e2e/streetshot.mjs`.
The main e2e suite is pinned to the plain demo.duckdb export in `web/public`;
the POSITIVE paths are pinned by `e2e/rich.spec.ts` against the committed
`e2e/fixtures/rich.city.json` via route interception (regeneration recipe in
that file's header).

### Where the city stood before today (still true)

Streets v4 shipped **both halves** on 2026-08-05 — planner (`town_rows.py` /
`town_streets.py` / `town_plan.py`, `DagPlan.street_features`, property S7:
no naked stub) and renderer (3D sidewalk curbs from `scene/road_mask.ts`,
apron/dock/plaza meshes). Also standing: graph-driven placement with schema
bands, affinity clusters, sibling blocks and 2×2 footprints; traffic that only
restates real data movement; the road-load overlay (`T`); fires + firehouse +
library + wear-and-tear with contractor vans; the full HUD; the RoadNet rule
that **every** vehicle class drives on roads.

### What landed 2026-08-06 (each phase has a detailed log entry)

1. **Phase 0 — structural prep and real-catalog correctness.** `main.ts`
   499 → 372 (`boot/mount.ts`, `boot/hooks.ts`, `ui/overlays.ts` with the
   `OverlayRegistry`); `export/city_json.py` 444 → 164 + `export/blocks.py`;
   all five reserved seams (`budget`, `weather`, `joins`, `objects[].usage`,
   `objects[].semantic`) cut in **once**, empty, so four parallel workstreams
   could not race the golden; the latent district contract-test gap closed with
   a `mixed_schema` fixture. Then five correctness fixes that only bite at real
   scale: the `MAX_OBJECTS` cap that dropped every view (and therefore every
   street) on a 600-object catalog while telling only the logger; bare-name
   lineage now parsed with sqlglot instead of regex-scanned through string
   literals and comments; `prefer_target` notes that claimed a filter that never
   ran; the server binds `127.0.0.1` by default; and a 500-object catalog now
   loads in 2.25 s, down from 10.40 s, with an identical edge set.
2. **Phase 1 — four workstreams in parallel.** Run replay's Python half
   (`run_nodes` at every status, `export/run_json.py`, `failure_cascade` as a
   join of three measured facts, a sentinel test keeping ids and timestamps out
   of `city.json`); budget / usage / weather, all measured, each with its own
   absence rule; the OSI loader (`catalog/osi.py`) with `joins[]` kept separate
   from `edges[]`; streets v5 spikes 0–1 (nothing wired in).
3. **Phase 1b — the web halves.** `sim/run_replay.ts` (a pure state machine:
   `stateOf(key)` is a total function of the cursor), `ui/run_panel.ts`, the OSI
   inspector; streets v5 spike round 2 (block shapes, depth-column wrapping, the
   unused-line-width-0 fix).
4. **Phase 2 — the role layer.** Four lenses + `?tour=1`; six stateless
   achievements (`export/achievements.py`); a demo cascade so replay's headline
   demos as a cascade rather than as one fire; streets v5 spike 2 (lots on
   frontage, every lot fronting a street by construction).

### Decisions taken today from spike PNGs

- **Streets v5 `cell_size = 2`** is the default (`resolve_coordinates`) — cell 1
  reads as a circuit board and spends a tile of street per tile of lot.
- **Block fill gets fixed by variable-size blocks, not by merging thin bands** —
  merging would break the rule that **districts stay 1:1 with schemas**, which
  is load-bearing for every district-keyed feature (plates, weather cells,
  labels, achievements).

## Next session: start here

Four items need **no decision from Stephen**. Recommended order, and the reason
for that order is that the first covers code just added and the second and third
are correctness bugs on his weekly-use path (his stated success test is using
this on real client catalogs every week).

1. **Test `sim/town_v5_plan.py`. It has zero coverage.** What to assert, and
   each of these is a real property rather than a restatement of the code:
   S8 holds over the v5 planner's own road tiles (use `road_junctions.
   check_junctions`, which exists for exactly this and is still unwired);
   the plan is deterministic (same catalog twice → identical `DagPlan`, which is
   what `city.json` byte-stability rests on, and the BFS tie-break in `_bfs` is
   the thing that could break it); frontage is 0 (every lot has a road tile
   orthogonally adjacent); every measured edge resolves to a route; and **the
   flag is off by default** (no env var → `plan_dag_layout`). Mutation-test each
   guard per the rules below, and beware the degenerate-fixture trap: a fixture
   whose schemas all sit at one depth cannot tell schema grouping from depth
   grouping.
2. **The `.duckdb` mtime/WAL staleness trap** (found via dogfood, 2026-08-07).
   **FIXED (2026-08-08).** DuckDB can leave 10 MB of committed writes in a
   `.wal` sidecar, so the main file's mtime stays old while the content has
   changed — dogfood's read 2026-07-25 after a build that day. `webserve`'s
   `_SourceCache` keys on the mtime and size of every file behind the source,
   so it would serve the OLD catalog and the footer would date it as current.
   That violates the standing rule that unknown never renders as stale. Fix:
   stat the `-wal` sidecar too (and any `.tmp` dir), or key on content. Test
   added: `test_fingerprint_includes_duckdb_wal_sidecar` in `test_webserve.py`.
   The fix is in `webserve.py:_fingerprint` — it now checks for `-wal` sidecars
   alongside every `.duckdb` file.
3. **The run-history key-matching bug is OURS, not dogfood drift.** A subagent
   proved it from the dogfood side: all 164 run-history node names are present in
   the refreshed `manifest.json`, no model has been renamed or dropped, and the
   manifest's 40 models + 2 seeds map 1:1 onto the 42 relations in
   `dogfood_dev.duckdb`. Yet the loader reports `5 of 164 nodes … do not match
   anything in this catalog`. Leading hypotheses, unverified from our side: the
   **4 tests whose only parent is a seed** (no `model.*` entry in `depends_on` at
   all) plus the **1 test with two model parents** (ambiguous single-key parent
   lookup) = exactly 5; and separately, generic tests have **4** dot-separated
   id components (`test.pkg.name.hash`) while the 9 singular tests have **3**, so
   any fixed-component parser mis-keys one group (the history splits 115/49).
4. **Two stale lines in this very file, now corrected but worth knowing**: the
   `tycoon-city demo` subcommand DID land (it works; `webserve.py:393` dispatches it
   before argparse) and the Dockerfile ALREADY has `--no-editable` (line 44, with
   a comment explaining why). Both were listed as open for a while.

### Waiting on Stephen before touching

- **Varying block shape within a precinct** — the only live route to fixing the
  linearity complaint, and it breaks `Precinct`'s documented one-shape promise
  and needs `town_blocks.py` split first. See the current-state block.
- **Whether v5 becomes the default.** If yes: `city.json` **version 2**, the
  golden regenerated in one reviewed commit, and `README.md`'s "Reading the map"
  rewritten — it currently describes placement "in columns" by lineage depth,
  which v5 replaces, so it would be actively wrong the moment v5 ships.
- **dogfood source freshness.** `dbt source freshness` was run and returned
  "Nothing to do." — **not one** of the 17 source tables declares `freshness:` or
  `loaded_at_field:`, so `sources.json` is a valid but EMPTY snapshot and the
  city has zero weather cells for a real reason. A concrete config was drafted
  (all 17 are dlt-loaded, so `loaded_at_field: "to_timestamp(cast(_dlt_load_id
  as double))"` works uniformly) but deliberately NOT applied: it is a
  source-tree change to a production-adjacent repo. Related dogfood findings, for
  whoever picks it up: three `stg__dlt_*` models interpolate `catalog.schema.
  table` as strings instead of using `source()`, so they have ZERO lineage edges
  and are invisible graph roots; `dbt docs generate` overwrites `run_results.json`
  with an all-success `generate` result, so it must run BEFORE `dbt build`, and
  dogfood's own README has them in the harmful order.

## Older open work, in rough order

- **Streets v5, the rest of the spike gauntlet** — spike 3 (arterials +
  surfaces: does it still read as flow? is the sprawl rank preserved?), 4
  (hierarchy widths + step-down, both `WIDTH_MEASURE` candidates side by side
  for Stephen to pick from), 5 (junctions / loops / endings, S7 extended to
  dirt), 6 (full 3D acceptance: "does this read as a city?"), 7 (dirt → join dry
  run). **No test before its PNG is accepted** — that process is the answer to
  four spec-first geometry failures. Then the flip: `city.json` **version 2**
  (`streets[]` with `width_class` + `surface`, `ROAD_DIRT`, `districts[].texture`,
  `lots[].frontage`), v4 to `town_dag_legacy.py` for one green cycle, goldens and
  fixtures regenerated in one deliberate reviewed commit.
  Note `sim/town_blocks.py` is at **499 lines** against the 500-line law —
  it must split at the next change, not after.
- **Pavement fraction is still the unfixed streets v5 defect** (60% at cell 1;
  40% at cell 2 only because the lots are bigger). Spike 2 did not address it.
- **Phase 3 — OSI-B: join streets.** `plan_arterials(..., surface="join")` paves
  dirt into marked join streets; blocked on v5 merging.
- **Launch polish (Phase 5), all still open:** ~~no `LICENSE` file~~ — **done**: MIT `LICENSE` and `THIRD-PARTY.md` both exist, and a trademark notice ships in the README; `README.md`'s
  "Reading the map" section still describes the **retired ring layout** and
  would read as a bug to launch traffic; tour copy was rewritten 2026-08-08
  to cover the 3D view, four lenses, controls, orphans, and POWER_LINE
  arterials (see `web/src/ui/tour.ts`); `meta.json` sibling for static
  exports; Docker `--no-editable` check; npm majors (TS 7, Vite 8, zod 4)
  as their own pass; PyPI publish; public repo flip.
- **The `tycoon-city demo` subcommand** (demo project baked into the wheel, no
  runtime dependency on `scripts/make_demo_tycoon.py`) was planned for Phase 2
  and did **not** land.
- District labels still stack when bands are adjacent; far-view residential
  contrast is low. A dedicated **works depot** for the contractor vans is
  explicitly out of 1.0 (they keep sharing the firehouse).
- **CRLF blueprints 2–3 are OUT of 1.0** — they stay archived for agents.
  `task_weather_module.md` is superseded by the measured weather that shipped.

### Waiting on Stephen

- **The public repo name** — needed before the URL is minted.
- **`WIDTH_MEASURE` for hierarchy widths** — carriers vs downstream-closure.
  Both get rendered side by side in spike 4; he picks from the PNG when routing
  lands.
- **`edges.rate`** — retire in favour of `daily_load_s`, or re-derive it. Still
  emitted today; the recommendation is retirement, but it is a contract call.
- Older, still unanswered: `dbt source freshness` in dogfood (client-ish repo —
  ask first); the big-raw-source ending precedence (dock vs plaza, a one-line
  flip).

### Decided, do not re-raise

- **Pushing the branch: no.** Asked three times on 2026-08-06; the answer each
  time was "not yet". The single-point-of-loss risk is known and accepted.
  Do not frame this as an open question again.
- Achievements are **stateless** (counts, not minted trophies) — shipped that way.
- **CRLF is out of 1.0**; **local DuckDB only**; **MIT**; **tycoon-CLI
  integration is deferred to that product's 0.2.0** (artifact-contract-only
  stands); **observation + achievements only — no player verbs.**

## Standing directions (Stephen, in force)

- **Facts wear provenance; absence stays named; unknown never renders as
  stale.** The three shapes this took today: `$0` is a fact but
  `$0`-because-unpriced is null; no freshness verdicts means **no** weather
  cells, because all-clear would be clear-because-unknown wearing
  clear-because-fine; a catalog with no manifest has `state: "unknown"`
  coverage with met/have/need all null, never `met: false, have: 0`.
- **A lens re-weights presentation, never arithmetic.** Ordering and defaults
  only, every hook after the numbers are computed; the cross-lens byte-equality
  test is what keeps it honest.
- **The game thesis: flow efficiency.** Sprawl, load, cost, fires are the
  scoreboard — all measured.
- **Property S8, 2026-08-07: "You cant have two consecutive intersection
  tiles."** An intersection is a road tile with ≥3 road neighbours; consecutive
  means orthogonally adjacent. It is the constructive form of the no-asphalt-plaza
  rule S7 could never express — S7 polices road *ends*, nothing policed road
  *area*, and a contiguous paved area is nothing but mutually adjacent
  intersections. v4 fails it everywhere (dogfood: 984 violating pairs, one
  207-tile clump); the v5 lattice satisfies it by construction. Full rule and
  baseline in `docs/road-grammar.md`.
- **Paint every road variant, not just the straights.** Before 2026-08-07 only
  the two pure straights carried a centre line, so on a real catalog — where
  nearly every road tile is fused — the network rendered as a featureless slab
  and hid the plaza defect completely. Each mark must state something TRUE about
  the tile (a T's stop bar goes on the stem, because the minor approach yields).
- **Declared ≠ observed.** `joins[]` (OSI, declared) stays separate from
  `edges[]` (measured); solid/dashed in the UI; a declared join may never read
  as observed data movement.
- **One producer per document, and no second source of truth in the client** —
  `failure_cascade[]` is computed in Python and replayed, never re-derived.
- **Engine VERSIONS, like Pokémon games (stretch goal):** this build is the
  vanilla DuckDB / local-only version; MotherDuck ("ducklings") and Snowflake
  ("warehouses") later — query history is their headline differentiator, which
  is why `usage.source` exists as a discriminator today.
- **Semantic roads (Apache Ossie / OSI):** joins become roads, documentation
  builds the city out of the dirt. The loader and `joins[]` shipped; the
  streets themselves are Phase 3.
- **Incentivize documentation**: the library is the surface; coverage counts are
  real artifacts, achievements are counts, never points.
- Never push, never open/close/merge PRs, never post outbound without asking.
  No test touches the real dogfood project unless
  `DATABASE_TYCOON_DOGFOOD` is set. Files under ~500 lines. Subagents never
  run on the Fable model — explicit `model` override on every Agent call.

## Traps this repo has already sprung — read before writing tests

**The dominant failure mode is the wrong-axis test**: asserting the right
value on an axis that cannot fail. Nine escaped in one early session; the
2026-08-05 sessions caught more only by mutation checks. Catalogue: memory
`wrong-axis-test-failures.md`. The rules:

1. **Mutation-test every guard**: break the exact thing it names, watch it
   fail, restore from an in-memory copy — never `git checkout`.
2. **`PYTHONDONTWRITEBYTECODE=1` + clear `__pycache__`** — same-length edits
   inside one second get served from stale bytecode; two verdicts were
   contaminated that way.
3. **Render it and look** — `web/e2e/shot.mjs` (in-repo on purpose;
   scratchpad harnesses get wiped). Build-before-spec for all geometry: FOUR
   spec-first geometry attempts have been wrong here, and the streets v5 spike
   gauntlet exists because of them.
4. **A degenerate fixture makes a guard unfalsifiable, and the suite will not
   tell you.** Three escapes today all had this one shape, and all three were
   fixed by adding a *fixture*, not an assertion: the achievements fixture had
   no non-dbt object, so "the whole city" and "the dbt-managed set" were the
   same set; every OSI factory object was lowercase, so a **case-sensitive**
   match passed the entire suite; and streets v5's round-1 bench had no schema
   whose member keys sort differently from their names, so a `members[0]`
   determinism mutant survived until the `dotted-tie` fixture existed. Before
   trusting a guard, ask what the fixture makes *impossible* to observe.
5. **A guard that cannot be falsified gets deleted, not decorated.** Run
   replay's edge filter went that way today; the plaza pad's dead branch went
   the same way on 2026-08-05.
6. **Python heredoc patches:** verify every "patched OK" print — a failed
   assert mid-script leaves earlier edits unwritten.
7. **Parallel checkouts must not share dev-server ports** — a screenshot of
   the wrong checkout looks fine and lies. Worktree agents use their own
   `DATABASE_TYCOON_WEB_PORT` and copy untracked assets (demo.duckdb, web/public)
   themselves.
8. **Serialize contract changes.** Four workstreams adding `city.json` keys in
   parallel is four races against the golden and the zod schema; the answer that
   worked was one commit cutting every seam in empty, up front.
9. **A finding the user cannot DRIVE is not a delivered feature** (2026-08-07,
   the session's most expensive mistake). A spike sheet was produced, measured
   and reported with "not wired into anything" on the fourth line; Stephen went
   to test the app and said *"Im not seeing the clustering of schemas that I
   asked for."* If a deliverable is spike-only, that belongs in the FIRST
   sentence. He tests the running app, not the report.
10. **The demo catalog cannot reproduce real-catalog defects, and four spike
    rounds missed a 17:1 pavement ratio because of it.** demo.duckdb yields 24
    road tiles and zero intersections; dogfood yields 833 and 601. Measure
    geometry on a real project (`$DATABASE_TYCOON_DOGFOOD`, read-only) before
    believing a green sheet.
11. **A metric can crown the very defect it was written to catch.** `nn_iqr`
    (spread of near-neighbour distance) was the literal reading of Stephen's
    "similar median radius" request — and a perfect lattice scores **0.0**, so
    optimising it alone would have recommended the striped grid he rejected. It
    needed a second, opposed metric (`linear`) to say anything true.
12. **A spike's own metrics get the degenerate-fixture treatment too.** The
    first cluster sheet reported the jitter and blue-noise panels as CLEAN: it
    measured missing frontage but not lot-on-lot overlap or lots standing on
    pavement, and the only trace of 16 overlapping buildings was a `lot` tile
    count quietly falling 214 → 199. Ask what the instrument cannot see, not
    just what the layout does.
13. **A contact sheet whose lots are filled but not OUTLINED is unreadable** —
    ten neighbouring lots merge into one grey bar and you cannot tell one
    building from a block of them.

## Environment gotchas

- Playwright: `channel: 'chrome'` + `--use-angle=swiftshader
  --enable-unsafe-swiftshader`; serve over HTTP, never `file://`.
- `uv sync` installs editable — the Dockerfile needs `--no-editable`.
- No local MotherDuck token: the `md:` connection path is still untested.
- The :8000 server (`uv run tycoon-city <src>`) serves `web/dist`: rebuild
  (`npm --prefix web run build`) AND restart after client changes; browsers
  cache index.html (hard refresh). It now binds **127.0.0.1** by default —
  use `--host` / `$DATABASE_TYCOON_HOST` to expose it, and know what you are exposing.
- `R` re-serves from `_SourceCache` unless a file behind the source changed;
  signals (build ages) are still re-derived on every hand-out.
- The session's tool-permission classifier can flake ("temporarily
  unavailable" on every write): reads still work — stage work, retry.
- **`uv run ruff format .` rewrites the whole tree**, including the ~50
  uncommitted WIP files that are not yours. It is semantics-only and pytest stays
  green, but it pollutes `git diff`. Format only the paths you touched.
- **A `.duckdb` file's mtime lies while writes sit in its `-wal` sidecar** — see
  next-session item 2. This is a correctness bug, not just a gotcha.
- **Ports collide across the tools**: `:5173` is the Vite dev server, `:8000` is
  both the documented container port and the default `tycoon-city` port, so a local
  server must be stopped before `docker run -p 8000:8000`. Use distinct ports
  when comparing planners (v4 on one, `DATABASE_TYCOON_PLANNER=v5` on another) — a
  screenshot of the wrong one looks fine and lies.
- **A stale `.git/index.lock`** (hours old, no `git` process running) blocks
  every git command. Check `ps` first, then remove it.
- **`sqlglot` prints `Applying array index offset (-1)` to stdout** while parsing
  real view SQL — it is sqlglot's own print, not ours, and it leaks into the
  server log. Cosmetic, but it will read as our bug at launch.

## Standing decisions — do not re-litigate

| Decision | Why |
|---|---|
| Renderer is **web/Three.js** | Ursina cannot render headless on macOS; render-and-look is this repo's best defect detector |
| **Streets ARE the lineage; placement is graph-driven** | Stephen's redirect, refined repeatedly; the ring layout is gone and stays gone |
| **Do not import the `tycoon` package** | Pre-1.0, cwd-bound singleton, `SystemExit` in load |
| Traffic/fires/trucks/overlays **restate measured facts** | Anything else is theater; simulated content is flag-gated and labeled |
| `city.json` v1 is **byte-stable** | uuid/timestamp-bearing records (runs, CRLF requests/shipments) live in their own documents |
| **Observation + achievements only** for 1.0 | No player verbs; a catalog is not a toy to edit |
| **Local DuckDB only** for 1.0 | Engine-neutral wording stays, engine versions come later |
| **MIT licence**, pip + Docker | Matches the public Database Tycoon CLI |
| CRLF is the **Simulated layer**, and is **out of 1.0** | Own fields, tick+seed, never mutates derived facts |

## Where the records live

| What | Where |
|---|---|
| Detailed history and reasoning | `docs/log.md` — newest first, the real record |
| Contract | `docs/city-json-v1.md` + golden `contract/fixtures/demo.city.json` |
| Run replay documents | `docs/run-json-v1.md` — not byte-stable, no golden, by design |
| Street grammar, legal endings (S7), junction spacing (S8) | `docs/road-grammar.md` |
| The S8 detector (pure, unwired, mutation-tested) | `sim/road_junctions.py` + `tests/sim/test_road_junctions.py` |
| The v5 planner (35 tests, 3 S8 documented findings) | `sim/town_v5_plan.py` + `tests/sim/test_town_v5_plan.py` |
| Clustering evidence: 6 panels + metrics | `scripts/spike_cluster.py` → `spike-out/cluster-sheet.png` |
| Agent blueprints (CRLF, archived for 1.0) | `docs/agent_tasks/` — spec + tasks, index inside |
| Design sketches | `docs/semantic-roads.md`, `docs/hud-design.md` |
| The 1.0 plan | `~/.claude/plans/fancy-wiggling-clarke.md` |
| Cross-session facts | `~/.claude/projects/-Users-ssciortino-Projects-marvin/memory/` — start at `database-tycoon-game` |

## Stephen's working preferences, observed

- Directs in rapid short strokes mid-session and expects the engine to keep
  moving; capture his verbatim phrasing in log entries — it IS the design
  record.
- Proportionate verification: mandatory for geometry/visuals, light for
  plumbing. Report failures plainly; under-claim rather than fabricate.
- Reviews **pictures**, not prose, for anything spatial: the spike gauntlet
  hands him PNGs and waits.
- Route bulk single-file analysis to the local LM Studio model (rate-limit
  headroom); it is useless across files.
- Never push/PR/comment outbound without asking.
