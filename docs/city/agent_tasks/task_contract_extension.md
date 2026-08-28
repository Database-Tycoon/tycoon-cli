---
title: "Blueprint: CRLF contract extension (requests & shipments)"
description: Add the request and shipment schemas to contract/fixtures with validation helpers - the Customs foundation every other CRLF task depends on
tags: [crlf, blueprint, contract]
related: [specification_citizen_request_framework, index]
updated: '2026-08-05'
---

# Blueprint: CRLF contract extension

**Depends on:** nothing — do this one first. **Unblocks:** weather module, stats UI.

## Requirements

1. Write `contract/fixtures/request_schema.json` and
   `contract/fixtures/shipment_schema.json` exactly as defined in the master
   specification (section 3).
2. New module `src/tycoon_city/sim/contracts.py`: `validate_request(obj)` and
   `validate_shipment(obj)` returning `(ok: bool, errors: list[str])`. Plain
   stdlib validation against the schema files (no new runtime deps —
   jsonschema is NOT in the dependency tree; hand-roll the small subset:
   required keys, enums, types, integer bounds).
3. Failed validation is "Contraband": the error list must name every failing
   field, not just the first (Customs reports, it does not shrug).
4. These records must NOT enter `city.json` v1 (uuids/timestamps would break
   byte-stability). Do not touch `export/city_json.py` or the golden.

## Acceptance criteria

- [ ] Both schema files exist, valid JSON, matching the spec byte-for-intent.
- [ ] `uv run pytest tests/sim/test_contracts.py -q` green, covering: a valid
      request, a request missing a required key, a bad enum value, a
      complexity out of bounds, a shipment with `is_contaminated` defaulted
      absent, and an error list naming MULTIPLE failures at once.
- [ ] Wrong-axis check performed on at least one guard (break validation,
      watch the test fail, restore) and stated in your report.
- [ ] `contract/fixtures/demo.city.json` untouched (`git diff --stat` clean).
- [ ] `docs/log.md` entry; local commits only.
