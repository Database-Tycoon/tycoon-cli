---
title: Release notes — 0.1.0
description: What ships in database-tycoon-city 0.1.0, both install paths, the known issues, and the two draft PR bodies
tags: [release, packaging, known-issues, pull-requests]
related: [handover, log, city-json-v1, run-json-v1]
updated: '2026-08-09'
---

# database-tycoon-city 0.1.0

First public release candidate. Built and verified locally; nothing is
published, and the tag `v0.1.0` is local only.

## What this is

A read-only view of a DuckDB catalog rendered as a SimCity-style living city.
Schemas become districts, tables and views become buildings, lineage becomes
the street network, the database is the power plant, and row counts drive
building height. Failing dbt tests set buildings on fire. It never writes to
your database.

The claim the visuals rest on: every one of them restates a fact that was
measured — from the catalog, from dbt artifacts, from run history — and
anything that could not be measured is drawn as **unknown**, never as fine and
never as stale. `city.json` is the contract between the Python side and the
renderer; it is specified in [city-json-v1.md](city-json-v1.md) and
[run-json-v1.md](run-json-v1.md), and a golden fixture holds it byte-stable.

Distribution `database-tycoon-city`, module `tycoon_city`. MIT licensed.

## Installing it

### Standalone

The wheel carries the compiled web bundle, so there is nothing to build:

```bash
pip install database-tycoon-city
tycoon-city demo                      # → http://127.0.0.1:8000/?tour=1
tycoon-city path/to/db.duckdb         # → http://127.0.0.1:8000
```

`tycoon-city demo` generates a synthetic tycoon project into a temp directory
and serves it: a week of scheduled runs, a stale mart, a failing test, a build
error, a source past its freshness SLA, a schema that drifted, a
`dbt build --fail-fast` cascade to replay, and a declared semantic model. It is
generated rather than shipped pre-built because every one of those facts is a
*time*. It writes nothing outside `$TMPDIR` and deletes itself on exit.

The path argument takes a plain DuckDB file or a **tycoon project directory**
(one holding `tycoon.yml`, a dbt `target/manifest.json`, and a
`.tycoon/metadata.duckdb` of run history). A plain file gives the catalog,
lineage traced out of view SQL, and row counts; a project adds everything that
needs artifacts. Anything missing is named in the footer's notes popover rather
than silently dropped.

Console scripts: `tycoon-city` (alias `tycoon-city-serve`) and
`tycoon-city-export`. Environment: `DATABASE_TYCOON_DB`,
`DATABASE_TYCOON_WEB_DIST`, `DATABASE_TYCOON_THEME`, `DATABASE_TYCOON_HOST`.

### As an add-on to the Tycoon CLI

The city is an optional extra on the `database-tycoon` CLI distribution:

```bash
pip install "database-tycoon[city]"
cd my-tycoon-project && tycoon city
```

`tycoon city` resolves the project root and hands it to the same server. When
the extra is not installed, `tycoon city` prints one line —
`ERROR city renderer not installed — pip install "database-tycoon[city]"` — and
exits non-zero. The CLI does not import `tycoon_city` at startup, so the
absence costs nothing.

The dependency runs one way only: `database-tycoon[city]` requires
`database-tycoon-city`, and the city never imports `tycoon`.

## Trademarks

dbt is a trademark of dbt Labs, Inc. This project is independent and is not
affiliated with, sponsored by, or endorsed by dbt Labs. It reads the artifacts
dbt produces; the name is used only to say so.

## Known issues

### The CRLF-gated defects

The Citizen Request Framework is out of 1.0. Its surfaces are reachable only
with `?crlf=1`, so no default user meets these, and they are recorded rather
than fixed:

- **`src/tycoon_city/sim/contracts.py` accepts a bool where a schema says
  integer.** `_validate` types integers with `isinstance(value, int)`, and in
  Python `bool` is a subclass of `int`. `complexity` is declared
  `{"type": "integer", "minimum": 1, "maximum": 10}`, and a request carrying
  `"complexity": true` returns `(True, [])` — it passes the type check, and it
  passes the bounds check too, because `True == 1`. The fix is an explicit
  `isinstance(value, bool)` rejection on the integer branch.
