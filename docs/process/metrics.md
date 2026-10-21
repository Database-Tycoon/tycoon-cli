---
title: Project metrics proposal
description: Monthly metrics for tycoon-cli across adoption, quality, and community, with the definition, source, collection method, and target for each
tags: [metrics, qa, community, adoption]
related: [ci-cd-workflows, qa-test-plan]
updated: '2026-10-21'
---

# Project metrics proposal (monthly)

Review cadence: first week of each month, alongside the board reality check against the GitHub Project. "Scriptable" metrics are candidates for a single collection script (or a dlt source into the dogfood pipeline) later; start manual, automate once the numbers are looked at three months running.

## Adoption

| Metric | Definition | Source | Collection | Suggested target |
|---|---|---|---|---|
| PyPI downloads | `database-tycoon` downloads/month, excluding mirrors | pypistats.org | Scriptable: `pypistats recent database-tycoon` / JSON API | Month-over-month growth; flag any month flat or down 2x running |
| GitHub stars | Cumulative stars on `Database-Tycoon/tycoon-cli` | GitHub | Scriptable: `gh api repos/Database-Tycoon/tycoon-cli --jq .stargazers_count` | +10/month while pre-1.0 |
| Repo traffic (clones/views) | Unique cloners + unique visitors, 14-day window | GitHub Insights, Traffic tab | Scriptable: `gh api .../traffic/clones` (needs push access; 14-day retention, so it must be captured at least fortnightly) | Trend only; no absolute target yet |

## Quality

| Metric | Definition | Source | Collection | Suggested target |
|---|---|---|---|---|
| Test count trend | Tests collected on the release branch | pytest | Scriptable: `uv run pytest --collect-only -q \| tail -1` (baseline: 1,551 on `v0.2.3`, 2026-10-21) | Rises with every feature release; never drops without an explanatory note |
| CI pass rate | % of `ci.yml` runs on PRs concluding success (cancelled excluded), trailing 30 days | GitHub Actions | Scriptable: `gh run list --workflow ci.yml --json conclusion` | ≥ 90%; nightly-e2e tracked separately (upstream flake excluded) |
| Coverage | `--cov` figure from the latest main CI run vs the `fail_under` floor | CI coverage report | Manual read from the run log (scriptable via the coverage-xml artifact) | Floor (73 since #256) ratcheted up each quarter toward the actual baseline |
| Open bug count | Open issues labeled `bug` | GitHub | Scriptable: `gh issue list -l bug --state open --json number --jq length` | ≤ 5 open; zero older than one release cycle |

## Community

| Metric | Definition | Source | Collection | Suggested target |
|---|---|---|---|---|
| Issues opened / closed | Count per month, and the ratio | GitHub | Scriptable: `gh issue list` with `--search "created:>=..."` / `closed:` filters | Closed ≥ opened (backlog not growing) |
| External contributors | Unique PR authors per month outside the maintainer team (`db-tycoon-stephen`, `JesuFemi-O`, `Mercy2codesgit`) | GitHub PRs | Scriptable: `gh pr list --state merged --json author` + filter | First external PR in 2026; then ≥ 1/quarter |
| Discussions engagement | New GitHub Discussions threads + non-maintainer replies | GitHub Discussions | Manual skim (API scriptable later) | ≥ 1 active thread/month once Discussions launch |

## Notes

- **Don't over-collect.** Nine numbers, one page, once a month. If a metric goes three months unused, drop it.
- Repo **traffic data expires after 14 days**, so that one metric needs a recurring capture (good first candidate for a tiny scheduled script writing to the dogfood MotherDuck warehouse, which would also make these dashboardable in the CEO Notion views).
- CI pass rate should be read with G1 from the CI/CD docs page in mind: `e2e.yml` has never run, so its rate is undefined until it's exercised.
