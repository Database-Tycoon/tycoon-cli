"""Spike 4's paint: the routed network as pixels, and the A/B decision sheet.

Not a test — the drawing half of `scripts/spike_arterials.py`, split out at the
line law. One pixel per tile, and the ONE rule that matters here: pavement is
coloured by the tile width its line actually resolved at, never by the class the
measure gave the unit. A line index gets a single width out of the prefix sum,
so a unit the measure called an alley on a line an avenue widened really is
three tiles of ground; colouring it by its class would make the picture disagree
with the geometry it is a picture of, and this repo judges by pictures.

Dirt is earth-coloured and never brightens: unearned frontage must not be
mistakable for an arterial at thumbnail size, which is the size every v5
judgement has been made at.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spike_lattice import fit  # noqa: E402
from spike_streetmetrics import class_histogram, surface_split  # noqa: E402

from dbtycoon.sim.town_arterials import DIRT, JOIN  # noqa: E402
from dbtycoon.sim.town_hierarchy import spine_run, unit_tiles  # noqa: E402
from dbtycoon.sim.town_texture import DOWNTOWN, INDUSTRIAL, SUBURBAN  # noqa: E402
from dbtycoon.sim.town_zoning import lot_rect  # noqa: E402

# `Built` is `spike_arterials`' harness object; importing it back would make the
# two scripts circular, so it is duck-typed here.
Built = object

COL_GRASS = (58, 132, 66)
LAND = {INDUSTRIAL: (96, 68, 46), DOWNTOWN: (54, 60, 86), SUBURBAN: (62, 96, 56)}
# Surface first, then width. Dirt is earth-coloured and never gets brighter:
# unearned access must not be mistakable for an arterial at thumbnail size.
COL_DIRT = (128, 106, 74)
COL_JOIN = (150, 120, 170)
# Keyed on the RESOLVED TILE WIDTH, not on the unit's class. A line index gets
# ONE width from the prefix sum, so a unit the measure called an alley on a line
# an avenue widened really is three tiles of ground; colouring it by its class
# would make the picture disagree with the geometry it is a picture of.
PAVED_BY_WIDTH = {1: (120, 122, 130), 2: (176, 178, 186), 3: (240, 240, 246)}
COL_LOT = ((216, 202, 170), (188, 174, 142))
COL_BIG = (198, 92, 70)
COL_DOOR = (90, 210, 230)
COL_NAKED = (255, 0, 255)

# SPIKE 5: the legal-ending taxonomy, one colour per kind, painted OVER the
# pavement so a sheet answers "is every ending dressed" by eye. CAP is loud on
# purpose — the taxonomy calls it a last resort that should be rare enough to be
# a smell, so it has to be visible at thumbnail size when it is not.
COL_ENDING = {
    "apron": (150, 200, 120),
    "bulb": (250, 210, 90),
    "plaza": (235, 235, 250),
    "dock": (230, 130, 60),
    "map_edge": (120, 140, 255),
    "cap": (255, 0, 255),
}

# --- the picture -----------------------------------------------------------


def arterial_image(b: Built) -> Image.Image:
    """One pixel per tile, painted in the order a defect must survive: land,
    dirt, pavement by width class, lots, doors."""
    img = Image.new("RGB", (max(b.tiles.width, 1), max(b.tiles.height, 1)), COL_GRASS)
    px = img.load()

    def put(x: int, y: int, colour) -> None:
        if 0 <= x < img.width and 0 <= y < img.height:
            px[x, y] = colour

    texture_of = {p.pid: p.texture for p in b.lattice.precincts}
    for pid, x, y, w, h in b.tiles.precinct_rects:
        colour = LAND[texture_of[pid]]
        for ix in range(x, x + w):
            for iy in range(y, y + h):
                put(ix, iy, colour)
    order = {DIRT: 0, JOIN: 1}
    for unit in sorted(b.units, key=lambda u: (order.get(b.plan.surface_of[u], 2), b.width[u], u)):
        surface = b.plan.surface_of[unit]
        colour = (
            COL_DIRT
            if surface == DIRT
            else COL_JOIN
            if surface == JOIN
            else PAVED_BY_WIDTH[min(3, max(1, _band(unit, b.tiles)))]
        )
        for x, y in unit_tiles(unit, b.tiles):
            put(x, y, colour)
    # The umbilical is pavement OUTSIDE the lattice, so it is painted from its
    # own tile set rather than from a unit — the west margin's three tiles that
    # say "this network continues off the map".
    if getattr(b, "umbilical", None) is not None:
        for x, y in sorted(b.umbilical.road):
            put(x, y, PAVED_BY_WIDTH[3])
    naked = naked_lots(b)
    for key in sorted(b.zone.slot_of):
        slot = b.zone.slot_of[key]
        x, y, w, h = lot_rect(slot, b.tiles, b.cover)
        if key in naked:
            colour = COL_NAKED
        elif len(slot.cells) > 1:
            colour = COL_BIG
        else:
            colour = COL_LOT[(slot.index + (0 if slot.side in "nw" else 1)) % 2]
        for ix in range(x, x + w):
            for iy in range(y, y + h):
                put(ix, iy, colour)
    for key in sorted(b.zone.door_of):
        (dx, dy), _facing = b.zone.door_of[key]
        put(dx, dy, COL_DOOR)
    # Endings last: they are the thing spike 5 exists to show, and a pad that
    # landed on a lot instead of on its kerb has to be visible as such.
    for ending in getattr(b, "endings", ()):
        colour = COL_ENDING.get(ending.kind)
        if colour is None:
            continue
        for x, y in sorted(ending.tiles()):
            put(x, y, colour)
    return img


def _band(unit, tiles) -> int:
    """The tile width the unit's line actually resolved at."""
    axis, line, _pos = unit
    return tiles.v_w[line] if axis == "v" else tiles.h_w[line]


