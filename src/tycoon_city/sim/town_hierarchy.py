"""Streets v5, SPIKE 4: HIERARCHY WIDTHS and the STEP-DOWN RULE.

**Not wired into anything.** Reachable from `scripts/spike_arterials.py` and
nowhere else; `plan_dag_layout` is untouched.

`docs/road-grammar.md` theme 1, and it calls this the strongest single "reads as
a city" fix: *"2-3 road widths; thin roads always meet medium before thick. One
continuous spine plus ribs is the single strongest city tell."*

Three width classes, and the number that produces them is MEASURED, never
styled:

    1  alley    a spur, or unearned frontage (dirt is always an alley)
    2  street   ordinary lineage
    3  avenue   the trunks a lot of the warehouse hangs off

**`WIDTH_MEASURE` is Stephen's call and this module does not make it.** Both
candidates are computed in `town_arterials` — `measure_carriers` (distinct
lineage edges over the unit, continuous with v4's "two models merging becomes a
two lane road") and `measure_closure` (downstream-closure size, road-grammar's
literal wording) — and `classify` takes whichever it is handed with its own
bucket edges. The spike renders both side by side.

The step-down fixpoint is the rule proper: an ALLEY incident to an AVENUE where
no STREET is incident gets promoted to a street, repeatedly until nothing moves.
Driveways are exempt, because a lot's door onto an avenue is an apron and the
apron IS the transition — and in v5 a driveway is not a segment at all (the door
opens straight onto the street tile), so the only exempt units are the suburban
cul-de-sac stubs, which are literal driveways serving one block.

Everything here is integer arithmetic over lattice indices. The widths come out
as a per-LINE map for `resolve_coordinates`, which is the whole architectural
claim: nothing reserved width before routing, and the prefix sum still runs
exactly once, last.
"""

from __future__ import annotations

from .town_arterials import DIRT, ArterialPlan, Unit, ends, node_degree
from .town_blocks import H, V

ALLEY, STREET, AVENUE = 1, 2, 3

# Tiles a class resolves to. 1/2/3 rather than 1/1/2: the hierarchy has to be
# legible at THUMBNAIL size, which is where every v5 judgement has been made.
WIDTH_TILES = {ALLEY: 1, STREET: 2, AVENUE: 3}

# Bucket edges per candidate measure, as (street_from, avenue_from): a unit
# whose measure is below `street_from` is an alley, below `avenue_from` a
# street, at or above it an avenue. Avenues must stay a clear minority (~15%
# of surfaced units) or the buckets are wrong, not the rule.
BUCKETS = {
    "carriers": (3, 8),
    "closure": (2, 4),
}

# **Stephen's call, 2026-08-06, from spike 4's side-by-side PNGs: CARRIERS.**
# It is the default here and in every spike script; `closure` stays reachable
# behind `--measure closure` and is not dead code.
#
# The caveat he attached, recorded so the re-run actually happens: **revisit
# against a real catalog before 1.0, because this bench is shallow and shallow
# flatters carriers.** Nothing on the 38 fixtures is deeper than a handful of
# layers, so almost every downstream closure collapses toward 1-4 and `closure`
# has nearly nothing to say; a 12-layer warehouse would spread it out and could
# well pick the other trunk. The A/B is `--ab`, and it costs one command.
WIDTH_MEASURE = "carriers"

# THE JUNCTION RULE (spike 5, road-grammar theme 6: "wide roads cross at
# aligned right angles" — and no more often than that).
#
# Width is per LINE INDEX and a line index is global, so ONE avenue unit widens
# its whole line from margin to margin. Spike 4 shipped that and the sheets show
# what it costs: on fan-in-20 and sprawl-12 the trunk plus the north arterial
# resolve as two full-length three-tile lines whose crossing is a 3x3 white
# square, and the pair reads as the asphalt plaza Stephen condemned on
# 2026-08-05 — the same defect at a different scale.
#
# Two conditions, both cheap and both in lattice space:
#   MAJORITY  a line may only resolve at avenue width if avenue units cover at
#             least half of its own length. That is what stops a short trunk
#             from painting a runway across the whole map, and it is the honest
#             reading of a global width: the line IS what most of it carries.
#   COUNT     at most `AVENUE_LINES_PER_AXIS` avenue lines per axis, the ones
#             with the longest unbroken avenue run. Theme 1 asks for ONE
#             continuous spine plus ribs, so one boulevard each way is the
#             shape, and it caps avenue-crosses-avenue at a single junction.
# A line that loses either test resolves at STREET, never below: it keeps the
# class its own traffic earned, it just stops being three tiles of white.
AVENUE_LINES_PER_AXIS = 1


def classify(
    plan: ArterialPlan,
    measure: dict[Unit, int],
    buckets: tuple[int, int],
    units: tuple[Unit, ...] | None = None,
) -> dict[Unit, int]:
    """Width class per unit from one measure. Dirt is always an alley.

    Pavement is EARNED (Stephen's rule: every lot fronts a street, but
    non-lineage access renders as dirt), so an unearned unit can never buy a
    width class off the back of a neighbour's traffic.
    """
    street_from, avenue_from = buckets
    live = plan.units if units is None else units
    out: dict[Unit, int] = {}
    for unit in live:
        value = 0 if plan.surface_of[unit] == DIRT else measure.get(unit, 0)
        out[unit] = AVENUE if value >= avenue_from else STREET if value >= street_from else ALLEY
    return out


