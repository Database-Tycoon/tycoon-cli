"""SPIKE 6: a THROWAWAY bridge — a streets v5 plan as a v1 `city.json`.

**Not a contract change, and not a step toward one.** `export/city_json.py`,
`export/blocks.py`, `web/src/contract.ts` and the golden are untouched; this
script writes its output under `spike-out/render/` and nothing else reads it.
When v5 really lands it lands as `city.json` **version 2** with `streets[]`,
`width_class`, `surface`, `ROAD_DIRT` and `districts[].texture` — the point of
this bridge is only to answer Stephen's question, *"does this read as a city?"*,
in the renderer, months before that contract exists.

Everything so far has been judged at one pixel per tile in 2D. Four spec-first
geometry attempts have been wrong in this repo, and a 2D sheet is itself a kind
of spec: it shows what the planner MEANT. The renderer shows what a person will
see.

**What is approximated, and which way each approximation LEANS.** An
approximation that flatters the result is worthless, so each of these is stated
with its direction; the report repeats them.

  DIRT -> asphalt   v1 has ONE road tile kind. Every v5 unit, earned or not,
                    ships as `ROAD`. **Flatters**: 54% of the surviving network
                    is unearned frontage that a v2 document would render as
                    dirt, and here it is all pavement.
  WIDTH             v1 has no width class, but width in v5 is already GEOMETRY
                    — an avenue is three adjacent lattice tiles — so the
                    hierarchy survives the crossing intact. **Neutral.** What
                    is lost is only what a width CLASS would let a renderer add
                    (centre lines, bus lanes).
  bulb / map_edge   v1's frozen kinds are apron/dock/plaza and the shipped
                    renderer draws nothing for an unknown kind (deliberately —
                    `contract.ts` keeps `kind` a plain string). So a cul-de-sac
                    bulb and the umbilical's map-edge marker are INVISIBLE in
                    3D; their road tiles show, their dressing does not.
                    **Understates**: two of the six taxonomy kinds do not
                    render at all.
  routes            `ArterialPlan.routes` keeps each edge's units as a SET, so
                    the walk order is gone. It is recovered here by a BFS over
                    that edge's own tiles. Same pavement, reconstructed order.
                    **Neutral** for geometry; traffic may take a different lane
                    through a junction than the router did.
  plant + civic     v5 has no utility precinct. The bridge puts the plant and
                    the library/firehouse strip in the WEST MARGIN beside the
                    umbilical, which is v4's strip in the one place v5 has a
                    root. **Honest sketch, not a plan** — see the report.
  zone_style        v1 carries the theme's regex-resolved style; the bridge
                    overrides it with the precinct's TEXTURE, because district
                    texture by depth is the thing v5 is claiming and it has to
                    be visible. **Neutral, and deliberate.**
  power lines       not emitted. **Understates** — v4's map has power-line
                    tiles running from the plant and this one does not.

Everything not listed — objects, edges, joins, replay, budget, weather,
achievements, theme — is the REAL emitter's output for the same catalog,
because `city_document` is called and then only its geometry is replaced.

Usage:

    uv run python scripts/spike_city_json.py                # all render fixtures
    uv run python scripts/spike_city_json.py cap-500 random-0
"""

from __future__ import annotations

import json
import shutil
import sys
from collections import deque
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spike_fixtures import load_fixtures  # noqa: E402
from spike_streetpaint import lot_tiles  # noqa: E402
from spike_v5plan import build  # noqa: E402

from dbtycoon.export.city_json import city_document, dumps  # noqa: E402
from dbtycoon.sim.channels import DEFAULT_BINDINGS, apply_signals  # noqa: E402
from dbtycoon.sim.generator import generate_city  # noqa: E402
from dbtycoon.sim.tiles import TileKind  # noqa: E402
from dbtycoon.sim.town_endings import MAP_EDGE  # noqa: E402
from dbtycoon.sim.town_hierarchy import unit_tiles  # noqa: E402
from dbtycoon.sim.town_texture import DOWNTOWN, INDUSTRIAL, SUBURBAN  # noqa: E402
from dbtycoon.sim.town_zoning import lot_rect  # noqa: E402
from dbtycoon.theme_data import load_theme_data, theme_dir  # noqa: E402

OUT_DIR = Path(__file__).resolve().parents[1] / "spike-out"
RENDER_DIR = OUT_DIR / "render"
# The three Stephen named, plus two shapes that stress the grammar differently:
# a pure fan (one destination, twenty sources) and the biggest catalog on the
# bench. Named here rather than chosen by eye at render time.
DEFAULT_FIXTURES = ("cap-500", "random-0", "demo-tycoon", "fan-in-20", "sized-1")

