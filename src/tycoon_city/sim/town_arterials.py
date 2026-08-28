"""Streets v5, SPIKE 4: ARTERIALS — lineage becomes pavement over the lattice.

**Not wired into anything.** `plan_dag_layout` is still the only planner the
app, the contract and the tests reach; nothing here is imported by `layout`,
`town_plan`, `city_json` or any test. The callers are `scripts/spike_arterials.py`
and `town_hierarchy`, which render it so it can be JUDGED before a rule earns a
test (four spec-first geometry attempts have been wrong in this repo).

Spike 1 decided the LAND, spike 2 put buildings on its frontage, spike 3 fitted
the block to the band. Every line the lattice draws is currently pavement, which
is a lie: most of those lines exist so a lot has a door, not because anything
flows down them. This round makes the distinction physical.

  **unit**     one CELL of one lattice line — the atom routing walks over.
               `(axis, line, pos)`; a `v` unit on line `l` at `p` joins the
               nodes `(l, p)` and `(l, p+1)`, where a node is an intersection
               `(v_line, h_line)`. Segments are not split anywhere; they are
               enumerated into units here and nowhere else.
  **paved**    an arterial was routed over it. A lineage edge EARNED it.
  **dirt**     the unit exists so a lot fronts something. Unearned.
  **join**     reserved for declared OSI relationships (`docs/semantic-roads.md`);
               `plan_arterials(..., surface=JOIN, base=<the paved plan>)` is a
               second call over the same lattice that snaps onto the arterials
               the first one laid. Nothing emits it yet — the seam exists so
               documentation can become pavement later without a re-plan.

Routing is integer-cost Dijkstra over the unit graph, per DESTINATION in sorted
order with that destination's sources sorted, marking units paved as it goes so
a later tributary snaps onto the trunk an earlier one laid. That reproduces
v4's per-destination trunk merging (`town_streets`: "combine the small roads
together if they lead to the same place") with no channels and no reserved
land. Westward steps carry a surcharge so the raw->marts reading survives
contact with a shortest path.

**No floats anywhere.** The heap key is `(cost, node)` over integer costs and
tuple nodes, neighbours are visited in sorted order, and the destination and
source walks are sorted — so the result cannot depend on dict insertion order,
which is the failure that passes on a bench and fails on a customer's catalog.

Endpoints are DOORS (`town_zoning.door_unit`), not route stubs, which is what
lets the legal-ending taxonomy attach to a building's actual frontage in spike 5.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from heapq import heappop, heappush

from .town_blocks import Lattice, V

# (axis, line, position along the line). A unit spans `pos` to `pos + 1` on the
# cross axis, so it is exactly one CELL of street.
Unit = tuple[str, int, int]
# (vertical-line index, horizontal-line index) — a lattice intersection.
Node = tuple[int, int]

PAVED = "paved"
DIRT = "dirt"
JOIN = "join"
# Precedence when two surfaces claim one unit: pavement earned by measured
# lineage outranks a declared join, which outranks unearned frontage. Declared
# never renders as observed (the standing rule), so a join may only ever
# UPGRADE dirt.
_SURFACE_RANK = {PAVED: 0, JOIN: 1, DIRT: 2}

# Integer costs, and the three of them are the whole flow policy.
STEP = 3  # cross one cell of unpaved lattice line
REUSE = 1  # ... one already-surfaced cell: tributaries snap onto trunks
WEST = 6  # surcharge for a step that runs against the raw->marts flow


def ends(unit: Unit) -> tuple[Node, Node]:
    """The two lattice intersections one unit joins, west/north end first."""
    axis, line, pos = unit
    if axis == V:
        return (line, pos), (line, pos + 1)
    return (pos, line), (pos + 1, line)


def unit_graph(lattice: Lattice) -> tuple[Unit, ...]:
    """Every segment of the lattice enumerated into single-cell units.

    Segments overlap and are deliberately NOT split by `plan_lattice` ("that is
    routing's job"); this is where the splitting happens, and the set is
    deduplicated so two coincident segments contribute one unit.
    """
    out: set[Unit] = set()
    for seg in lattice.segments:
        k = seg.key
        for pos in range(k.start, k.end):
            out.add((k.axis, k.line, pos))
    return tuple(sorted(out))


def adjacency(units: tuple[Unit, ...]) -> dict[Node, tuple[tuple[Node, Unit], ...]]:
    """Node -> its sorted neighbours and the unit reached through each."""
    out: dict[Node, list[tuple[Node, Unit]]] = {}
    for unit in units:
        a, b = ends(unit)
        out.setdefault(a, []).append((b, unit))
        out.setdefault(b, []).append((a, unit))
    return {node: tuple(sorted(links)) for node, links in sorted(out.items())}


def _cost(unit: Unit, frm: Node, to: Node, surfaced: set[Unit]) -> int:
    """What one step costs. Integer, and the only place flow policy lives.

    Already-surfaced pavement is a third of the price of virgin line, which is
    what merges tributaries onto trunks without a channel abstraction, and a
    step whose vertical-line index DECREASES pays `WEST` on top — the depth
    columns run west->east, so a route that doubles back is a route that reads
    backwards.
    """
    cost = REUSE if unit in surfaced else STEP
    if to[0] < frm[0]:
        cost += WEST
    return cost


def _route(
    adj: dict[Node, tuple[tuple[Node, Unit], ...]],
    starts: tuple[Node, ...],
    targets: frozenset[Node],
    surfaced: set[Unit],
) -> tuple[Unit, ...] | None:
    """Cheapest walk from any start node to any target node, as units.

    Plain Dijkstra with the heap key `(cost, node)`: costs are integers and
    nodes are totally ordered tuples, so two entries can never tie and fall
    back on insertion order. Neighbours are already sorted by `adjacency`, so
    the predecessor a node settles with is a function of the graph alone.
    """
    dist: dict[Node, int] = {}
    prev: dict[Node, tuple[Node, Unit]] = {}
    heap: list[tuple[int, Node]] = []
    for node in sorted(starts):
        if node in adj and node not in dist:
            dist[node] = 0
            heappush(heap, (0, node))
    seen: set[Node] = set()
    while heap:
        cost, node = heappop(heap)
        if node in seen:
            continue
        seen.add(node)
        if node in targets:
            path: list[Unit] = []
            while node in prev:
                node, unit = prev[node]
                path.append(unit)
            return tuple(reversed(path))
        for nxt, unit in adj[node]:
            if nxt in seen:
                continue
            step = cost + _cost(unit, node, nxt, surfaced)
            if step < dist.get(nxt, step + 1):
                dist[nxt] = step
                prev[nxt] = (node, unit)
                heappush(heap, (step, nxt))
    return None


@dataclass(frozen=True)
class ArterialPlan:
    """The surfaced network: which units exist, what each one IS, and why.

    `carriers[u]` is every lineage edge routed over `u` — the "two models
    merging becomes a two lane road" measure, and one of the two `WIDTH_MEASURE`
    candidates. `routes` keeps the whole walk per edge so a later spike can
    dress its endings; `unrouted` is named rather than dropped.
    """

    units: tuple[Unit, ...]
    surface_of: dict[Unit, str]
    carriers: dict[Unit, tuple[tuple[str, str], ...]]
    routes: dict[tuple[str, str], tuple[Unit, ...]]
    unrouted: tuple[tuple[str, str], ...]

    def paved(self) -> tuple[Unit, ...]:
        return tuple(u for u in self.units if self.surface_of[u] == PAVED)

    def dirt(self) -> tuple[Unit, ...]:
        return tuple(u for u in self.units if self.surface_of[u] == DIRT)


def plan_arterials(
    lattice: Lattice,
    doors: dict[str, Unit],
    edges: list[tuple[str, str]],
    surface: str = PAVED,
    base: ArterialPlan | None = None,
) -> ArterialPlan:
    """Route every edge door-to-door and surface what it used.

    Per DESTINATION in sorted order, sources sorted inside it. The destination's
    own frontage unit is surfaced first, so the first tributary to arrive lays
    the trunk and every later one is pulled onto it by `REUSE` — v4's
    destination-group merging, without a channel or a reserved track.

    `base` is a previously routed plan: its surfaced units are already cheap, so
    `plan_arterials(lattice, doors, joins, surface=JOIN, base=paved_plan)` paves
    declared relationships onto the arterials the measured ones earned, and
    `_SURFACE_RANK` keeps a join from ever overwriting observed pavement. That
    second call is the whole of Phase 3's OSI-B seam; nothing calls it yet.
    """
    units = base.units if base is not None else unit_graph(lattice)
    surface_of: dict[Unit, str] = dict(base.surface_of) if base is not None else {u: DIRT for u in units}
    carriers: dict[Unit, list[tuple[str, str]]] = {u: [] for u in units}
    if base is not None:
        for unit, borne in base.carriers.items():
            carriers[unit] = list(borne)
    routes: dict[tuple[str, str], tuple[Unit, ...]] = dict(base.routes) if base else {}
    adj = adjacency(units)
    surfaced = {u for u in units if surface_of[u] != DIRT}
    known = set(units)

    def mark(unit: Unit, edge: tuple[str, str] | None) -> None:
        if _SURFACE_RANK[surface] < _SURFACE_RANK[surface_of[unit]]:
            surface_of[unit] = surface
        surfaced.add(unit)
        if edge is not None and edge not in carriers[unit]:
            carriers[unit].append(edge)

    by_dst: dict[str, set[str]] = {}
    for src, dst in edges:
        if src != dst and src in doors and dst in doors:
            by_dst.setdefault(dst, set()).add(src)

    unrouted: list[tuple[str, str]] = []
    for dst in sorted(by_dst):
        target = doors[dst]
        if target not in known:
            unrouted.extend((s, dst) for s in sorted(by_dst[dst]))
            continue
        mark(target, None)
        targets = frozenset(ends(target))
        for src in sorted(by_dst[dst]):
            start = doors[src]
            if start not in known:
                unrouted.append((src, dst))
                continue
            mark(start, (src, dst))
            walk = _route(adj, ends(start), targets, surfaced)
            if walk is None:
                unrouted.append((src, dst))
                continue
            edge = (src, dst)
            for unit in (start, target, *walk):
                mark(unit, edge)
            routes[edge] = tuple(sorted({start, target, *walk}))

    return ArterialPlan(
        units=units,
        surface_of=surface_of,
        carriers={u: tuple(carriers[u]) for u in units},
        routes=routes,
        unrouted=tuple(sorted(unrouted)),
    )


# --- the two WIDTH_MEASURE candidates -------------------------------------


def downstream_reach(keys: list[str], edges: list[tuple[str, str]]) -> dict[str, int]:
    """`|{k} union everything k feeds|` per object — a plain BFS per key.

    Cycles are fine: the visited set terminates the walk. This is the input to
    the `closure` width measure, which is `docs/road-grammar.md`'s literal
    wording ("road width = downstream dependency count").
    """
    successors: dict[str, list[str]] = {k: [] for k in keys}
    for src, dst in sorted({(s, d) for s, d in edges if s != d}):
        if src in successors and dst in successors:
            successors[src].append(dst)
    out: dict[str, int] = {}
    for key in keys:
        seen = {key}
        queue = deque([key])
        while queue:
            for nxt in successors[queue.popleft()]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        out[key] = len(seen)
    return out


def measure_carriers(plan: ArterialPlan) -> dict[Unit, int]:
    """Candidate (a): distinct lineage edges routed over the unit.

    Continuous with the semantics already shipped in v4 — Stephen, 2026-08-05:
    "two models merging becomes a two lane road". A trunk that four tributaries
    joined is four wide; a spur that carries one edge is one.
    """
    return {u: len(plan.carriers[u]) for u in plan.units}


def measure_closure(plan: ArterialPlan, reach: dict[str, int]) -> dict[Unit, int]:
    """Candidate (b): the size of the downstream closure the unit serves.

    Road-grammar's literal wording. Taken as the LARGEST closure among the
    edges the unit carries rather than their sum, so the number means "how much
    of the warehouse hangs off what flows down this street" and two unrelated
    tributaries sharing a block of trunk do not add up to a boulevard.
    """
    return {u: max((reach.get(dst, 1) for _src, dst in plan.carriers[u]), default=0) for u in plan.units}


# --- trimming what nothing dresses -----------------------------------------


def trim_dangles(plan: ArterialPlan, keep: frozenset[Unit]) -> tuple[tuple[Unit, ...], tuple[Unit, ...]]:
    """`(surviving units, trimmed units)` — pull out every road that just stops.

    A unit whose far end is a leaf and which nothing dresses is exactly the
    naked stub road-grammar's theme 7 says both real cities and sims avoid, and
    property S7 already fails a v4 build on. `keep` is what a leaf is ALLOWED to
    be: a unit carrying a route (its far end is a door), a unit a lot's door
    opens onto (an apron), or a suburban cul-de-sac stub (a bulb).

    A cycle can never be trimmed, so this only ever chews back trees — the
    spine that overshot the last precinct into open grass, and the frame of a
    band nothing was routed to. Iterated to a fixpoint, because trimming a leaf
    makes its neighbour a leaf.
    """
    live = set(plan.units)
    trimmed: list[Unit] = []
    cutting = True
    while cutting:
        cutting = False
        degree = node_degree(tuple(sorted(live)))
        for unit in sorted(live):
            if unit in keep:
                continue
            a, b = ends(unit)
            # `degree` goes stale as the pass removes units, but only ever
            # upward, so a stale reading can delay a cut to the next pass and
            # can never make one that the fixpoint would not have made.
            if degree[a] == 1 or degree[b] == 1:
                live.discard(unit)
                trimmed.append(unit)
                cutting = True
    return tuple(sorted(live)), tuple(sorted(trimmed))


def node_degree(units: tuple[Unit, ...]) -> dict[Node, int]:
    """How many units meet at each intersection — leaves, junctions and loops
    are all read off this one count."""
    out: dict[Node, int] = {}
    for unit in units:
        for node in ends(unit):
            out[node] = out.get(node, 0) + 1
    return out
