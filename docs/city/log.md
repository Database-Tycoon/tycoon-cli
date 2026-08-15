---
title: Documentation log
description: Chronological record of documentation changes
tags: [log]
related: []
updated: '2026-08-14'
---

# Log

- 2026-08-15 — **Data-cli metaphor audit** (`023a663` on `feat/data-cli`,
  PR #207): every city claim in the fire/layers/explore commands checked
  against what the renderer draws. Vocabulary aligned (fire trucks,
  contractor vans, worn facades, district fog), the fleet honesty rule ("a
  vehicle means a problem is awaiting response, never a running fix") stated
  in every command, the fake `unreachable` stat removed (no contract field;
  reachability is by construction), `tycoon.districts` renamed back to
  `tycoon.layers` (district = schema plate; the layers are the RINGS). Bugs:
  `fire --run` ignored its argument; statuses read from `manifest.json`
  (they live in `run_results.json`); three groups wired as one-command
  sub-apps forcing `tycoon fire fire`-style invocations. New docs:
  `commands/fire.md`, `commands/data/layers.md`. Verified live on dogfood —
  `tycoon fire` surfaced the failing `assert_toggl_deel_hours_variance`.

- 2026-08-14 — **Published to the tycoon-cli remote; PR stack repaired.**
  `feat/city-addon` fast-forwarded with the day's commits (merge resolution,
  radial inversion, ruff-format). The 8/12 stacked PRs #205/#206/#207 were
  found mis-carved: #206 (`feat/city-sim`) and #207 (`feat/data-cli`) had
  committed, unresolved conflict markers (nine and seven files), were based
  on `main` while depending on each other's content, and #207 additionally
  carried the abandoned `pipeline_city` rename plus Xcode user-state files.
  Both heads were rebuilt as true stacks — #206 = `feat/city-engine` + one
  sim-slice commit (resolved planner + radial inversion + suite fixes),
  #207 = `feat/city-sim` + one data-cli commit (fire/layers/source_explorer,
  layers→districts, 0.2.0, `pipeline city`→`tycoon city`, and re-registering
  `city` in cli.py, which the old carve had dropped) — bases retargeted so
  CI runs the stacked trees. Merge order: #205 → #206 → #207.

