---
title: Database Tycoon docs
description: Index of the Database Tycoon documentation bundle
tags: [index]
related: []
updated: '2026-08-09'
---

# Database Tycoon — Documentation

- [guide.md](guide.md) — the reader's guide to the city: how to read the map, what the city knows, role lenses and the tour, the HUD, static export, theming, and what it deliberately does not do
- [conventions.md](conventions.md) — working conventions carried from the renderer's own repo: the mutation-testing rule, the contract-change process, and the render-and-look rule
- [handover.md](handover.md) — **start here in a new session**: what this is, current state, what to do next, and the traps this repo has already sprung
- [hud-design.md](hud-design.md) — the HUD design brief: Stephen's standing priority (HUD over visual quality), principles, and the component build order
- [city-json-v1.md](city-json-v1.md) — normative `city.json` contract: the seam between the Python side and any renderer, with the measurements behind each decision
- [run-json-v1.md](run-json-v1.md) — normative `runs.json` / `runs/<id>.json` contract: replaying one specific dbt run step by step, and why these id- and timestamp-bearing documents live outside byte-stable `city.json`
- [agent_tasks/](agent_tasks/index.md) — the CRLF master spec and active blueprints: Markdown tasks agents pick up, each with requirements and acceptance criteria
- [road-grammar.md](road-grammar.md) — research synthesis (real cities + sims): the seven themes, the legal road-ending taxonomy (S7), the junction-spacing rule (S8), the streets v4 rules, and the streets v5 spike status
- [semantic-roads.md](semantic-roads.md) — design sketch: Apache Ossie (OSI) join knowledge as a new road class, and semantics-as-city-development (the documentation incentive layer)
- [local-ai-capacity.md](local-ai-capacity.md) — design sketch, post-1.0: local LLM capacity as a second generating station, what "capacity" may honestly claim, and why it belongs in its own document rather than byte-stable `city.json`
- [release-notes-0.1.0.md](release-notes-0.1.0.md) — the 0.1.0 release candidate: what ships, both install paths (standalone and the `database-tycoon[city]` add-on), the trademark notice, the known issues, and the two draft PR bodies
- [superpowers/](superpowers/index.md) — design specs and plans from agent sessions
- [log.md](log.md) — documentation change log, newest first; the detailed record
