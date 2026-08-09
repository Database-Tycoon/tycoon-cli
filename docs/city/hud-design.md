---
title: HUD design brief
description: The observation-platform HUD — priorities, principles, and the component plan (Stephen: HUD design matters more than visual quality)
tags: [hud, design, ui, observation]
related: [handover, city-json-v1]
updated: '2026-08-09'
---

# HUD design brief

**Standing priority (Stephen, 2026-08-04): HUD design over visual quality.**
Building silhouettes, skybridges and atlas polish rank *below* everything on
this page.

## What is wrong with the current HUD

- **No aggregate view.** The city knows 2 tests fail, 1 source is late, 1
  build errored — but you only learn it by clicking buildings one at a time.
  An observation platform must answer "is anything wrong?" in zero clicks.
- **The footer is a junk drawer.** Database facts, degradation notes and the
  controls hint share one ellipsized line; dogfood's notes overflow it.
- **No way to find anything.** 42 objects already needs search; 500 demands it.
- **Stats is a detour, not a tool.** A modal table you open, read, close.
- **No time anchor.** Nothing says when this picture was taken or how old the
  newest run is without opening an inspector.

## Design principles

1. **Zero-click health.** The most important facts are visible before any
   interaction.
2. **Every number is a door.** Any count or name shown is clickable and takes
   the camera to the thing (smooth fly-to, then select).
3. **Facts wear their provenance** — measured / declared / verdict labels
   carry into every new surface, exactly as the inspector does today.
4. **Absence stays named.** Degradation notes get a first-class affordance,
   never an ellipsis.
5. **Keyboard-first is acceptable.** This runs on an engineer's monitor.

## Components, in build order

0. **Model graph in the inspector** (LANDED 2026-08-04): the selected object's
   ancestry/descendants as a layered SVG DAG — verdict-coloured nodes,
   provenance-styled edges (solid declared, dashed inferred), every node
   clickable, trimmed to ±2 hops past 28 nodes.

1. **Health strip** (LANDED 2026-08-05) (under the header, always visible). Chips:
   `● 2 tests failing · ● 1 warn · ▲ 1 source late · ✕ 1 build error ·
   ◐ oldest build 21d`. Each chip clickable → cycles through its offenders
   (fly-to + select). Chips render only when nonzero; an all-clear strip shows
   a single quiet `✓ no findings`. Data: pure aggregation over `lots[]`.
2. **Camera fly-to** (LANDED 2026-08-05) (enabler for 1, 3, 4). Tween position+target over ~0.6s
   to frame a lot; `Cameras.flyTo(lot)`. Selection follows arrival.
3. **Problems panel** (LANDED 2026-08-05, incl. gauges) (left drawer, toggle `P` / chip long-press): the triage
   list — every flagged object with its verdicts, sorted worst-first, click →
   fly-to. This is Stats reborn as a tool.
4. **Search** (LANDED 2026-08-05) (`/` or Cmd-K): type-ahead over object keys, tags, owners;
   enter → fly-to + select. Include districts and the plant.
5. **Footer rework** (LANDED 2026-08-05; as-of is client fetch-time, so the byte-stable contract keeps no timestamp): left = `database · objects · rows · generated Xs ago`
   (add `generated_at` to city.json — additive; the age ticks live client-side
   so R-freshness is visible). Right = an `ⓘ notes (N)` popover holding the
   degradation notes, and a `?` keymap overlay. Controls hint moves into `?`.
6. **Coverage gauges** (LANDED 2026-08-05, in the problems header) (in the health strip's overflow or Problems header):
   documented %, tested %, sources-with-SLA % — the lit-city metric as
   numbers. All derivable from `objects[].columns` and `dbt.tests`.
7. **Inspector polish** (last): copy-key button, owner/tag chips clickable as
   search filters, sticky section headers.

## Non-goals

No dashboards-for-their-own-sake (charts of things the city already shows),
no invented scores (observation platform), no theming work until the above
lands.

## Verification pattern

Health-strip counts are pure functions of the document — unit-assertable in
the e2e page context against hand-counted fixtures; fly-to is assertable via
`__tycoonCity.cameraPose()` deltas; search via keyboard-driven specs. Same
render-and-look discipline as everything else.
