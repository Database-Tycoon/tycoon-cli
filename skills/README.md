# Agent skills

Task-shaped instructions that coding agents (Claude Code, Codex, Cursor, …)
load on demand to drive the tycoon CLI correctly — the successor to a single
ever-growing agents file. Each skill is one directory holding a `SKILL.md`.

## Three tiers, three audiences

| Tier | For | Example concerns |
|---|---|---|
| `users/` | People who `pip install database-tycoon` and work *in a tycoon project* | adding sources, diagnosing failures, reading state, building models |
| `contributors/` | People with this repo cloned, changing the CLI | branch model, test layers, snapshot tests |
| `maintainers/` | Release-cutting maintainers | the release/publish cycle |

Org-internal maintainer tooling that leans on private systems (Jira, meeting
notes) is deliberately **not** committed here — it lives in maintainers'
local `.claude/skills/`, which is gitignored.

## How agents get these skills

Claude Code does not discover nested folders under `.claude/skills/`, so the
tiers are distributed as **plugins** instead — the root
`.claude-plugin/marketplace.json` declares one plugin per tier:

```
/plugin marketplace add Database-Tycoon/tycoon-cli
/plugin install tycoon@tycoon-skills              # users tier
/plugin install tycoon-contrib@tycoon-skills      # contributors tier
/plugin install tycoon-maintainers@tycoon-skills  # maintainers tier
```

Open question (PTC-80): additionally scaffolding the `users/` tier into new
projects via `tycoon init`, so a user's agent picks the skills up with zero
setup. Note for whoever implements it: `scaffold_from_template()` applies
`{{ }}` substitution to `.md` files, and fenced bash in docs paths marked
`tycoon-test:` gets executed by the recipe doctest harness — route around
both.

## Command → skill coverage index (users tier)

Skills align 1:1 with command *families* (the CLI's sub-app groupings /
user jobs), not individual commands — the valuable knowledge sits between
the commands of a family, and `--help` already covers single-command
mechanics. This index is the completeness audit: every command maps to its
owning skill, or explicitly to none.

| Command | Owning skill |
|---|---|
| `data sources *` (catalog/add/list/run/run-all/remove) | adding-data-sources |
| `register dbt` / `register warehouse` / `register rill` | building-models-and-dashboards |
| `data analyze`, `data transform *`, `start` / `stop` | building-models-and-dashboards |
| `data status` / `history` / `schema` / `query`, `data observability scaffold` | reading-project-state |
| `doctor`, `profiles *`, `setup`, `init --upgrade` | diagnosing-projects |
| `data run-all`, `schedule *`, `notify`, `data sync`, `data clean` | operating-pipelines |
| `init` (new projects), `run <tool>`, `docs *` | none — `--help` and the docs site suffice |
| `semantics *` (OSI), `data fivetran *` | none yet — add a skill when these grow traps worth teaching |

When adding or renaming a command, update this table in the same PR — an
unmapped command is an undocumented one.

## Authoring conventions

- One directory per skill: `skills/<tier>/<skill-name>/SKILL.md`; the
  frontmatter `name` must equal the directory name (lowercase, hyphens).
- `description` states **trigger conditions** — when an agent should load the
  skill (symptoms, error strings, task shapes) — not a summary of its
  content. It is the only text agents see before deciding to read the skill.
- Keep frontmatter to the open agentskills.io spec fields (`name`,
  `description`, `license`, `compatibility`, `metadata`) so the skills work
  across agents, not just Claude Code.
- Body under 500 lines; push heavy reference into sibling files, linked one
  level deep. Assume the agent is smart — document the traps and exact
  commands, not what a flag obviously does.
- Every claim must be grounded in the current code. Stale skills are worse
  than no skills: verify commands against `--help` before committing, and
  update skills in the same PR that changes the behavior they describe.
