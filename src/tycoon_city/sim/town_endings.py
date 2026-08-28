"""Streets v5, SPIKE 5: DRESSED ENDINGS and the map-edge umbilical.

**Not wired into anything.** `plan_dag_layout` is still the only planner the
app, the contract and the tests reach; nothing here is imported by `layout`,
`town_plan`, `city_json` or any test. The callers are `scripts/spike_arterials.py`
and `scripts/spike_city_json.py`, which render it so it can be JUDGED before a
rule earns a test.

`docs/road-grammar.md` theme 7 — *"terminations are dressed, never raw"* — and
its LEGAL-ENDING TAXONOMY table, which is the spec for this module:

    apron      ordinary building <-> street: the driveway pad at its face
    bulb       a small cluster of sibling leaves: the widened cul-de-sac cap
    plaza      important leaves (marts) and whole-block lots: the terminated
               vista, a paved forecourt against the building
    dock       source-layer tables and the plant: the industrial truck court
    map_edge   external sources/sinks: the widest road run to the grid border
               and stopped, which universally reads as "continues elsewhere"
    cap        last resort, and rare enough to be a SMELL

v4 shipped apron/dock/plaza (`town_streets.plan_street_features`) derived from
ROUTE ENDPOINTS. The difference here, and the thing zoning made possible, is
that a v5 ending hangs off a building's actual DOOR: `town_frontage.door_unit`
already decided which cell of which line a lot fronts, so the pad lands on the
kerb the building really meets instead of on wherever a path happened to stop.

**Property S7, extended (spike 5): wherever the network ENDS, a feature must
dress it — over DIRT as well as pavement.** A dirt dead end is still a dead
end, and `naked_ends` is the instrument: every leaf of the surviving unit graph
whose junction square no emitted pad covers. It is held at zero by emitting a
`cap` for anything the taxonomy's other five kinds do not reach, which is why
the number that actually judges the design is the CAP SHARE, not the naked
count. A city that is 40% caps has passed S7 and failed theme 7.

Two conventions worth stating once:

  **`facing` points at the BUILDING**, which is v4's convention and the one
  `web/src/scene/streetscape.ts` reads. It is therefore the OPPOSITE of the
  slot's side: a lot on its block's north row fronts the street to its north,
  so the pad on that street faces SOUTH toward the lot.

  **Pads are rectangles of ROAD**, never of lot. They run along the kerb, so a
  plaza spans the frontage face and an apron is one tile — a pad has no reason
  to reach into the building it serves.
"""

from __future__ import annotations

from dataclasses import dataclass

from .town_arterials import Node, Unit, ends, node_degree
from .town_blocks import H, TileMap, V
from .town_frontage import Slot, door_tile, door_unit

APRON = "apron"
BULB = "bulb"
PLAZA = "plaza"
DOCK = "dock"
MAP_EDGE = "map_edge"
CAP = "cap"

# Precedence when one building could read as two kinds. v4's order, kept: the
# plaza is the only kind that carries geometry beyond its own tile, so keeping
# it first is what makes "a pad wider than one tile is a plaza" true. The one
# open question this inherits is still open — `docs/handover.md`, "the big-raw
# -source ending precedence (dock vs plaza, a one-line flip)".
_KIND_RANK = {PLAZA: 0, DOCK: 1, BULB: 2, APRON: 3, MAP_EDGE: 4, CAP: 5}

# A door's slot side -> the compass direction from the kerb toward the lot.
TOWARD_BUILDING = {"n": "s", "s": "n", "e": "w", "w": "e"}


@dataclass(frozen=True)
class Ending:
    """One dressed road ending, in TILES. `key` is the object served, or None
    for the three kinds that dress the network rather than a building."""

    kind: str
    x: int
    y: int
    w: int
    h: int
    facing: str | None
    key: str | None

    def tiles(self) -> frozenset[tuple[int, int]]:
        return frozenset((self.x + dx, self.y + dy) for dx in range(self.w) for dy in range(self.h))


def _sort_key(e: Ending) -> tuple:
    return (e.kind, e.x, e.y, e.facing or "", e.w, e.h, e.key or "")


# --- which ending a building gets ------------------------------------------


