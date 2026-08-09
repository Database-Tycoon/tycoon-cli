"""Spike 4's instruments: the numbers that judge a routed v5 network.

Not a test — the measuring half of `scripts/spike_arterials.py`, split out at
the line law. Every function here reads a finished plan and reports; none of
them decides anything, and none of them may repair a defect it finds. A nonzero
naked-ending count or a downtown precinct with no closed loop is the FINDING.

The one number with a v4 counterpart is sprawl. v4 priced it as channel width
per distinct DESTINATION (`town_streets`: "each *distinct* destination group
widens its channel by TRACK_PITCH, so a genuinely tangled DAG still paves itself
into an ugly, sprawling city while a clean pipeline earns a tight village"). v5
has no channels, so the equivalent is paved length per distinct destination —
and the question that matters for the game thesis is not whether the two numbers
agree but whether they RANK the 38 fixtures the same way. `spearman` is that
check.
"""

from __future__ import annotations

from dbtycoon.sim.town_arterials import DIRT, PAVED, Unit, ends, node_degree
from dbtycoon.sim.town_hierarchy import ALLEY, AVENUE, STREET, cyclomatic, precinct_units
from dbtycoon.sim.town_texture import DOWNTOWN


def surface_split(plan, units: tuple[Unit, ...]) -> tuple[int, int]:
    """`(paved, dirt)` unit counts over the SURVIVING units."""
    paved = sum(1 for u in units if plan.surface_of[u] == PAVED)
    return paved, sum(1 for u in units if plan.surface_of[u] == DIRT)


def class_histogram(width: dict[Unit, int]) -> tuple[int, int, int]:
    """`(alleys, streets, avenues)` in units. Avenues above ~15% means the
    buckets are wrong, not the rule."""
    return tuple(sum(1 for c in width.values() if c == want) for want in (ALLEY, STREET, AVENUE))


def loops_by_texture(precincts, units: tuple[Unit, ...]) -> dict[str, tuple[int, int, int]]:
    """`texture -> (precincts, precincts with a closed loop, total cyclomatic)`.

    Road-grammar theme 2: closed loops in the core are the #1 city tell, and an
    all-dead-end network reads as a plumbing diagram. Downtown is the texture
    that must not come out a tree.
    """
    out: dict[str, list[int]] = {}
    for precinct in precincts:
        mu = cyclomatic(precinct_units(precinct, units))
        row = out.setdefault(precinct.texture, [0, 0, 0])
        row[0] += 1
        row[1] += 1 if mu > 0 else 0
        row[2] += mu
    return {texture: tuple(row) for texture, row in sorted(out.items())}


def downtown_treed(precincts, units: tuple[Unit, ...]) -> int:
    """Downtown precincts with NO closed loop — the failure this checks for."""
    return sum(1 for p in precincts if p.texture == DOWNTOWN and cyclomatic(precinct_units(p, units)) == 0)


def junction_mix(units: tuple[Unit, ...]) -> tuple[int, int, int]:
    """`(leaves, T-junctions, 4-ways)`. Theme 6 wants T-junctions dominant and
    4-ways clustered in the core; this is the raw count that says whether the
    lattice has produced a plumbing diagram or a street plan."""
    degree = node_degree(units)
    counts = [0, 0, 0]
    for value in degree.values():
        if value == 1:
            counts[0] += 1
        elif value == 3:
            counts[1] += 1
        elif value >= 4:
            counts[2] += 1
    return tuple(counts)


def road_tiles(units: tuple[Unit, ...], tiles, unit_tiles) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for unit in units:
        out.update(unit_tiles(unit, tiles))
    return out


def seam_geometry(precincts, tiles) -> int:
    """Spike 3's seam, unchanged: tiles taken by a lattice line that runs INSIDE
    somebody's block. The BEFORE number for the spike-4 fix.

    Copied verbatim from `spike_zoning.seam_tiles` rather than imported, so the
    before/after comparison cannot drift with a later edit to that script.
    """
    total = 0
    for p in precincts:
        inner_v = [p.cell_x + i for i in range(p.cells_w) if i % p.block_w]
        inner_h = [p.cell_y + i for i in range(p.cells_h) if i % p.block_h]
        east, south = p.cell_x + p.cells_w, p.cell_y + p.cells_h
        width = tiles.v_at[east] + tiles.v_w[east] - tiles.v_at[p.cell_x]
        height = tiles.h_at[south] + tiles.h_w[south] - tiles.h_at[p.cell_y]
        total += sum(tiles.v_w[i] for i in inner_v) * height
        total += sum(tiles.h_w[i] for i in inner_h) * width
    return total


