---
title: Agent tasks (CRLF blueprints)
description: Index of the CRLF master specification and the active blueprints agents can pick up
tags: [index, crlf, agents]
related: [specification_citizen_request_framework]
updated: '2026-08-05'
---

# Agent tasks — CRLF blueprints

## Streets v4 (2026-08-05, dispatched)

- [task_streets_v4_planner.md](task_streets_v4_planner.md) — legal endings (apron/dock/plaza) + S7 no-naked-stub property + town_plan split; contract seam frozen
- [task_streets_v4_renderer.md](task_streets_v4_renderer.md) — 3D sidewalk curbs + dressed-ending rendering; builds against the frozen street_features shape
- [task_v5_reconciliation.md](task_v5_reconciliation.md) — Streets v5 planner unit tests (Property S7/S8, schema clustering, determinism) + v5 cutover & block stagger reconciliation

## CRLF blueprints

- [specification_citizen_request_framework.md](specification_citizen_request_framework.md) — **read first**: the Three Pillars (Citizens/Demand, Blueprints/Supply, Logistics/Flow), schemas, roadmap, and the repo-laws addendum every blueprint inherits
- [task_contract_extension.md](task_contract_extension.md) — request/shipment schemas + Customs validation; no dependencies, **do first**
- [task_weather_module.md](task_weather_module.md) — first external Source shipping through the Logistics loop into the demo city; depends on the contract extension
- [task_stats_ui.md](task_stats_ui.md) — City Dashboard slice: the requests backlog panel behind `?crlf=1`; depends on the contract extension
