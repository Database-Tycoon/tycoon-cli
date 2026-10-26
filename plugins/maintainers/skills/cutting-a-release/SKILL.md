---
name: cutting-a-release
description: Use when running a tycoon-cli release cycle or any step of it - opening the next `v<ver>` branch and milestone, getting a cycle content-complete, testing the release build, naming a release, setting the release date, opening or merging the release PR into main, pushing the version tag, a failed or stalled publish.yml run, a tag that needs moving, creating the GitHub Release, or asking "is the release ready" or "is the release done".
license: MIT
compatibility: tycoon-cli repository, write access to Database-Tycoon/tycoon-cli
metadata:
  author: database-tycoon
  tier: maintainers
---

# Cutting a release

CONTRIBUTING.md, "Release process" and "Merging into the release branch", is the
authoritative procedure. This skill is the operator's checklist: the order, the
exact commands, and the steps that have gone wrong before. Read those two
sections first.

A release is done when four surfaces are verified: the release PR merged to
`main`, the tag pushed, PyPI serving the version, and a GitHub Release marked
Latest. The tag push and the PyPI upload cannot be undone. The GitHub Release
is manual, and it has been forgotten before.

## Fixed facts

| Fact | Value |
|---|---|
| Cadence | Two-week cycles, one GitHub milestone each, with the cycle's theme in the milestone description. Each cycle ships as a patch release (`v0.2.4`, `v0.2.5`) and may carry features before 1.0. The minor version goes up when a themed milestone lands (`v0.3.0`). |
| Remote | `<remote>` below means the remote that points at `Database-Tycoon/tycoon-cli`. Check `git remote -v` rather than assuming `origin`. |
| Release branches | `v*.*.*` branches are protected: every change arrives by PR with one approval, and force pushes and deletion are blocked. Only admins bypass, so a maintainer with write access opens a PR even for a one-line date change. |
| Refs | Branch and tag share a name. Write `refs/tags/v<ver>` and `refs/heads/v<ver>` in every command. |
| Tag | Lightweight (no `-a` or `-s`), on the merge commit at `<remote>/main`. |
| Publish | `publish.yml` runs on `push: tags: v*` only, from the tagged commit, with no `workflow_dispatch`. Jobs: preflight, build, TestPyPI, PyPI, through trusted publishing. The `pypi` and `testpypi` environments accept only tags matching `v*.*.*`. |
| CI | `ci.yml` runs on PRs and on pushes to `main`. It never runs on release branches, so per-PR green says nothing about the merged result. |
| GitHub Release | Not created by the workflow. Copy the previous release's title format (version, then the release name); the notes are `docs/releases/v<ver>.md`. |
| Sign-off | The lead maintainer names the release and gives a written go-ahead before the tag push. When the lead is out, the backup maintainer does both. |

## Order

0. **Content complete.** Every PR in the milestone is merged or moved to the
   next one. The release-notes PR merges last. If its CHANGELOG conflicts with
   entries merged since, don't hand-merge: rebuild the `[Unreleased]` section
   with `rebuild_unreleased.py` (in this directory; it exits 1 if an entry
   would be lost) and leave a PR comment explaining the rebuild. Then run
   `uv run pytest -q`, `uv run ruff check src tests`,
   `uv run ruff format --check src tests` and
   `uv run --extra docs mkdocs build --strict` on the release-branch tip,
   because CI never ran on it.
1. **Test the release as a user would.** The suite stubs the uv and dlt calls
   these features depend on, so a green suite does not prove the release
   works. Build the wheel from the release-branch tip in a clean worktree,
   install it into a fresh `uv venv`, and in throwaway projects run
   `tycoon init`, a template `tycoon data run-all`, a real
   `tycoon data sources add <catalog-name> --no-prompt`, and the cycle's
   headline features. Then test the upgrade path: install the previous version
   from PyPI into a separate venv, with `HOME` set to a scratch directory (keep
   `UV_CACHE_DIR` and `UV_PYTHON_INSTALL_DIR` pointed at the real ones) so the
   old version never touches your real `~/.tycoon`.
   A project's `.venv` resolves `database-tycoon` from PyPI, which still holds
   the previous release, and every `uv add` re-syncs back to it. Run the tool
   venv's `tycoon` binary, not `.venv/bin/tycoon`. Write down what you did not
   cover.
2. **Name it.** Offer the lead maintainer three or four names drawn from the
   notes' themes, with a recommendation. Names are concrete feature
   descriptors ("project-local environments"), never metaphors. The lead
   maintainer picks.
3. **Date-set PR, then the release PR.**
   - Open a small PR into `v<ver>` that renames `## [Unreleased]` in
     `CHANGELOG.md` to `## [<ver>] - YYYY-MM-DD`, adds a
     `_Headline: **<name>**. <two or three sentences>._` line under it, sets
     `_Released: YYYY-MM-DD_` in `docs/releases/v<ver>.md`, replaces its
     `Headline: TBD` line, and points the "current release" line in
     `docs/releases/index.md` at the new page. A maintainer approves it. It
     must be the last content change: preflight checks only the date's shape,
     so a date set before a later merge ships stale.
   - Before merging it, run `publish.yml`'s preflight locally: copy the `run:`
     block of the "Validate version + changelog coherence" step and run it
     with `GITHUB_REF=refs/tags/v<ver>`.
   - Open the release PR as a draft:
     `gh pr create --draft --base main --head v<ver>`, titled like earlier
     release PRs (`release: v<ver>` and the name). Release-promotion PRs are
     exempt from the title and size checks. The body covers what it promotes,
     the name, a Mental model, the merged PRs grouped by area, and the step 1
     results including what was not covered.