def orphan_tiles(precincts, tiles, roads: set[tuple[int, int]], lots: set[tuple[int, int]]) -> int:
    """The seam AFTER the fix, measured the honest way: settled tiles that are
    neither street nor lot nor an empty block slot.

    A seam tile a lot absorbed is now lot, so it stops counting. What is left is
    land inside a precinct that belongs to nobody — which is what the defect
    actually was.
    """
    total = 0
    for p in precincts:
        east, south = p.cell_x + p.cells_w, p.cell_y + p.cells_h
        x0, y0 = tiles.v_at[p.cell_x], tiles.h_at[p.cell_y]
        x1 = tiles.v_at[east] + tiles.v_w[east]
        y1 = tiles.h_at[south] + tiles.h_w[south]
        inner_v = {p.cell_x + i for i in range(p.cells_w) if i % p.block_w}
        inner_h = {p.cell_y + i for i in range(p.cells_h) if i % p.block_h}
        bands: set[tuple[int, int]] = set()
        for i in sorted(inner_v):
            for x in range(tiles.v_at[i], tiles.v_at[i] + tiles.v_w[i]):
                bands.update((x, y) for y in range(y0, y1))
        for i in sorted(inner_h):
            for y in range(tiles.h_at[i], tiles.h_at[i] + tiles.h_w[i]):
                bands.update((x, y) for x in range(x0, x1))
        total += len(bands - roads - lots)
    return total


def land_shares(tiles, roads: set[tuple[int, int]], lots: set[tuple[int, int]]) -> tuple[int, int]:
    """`(paved%, built%)` of the SETTLED land — the precincts' own footprint,
    never the whole grid, so margins and open ground cannot flatter either.

    The number spike 3 left at paved 55 / built 36, and the one hierarchy widths
    can only make worse: a two-tile street beside a two-tile lot is the same 1:1
    trade `cell_size` was doubled to escape. If it runs away, widths are being
    bought with the city.
    """
    land = {
        (x, y) for _pid, rx, ry, rw, rh in tiles.precinct_rects for x in range(rx, rx + rw) for y in range(ry, ry + rh)
    }
    if not land:
        return 0, 0
    return 100 * len(land & roads) // len(land), 100 * len(land & lots) // len(land)


def line_width_mix(tiles) -> tuple[int, int, int]:
    """How many LINES resolved at one, two and three tiles. Width is per line —
    that is the architecture — so this is the histogram that says what the eye
    will actually see."""
    counts = [0, 0, 0]
    for width in list(tiles.v_w) + list(tiles.h_w):
        if 1 <= width <= 3:
            counts[width - 1] += 1
    return tuple(counts)


def paved_per_destination(paved_tiles: int, edges: list[tuple[str, str]]) -> float:
    """v4's sprawl signal, restated for a network with no channels."""
    destinations = len({d for _s, d in edges})
    return paved_tiles / destinations if destinations else 0.0


def v4_per_destination(plan, edges: list[tuple[str, str]]) -> float:
    """The same ratio off `plan_dag_layout`, so the ranking comparison is like
    for like: v4's road tiles are its routes' interiors plus its lane tiles."""
    road = {t for route in plan.routes.values() for t in route[1:-1]} | set(plan.lane_tiles)
    destinations = len({d for _s, d in edges})
    return len(road) / destinations if destinations else 0.0


def _ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2 + 1
        for k in range(i, j + 1):
            out[order[k]] = shared
        i = j + 1
    return out


def spearman(a: list[float], b: list[float]) -> float:
    """Rank correlation, ties averaged. An INSTRUMENT, not a rule — the floats
    here never touch geometry.

    The question it answers: does a clean pipeline still earn a tighter city
    than a tangled one? If v5 reorders the bench against v4, the game thesis
    ("flow efficiency is the scoreboard") stops being carried by the picture.
    """
    if len(a) < 2:
        return 0.0
    ra, rb = _ranks(a), _ranks(b)
    n = len(a)
    mean_a, mean_b = sum(ra) / n, sum(rb) / n
    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(ra, rb, strict=True))
    var_a = sum((x - mean_a) ** 2 for x in ra)
    var_b = sum((y - mean_b) ** 2 for y in rb)
    return cov / (var_a * var_b) ** 0.5 if var_a and var_b else 0.0


def leaf_units(units: tuple[Unit, ...]) -> tuple[Unit, ...]:
    degree = node_degree(units)
    return tuple(u for u in units if any(degree[n] == 1 for n in ends(u)))


