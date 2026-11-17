---
name: contributing-changes
description: Use when preparing a change for the tycoon-cli repo: choosing which branch to target, opening a PR, updating the changelog, or when CI behaves differently than expected because workflow config differs between main and the release branch.
license: MIT
compatibility: tycoon-cli repository checkout with uv
metadata:
  author: database-tycoon
  tier: contributors
---

# Contributing changes

CONTRIBUTING.md is the authority for PR size, titles, issue links, the
Mental model section and the release process. This skill covers what an agent
most often gets wrong, and points at the section that settles each one.

## Which branch to target

Target the **active release branch**, never `main`. `main` only advances when a
finished release branch merges into it. CONTRIBUTING.md, "Release process"
and "Merging into the release branch" say how a branch
becomes active and how it merges.

Do not guess from branch names. Old release branches are never deleted, so the
set of open version branches includes abandoned ones. To find the active
branch, read the base of the most recently merged PR, or ask in the issue.

Consequences:

- CI workflow config and tool pins live on the release branch and may differ
  from `main`. Diagnose a PR's check failures against the release branch's
  `.github/workflows/`, not `main`'s.
- A regression test should fail on the release branch and pass on yours.

## Change checklist

1. Open an issue first for anything non-trivial (CONTRIBUTING.md, "Break up
   large issues"), and set its milestone to the active release
   (`gh issue edit <N> --milestone <release>`), so the milestone's open count
   reflects the work left.
2. Before writing code, list the files the change will touch, including tests,
   `CHANGELOG.md` and docs. Over 8 counted files means several PRs, and an
   issue that needs several PRs gets sub-issues, one per PR (CONTRIBUTING.md,
   "Break up large issues").
3. Branch from the active release branch.
4. Tests: new behaviour needs a test, and a bug fix needs a regression test. For
   a CLI-surface bug, use the subprocess layer (testing-cli-changes skill).
5. Update `CHANGELOG.md` under `[Unreleased]` in the section for the change's
   type.
6. A user-visible change also updates `README.md` and the relevant `docs/` page.
7. Before pushing, run the gates CI runs, with `uv run`:
   `uv run pytest -q`, `uv run ruff check src tests`,
   `uv run ruff format --check src tests`. Do not use `uvx ruff`: it resolves
   the latest release, not the version CI pins (CONTRIBUTING.md, "What CI gates on").
8. Open the PR as a draft, with the template body and a Mental model section.
9. After the PR merges, close its issue by hand. Closing keywords such as
   `Closes #N` only fire on merges into the default branch (`main`), and PRs
   here merge into the release branch (CONTRIBUTING.md, "Title your PR consistently", under
   "Closing GitHub issues").

## Stacking PRs

Stack PRs only when a later PR needs code from an earlier one. Independent
PRs each target the release branch. A stack merges from the bottom up
(CONTRIBUTING.md, "Merging into the release branch"). Don't put a PR in a
stack if it might merge on its own, out of that order: `gh stack` then refuses
to unstack or retarget the stack, and the layers above have to be relinked as
new PRs.

## Code conventions

CONTRIBUTING.md, "Code conventions", is authoritative. The rules
reviews repeat most: no comments that describe what code does (only a
non-obvious why), no unused imports or half-finished implementations, no
backwards-compatibility shims before 1.0, and one logical change per commit.