def naked_lots(b: Built) -> set[str]:
    """Lots with no road tile touching them, measured against the ACTUAL
    surviving pavement — the trim could in principle strand one, and the
    instrument has to be able to say so."""
    out: set[str] = set()
    for key, slot in sorted(b.zone.slot_of.items()):
        x, y, w, h = lot_rect(slot, b.tiles, b.cover)
        lot = {(ix, iy) for ix in range(x, x + w) for iy in range(y, y + h)}
        touching = {n for t in lot for n in ((t[0] + 1, t[1]), (t[0] - 1, t[1]), (t[0], t[1] + 1), (t[0], t[1] - 1))}
        if not (touching - lot) & b.roads:
            out.add(key)
    return out


def lot_tiles(b: Built) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for slot in b.zone.slot_of.values():
        x, y, w, h = lot_rect(slot, b.tiles, b.cover)
        out |= {(ix, iy) for ix in range(x, x + w) for iy in range(y, y + h)}
    return out


def ab_sheet(pairs: list[tuple[str, Image.Image, Image.Image, str, str]], out: Path) -> None:
    """The `WIDTH_MEASURE` decision sheet: the same city under both candidates,
    side by side, at the biggest size that fits. Stephen picks from this."""
    box, pad = 300, 10
    cell_w, cell_h = 2 * box + 3 * pad, box + 46
    sheet = Image.new("RGB", (cell_w, len(pairs) * cell_h + 46), (26, 28, 32))
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 8), "streets v5 SPIKE 4 - WIDTH_MEASURE, side by side", fill=(232, 232, 236))
    draw.text(
        (pad, 24),
        "LEFT (a) carriers = distinct lineage edges over the segment   |   "
        "RIGHT (b) closure = downstream dependency count",
        fill=(150, 152, 160),
    )
    for i, (name, left, right, cap_a, cap_b) in enumerate(pairs):
        y = 46 + i * cell_h
        for j, (img, cap) in enumerate(((left, cap_a), (right, cap_b))):
            thumb = fit(img, box)
            x = pad + j * (box + pad)
            sheet.paste(thumb, (x + (box - thumb.width) // 2, y + (box - thumb.height) // 2))
            draw.rectangle([x - 1, y - 1, x + box, y + box], outline=(70, 72, 80))
            draw.text((x, y + box + 4), f"{name}  {cap}", fill=(232, 232, 236))
    sheet.save(out)


def row_caption(b: Built, measure: str) -> str:
    paved, dirt = surface_split(b.plan, b.units)
    alley, street, avenue = class_histogram(b.width)
    total = max(alley + street + avenue, 1)
    return (
        f"{b.tiles.width}x{b.tiles.height} paved={paved}/{paved + dirt} "
        f"a{100 * alley // total}/s{100 * street // total}/v{100 * avenue // total} "
        f"spine={spine_run(b.width)}"
    )
