---
title: CI/CD GitHub Actions workflows
description: What each of the five GitHub Actions workflows does, why it exists, its current run status, and the gaps worth closing
tags: [ci-cd, github-actions, release-process, testing]
related: [qa-test-plan, metrics]
updated: '2026-09-04'
---

# CI/CD GitHub Actions workflows

The repo (`Database-Tycoon/tycoon-cli`) carries five workflows. **Workflow YAML lives on the active release branch, not `main`** — `main` lags a release cycle, so always read/diagnose CI from the release branch (documented as of `probe/v0.2.1-content`). Run status below is from `gh run list` on 2026-09-04.

## 1. `ci.yml` — CI (the merge gate)

**Trigger:** every pull request, and every push to `main`. Concurrency-grouped per ref with cancel-in-progress, so a force-push cancels the stale run.

**Purpose:** the single quality gate for merging. Anything that would break a user install, the test suite, the docs site, or the vendored web renderer blocks the PR here instead of surfacing at release time. Network-dependent tests are deliberately excluded (they live in `e2e.yml` / `nightly-e2e.yml`).

**Jobs:**

| Job | What it gates |
|---|---|
| `test` (py3.12 + py3.13 matrix, fail-fast off) | Full pytest suite incl. the `offline_e2e` marker (csv-import full-pipeline run — real integration with no network). Enforces the coverage floor from `pyproject.toml` (`fail_under`, pinned at 60% since v0.1.2). Uploads `coverage.xml`. |
| `lint` | `ruff check` + `ruff format --check` on `src` and `tests`, version-pinned via the dev dependency group. |
| `secret-scan` | gitleaks over the **full git history** (fetch-depth 0). Runs a checksum-verified binary directly rather than the marketplace action, to keep the supply chain narrow. |
| `build` | `uv build` (wheel + sdist), then installs the built wheel into a fresh venv and smoke-runs `tycoon --version` / `tycoon -h`. Catches packaging regressions (console-script wiring, manifest typos) before a tag. |
| `web` | The `tycoon city` renderer that ships inside the wheel: `tsc --noEmit` typecheck, production build, **bundle-freshness check** (committed `src/tycoon_city/web_dist` must byte-match a rebuild of `web/` — a stale bundle ships unreviewed UI), then Playwright e2e against a real `tycoon-city-export` of the demo fixture. |
| `docs` | `mkdocs build --strict` — broken internal links and nav targets block the merge. |
| `template-smoke` (csv-import + nyc-transit matrix) | `tycoon init --template <t>` into a fresh dir, then `tycoon doctor`, asserting no `ERROR` lines (doctor currently always exits 0, so the grep is the real gate). |

**Status:** passing. Last 5 runs: 4 success, 1 cancelled (concurrency supersede). Typical duration ~2 min.

## 2. `publish.yml` — Publish to PyPI (the release train)

**Trigger:** push of a `v*` tag. Zero default permissions; each job requests exactly what it needs.

**Purpose:** turn a tag into a PyPI release, with a fail-fast coherence gate so a half-prepared release never ships. Publishing uses PyPI **Trusted Publishing** (OIDC, `id-token: write`) — no API-token secrets — via GitHub environments `testpypi` and `pypi`.

**Jobs (sequential):**
1. `preflight` — the tag, `pyproject.toml` version, `src/tycoon/__init__.py` `__version__`, a **dated** `CHANGELOG.md` entry, and `docs/releases/v<ver>.md` (no `_Released: TBD_`) must all agree. This encodes the release checklist mechanically.
2. `build` — `uv build`, artifacts uploaded.
3. `publish-testpypi` — publishes to TestPyPI first (environment `testpypi`).
4. `publish-pypi` — only after TestPyPI succeeds, publishes to PyPI (environment `pypi`).

**Status:** last run (v0.2.0 re-tag, 2026-08-28) success. The run immediately before it **failed**: the v0.2.0 wheel carried Metadata-Version 2.5, which the publisher rejected even though CI's build job was green (fixed in #210, tag re-pushed). That failure is the motivating example for gap G2 below. v0.1.9–v0.1.11 all published clean.

## 3. `jira-sync.yml` — one-way GitHub → Jira lifecycle sync

**Trigger:** `issues: [opened, closed, reopened]`.

**Purpose:** keep the PTC Jira board honest without manual mirroring:
- **opened** with no `PTC-NN` reference → posts a single marker-deduped reminder comment asking the maintainer to mirror it on the roadmap.
- **closed** → finds every `PTC-NN` in the issue body/comments and transitions those Jira issues to **Done** via the Jira REST API.
- **reopened** → transitions them back to **To Do**.