# Precinct texture -> the v1 zone style that reads closest to it.
ZONE_OF = {INDUSTRIAL: "industrial", DOWNTOWN: "commercial", SUBURBAN: "residential"}

# A fixed instant, so a re-render of the same catalog produces the same
# document: `apply_signals` reads the wall clock otherwise and every age moves.
FROZEN_NOW = datetime(2026, 8, 6, 12, 0, 0, tzinfo=UTC)


def _tile_grid(b) -> list[list[TileKind]]:
    """The v5 plan as a v1 tile grid. Road first, then lots on top of it.

    Order matters: a lot that absorbed an unfronted seam line overlaps tiles the
    line would otherwise claim, and the LOT has to win — that absorption is the
    spike-4 fix and painting road last would undo it in the picture only.
    """
    grid = [[TileKind.GRASS for _ in range(b.tiles.width)] for _ in range(b.tiles.height)]

    def put(x: int, y: int, kind: TileKind) -> None:
        if 0 <= x < b.tiles.width and 0 <= y < b.tiles.height:
            grid[y][x] = kind

    for x, y in sorted(b.roads):
        put(x, y, TileKind.ROAD)
    for ending in b.endings:
        for x, y in sorted(ending.tiles()):
            put(x, y, TileKind.ROAD)
    for x, y in sorted(lot_tiles(b)):
        put(x, y, TileKind.LOT)
    return grid


def _utility_strip(b) -> tuple[tuple[int, int], tuple[int, int] | None, tuple[int, int] | None]:
    """Plant, library, firehouse — v4's western strip, hung off the umbilical.

    v5 has no civic land of its own (see the report: the answer is a utility
    PRECINCT at depth -1, and it is not built). This is the honest sketch: the
    umbilical is the one place v5 already has a root, the west margin is the one
    place there is room, and v4's strip is the shape that is not to be
    redesigned. Returns tiles inside the margin, north of the umbilical so the
    entry road stays clear.
    """
    if b.umbilical is None:
        return (1, 1), None, None
    y = b.umbilical.y
    plant = (1, max(0, y - 2))
    library = (1, y + b.umbilical.height + 1)
    firehouse = (1, y + b.umbilical.height + 4)
    inside = lambda t: 0 <= t[0] < b.tiles.width and 0 <= t[1] < b.tiles.height  # noqa: E731
    return plant, (library if inside(library) else None), (firehouse if inside(firehouse) else None)


def _route_path(b, edge) -> list[list[int]]:
    """One edge's street as an ORDERED tile path, door tile to door tile.

    `ArterialPlan.routes` stores the units it used as a sorted SET, so the walk
    is gone; a BFS over exactly those units' tiles recovers an order along the
    same pavement. Empty when the two doors are not connected through the
    edge's own units, which the caller ships as `route: []` rather than as a
    straight line nobody paved.
    """
    units = b.plan.routes.get(edge)
    if not units:
        return []
    allowed = {t for unit in units for t in unit_tiles(unit, b.tiles)}
    (sx, sy), _f = b.zone.door_of[edge[0]]
    (dx, dy), _g = b.zone.door_of[edge[1]]
    if (sx, sy) not in allowed or (dx, dy) not in allowed:
        return []
    prev: dict[tuple[int, int], tuple[int, int]] = {}
    queue = deque([(sx, sy)])
    seen = {(sx, sy)}
    while queue:
        at = queue.popleft()
        if at == (dx, dy):
            path = [at]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            return [[x, y] for x, y in reversed(path)]
        for step in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (at[0] + step[0], at[1] + step[1])
            if nxt in allowed and nxt not in seen:
                seen.add(nxt)
                prev[nxt] = at
                queue.append(nxt)
    return []