def door_kinds(
    keys: tuple[str, ...],
    big: frozenset[str],
    depth: dict[str, int],
    important: frozenset[str],
    ships: frozenset[str] = frozenset(),
) -> dict[str, str]:
    """`key -> ending kind`, straight off the taxonomy table.

    A whole-block lot or an IMPORTANT leaf gets the plaza (the terminated-vista
    move); a SOURCE that actually ships gets the loading dock; everything else
    is an ordinary building and gets the driveway apron.

    `important` and `ships` are the caller's measured sets — nothing here may be
    a name pattern or a style rule. `scripts/spike_v5plan` uses "a sink that at
    least two things feed" for the first and "has an outgoing lineage edge" for
    the second. That second condition is not decoration: v4 tested `depth == 0`
    alone, and on a catalog with NO lineage that makes every building in the
    city a loading dock — the first spike-5 sheet came out solid orange, 633
    docks over the bench. A table nothing reads and that reads nothing is not a
    source layer, it is a building.
    """
    out: dict[str, str] = {}
    for key in sorted(keys):
        if key in big or key in important:
            out[key] = PLAZA
        elif depth.get(key, 0) == 0 and key in ships:
            out[key] = DOCK
        else:
            out[key] = APRON
    return out


# --- pad geometry -----------------------------------------------------------


def _leaves(units: tuple[Unit, ...]) -> frozenset[Node]:
    degree = node_degree(units)
    return frozenset(node for node, n in degree.items() if n == 1)


def junction_rect(node: Node, tiles: TileMap) -> tuple[int, int, int, int]:
    """The tile square where a vertical and a horizontal line cross — which is
    where a road that just stops actually stops. Zero-width when one of the two
    lines resolved at width 0, in which case there is nothing to dress."""
    v, h = node
    return tiles.v_at[v], tiles.h_at[h], tiles.v_w[v], tiles.h_w[h]


def _door_pad(slot: Slot, tiles: TileMap, kind: str, leaves: frozenset[Node]) -> tuple[int, int, int, int]:
    """The rectangle a door's ending covers, along the kerb it opens onto.

    An APRON is one tile — a driveway is a notch, not a forecourt. A PLAZA or a
    DOCK spans the frontage cell, so a whole-block lot gets a court the width of
    its face rather than a one-tile nick.

    Either way the pad EXTENDS to a junction square at the end of its own unit
    when that junction is a leaf. That is the S7 extension made geometric: a
    street that runs past a door and then stops has to be dressed where it
    stops, and "the driveway is at the end of the cul-de-sac" is the reading
    both real suburbs and every sim use for exactly this shape.
    """
    axis, line, pos = door_unit(slot)
    (dx, dy), _side = door_tile(slot, tiles)
    at, width = (tiles.v_at, tiles.v_w) if axis == H else (tiles.h_at, tiles.h_w)
    along = dx if axis == H else dy
    # A node is `(v_line, h_line)`, so which coordinate `pos` is depends on the
    # axis: an `h` unit runs along vertical lines and a `v` unit along horizontal
    # ones. Getting this backwards puts the leaf extension on the wrong end.
    near, far = ((pos, line), (pos + 1, line)) if axis == H else ((line, pos), (line, pos + 1))
    if kind == APRON:
        lo = hi = along
    else:  # the whole frontage cell: a forecourt the width of the face
        lo, hi = at[pos] + width[pos], at[pos + 1] - 1
    if near in leaves:
        lo = at[pos]
    if far in leaves:
        hi = at[pos + 1] + width[pos + 1] - 1
    lo, hi = min(lo, along), max(hi, along)
    if axis == H:
        return lo, dy, hi - lo + 1, 1
    return dx, lo, 1, hi - lo + 1


def _unit_rect(unit: Unit, tiles: TileMap) -> tuple[int, int, int, int]:
    """One unit's whole footprint, both junction squares included — the bulb."""
    axis, line, pos = unit
    if axis == V:
        y0 = tiles.h_at[pos]
        y1 = tiles.h_at[pos + 1] + tiles.h_w[pos + 1]
        return tiles.v_at[line], y0, max(1, tiles.v_w[line]), max(1, y1 - y0)
    x0 = tiles.v_at[pos]
    x1 = tiles.v_at[pos + 1] + tiles.v_w[pos + 1]
    return x0, tiles.h_at[line], max(1, x1 - x0), max(1, tiles.h_w[line])


# --- the umbilical: one root, at the map edge -------------------------------


@dataclass(frozen=True)
class Umbilical:
    """Theme 5's single root: the widest road, run west to the grid border.

    `tiles` is the pavement it adds OUTSIDE the lattice (the west margin only —
    the lattice itself is untouched, so the one-prefix-sum discipline holds).
    `node` is the lattice intersection it lands on, which is what makes the
    whole network drain to one entry rather than to nothing.
    """

    node: Node
    road: frozenset[tuple[int, int]]
    y: int
    height: int


