---
title: "Blueprint: weather module (first external Source + Shipments)"
description: A synthetic weather Source shipping data into the demo project through the Logistics loop - the first end-to-end DATA_SOURCE fulfillment
tags: [crlf, blueprint, logistics]
related: [specification_citizen_request_framework, task_contract_extension, index]
updated: '2026-08-05'
---

# Blueprint: the weather module

> **SUPERSEDED (2026-08-06) — the weather half only.** The city's weather is
> now MEASURED, not synthesised: `city.json`'s `weather` block derives fog from
> real `dbt source freshness` verdicts walked downstream over the measured
> edges, so a late source fogs the districts it FEEDS (see "`weather`" in
> `docs/city-json-v1.md` and `src/tycoon_city/export/measured.py`). Requirements
> 2–3 below — the synthetic `raw.weather` source and the buildings it would
> add — are retired; a fabricated weather feed belongs in the SIMULATED layer
> and the real one already covers the map. The **logistics half**
> (requirement 1: `sim/logistics.py`, `Shipment`, `LogisticsHub`, Customs) is
> CRLF, out of scope here, and stands unchanged.

**Depends on:** task_contract_extension (Customs validation).
**Fulfills:** a `DATA_SOURCE` DataRequest ("citizens need weather_temp").

## Requirements

1. New module `src/tycoon_city/sim/logistics.py`: `Shipment` (schema-shaped) and
   `LogisticsHub.receive(shipment) -> Landed | Contraband`, where Customs is
   `contracts.validate_shipment`. Contraband is counted, never silently
   dropped (absence stays named — expose `hub.contraband_count`).
2. Synthetic weather source: extend `scripts/make_demo_tycoon.py` with a
   `raw.weather` table (hourly rows: ts, temp_c, precip_mm) plus a staging
   model `stg_weather` (raw_code with `{{ source('raw','weather') }}` so
   column lineage traces) and dlt-style load rows in the metadata DB so the
   new street carries REAL freshness/traffic like every other source.
3. The demo city must show it: a new industrial building in `raw`, a street
   to `staging.stg_weather`, traffic within the fresh-build hour.
4. NO invented on-map numbers: the Hub/Shipment machinery is plumbing plus
   fixture data; anything visible on the map must flow through the existing
   measured channels (loads, builds, freshness).

## Acceptance criteria

- [ ] `uv run pytest -q` fully green including new `tests/sim/test_logistics.py`
      (landed shipment, contraband shipment counted with named errors).
- [ ] Regenerated demo-tycoon renders the weather buildings + street; state
      what you SAW in the report (render-and-look; use your own vite port).
- [ ] The e2e fixture (`demo.duckdb` export in `web/public`) restored;
      Playwright suite green.
- [ ] `docs/log.md` entry; local commits only; report deliberately-left-out items.
