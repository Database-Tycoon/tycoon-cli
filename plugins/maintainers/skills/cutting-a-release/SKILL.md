---
name: cutting-a-release
description: Use when cutting or publishing a tycoon release: opening the next version branch, finalizing CHANGELOG.md and docs/releases/, merging the release branch to main, pushing the version tag, or troubleshooting the PyPI trusted-publishing workflow.
license: MIT
compatibility: tycoon-cli repository, maintainer permissions on Database-Tycoon/tycoon-cli
metadata:
  author: database-tycoon
  tier: maintainers
---

# Cutting a release

CONTRIBUTING.md, "Release process" and "Merging into the release branch", is the
authoritative procedure. This skill names the steps
that have gone wrong and the checks that catch them. Read the CONTRIBUTING.md
sections first.

## Before the merge to main

1. Finish the record on the release branch, in the same commit series:
   - `CHANGELOG.md`: convert `[Unreleased]` into `## [<ver>] - YYYY-MM-DD`.
   - `docs/releases/v<ver>.md`: the long-form notes. The CHANGELOG and this page
     must agree, since CI and readers both use them.
   - Regenerate Rich-output snapshots if user-facing strings changed (see the
     testing-cli-changes skill), and review the diff.
2. Run the gates CI runs, with `uv run`, not `uvx`:

   ```bash
   uv run pytest -q
   uv run ruff check src tests
   uv run ruff format --check src tests
   uv run --extra docs mkdocs build --strict
   uv run tycoon --version    # reports the version being released
   ```

3. Check that the version agrees in `pyproject.toml`, `src/tycoon/__init__.py`,
   `CHANGELOG.md` and `docs/releases/v<ver>.md`. The tag is immutable once
   publish fires.

## Preflight

`publish.yml`'s `preflight` job fails the release before anything publishes. It
requires the tag, `pyproject.toml`, `__version__` and a dated CHANGELOG entry to
agree, and it requires `docs/releases/v<ver>.md` without `_Released: TBD_`. A
release that passes CI can still fail preflight, so run the same comparison
before tagging.

## Tag and publish

Branch and tag share a name, so push the tag with its full ref:

```bash
git tag v<ver>
git push <remote> refs/tags/v<ver>   # the upstream remote, not a guessed name
```

Pushing an unqualified `v<ver>` is ambiguous between the branch and the tag.
The tag triggers `publish.yml`: build, then TestPyPI, then PyPI, through
OIDC trusted publishing with no tokens. A stalled publish is usually the
GitHub environment approval gate, or a trusted-publisher registration that does
not match the repository, workflow file and environment name exactly.

## After publish

Check that `pip install database-tycoon==<ver>` installs the new version. Create
the GitHub release from the CHANGELOG section, close the milestone's issues,
and close the milestone.