def plan_umbilical(tiles: TileMap, units: tuple[Unit, ...]) -> Umbilical | None:
    """The map-edge connection: run the WIDEST road that reaches the west frame
    out to x=0 and stop.

    v5 has had no root at all — no plant, no civic strip, no outside connection
    — and `docs/road-grammar.md` theme 5 is emphatic that this is what makes a
    network read as one city instead of as islands (Anno's trading post, Cities:
    Skylines' outside highway, W&R's border crossing).

    West, because the depth columns run west->east and depth 0 is where data
    enters the catalog; the widest road that gets there, because the umbilical
    that the network drains to cannot be an alley. The road is drawn at that
    line's own resolved width, so it meets the city flush and needs no flare.
    """
    west = min((line for axis, line, _pos in units if axis == V), default=None)
    if west is None or tiles.v_at[west] <= 0:
        return None
    candidates = [line for axis, line, pos in units if axis == H and pos == west and tiles.h_w[line] > 0]
    if not candidates:
        return None
    line = min(candidates, key=lambda ln: (-tiles.h_w[ln], ln))
    y0, height = tiles.h_at[line], tiles.h_w[line]
    road = frozenset((x, y) for x in range(0, tiles.v_at[west]) for y in range(y0, y0 + height))
    return Umbilical(node=(west, line), road=road, y=y0, height=height)


# --- the whole taxonomy, emitted -------------------------------------------


def plan_endings(
    tiles: TileMap,
    units: tuple[Unit, ...],
    slot_of: dict[str, Slot],
    kinds: dict[str, str],
    stubs: frozenset[Unit],
    umbilical: Umbilical | None = None,
) -> tuple[Ending, ...]:
    """Every ending in the city, dressed. Deterministic and sorted.

    Order of emission is the order of the taxonomy's authority: doors first
    (they know which building they serve), then the suburban cul-de-sac bulbs,
    then the map-edge umbilical — and only then a `cap` for each leaf square
    none of those reached. The cap count is therefore the honest measure of how
    much of the network the grammar could NOT explain.
    """
    leaves = _leaves(units)
    live = set(units)
    out: dict[tuple[int, int, int, int], Ending] = {}

    def add(e: Ending) -> None:
        box = (e.x, e.y, e.w, e.h)
        current = out.get(box)
        if current is None or _KIND_RANK[e.kind] < _KIND_RANK[current.kind]:
            out[box] = e

    for key in sorted(slot_of):
        slot = slot_of[key]
        kind = kinds.get(key, APRON)
        x, y, w, h = _door_pad(slot, tiles, kind, leaves)
        add(Ending(kind, x, y, w, h, TOWARD_BUILDING[slot.side], key))

    for unit in sorted(stubs & live):
        if any(node in leaves for node in ends(unit)):
            x, y, w, h = _unit_rect(unit, tiles)
            add(Ending(BULB, x, y, w, h, None, None))

    if umbilical is not None and umbilical.road:
        border = min(x for x, _y in umbilical.road)
        add(
            Ending(
                MAP_EDGE,
                border,
                umbilical.y,
                1,
                umbilical.height,
                "e",
                None,
            )
        )

    covered: set[tuple[int, int]] = set()
    for e in out.values():
        covered |= e.tiles()
    for node in sorted(leaves):
        x, y, w, h = junction_rect(node, tiles)
        if w and h and not covered & {(x + dx, y + dy) for dx in range(w) for dy in range(h)}:
            add(Ending(CAP, x, y, w, h, None, None))

    return tuple(sorted(out.values(), key=_sort_key))


def naked_ends(units: tuple[Unit, ...], tiles: TileMap, endings: tuple[Ending, ...]) -> tuple[Node, ...]:
    """Property S7, extended and measured on the GROUND rather than on intent.

    A leaf of the surviving unit graph — paved or dirt, it makes no difference —
    whose junction square no emitted pad covers. Read off the pads themselves,
    not off the set that produced them, so a pad computed at the wrong end of a
    widened avenue shows up here instead of being asserted away.
    """
    covered: set[tuple[int, int]] = set()
    for e in endings:
        covered |= e.tiles()
    bad: list[Node] = []
    for node in sorted(_leaves(units)):
        x, y, w, h = junction_rect(node, tiles)
        if not w or not h:
            continue
        if not covered & {(x + dx, y + dy) for dx in range(w) for dy in range(h)}:
            bad.append(node)
    return tuple(bad)


def kind_histogram(endings: tuple[Ending, ...]) -> dict[str, int]:
    """How many of each kind — the sheet's caption and the cap smell."""
    out = dict.fromkeys(_KIND_RANK, 0)
    for e in endings:
        out[e.kind] = out.get(e.kind, 0) + 1
    return out
