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
- **`uvx ruff check src tests`** — lint. Auto-fix most issues with
  `uvx ruff check src tests --fix`.

Before pushing, run the same locally:

```bash
uv run pytest -q
uvx ruff check src tests
```

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
2. Branch from the **active release branch** (`v0.1.x` — the highest open
   version branch, e.g. `v0.1.10`), and open your PR back into that same
   branch. Nothing PRs into `main` directly: `main` only advances when a
   release branch merges into it at release time, so it always reflects the
   latest published version. If no release branch is open yet, ask in an
   issue and a maintainer will cut one.
3. Write tests. New behavior needs a test; bug fixes need a regression test.
   Reach for `conftest.py` fixtures before hand-rolling new ones.
4. Update `CHANGELOG.md` under the appropriate `[Unreleased]` subsection
   (Added / Changed / Fixed / Removed / Deprecated / Security).
5. For user-visible changes, update `README.md` too.

### Fixing a bug

1. If there's an open issue, reference it in the commit (`fix: foo bar — #42`).
2. Add a regression test that fails on the release branch and passes on yours.
   This is enforced by review, not CI, but it's load-bearing.

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

Each release cycle lives on its own version branch, cut from `main` when the
cycle starts:

1. A maintainer cuts `v0.1.x` off `main` and it becomes the active release
   branch. All feature and fix PRs for that cycle target it (see *Making
   changes* above).
2. When the cycle is done, the maintainer finalizes `CHANGELOG.md` and the
   `docs/releases/v<ver>.md` long-form narrative on the branch.
3. The release branch merges into `main` via PR, then the version tag is
   pushed. The tag triggers PyPI publish via `.github/workflows/publish.yml`
   and the GitHub release.

Contributors don't cut releases — maintainers do. If you want to propose one,
open an issue first.

## Questions?

Open an issue on [GitHub](https://github.com/Database-Tycoon/tycoon-cli/issues)
or drop a comment on an existing one. We're small and the maintainers read
every issue.
