---
title: "Blueprint: City Dashboard slice (requests backlog panel)"
description: Phase-3 observability - a Requests panel in the web UI listing CRLF DataRequests with status, gated behind a URL flag until Stephen flips the default
tags: [crlf, blueprint, web, hud]
related: [specification_citizen_request_framework, task_contract_extension, index]
updated: '2026-08-05'
---

# Blueprint: City Dashboard — the requests backlog

**Depends on:** task_contract_extension. Citizens themselves (patience,
happiness) are NOT in scope — this is the read-only backlog surface that
will display them later.

## Requirements

1. A requests document (`requests.json` beside `city.json`, served by
   `webserve.py` when present; 404 → panel hidden, absence named in the
   notes popover as "no request backlog"). Validate client-side against the
   request schema (zod mirror in `web/src/`).
2. Panel toggled with `B` (backlog), styled like the problems panel:
   requests worst-first (CRITICAL→LOW), status badge, age. Click →
   nothing yet (no fulfillment loop) — render a plain row, no dead buttons.
3. SIMULATED provenance label on the panel header until requests come from a
   real source: this is the `?guests=1` pattern — the panel only renders
   with `?crlf=1` for now.
4. Demo data: `scripts/make_demo_tycoon.py` writes a small `requests.json`
   (3-5 requests across types/priorities) into its export directory.

## Acceptance criteria

- [ ] `npx tsc --noEmit` clean; Playwright green INCLUDING two new specs:
      default demo fixture shows no panel and no `B` response; with
      `?crlf=1` + a requests.json fixture the panel lists rows worst-first.
- [ ] Keyboard `B` ignored while typing in inputs (follow the existing guard).
- [ ] Keymap (`?`) and notes popover updated; legend untouched.
- [ ] `docs/log.md` entry; local commits only.
