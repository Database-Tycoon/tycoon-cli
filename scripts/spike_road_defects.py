"""Spike: render the planned road network and count its geometry defects.

Not a test — a look-first instrument for the roads pass (2026-08-05, Stephen:
"strange and unrealistic and ugly roads"). Draws the plan tile map with PIL
and prints, per city:
  - jogs: direction changes per route (staircases score high)
  - parallel runs: pairs of long same-direction road runs <= 2 tiles apart
  - stubs: road tiles with exactly one road/lot neighbour that are not a
    route endpoint's approach (dead ends)
  - endings vs dressings (streets v4): every tile where the road network stops
    (at most one orthogonal ROAD neighbour) and whether a street feature is
    there to dress it. NAKED endings are drawn in magenta and are what
    property S7 fails a build on. Features paint over the road: cyan aprons,
    orange-red docks, off-white plazas.

Usage: uv run python scripts/spike_road_defects.py <duckdb-or-tycoon-src> <out.png>
"""

from __future__ import annotations

import sys
from collections import defaultdict

from PIL import Image

from tycoon_city.catalog.loader import load_context
from tycoon_city.sim.layout import plan_dag_layout

CELL = 8

COL_GRASS = (58, 132, 66)
COL_ROAD = (110, 110, 116)
COL_LANE = (140, 140, 148)
COL_LOT = (60, 90, 200)
COL_PLANT = (200, 80, 80)
COL_POWER = (230, 210, 80)
COL_STUB = (255, 40, 40)
COL_JOG = (255, 140, 0)
# Streets v4 endings.
COL_APRON = (90, 210, 230)
COL_DOCK = (120, 40, 170)  # purple: jog orange is too close to any warm tone
COL_PLAZA = (245, 245, 235)
COL_NAKED = (255, 0, 255)
FEATURE_COLOURS = {"apron": COL_APRON, "dock": COL_DOCK, "plaza": COL_PLAZA}


def main() -> None:
    src, out = sys.argv[1], sys.argv[2]
    ctx = load_context(src)
    plan = plan_dag_layout(ctx)

    route_tiles: set[tuple[int, int]] = set()
    for route in plan.routes.values():
        route_tiles |= set(route[1:-1])
    lane_tiles = set(plan.lane_tiles)
    road = route_tiles | lane_tiles | set(plan.access_road)
    lots = set(plan.positions.values())

    # --- jogs per route -----------------------------------------------------
    jog_tiles: set[tuple[int, int]] = set()
    jog_counts: list[tuple[int, tuple[str, str]]] = []
    for key, route in plan.routes.items():
        jogs = 0
        for i in range(1, len(route) - 1):
            d1 = (route[i][0] - route[i - 1][0], route[i][1] - route[i - 1][1])
            d2 = (route[i + 1][0] - route[i][0], route[i + 1][1] - route[i][1])
            if d1 != d2:
                jogs += 1
                jog_tiles.add(route[i])
        jog_counts.append((jogs, key))
    jog_counts.sort(reverse=True)

    # --- dead-end stubs -----------------------------------------------------
    def neighbours(t: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = t
        return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

    endpoints: set[tuple[int, int]] = set()
    for route in plan.routes.values():
        if len(route) >= 3:
            endpoints.add(route[1])
            endpoints.add(route[-2])
    if plan.access_road:
        endpoints.add(plan.access_road[0])
        endpoints.add(plan.access_road[-1])

    stubs = set()
    for t in road:
        linked = sum(1 for n in neighbours(t) if n in road or n in lots)
        if linked <= 1 and t not in endpoints:
            stubs.add(t)

    # --- long parallel runs -------------------------------------------------
    # Horizontal runs: maximal x-spans of road at one y. Two runs are
    # "redundant parallel" when they overlap in x for >= 6 tiles and sit
    # 1-2 rows apart (lane widening's extra rows are excluded via lane_tiles).
    rows: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for x, y in sorted(route_tiles):
        spans = rows[y]
        if spans and spans[-1][1] == x - 1:
            rows[y][-1] = (spans[-1][0], x)
        else:
            rows[y].append((x, x))
    parallel_pairs = 0
    ys = sorted(rows)
    for i, y1 in enumerate(ys):
        for y2 in ys[i + 1 :]:
            if y2 - y1 > 2:
                break
            for a0, a1 in rows[y1]:
                for b0, b1 in rows[y2]:
                    if min(a1, b1) - max(a0, b0) >= 6:
                        parallel_pairs += 1

    # --- streets v4: endings and their dressings ----------------------------
    dressed: set[tuple[int, int]] = set()
    for f in plan.street_features:
        for dx in range(f.w):
            for dy in range(f.h):
                dressed.add((f.x + dx, f.y + dy))
    all_road = road | dressed
    endings = [t for t in sorted(all_road) if sum(1 for n in neighbours(t) if n in all_road) <= 1]
    naked = [t for t in endings if not any(n in dressed for n in [t, *neighbours(t)])]

    # --- paint --------------------------------------------------------------
    img = Image.new("RGB", (plan.width * CELL, plan.height * CELL), COL_GRASS)
    px = img.load()

    def fill(t: tuple[int, int], c: tuple[int, int, int]) -> None:
        for dx in range(CELL - 1):
            for dy in range(CELL - 1):
                px[t[0] * CELL + dx, t[1] * CELL + dy] = c

    for t in route_tiles:
        fill(t, COL_ROAD)
    for t in lane_tiles:
        fill(t, COL_LANE)
    for t in plan.access_road:
        fill(t, COL_ROAD)
    for t in plan.power_tiles:
        fill(t, COL_POWER)
    for t in jog_tiles:
        fill(t, COL_JOG)
    for t in stubs:
        fill(t, COL_STUB)
    for f in plan.street_features:
        for dx in range(f.w):
            for dy in range(f.h):
                fill((f.x + dx, f.y + dy), FEATURE_COLOURS[f.kind])
    for t in naked:
        fill(t, COL_NAKED)
    for t in lots:
        fill(t, COL_LOT)
    fill(plan.plant_xy, COL_PLANT)
    img.save(out)

    total_jogs = sum(j for j, _ in jog_counts)
    print(f"routes={len(plan.routes)} road_tiles={len(road)} lane_tiles={len(lane_tiles)}")
    print(f"total_jogs={total_jogs} mean_jogs={total_jogs / max(len(jog_counts), 1):.1f}")
    print("worst routes by jogs:")
    for jogs, key in jog_counts[:8]:
        print(f"  {jogs:3d}  {key[0]} -> {key[1]}")
    print(f"stubs={len(stubs)}: {sorted(stubs)[:12]}")
    print(f"redundant_parallel_pairs={parallel_pairs}")
    kinds: dict[str, int] = {}
    for f in plan.street_features:
        kinds[f.kind] = kinds.get(f.kind, 0) + 1
    pads = [f for f in plan.street_features if f.w > 1 or f.h > 1]
    print(f"endings={len(endings)} features={len(plan.street_features)} {kinds}")
    print(f"wide_pads={len(pads)} naked_endings={len(naked)}: {naked[:12]}")
    print(f"image -> {out}")


if __name__ == "__main__":
    main()