- **`_validate` raises `TypeError` instead of reporting a type mismatch.** The
  bounds checks (`if "minimum" in rules and value < rules["minimum"]`) run
  unconditionally, after the type check has already appended an error. A string
  where the schema wants an integer therefore reaches `"abc" < 1` and raises
  `TypeError: '<' not supported between instances of 'str' and 'int'`, blowing
  out of the validator rather than returning `(False, errors)` — the function's
  whole contract is to return the errors, so a caller that trusts the signature
  crashes. The fix is to skip the constraint checks once the type check has
  failed.
- **`web/src/ui/requests.ts` injects request text as HTML.** `render()` builds
  the table with `innerHTML` and interpolates `r.description`, `r.priority` and
  `r.status` unescaped, so markup in `requests.json` executes in the page. The
  fix is `textContent` per cell, or an escape on the way in.
- **The quiet gauge always reads zero.** `problems.ts` computes
  `quiet = measured.filter((o) => o.usage!.runs_seen === 0).length`, but
  `export/measured.py` emits a `usage` block only when the build history is
  non-empty (`if not history: continue`), so `runs_seen` is never 0 for any
  object that has a `usage` at all. The gauge reads `quiet buildings 0/N` on
  every catalog. The two sides disagree about what "measured but unused" means;
  fixing it means deciding that question, which is why it was not done here.

### District labels stack when two bands are adjacent

The district-label overlay places one chip per district with no collision
handling between chips. Two districts whose bands are adjacent on screen can
render their labels on top of one another. It was not reproduced in the demo
city, whose three district chips are well separated horizontally, so the defect
is documented from the code rather than from an observed failure. The
parameterised framing test locks in that labels exist and do not overlap
buildings; it does not assert chip-versus-chip separation.

### Cut on purpose

- **Streets v5 as the default planner.** Still behind `DATABASE_TYCOON_PLANNER=v5`.
  Promoting it is a `city.json` version 2 and a reviewed golden regeneration,
  which does not belong in a first release.
- **The strip-layout defect** remains unfixed, as decided in the handover.
- **Docker Hub publish, CI for this repo, and the block-shape linearity work.**
  All follow the first release rather than block it.

## Verification behind this candidate

- `pytest` — 555 passed, 1 skipped.
- `ruff check` — clean; `ruff format --check` — 134 files already formatted.
- `tsc --noEmit` — clean.
- Playwright — 128 passed.
- The golden `city.json` regenerates unchanged.
- The committed `src/tycoon_city/web_dist/` matches a fresh `npm run build`.
  This is a **release step, not a guard**: nothing in the test suite compares
  the two. `tests/test_web_bundle.py` asserts only that the packaged bundle
  exists, has an `index.html`, and carries no `city.json`. Drift is caught by
  running the step, which was done by hand for this candidate:

  ```bash
  uv run python scripts/sync_web_bundle.py
  git diff --exit-code -- src/tycoon_city/web_dist
  ```
- A clean venv with only the wheel installed serves `/`, the JS asset,
  `/city.json`, `/spritesheet.png` and `/healthz`, all 200, from
  `site-packages/tycoon_city/web_dist`.
- The same venv plus the CLI serves a real tycoon project through
  `tycoon city`; a venv without the city prints the one-line advice and exits 1.

---

## Draft PRs

Neither has been opened. `gh` was not run.

### PR 1 — this repository (`tycoon-city`)

**Base:** `main` **Head:** `feature/city-foundation`

**Title:** `Database Tycoon City 0.1.0 — the first releasable wheel`

**Body:**