def _by_node(width: dict[Unit, int]) -> dict[tuple[int, int], set[int]]:
    incident: dict[tuple[int, int], set[int]] = {}
    for unit, cls in width.items():
        for node in ends(unit):
            incident.setdefault(node, set()).add(cls)
    return incident


def step_down(width: dict[Unit, int], exempt: frozenset[Unit]) -> dict[Unit, int]:
    """Promote alleys so that thin never meets thick directly. To a fixpoint.

    At a junction where an AVENUE arrives and no STREET does, every non-exempt
    ALLEY becomes a STREET. Promoting one alley can satisfy its far node too,
    or expose a new avenue-meets-alley junction; iterating is cheaper than
    reasoning about which, and the fixpoint is reached because the rule only
    ever raises a class and the classes are bounded.
    """
    out = dict(width)
    moving = True
    while moving:
        moving = False
        incident = _by_node(out)
        promote: set[Unit] = set()
        for unit, cls in out.items():
            if cls != ALLEY or unit in exempt:
                continue
            for node in ends(unit):
                classes = incident[node]
                if AVENUE in classes and STREET not in classes:
                    promote.add(unit)
                    break
        for unit in promote:
            out[unit] = STREET
            moving = True
    return out


def step_down_violations(width: dict[Unit, int], exempt: frozenset[Unit]) -> tuple[tuple[int, int], ...]:
    """The junctions the rule still fails at — must be empty after `step_down`."""
    incident = _by_node(width)
    bad: set[tuple[int, int]] = set()
    for unit, cls in width.items():
        if cls != ALLEY or unit in exempt:
            continue
        for node in ends(unit):
            classes = incident[node]
            if AVENUE in classes and STREET not in classes:
                bad.add(node)
    return tuple(sorted(bad))


def touching_violations(width: dict[Unit, int], exempt: frozenset[Unit]) -> int:
    """The STRICTER reading, reported alongside so the rule cannot hide behind
    its own definition: junctions where a non-exempt alley and an avenue meet at
    all, even with a street present. Never expected to be zero — a street
    stepping down to its own alleys at the corner where it meets the avenue is
    the normal city junction — but a number that runs away means the buckets are
    wrong, not the rule."""
    avenue_nodes = {n for u, c in width.items() if c == AVENUE for n in ends(u)}
    return len(
        {
            node
            for unit, cls in width.items()
            if cls == ALLEY and unit not in exempt
            for node in ends(unit)
            if node in avenue_nodes
        }
    )


def _runs(positions: list[int]) -> int:
    """Longest unbroken run in a list of line positions."""
    run = best = 0
    last = None
    for pos in sorted(positions):
        run = run + 1 if last is not None and pos == last + 1 else 1
        best = max(best, run)
        last = pos
    return best


def avenue_lines(width: dict[Unit, int], per_axis: int = AVENUE_LINES_PER_AXIS) -> frozenset[tuple[str, int]]:
    """Which lines are ALLOWED to resolve at avenue width — the junction rule.

    Two filters, in this order (see `AVENUE_LINES_PER_AXIS` above for why):
    majority (avenue units cover at least half the line's own length, so a
    global width means what most of the line carries), then the longest
    unbroken avenue run, capped per axis.

    Deterministic and integer: the sort key is
    `(-run, -avenue units, axis, line)`, which cannot tie because a line index
    appears once per axis.
    """
    lines: dict[tuple[str, int], list[int]] = {}
    avenues: dict[tuple[str, int], list[int]] = {}
    for (axis, line, pos), cls in width.items():
        lines.setdefault((axis, line), []).append(pos)
        if cls == AVENUE:
            avenues.setdefault((axis, line), []).append(pos)
    eligible = [key for key, spans in avenues.items() if 2 * len(spans) >= len(lines[key])]
    out: set[tuple[str, int]] = set()
    for axis in (V, H):
        ranked = sorted(
            (key for key in eligible if key[0] == axis),
            key=lambda key: (-_runs(avenues[key]), -len(avenues[key]), key[1]),
        )
        out.update(ranked[: max(0, per_axis)])
    return frozenset(out)


