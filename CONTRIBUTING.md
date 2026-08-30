# Contributing to tycoon

Thanks for your interest in contributing. This document covers how to get a
working dev environment, what the CI gate expects, and the repo conventions
we care about.

## Dev setup

Requires Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:Database-Tycoon/tycoon-cli.git
cd tycoon-cli
uv sync --all-extras   # install runtime + dev deps + the docs extra (mkdocs)
```

Verify the install:

```bash
uv run tycoon --version
uv run pytest -q
```

## What CI gates on

Every pull request (whatever branch it targets) and every push to `main` runs
`.github/workflows/ci.yml`:

- **`uv run pytest -q`** — full default test suite (256 tests as of v0.1.2).
  Runs against Python 3.12 **and** 3.13 in parallel. Network-gated tests
  (live APIs, credentials) are excluded by default; see *Test markers* below.
- **Coverage floor** — fails if overall coverage drops below 55%. Raise
  `[tool.coverage.report].fail_under` in `pyproject.toml` as coverage improves.
- **`uv run ruff check src tests`** — lint, followed by
  **`uv run ruff format --check src tests`**. Auto-fix most lint issues with
  `uv run ruff check src tests --fix`.

Before pushing, run the same locally:

```bash
uv run pytest -q
uv run ruff check src tests
uv run ruff format --check src tests
```

Use `uv run` rather than `uvx` for ruff. `uv run` honours the `ruff` version
pinned in `[dependency-groups] dev`, which is what CI runs; `uvx ruff` resolves
to the latest release instead and will report failures against rules this
codebase has never been linted for (see #201).

## Test markers

Three tiers, defined in `pyproject.toml` under `[tool.pytest.ini_options]`:

| Marker | Runs in default `pytest`? | Description |
|---|---|---|
| _(none)_ | ✅ yes | Unit tests — no network, no external services, fast |
| `offline_e2e` | ✅ yes | Full-pipeline tests that stay local (e.g. `csv-import` template) |
| `e2e` | ❌ no | Live API / credentialed tests (opt-in: `uv run pytest -m e2e`) |

The `e2e` tests run only via the manual `.github/workflows/e2e.yml` workflow
(click "Run workflow" in the Actions UI). They hit flaky upstream APIs and
aren't suitable for per-PR gating.

## pre-commit (optional)

Contributors can opt into local pre-commit hooks so ruff runs before each
commit:

```bash
uvx pre-commit install
```

The hook config lives in `.pre-commit-config.yaml` and mirrors what CI runs.
Not enforced — CI is still the source of truth.

## Making changes

### Adding a new feature

1. Open an issue first for anything non-trivial. We'd rather discuss design
   before you write the code than after.
2. Branch from the active release branch (e.g. `v0.1.10`) and PR back into
   it — not `main`. See *Release process* below.
3. Write tests. New behavior needs a test; bug fixes need a regression test.
   Reach for `conftest.py` fixtures before hand-rolling new ones.
4. Update `CHANGELOG.md` under the appropriate `[Unreleased]` subsection
   (Added / Changed / Fixed / Removed / Deprecated / Security).
5. For user-visible changes, update `README.md` too.

### Fixing a bug

1. If there's an open issue, reference it in the PR title — see
   *Pull request guidelines* below.
2. Add a regression test that fails on the release branch and passes on yours.
   This is enforced by review, not CI, but it's load-bearing.

## Pull request guidelines

### Keep PRs small

Each PR should change **at most 8 counted files**. A well-scoped change will often include an implementation file, a test file, and a few supporting changes such as documentation, registration, or configuration.

If your change needs to touch more than eight files, split it into a sequence of smaller PRs.

How you manage that sequence is up to you. You can create each branch from the previous one and select the previous branch as the PR base:

```shell
gh pr create --base <previous-branch>
```

You can also use a stacking tool such as [`gh-stack`](https://github.com/github/gh-stack). What matters is that each PR remains focused and can be reviewed on its own.

The following are excluded from the file-count limit:

- Files under `src/tycoon/templates/**`. A template's file tree is treated as one atomic bundle, so its contents are not counted.
- Release promotion PRs that merge a version branch such as `v0.2.0` into `main`. These collect work that has already been reviewed in earlier PRs.

New Python source files under `src/**/*.py` must also be no more than **300 lines** long. This applies only to newly added files; modifying an existing file that already exceeds the limit will not trigger the check.

### Title your PR consistently

Use the following format:

```text
type(scope): description
```

- `type` must be one of `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, or `ci`.
- `scope` identifies the issue, ticket, or maintenance area associated with the change.
- `description` is a short summary without a trailing period.
- The complete title must not exceed **100 characters**.