> This branch takes the city from "works in a checkout" to "works from a
> wheel", and fixes the defects found on the way.
>
> **The headline change: the wheel carries its own front end.** Before this,
> `pip install database-tycoon-city && tycoon-city demo` told you it had no web
> bundle. The compiled bundle now ships inside the package at
> `src/tycoon_city/web_dist/`, resolved through `importlib.resources`, and a
> checkout's `web/dist` still wins over it so front-end iteration is unaffected.
> `scripts/sync_web_bundle.py` rebuilds and re-syncs it. Keeping the committed
> copy current is a **release step, not automation**: run that script and then
> `git diff --exit-code -- src/tycoon_city/web_dist`. The test suite does not
> compare the two — `tests/test_web_bundle.py` only asserts the packaged bundle
> is there, has an entry point, and carries no dev `city.json`.
>
> **Naming.** The module is `tycoon_city` and the environment variables are
> `DATABASE_TYCOON_*`. The browser verification seam is `window.__tycoonCity`.
> The distribution name `database-tycoon-city` is unchanged. `database_tycoon`
> was tried as the module name and rejected: the CLI's own PyPI distribution
> `database-tycoon` normalises to exactly that string.
>
> **The add-on seam.** `database-tycoon[city]` is an optional extra on the CLI
> side; nothing here imports `tycoon`, and that direction is not to be reversed.
>
> **Fixes.** The loader no longer crashes on freshness-without-manifest. The web
> layering guard is restored. The S7 check is out of the request path. Tour
> progress resumes by stop id rather than by index, so reordering stops no
> longer resumes at the wrong subject. Selection survives an `R` refresh, and a
> refresh mounts one city rather than two. The tour, the run replay and the
> `visit` door all resolve keys against the document currently on screen rather
> than the one the page booted with, so an `R` refresh no longer flies the
> camera to where a building used to stand. The sdist no longer packages
> `web/node_modules`, the agent planning bundle, or the internal working
> documents under `docs/superpowers/` and `docs/agent_tasks/`.
>
> **Trademark notice** added to `README.md` and `THIRD-PARTY.md`.
>
> **Verification.** pytest 555 passed / 1 skipped; ruff clean; `tsc --noEmit`
> clean; Playwright 128 passed; golden `city.json` regenerates unchanged. A
> clean venv with only the built wheel serves `/`, the JS asset, `/city.json`,
> `/spritesheet.png` and `/healthz` at 200 from `site-packages`.
>
> Known issues, including the CRLF-gated defects and the district-label
> stacking, are in `docs/release-notes-0.1.0.md`.

### PR 2 — the CLI repository, branch `feat/city-addon`

**Base:** the `v0.2.0` release branch (**not** `main`) **Head:** `feat/city-addon`

**Title:** `feat(city): serve the catalog as a 3D city behind an optional add-on`

**Body:**

> Adds `tycoon city`, which serves the current tycoon project as an interactive
> 3D city. The renderer is an optional extra rather than a dependency:
>
> ```bash
> pip install "database-tycoon[city]"
> cd my-project && tycoon city
> ```
>
> `[project.optional-dependencies] city = ["database-tycoon-city>=0.1.0"]`. The
> CLI does not import `tycoon_city` at startup — the import happens inside the
> command — so users who never install the extra pay nothing. Without it,
> `tycoon city` prints one line,
> `ERROR city renderer not installed — pip install "database-tycoon[city]"`,
> and exits non-zero.
>
> An extra was chosen over a plugin API deliberately: a plugin API is a
> long-lived interface commitment for exactly one consumer.
>
> Adds `src/tycoon/commands/city.py`, `docs/commands/city.md`, and
> `tests/test_city_command.py` (both the present and the absent path).
>
> **Ordering constraint — this branch's CI cannot go green before the city is
> published.** `uv lock --check` currently fails: `database-tycoon-city>=0.1.0`
> does not resolve, because the distribution is not on PyPI yet, so uv concludes
> `database-tycoon[city]`'s requirements are unsatisfiable. `ci.yml`, `e2e.yml`
> and `nightly-e2e.yml` all run `uv sync --all-extras`, which hits the same
> wall. The required order is:
>
> 1. Publish `database-tycoon-city` 0.1.0 to PyPI.
> 2. Refresh this repository's `uv.lock` so the new distribution resolves.
> 3. Then this PR's CI can pass and the PR can merge.
>
> Do not merge before step 2.
