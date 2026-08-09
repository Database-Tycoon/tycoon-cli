---
title: Public add-on release design
description: Ship the city as database-tycoon-city, a self-contained wheel installable as an optional add-on to the Tycoon CLI, under names that embed no third-party trademark
tags: [release, packaging, naming, trademark, tycoon-cli, add-on]
related: [handover, city-json-v1, run-json-v1]
updated: '2026-08-09'
---

# Public add-on release — design

Approved 2026-08-09. Turns the city into a publicly installable add-on to the
Tycoon CLI. The deliverable for the day is a **release candidate**: everything
green, tagged, built and proven, with nothing pushed and nothing published.

## Goal

`pip install "database-tycoon[city]"` followed by `tycoon city` renders a user's
own Tycoon project as a city, from a wheel that carries everything it needs.

## Decisions

| Surface | Value |
|---|---|
| PyPI distribution | `database-tycoon-city` (unchanged) |
| Python module | `tycoon_city` (was `dbtycoon`) |
| Console scripts | `tycoon-city`, `tycoon-city-serve`, `tycoon-city-export` |
| Environment variables | `DATABASE_TYCOON_*` |
| Public repository | `Database-Tycoon/tycoon-city` |
| Add-on install | `pip install "database-tycoon[city]"` |
| Add-on command | `tycoon city` |
| Web bundle | committed to `src/tycoon_city/web_dist/` |
| `city.json` `objects[].dbt` field | unchanged; no contract version bump |

The module's final name took two tries the same day. `database_tycoon` was
the first choice and was reversed hours later: the Tycoon CLI's own PyPI
distribution is `database-tycoon`, and PyPI name normalization turns hyphens
into underscores, so it normalizes to exactly `database_tycoon` too — `pip
show database-tycoon` would return the CLI while `import database_tycoon`
returned the city, two different products under an identical name. `tycoon_city`
also matches everything else already named: the `tycoon-city` repository and
console scripts, and the `tycoon city` CLI subcommand. See `docs/log.md`,
Task 10 and Task 10b.

No deprecation aliases for the old names. Nothing is published yet, so there
are no installed users to break — which is precisely why the rename happens
before v0.1.0 rather than after.

## Non-goals

Out of scope for this release, each for a stated reason:

- **Streets v5 as the default planner.** That is `city.json` version 2 and a
  reviewed golden regeneration; it does not belong in a first release.
- **The CRLF-gated defects** (`sim/contracts.py` validation, the `ui/requests.ts`
  HTML injection, the contradictory quiet gauge). All sit behind `?crlf=1`, and
  CRLF is out of 1.0, so no public user reaches them. Recorded as known issues.
- **A Tycoon CLI plugin API.** Rejected in favour of an optional extra; see
  "The add-on seam".
- **Docker Hub publish, CI for the new repo, and the block-shape linearity
  work.** All follow the first release rather than blocking it.

## Architecture

Two distributions, two repositories, one direction of dependency:

```
database-tycoon  (CLI, module `tycoon`, repo tycoon-cli)
    └── optional extra [city] ──> database-tycoon-city
                                      (module `tycoon_city`, repo tycoon-city)
```

**The CLI depends on the city, optionally. The city never imports the CLI.**
That preserves the standing decision recorded in `catalog/tycoon_project.py`:
the CLI is pre-1.0 and drifting, builds a cwd-bound singleton at import, and can
`SystemExit` during config load. The city keeps reading `tycoon.yml` off disk
and tolerating drift by construction.

## Execution order

The component numbering below is a table of contents, not a running order. The
work runs in this sequence, and the reason for it is that each step needs the
previous one's guarantee:

1. **Component 4 — clear the gates.** A green suite is the oracle that proves
   the rename.
2. **Component 1 — the naming migration.** One reviewed commit, green before and
   after.
3. **Component 2 — the self-contained wheel.** Writes into
   `src/tycoon_city/web_dist/`, so it must follow the rename.
4. **Component 3 — the add-on seam** in `tycoon-cli`, which imports the renamed
   module and needs a wheel that works.
5. **Component 5 — the release candidate.**

## Component 1 — naming migration

Rename every name of ours that embeds `dbt`. Referential use of dbt stays
everywhere it is factual.

**Renamed:** the `dbtycoon` module, to `tycoon_city` (by way of a same-day
intermediate `database_tycoon` — see the note under "Decisions" above); the
three console scripts, to `tycoon-city`, `tycoon-city-serve` and
`tycoon-city-export`; the six environment variables, to `DATABASE_TYCOON_*`;
`DBT_WEB_PORT` → `DATABASE_TYCOON_WEB_PORT` (13 uses — the sharpest exposure,
since `DBT_*` is dbt's own environment-variable namespace, so a reader would
fairly take it for a dbt variable); the `dbtycoon` Docker image tag in the
README and Dockerfile, to `tycoon-city`.

**Unchanged:** reading dbt artifacts; "works with dbt" in prose; the internal
`_dbt_block` helper; test names naming dbt behaviour; the `demo-tycoon/dbt/`
project directory; and the `objects[].dbt` field in `city.json`, which is named
for what it holds — dbt's own metadata — exactly as a `github` field would hold
GitHub data. Renaming it would force a contract break for no reduction in risk.

