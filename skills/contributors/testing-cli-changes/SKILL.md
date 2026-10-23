---
name: testing-cli-changes
description: Use when writing or fixing tests in the tycoon-cli repo, when a CLI-surface bug slipped past in-process tests (PATH resolution, Rich rendering, console-script wiring, exit codes), when snapshot tests fail after changing user-facing strings, or when adding runnable bash examples to README or docs/recipes.
license: MIT
compatibility: tycoon-cli repository checkout with uv
metadata:
  author: database-tycoon
  tier: contributors
---

# Testing CLI changes

CONTRIBUTING.md, "What CI gates on" (line 24), lists every gate. Run the ones
that apply to your change before pushing:

```bash
uv run pytest -q                       # default suite, must pass on 3.12 and 3.13
uv run ruff check src tests            # lint gate
uv run ruff format --check src tests   # format gate; CI fails on this too
```

Coverage is enforced by `[tool.coverage.report].fail_under` in
`pyproject.toml`. Read the current value there rather than a number from memory.
Changes to `web/` also need `npx tsc --noEmit` and the Playwright suite, and the
committed bundle must match a rebuild (`scripts/sync_web_bundle.py`). Changes to
`docs/` need `uv run mkdocs build --strict` and
`scripts/check_docs_publishable.py`.

## Test tiers

| Marker | In default run? | Scope |
|---|---|---|
| _(none)_ | yes | Unit, no network, fast |
| `offline_e2e` | yes | Full pipeline, local only (e.g. csv-import template) |
| `e2e` | no | Live APIs or credentials; manual `e2e.yml` workflow only |

## The subprocess layer: when in-process tests lie

In-process Typer tests cannot see PATH resolution, Rich rendering artifacts,
stdout and stderr framing, or console-script wiring. Any CLI-surface bug needs
its regression test at the subprocess layer:

- `tests/test_recipe_doctests.py` runs fenced bash blocks from README and
  `docs/recipes/*.md` marked `<!-- tycoon-test: mode=offline -->`, with
  `bash -e -o pipefail` in a fresh temporary directory and `HOME` rebound.
  `mode=online` blocks run only in `nightly-e2e.yml`. Commands run literally,
  with no substitution.
- `tests/test_e2e_demo_arc.py` drives the installed console script end to end.
- `tests/test_cli_surface.py` walks the registered command tree: every
  subcommand's `--help` must exit 0, and a stale-string registry rejects
  user-facing strings that mention removed commands. When you remove or
  rename a command, add its old invocation to that registry.

## Snapshot tests for Rich output

`tests/test_snapshots.py` (syrupy) pins exact rendered strings of install
hints, doctor rows and error paths. After intentionally changing a user-facing
string:

```bash
uv run pytest --snapshot-update tests/test_snapshots.py
git diff tests/__snapshots__/      # review before committing
```

Never commit a snapshot update without reading its diff: the diff is the review.