def line_widths(
    width: dict[Unit, int],
    v_lines: int,
    h_lines: int,
    allow_avenue: frozenset[tuple[str, int]] | None = None,
) -> tuple[dict[int, int], dict[int, int]]:
    """Per-LINE tile widths for `resolve_coordinates` — the single seam where
    all of this becomes geometry.

    A line takes the widest class any of its surviving units resolved at, and
    **0 when it has no units at all**, which is what deletes a line the trim
    emptied. This is the pessimism the lattice architecture was chosen to
    avoid: routing has already finished, so nothing here is a reservation
    against a decision not yet made.

    It is also where the architecture's one real cost shows: a line index is
    GLOBAL, so an avenue anywhere on line 12 widens line 12 across the whole
    grid, including where it runs mid-block through some other precinct. The
    lot-absorbs-an-unfronted-line rule (`town_zoning.lot_rect`) is what keeps
    that from reading as a moat, and `allow_avenue` (spike 5's junction rule) is
    what keeps it from reading as an asphalt plaza: a line outside that set caps
    at STREET however wide its widest unit's class was. Pass `None` for spike
    4's behaviour, which is the A/B.
    """
    allowed = allow_avenue
    v_max: dict[int, int] = {}
    h_max: dict[int, int] = {}
    for (axis, line, _pos), cls in width.items():
        if cls == AVENUE and allowed is not None and (axis, line) not in allowed:
            cls = STREET
        target = v_max if axis == V else h_max
        target[line] = max(target.get(line, 0), WIDTH_TILES[cls])
    return (
        {i: v_max.get(i, 0) for i in range(v_lines)},
        {i: h_max.get(i, 0) for i in range(h_lines)},
    )


# --- the instruments that judge the network --------------------------------


def spine_run(width: dict[Unit, int], wanted: int = AVENUE) -> int:
    """Longest unbroken run of one class along a single line, in CELLS.

    "One continuous spine plus ribs is the single strongest city tell" — this is
    that spine, measured. Falls back a class when the widest one is absent, so a
    catalog with no avenue still reports its longest street.
    """
    while wanted >= ALLEY:
        runs = [0]
        by_line: dict[tuple[str, int], list[int]] = {}
        for (axis, line, pos), cls in width.items():
            if cls == wanted:
                by_line.setdefault((axis, line), []).append(pos)
        for positions in by_line.values():
            run = best = 0
            last = None
            for pos in sorted(positions):
                run = run + 1 if last is not None and pos == last + 1 else 1
                best = max(best, run)
                last = pos
            runs.append(best)
        if max(runs):
            return max(runs)
        wanted -= 1
    return 0


def cyclomatic(units: tuple[Unit, ...]) -> int:
    """`E - V + C` over a unit set: the number of independent closed loops.

    Road-grammar theme 2 — "all-dead-end networks read as plumbing diagrams",
    closed loops in the core are the #1 city tell. Downtown precincts must come
    out above zero or the core is a tree.
    """
    if not units:
        return 0
    nodes = {node for unit in units for node in ends(unit)}
    parent = {node: node for node in nodes}

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    components = len(nodes)
    for unit in units:
        a, b = (find(n) for n in ends(unit))
        if a != b:
            parent[a] = b
            components -= 1
    return len(units) - len(nodes) + components


def endings(units: tuple[Unit, ...], dressed: frozenset[Unit]) -> tuple[tuple[Unit, ...], tuple[Unit, ...]]:
    """`(dressed endings, NAKED endings)` — every road that stops, and whether
    anything stands at the end of it.

    A leaf is a node exactly one unit meets. The unit hanging off it is dressed
    when it is one of the legal endings v5 can already produce: a door opens
    onto it (apron / dock / plaza) or it is a suburban cul-de-sac stub (bulb).
    Anything else is the naked stub property S7 fails a build on, and this
    number is what `trim_dangles` exists to hold at zero.
    """
    degree = node_degree(units)
    good: list[Unit] = []
    bad: list[Unit] = []
    for unit in units:
        if any(degree[node] == 1 for node in ends(unit)):
            (good if unit in dressed else bad).append(unit)
    return tuple(sorted(good)), tuple(sorted(bad))


def unit_tiles(unit: Unit, tiles) -> list[tuple[int, int]]:
    """One unit's tiles at the resolved widths, junction squares included.

    A unit runs from the near end of the line it starts on to the FAR end of the
    line it stops on, so two crossing units share their intersection and a
    junction paints solid rather than leaving a hole at the corner.
    """
    axis, line, pos = unit
    if axis == V:
        span = range(tiles.h_at[pos], tiles.h_at[pos + 1] + tiles.h_w[pos + 1])
        return [(x, y) for x in _run(tiles.v_at[line], tiles.v_w[line]) for y in span]
    span = range(tiles.v_at[pos], tiles.v_at[pos + 1] + tiles.v_w[pos + 1])
    return [(x, y) for y in _run(tiles.h_at[line], tiles.h_w[line]) for x in span]


def _run(at: int, width: int) -> range:
    return range(at, at + width)


def precinct_units(precinct, units: tuple[Unit, ...]) -> tuple[Unit, ...]:
    """Every unit lying wholly inside one precinct's land, frame included."""
    x0, y0 = precinct.cell_x, precinct.cell_y
    x1, y1 = x0 + precinct.cells_w, y0 + precinct.cells_h
    out = []
    for unit in units:
        axis, line, pos = unit
        if axis == V and x0 <= line <= x1 and y0 <= pos and pos + 1 <= y1:
            out.append(unit)
        elif axis == H and y0 <= line <= y1 and x0 <= pos and pos + 1 <= x1:
            out.append(unit)
    return tuple(out)