- 2026-08-14 — **Radial inversion: gold downtown, sources on the periphery**
  (Stephen's directive, same day: "density should generally radiate outward…
  core/gold models central… surrounded by the major int models… fan out to
  the smaller source neighborhoods"). The ring index is now the schema's
  longest-chain depth over the CROSS-SCHEMA edge graph
  (`layout.longest_chain_depths`, extracted from `compute_depths`), inverted —
  mean member depth could not express the directive (it banded dogfood's
  `mart` and `int` together). Within-ring ties (the real conflict: an 18-way
  tie of depth-0 source schemas on dogfood) break decisively on cross-schema
  fan-out desc, then member count desc, then name. Observed on dogfood:
  routing IMPROVED — median route 229 → 36 tiles (total 11,249 → 2,795),
  congestion halved (worst tile 47 → 22 routes), map 99×161 → 96×135 —
  because consumers are now central, producers reach them radially. Two
  fixture-truth updates: S8 now HOLDS under the fan-in fixture (flipped per
  the old test's own instruction), and the plaza-forecourt "starts as grass"
  precondition is no longer constructible (downtown kerbs are through-streets;
  the paved-on-map assertion stays). Golden regenerated again — same review
  process as the morning's contract change. Suite: 563 passed, 6 skipped.

- 2026-08-14 — **Ring-planner promotion reconciled with the contract.** The
  working tree makes the ring planner (`town_plan.py`, v5 lineage) the sole
  default — the `DATABASE_TYCOON_PLANNER` switch and the v4 depth-column path
  are gone from `generator.py`. Consequences landed as one deliberate contract
  change: the golden (`contract/fixtures/demo.city.json`) regenerated via
  `scripts/update_contract_golden.py`; `districts` redefined in
  `city-json-v1.md` from "bounding rect of connected lots, orphans excluded"
  to the schema's zoned precinct rect housing every member (ring zoning has no
  suburb, so the stretched-plate failure mode is impossible by construction);
  a big lot's forecourt pad may flank either side of the building. Also fixed
  six carried-over test files (plus `update_contract_golden.py`) whose
  `parents[N]` anchors still resolved to `tests/` instead of the repo root
  after the pipeline-city absorb, restored `tests/fixtures/tycoon_factory.py`
  as the re-export of `tycoon_city.demo.factory` (a prior session had stubbed
  it), and module-skipped `test_layout_plan.py` (pure v4 geometry). Suite:
  560 passed, 6 skipped. **Awaiting Stephen's review**: the golden diff and
  the districts redefinition are the contract calls.

- 2026-08-09 — **Release candidate made honest, and the tour stopped reading a
  dead city.** The final whole-branch review found the release notes claiming a
  bundle-drift *guard* that was only ever a manual release step, and documenting
  `DBTYCOON_PLANNER` — a broken instruction and the last trademarked string
  outside deliberate historical quotation. Both corrected. The substantive bug:
  `boot/hud.ts` handed the **boot-time** document to `Tour` and
  `installRunReplay` while every other consumer got `currentDoc`, so after an
  `R` refresh the tour narrated and flew against a city that had already been
  unmounted; `run.apply()` also ran one line before the swap. The same stale
  read was in `visit()` and the `?selected=` path (which additionally threw on a
  temporal-dead-zone reference during boot — a path with no e2e coverage).
  Fixed together, with a spec that moves every lot under a live tour and asserts
  the next stop still lands on its subject: 127 → 128 Playwright.

  Two artifact-hygiene fixes with the same root cause — hatchling reads only the
  root `.gitignore`. An earlier build had packaged `node_modules`, the agent
  planning bundle and `demo.duckdb` into a 25 MB sdist. This wave found the same
  class again in documentation: `docs/log.md` (this file, a session diary),
  `docs/handover.md`, `CLAUDE.md`, `docs/local-ai-capacity.md` and
  `scripts/spike_cluster.py` were all bound for PyPI, naming `~/clients/…` and
  `~/.claude/…` paths. The rule now stated in `pyproject.toml` is *who a file is
  addressed to*: a reader of the package, or someone working on it. Sdist
  823K → 658K. What ships is the README, the contract documents, the city's own
  design sketches, and the licences.

  Also: `THIRD-PARTY.md` attributed three.js and zod to `web/dist` rather than
  the path the wheel ships; `sync_web_bundle.py` deleted the committed bundle
  before checking the build had produced one.

- 2026-08-09 — **Task 15: the 0.1.0 release candidate, built and verified.**
  New page [release-notes-0.1.0.md](release-notes-0.1.0.md): what ships, both
  install paths, the trademark notice, the known issues, and the two draft PR
  bodies (this repo, and the CLI's `feat/city-addon`). Every gate run to
  completion — pytest 555 passed / 1 skipped, ruff clean, `tsc --noEmit` clean,
  Playwright 127 passed, the golden `city.json` regenerating unchanged, and the
  committed `src/tycoon_city/web_dist/` matching a fresh `npm run build` (it was
  already current, so nothing was re-committed). Artifacts built with
  `uv build`. Two defects were found by the release process itself and fixed
  here rather than filed. **The sdist packaged 25 MB it should not have:**
  hatchling reads only the repository-root `.gitignore`, so `web/node_modules/`
  — ignored by `web/.gitignore` — went into the source distribution along with
  the `.superpowers/` planning bundle (task briefs, reports, review diffs) and
  `demo.duckdb`. An explicit `[tool.hatch.build.targets.sdist]` exclude list
  took it from 25,545,981 to 818,335 bytes; the wheel was never affected and is
  byte-identical at 384,368. **`README.md` still carried the pre-Task-12
  claim** that "the wheel does not carry the compiled JavaScript", contradicting
  the thing this release exists to assert; it now documents
  `pip install database-tycoon-city && tycoon-city demo` as the zero-setup path,
  states why a checkout's `web/dist` still wins over the packaged copy, and adds
  the add-on install line. Self-containment proved by serving, not by import: a
  clean venv holding only the wheel served `/` (17,286 bytes), the JS asset
  (716,447), `/city.json` (37,071), `/spritesheet.png` (957) and `/healthz`
  (61), all 200, out of `site-packages/tycoon_city/web_dist`. The add-on path
  was proved against the repo's own `demo-tycoon/` project rather than
  `~/clients/dogfood`, which nothing automated touches. Tagged `v0.1.0`,
  locally. Nothing pushed, nothing published; TestPyPI deliberately skipped,
  since an upload permanently consumes a version.
- 2026-08-09 — **Task 13: the trademark notice, plus two rename leftovers.**
  `THIRD-PARTY.md` and the top of `README.md` each gained the same `##
  Trademarks` section: dbt is a trademark of dbt Labs, Inc., this project is
  independent and not affiliated with, sponsored by, or endorsed by dbt Labs,
  and the name is used only to say so. DuckDB was considered and left out —
  `duckdb-1.5.5.dist-info/licenses/LICENSE` and `THIRD-PARTY.md`'s own table
  establish a *copyright* holder (Stichting DuckDB Foundation) from the MIT
  licence text, not a confirmed *trademark* holder, and nothing else in the
  repo says otherwise; asserting one without that confirmation would be a
  guess, so only dbt Labs is named. Two documentation leftovers from the
  rename campaign, found by re-grepping for old names as live-state claims:
  `superpowers/specs/2026-08-09-tycoon-city-addon-design.md`'s "Decisions"
  table and "Renamed:" paragraph were written before Task 10b reversed Task
  10 and still named the module `database_tycoon`; both now read `tycoon_city`,
  with a note on why `database_tycoon` was tried first and rejected (the
  Tycoon CLI's own PyPI distribution `database-tycoon` normalizes to exactly
  that string). Every other `database_tycoon`/`dbtycoon` hit was left alone on
  inspection: this log's own Task 9/10/10b entries and the addon plan's Task
  9/10 sections are correct historical records that quote the exact names and
  commands as they were at the time, and the CLI's own package really is
  `database_tycoon` (a different product, `~/Projects/localhost-stack`) where
  it appears in `CLAUDE.md` and `superpowers/specs/2026-08-03-city-foundation-design.md`.
  Docs-only change: `ruff check` and `ruff format --check` clean.

- 2026-08-09 — **Task 11: the browser verification seam is `window.__tycoonCity`.**
  `__dbt` was our own abbreviation of *Database Tycoon* — exactly the
  collision this rename campaign exists to remove, since it reads as `dbt`
  in every devtools console and spec file. Replaced in order —
  `__dbtRefresh` → `__tycoonCityRefresh` first (else the shorter pattern
  corrupts it), then `DbtHooks` → `TycoonCityHooks`, then the remaining
  `__dbt` → `__tycoonCity` — across `web/src` and all 20 `web/e2e` spec/mjs
  files, 250 occurrences before, all renamed. Two `localStorage` keys found
  in a later sweep, not in the original task brief, got the same treatment
  because they are just as visible in devtools: the tour's `STORAGE_KEY`
  (`web/src/ui/tour.ts`) `"dbt.tour"` → `"tycoon-city.tour"` (4 sites) and
  the lens picker's (`web/src/ui/lens_picker.ts`, referenced in
  `web/src/ui/lenses.ts`) `"dbt.lens"` → `"tycoon-city.lens"` (11 sites);
  `tour.spec.ts` and `lens.spec.ts` read/write those keys directly and were
  updated in the same pass. Referential `dbt` — the `objects[].dbt` contract
  field, `inspector.ts`'s `dbt.description`/`dbt.tags`, UI copy like
  `"declared (dbt)"`, and the `model.fx_dbt.*` fixture ids — is the actual
  trademark's own domain vocabulary and was left alone; only the browser
  global and the two storage keys named this project both times. Gate
  unmoved: pytest 553 passed / 1 skipped, Playwright 127 passed, `ruff
  check`/`ruff format --check` and `tsc --noEmit` clean, contract golden
  unchanged.

- 2026-08-09 — **Task 10b: the module is `tycoon_city`, not `database_tycoon`.**
  Reverses part of Task 10, same day. The reason: `database-tycoon` on PyPI
  is the Tycoon CLI's own distribution, and it normalizes to exactly
  `database_tycoon` — its venv holds a `database_tycoon-0.1.11.dist-info`.
  Task 10's choice meant `pip show database-tycoon` would return the CLI
  while `import database_tycoon` returned the city: two different products
  under near-identical names. `tycoon_city` also matches everything else
  already named — repo `tycoon-city`, console scripts
  `tycoon-city`/`-serve`/`-export`, and the CLI subcommand `tycoon city`.
  `src/database_tycoon/` moved with `git mv` again (history follows through
  both moves) and the `\bdatabase_tycoon\b` regex was safe this time — that
  word meant only the module, never a command — except for two false
  positives where it named the *Tycoon CLI's own* package
  (`~/Projects/localhost-stack`, a different product): `docs/log.md` and
  `superpowers/specs/2026-08-03-city-foundation-design.md` each had one site
  reverted back to `database_tycoon` by hand. The distribution stays
  `database-tycoon-city` (hyphenated, untouched — no word boundary matches
  it) and the environment variables stay `DATABASE_TYCOON_*` deliberately:
  env vars carry no distribution/module ambiguity, and keeping them out of
  the CLI's own `TYCOON_*` namespace keeps the two products disjoint. The
  same two documents Task 10 held out — `superpowers/plans/2026-08-09-tycoon-city-addon.md`
  (Task 10 section, the rename recipe as it actually ran) and
  `superpowers/specs/2026-08-09-tycoon-city-addon-design.md`
  (old-name/new-name table) — were held out again, for the same reason: they
  quote names as they were at the time, and `git mv src/dbtycoon
  src/database_tycoon` never became `git mv src/dbtycoon src/tycoon_city` no
  matter how the module was later renamed a second time. Gate unmoved:
  pytest 553 passed / 1 skipped, Playwright 127 passed, `ruff
  check`/`ruff format --check` and `tsc --noEmit` clean, contract golden
  unchanged.

- 2026-08-09 — **Task 10: the module is `database_tycoon`.** `src/dbtycoon/`
  moved with `git mv` (history follows) and every import, entry point,
  package path and doc reference followed it. The judgement in this rename is
  that one word carried two meanings: `dbtycoon` was both the *module* and the
  *command*. Module sites became `database_tycoon`; the 49 sites that were a
  command a human types — Docker image tags, `uv run …`, argparse `prog=` and
  epilog strings, the `serve it:` line `scripts/make_demo_tycoon.py` prints —
  became `tycoon-city`, the console script Task 9 created. A blanket
  `s/\bdbtycoon\b/database_tycoon/` gets every one of those wrong, so the
  blanket pass was run and then hand-corrected. Two documents were held out of
  it deliberately, because they quote names as they were at the time:
  `superpowers/plans/2026-08-09-tycoon-city-addon.md` (its Task 9 section
  records `dbtycoon-serve`/`dbtycoon-export` as run, and its Task 10 section
  is the rename recipe itself) and
  `superpowers/specs/2026-08-09-tycoon-city-addon-design.md` (old-name/new-name
  table). The 2026-08-04 entry below was likewise restored to the script names
  that actually shipped that day. Gate unmoved: pytest 553 passed / 1 skipped,
  Playwright 127 passed, `ruff check`/`ruff format --check` and `tsc --noEmit`
  clean, contract golden unchanged.

- 2026-08-09 — **Pre-rename baseline recorded: pytest 553 passed / 1 skipped,
  Playwright 127 passed, `ruff check` and `ruff format --check` clean, `tsc
  --noEmit` clean, contract golden reproduces byte-for-byte.** This is the
  gate Tasks 9–11 exist to leave undisturbed: ~342 occurrences across ~76
  files get mechanically renamed (the `dbtycoon` module → `database_tycoon`,
  six environment variables, three console scripts, and 240 uses of the
  `window.__dbt` browser global), and the only proof that a rename this size
  changed no behaviour is that every one of these counts comes back
  identical afterward. Also recorded here because it had no earlier entry:
  `web/src/ui/tour.ts` now persists the tour's stop **id** rather than a
  numeric index, so inserting a stop no longer silently moves a mid-tour
  reader to a different subject. The stored `localStorage` format therefore
  changed for every existing reader; an unknown or renamed id restarts the
  tour cleanly rather than guessing a position from a shifted number.

- 2026-08-09 — **Local AI capacity scoped for a post-1.0 release.** Stephen:
  *"I want to make this a frontend for local llms also... connect it with the
  power grid concept... a UI that helps people understand how much AI capacity
  they have just from the local hardware."* Captured as a design sketch rather
  than built, in `local-ai-capacity.md`. Three decisions it forces are recorded
  there: capacity is machine-specific and timestamp-bearing, so it belongs in a
  sibling `capacity.json` and never in byte-stable `city.json` (the run-replay
  precedent); Python measures and the browser only renders, because a page
  cannot read `localhost:1234` without CORS and should not carry runtime
  detection; and tokens/sec must be *measured*, never inferred from parameter
  count, with no reachable runtime rendering as unknown rather than zero. Corrected same
  day: the CLI **did** have a working LM Studio client, removed in `75b71eb`
  (2026-04-09, *"deferred to v0.2"*) along with nine sibling modules. Its
  `ModelInfo` already carries `quantization`, `max_context_length` and a
  `state` defaulting to `"unknown"`; what it lacks is measured throughput and
  memory headroom — the two facts most easily faked. The CLI's AI module and
  this project's Tycoon-CLI integration are both due in CLI **v0.2.0**, so they
  can be designed against each other.

- 2026-08-09 — **Implementation plan written: 15 tasks.** Gates first (1–8), so a
  green suite is the oracle that proves the rename; then the rename (9–11),
  packaging (12–13), the CLI seam (14) and the release candidate (15). Two
  findings while planning enlarged the rename beyond the design's audit: the
  browser verification seam `window.__dbt` is 240 uses of our own abbreviation
  of *Database Tycoon* — precisely the collision worth avoiding — and both tour
  failures turned out to be stale spec expectations hiding a real defect, that
  tour progress persists a numeric **index**, so inserting a stop silently moved
  every mid-tour reader. Task 6 is deliberately a diagnosis rather than a fix:
  the lost-selection-across-`R` regression reproduces but is not root-caused.
  Plan: `superpowers/plans/2026-08-09-tycoon-city-addon.md`.

- 2026-08-09 — **Public add-on release design approved.** The city ships as
  `database-tycoon-city`, installable as `pip install "database-tycoon[city]"`
  and driven by a new `tycoon city` command. Four decisions taken: the module
  becomes `database_tycoon` and the scripts `tycoon-city*` (no name of ours may
  embed `dbt`, a trademark of dbt Labs — referential use stays wherever it is
  factual, including the `objects[].dbt` contract field, which is unchanged);
  the web bundle is committed to `src/database_tycoon/web_dist/` with a
  rebuild-and-diff staleness guard, closing the "honest limit" the README names
  at line 50; the CLI gains an optional extra rather than a plugin API, so the
  city is never imported at CLI startup and never imports the CLI; and the day
  ends at a release candidate with nothing pushed or published. Spec:
  `superpowers/specs/2026-08-09-tycoon-city-addon-design.md`.

- 2026-08-08 — **Tour rewritten: 3D view, four lenses, controls, orphans.**
  `web/src/ui/tour.ts` gained four new stops (view, lenses, orphans, controls)
  and had its plant and streets stops tightened. Every lens's `tourStops` was
  updated to include the new stops in order. The tour now opens by establishing
  that this is a 3D city (drag to orbit, scroll to zoom, click to inspect),
  explains the four role lenses, names dimmed buildings as orphans (no edge
  touches them, no power line reaches them), mentions POWER_LINE arterials
  radiating from the plant, clarifies that roads follow lineage, and closes
  with a controls summary. The handover's "launch polish" item "tour copy
  should be re-authored against final v5 geometry" is now addressed.

- 2026-08-07 — **Streets v5 wired in behind `DATABASE_TYCOON_PLANNER=v5`: schema
  neighbourhoods on an S8-clean lattice.** Stephen, testing the app: *"Im not
  seeing the clustering of schemas that I asked for"* — correctly, because the
  clustering existed only as a spike PNG. The lesson is a reporting one: a
  finding the user cannot drive is not a delivered feature, and "not wired into
  anything" belongs in the FIRST line of such a report, not the fourth.
  `sim/town_v5_plan.py` now builds a real `DagPlan` from the existing
  precinct → lattice → slots → frontage chain, with precincts keyed by SCHEMA
  instead of `(depth, schema)`; depth only orders neighbourhoods west to east.
  Routes are deterministic BFS door-to-door over the lattice (fixed N/E/S/W
  neighbour order, FIFO queue — an unordered tie-break would break byte
  stability on the first rehash); every lattice tile no route used is carried in
  `lane_tiles`, which the generator already paints as ROAD, so the whole grid
  renders without a contract change. The flag is read per CALL, not at import.
  **On dogfood: grid 83x42 → 54x34, road tiles 833 → 258, S8 violations
  984 → 0, largest intersection clump 207 → 1, buildings with no street 8 → 0,
  all 33 routes resolved.** Stephen's verdict on the render: *"this is a lot
  better now"* — so the PNG is accepted and v5 geometry may now earn tests.
  **v4 remains the default and is untouched** (510 pytest, golden and contract
  frozen against it). Known gaps, all deliberate: lot footprints are 1x1 (2x2
  for big ones) anchored at the tile touching their own door, because `DagPlan`
  carries one anchor plus a size flag and cannot express a 3x2 lot — so blocks
  look emptier than they are; no merged trunk widths; no orphan suburb (orphans
  get ordinary neighbourhood land). **Still unresolved: the original
  complaint.** v5's `linear` metric is 0.86 against v4's 0.56 — the blobs read
  as neighbourhoods but rows INSIDE a precinct still align, and that traces to
  `Precinct`'s documented one-shape-per-precinct promise.

- 2026-08-07 — **Clustering spike: v5 already answers the roads, and makes the
  linearity worse.** Stephen: *"The buildings cant be lined up linearly like
  that... Find ways to randomly cluster them so most of the buildings have a
  fairly similar median radius from each other"* — he chose schema-led
  neighbourhoods (depth orders the clusters, not the buildings) and a mild ~2x
  gap from ASCII mockups. `scripts/spike_cluster.py` is the look-first
  instrument; **nothing is wired in**.
  **THE HEADLINE, which nobody expected:** the streets v5 lattice *already*
  satisfies S8 perfectly — 0 violations, every intersection isolated, on both
  catalogs at both cell sizes — and uses a fifth of the pavement. On dogfood,
  road:lot falls **17.35 -> 1.15** and the S8 clump goes **207 -> 1**. So "the
  roads are insane" is very largely *v4 is still the wired-in planner*.
  **BUT v5 is MORE linear, not less:** `linear` (share of lots in a run of 4+
  sharing an edge line) rises **0.56 -> 0.86**. A regular block grid is more
  lined-up than v4's stripes.
  **BOTH NAIVE DE-GRIDDINGS FAIL.** In-block jitter: 16 lots overlapping, 17 in
  the carriageway. Blue noise: 11 and **33 of 42**. They do cut `linear` (0.44,
  0.20) by destroying the city. Staggering whole neighbourhoods does nothing
  (0.87) — the collinearity is INSIDE a precinct.
  **WHERE THAT LEAVES IT.** The tension is now located on a documented
  invariant: `Precinct` promises one block shape per precinct, "which is what
  keeps the district reading uniform" — and that promise IS the rows. The fix is
  to vary block shape *within* a precinct while frontage holds by construction,
  which means changing `town_blocks.py`, which must be **split first** (489 lines
  against the 500-line law).
  **TWO TRAPS THE SPIKE ITSELF SPRUNG**, both instances of handover trap 4. Its
  first version reported jitter and blue noise as *clean*: it measured
  `no_frontage` but not lot-on-lot overlap or lots standing on pavement, and the
  only trace was a `lot` tile count quietly falling 214 -> 199. And `nn_iqr` — the
  literal reading of Stephen's criterion — scores a perfect lattice **0.0**, so
  optimising it alone crowns the very grid he rejected; `linear` exists to say
  the other half. A sheet whose fill merged ten neighbouring lots into one grey
  bar was also unreadable until lots were outlined.

- 2026-08-07 — **Road paint on every tile variant, and property S8: no two
  consecutive intersection tiles.** Both came out of running the app against
  `~/clients/dogfood` (42 objects, 33 edges) rather than the demo.
  **THE PAINT.** `terrain.ts`'s `drawRoadCell` painted a dashed centre line on
  the two pure straights *only*; every junction and every widened tile was bare
  asphalt. On the demo that is invisible, because most tiles there are
  straights. On a real catalog almost every road tile is fused, so the network
  rendered as one featureless grey slab. Now all sixteen connectivity variants
  are painted, and each mark states something true about the tile: the centre
  line turns through a corner; a T gets a stop bar on the **stem only**, because
  the minor approach is what yields, and the through road keeps its centre line;
  a crossroads gets four bars and a deliberately bare box, as a real junction
  box is; a stub gets a short approach line. `tsc` clean, 118/118 Playwright —
  the two initial failures were a stale `web/public` (I skipped
  `npm run demo-data`), not the change.
  **WHAT THE PAINT DIAGNOSED.** The west half of the dogfood city came out as a
  solid field of four-way stops, which is only possible if every tile there has
  all four neighbours paved. So it is not a set of wide roads — it is a paved
  AREA with junction markings on every square. Stephen's response was the new
  rule, verbatim: *"You cant have two consecutive intersection tiles."*
  **PROPERTY S8**, now in `docs/road-grammar.md`: an intersection is a road tile
  with ≥3 road neighbours; consecutive means orthogonally adjacent; two adjacent
  intersections are a failing build. S8 is the constructive form of the
  no-asphalt-plaza rule S7 could never express — S7 polices road *ends*, nothing
  policed road *area*, and a contiguous paved area is nothing but mutually
  adjacent intersections. Baseline (v4, measured, so S8 is an acceptance
  criterion for the v5 router and NOT a regression guard on v4): demo 47 of 70
  road tiles are intersections, 76 violating pairs, and the whole network is
  **one 47-tile clump**; dogfood 601 of 833 (**72%**), 984 violating pairs,
  largest clump **207 tiles**. A 207-tile contiguous intersection is the plaza,
  stated as a number.
  **THE DETECTOR** is `sim/road_junctions.py` — pure, reads a set of road tiles
  and nothing else, so the spike gauntlet and a property test can share it, and
  it works on a candidate router's output before that router is wired to
  anything. **Not wired into anything yet**, same status as `town_endings.py`.
  Seven tests; four mutants killed, each by a fixture that exists for it: the
  `>= 3` threshold mutated to `>= 4` is caught **only** by two adjacent
  *three*-way junctions (a fixture built from crossroads passes either way),
  diagonal adjacency is caught by the pair that must stay legal, an east-only
  violation scan by the vertical pair, and clump ordering by the two-clump
  determinism case. A no-op control mutant survived.
  **ALSO MEASURED, on the shipping v4 planner** (first measurement of this
  mechanism; the pavement-fraction figures in the handover were taken on the v5
  lattice and describe something else): channel width is O(distinct
  destinations) at `town_streets.py:161-165`, so dogfood's depth-0 channel is
  **31 tiles wide** (20 edges leaving toward 13 distinct destinations), and every
  edge crossing a column pays that width horizontally — 1042 of 1160 route steps
  are horizontal, and holding the edges fixed while shrinking channels to the
  5-tile minimum takes horizontal pavement from 1076 tiles to 228, so **79% of
  it is channel-width tax**. road:lot is **17.35:1** on dogfood against 5.38:1
  on the demo. The demo cannot reproduce any of this, which is why four spike
  rounds did not catch it.
  **HOUSEKEEPING:** `uv run ruff format .` rewrote seven files that are
  pre-existing uncommitted work (`sim/contracts.py`, `sim/logistics.py`,
  `webserve.py`, `town_streets.py`, `scripts/make_demo_tycoon.py` and two tests)
  — formatting only. The 19 `ruff check` errors all live in that same WIP; the
  two new files are clean. 510 pytest passed (1 skipped) before and after.

- 2026-08-07 — **Task 5: Streets v4 Renderer (Partial).** Added `street_features` to contract validation in `web/src/contract.ts`.

- 2026-08-07 — **Task 4: Streets v4 Planner.** Refactored `town_plan.py` into modular structure. Implemented `StreetFeature` system for road endings (apron, dock, plaza). Enforced S7 property ("no naked stub") with validation, and fixed road-ending dressing logic. Verified with 29 passing tests in `tests/sim/test_layout_plan.py`.

- 2026-08-07 — **Task 3: Stats UI (City Dashboard requests backlog).** Implemented backend support for `requests.json` and frontend RequestsPanel behind `?crlf=1`. Added `RequestSchema`, registered panel, and wired 'B' key for toggling. Verified UI integration.

- 2026-08-07 — **Task 2: Weather module (logistics hub).** Implemented `Shipment` and `LogisticsHub` in `src/tycoon_city/sim/logistics.py`. The hub validates shipments against contract schemas, tracking landed shipments and counting contraband. Verified with new tests in `tests/sim/test_logistics.py`.

- 2026-08-07 — **Task 1: CRLF contract extension.** Implemented request and shipment schemas in `contract/fixtures/` and added validation helpers to `src/tycoon_city/sim/contracts.py`. Verified with 4 new tests in `tests/sim/test_contracts.py` covering valid/invalid cases, including multi-field validation failures. Wrong-axis discipline confirmed by mutation testing.

- 2026-08-06 — **Phase 2: role lenses + the guided tour, achievements, the demo cascade, streets v5
  spike 2 (zoning).** Three parallel worktrees, merged with no conflicts. **465 pytest / 102
  Playwright green, ruff and tsc clean.**
  **ROLE LENSES** — the headline of the "fun UI for data teams" thesis. Four presets (data
  engineer, analytics engineer, on-call, data lead) that re-weight **presentation only**: chip
  order and the two leading chips, the triage comparator, which gauges lead, which overlays start
  on, which panel opens. Every list is an ordering or a default, never a filter, and every hook
  runs AFTER the numbers are computed. The guard that carries the feature: one document rendered
  under two lenses, chip count texts compared byte for byte plus the flagged-key set and every
  gauge value — the mutant that makes a lens filter a chip out of the aggregation dies on it. That
  is what stops "lens" becoming "invented score". Resolution is `?lens=` (wins, never persists,
  because a shared link must not rewrite the recipient's preference) → localStorage → first-run
  picker; skip persists `"none"` so it never nags. `?tour=1` walks the metaphors: every stop
  addresses its subject SEMANTICALLY (object key, schema, civic key — never a tile, so streets v5
  cannot kill it) and carries a mandatory `requires()`, so a tour never narrates an absent fact.
  9 mutants killed, 1 control survived.
  **ACHIEVEMENTS** — six milestones (`documented_buildings`, `tested_buildings`,
  `sources_under_sla`, `old_town_signed`, `marts_paved`, `fires_out`), each a COUNT OF REAL
  ARTIFACTS and each STATELESS: true right now, nothing minted, nothing persisted, bytes stay
  stable. "Mart" is the lineage DAG's terminal object, not a schema named `mart`; "paved" is
  `joins[]` (declared), not `edges[]` (measured). The law it exists for: a catalog with no manifest
  does not have 0% documentation coverage, it has UNKNOWN coverage — `state: "unknown"` with
  met/have/need all null, never `met: false, have: 0`. demo.duckdb returns all six unknown, so the
  golden itself demonstrates that absence is not failure. 17 mutants killed — and **one escaped
  first**, honestly recorded: the fixture had no non-dbt object, which made "the whole city" and
  "the dbt-managed set" the same set, so a mutant swapping one for the other had no axis to move on.
  **DEMO CASCADE** — demo-tycoon had no run containing a single skip, so run replay's headline
  feature demoed as "one building catches fire". A new fail-fast build errors `stg_customers` and
  skips three reachable models, while `stg_orders` skips WITHOUT being downstream (and sorts after
  the failure, so only reachability excludes it) and `dim__customers` is downstream but dbt built
  it anyway. All three of the cascade's tests now do real work on the demo project instead of
  passing on an empty set.
  **STREETS V5, SPIKE 2 (lots on frontage)** — reuses v4's own placement inputs rather than
  inventing new ones: sibling blocks become one literal city block, affinity clusters order the
  blocks, barycenter rank orders the slots, and a big lot consumes a whole block ringed by streets.
  The property holds **by construction** on all 38 fixtures: lots with no frontage 0, unzoned
  interior cells 0, roads threaded through a lot 0. Two rules changed after LOOKING, not after
  reasoning — block faces interleave (filling one face first gave every street buildings on one
  side only) and fill alternates end per block row. `cell_size = 2` is now the default
  (`resolve_coordinates`). Still spikes only: `plan_dag_layout` is untouched and `town_zoning.py`
  is reachable from the spike scripts alone.

- 2026-08-06 — **Phase 1b: run replay and OSI reach the HUD; streets v5 lattice, round 2.** Two
  workstreams in parallel worktrees, merged with no conflicts. Combined tree **448 pytest / 74
  Playwright**, ruff and tsc clean.
  **WEB WIRING** — both Python halves landed in Phase 1 finally have a consumer. `contract_runs.ts`
  reads `runs.json` / `runs/<id>.json` and is kept separate from `contract.ts` exactly as the
  documents are separate from `city.json`. `sim/run_replay.ts` is a state machine whose
  `stateOf(key)` is a PURE TOTAL FUNCTION OF THE CURSOR rather than accumulated animation state —
  backward stepping is exact, `jumpTo` needs no re-walk, and the whole cascade is assertable
  without a screenshot, which is the point in a repo whose dominant defect is geometry tests that
  cannot fail. There is no timer anywhere, in any mode, so "advance on a timer" had to be INJECTED
  to be mutation-tested rather than switched on. `ui/run_panel.ts` replaces the single replay
  button with a worst-first run picker plus a step inspector, and NAMES absent or locked run
  metadata instead of hiding it — silently missing UI is the exact failure the absence law exists
  to prevent. `city.json`'s aggregate `replay` block survives as a labelled second-best row so no
  contract block is orphaned. Fires / DispatchFleet / Traffic gained overrides: a named
  invocation's failures burn at the cursor that failed them, the station answers them, and only
  the current step's in-edges move data. **The cascade is NOT re-derived client-side** —
  `failure_cascade[]` is a measured join of three facts and the producer owns it; a second
  implementation in the client would be a second source of truth. What the machine adds is timing,
  plus two guards on what a document may make the city say: only a step dbt itself reported
  skipped may dim, and a cascade may not run backwards up the run order. The inspector shows
  declared OSI datasets and joins with their own provenance, solid/dashed as the model graph
  already does, so a declared join can never read as observed data movement. No join streets in 3D
  — that is streets v5. 74 specs (was 54), 12 mutants killed, 2 no-op controls survived.
  **STREETS V5, ROUND 2** — still spikes only; `plan_dag_layout` untouched. Every change judged by
  re-rendering the 38-city sheet and looking, never by spec. Downtown loses its internal lattice:
  round 1 made every block a plus-sign of road around four one-tile lots — the exact circuit board
  Stephen had named as the defect — so density now comes from 2×2 blocks against industrial 4×2
  and suburban 2×4, and texture becomes grain. `MAX_INTERIOR_CELLS` becomes `MAX_INTERIOR_SHORT`:
  holding only the SHORT axis to 2 is what makes a long block legal while every cell keeps a
  bounding line on one of its own edges. Suburban's stamped "H" becomes one cul-de-sac stub
  alternating on `bx+by+band`, which actually varies on the single-block precincts that are most of
  this bench. Depth columns wrap at a shared `isqrt(land)` height: flat-7x9 15×63 → 22×25, cap-500
  45×103 → 48×52, aspect median 1.40 → 1.20, worst 4.20 → 1.85. `resolve_coordinates` now gives an
  UNUSED line index width 0 — round 1 charged a tile per line index whether a street ran on it or
  not, so dropping a line left a one-tile moat inside the block; bench total 21389 → 13775 tiles.
  **Pavement is the defect this round did NOT fix:** 60% at cell 1 against round 1's 61%, because a
  one-tile lot bought with a one-tile street is a 1:1 trade whatever the block shape. `cell_size=2`
  gets 40% and reads as a city of buildings — that is a lot-size decision for the lots spike, so
  both sheets were rendered rather than one being argued for. New fixture `dotted-tie` (schemas
  whose member keys do not sort like their names, in both directions) KILLS round 1's surviving
  `members[0]` determinism mutant: round 1's bench could not see that class of regression at all,
  and no amount of re-running it would have.

- 2026-08-06 — **Phase 1: run replay, the three measured mappings, OSI semantics, streets v5 spikes
  0–1.** Four workstreams built in parallel worktrees off the Phase 0 tree and merged here, each
  verified on its own branch first. Combined tree **448 pytest / 54 Playwright**, ruff and tsc
  clean, and the contract golden still reproduces byte-for-byte from a fresh export.
  **W-REPLAY — replay one specific run, step by step.** Probed the metadata first: `dbt_nodes`
  carries durations and NO per-node timestamps, so step order is *reconstructed*, and it REUSES
  `build_replay`'s Kahn walk (extracted as `induced_subgraph` / `topological_order`) rather than a
  second one that drifts; documents say `order_source` so an engine that one day records start
  times upgrades to "observed" without a version bump. `RunHistory.run_nodes` keeps the newest
  `MAX_REPLAY_RUNS = 20` invocations at EVERY status — `node_results` folds to the newest and
  `build_history` keeps only successes, so between them every failure and skip, the whole point of
  the feature, was being discarded. New `export/run_json.py` produces `/runs.json` and
  `/runs/<id>.json`, served and statically exported at the same paths, with the id validated
  against the known invocation set before it is used for anything. `failure_cascade` joins three
  MEASURED facts — dbt said skipped, reachable over the city's `edges[]`, later in the order — and
  never an inferred blast radius. These records carry ids and timestamps, so they are their own
  documents (`docs/run-json-v1.md`); a sentinel test asserts neither reaches `city.json`'s bytes.
  24 mutants killed, and the sweep found two honest holes: an **unfalsifiable edge filter, deleted**
  rather than left as decoration, and an untested empty-cascade case.
  **W-MEASURE — budget, usage, weather, all measured.** BUDGET is `daily_load_s` at a declared
  rate; local DuckDB's $0 is a FACT with its note, while $0-because-unknown is null instead, and
  the objects it could not price are counted so a partial bill announces its own partiality. USAGE
  is build/run appearances, **not queries** — vanilla DuckDB has no query log, so the `source`
  discriminator (`"runs"`) holds that seam open for the MotherDuck/Snowflake versions; one cadence
  calculator and one one-hour floor now serve both usage and the road heat, so "how often" means
  the same thing in both places. WEATHER walks downstream from every judged source, so fog covers
  the districts a late source FEEDS rather than the source's own — and emits NO cells when nothing
  has been judged, because all-clear there is clear-because-unknown wearing clear-because-fine.
  That rule got its own mutant. 13 killed. `W` fogs the districts, capped below the shortest roof
  so it can never hide a fire — verified by looking at a render, not by counting meshes.
  **W-OSI-A — the semantic layer loads.** `catalog/osi.py` reads datasets, many-to-one
  relationships (simple and composite), metrics and `ai_context`, tolerant like the manifest
  reader: a missing file is a note, a malformed section costs itself and nothing else, and
  unmatched declarations are COUNTED ("1 of 2 declared joins did not match a catalog object")
  rather than dropped. Joined case-insensitively with catalog spelling canonical. `city.json` gains
  a top-level `joins[]` kept SEPARATE from `edges[]` on purpose: an edge asserts data moved at
  build time, a join asserts two objects are formally joinable whether or not anything ever ran —
  and the dim joined constantly but never built from the fact, the case that makes the whole
  feature worth having, has nowhere else to live. Pairs that have both are reconciled through
  `joins[].lineage_edge` so the renderer marks the existing street instead of laying a parallel
  road. demo-tycoon ships the first real OSI file. 25 mutants killed and **one ESCAPE caught
  honestly: a case-SENSITIVE match survived the whole suite** because every factory object is
  already lowercase — the canonical-spelling law had nothing to prove itself against until a
  mixed-case catalog was added.
  **W-STREETS — spikes 0 and 1 only, nothing wired in.** `plan_dag_layout` is untouched;
  `town_blocks.py` is reachable only from the spike scripts. `spike_contact_sheet.py` renders all
  37 fixture cities on one sheet (the BEFORE picture) and fingerprints every plan under three
  SHUFFLED input orders — a determinism property that did not exist before today, and the one that
  will catch v5 nondeterminism. `town_blocks.py` decides precincts, block shapes and lines entirely
  in LATTICE SPACE with one prefix-sum conversion to tiles last, which is what will make hierarchy
  widths cheap. The render caught a defect no spec-first test would have named: narrow precincts
  grew arterials dangling into open grass.
  **Merge resolution, worth remembering because all four had the same shape:** W-MEASURE and
  W-OSI-A each filled their own reserved keys and described the other's as still reserved. Resolved
  so all five are filled, and the reserved-seam test was re-cut as
  `test_the_seam_keys_are_emitted_unconditionally_on_every_catalog` — the invariant that outlives
  the reserved era — with the empty shapes pinned by the two provenance-specific tests (measured
  absence, declared absence) the two workstreams had written independently.

- 2026-08-06 — **Phase 0, part 3: five real-catalog correctness fixes in the loader and server.**
  Found in review. The 1.0 metric is "works weekly on real, messy client catalogs", and every one
  of these only bites at real-catalog scale — which is why none of them had ever failed a test.
  **(1) The `MAX_OBJECTS` cap, two bugs in one place** (`catalog/loader.py`). Truncation was logged
  and nowhere else, so it never reached the UI; it is now a note on the context — "catalog has N
  objects; showing the 500 most relevant" — and therefore reaches `database.notes` in `city.json`.
  And views carry `row_count=0`, so "keep the 500 largest by row count" ranked every view below
  every non-empty table: **views are the only carriers of SQL and SQL is where streets come from,
  so a 600-object catalog rendered a city with no lineage at all.** `_cap_objects` now keeps views
  first and spends the rest of the budget on the largest tables. "Participates in an edge" would be
  the better criterion but is not computable there — the cap runs before `_derive_edges`, which
  takes the retained set as input; the docstring says so rather than leaving the next reader to
  rediscover it. Measured on a 520-object synthetic (40 views): 20 views and 1045 road tiles
  before, 40 views and 4075 after.
  **(2) Bare-name lineage now parses instead of scanning** (new `catalog/sql_lineage.py`).
  `\bstatus\b` over lowercased view SQL matched inside string literals, comments and column
  positions, so on a real catalog a table called `status` or `date` wired itself to nearly every
  view. sqlglot (duckdb dialect, already a dependency) reports only names in table position. Parse
  failure falls back to the old regex over text with literals and comments stripped — degraded,
  never absent, and never credulous. Qualified matching is unchanged. Extracted to its own module,
  the coarse-grain sibling of `column_lineage.py`, because `loader.py` had crossed 500 lines.
  **(3) `run_history` `prefer_target` notes said things that did not happen.**
  `prefer_target='staging'` against dev/prod runs matched nothing, left the runs UNFILTERED, and
  appended "run history from target 'dev'" — a filter that never ran, named after the wrong target.
  Each branch now states what actually happened, including which targets a real filter hid.
  **(4) webserve: bind and cache.** Default bind is `127.0.0.1`; `--host` / `$DATABASE_TYCOON_HOST` opts
  into wider exposure, because a city names a client's schemas, tables and columns. The image sets
  `DATABASE_TYCOON_HOST=0.0.0.0` since a published port cannot reach loopback. `_SourceCache` keys on
  `(path, mtime_ns, size)` for every file behind the loaded source — warehouse, `tycoon.yml`,
  manifest, `sources.json`, metadata db — so `R` re-serves a parsed catalog instead of rebuilding
  it; sources with no files (`md:`) fingerprint as None and are never cached; the fingerprint is
  re-taken after the build and a raced build is used but not stored. Signals are re-derived on
  every hand-out, cache hit or not: last-build age counts from the wall clock, and a frozen clock
  would be a stale render.
  **(5) `_derive_edges_from_sql` compiled both patterns per (view, object) pair** — a quarter of a
  million `re.compile` calls at the cap. Compiled once per object. With (2), a 500-object catalog
  loads in **2.25 s, down from 10.40 s, with an identical edge set** (that pair of numbers is the
  parse+compile work; the mtime cache above is a separate win and was not timed).
  18 new tests, 322 passing on this branch. demo.duckdb's exported `city.json` is byte-identical
  before and after and the contract golden is untouched — the new note lands under the existing
  free-text `notes` field, so no version bump. Twelve mutants, one per guard, each killed by the
  test that names it; one no-op control (rewording the cap's log line) survived as required.

- 2026-08-06 — **Phase 0, parts 1–2: the two 500-line files split, the OverlayRegistry, and all
  five contract seams cut in at once.** Four 1.0 workstreams were about to add blocks to
  `city.json` and lines to `main.ts`; landing their keys separately would have meant four contract
  changes racing the golden and the client schema.
  **`main.ts` 499 → 372**, behaviour-neutral, along the two seams that grow on their own:
  `boot/mount.ts` (137) holds the mount/unmount cycle — `mountCity()` returns the per-document
  handles as ONE bundle (`MountedCity`) instead of nine long-lived `let`s, and a stale handle after
  an `R` refresh is the failure mode that bundle shape rules out; `boot/hooks.ts` (149) holds the
  `window.__dbt` block as `installHooks(deps)`, with `doc` and `city` as getters because `R`
  replaces both, and **not one hook name, signature or key binding changed** — they are a contract
  with `web/e2e/`. `ui/overlays.ts` (49) is `Overlay` + `OverlayRegistry`: deliberately minimal —
  an id map and case-insensitive key routing, no rendering, no ordering, no exclusivity —
  with `FlowOverlay` as its first member (id `flow`, key `t`). `main.ts` is now composition root
  only, and Guests is still constructed there and nowhere below, so `tests/test_web_layering.py`
  keeps its meaning. Verified the way this repo demands rather than by a green suite: the rich
  fixture at `?settle=1&seed=7` renders BYTE-IDENTICAL before and after (1280×692, 0 differing
  pixels), every counting hook returns the same value (flow 35, curb 71, feat 12, `screenPos` and
  `districtScreenRect` to the digit), and the `T` route was checked by pixel diff rather than by
  existence — `T` hides the overlay (10,439 px change), `T` again restores it exactly (0 px), an
  unbound key changes nothing. 47/47 Playwright, twice.
  **`export/city_json.py` 444 → 164** — the document assembler only (the list of blocks a document
  is made of, in wire order, plus `dumps`); the per-section builders moved to `export/blocks.py`
  (367). Pure refactor, proved by exporting demo.duckdb before and after: byte-identical, golden
  untouched by this step alone. Every historical import path still resolves (`from ...city_json
  import encode_rle`, `_focus`, `RATE_PRECISION`, …) via re-exports listed in `__all__`, and
  `blocks` joins the no-pygame module list so that guard cannot go quiet on it.
  **The five seams**, emitted unconditionally and never conditionally, each with a one-line comment
  naming its workstream: top-level `"budget": null` (cost), `"weather": null` (freshness),
  `"joins": []` (OSI); per object `"usage": null` (run appearances), `"semantic": null` (OSI).
  Strictly additive, `version` stays 1. Golden regenerated: **+17 lines, 0 deletions, 0 moved** —
  7 objects × 2 keys plus the 3 top-level keys, and nothing else in the document shifted.
  `docs/city-json-v1.md` gained a "Reserved fields (1.0 workstreams)" section saying null / `[]` is
  the only legal value at version 1, so a later document renders as absence and never as a guessed
  shape. `web/src/contract.ts` takes all five as `.optional()` / `.nullable()` with empty defaults —
  the pattern `street_features` already uses — verified by parsing three documents against the
  schema: the new golden, the golden with all five keys deleted, and one with content in all five.
  **The latent district contract-test gap is closed** (it was carried on the open-work list from
  2026-08-05). `test_districts_..._contain_their_own_lots` asserted every lot sits inside its
  schema's plate; the documented rule is the OPPOSITE for a schema that mixes connected lots with
  suburb orphans — the plate bounds the CONNECTED lots and leaves the orphans out, or one stray
  table stretches the rect across the map. No fixture in the export suite mixed the two, so the
  assertion had never met the rule it contradicted. Added the `mixed_schema` catalog (`raw` owns a
  connected lot AND a stray; `scratch` is all-orphan) and rewrote the assertion into its three real
  branches: connected lots inside, a mixed schema's orphans asserted **OUTSIDE** (not merely
  exempt), an all-orphan schema keeps its plate. `test_the_mixed_schema_fixture_actually_mixes`
  pins the precondition on the emitted document so the fixture cannot silently degrade into an
  assertion that cannot fail. Also added
  `test_reserved_seams_are_emitted_unconditionally_and_stay_empty` over every adversarial catalog —
  the golden pins the demo catalog only and would not catch an emitter that dropped `budget` on a
  lineage-free one.
  10 mutants killed + 1 control survived (`PYTHONDONTWRITEBYTECODE=1`, `__pycache__` cleared,
  in-memory restores, no `git checkout`). Two are worth naming: **M8 swaps the plate's x and y, M9
  swaps its w and h** — the wrong-axis pair this repo keeps getting caught by; both die, so the
  district test is not asserting on an axis that cannot fail. Full suite 326 passed / 1 skipped.

- 2026-08-06 — **The 1.0 plan: "a fun UI for data teams"** (`~/.claude/plans/fancy-wiggling-clarke.md`,
  24-question planning interview with Stephen). The decisions that now steer everything above.
  **The success test Stephen chose is that he uses it weekly on his own client catalogs** — a
  public OSS launch and a conference/video demo are the announcement, not the goal, which is why
  Phase 0 spent itself on real-catalog robustness rather than on launch glitter. Locked:
  interactivity is **observation + achievements only** (counts of real artifacts, never points) and
  **CRLF is OUT of 1.0** (the blueprints stay archived for agents); **local DuckDB only**, keeping
  engine-neutral wording so the MotherDuck/Snowflake versions stay cheap; **four role lenses** (data
  engineer, analytics engineer, on-call responder, data lead) as HUD presets, no avatars and no
  civic-HQ mechanics; three new measured mappings (budget = cost, usage = query traffic honestly
  named as build/run appearances, weather = freshness); replay of specific individual runs with
  step-through and failure-cascade dramatization, no cinematic mode; OSI semantics IN, with join
  streets that pave dirt; streets v5 as a **blocks-first pivot** gated by a spike-render gauntlet
  where Stephen reviews the PNGs before any test is written; distribution pip + Docker under
  **MIT**; **tycoon-CLI integration deferred to that product's 0.2.0** (the artifact-contract-only
  rule stands). Held open on purpose: the AI responder (the firehouse seam stays draft-only and
  labelled "not connected") and cost skill-builds (pricing is a config layer). Open decisions
  recorded for Stephen: the public repo name, `WIDTH_MEASURE` (carriers vs downstream-closure,
  to be picked from a spike PNG), and whether `edges.rate` retires in favour of `daily_load_s`.
  **Pushing the branch was raised three times over the day and declined each time — "not yet".**
  It is a settled answer, not a pending one; the single-point-of-loss risk is Stephen's to carry
  and re-raising it is not this project's job.

- 2026-08-05 — **Streets v4, renderer half: the streets stand up (curbs) and their endings are
  dressed (apron / dock / plaza).** Stephen: the streets "look flat/pasted" — correctly, since the
  whole network was painted into the terrain atlas and any low camera angle gave it away.
  `web/src/scene/streetscape.ts` extrudes a raised concrete curb along every CLOSED edge of every
  road tile, instanced (one draw call), straddling the tile boundary so the asphalt reads as sunken.
  The closed-edge set comes from the newly extracted `scene/road_mask.ts`, shared with terrain.ts's
  16 painted variants so paint and geometry cannot drift; adjacent tiles fuse exactly as the paint
  does and no curb crosses a junction. Skipped entirely under `?flat=1` (its pixel tests count exact
  colours). Dressed endings arrive on the frozen contract seam `street_features:
  [{kind, x, y, facing, w, h}]` — **optional, default `[]`**, and `kind` is a plain string so an
  unknown kind is a forward-compatible no-op rather than a load failure. `apron` = a narrow ramp
  that NOTCHES the curb (two flanking stubs, a real curb cut) toward the building it serves, plus a
  door on that building's face; `dock` = a striped loading court with a raised platform at the face
  (the tell that separates a loading bay from a zebra crossing); `plaza` = the lighter paved
  forecourt of a terminated vista, re-paving its tiles outright. `rich.city.json` carries a
  HAND-ADDED three-feature block (apron 21,5 e; dock 7,5 w; plaza 20,8 2×2) on tiles its real
  routes use — the spec header names it and says regeneration will replace it. **46/46 Playwright**
  (7 new), tsc clean, `?flat=1` counts unchanged. Six mutations, one per new guard, each failed the
  guard naming it. Two things worth keeping: (a) the e2e counts read the LIVE instanced meshes, not
  bookkeeping integers, so a feature that validates but never reaches the scene reads as missing;
  (b) a first draft of the kerb-coverage test pinned the colour `#606065`, which survives deleting
  the curb mesh entirely — it is not the curb, and only the mutation check said so. The pin that
  works runs the other way: the atlas's painted kerb line (`#8a8a92`) must be **absent**, because
  the geometry covers it (thin the curb and it peeks out as a double kerb). Also landed:
  `DATABASE_TYCOON_WEB_PORT` for the dev server and Playwright (parallel worktrees must not share :5173),
  `e2e/streetshot.mjs` + a `setCameraPose` hook for street-level looks, and `disposeTree` moved to
  `scene/dispose.ts` to keep main.ts under the 500-line law.
  **A bug the curbs uncovered:** from eye height a few tiles out, the curbs were there and the
  ROADS WERE NOT — the whole network rendered as grass. The 4096-tile grass skirt sits 0.02 below
  the terrain grid, which is nothing against a 0.1..6000 depth range, so at grazing incidence the
  skirt won the depth fight and painted over every road tile; only the 3D geometry survived it and
  gave it away. The skirt now writes no depth and draws first (it is the lowest surface in the
  scene, so nothing legitimately hides behind it). Pinned by a grazing-camera asphalt count: 70k
  pixels with the fix, exactly 0 without. Flat mode untouched. **47/47 Playwright.**
- 2026-08-05 — **Streets v4, planner half: a road may only end at something (apron / dock / plaza),
  plus property S7 and the planner split.** Stephen, verbatim: *"there needs to be a clear
  definition for when and where a road is allowed to end, and what that looks like."*
  `docs/road-grammar.md` holds the researched taxonomy; this is the first half of building to it.
  **(1) The planner split.** `town_plan.py` had reached 658 lines. Split at the seam the blueprint
  named — `town_rows.py` (columns, barycenter, schema bands, affinity clusters, sibling blocks, 2×2
  footprints, the row cursor/float rules, the highway pass: everything decided before a road
  exists) and `town_streets.py` (channel units, straight units, trunk tracks, segment paths,
  routes, merged lane width, and now the endings) — with `town_plan.py` keeping the `DagPlan`
  contract, the utility strip, the civic buildings, the suburb, the plates and the orchestration.
  `tycoon_city.sim.layout` re-exports exactly what it did before. Behaviour-neutrality was PROVEN,
  not asserted: `plan_dag_layout` was fingerprinted over all 29 property-sweep families plus
  demo-tycoon and dogfood, and the sha256 was identical before and after.
  **(2) Street features.** `DagPlan.street_features` — a sorted tuple of frozen
  `StreetFeature(kind, x, y, facing, w, h)`, derived from route endpoints plus lot metadata,
  nothing invented. `dock` where a street leaves a depth-0 source (industrial truck court),
  `plaza` where it meets a 2×2 lot or a civic building (paved forecourt spanning the whole
  frontage, the terminated-vista move), `apron` for every ordinary building. Precedence is
  plaza > dock > apron so that **a pad wider than one tile is always a plaza** — the invariant the
  renderer keys its geometry off. The generator paints feature pads last, grass-only; a plaza's
  extra forecourt tile is the only pavement a feature adds.
  **(3) Property S7.** Wherever the road network ENDS — a ROAD tile with at most one orthogonal
  ROAD neighbour — a feature must dress it, and every pad tile must come out paved. ROAD-only
  neighbour counting is deliberately stricter than ROAD-or-LOT: the tile where a street stops dead
  against a building face has a lot beside it and would otherwise never be examined, and that
  abrupt ending is the whole complaint. Measured before writing the property: 445 endings across
  the sweep + demo-tycoon + dogfood, every one dressed, and every city with roads must show at
  least one ending so S7 can never pass by having nothing to look at. Spike-rendered before/after
  on demo-tycoon (12 features, 4 endings, 0 naked) and dogfood (43 features — 28 aprons, 13 docks,
  2 plazas — 12 endings, 0 naked); the spike now draws the endings, and naked ones in magenta.
  Dogfood's docks line up in one column against the power strip, which reads as a loading edge.
  **(4) Contract.** `city.json` gains `street_features: [{kind, x, y, facing, w, h}]` — additive,
  v1 unchanged, sorted by (kind, x, y), golden regenerated deliberately in the same commit (74
  inserted lines, tile grid unmoved). `docs/city-json-v1.md` documents the taxonomy and the
  plaza-pad invariant. This shape is FROZEN: the renderer half is being built against it.
  **18 mutation checks, all killed** (PYTHONDONTWRITEBYTECODE=1, `__pycache__` cleared, restored
  from in-memory copies). Three wrong-axis escapes caught by them and worth remembering:
  the first plaza-paving fixture had a merged LANE sitting on the forecourt tile, so it passed
  without the plaza doing anything; the pad's "yield if a building owns this tile" guard survived
  mutation, and measuring showed why (768 endings, not one vertical — a channel's trunk x is
  always ≥2 tiles short of the next building column, so every route's first and last leg is
  horizontal), so the guard and its dead branch were deleted rather than left as decoration; and
  swapping `w`/`h` in the emitter survived because no export catalog had a 2×2 building at all —
  the contract's most renderer-critical geometry field was pinned by nothing until a `big_plaza`
  catalog was added. **270 → 304 Python tests.**
  Two things left open, both deliberate: a big raw source now reads as a plaza rather than a dock
  (precedence chose the pad invariant over road-grammar's literal source-layer assignment — a
  one-line flip if Stephen prefers the industrial read), and no cul-de-sac bulbs, map-edge
  connections or hierarchy widths yet — those are later stages.

- 2026-08-05 — **Proper streets rendered + wear-and-tear with contractor vans (roads pass, part 2).**
  The renderer half of the roads pass: sixteen connectivity-variant road cells join the runtime
  atlas (CPU computes each road tile's N/E/S/W adjacency mask; shader picks `ROAD_BASE + mask`) —
  asphalt with curbs only on closed edges, so adjacent tiles fuse into one street, two-lane trunks
  read as one wide road, junctions read as junctions, dashed centre paint marks pure straights,
  and a street ending at a building keeps its curb cap. Flat mode untouched (pixel tests).
  A gotcha for posterity: when the whole terrain grid fails, the phase-aligned skirt makes the
  screenshot look like "roads vanished" — check for the skirt-only symptom before debugging roads.
  Then Stephen's newest directive same-day: *"Source freshness is also something we should monitor
  visually. Maybe allow the building to show signs of wear and tear, and they need to have
  contractors come and fix it."* Landed as `scene/wear.ts` (SLA warn = weathered-plywood boards on
  the south face, error = more boards + grime skirt; deterministic, facts-only) and `RepairVans` —
  FireTrucks generalised into a configurable `DispatchFleet`, amber vans sharing the station, the
  roads-only rule and the never-claims-a-fix honesty rule. Firehouse panel gains "repair calls";
  district labels moved just inside their plates (the old 0.4-outside float broke the overlap spec
  once the city tightened). **39/39 Playwright, 270 Python.**

- 2026-08-05 — **Streets v3 + urban-planner clustering + 2×2 footprints (the roads pass).**
  Stephen: the roads were "strange and unrealistic and ugly" — he picked zigzag/staircase
  routes and dead-end/redundant runs as the offenders, "proper streets" as the target style,
  approved 2×2 footprints, and mid-pass added: *"Think like a true urban planner. Try to
  cluster together the bigger buildings / tables visually especially if they share common
  sources."* Three planner generations, each spike-rendered (`scripts/spike_road_defects.py`,
  the new look-first instrument) before/after and mutation-checked:
  **(1) Streets v3** — first-member float (a column starts on its predecessors' row; measured
  against per-building slack stretching, which LOST by manufacturing 1-tile kinks — the losing
  variant is documented in the code comment), straight units (an aligned 1:1 comb reserves no
  channel width — dogfood's raw→staging ladder collapsed), the highway pass (one constant
  pass-through row per destination; pass-through slots no longer inflate cursor rows), and
  direction-aware lane merging (crossings/splits no longer drop orphan dead-end lane stubs).
  Dogfood route tiles 1058 → 694, straight routes 0 → 8, demo city 31 → 23 wide. 4 mutants
  KILLED. **(2) Affinity clusters** — within a schema band, buildings sharing ≥1 source join
  one cluster (union-find), biggest tables lead, members touch at pitch 1; exact-source blocks
  keep the one-trunk privilege; the sibling-block pin now REQUIRES a common-source neighbour
  to touch the block. Clustering finally visible on dogfood (zero exact-source siblings).
  **(3) 2×2 footprints** — the top decile of the catalog's row counts (≥4 objects with rows)
  claims a 2×2 NW-anchored ground plan; outbound streets leave the east face so no street
  crosses its own building; lots ship `w`/`h` in the contract; the whole web layer
  (buildings/fire/markers/silhouettes/facades/skybridges/outline/fly-to/firetruck goals)
  anchors on footprint centres. New sized property family in the sweep asserts its own
  fixtures actually contain 2×2 lots. Golden + web fixtures regenerated deliberately.
  Still open from the pass: the proper-street renderer (junction-aware asphalt, lane paint,
  curbs) and Stephen's newest directive — wear-and-tear on stale-source buildings with
  road-bound contractor dispatch.

