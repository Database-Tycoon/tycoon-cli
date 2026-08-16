---
name: contributing-changes
description: Use when preparing a change for the tycoon-cli repo — choosing which branch to target, opening a PR, updating the changelog, or when CI behaves differently than expected because workflow config differs between main and the release branch.
license: MIT
compatibility: tycoon-cli repository checkout with uv
metadata:
  author: database-tycoon
  tier: contributors
---

# Contributing changes

## Branch model — never target main

Each release cycle lives on its own version branch (e.g. `v0.1.12`). All
feature and fix PRs target the **active release branch**, never `main` —
`main` only advances when a finished release branch merges into it, so it
always reflects the latest published version.

Consequences:

- Branch from the active release branch, PR back into it. If you can't tell
  which branch is active, it's the highest open `v0.1.*` branch; ask in an
  issue if unsure.
- CI workflow config and tool pins live on the release branch and may differ
  from `main` — diagnose PR check failures against the release branch's
  `.github/workflows/`, not `main`'s.
- A regression test should fail on the release branch and pass on yours.

## Change checklist

1. Open an issue first for anything non-trivial — design discussion happens
   before code.
2. Branch from the active release branch.
3. Tests: new behavior needs a test; bug fixes need a regression test. Use
   `conftest.py` fixtures before hand-rolling new ones. CLI-surface bugs need
   subprocess-layer tests (see the testing-cli-changes skill).
4. Update `CHANGELOG.md` under `[Unreleased]` (Added / Changed / Fixed /
   Removed / Deprecated / Security).
5. User-visible change → update `README.md` too.
6. Before pushing: `uv run pytest -q && uvx ruff check src tests`.

## Code conventions that reviews enforce

- No comments describing *what* code does — only non-obvious *why*.
- No unused imports, half-finished implementations, or backwards-compat
  shims (pre-1.0: delete aggressively).
- Type hints everywhere; `ruff` + `ty` clean.
- One logical change per commit, imperative mood, body explains why.