def bridge(name: str, ctx) -> dict:
    """The v5 plan as a v1 document: real emitter, geometry replaced."""
    theme = load_theme_data(theme_dir("default"))
    city = generate_city(ctx, theme.style_rules)
    apply_signals(city, ctx, DEFAULT_BINDINGS, now=FROZEN_NOW)
    doc = city_document(ctx, city, theme)

    b = build(ctx)
    texture_of = {p.pid: p.texture for p in b.precincts}
    precinct_of = {key: pid for p in b.precincts for pid in (p.pid,) for key in p.members}

    grid = _tile_grid(b)
    plant, library, firehouse = _utility_strip(b)
    grid[plant[1]][plant[0]] = TileKind.PLANT

    doc["grid"] = {
        "width": b.tiles.width,
        "height": b.tiles.height,
        "tile_kinds": doc["grid"]["tile_kinds"],
        "tiles_rle": _rle(grid),
    }
    doc["plant"] = {"x": plant[0], "y": plant[1]}
    doc["library"] = {"x": library[0], "y": library[1]} if library else None
    doc["firehouse"] = {"x": firehouse[0], "y": firehouse[1]} if firehouse else None

    lots = []
    was = {lot["object_key"]: lot for lot in doc["lots"]}
    for key in sorted(b.zone.slot_of):
        x, y, w, h = lot_rect(b.zone.slot_of[key], b.tiles, b.cover)
        record = dict(was.get(key, {}))
        texture = texture_of.get(precinct_of.get(key, ""), INDUSTRIAL)
        record.update(
            {
                "object_key": key,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "zone_style": ZONE_OF[texture],
            }
        )
        record.setdefault("target_density", 4)
        record.setdefault("powered", True)
        for absent in (
            "last_build_age_s",
            "build_status",
            "test_status",
            "freshness_status",
            "schema_drift_age_s",
        ):
            record.setdefault(absent, None)
        lots.append(record)
    doc["lots"] = lots

    # Districts: a schema's own land, as the bounding box of its precincts. A
    # schema at two depths spans both, exactly as v4's does.
    boxes: dict[str, list[int]] = {}
    for pid, rx, ry, rw, rh in b.tiles.precinct_rects:
        schema = pid.split(":", 1)[1]
        box = boxes.setdefault(schema, [rx, ry, rx + rw, ry + rh])
        box[0], box[1] = min(box[0], rx), min(box[1], ry)
        box[2], box[3] = max(box[2], rx + rw), max(box[3], ry + rh)
    doc["districts"] = [
        {"schema": schema, "x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}
        for schema, (x0, y0, x1, y1) in sorted(boxes.items())
    ]

    doc["street_features"] = [
        {"kind": e.kind, "x": e.x, "y": e.y, "facing": e.facing, "w": e.w, "h": e.h} for e in b.endings
    ]
    for record in doc["edges"]:
        record["route"] = _route_path(b, (record["src"], record["dst"]))

    xs = [lot["x"] for lot in lots] + [lot["x"] + lot["w"] - 1 for lot in lots] + [plant[0]]
    ys = [lot["y"] for lot in lots] + [lot["y"] + lot["h"] - 1 for lot in lots] + [plant[1]]
    doc["focus"] = {"min_x": min(xs), "min_y": min(ys), "max_x": max(xs), "max_y": max(ys)}
    _report(name, b, doc)
    return doc


def _rle(grid) -> list[int]:
    from dbtycoon.export.city_json import encode_rle

    return encode_rle(grid)


def _report(name: str, b, doc: dict) -> None:
    routed = sum(1 for e in doc["edges"] if e["route"])
    dirt = sum(1 for u in b.units if b.plan.surface_of[u] == "dirt")
    invisible = sum(1 for e in b.endings if e.kind in ("bulb", MAP_EDGE, "cap"))
    print(
        f"{name:<14} {doc['grid']['width']:>4}x{doc['grid']['height']:<4} "
        f"lots={len(doc['lots']):<4} features={len(doc['street_features']):<4} "
        f"(invisible in v1: {invisible})  "
        f"routes={routed}/{len(doc['edges'])}  "
        f"dirt shipped as asphalt={100 * dirt // max(len(b.units), 1)}% of units"
    )


def main() -> None:
    wanted = [a for a in sys.argv[1:] if not a.startswith("-")] or list(DEFAULT_FIXTURES)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    theme = load_theme_data(theme_dir("default"))
    for name in wanted:
        found = load_fixtures(name)
        if not found:
            raise SystemExit(f"no fixture named {name!r}")
        _fixture, ctx = found[0]
        out = RENDER_DIR / name
        out.mkdir(parents=True, exist_ok=True)
        (out / "city.json").write_text(dumps(bridge(name, ctx)))
        shutil.copy2(theme.spritesheet_path, out / theme.spritesheet_path.name)
        (out / "meta.json").write_text(
            json.dumps({"format": "database-tycoon.meta", "version": 1, "generated_at": None}, indent=2)
        )
    print(f"\ndocuments -> {RENDER_DIR}")


if __name__ == "__main__":
    main()