Implementation is an inline Python script (stdlib urllib + `gh api`), re-fetching the issue body/comments fresh rather than trusting YAML interpolation. Auth via `JIRA_EMAIL` / `JIRA_API_TOKEN` repo secrets; the workflow degrades to a warning-and-skip if they're unset. Project key and base URL are hardcoded (repo-specific by design).

**Status:** dormant — it has never synced anything. The recent "successful" runs (five on 2026-08-30, 6–8s each) are all no-op bailouts: the run logs show `##[warning]JIRA_EMAIL or JIRA_API_TOKEN secret not set; skipping sync.` (verified in run 33331378534 on 2026-09-04), and `gh secret list` confirms the repo has no Actions secrets. A green conclusion here means only that the bailout path exited 0. Setting the two secrets turns the sync on with no code change — tracked as PTC-93.

## 4. `nightly-e2e.yml` — Nightly e2e (live APIs, no credentials)

**Trigger:** cron `0 8 * * *` (04:00 ET, a low-traffic window for the NYC Open Data / NOAA APIs), plus `workflow_dispatch` for post-fix confirmation.

**Purpose:** upstream API drift should surface as an overnight issue, not as a failure during a release. Runs only the **no-credential** live subset:
- `tests/test_templates_e2e.py::test_nyc_transit_e2e` (`pytest -m e2e`)
- online recipe doctests (`--run-online`) — README/docs code blocks marked `mode=online`, catching contract drift against PokéAPI, NOAA, etc.

**On failure it files a GitHub issue itself** (job-level `issues: write`): dated title, link to the failed run, embedded triage steps (upstream flake → close and let the next nightly clear it; tycoon regression → fix via PR). Deduped by searching for an open `nightly-e2e` issue before creating.

**Status:** green every night. Last 5 runs (2026-08-31 → 2026-09-04) all scheduled successes, ~50–60s each.

## 5. `e2e.yml` — End-to-end template tests (manual, credentialed)

**Trigger:** `workflow_dispatch` only — deliberately no cron, because these hit live APIs with credentials and would burn CI minutes unattended.

**Purpose:** run the full `pytest -m e2e` suite (all live-API template tests, including those needing `E2E_GITHUB_TOKEN`) on demand before a release or after touching an ingestion path.

**Status:** **zero runs, ever.** `gh run list` returns nothing. Whether the `E2E_GITHUB_TOKEN` secret even exists is unverified, and the credentialed e2e path has never executed in CI. See gap G1.

## Gaps

- **G1 — `e2e.yml` has never run.** The credentialed live-API suite it exists for has no CI baseline; the `E2E_GITHUB_TOKEN` wiring is untested. Either run it once per release cycle (add it to the release checklist / release-prep agent) or fold the no-credential parts into `nightly-e2e.yml` and delete it.
- **G2 — no "publishable" check before tag time.** The v0.2.0 publish failure (Metadata-Version 2.5 rejected by PyPI while CI was green) showed that `uv build` succeeding ≠ the artifact being acceptable to the publisher. Add a metadata/`twine check`-equivalent validation to `ci.yml`'s `build` job and/or `publish.yml`'s `preflight`, and pin the build backend.
- **G3 — CI is ubuntu-only, Python 3.12/3.13 only.** For a local-first CLI aimed at analyst laptops, macOS (the primary user platform, incl. Apple Silicon) and ideally Windows are never exercised. At minimum add a macOS leg to the `build`/install-smoke and `template-smoke` jobs.
- **G4 — stale coverage floor.** `fail_under` has sat at 60% since v0.1.2; the suite is now ~1,296 tests. Ratchet the floor toward the actual baseline so regressions can't hide in the headroom.
- **G5 — jira-sync is issues-only and silent on failure.** PR events don't sync, transition failures only print to the run log (nobody is notified), and there's no reverse (Jira → GitHub) direction. Acceptable for now, but worth a `::error`/issue-on-failure once the board is load-bearing.
- **G6 — docs are built strict but never deployed.** No workflow publishes the MkDocs site (e.g. `gh-pages` on tag); the strict build gates link rot but users can't read the result.
- **G7 — no dependency-vulnerability scanning.** gitleaks covers committed secrets, but nothing runs `pip-audit`/Dependabot-style checks against the pinned dependency tree.