#### Link features and fixes to tracked work

For `feat`, `fix`, `refactor`, `test`, and `docs` PRs, the scope must point to the GitHub issue or Jira ticket being addressed.

Use `gh-<N>` for a GitHub issue in this repository:

```text
feat(gh-128): add layer materialization command
```

Use the canonical uppercase `PTC-<N>` format for a Jira ticket:

```text
fix(PTC-300): correct dbt profile resolution on Windows
```

Use whichever tracker contains the work. A corresponding GitHub issue is not required when the work is tracked directly in Jira.

For `chore` and `ci` PRs, the scope may describe the affected maintenance area:

```text
chore(deps): bump dlt from 1.26.0 to 1.29.1
ci(pypi-publish): bump action to v1.14.2
```

Routine maintenance and CI work do not require an issue or Jira ticket.

Release promotion PRs are exempt from the title format because they collect multiple previously reviewed changes and do not map to a single issue.

#### Closing GitHub issues

A reference such as `gh-128` in the title does not automatically close the issue when the PR is merged.

To close an issue automatically, include GitHub's closing syntax in the PR description:

```text
Closes #128
```

This is optional and is not enforced by the title check.

### Break up large issues

If an issue requires several PRs, divide it into smaller sub-issues before starting implementation. Each sub-issue should represent a focused unit of work that can be completed by one reasonably sized PR.

The parent issue remains the record of the overall goal, while each sub-issue provides the `gh-<N>` reference for its corresponding PR. Work tracked directly in Jira can follow the same pattern using separate `PTC-<N>` tickets.

### Quick reference

| Situation | What to do |
|---|---|
| Work is tied to a GitHub issue | `type(gh-<N>): description` |
| Work is tied directly to a Jira ticket | `type(PTC-<N>): description` |
| Routine maintenance does not need a ticket | `chore(<area>): description` |
| CI work does not need a ticket | `ci(<area>): description` |
| A change needs more than 8 counted files | Split it into a sequence of smaller PRs |
| An issue requires multiple PRs | Create smaller sub-issues or tickets, with one PR for each |
| A version branch is being promoted into `main` | The PR is exempt from the size and title checks |

### Enforcement status

The size and title checks currently appear as **visible, non-blocking CI warnings**. They will become required checks after contributors have had time to adopt the conventions and the rules have been validated in practice.

## Code conventions

- **No comments describing *what* the code does.** Well-named identifiers do
  that. Only write a comment when *why* is non-obvious — a subtle invariant,
  a workaround for a specific bug, behavior that would surprise a reader.
- **No unused imports, no half-finished implementations, no backwards-compat
  shims.** v0.1 is pre-1.0; we don't have users locked into old behavior.
  Delete aggressively.
- **Type hints everywhere** — we target `ruff` + `ty` clean. Forward
  references as string literals are fine when needed for circular imports.
- **Commits**: one logical change per commit, imperative mood, body explaining
  *why* the change was made. Squash noisy fixup commits before merging.

## Release process

Each release cycle lives on its own version branch. Nothing PRs into `main`
directly — it only advances when a release branch merges into it, so it
always reflects the latest published version.

1. A maintainer cuts a branch named for the next version (e.g. `v0.1.10`)
   off `main`. It becomes the active release branch, and all feature and fix
   PRs for the cycle target it. If none is open yet, ask in an issue.
2. Early in the cycle, the maintainer runs `uv tree --outdated` and opens a
   single dependency-review PR against the release branch, bumping the pins
   and SHA-pinned actions that are worth taking. Runtime pins are exact and
   propagate to downstream consumers, so each bump is a deliberate call —
   check what a version change drags into the lockfile, not just its number.
3. When the cycle is done, the maintainer finalizes `CHANGELOG.md` and the
   `docs/releases/v<ver>.md` long-form narrative on the branch.
4. The release branch merges into `main` via PR, then the version tag is
   pushed (branch and tag share a name, so use fully-qualified refs — see
   `docs/publishing-to-pypi.md`). The tag triggers PyPI publish via
   `.github/workflows/publish.yml` and the GitHub release.

Contributors don't cut releases — maintainers do. If you want to propose one,
open an issue first.

## Questions?

Open an issue on [GitHub](https://github.com/Database-Tycoon/tycoon-cli/issues)
or drop a comment on an existing one. We're small and the maintainers read
every issue.
