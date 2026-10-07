# CLAUDE.md

Guidance for coding agents working in this repository. Rules live in the files
below; this page only points at them.

- **Contributing rules** (PR size cap, title format, issue linkage, code and
  commit conventions, release process): `CONTRIBUTING.md`.
- **PR body:** fill in `.github/PULL_REQUEST_TEMPLATE.md`. Tick a checklist
  item only when it is true.
- **Prose** (docs, issues, PR bodies, changelog, release notes): follow
  `skills/repository-writing-style/SKILL.md` and the reference for the format
  you are writing.
- **City renderer** (`src/tycoon_city`, `web/`): `docs/city/conventions.md`,
  then `docs/city/handover.md`. Layout or visual changes are verified by
  looking at a screenshot, not by a green suite.
- **Docs site:** `docs/index.md` is the entry point; `uv run mkdocs build
  --strict` must stay clean.
- **Checks before opening a PR:** `uv run pytest -q`, `uv run ruff check src
  tests`, `uv run ruff format --check src tests`; for `web/`, `npx tsc
  --noEmit` and `npx playwright test`.