Scale: 342 line hits across 76 files. The contract golden contains zero
occurrences, so `city.json` byte-stability is outside the blast radius.

## Component 2 — the self-contained wheel

Today the wheel installs a server with no front end. `README.md:50` names this
honestly as "The honest limit"; it is a known gap, not an oversight, and it is
the single thing that must change for a public `pip install` to mean anything.

Three parts:

1. **`scripts/sync_web_bundle.py`** clean-builds the bundle (removing `web/public`
   first, as the Dockerfile does, so gitignored dev data cannot ride along) and
   copies it into `src/tycoon_city/web_dist/`, which is committed.
   `packages = ["src/tycoon_city"]` already ships non-Python package data,
   so the bundle needs no separate include directive.
2. **`_default_dist()` gains a resolution order:** `--dist` → `$DATABASE_TYCOON_WEB_DIST`
   → the repo's `web/dist` → the packaged `tycoon_city/web_dist` via
   `importlib.resources`. Repo before packaged, so a developer's fresh build
   always wins and a stale committed copy can never shadow it mid-iteration.
3. **A staleness guard for release:** rebuild, then
   `git diff --exit-code src/tycoon_city/web_dist/`. A dirty tree means the
   committed bundle was stale, and the release stops. Same shape as
   `scripts/update_contract_golden.py` guarding the contract.

Bundle size is 736K across 4 files, which is what makes committing it viable.

## Component 3 — the add-on seam

In the `tycoon-cli` repository:

- `[project.optional-dependencies] city = ["database-tycoon-city>=0.1.0"]`.
- `src/tycoon/commands/city.py`: resolve the project root the way sibling
  commands do, then serve the city against it.
- **The `tycoon_city` import lives inside the function body, never at module
  scope.** The CLI's startup must not depend on the city being installed, and a
  missing package must produce a one-line "run `pip install "database-tycoon[city]"`"
  with a non-zero exit, not a traceback.
- Registered in `cli.py` alongside the existing static imports.

No plugin API, no new public surface on a 0.1.x CLI, and trivially revertible.

**Verify before writing:** that the command can resolve a project root without
touching the CLI's cwd-bound config singleton. If it cannot, the command shells
out to `tycoon-city-serve` as a subprocess and nothing else in this design
changes.

## Component 4 — clearing the gates

From the 2026-08-09 review, in this order:

1. `catalog/loader.py` — `_enrich_freshness` dereferences `index.key_of` when
   `index` is `None`, killing the whole load path for a project with
   `sources.json` but no manifest. Also its `E501` and formatting.
2. `tests/test_web_layering.py` — the `main.ts` split moved the `mechanics`
   import into `boot/setup.ts`, which is not on the guard's allowlist.
3. `git add` the seven untracked load-bearing files under `web/src/`.
4. Delete `docs/project_blueprint.md` — a leaked model transcript whose content
   contradicts two closed decisions.
5. `sim/town_streets.py` — move the S7 `ValueError` out of the request path.
6. The two e2e regressions: tour-stop persistence, and selection lost across `R`.
7. `README.md` — resolve the "v5 ships today" contradiction.

Gate: pytest, Playwright, `ruff check`, `ruff format --check`, and `tsc --noEmit`
all green, with Playwright run to completion rather than timed out.

## Component 5 — the release candidate

Commit in reviewed slices; tag `v0.1.0`; build wheel and sdist. The proof is
installing the built wheel into a clean virtualenv alongside the CLI and running
`tycoon city` against a real project.

TestPyPI is **not** in scope: uploading there is an outbound publish and
permanently consumes a version. The clean-venv install proves the same property
with nothing published. If TestPyPI is wanted later it is a separate, explicitly
approved step.

Day's end state: a tagged green branch, verified artifacts, a draft PR for each
repository, and release notes. Nothing pushed, nothing published.

## Trademark posture

dbt is a trademark of dbt Labs, Inc. The posture is: our own names carry no
`dbt` substring; referential use stays because the integration is real and must
be describable; and `THIRD-PARTY.md` and the README carry an explicit notice —
*"dbt is a trademark of dbt Labs, Inc. This project is independent and not
affiliated with or endorsed by dbt Labs."*

This is naming hygiene, not legal advice. A short conversation with counsel is
worth having before the repository goes public.

## Testing strategy

- **The rename is validated by the existing suite**, which is why it happens
  after the gate fixes: a green suite before and after is the proof.
- **Two new guard tests** for the bundle, mirroring the `test_demo_project.py`
  pattern already trusted here: the bundle resolves through
  `importlib.resources`, and it contains no `city.json` (dev data that would
  otherwise bake a stale demo catalog into the package).
- **Two new tests in `tycoon-cli`**: the `city` command appears in `--help`, and
  the not-installed path gives the friendly message with a non-zero exit.
- Every new guard is mutation-tested per the repo rules, with
  `PYTHONDONTWRITEBYTECODE=1` and `__pycache__` cleared.

## Risks and the cut line

The gate fixes are the uncertain part; the two e2e regressions are unfamiliar
code and could each take an hour.

**If time runs short, cut the two e2e regressions — not the rename or the
bundle.** A wheel that installs and starts under the right name is a coherent
release candidate with documented known issues. A green suite that installs
under a rejected name is not, and the name is the one thing that becomes
permanently expensive the moment it is published.
