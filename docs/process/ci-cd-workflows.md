---
title: CI/CD GitHub Actions workflows
description: What each of the seven GitHub Actions workflows does, why it exists, its current run status, and the gaps worth closing
tags: [ci-cd, github-actions, release-process, testing]
related: [qa-test-plan, metrics]
updated: '2026-10-21'
---

# CI/CD GitHub Actions workflows

The repo (`Database-Tycoon/tycoon-cli`) carries seven workflows. **Workflow YAML lives on the active release branch, not `main`.** `main` lags a release cycle, so always read and diagnose CI from the release branch. Run status below is from `gh run list` on 2026-10-21.

## 1. `ci.yml`: CI (the merge gate)

**Trigger:** every pull request, and every push to `main`. Concurrency-grouped per ref with cancel-in-progress, so a force-push cancels the stale run.

**Purpose:** the single quality gate for merging. Anything that would break a user install, the test suite, the docs site, or the vendored web renderer blocks the PR here instead of surfacing at release time. Network-dependent tests are deliberately excluded (they live in `e2e.yml` and `nightly-e2e.yml`).

**Jobs:**

| Job | What it gates |
|---|---|
| `test` (py3.12 + py3.13 matrix, fail-fast off) | Full pytest suite including the `offline_e2e` marker (the csv-import full-pipeline run, a real integration with no network). Enforces the coverage floor from `pyproject.toml` (`fail_under = 73`, re-baselined by #256 when the city renderer joined the run). Uploads `coverage.xml`. |
| `lint` | `ruff check` and `ruff format --check` on `src` and `tests`, version-pinned via the dev dependency group. `scripts/` is outside this gate (#426). |
| `secret-scan` | gitleaks over the **full git history** (fetch-depth 0). Runs a checksum-verified binary directly rather than the marketplace action, to keep the supply chain narrow. |
| `build` | `uv build` (wheel + sdist), then installs the built wheel into a fresh venv and smoke-runs `tycoon --version` and `tycoon -h`. Catches packaging regressions (console-script wiring, manifest typos) before a tag. |
| `web` | The `tycoon city` renderer that ships inside the wheel: `tsc --noEmit`, production build, **bundle-freshness check** (the committed `src/tycoon_city/web_dist` must byte-match a rebuild of `web/`, since a stale bundle ships unreviewed UI), then Playwright e2e against a real `tycoon-city-export` of the demo fixture. |
| `docs` | `mkdocs build --strict`, then `scripts/check_docs_publishable.py`. Strict catches broken links and nav targets, and a page in none of `nav`, `draft_docs`, `exclude_docs` or `not_in_nav`. The script catches the two cases strict reports only at INFO: an internal page reaching the build, and a published page linking to a withheld one. See the Documentation section of `CONTRIBUTING.md`. |
| `template-smoke` (csv-import + nyc-transit matrix) | `tycoon init --template <t>` into a fresh dir, then `tycoon doctor`, asserting no `ERROR` lines (doctor always exits 0, so the grep is the real gate). |

**Status:** passing. Every PR run on 2026-10-20 and 2026-10-21 succeeded. Typical duration 2 to 5 minutes; the `web` job is the long pole.

## 2. `pr-compliance.yml`: PR size and title checks

**Trigger:** pull request opened, edited, synchronized or reopened.

**Purpose:** the two PR conventions from `CONTRIBUTING.md`, checked by machine and reported as a sticky comment on the PR: the `size` job counts changed files against the eight-file cap (`.github/pr-size.yml`), and the `title` job checks the `type(gh-N): ...` format (`.github/pr-title.yml`). Both run in `mode: warn` today, so they comment rather than fail. Each job runs the check script and its config from the PR's **base** ref, fetched into a `trusted/` directory, so a PR cannot loosen the rule it is being checked against.

**Status:** passing on every PR. Flipping either check to `fail` is a one-line config change once the open PRs are within the cap.

## 3. `docs.yml`: Deploy docs (GitHub Pages)

**Trigger:** push to `main`, plus `workflow_dispatch`. The deploy job additionally requires `github.ref == 'refs/heads/main'`, so a dispatch aimed at another ref builds nothing.

**Purpose:** publish the MkDocs site to GitHub Pages at `https://database-tycoon.github.io/tycoon-cli/`. The job runs `mkdocs build --strict` and `scripts/check_docs_publishable.py` itself before uploading, because nothing guarantees that `ci.yml` ran on the commit being deployed. Permissions are zero at the workflow level; the deploy job holds `contents: read`, `pages: write` and `id-token: write`. Concurrency group `pages` without cancel-in-progress, since a cancelled Pages deploy can leave the site half-applied. Pages is set to the "GitHub Actions" build type (switched 2026-10-11).

**Status:** no runs yet. The workflow landed on the `v0.2.3` branch (#415) and reaches `main` with the v0.2.3 release, which is the first publish. Verify the site after that merge.

## 4. `publish.yml`: Publish to PyPI (the release train)

**Trigger:** push of a `v*` tag. Zero default permissions; each job requests exactly what it needs.

**Purpose:** turn a tag into a PyPI release, with a fail-fast coherence gate so a half-prepared release never ships. Publishing uses PyPI **Trusted Publishing** (OIDC, `id-token: write`), no API-token secrets, via the GitHub environments `testpypi` and `pypi`.

**Jobs (sequential):**

1. `preflight`: the tag, the `pyproject.toml` version, `src/tycoon/__init__.py` `__version__`, a **dated** `CHANGELOG.md` entry, and `docs/releases/v<ver>.md` (no `_Released: TBD_`) must all agree. This encodes the release checklist mechanically.
2. `build`: `uv build`, artifacts uploaded. The build backend is pinned (`hatchling==1.32.4`) so the wheel metadata version cannot float between releases.
3. `publish-testpypi`: publishes to TestPyPI first (environment `testpypi`).
4. `publish-pypi`: only after TestPyPI succeeds, publishes to PyPI (environment `pypi`).

**Status:** v0.2.2 (2026-10-09), v0.2.1 (2026-09-17) and the v0.2.0 re-tag (2026-08-28) all published clean. The run before the re-tag **failed**: the v0.2.0 wheel carried Metadata-Version 2.5, which the publisher rejected even though CI's build job was green (fixed in #210, tag re-pushed). That failure is why the backend is pinned, and the motivating example for gap G2 below.

## 5. `jira-sync.yml`: one-way GitHub to Jira sync (retired)

**Trigger:** `issues: [opened, closed, reopened]`.

**Purpose, historically:** mirror issue lifecycle onto the PTC Jira board. The board was retired on 2026-10-09 (Discussion #353); tracking is the GitHub Project "Tycoon CLI" and milestones only.

**Status:** every run is a no-op bailout. The repo has no Actions secrets, so the workflow logs `JIRA_EMAIL or JIRA_API_TOKEN secret not set; skipping sync.` and exits 0. It still fires on every issue event (five runs on 2026-10-20 alone). Removing the workflow and the `PTC-` key handling is #351, scheduled for v0.2.3. Do not set the secrets.

## 6. `nightly-e2e.yml`: Nightly e2e (live APIs, no credentials)

**Trigger:** cron `0 8 * * *` (04:00 ET, a low-traffic window for the NYC Open Data and NOAA APIs), plus `workflow_dispatch` for post-fix confirmation.

**Purpose:** upstream API drift should surface as an overnight issue, not as a failure during a release. Runs only the **no-credential** live subset:

- `tests/test_templates_e2e.py::test_nyc_transit_e2e` (`pytest -m e2e`)
- online recipe doctests (`--run-online`): README and docs code blocks marked `mode=online`, catching contract drift against PokeAPI, NOAA and the like.

**On failure it files a GitHub issue itself** (job-level `issues: write`): dated title, link to the failed run, embedded triage steps (upstream flake: close and let the next nightly clear it; tycoon regression: fix via PR). Deduped by searching for an open `nightly-e2e` issue before creating.

**Status:** green every night through 2026-10-21, about a minute each.

## 7. `e2e.yml`: End-to-end template tests (manual, credentialed)

**Trigger:** `workflow_dispatch` only, deliberately no cron, because these hit live APIs with credentials and would burn CI minutes unattended.

**Purpose:** run the full `pytest -m e2e` suite (all live-API template tests, including those needing `E2E_GITHUB_TOKEN`) on demand before a release or after touching an ingestion path.

**Status:** **zero runs, ever.** `gh run list` returns nothing, and the repo has no Actions secrets, so `E2E_GITHUB_TOKEN` does not exist. See gap G1. The MotherDuck roadmap (#429) proposes a token-gated job in this workflow (#431), which would give it a reason to run.

## Gaps

- **G1: `e2e.yml` has never run.** The credentialed live-API suite it exists for has no CI baseline. Either run it once per release cycle (add it to the release checklist) or fold the no-credential parts into `nightly-e2e.yml` and delete it. #431 may settle this.
- **G2: no "publishable" check before tag time.** The build backend is pinned now, which removes the cause of the v0.2.0 failure, but nothing in `ci.yml`'s `build` job or `publish.yml`'s `preflight` validates the artifact the way the publisher will (a `twine check` equivalent). Add one.
- **G3: CI is ubuntu-only, Python 3.12 and 3.13 only.** For a local-first CLI aimed at analyst laptops, macOS (the primary user platform, including Apple Silicon) and Windows are never exercised. At minimum add a macOS leg to the `build` and `template-smoke` jobs.
- **G4: the coverage floor should keep ratcheting.** `fail_under` is 73 since #256; the suite collects 1,551 tests on `v0.2.3`. Raise the floor toward the actual figure each quarter so regressions cannot hide in the headroom. The comment in `ci.yml` still says 60; fix it with the next ratchet.
- **G5: `jira-sync.yml` still fires.** Retired board, dormant workflow, a run per issue event. #351 removes it.
- **G6: `scripts/` is outside the lint gate.** The docs guard and the PR-compliance checks live there and are CI-critical (#426).
- **G7: no dependency-vulnerability scanning.** gitleaks covers committed secrets, but nothing runs `pip-audit` or Dependabot-style checks against the pinned dependency tree.
