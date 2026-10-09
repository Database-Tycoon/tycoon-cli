---
title: Per-release manual QA test plan
description: Reusable manual QA checklist run against the built/published package before (RC) and after (PyPI) each tycoon release
tags: [qa, testing, release-process, checklist]
related: [ci-cd-workflows, metrics]
updated: '2026-09-04'
---

# Per-release manual QA test plan

Run this checklist for every release, twice if possible: once against the release-branch wheel (`uv build` → install the wheel) as the ship gate, and once against the published PyPI package as post-publish verification. Automated CI (unit + offline-e2e + template smoke) already gates the merge; this plan covers what CI can't — the interactive wizard, the browser surfaces (Rill, city), and the real-PyPI install/upgrade path.

Commands below are the real v0.2.0 surface (README CLI reference + `src/tycoon/cli.py`). Update the table when the surface changes.

## Environment setup

```bash
# Fresh, isolated environment — never the dev checkout's venv
uv venv /tmp/qa-tycoon --python 3.12
source /tmp/qa-tycoon/bin/activate
pip install database-tycoon        # post-publish pass
# pip install dist/database_tycoon-<ver>-*.whl   # pre-publish pass
mkdir -p /tmp/qa-run && cd /tmp/qa-run
```

Prereqs: Python >= 3.12, network access (PokéAPI test), a browser for the Rill/city checks. Record: tester, date, version under test, OS/arch.

## Checklist

| # | Surface | Steps | Expected result | Pass/Fail |
|---|---|---|---|---|
| 1 | Install + entrypoint | `pip install database-tycoon` in the fresh venv, then `tycoon --version` and `tycoon -h` | Installs cleanly; version matches the release tag; help renders without traceback or Rich markup artifacts | |
| 2 | Init wizard (interactive) | `mkdir wizard-demo && cd wizard-demo && tycoon init`, walk the prompts accepting defaults (dlt / DuckDB / dbt / Rill) | Wizard completes; `tycoon.yml`, `data/`, dbt project, and `rill/` scaffolded per the chosen answers; re-running warns rather than clobbering | |
| 3 | Init from template (offline path) | `cd /tmp/qa-run && tycoon init --template csv-import --name analytics-demo && cd analytics-demo` | Project created non-interactively with sample CSV + working dbt project | |
| 4 | Sources: catalog + list | `tycoon data sources catalog`, then `tycoon data sources list` and `tycoon data sources list show files` | Catalog table renders; `files` source listed; `show` prints its config | |
| 5 | Sources: run (offline) | `tycoon data sources run files` | dlt run succeeds; `data/raw_files.duckdb` created with rows; summary output sane | |
| 6 | Sources: add + run (live API) | `tycoon data sources add rest_api --base-url https://pokeapi.co/api/v2/ --resources pokemon,berry,type --no-prompt`, then `tycoon data sources run pokeapi` | Source registered in `tycoon.yml`; ingestion pulls the three resources into `data/raw_pokeapi.duckdb` | |
| 7 | dbt build path | `tycoon data transform run` (in analytics-demo), then `tycoon data run-all` | dbt runs green; `data/warehouse.duckdb` populated; `run-all` chains ingest→build without error | |
| 8 | Analyze scaffolding | `tycoon data analyze pokeapi`, then `tycoon data transform run --select 'stg_pokeapi__*'` | Staging models generated for each pokeapi table; selected build passes | |
| 9 | Status / history / query | `tycoon data status`, `tycoon data history`, `tycoon data history show <id>` (an id from the list), `tycoon data db query "select 42"` | Freshness/row counts match the runs just performed; history shows the dlt + dbt runs with per-table/per-node detail; query returns 42 | |
| 10 | Doctor | `tycoon doctor` inside the project, and once in an empty dir | In-project: all checks pass (or only expected warnings), exit 0, no `ERROR` lines. Empty dir: clear "not a tycoon project" style guidance, no traceback | |
| 11 | Rill / analyze --rill | `tycoon data analyze pokeapi --rill`, then `tycoon start --only rill`; open http://localhost:9009; finish with `tycoon stop` | Dashboards generated per table; Rill serves them with data visible; `stop` shuts services down cleanly (port freed) | |
| 12 | tycoon city | `tycoon city` in the project; open the printed URL; Ctrl-C to stop | Browser shows the interactive 3D catalog city reflecting the project's tables; no blank canvas or console errors; server exits cleanly | |
| 13 | Run passthrough | `tycoon run dbt -- ls` (or `tycoon run dbt debug`) | Arguments passed through to the underlying tool from the managed environment; exit code propagated | |
| 14 | Upgrade path from previous version | In a **second** fresh venv: `pip install database-tycoon==<previous>`, `tycoon init --template csv-import --name upgrade-demo`, run steps 5+7; then `pip install --upgrade database-tycoon` (to the RC/new version) and re-run `tycoon doctor`, `tycoon data status`, `tycoon data run-all` in the same project | Old-version project keeps working after upgrade: no config-format errors, metadata/observability DB still readable, pipeline re-runs green | |
| 15 | Uninstall hygiene (optional) | `pip uninstall database-tycoon` | Uninstalls cleanly; `tycoon` no longer on PATH | |

## Recording results

- Any Fail → file a GitHub issue (per project convention: file it, don't fix mid-QA), link it in the release notes, and decide ship/no-ship explicitly.
- Attach the completed table to the release PR description or `docs/releases/v<ver>.md`.
- Known-limitation Fails carried into the release must be listed in the release notes as such.