- 2026-08-05 — **Session wrap: CRLF blueprint 1 merged, layout split, the rich fixture pins the
  positive paths, handover rewritten.** The worktree agent's contract extension merged clean
  (Customs validation in `sim/contracts.py`, request/shipment schemas in `contract/fixtures/`,
  11 tests incl. three killed mutations). `sim/layout.py` (650 lines) split: structure
  (depths/SCC/orphans, 214) stays; the DAG planner moved to `sim/town_plan.py` (487) with
  re-exports so `tycoon_city.sim.layout` remains the import path of record. NEW positive-path e2e
  suite `web/e2e/rich.spec.ts`: a committed demo-tycoon export (`e2e/fixtures/rich.city.json`,
  ages frozen at generation) served via Playwright route interception pins fires=1, one truck
  dispatched, vehicles on fresh streets, the road-load overlay lit with `T` toggling, health
  chips as doors gliding to the burning mart, and skybridges on selection — everything that was
  previously render-and-look-only. Suites: **263 Python + 38 Playwright green.** Handover
  rewritten for the day (streets v2 line, game thesis, engine versions, CRLF, all open work).
  Mid-wrap the session's tool-permission classifier went down for ~10 minutes (every write
  blocked); work was staged during the outage and landed after — noted in the handover's
  environment gotchas.

