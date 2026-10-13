---
name: cutting-a-release
description: Use when cutting or publishing a tycoon release — opening the next version branch, finalizing CHANGELOG.md and docs/releases/, merging the release branch to main, pushing the version tag, or troubleshooting the PyPI trusted-publishing workflow.
license: MIT
compatibility: tycoon-cli repository, maintainer permissions on Database-Tycoon/tycoon-cli
metadata:
  author: database-tycoon
  tier: maintainers
---

# Cutting a release

The cycle, in order:

1. **Open the branch.** Cut `v<next>` off `main`. It becomes the active
   release branch; announce it so PRs target it. Nothing PRs into `main`
   directly.
2. **Land the cycle's PRs** into the release branch.
3. **Finalize the record** on the branch, in the same commit series:
   - `CHANGELOG.md`: convert `[Unreleased]` into the versioned section.
   - `docs/releases/v<ver>.md`: the long-form narrative. CHANGELOG and the
     release doc must stay in sync — CI and readers both use them.
   - Regenerate Rich-output snapshots if user-facing strings changed
     (`uv run pytest --snapshot-update tests/test_snapshots.py`, review the
     diff).
4. **Merge to main** via PR (release branch → `main`).
5. **Tag.** Branch and tag share a name, so use fully-qualified refs:

   ```bash
   git tag v<ver> && git push origin refs/tags/v<ver>
   ```

   Pushing `v<ver>` unqualified is ambiguous between the branch and the tag —
   this has bitten before; `docs/publishing-to-pypi.md` has the details.
6. **Publish happens automatically.** The tag triggers
   `.github/workflows/publish.yml`: build → TestPyPI (`testpypi`
   environment) → PyPI (`pypi` environment, OIDC trusted publishing — no
   tokens). Check the Actions run; a stuck publish is usually the GitHub
   environment approval gate or a trusted-publisher config mismatch (repo,
   workflow filename, and environment name must match PyPI's registration
   exactly).
7. **Close the loop.** GitHub release notes from the CHANGELOG section; close
   the milestone's issues; verify `pip install database-tycoon==<ver>` pulls
   the new version.

## Verification gates before tagging

```bash
uv run pytest -q            # green on 3.12 and 3.13 in CI, not just locally
uvx ruff check src tests
uv run tycoon --version     # reports the version being released
tycoon docs build --strict  # docs site builds clean
```

Version coherence: `pyproject.toml`, `CHANGELOG.md`, and
`docs/releases/v<ver>.md` must all agree before the tag exists — the tag is
immutable once publish fires.
