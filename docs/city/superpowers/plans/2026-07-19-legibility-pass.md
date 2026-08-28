---
title: Legibility pass implementation plan
description: Make the Map screen understandable — differentiated sprites, labels, legend, hover, camera centering, clipping fix, key hints
tags: [plan, ui, legibility, pygame]
related: [2026-07-19-pipeline-city-bones-design, 2026-07-19-pipeline-city-bones]
updated: '2026-07-19'
---

# Legibility Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use checkbox syntax.

**Goal:** A first-time viewer of the Map screen can tell what they're looking at and what they can do, without being told.

**Architecture:** Theme + render layer only. The sim/catalog layers and the
data-function registry are untouched; every new visual still derives from
existing data-derived state (zone_style, density, powered, lots, tiles).

## Global Constraints (inherited from the bones plan — all still binding)

- uv-managed; runtime deps ONLY duckdb + pygame-ce; dev ONLY pytest + ruff.
- All on-screen text uses data concepts as-is (schema, table, view, rows, database).
- No functional simulation: new visuals read existing data-derived state only.
- Files under ~500 lines; ruff format+check clean before every commit; TDD.
- Commit trailer: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Headless tests via SDL_VIDEODRIVER=dummy.

## Task L1: Differentiated building art + lot-aware tile drawing

**Files:** Modify `scripts/make_default_theme.py`, `themes/default/theme.toml`,
`themes/default/spritesheet.png` (regenerated output, committed),
`src/pipeline_city/render/tilemap.py`. Test: `tests/render/test_tilemap.py`,
`tests/render/test_theme.py`.

**Interfaces produced:**
- Sprite names `lot_{style}_{level}` for style in {industrial, commercial,
  residential} and level in 1..8 (24 sprites), plus existing grass/road/
  power_line/plant/water/vehicle. Grass becomes borderless/subtle (no black
  grid outline); two grass variants `grass` and `grass_alt` chosen by
  `(x + y) % 2` for texture.
- `lot_sprite_name(lot: Lot) -> str` in tilemap.py: returns
  `f"lot_{lot.zone_style.name.lower()}_{max(1, lot.density)}"`.
- `draw_tiles` gains lot-awareness: build `{(lot.x, lot.y): lot}` once per
  call; LOT tiles use `lot_sprite_name`; unpowered lots get a 55%-alpha black
  overlay after blit (data-derived dimming).
- Building look: per-style base colors (industrial rust `#b0563a`-family,
  commercial steel-blue `#4a6fa5`-family, residential warm gray
  `#8a8f79`-family), building footprint/height illusion and lit-window count
  increasing with level; level 8 visibly reads "tall downtown block" at 16px.
  Exact pixel art is implementer's judgment within these constraints.

**Steps:**
- [ ] Failing tests: `test_theme_has_all_lot_sprites` (all 24 names + grass_alt
  resolve via `theme.sprites` without placeholder warning),
  `test_lot_sprite_name_levels` (density 0 → level 1; density 8 → level 8;
  style name lowercased).
- [ ] Extend `make_default_theme.py` + `theme.toml`; regenerate the sheet.
- [ ] Implement `lot_sprite_name` + lot-aware `draw_tiles` with unpowered dim.
- [ ] `test_unpowered_lot_draws_dim_overlay`: render two 1-lot cities
  (powered/unpowered), assert center pixel of unpowered lot is darker.
- [ ] Full suite + ruff; commit `feat: differentiated building sprites and lot-aware drawing`.

## Task L2: Map screen legibility — clip fix, centering, labels, legend, hover, hints

**Files:** Modify `src/pipeline_city/render/screens.py`,
`src/pipeline_city/render/camera.py`, `src/pipeline_city/render/chrome.py`,
`src/pipeline_city/app.py` (camera init only). Test:
`tests/render/test_screens.py`, `tests/render/test_camera.py`,
`tests/render/test_chrome.py`.

**Interfaces produced:**
- `Camera.center_on_tiles(tiles: list[tuple[int,int]]) -> None`: sets offset so
  the bounding box of the given tile coords is centered in the viewport
  (clamped ≥ 0). `run_app` calls it with all non-GRASS/WATER tile coords after
  generation and after R-refresh.
- `MapScreen.draw` wraps map blitting in `surface.set_clip(pygame.Rect(*state.viewport))`
  / `set_clip(None)` — fixes the status-strip overdraw bug.
- `district_label_positions(city) -> dict[str, tuple[int,int]]` in screens.py:
  schema → centroid tile of its lots. MapScreen draws each schema name on a
  beveled chip at the centroid (small font, data-term text = the schema name).
- `_legend_entries(theme) -> list[tuple[str, str]]`: (sprite_name, label) pairs
  — labels: "table / view", "road (lineage)", "database", "power line",
  "water". MapScreen draws a compact legend panel bottom-right of the viewport.
- Hover: MapScreen tracks mouse position; `hovered_lot(state, pos) -> Lot | None`
  via `camera.screen_to_tile`; hovered lot gets a 2px light outline and a
  tooltip near the cursor: `f"{lot.object_key} — {rows} rows"` (rows from
  `state.ctx` lookup; views show their real 0).
- `draw_chrome` status strip gains right-aligned hint text:
  `"arrows/drag pan · wheel zoom · click an object · R refresh"` (constant
  `HINT_TEXT` in chrome.py so tests can assert it).

**Steps:**
- [ ] Failing tests: `test_map_draw_respects_viewport_clip` (pixel in status
  strip row unchanged after MapScreen.draw), `test_center_on_tiles_centers_bbox`,
  `test_hovered_lot_hit_and_miss`, `test_district_label_positions_centroids`,
  `test_legend_entries_use_data_terms` (no words "district"/"city"/"power plant"
  as labels; "power line" is allowed as an infrastructure term per spec tile
  names), `test_hint_text_present_in_status`.
- [ ] Implement camera centering; wire into run_app (initial + R-refresh).
- [ ] Implement clip fix, labels, legend, hover outline + tooltip, hints.
- [ ] Full suite + ruff; commit `feat: map legibility — centering, labels, legend, hover, hints, clip fix`.

## Task L3: Verify visually + docs

**Files:** Modify `README.md` (controls section), `docs/log.md`. Create
`scripts/screenshot.py` (reusable headless screenshot tool: args db_path,
out_dir; renders map/object/stats PNGs — extracted from the ad-hoc snippet in
`.superpowers/sdd/`).

**Steps:**
- [ ] Write `scripts/screenshot.py`; run it against `demo.duckdb`; READ the
  produced map PNG and confirm: buildings differ by density/style, schema
  labels visible, legend visible, no tiles below the status strip. Iterate on
  L1/L2 output if anything fails the eyeball test (report what changed).
- [ ] README: add Controls + "reading the map" sections (data terms as-is).
- [ ] docs/log.md entry. Full suite + ruff; commit `docs: legibility pass wrap-up`.

## Self-review notes

- L1/L2 ordering matters (L2's hover tooltip uses L1's lot index approach but
  touches different functions; still sequential to avoid tilemap.py conflicts).
- Nothing here writes sim state; hover/labels/legend are read-only overlays.
- Deferred (recorded): sprite art quality iteration beyond "readable",
  minimap, sounds, zoom-to-fit.
