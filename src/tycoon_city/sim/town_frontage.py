"""Streets v5: FRONTAGE — where a lot meets its street, and the one tile seam.

**Not wired into anything.** Split out of `town_zoning` in spike 4, at the line
law, and at the seam that was already there: `town_zoning` decides which
building stands on which piece of land, and this module decides what that piece
IS on the ground — its rectangle, its door, and which lattice unit that door
opens onto.

Two things live here and nowhere else.

  **`door_unit`** — the lot's frontage as a lattice UNIT, `(axis, line, pos)`.
  This is what makes doors the endpoints of routing (`town_arterials`) without
  routing ever seeing a tile: an arterial runs door to door in block/line
  indices, and the legal-ending taxonomy can then attach to a building's actual
  door rather than to a route stub.

  **The seam fix** — `lot_rect` lets a lot ABSORB a bounding line that carries
  no street beside it. Line widths are global by index, so a line that bounds a
  block in one precinct lands mid-block in a neighbour of a different width and
  steals a tile of its land; spike 3 measured that at 5% of grid tiles (10% on
  cap-500) and spike 4 pays for the fix with data it needed in hand anyway.
  Hierarchy widths make the defect worse before they make it better — an avenue
  is three tiles wide everywhere its line runs — which is why the two landed in
  the same round.

Imports nothing from `town_zoning`: the dependency runs one way, zoning -> here.
"""

from __future__ import annotations

from dataclasses import dataclass

from .town_blocks import H, Lattice, TileMap, V


@dataclass(frozen=True)
class Slot:
    """One buildable piece of one block, in LATTICE CELL space.

    `block` is the block's NW cell, which is unique city-wide and sorts
    row-major. `side` is the frontage this slot's door opens onto and `index`
    its position along that side. `cells` is one cell for an ordinary lot and
    every cell of the block for a big one.
    """

    block: tuple[int, int]
    side: str
    index: int
    cells: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class ZonePlan:
    """Slots in lattice space, plus the one conversion of them into tiles."""

    slot_of: dict[str, Slot]
    lot_xy: dict[str, tuple[int, int]]  # NW anchor, tile space
    door_of: dict[str, tuple[tuple[int, int], str]]  # (road tile, facing)


# --- frontage and the single lattice -> tile conversion --------------------


def _bounds(slot: Slot) -> tuple[int, int, int, int]:
    xs = [c[0] for c in slot.cells]
    ys = [c[1] for c in slot.cells]
    return min(xs), max(xs) + 1, min(ys), max(ys) + 1


def door_unit(slot: Slot) -> tuple[str, int, int]:
    """The lattice UNIT this lot's door opens onto: `(axis, line, pos)`.

    Spike 4's addition, and the reason routing never needs a tile: an arterial
    runs from one building's door to another's over `town_arterials`' unit
    graph, entirely in block/line indices. The unit is the middle cell of the
    frontage face, so a whole-block lot's door is centred on the face rather
    than at its corner.
    """
    x0, x1, y0, y1 = _bounds(slot)
    if slot.side in ("n", "s"):
        return (H, y0 if slot.side == "n" else y1, x0 + (x1 - x0 - 1) // 2)
    return (V, x0 if slot.side == "w" else x1, y0 + (y1 - y0 - 1) // 2)


LineCover = dict[tuple[str, int], frozenset[int]]


def segment_cover(lattice: Lattice) -> LineCover:
    """Which CELLS of each lattice line actually carry street.

    The input to the seam fix below, and answerable from `lattice.segments`
    alone — which is why spike 3 could name the defect and spike 4 could fix it
    for free. `scripts/spike_arterials.py` passes the post-trim UNIT set here
    instead, so a line the trim emptied stops bounding anybody's lot.
    """
    out: dict[tuple[str, int], set[int]] = {}
    for seg in lattice.segments:
        k = seg.key
        out.setdefault((k.axis, k.line), set()).update(range(k.start, k.end))
    return {key: frozenset(cells) for key, cells in out.items()}


def unit_cover(units) -> LineCover:
    """The same map built from `(axis, line, pos)` units rather than segments."""
    out: dict[tuple[str, int], set[int]] = {}
    for axis, line, pos in units:
        out.setdefault((axis, line), set()).add(pos)
    return {key: frozenset(cells) for key, cells in out.items()}


def _carries(cover: LineCover, axis: str, line: int, lo: int, hi: int) -> bool:
    cells = cover.get((axis, line))
    return bool(cells) and any(pos in cells for pos in range(lo, hi))


def lot_rect(slot: Slot, tiles: TileMap, cover: LineCover | None = None) -> tuple[int, int, int, int]:
    """`(x, y, w, h)` in tiles. A lot runs from just past its west/north street
    to just before the next line, so multi-cell lots stay contiguous.

    **The seam fix (spike 4).** Line widths are GLOBAL by index: once precincts
    differ in width, a line that bounds a block in one of them lands mid-block in
    its neighbour and takes a tile of that block's land — 5% of grid tiles on the
    spike-3 bench, 10% on cap-500 — and hierarchy widths make it worse, because
    an avenue on a line is three tiles wide everywhere that line runs. Given
    `cover` (which cells of which line actually carry street, from
    `segment_cover` or `unit_cover`) a lot ABSORBS its east and south bounding
    line when no street runs along the lot there. East/south only, so the lot to
    the west of a seam takes it and the two never overlap; a precinct's own
    frame always carries a segment, so a lot can never absorb its own kerb.
    """
    x0, x1, y0, y1 = _bounds(slot)
    x = tiles.v_at[x0] + tiles.v_w[x0]
    y = tiles.h_at[y0] + tiles.h_w[y0]
    east, south = tiles.v_at[x1], tiles.h_at[y1]
    if cover is not None:
        if not _carries(cover, V, x1, y0, y1):
            east += tiles.v_w[x1]
        if not _carries(cover, H, y1, x0, x1):
            south += tiles.h_w[y1]
    return x, y, east - x, south - y


def door_tile(slot: Slot, tiles: TileMap) -> tuple[tuple[int, int], str]:
    """The road tile the lot's door opens onto, and the way the door faces.

    Derived from `door_unit`, so the tile the render paints cyan is the same
    cell of the same line the arterial was routed to — one source of truth. It
    sits at the middle of that cell, on the LAST tile of the street rather than
    its first, so a widened avenue puts the apron on the kerb the building
    actually meets.
    """
    axis, line, pos = door_unit(slot)
    if axis == H:
        at = tiles.v_at[pos] + tiles.v_w[pos]
        mid = at + (tiles.v_at[pos + 1] - at) // 2
        if slot.side == "n":
            return (mid, tiles.h_at[line] + tiles.h_w[line] - 1), "n"
        return (mid, tiles.h_at[line]), "s"
    at = tiles.h_at[pos] + tiles.h_w[pos]
    mid = at + (tiles.h_at[pos + 1] - at) // 2
    if slot.side == "w":
        return (tiles.v_at[line] + tiles.v_w[line] - 1, mid), "w"
    return (tiles.v_at[line], mid), "e"