- 2026-08-05 — **CRLF contract extension: Customs opens for business (first blueprint executed).**
  `contract/fixtures/request_schema.json` + `shipment_schema.json` land exactly as Stephen's
  master spec §3 defines them, and `src/tycoon_city/sim/contracts.py` validates documents against
  them — `validate_request` / `validate_shipment` returning `(ok, errors)` where the error list
  names EVERY failing field (Customs reports, it does not shrug). The validator is a hand-rolled
  JSON-Schema subset (required keys, enums, types, integer bounds; jsonschema stays out of the
  dependency tree), loaded from the schema files so the fixtures remain the single source of
  truth. One trap pre-closed: `bool` is a subclass of `int` in Python, so `complexity: true`
  is rejected, not waved through. Requests/shipments carry uuids and timestamps, so they stay
  OUT of city.json v1 — `export/city_json.py` and the demo golden are untouched (diff clean).
  11 new tests in `tests/sim/test_contracts.py`, each rejection breaking exactly one axis on an
  otherwise-valid document; three mutations run under `PYTHONDONTWRITEBYTECODE=1` with cleared
  `__pycache__` (enum guard killed, error list truncated to first, upper-bound comparison
  flipped same-length) and all three caught before the original was byte-restored. Full suite
  269 passed / 1 skipped, plus one PRE-EXISTING failure inherited from HEAD `efbb020`:
  `test_mechanics_imports_only_facts_and_primitives` rejects guests.ts's new `../sim/roadnet`
  import because the roadnet commit never widened the layering allowlist — not touched here
  (web-side guard, out of this blueprint's scope), flagged for whoever owns the roads work.

- 2026-08-05 — **ALL vehicles are subject to the roads rule (Stephen, closing the loop).** One
  shared `web/src/sim/roadnet.ts` now defines drivability for every vehicle class: ROAD tiles,
  building LOTS (streets terminate on their buildings — lots are the junctions), and POWER_LINE
  (the utility corridor is how anything leaves the plant/civic strip). Grass is never drivable.
  Fire trucks moved onto RoadNet (local BFS deleted); GUESTS (?guests=1) now walk cached
  road-network paths from the plant instead of manhattan beelines — an unreachable building is
  simply never visited; TRAFFIC lost its legacy manhattan fallback (a document without routes
  gets no vehicles; off-road motion is theater). 33 Playwright specs green including the guest
  mechanics spec.

- 2026-08-05 — **CRLF scaffolding filled in (docs/agent_tasks/).** Stephen authored the
  Citizen-Request & Logistics Framework master spec (Demand/Citizens, Supply/Blueprints,
  Flow/Logistics) with three empty task stubs; the resident agent added OKF frontmatter, an
  addendum binding CRLF to the standing laws (CRLF = the Phase-G SIMULATED layer: own fields,
  tick+seed, never mutates derived facts, flag-gated and provenance-labeled until Stephen flips
  the default; request/shipment records carry uuids/timestamps so they stay OUT of byte-stable
  city.json v1 as their own schema'd documents), and drafted the three blueprints with
  requirements + acceptance criteria: contract extension (Customs validation, no deps, first),
  weather module (first external Source shipping through the Logistics loop into demo-tycoon via
  the real measured channels), and the City Dashboard requests-backlog panel (behind ?crlf=1,
  the ?guests=1 pattern). Directory index added and linked from docs/index.md.

- 2026-08-05 — **Vehicles must travel on roads (Stephen, verbatim).** Fire trucks were driving
  manhattan beelines over grass. Two fixes: the planner wires the firehouse into the network
  with a CIVIC ACCESS ROAD (deterministic BFS over grass to the nearest street, blocked by
  power/lots/plant; a city with no roads gets none — a road to nowhere would be theater), and
  the client BFS-routes trucks over DRIVABLE tiles only. Drivable = road + building lots,
  because streets terminate ON their buildings — lots are the junctions stitching streets
  together (regular traffic already drives through route endpoints the same way); that subtlety
  surfaced as trucks:0 when road-only BFS found the network tile-fragmented at every building.
  A fire the network cannot reach gets NO truck (`unreachable` counted) — a burning orphan in
  the streetless suburb is unreachable by design. The suburb moved below the civic strip so the
  access road can never brush an orphan (S4 stays honest). Access road pinned: starts at the
  station door, contiguous, ends on a real street; goldens regenerated. 259 py / 33 e2e green.

- 2026-08-05 — **The civic strip: public library + firehouse (Stephen's asks, same breath).**
  Two civic buildings join the plant on the western utility strip, both in the contract
  (`library`/`firehouse` points, additive; focus box extended so the opening camera never crops
  them), both pickable/searchable/outlined like the plant. The LIBRARY ("where we store the
  context and other documentation") is the city's context inventory: its panel counts real
  declared artifacts only — objects described, columns documented, tags, owners, tests — and
  names the Ossie shelf as not yet connected. The FIREHOUSE dispatches fire response: one truck
  per burning building drives firehouse→fire, parks flashing, returns (deterministic, frozen
  under ?settle=1), and the panel lists active fires clickably. The honesty line is load-bearing:
  trucks mean "failure awaiting response", never "a fix is running" — the panel states the AI
  responder is NOT CONNECTED in the local version (the future hookup: dispatch runs an agent to
  prepare a suggested fix for review; an engine-version differentiator, and any PR it drafts
  stays a draft pending Stephen's approval). 258 py / 33 e2e green; focus test renamed and
  extended; render shows the truck en route on the hot mart road.

- 2026-08-05 — **Clustering rhythm: tight bands, wide boundaries (Stephen: "I don't see any of
  the clustering stuff").** Root cause of the invisibility: uniform ROW_PITCH — grouping cannot
  read when every neighbour is equally far. Spacing now varies by relationship: block members
  touch (1), same-schema neighbours sit at NEIGHBOUR_PITCH (2), a schema boundary opens a
  BAND_GAP (5), dummy pass-throughs keep ROW_PITCH (3). Pinned by a rhythm test asserting the
  exact gaps on a two-schema fan. On dogfood the staging band now reads as one dense strip with
  open ground before seeds and after — visible at the default zoom, which uniform spacing never
  was. 258 py / 32 e2e green; demo golden regenerated (rows moved).

- 2026-08-05 — **Failing tests are buildings ON FIRE (Stephen, verbatim).** The red roof
  octahedron never conveyed "this mart is failing"; flames do, and they read at any zoom. A fire
  exists iff `test_status === "fail"` — fact, never ambience: three emissive flame tongues
  (sizes/angles from a coordinate hash, so no two fires are copies) plus a looping smoke puff
  rising and fading off the roof. Flicker is deterministic in elapsed time (no RNG) and frozen
  under `?settle=1` so screenshots stay reproducible. The fail octahedron is retired (warn/pass
  markers stay); legend row now reads "tests: fail = ON FIRE / warn / pass". Negative e2e pinned
  (nothing burns in the verdict-free demo fixture, `fireCount() === 0`); positive verified by
  render-and-look — mart__revenue burns over the mart district. 32 Playwright specs green.

- 2026-08-05 — **Sibling BLOCKS: same sources, one city block (Stephen: "if two models have the
  exact same sources, they should be clustered together to form a block").** Exact rule, never
  fuzzy: same schema + same depth + identical full source set -> members pack at PITCH 1
  (touching buildings, a real terrace) and share ONE delivery trunk (unit key collapses via
  `block_of`), since one street serves buildings fed by the same suppliers. S2 gains the block
  exception (vertical sharing ok within a block; also encoded in the sweep) and the sprawl
  fixture moved its destinations into distinct schemas — a same-schema same-source fan
  COLLAPSING to one trunk is now the reward, not sprawl. Measured reality: dogfood has ZERO
  exact-source sibling pairs (chain-heavy DAG) so it is visually unchanged; star schemas are
  where blocks shine, so demo-tycoon gained dim__customers/dim__customer_status alongside
  mart__broken (all from stg_customers) — the render shows a three-building terrace served by
  one street. Looseness (Jaccard-style near-siblings) deliberately NOT invented; that threshold
  is Stephen's call. 257 py / 31 e2e green; demo golden unchanged.

- 2026-08-05 — **New page: semantic-roads.md — Apache Ossie (OSI) design sketch.** Stephen wants
  documentation/context/semantics REWARDED, and the semantic layer's join knowledge mapped into
  the road architecture. Verified the framework first: Open Semantic Interchange, Apache
  Incubator since June 2026 as "Apache Ossie" (YAML, Apache-2; relationships are FK joins,
  always many-to-one, simple/composite keys; `ai_context` annotations at every level). Core
  design distinction: JOIN streets (declared joinability, no traffic, no load, signage toward
  the "one" side) vs lineage streets (data actually moved). Incentive layer: semantics build
  the city out of the dirt — undeclared joins are dirt tracks, declaring paves them,
  ai_context raises street signs, metrics raise landmarks; achievements are counts of real
  declared artifacts, never invented points. Sketch only — open questions for Stephen listed
  on the page.

- 2026-08-05 — **Schema neighbourhoods (Stephen: "cluster buildings by schema... otherwise this
  is going to look like a circuit board").** Within each depth column, same-schema buildings now
  form one contiguous band: bands order by their mean barycenter rank (lineage still pulls
  related neighbourhoods together), buildings keep barycenter order inside their band, and
  dummy pass-through streets stay where crossing-reduction put them — a road may cross a
  neighbourhood, buildings may not scatter. Every table keeps its own building (the inspector,
  facades and skybridges depend on that); the clustering is the ORDER, not a merge. Pinned by a
  no-A-B-A contiguity test whose first fixture couldn't fail (alphabetical seeding kept bands
  contiguous by luck — the mutation check caught it, wrong-axis discipline again) and was rebuilt
  on a split-loyalty fan that provably interleaves without the banding pass. District rects get
  tighter for free. Further densification (smaller row pitch inside a band) deliberately not
  attempted — it interacts with lane widening's south-growth margins. 255 py green; demo golden
  unchanged; dogfood verified in 3D (seeds/staging now adjacent bands, not an interleave).

- 2026-08-05 — **Merged roads keep their combined thickness (Stephen, verbatim: "two models
  merging becomes a two lane road").** A tile crossed by c edges now widens to min(c, LANE_CAP=4)
  lanes — vertical trunk runs grow east, shared horizontal runs grow one row south (H_LANE_CAP=2;
  building rows are only ROW_PITCH apart) — and the channel allocation RESERVES each destination
  group's lane count up front (`unit_lanes`), because roads only ever paint over grass: an
  unreserved lane would silently vanish, which is exactly what the new S6 sweep guard detects
  (every planned lane tile must paint as ROAD — paint is the collision detector). Routes stay
  centre-line per edge; `DagPlan.lane_tiles` carries the extra lanes. The width economics stay
  intact: a 12-way merge is exactly LANE_CAP-2 tiles wider than a 2-way (pinned), distinct
  destinations still pay full price. First version of the pin test was wrong-axis (conflated the
  approach row's south lane with tributary widening at the corner) — rebuilt to measure 2+ rows
  clear of the corner. Known cosmetic gap: the road-load heat tints the centre line only, so a
  two-lane road shows a one-lane heat stripe. Render on demo-tycoon shows the mart approach as a
  genuine two-lane street. 254 py / 31 e2e green; demo golden unchanged (no merges there).

- 2026-08-05 — **The road-load overlay: expected compute painted on the streets.** Stephen's
  analogy made a metric: "warehouses carry load, so the roads should basically correspond to
  warehouse load" — and it should be worth looking at while nothing moves ("this is ultimately a
  game to see if engineers can keep the city flowing efficiently"). Every edge now ships
  `daily_load_s`: its destination's measured build cadence ((n-1) successful builds over their
  real span, one-hour floor) times mean build cost, from the new `RunHistory.build_history`
  (every successful build's timestamp+cost — `node_results` only kept the latest). The client
  accumulates load per road tile across all routes crossing it — a shared trunk glows with the
  combined load of everything it carries — and tints tiles on a cool→hot ramp normalised to the
  busiest tile. `T` toggles; the legend carries the ramp with engine-neutral wording ("compute
  load" — Snowflake bills these as warehouses, MotherDuck as ducklings, local DuckDB is free).
  Fewer than two builds → null → no tint, and a catalog with no usable history shows no overlay
  at all (e2e-pinned on the demo fixture). demo-tycoon gained a week of scheduled history
  (6-hourly stg_orders, daily marts): render shows the orders street amber, the customers street
  cool blue, and both feeds into mart__revenue red. 252 py / 31 e2e green.

- 2026-08-05 — **Traffic is real data movement only (Stephen: "I don't know why the people are
  moving between buildings so much").** The always-on Bernoulli flow was demo theater. Now a
  vehicle on an edge asserts a fact: the edge's DESTINATION was built/loaded recently — spawn
  weight is the dst lot's `last_build_age_s` fading linearly to zero over one hour, shaded by the
  edge rate for relative volume. No run history → a perfectly still city (the moving twin of
  unknown-never-renders-stale), which is exactly what the plain demo.duckdb fixture now shows and
  what its e2e spec pins (`vehicleCount() === 0`, with `?ambient=1` restoring the old decorative
  flow for demos — parked like `?guests=1`). The legend says it on screen: "traffic = built in
  the last hour". Verified on demo-tycoon: vehicles ride the 20-minute-old pipeline while the
  forgotten mart's street and the orphan suburb stay empty. 30 Playwright specs green.
- 2026-08-05 — **STREETS v2.1: tributaries — small roads combine when they lead to the same
  place (Stephen's direction, verbatim: "Combine the small roads together if they lead to the
  same place").** v2 gave every edge its own dedicated vertical track, so N edges converging on
  one destination arrived as N parallel streets — correct, but it read as plumbing, not a city.
  Now edges sharing a DESTINATION merge like tributaries: per channel, one trunk track per
  destination group (each tributary runs east along its own row to the trunk x, merges
  vertically on it, and the group leaves together at the head's row), and long edges to the same
  destination share ONE pass-through dummy per intermediate column — the system stays merged
  once it merges. A group's trunk x is its head's row-rank among the channel's track units
  (destination groups + loop edges, sorted by exit row so trunks rarely weave). Channel width
  now prices sprawl per DISTINCT destination (+ loop edges), not per edge: a pure fan-in of 12
  is exactly as wide as a fan-in of 2 (pinned), while a 12-way fan-out to distinct destinations
  still pays 10×TRACK_PITCH more than a 2-way (the sprawl test, re-aimed at distinct-destination
  monotonicity). S2 RELAXED, not deleted: vertical sharing allowed iff the edges share a source
  or a destination; different-src-AND-different-dst edges still never fuse, so every street
  stays traceable. `edge_routes` stay per-edge full lot→lot paths — overlapping on shared trunks
  is desired, vehicles merge. Process per the law: PIL spike first over demo/dogfood/36-node-70-
  edge synthetic — the renders showed dogfood 106→76 tiles wide and the synthetic 375→193 with
  same-hue tributaries visibly combing onto shared trunks, demo byte-identical (clean pipelines
  keep their village; the contract golden did not change); the first merge-pinning test was
  itself wrong-axis (asserted trunk sharing on a 2×2 fan where one tributary runs straight and
  has no vertical run at all) and was caught and rebuilt on a 4-source fan; both mutations
  (everything-on-one-track, back-to-per-edge-tracks) fail the guards, restore verified from an
  in-memory copy. 251 Python tests green; demo + dogfood verified in 3D on a side port.

- 2026-08-05 — **STREETS v2: the edge IS the street (Stephen's live redirect).** His correction of
  P1: "the lineage connections between each model node should be matched by a street style grid
  that literally connects the two. There shouldn't be other buildings in the way" — and the
  intended consequence: "people will not want to see big ugly sprawling cities." So placement
  itself became graph-driven, replacing the ring layout entirely: `plan_dag_layout` puts buildings
  in **topological columns** (depth via the existing cycle-safe SCC condensation), orders rows by
  barycenter sweeps, and routes every edge through a **channel between columns on its own
  dedicated vertical track**, with dummy row slots reserving pass-throughs for multi-column edges
  — so no building can ever stand in a street's way (S1, the redirect verbatim as a property
  test). Horizontal rows merge like real avenues; vertical tracks never do (S2). Cycles share a
  column and route out-and-back through their channel. Orphans keep their streetless southern
  suburb; the plant + POWER_LINE utility strip feeds exactly the depth-0 sources (moved north
  after the render showed a tall orphan occluding it). **Sprawl is now the gameplay signal**: each
  edge widens its channel by TRACK_PITCH, so the 70-edge synthetic paves a 392-tile wasteland
  while the clean demo is a 31-tile village — pinned by `test_sprawl_channel_width_grows...`.
  Districts became bounding rects (`w`/`h` replaced `ring`/`size` in the contract — the ring
  concept is gone). Process: two PIL spike rounds (accepted after track/row spacing fixed the
  pavement-lake defect), then codify; the new planner tests caught a duplicate-joint route bug
  and an over-strong sharing invariant on first run. 250 Python tests + 29 Playwright specs
  green; dogfood verified in 3D at far and street level. Supersedes the P1 R-rules (R1/R6 spirit
  survives as S1/S4; R3/R4 bundling died with the rings — every edge now owns its street).

- 2026-08-05 — **PRIORITY THREE, second slice: SKYBRIDGES — column-level lineage.** New
  `catalog/column_lineage.py`: sqlglot traces every *measured* output column (from
  `duckdb_columns()`, never the SQL's own claims) back to the catalog columns it reads. Sources of
  SQL, most authoritative first: dbt `compiled_code`, dbt `raw_code` with the resolvable jinja
  subset substituted (`config` stripped, `ref()`/`source()` → relation names — dogfood's manifest
  has raw_code on all 40 models and compiled_code on none, so the fallback IS the real path),
  and view definitions. Models with residual jinja (loops, `var()`) are **counted into a note**,
  never mis-parsed. Traced pairs ride the contract as `edges[].columns` (`[src_col, dst_col]`,
  additive, v1 unchanged), and a traced pair unions its table edge in even when `depends_on`
  never declared it — a proven column read is the strongest possible edge evidence. The client
  renders bridges **for the selected building only** (its whole column neighbourhood), anchored
  on the exact facade windows via the layout now shared with `facade.ts`; always-on bridges would
  be spaghetti at city scale. Factory manifests gained `raw_code` + `source_name` (both real-shape
  fields); the tables-only integration test proves the alias-override rule holds at column grain
  (`ref('stg_daily')` → `staging.daily`). 281 Python tests, 29 Playwright specs green;
  render-and-look on the rich fixture shows five gold bridges fanning from `mart__revenue`'s
  windows to its two staging feeders, each landing on its own floor.

- 2026-08-05 — **PRIORITY THREE, first slice: buildings grew silhouettes.** Schema architecture now
  reads from the skyline, not just the inspector. Clock spire (gold cone) for temporal columns,
  rooftop antenna for nested/JSON columns, gold doorway for a unique/primary-key test, and a
  **construction crane** (mast beside the building, orange boom over the roof) when
  `dbt_schema_changes` recorded drift in the last 7 days — the crane rides a new `SchemaDriftAt`
  timestamp signal through a `DRIFT` channel onto `Lot.schema_drift_age_s`, emitted in city.json.
  The fixture factory writes a real 8-column `dbt_schema_changes` table (`write_schema_changes`),
  and the demo-tycoon scenario drifts `stg_customers` two days ago so the crane is demoable. Facade
  window rows are now vertically centered instead of bottom-stacked. Verified by render-and-look on
  the rich fixture (spire, antenna, doorway, crane all legible at inspect distance); 272 Python
  tests + 26 Playwright specs green.

- 2026-08-05 — **PRIORITY TWO landed: the observation HUD is complete.** Health strip (zero-click
  health: failing/warning tests, build errors, late sources, 14d+ unbuilt — chips render only when
  nonzero, all-clear shows a quiet check, and every chip cycles through its offenders via a 0.6s
  camera glide). Problems panel on `P`: the triage list worst-first with the coverage gauges
  (columns documented %, objects tested %, freshness SLAs) in its header. Search on `/` / Cmd-K over
  keys, tags, owners and the plant; Enter flies. Footer reworked: short status, a live "as of Xs
  ago" (client fetch-time — deliberately NOT a contract timestamp, which would break
  byte-stability), degradation notes in an `ⓘ notes (N)` popover, and the keymap behind `?`.
  Keyboard shortcuts ignore typing in inputs, with a spec typing "raw performance" into search and
  proving R/F/P never fire. 26 Playwright specs green; every principle from `docs/hud-design.md`
  holds: zero-click health, every number is a door, absence stays named.

- 2026-08-05 — **PRIORITY ONE landed: streets ARE the lineage.** The generator's road network is
  now built FROM the edge graph (Stephen's inversion). The rules, each mutation-pinned: **R1** a
  street exists iff an edge exists — the decorative district grid is gone; **R2** intra-district
  edges get lanes (dogfood's 9 were invisible for the project's whole life); **R3** inter-district
  edges bundle onto one avenue per district pair between cardinal gateways (wall midpoints — the
  spike showed per-pair border clamps produce parallel spaghetti); **R4** bundles ≥3 paint 2-wide,
  widened consistently perpendicular to direction; **R5** ingestion arterials reach only ring-0
  districts holding a connected lot (the old everywhere-arterials were decoration); **R6** orphans
  get no street. Lanes route via **even-coordinate corridors** — lots live at odd/odd, so corridors
  can never dead-end into a building — which also makes every edge's route a contiguous road path,
  carried on `CityMap.edge_routes` and emitted as `edges[].route` in city.json. **The client's
  traffic now drives the real streets.**

  Process notes. Build-before-spec held: two PIL spike renders (current vs proposed, demo +
  dogfood) shaped R3's gateways and R4's widening before any code; the R5 refinement (arterials
  must be earned) fell out of looking at the demo render. The property sweep's `_assert_sound` was
  rewritten from grid-world invariants to: street access for every connected lot, no route built
  for an orphan, route contiguity with no-GRASS interiors that never cross their own districts'
  buildings, and earned-arterials both ways. Mutation: 10 real mutants — 7 killed, 3 survivors all
  real: a **dead clamp branch** in `_even_beside` (largest odd local index is size-2, so +1 always
  fits — code simplified rather than tested), the sweep allowing lanes through their own district's
  lots (N3 tightened), and the R4 width measure confounded by converging access lanes near
  gateways (now measured on the trunk's middle third). Both remaining mutants kill-verified.
  Looked at in 3D on dogfood: int → staging → mart reads as flow, twin trunk avenues, no spaghetti.

- 2026-08-04 — **Schema as architecture, stages 1–3 (Stephen: "go wild") + in-place R.**
  `objects[].columns` carries the table's schema with three-way provenance: name/type **measured**
  from `duckdb_columns()` (database-scoped like the catalog scan; a missing function costs the
  facade, not the city), description **declared** by dbt column docs, worst column-test **verdict**
  from run history. The inspector gains the full column table. **Facade windows** render the schema
  from the street: one window per column on the south face, hue by type family (numeric blue / text
  green / temporal amber / nested violet), lit = documented, dark = undocumented, red = failing
  column test — documentation coverage is literally how lit-up the city is. In-place `R` landed the
  same evening: mount/dispose cycle, camera and selection survive, a failed fetch keeps the old
  city, and the regression spec proves no navigation. Roadmap approved but unbuilt: type
  silhouettes, drift cranes, sqlglot column-lineage skybridges — see the handover.

- 2026-08-04 — **Direction reset (Stephen): observation platform, not a game — not yet.** The score
  is gone entirely, ratings are gone (invented opinions have no place on an observation platform),
  and the guest flow is parked behind `?guests=1` — off by default, because an observation platform
  shows no invented activity unless asked. What survives of the flow under the flag is honest:
  guests colour by **real** verdicts (failing test / build error → red), nothing is tallied. The
  mechanics module and its layering guards stay, so the game can return later without re-plumbing.
  This supersedes the Phase-G "first playable slice" entry below and the plan's Phase-G framing.

- 2026-08-04 — **Building height is now an absolute log scale** (Stephen's direction): density
  level = decade of rows (1–9 → 1, 10k → 5, 1M → 7, 10M+ → 8, clamped), replacing the percentile
  rank that made 1,200 and 250,000 rows near-neighbours. Height now carries magnitude and is
  comparable across catalogs; a uniformly tiny warehouse renders uniformly short, which is honest.
  Golden regenerated; guests' attraction inherits the new scale automatically.

- 2026-08-04 — **dbt's semantic layer reaches the UI.** The manifest's declared context now rides
  `city.json` (`objects[].dbt`, nullable): description, materialization, tags, owner, and **tests by
  name and column, each with its last verdict** — null status means *declared but never run*, shown
  as an open circle because an unrun test must not read as passing. The inspector renders it all
  (doc paragraph, chips, owner, the test list with coloured dots). **Source freshness comes from
  dbt's own artifact**: `target/sources.json` SLA verdicts land as `lots[].freshness_status` via a
  new FRESHNESS channel (cone markers: red error / amber warn, offset when a test marker shares the
  roof), and its `max_loaded_at` beats schema-level dlt timestamps for DECAY. Missing artifact is
  noted only when sources exist ("run `dbt source freshness`"); `runtime error` folds to error.
  **Test passes are now visible from the skyline** — a small green octahedron — so tested-and-passing
  stops looking identical to never-tested. Legend gained both vocabularies. Dogfood has no
  sources.json yet; the note will tell it to run the command.

- 2026-08-04 — **Phase G, first playable slice: guests, ratings, the score.** The simulated layer
  lives client-side (`web/src/mechanics/guests.ts`) per the three-layer decree, and the decree is
  enforced twice: `tests/test_web_layering.py` greps real imports (mechanics may reach only the
  contract and the deterministic primitives; only the composition root and its presentation layer
  may reach mechanics), and an e2e guard asserts the document is **byte-identical** after ~50 ticks
  of simulation — a rating cached onto a lot lands as a named failure. The game reading: guests
  spawn at the database and carry queries to buildings (attraction = density × freshness-decay,
  unknown stays fully attractive per THE RULE; unpowered draws nobody), and a failing test or build
  error is a bad experience — the guest walks home **red**, the building's rating (Bayesian around
  a neutral prior) sinks, and the city score (served − 2×bad) stalls. Ratings and visit counts
  reach the inspector through the provenance seam labelled **simulated**; the score sits in the
  header. Verified by eye on the synthetic project: a stream of red guests leaving the failing
  mart, rating ★☆☆☆☆ 1.8, score suppressed. Deterministic over (document, seed, tick count) with an
  RNG stream independent of traffic's. Future G work: growth/decay feeding back into density,
  scoring over time windows, goals.

- 2026-08-04 — **Phase F complete: the city lives in time.** Signals now declare a kind
  (scalar/timestamp/status), `CHANNEL_KIND` validates bindings at apply time, and `apply_signals`
  takes an injected `now` — timestamps become ages in exactly one place (`as_naive_utc` is the
  single normalisation point). Absence is a missing key. THE RULE, tested first and repeated in
  every module it touches: **unknown never renders as stale** — a catalog with no history keeps
  every temporal field None/null and renders full colour, no tint, no marker.

  Three new channels over Phase E's run history: `last_build_at` → DECAY (desaturation toward grey
  over ~30 days, floor 0.35), `build_status` → TINT (error shifts red), `test_status` → CONDITION
  (a red/amber octahedron over the roof). Status vocabularies are frozen with containment tests;
  unrecognised build words map to "partial", unrecognised test words to "fail" — for a test result,
  an unknown word is not reassurance. `row_delta` reads dlt loads and says plainly it has no
  dbt-model coverage in v1. ?flat=1 keeps exact zone colours so the pixel suite stays meaningful.

  **Build replay (F4).** `sim/build_replay.py` schedules the last run topologically over the edges
  from measured per-node durations (infinite parallelism — dbt stores no per-node start times), and
  refuses rather than misleads: no history and foreign history are named, not animated.
  `city.json` carries `replay` (null on plain files — golden gains one line); the client plays it
  with per-lot height factors, uncovered objects keep standing, and the footer shows the verbatim
  note "durations measured, ordering reconstructed" for the whole run. Watched it play on the
  synthetic project: staging grows first, marts start exactly when their upstream finishes.

  **`scripts/make_demo_tycoon.py` (F5)** builds every named scenario at once: fresh pipeline,
  21-day stale mart, failing test, warning test, build error, and an unknown object standing next
  to the stale one. All verified by rendering and looking; dogfood verified live (its real failing
  test shows as a red marker once its next `tycoon` run refreshes node history).

- 2026-08-04 — **Phase E: the Tycoon backend — real dbt lineage on the map, run history in hand.**
  `load_context` dispatches: a `.duckdb` file or `md:` catalog takes the old path byte-for-byte
  (tested equal to `load_catalog`); a **directory** must hold a `tycoon.yml` (never a guess — a
  plain file inside a project logs an info suggesting the root, and that is all). The tycoon path
  reads three artifacts **off disk, never importing the `tycoon` package**: `tycoon.yml`
  (`catalog/tycoon_project.py` — only the needed keys, so drift like `ask:` is ignored by
  construction; `${VAR}` interpolated; unknown vars left visible), the dbt manifest
  (`catalog/dbt_manifest.py`), and `.tycoon/metadata.duckdb` (`catalog/run_history.py`).

  **The join rule is the crux and is now pinned six ways:** key = `schema.alias`, case-insensitive,
  catalog spelling canonical, never the unique_id's last segment. The fixture factory
  (`tests/fixtures/tycoon_factory.py`) mirrors shapes copied from the real dogfood database — an
  `alias:`-overridden model, two models whose aliases collide across schemas (dbt forbids duplicate
  model *names*, so that is the realistic same-table-name shape; the first factory draft used
  duplicate names and silently lost a manifest node to dict collision), singular tests with
  `attached_node: None`, a source living in another database, `success` NULL on every run row and
  `rows_affected` NULL on every node row. **Headline test: a tables-only warehouse — where view-SQL
  lineage is structurally zero — gets real edges from the manifest.**

  `Edge` gained `provenance` (`manifest`/`duckdb`/`view_sql`): existence is a union, the most
  authoritative source tags it. `city.json` edges carry it (additive; golden regenerated) and the
  inspector labels each lineage entry *declared (dbt)* vs *inferred (SQL scan)*. `database.notes`
  carries the degradation ladder — every rung tested: missing manifest, corrupt manifest, missing
  metadata, empty history, **locked** metadata (a writer holds the handle), missing individual
  table. `dbt_runs.success` is never read (NULL on all real rows); ok derives from
  `models_error == 0 and tests_failed == 0`.

  **Canary against real dogfood** (read-only, opt-in via `DATABASE_TYCOON_DOGFOOD`): 42 objects, 33 edges
  — 31 declared + 2 inferred, where SQL-scan alone had almost nothing — notes correctly naming the
  17 MotherDuck-side sources and the dev-target history, and the latest run correctly reported
  failing with the real failing test (`assert_toggl_deel_hours_variance`). Rendered and looked at:
  dogfood is a four-district city with a dense declared road network.

  **Mutation pass: 12 real mutants, 10 killed, 2 survivors — both genuine test holes, both
  closed with kill-verified tests.** The case-insensitivity test had given the *catalog* side
  all-lowercase keys, so dropping the fold there was invisible (wrong-axis, again); and tag
  precedence was unobservable in a tables-only fixture because manifest and scan edges never
  overlapped — the new test rebuilds one model as a view so both sources see the same edge.
  `pytest` now needs `pythonpath` and package-ified `tests/` (which also retires the
  basename-collision gotcha). Footer status got the plan's ellipsis clamp — dogfood's notes
  overflowed it, caught by eye.

- 2026-08-04 — **Phase D: the pygame renderer is gone, and the container serves the real app.**
  Deleted: `app.py`, all of `render/`, `stills.py`, `server.py`, `tests/render/`,
  `tests/test_framing.py`, `tests/test_app.py`, and the `pygame-ce` runtime dependency (it survives
  only in a new `art` dependency group for `scripts/make_default_theme.py`). 206 Python tests remain
  from 326 — the 120 that left tested the thing that left. The suite-wide no-pygame guard now covers
  `tycoon_city.webserve` too.

  **Preconditions, all discharged before deleting.** (1) The sim suite was certified by mutation:
  24 mutants over `layout.py`/`generator.py` — 21 killed by `tests/sim`, the round→int placement
  mutant killed by the contract golden (so the recorded oracle is *sim suite + golden*), the
  bisection-bracket mutant equivalent (monotone predicate, same fixed point from a wider bracket),
  and one genuine hole — same-district edges could paint pavement over spare lot slots — closed with
  a kill-verified test whose fixture is the one shape that exposes it. Both no-op controls survived.
  (2) The framing policies were already ported (`framing.spec.ts`). (3) A parity inventory of
  `render/*` (local-LLM per-module sweep, its proven lane) found two real gaps, both closed before
  deletion: the map legend (now built from `palette.ts` so it cannot name a colour the renderer
  doesn't use) and `R` re-reading the catalog (reload with the orbit pose riding sessionStorage;
  in-place rebuild deferred to Phase F). The hover *outline* is an accepted difference. (4) Eyeball
  artifacts: demo, chain10, and flat-100 — 100 districts on one ring render as the designed wheel
  with `no lineage detected` in the status bar. The Linux-container e2e run defers to CI (A7, blocked
  on the repo push): the deployment container serves static files, so WebGL runs in the visitor's
  browser, never in the container.

  **The replacement server** (`tycoon_city.webserve`, stdlib-only) serves the built web bundle plus
  `/city.json` and `/spritesheet.png` regenerated per request — so `R` shows real changes — and the
  catalog-probing `/healthz` carried over. The Dockerfile grew a node build stage and lost SDL
  entirely. `docker run -p 8000:8000 tycoon-city` now serves the *interactive* city: verified by
  driving the container with headless Chrome — click → inspector, lineage walk, stats.

  **One bug found only by driving the served bundle like a user:** the inspector, parented to
  `<body>`, anchored to the *viewport* and covered the header's Stats button — unclickable exactly
  when a building was selected. The e2e suite missed it because its stats test starts from a fresh
  page; the fix (overlays anchored inside `#app`) ships with a regression spec that selects first,
  then opens Stats. Suite is now 15 specs.

- 2026-08-04 — **Sprite-atlas terrain (C2 complete) — and it fixes the far-view readability issue.**
  The terrain quad now renders through an index-texture shader, exactly as the plan specified: an R8
  DataTexture holds one kind id per tile (`unpackAlignment = 1`, or any width not divisible by 4
  shears the map), a 7-cell runtime atlas is cut from the theme spritesheet on a canvas (grass,
  grass_alt, road, power_line, plant, a flat pad for LOT — buildings are 3D boxes so the 2D building
  sprite never shows — and water), and the fragment shader maps fragment → tile → kind → atlas cell,
  with grass alternating on `(x + row) % 2` and locals clamped a half-texel in so cells never bleed.
  Unlit on purpose: sprites carry their own shading, like the 2D map. The skirt repeats a 2×2-tile
  checker cut from the same sprites, phase-aligned to the grid's parity — the boundary is invisible,
  verified by a full-grid frame (a phase mismatch would outline the 42×42 grid) and close zooms.
  `?flat=1` keeps the palette-texture path untouched; the exact-colour pixel tests still mean what
  they say. 14/14 e2e green.

  **The known far-view issue mostly dissolved as a side effect.** chain10's opening frame — which
  showed *no roads at all* under palette+mipmap minification — now shows every district's street
  grid and the whole arterial: per-fragment nearest-index sampling keeps one-texel roads crisp at
  any distance instead of mipmap-fading them. The trade is mild shimmer under camera motion at
  extreme distance, which reads far better than absence.

  Two colour-space bugs caught by eye in one feature, opposite directions: the *skirt* (built-in
  material, decodes by texture tag) rendered washed-out pale with `NoColorSpace` and needed the
  `SRGBColorSpace` tag; the *atlas* (custom shader, writes samples straight to the sRGB buffer)
  needs `NoColorSpace`, or the decode-to-linear would darken it. The rule of thumb worth keeping:
  built-in materials want honest tags; raw ShaderMaterials want untagged bytes.

- 2026-08-04 — **Traffic lives (C4 + a root-cause signal fix), and the Stats panel (C5 complete).**
  Porting traffic to the client exposed that it had **never once run against real data**:
  `edge_volume` took `min(src, dst)` row counts, SQL-scan lineage always points *into* a view, and
  the loader records every view as 0 rows — so the signal was structurally zero on 100% of
  loader-produced edges and no catalog ever spawned a vehicle, in pygame either. The one existing
  test used a 40-row *view*, a shape the loader never emits, which is how it hid. Fixed at the root
  (`cb157e7`): volume is the upstream row count, falling back to downstream; view→view edges stay 0
  because both ends are unmeasured and this project does not invent numbers. Golden regenerated per
  the contract protocol — the diff is exactly two rates (orders 1.0, customers 0.024).

  The client tick is `web/src/sim/` — mulberry32 (`?seed=`, default hashed from the database name),
  the manhattan-path port with the same leg order the generator paved (matching it is what keeps
  vehicles on the pavement), and a 10 Hz accumulator identical to the pygame app's `TICK_DT`.
  Vehicles draw as one InstancedMesh with positions interpolated between tiles by the accumulator
  fraction — presentation smoothing over the same discrete tick. `?settle=1` freezes traffic, per
  the C6 spec. The Stats screen became a modal table (schema/object/kind/rows, capped at 200 with a
  count note) whose rows select the object on the map. `npm run e2e` now also asserts: stats opens,
  a row click selects `marts.fct_revenue` and closes the modal, and the seeded vehicle count is
  nonzero across two samples. Verified by eye: a dense stream on the rate-1.0 road, occasional
  singles on the 0.024 road.

  Still owed in Phase C: sprite-atlas terrain (also the far-view contrast fix), `?flat=1`
  exact-colour mode, and promoting the harness to `@playwright/test`.

- 2026-08-04 — **The 3D web renderer's first working slice (Phase C1–C3, C5 partial).** `web/` is a
  Vite + TypeScript + three + zod app that reads `city.json` and renders the interactive city:
  index-colour DataTexture terrain (one quad, one draw call) with a grass skirt, one InstancedMesh
  for every building (height from `target_density`, colour from zone style, unpowered dimmed via
  instance colour), the plant as an emissive landmark, district plates with CSS2D labels, orbit
  camera framed on `focus` (F flies, H reframes), and real picking: hover tooltips, click →
  inspector with walkable upstream/downstream lineage, sky click clears. `npm run dev` in `web/`
  after `npm run demo-data`. Verified end-to-end with the C0 Playwright harness clicking real
  projected screen coordinates — all interactions pass with a clean console.

  Two defects found by looking, neither by the harness. (1) The grid rendered visibly darker than
  its skirt: `THREE.Color` stores linear floats and the bake wrote them raw into an sRGB-tagged
  texture — bytes must be `convertLinearToSRGB`'d. (2) On chain10 the opening frame showed **no
  roads and no buildings**: NearestFilter minification simply misses one-texel streets once the
  camera is far enough that the grid is under a texel per pixel, and this catalog's all-residential
  green boxes camouflage against grass. Mipmapped minification (nearest magnification kept) turns
  "vanished" into "faded"; the remaining far-view contrast problem — thin lines fade, green-on-green
  hides — is a known issue for the atlas/marker pass, and zooming in resolves everything (the
  close-up on chain10 is exactly the game). The demo catalog's opening frame is unaffected.

  Deliberate scope cuts in this slice, all still owed by Phase C: sprite-atlas terrain (flat colours
  ship first, per the plan), client-side traffic (C4), the stats panel, `?flat=1` exact-colour mode,
  and the `web/e2e` suite as checked-in tests (the harness lives in scratchpad today). `__dbt`
  (select/screenPos/doc) is the seam those tests will use.

- 2026-08-04 — **`city.json` v1 ships (B3–B5), and one plan assumption was wrong.** The contract, its
  emitter (`tycoon_city.export`), `tycoon-city-export`, a committed golden at
  `contract/fixtures/demo.city.json`, and `docs/city-json-v1.md` as the normative page. 324 tests
  green, up from 236. `stills.build_state` now goes through `export.build.build_city`, so a
  screenshot and an exported document describe the same city by construction.

  **The measurement that changed the design.** The plan specified tiles as "row-major run-length
  pairs" on the reasoning that RLE "exploits grass dominance". That holds on realistic catalogs and
  fails badly on the one `sim.layout` already documents as uncompactable: 500 one-object schemas give
  a 905² grid where the 500 radial arterials shred every grass row they cross, so **34% of cells
  start a new run** — 278,161 runs. Nested pairs at `indent=2` would have cost **6.12 MB**, past the
  5 MB the plan itself calls "the schema is wrong", and worse than shipping the raw grid (1.64 MB).
  So `dumps` writes the document at `indent=2` *except* `tiles_rle`, spliced in on one line:
  **1.31 MB, 27 KB gzipped, 0.13 s** at that worst case, and 6.9 KB for `demo.duckdb`. Full table in
  `docs/city-json-v1.md`. Measuring before fixing the format is what the plan's own risk register
  asked for, and it earned its keep on the first try.

  **The contract was rendered and looked at, not just tested.** A throwaway renderer that imports
  *nothing* from `tycoon_city` and reads only `city.json` + the spritesheet reproduces the pygame map
  exactly — same districts, same rings, same arterials, the one orphan dimmed — and additionally
  draws district plates and ring labels, which B2's `CityMap.districts` made possible for the first
  time. Doing that de-risking in Python rather than discovering it in TypeScript is deliberate: a
  contract that cannot redraw the map is much cheaper to find here.

  **Guards mutation-tested, since a contract test that cannot fail is the trap this repo keeps
  springing.** Ten mutants, all killed: tile ids taken from `auto()` values instead of legend
  positions; RLE no longer coalescing; the cell-count check disabled; the presentation tween leaking
  into the document; edges pointing outside the catalog emitted; sprite order unsorted; `tiles_rle`
  not collapsed; `focus` dropping the plant; signals never applied; the export package importing
  pygame. A deliberate no-op mutant survived, which is what proves the harness discriminates rather
  than failing on everything. Run under `PYTHONDONTWRITEBYTECODE=1` with `__pycache__` cleared.

  Two smaller notes. `tests/export/test_export_no_pygame.py` is named around a **pytest basename
  collision** — with no `__init__.py` in the test directories, a second `test_no_pygame.py` breaks
  collection of *both*, worth knowing before adding any test whose basename already exists. And that
  guard is stronger than the `sim` one it copies: it installs a `meta_path` finder that makes pygame
  genuinely unimportable, so a *lazy* import inside a function body fails too — the `sim` version
  only checks `sys.modules` afterwards, which such an import satisfies while still crashing when
  called.

- 2026-08-04 — **C0 passes: headless WebGL works on this machine.** Three boxes of differing height
  on a ground plane, rendered by headless Chrome via Playwright and screenshotted: 79.8% of the
  canvas painted, 5 distinct colours, no errors. That is the single biggest risk in the plan retired,
  and it is exactly the shape Phase C needs (height encodes density). Playwright reports
  `WebKit WebGL` under `--use-angle=swiftshader --enable-unsafe-swiftshader`.

  Two gotchas cost the attempt, both harness rather than capability, and both would have recurred in
  Phase C: (1) the cached Playwright browsers are build **1228** while the installed driver wants
  **1234** — rather than a ~100 MB download, `chromium.launch({ channel: 'chrome' })` uses the
  Google Chrome already on the machine; (2) ES module imports are **blocked over `file://` by CORS**
  (`Cross origin requests are only supported for protocol schemes: ... http, https`), so the spike
  page must be served over HTTP even for a local one-file test. Neither is a WebGL problem, and the
  first attempt's black frame was the second gotcha in disguise.

- 2026-08-04 — **Confirmed in a real browser: the stills container has nothing to click.** Driving it
  with Playwright — the capability whose absence let the concurrency bug ship — reports page 200,
  title correct, all three images decoded at 1024x768 (so the concurrency fix holds under a real
  browser's parallel fetches), and `clickable elements: NONE`. Clicking a building changes nothing.
  This is the stills design working as built, not a defect: the container renders single frames and
  serves them as images. The pygame app is interactive; its container is not. Interactivity is
  Phase C.

- 2026-08-04 — **The container was broken in a browser and I shipped it anyway.** `render_png`
  called global `pygame.init()`/`pygame.quit()` per request. Under `ThreadingHTTPServer` a browser
  fetches all three screens at once, so the first render to finish tore the library down under the
  others (`pygame.error: Library not initialized`) — and the survivors had been drawing into the same
  shared display surface, returning 53 KB where a sequential render gives 30-36 KB, i.e. each
  other's pixels.

  **I tested it with three sequential curls and declared it working.** Each request succeeds alone;
  the bug exists only when they overlap. Same wrong-axis pattern as the rest of this branch — right
  assertion, wrong access pattern — except this one reached Stephen, who reported it as "doesn't work
  at all".

  Fixed by treating pygame's display as the per-process global it is: initialise once, never quit,
  serialise renders behind a lock. Sub-second renders make queueing three of them a non-issue.
  `tests/render/test_stills_concurrency.py` fires every screen from threads over four rounds and
  asserts **byte-equality with the sequential render** rather than merely that bytes came back — a
  shared surface yields plausible PNGs of the wrong screen, which a truthy check accepts. Mutation
  verified: restoring the per-call init/quit fails it; file restored byte-identically under
  `PYTHONDONTWRITEBYTECODE=1`. Re-tested by fetching the page and all three images concurrently:
  correct sizes, byte-identical to reference, zero errors in the container log.

- 2026-08-04 — **The MotherDuck spike found a real bug, and it was not the one it went looking
  for.** `load_catalog` scanned `duckdb_tables()`/`duckdb_views()` with no `database_name` filter.
  Against a local file that is invisible, because nothing is attached. MotherDuck attaches every
  database and share in the account on connect — verified by querying `my_db` and getting back
  `dbt_poc` and `dogfood_dbt_prod` objects — so `load_catalog("md:my_db")` would have merged a whole
  account into one city and exhausted `MAX_OBJECTS` with objects nobody asked for, including from
  shares. Scoping is now `database_name = current_database()`, which is unaffected by ATTACH and so
  needs no MotherDuck special-casing. The scan is extracted as `_scan_catalog(con)`, which Phase E
  wanted anyway.

  The first test written for this **passed without reproducing the leak** — ATTACH is session-scoped,
  so closing the setup connection discarded it and `load_catalog` opened a fresh connection with
  nothing attached. Right assertion, condition never created: the same wrong-axis pattern, in a test
  written minutes after documenting the trap. Replaced with one that asserts on `_scan_catalog` with
  a live ATTACH, and confirmed to bite by mutation (dropping the filter fails it; file restored
  byte-identically, sha verified, run under `PYTHONDONTWRITEBYTECODE=1`).

  `md:` sources are now accepted: the filesystem existence check is skipped for them, and the
  displayed name is the catalog rather than a path stem (`md:_share/<name>/<uuid>` shows `<name>`,
  since neither `_share` nor a UUID names anything useful). **The MotherDuck connection itself
  remains untested locally** — there is no `MOTHERDUCK_TOKEN` and no `~/.duckdb/motherduck_token`,
  so the local duckdb client cannot authenticate. The session's MCP connector authenticates
  separately and cannot stand in for that code path.

- 2026-08-04 — **Database Tycoon runs in a container.** Renamed from Pipeline City (distribution
  `database-tycoon-city`, module `dbtycoon`, scripts `dbtycoon`/`dbtycoon-stills`/`dbtycoon-serve` —
  the names as they shipped that day, all renamed on 2026-08-09 to `tycoon_city` and `tycoon-city*`);
  the distribution name differs from the product name only because `database-tycoon` on PyPI is
  already the Tycoon CLI, and that constraint has since been relaxed as this may never be pip
  installable. Two string literals survived the import rename and had to be caught by grep: the
  subprocess import names in `tests/sim/test_no_pygame.py`, which would have left that guard passing
  while guarding a module that no longer existed, and a logo fallback in `render/theme.py`.

  **The package was never installable.** `themes/` sat at the repo root while pyproject packaged
  only `src/`, and the theme path was resolved relative to `__file__` — from
  `site-packages/tycoon_city/app.py` a `parents[2]/"themes"` walk lands in the venv's lib directory.
  Themes now ship as package data and **seven** independent `__file__`-relative resolvers collapse
  into one `importlib.resources` lookup: the two the plan named, plus five more that each test file
  had grown for itself. The tests now exercise the real resolver, so the next packaging break fails
  a test instead of only failing at install time. Verified by building the wheel and running the
  catalog-to-generator pipeline from a clean venv outside the repo.

  `scripts/screenshot.py` moved into the package as `tycoon_city/stills.py` (the container must import
  it; `scripts/` is not in the wheel), gaining `render_png` which returns bytes so the server needs
  no temp directory. All three screens render byte-identically to before the move. New
  `tycoon_city/server.py` is stdlib-only — no framework, no new dependency.

  Dockerfile is `python:3.12-slim` (verified first that pygame init, font render and image save all
  work there under the dummy driver — alpine would force an SDL source build), multi-stage with uv
  against the committed lock, non-root, 244 MB. **`uv sync` installs the project editable by
  default**, which produced a container whose console script could not import its own package: the
  venv pointed back at `/src`, which the final stage does not copy. `--no-editable` fixes it. The
  demo catalog is baked at an explicit `/data/demo.duckdb` rather than a package-relative path,
  which would have tied the Dockerfile to a site-packages layout that moves with the Python version.

  Verified running: `/healthz` reports the real catalog, all three PNG routes return images, the
  index page renders, unknown screens 404 with the valid list, a missing database 503s with the
  path, and the healthcheck reports healthy. A mounted tables-only catalog renders three lit
  buildings with `no lineage detected` in the strip — the honest "we don't know" rather than three
  false orphans.

- 2026-08-04 — **Renderer stack settled: WEB / Three.js. Ursina rejected after a feasibility
  spike.** Ursina 8.3.0 installs fine on this Mac but **cannot render headless**, verified three
  ways: `window-type offscreen` is silently ignored (returns a `GraphicsWindow` via cocoadisplay),
  Panda3D's auto-generated shaders target GLSL 130/140 which macOS's OpenGL core profile rejects
  (`version '130' is not supported`) so every frame comes out black, and the software fallback
  cannot load because the wheel ships `libp3tinydisplay.dylib` while Panda3D looks for
  `libtinydisplay.dylib`. Windowed Ursina was NOT disproved and probably works — but headless is
  dead, and that decided it: rendering a PNG and looking at it has caught more real defects in this
  project than any test, and Ursina would have cost that entirely. A browser page screenshots
  headlessly via Playwright. Web is also the only path to the containerised-DuckDB goal and later
  Snowflake, so deployment and renderer now point the same way. Shape: the Python CLI emits
  `CityMap` as JSON; a TypeScript app renders it with `OrbitControls`.

- 2026-08-04 — **Per-ring rotation implemented (`ef2ca66`) then reverted (`76c64df`) on Stephen's
  call.** The implementation was correct and well proven — aspect 6.80 → 1.69 on the demo, 34.00 →
  1.28 on a 15-schema chain, non-overlap and containment proven over 330 catalogs × 5 spacing
  candidates, and it constructed the ring-label collision an earlier review could not (labels
  `[0,3,6]` over 3 rings, all ≡ 0 mod n, reachable by advancing depth with a chain *inside* a
  schema). Reverted anyway because it made the map **less viewable**: the demo went from 3/3
  districts and 7/7 lots in the opening frame to 1/3 and 3/7, and a 10-layer chain went from 5/10
  districts visible to **zero** — the bounding box grew 113×5 → 159×139 while the minimum zoom shows
  54×42, so the camera centres on empty land. The strip was legible *because* it was 5 tall. The
  analysis error was mine and is the ninth instance of this branch's pattern: I measured aspect ratio
  and grid size, both of which improved, and neither measures how much of the city you can see. The
  collinear strip stands as a known cosmetic issue that the 3D orbit camera makes moot.

- 2026-08-04 — Phase 1 closed out: **the map now fills its viewport, and the UI stops lying.**
  Three changes, one commit each. (1) The tile pass was bounded by the grid while `app.run_app`
  clears to black, so any part of the map viewport the city did not reach rendered as void —
  measured on the demo catalog as 192 fully-black columns at screen x 832–1023, 129,024 pixels,
  with the map legend floating in them. `draw_tiles` is now bounded by the viewport and paints
  GRASS outside the grid. Centring the map was considered and rejected: it splits the same void
  into two 96px bands rather than removing it. A flat background fill would remove it but seams
  against the alternating grass at the grid border, whereas the `(tx + ty) % 2` parity carries
  straight through an out-of-grid coordinate. No tile moved, so `screen_to_tile` and the
  hover/click paths needed no change — verified by killing four hit-test mutants. The negative
  index guard is load-bearing: `row[-3]` is a live index in Python, so dropping the lower bound
  paints a mirror of the city's far edge into the land west of it while every "no hole" assertion
  still passes; there is a test for exactly that. (2) `HINT_TEXT` advertised `arrows/drag pan`
  while nothing in the package handles `MOUSEMOTION` — drag-to-pan is cut for the 3D renderer —
  and the claim is now pinned to behaviour in both directions instead of to a string. Narrowing
  the hint by 36px silently loosened the status-strip clamp fixtures (the 14-character one went
  from a 37px overflow to 1px, still passing while proving nothing); it was retuned deliberately
  and a new test measures every fixture's unclamped overflow so drift is no longer possible. Two
  stale measurements in those comments were corrected, and the measurement method is now written
  down. (3) README "Reading the map" rewritten against the code rather than against the task
  brief. Three of the brief's own sentences were wrong or overclaimed and were changed: roads are
  streets *inside* districts **plus** lineage paths *between* them (a same-schema dependency gets
  no road, because the district's streets already serve it); arterials are one `POWER_LINE` run
  per **district**, to the footprint cell nearest the plant, not "to every schema area" and
  certainly not the old README's "every table and view"; and "schema areas sit at their lineage
  depth" is only *roughly* true, because a district's ring is the **modal** depth of its objects,
  so a mixed schema sits on a ring not all its objects agree with and a district-to-district edge
  can run inward. A dimmed building now means the object takes part in no lineage at all, with
  the `no lineage detected` fallback stated. The determinism sentence under "Run" was verified
  rather than assumed and left alone: `sim/generator.py` and `sim/layout.py` contain no
  randomness, `generate_city`/`refresh` take no seed, and the only `random` in `sim/` is the
  traffic RNG, which `app.py` seeds from the database name — so even the vehicles repeat.
  The zoom levels are documented as the three that now exist. **Found here, fixed in `38c63c1`:**
  the map legend listed a `water` row while `TileKind.WATER` has never been written by the
  generator since random water was removed in Task 3 — the legend named a tile the map cannot
  show, the same defect class as the `POWER_LINE` phantom that opened this work stream. The row is
  gone and a guard now asserts every legend sprite corresponds to a tile the generator can emit.
  The enum member and sprite mapping were deliberately kept: neither makes a user-visible promise,
  and removing them would delete the water guards that actually fired under mutation.

- 2026-08-04 — Task 5 (app wiring) implemented: **the map is now viewable.** Two framing defects
  fixed, both found by rendering a PNG and looking at it rather than by any test. The camera framed
  the lots only, so on the demo the plant — the database itself — sat eight tiles off the right edge;
  it is now framed with them. And the camera had two zoom levels, 32px and 48px, showing 27 and 18
  tiles across an 864px viewport that has to hold a 42-tile demo grid; a 16px level was added and
  `frame_tiles` now picks the level the content needs before centring. A third fix fell out of
  measuring: the camera was constructed with the *window* size while the map draws into the viewport
  rect, so it fitted and centred against 160 columns of chrome. The `render/camera.py` spec section
  is superseded in place — clamping and drag-pan stay cut, and the measured ceiling of the new zoom
  level is recorded there: the demo fits whole, but a 21-schema warehouse plans an 85x85 grid of
  which only 31% is in frame, and closing that needs a fractional tile size this camera cannot
  express. Also recorded there: the straight-line layout from `layout._angles` returning pi for a
  lone district costs the plant its place in frame past five schemas, which is a layout decision, not
  a camera one, and is now pinned by a fails-when-fixed test.

- 2026-08-04 — Task 3 (generator rewrite) implemented: **the map now changes.** The unconditional
  road grid, the fixed 128 grid and the random water tiles are gone; the generator paints districts,
  streets, lots, the plant, arterials and cross-district lineage roads from `LayoutPlan`, with no
  randomness at all (`seed` dropped from `generate_city` and `refresh`). Three spec passages
  superseded in place, all in the generator section: even/even → **odd/odd** lot cells (the
  contradiction's second copy), the painting order (streets before lots — and the order is in any
  case slack, the load-bearing part being that steps 5-6 write only over `GRASS`), and "plant at
  grid center", which is false whenever the districts sit to one side of the ring origin. The
  lot-neighbour invariant shipped stronger than specified, because the specified form cannot fail.

  Two findings from mutation testing, neither of which any invariant could see. The task brief's
  `_entry_point` pushed one coordinate onto the nearer border *edge* before clamping the other,
  which sent **426 of the 2,435 districts** in the property sweep to a footprint corner instead of
  the wall facing the plant — a longer arterial, and still legal, since a corner is a border cell
  too. Replaced with a plain clamp, which is provably the Manhattan-nearest cell and is what this
  spec said all along; the distance is now asserted against a brute-force scan. Separately, the
  brief snapped that coordinate to an even index as insurance against landing on a lot slot; that
  branch could not fire (border cells of an odd footprint are always even), so it is deleted and the
  premise it guarded — every footprint border cell is a `ROAD` tile — is measured on every catalog in
  the sweep instead.

  13 of 13 mutations killed, each run with `PYTHONDONTWRITEBYTECODE=1` and a `__pycache__` purge,
  because a same-length constant edit reverted inside one second is served from the bytecode cache
  and the verdict is then worthless. Two candidate mutations turned out to be provably equivalent
  rather than killable and were replaced: reordering steps 3 and 6 leaves the map identical, as does
  dropping the snap. 156 tests green.

  Verified by rendering and looking, not only by assertion. Recorded from that: with **one district
  per ring**, `_angles` always returns π, so a purely linear pipeline (the demo catalog, raw →
  staging → marts) lays its districts collinearly due west of the plant. Correct, but it reads as a
  strip rather than a city, and at 32 px per tile a 42-tile strip does not fit one viewport.
  Catalogs with several schemas per ring (38 schemas / 108 objects, and 100 schemas at the
  500-object cap) do read as concentric rings of distinct blocks. Left for Task 5's app wiring: the
  camera frames lots only, so the plant sits off-screen on the demo catalog.

- 2026-08-04 — **Deployment direction, per Stephen: containerized with DuckDB is the near goal;
  Snowflake is deferred.** Recorded in the spec along with the tension it creates — Ursina is a
  desktop GL app needing Xvfb+VNC to containerize, while both deployment goals pull toward the
  Three.js renderer. Stephen's renderer choice stands (Ursina first, web later) and hosting model
  is deliberately undecided beyond "keep it possible". Noted that `scripts/screenshot.py` already
  renders headlessly, so the current pygame code could be containerized to serve stills today.

- 2026-08-04 — Task 2 (district planning) implemented, and **the spec's ring-radius formula was
  wrong.** It bounded Euclidean distance between district centres, but square overlap is a
  Chebyshev condition, so it was short by √2 and produced genuinely overlapping districts —
  including on the spec's own 500-object case, which its containment-only test could not see. The
  spec's suggested remedy (+1 to the circumference term) does not fix it either. Shipped formula
  applies √2 to every clearance, uses the exact chord instead of a small-angle approximation,
  allows a tile for rounding, and folds the plant into the clearance chain. Review verified √2 is
  both sufficient and minimal, and could not break non-overlap, containment or plant clearance
  across ~30,000 independently generated plans. Three spec passages superseded in place: the
  even-cells/odd-cells contradiction (odd/odd is correct), evenly-spaced angular slots (now
  per-district sectors, which reduce exactly to the old rule for equal sizes), and the claim that
  a 500-object catalog settles near the 256 soft target (it reaches 905 — nothing may assume the
  target is met).

- 2026-08-04 — **The Tycoon CLI is Pipeline City's backend, per Stephen.** Answers Phase 2
  prerequisite 2 ("a metadata source beyond the catalog"), which the spec had listed as unsolved
  with only candidate options. Tycoon lives at `~/Projects/localhost-stack` (package
  `database_tycoon`, console script `tycoon`) — not to be confused with the similarly-branded
  `~/Projects/local-project-manager`. Each managed repo carries a `tycoon.yml` (warehouse path,
  `dbt_project_dir`, declared sources, stack composition) and a `.tycoon/metadata.duckdb` whose
  twelve tables were inspected against `~/clients/dogfood`: `dbt_nodes` alone holds per-node
  status, execution time and rows affected across 244 rows, including one real test failure.
  Every Phase 2 visual channel now has a named source, and `dbt_project_dir` reaches a dbt
  manifest whose `depends_on` covers table-materialised models — real lineage for the exact case
  the view-SQL loader cannot see, retiring an option previously judged near-impossible. Recorded
  in the spec as the second `PipelineContext` loader the engine-bones seam was designed for.
  Explicitly does not block Phase 1: layout, generation and signals sit upstream of the context
  source.

- 2026-08-03 — Phase 1 partially implemented on `feature/city-foundation` (Tasks 1 and 4 plus
  the dim-overlay slice of Task 5; Tasks 2, 3 and 6 deliberately parked). New `sim/layout.py`
  computes lineage depth and isolation, `powered` is rebound to `lineage_participation` so
  orphaned objects finally dim, and the dim overlay is cached now that the path is live. Two
  review-driven corrections followed: a catalog with no known edges anywhere now renders lit
  with a `no lineage detected` note rather than as an entirely dark city (a tables-only DuckDB
  file has no lineage at all, since lineage comes only from view SQL), and `compute_depths` was
  reimplemented on Tarjan SCC condensation because the original Kahn-plus-`max_depth + 1`
  design let depth *decrease* across an edge. Per Stephen's ruling, an unfed cycle is a source
  at depth 0. The spec's `compute_depths` description and two edge-case bullets were superseded
  in place to match — one of them had become a backwards visual promise about ring placement.

  A final round closed seven gaps found by **mutation testing** the depth pass, and the lesson is
  worth keeping: validating the implementation against a definitional oracle over ~14,000 graphs
  proved the algorithm correct but could not reveal that the *test suite* was insensitive to a
  wrong one. Two mutations — a faithful shortest-path relaxation, and a recursive Tarjan against
  Python's default recursion limit — each passed the suite 99/99 while being genuinely broken. The
  causes were a symmetric diamond fixture that could not distinguish longest from shortest, and a
  400-node recursion guard sitting under a 1000-frame limit. Both now fail correctly, verified with
  before/after controls. 101 tests green.

  Not done, deliberately: Tasks 2, 3 and 6 of the plan plus Task 5's app wiring. The generator
  still lays the unconditional road grid, so the map is unchanged — this branch is groundwork
  (`sim/layout.py`, the powered signal) rather than a visible improvement.

- 2026-08-03 — Added the Phase 1 implementation plan
  (`superpowers/plans/2026-08-03-city-foundation.md`), 6 TDD tasks derived from
  the city-foundation spec: `sim/layout.py` (depth, isolation, district
  planning), generator rewrite, `LineageParticipation` rebinding, app wiring
  plus dim-overlay cache, and a README correction so "roads are lineage" and
  the power-line description become true. Drag-to-pan and camera clamping are
  recorded as cut. Not yet executed.

- 2026-08-03 — **Two direction decisions per Stephen, both reversing earlier
  rules.** (1) 3D stack chosen: Ursina on Panda3D first, keeping `uv`/pytest
  and the renderer-agnostic `sim/`, then a Three.js port for a shareable web
  build. (2) The engine-bones non-goal "No functional city simulation" is
  superseded — guests, ratings, growth/decay and scoring are wanted. The
  superseded bullets are struck through in place in the engine-bones spec, not
  deleted. Consequences recorded in the foundation spec: derived and simulated
  state hard-separated (`sim/mechanics.py` new, guard-tested in both
  directions), provenance labelling in the inspector made mandatory, and
  determinism redefined from "same file state" to "same catalog, seed and tick
  count" — which makes the README's current determinism claim false on the day
  mechanics ship. Mechanics sequenced last, after layout and the renderer.

- 2026-08-03 — Amended the city-foundation spec with a Phase 2 roadmap (time
  and flow: run status, freshness decay, build propagation replacing random
  traffic, named scenarios), after reviewing PGSimCity as a reference. Records
  three prerequisites: non-float data-function value types, a metadata source
  beyond the DuckDB catalog, and a written channel contract before any sprite
  work. Also records the colour tension — colour currently spent on
  regex-matched zone style, wanted for state that changes.

- 2026-08-03 — **Renderer direction changed to 3D, per Stephen.** Free orbit
  and fly cameras are the intended style; an earlier draft of the Phase 2
  section ruled 3D out and was wrong to. Related framing shift: Stephen is now
  describing this as a game, which moves the north star the engine-bones spec
  set on 2026-07-19 ("a useful control screen rather than a game") and puts its
  "utility over fun" and "legibility beats game balance" rules up for revision.
  Everything upstream of rendering survives; drag-to-pan and camera clamping
  are cut from Phase 1 as throwaway. Stack undecided.

- 2026-08-03 — Added the city-foundation design spec
  (`superpowers/specs/2026-08-03-city-foundation-design.md`), approved by
  Stephen in a brainstorming session. Replaces the unconditional road grid
  with catalog-scaled districts placed in rings by lineage depth, arterials
  and lineage roads that carry meaning, and a `powered` binding that can
  return false. Records three confirmed defects: drag-to-pan documented but
  never implemented, `POWER_LINE` legended but never placed, and the road
  grid laid regardless of catalog size. Sprite work is explicitly out of
  scope — Stephen is drawing his own tiles later. Merged
  `feature/engine-bones` into `main` (fast-forward to `142e4fc`, local only,
  nothing pushed) and branched `feature/city-foundation` from it.

- 2026-07-19 — Legibility pass (L1-L3) complete on `feature/engine-bones`:
  differentiated per-style/per-density building sprites with unpowered
  dimming, Map screen fixes (viewport clip bug, camera centering on lots,
  schema-name label chips, bottom-right legend, hover outline + tooltip,
  status-strip hint text), and a reusable headless screenshot tool
  (`scripts/screenshot.py`). Verified by rendering `demo.duckdb` and reading
  the PNGs directly: buildings clearly differ by zone style (color) and
  density level (size/window count), schema labels sit legibly over their
  areas, the 5-entry legend is readable, and no map pixels bleed below the
  status strip. No theme/render fixes were needed beyond what L1/L2 already
  shipped — the eyeball pass confirmed rather than changed the visuals.
  README gained "Controls" and "Reading the map" sections. 73 tests green,
  ruff clean.

- 2026-07-19 — Implemented the full 12-task engine-bones plan on
  `feature/engine-bones` (14 commits, 62 tests green). Per-task subagent
  reviews plus final whole-branch review: READY TO MERGE, no
  critical/important findings; six deferred minors triaged non-blocking
  (see `.superpowers/sdd/progress.md`). Not merged or pushed — awaiting
  Stephen's call.

- 2026-07-19 — Implementation plan revised to signal-engine model: tasks 5–8
  reworked (data-function registry, visual channels, presentation-only
  traffic/Engine), tasks 4/11/12 adjusted, self-review re-run against the
  amended spec.

- 2026-07-19 — Major correction per Stephen: no functional city simulation.
  Sim core reframed as a data-function → visual-channel signal engine;
  animation is presentation-only. Spec amended; plan revision in progress.

- 2026-07-19 — Added TDD implementation plan
  (`superpowers/plans/2026-07-19-pipeline-city-bones.md`, 12 tasks) and plans
  index.

- 2026-07-19 — Spec amendments per Stephen: data concepts used as-is in all UI
  text (no city euphemisms); reframed purpose as a useful control screen
  rather than a game; added R-to-refresh catalog reload.

- 2026-07-19 — Spec approved by Stephen; amended with RollerCoaster Tycoon
  influence (objects as attractions, RCT-style object/stats pages, deferred
  guest/rating mechanics).
- 2026-07-19 — Created docs bundle; added approved engine-bones design spec
  (`superpowers/specs/2026-07-19-pipeline-city-bones-design.md`).
