# Database Tycoon (game)

A DuckDB catalog rendered as an interactive SimCity-style 3D city. Distribution
`database-tycoon-city`, module `tycoon_city` — chosen so the name does NOT
collide with the Tycoon CLI (whose PyPI distribution `database-tycoon`
normalizes to `database_tycoon`); the two products share a brand, not a
name and not code.

**Start every session at [`handover.md`](handover.md)** — current
state, what to do next, and the traps this repo has already sprung. Detailed
history: `docs/log.md`. The approved 1.0 plan is at
`~/.claude/plans/fancy-wiggling-clarke.md` (the earlier phases-A–G plan it
replaced is gone; the handover carries its surviving decisions).

Rules that override defaults:

- **Render it and look.** For anything touching layout, geometry, or visuals, a
  green suite is not evidence — open the PNG/screenshot. The dominant defect
  class here is a test asserting the right value on the wrong axis; see the
  handover's trap list before writing tests.
- **Mutation-test every guard** you add (with `PYTHONDONTWRITEBYTECODE=1`,
  `__pycache__` cleared, plus one no-op control mutant that must survive).
- **`city.json` is a contract.** Changes go through `docs/city-json-v1.md`, a
  `version` bump when breaking, and `scripts/update_contract_golden.py` —
  review the golden's diff.
- The web app is verified headlessly — use the `verifying-web-uis-headless`
  skill (`~/.claude/skills/`) for the Playwright/Chrome/SwiftShader recipe.
- Python: `uv run pytest -q`, `uv run ruff format . && uv run ruff check .`.
  Web: `cd web && npx tsc --noEmit`; dev server `npm run dev` (port 5173),
  demo data via `npm run demo-data`.
- Decisions marked closed in the handover (web renderer, strip layout unfixed,
  containerised-DuckDB-first, no `tycoon` import) are **not to be reopened**.