4. **Merge the release PR** once CI is green and every review ask is answered,
   non-blocking ones included. Use a merge commit pinned to the reviewed head:
   `gh pr ready <n>`, then `gh pr merge <n> --merge --match-head-commit <sha>`.
5. **Preflight the merged tip from a clean worktree.** Ignored files in your
   working tree inflate the sdist, because hatchling honours only the root
   `.gitignore`.

   ```bash
   git fetch <remote> main
   git worktree add --detach /tmp/rel <remote>/main && cd /tmp/rel
   uv build && uvx twine check dist/*
   unzip -p dist/*.whl '*/METADATA' | head -2   # Metadata-Version
   ls -l dist/                                  # compare sizes with the previous release on PyPI
   ```

   Compare `Metadata-Version` with the last published wheel's (fetch its
   `.metadata` file from PyPI). A build backend upgrade once raised it to a
   version the pinned publish action rejected, after every other gate passed.
   Also check that `pyproject.toml` and `src/tycoon/__init__.py` agree on the
   version, and that `https://pypi.org/pypi/database-tycoon/<ver>/json` and the
   `test.pypi.org` equivalent both return 404.
6. **Stop and ask for the go.** Post the gate results, what they do not cover,
   and the exact commands for steps 7 to 9 to the lead maintainer (the backup
   when the lead is out). Push the tag only after a written go-ahead for this
   version. Approval of something else in the same thread is not a go.
7. **Wait for every run to finish, then tag.** `gh run list --commit <main sha>`
   must be all `completed success`, and `gh run list` must show nothing queued
   or in progress anywhere in the repository.

   ```bash
   git tag v<ver> <remote>/main
   git push <remote> refs/tags/v<ver>
   ```

8. **Watch the publish.** `gh run list --workflow publish.yml --limit 1` gives
   the run id; then `gh run watch <run-id> --exit-status` with the real id
   filled in. If it fails, first confirm the version still returns 404 on both
   indexes. If it does, nothing was consumed: fix forward on `main` through a
   PR, delete the tag (`git push <remote> --delete refs/tags/v<ver>`), re-tag
   the new tip and push again. Re-running the failed run reuses the old
   workflow file from the tagged commit, so it cannot pick up the fix. Never
   bump the version to escape a failed publish.
9. **Create the GitHub Release.**

   ```bash
   git show refs/tags/v<ver>:docs/releases/v<ver>.md > /tmp/notes-v<ver>.md
   gh release create v<ver> --verify-tag --title "<title>" --notes-file /tmp/notes-v<ver>.md
   ```

10. **Verify the four surfaces, then close the loop.**
    - `main` holds the merge; `git ls-remote <remote> refs/tags/v<ver>` shows
      the tag.
    - PyPI's `info.version` is the new version and
      `uv pip install database-tycoon==<ver>` installs cleanly in a fresh
      venv. The per-version JSON can 404 for a few minutes after `info.version`
      updates; that is CDN lag.
    - `gh api repos/Database-Tycoon/tycoon-cli/releases/latest -q .tag_name`
      returns `v<ver>`.
    - `Closes #N` fires only for merges into `main`, so issues fixed on the
      release branch are still open. Close them after checking with the lead
      maintainer, then close the empty milestone
      (`gh api -X PATCH repos/Database-Tycoon/tycoon-cli/milestones/<n> -f state=closed`).
    - Leave deleting the merged release branch to an admin; the ruleset blocks
      it for everyone else. Retarget any PR still based on it first, or GitHub
      closes them.
    - Hand over to the announcement (the `announcing-a-release` skill).

## Opening the next cycle

1. Create `v<next>` from `<remote>/main`. If the push is refused, ask an admin
   to create it.
2. Open a prep PR into it with the version bump (`pyproject.toml`,
   `src/tycoon/__init__.py` and the `version =` line for `database-tycoon` in
   `uv.lock`), a `docs/releases/v<next>.md` stub with `_Released: TBD_` and
   `Headline: TBD`, and its entry in the Releases nav in `mkdocs.yml` (a page
   missing from `nav` fails the strict build). Do not add a `## [<next>]`
   CHANGELOG section: every content PR adds its bullets under
   `## [Unreleased]` at that same spot, so an early section conflicts all of
   them. The release section is born in the date-set PR.
3. Early in the cycle, open the dependency-review PR described in
   CONTRIBUTING.md, "Release process".
4. Create the `v<next>` milestone, due two weeks out, with the theme in its
   description, and add `v<next>` as an option on the project board's Release
   field.

## Red flags

- "Every gate is green, so the publish will succeed." The publisher has
  rejected a wheel that passed every gate.
- "The suite is green, so the release code works." Only step 1 against the
  built wheel exercises the real uv and dlt calls.
- Building the sdist in your working tree instead of a clean worktree.
- Testing unreleased code from a project's `.venv`.
- Setting the release date before the last content PR merged.
- Hand-merging a CHANGELOG conflict on the release-notes PR.
- Tagging while any workflow is still running, or without the written go.
- Pushing an unqualified `v<ver>`, which is ambiguous between branch and tag.
- Never `uvx ruff`: use `uv run ruff`, since CI gates on the project's pinned
  ruff.
- Reporting the release done with fewer than four surfaces checked.
- In zsh, `set -- $var` does not word-split (use `${=var}`) and a literal
  `<run-id>` is read as a redirect. Check that a command that printed nothing
  actually ran.