# --- spike 5's instruments -------------------------------------------------


def junction_squares(units: tuple[Unit, ...], tiles) -> tuple[int, int, int]:
    """`(total slab tiles, biggest single slab, count of 3x3 slabs)`.

    THE instrument for the avenue-crossing defect. Where a vertical line `w`
    tiles wide crosses a horizontal one `h` tiles wide the intersection is a
    solid `w*h` square of pavement, and spike 4's sheets have several 3x3 ones
    plus two full-length three-tile lines feeding them — which is the asphalt
    plaza Stephen condemned on 2026-08-05, at a different scale. Counted only
    where BOTH lines are wider than a single tile, because a 1x1 crossing is
    just a street corner.
    """
    v_at: dict[int, set[int]] = {}
    h_at: dict[int, set[int]] = {}
    for axis, line, pos in units:
        target = v_at if axis == "v" else h_at
        target.setdefault(line, set()).update((pos, pos + 1))
    total = biggest = wide = 0
    for v, rows in sorted(v_at.items()):
        for h in sorted(rows):
            if h not in h_at or v not in h_at[h]:
                continue
            area = tiles.v_w[v] * tiles.h_w[h]
            if tiles.v_w[v] < 2 or tiles.h_w[h] < 2:
                continue
            total += area
            biggest = max(biggest, area)
            wide += 1 if area >= 9 else 0
    return total, biggest, wide


def width_tile_shares(units: tuple[Unit, ...], tiles, unit_tiles) -> tuple[int, int]:
    """`(% of road TILES on a 3-tile line, % of UNITS classed avenue)`'s first
    half — the second is `class_histogram`'s.

    The two disagreeing is the cost of a global line width, stated as a number
    rather than argued about: 10% of units came out avenue on the spike-4 bench
    and far more than 10% of the pavement was painted three tiles wide.
    """
    road = wide = 0
    for unit in units:
        span = len(unit_tiles(unit, tiles))
        road += span
        axis, line, _pos = unit
        if (tiles.v_w[line] if axis == "v" else tiles.h_w[line]) >= 3:
            wide += span
    return (100 * wide // road if road else 0), road


def components(units: tuple[Unit, ...]) -> int:
    """Connected components of the road network. Theme 5 wants ONE: a
    disconnected subnetwork reads as an island, and the umbilical only means
    "the whole network drains to one entry" if there is one network."""
    if not units:
        return 0
    parent: dict[tuple[int, int], tuple[int, int]] = {}

    def find(node):
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for unit in units:
        a, b = (find(node) for node in ends(unit))
        if a != b:
            parent[a] = b
    return len({find(node) for unit in units for node in ends(unit)})


def footprint_fill(tiles) -> int:
    """% of the settled BOUNDING BOX that is actually precinct land.

    The ragged-footprint instrument: spike 4 reported L- and T-shaped cities
    with large empty grass quadrants from the depth-column wrap. A city that
    fills its own bounding box reads as a city; one at 60% reads as two.
    """
    land = {
        (x, y) for _pid, rx, ry, rw, rh in tiles.precinct_rects for x in range(rx, rx + rw) for y in range(ry, ry + rh)
    }
    if not land:
        return 0
    xs = [x for x, _y in land]
    ys = [y for _x, y in land]
    box = (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)
    return 100 * len(land) // box


__all__ = [
    "AVENUE",
    "STREET",
    "class_histogram",
    "components",
    "footprint_fill",
    "junction_squares",
    "leaf_ends",
    "width_tile_shares",
    "downtown_treed",
    "junction_mix",
    "land_shares",
    "line_width_mix",
    "leaf_units",
    "loops_by_texture",
    "orphan_tiles",
    "paved_per_destination",
    "road_tiles",
    "seam_geometry",
    "spearman",
    "surface_split",
    "v4_per_destination",
]


def leaf_ends(units: tuple[Unit, ...]) -> tuple[tuple[int, int], ...]:
    """Every NODE exactly one unit meets — the places the network actually ends.

    Reported beside the naked-ending count because the two together are the
    honest statement. On the spike-5 bench this comes out at 2 over 38 fixtures:
    a v5 street runs frame to frame past its buildings' doors and hardly ever
    stops, so property S7 is satisfied almost vacuously and the taxonomy earns
    its keep at the DOOR rather than at the road end.
    """
    degree = node_degree(units)
    return tuple(sorted(node for node, n in degree.items() if n == 1))
