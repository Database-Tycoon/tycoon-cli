"""Lineage structure derived from a catalog, and the DAG city planned from it.

Reads a PipelineContext and reports how its objects relate: a lineage depth per
object, and which objects have no lineage at all. On top of that it plans the
map (streets v2.1): buildings in topological columns, every edge routed through
the channel between columns on its destination group's shared trunk — see
`plan_dag_layout`. It produces coordinates but no tiles; painting is the
generator's job.

Imports no pygame and holds no rendering concepts. Guarded by
tests/sim/test_no_pygame.py.
"""

from collections import deque

from ..catalog.models import PipelineContext


def _known_edges(ctx: PipelineContext) -> list[tuple[str, str]]:
    """Edges both of whose endpoints exist in the catalog, in context order."""
    keys = {obj.key for obj in ctx.objects}
    return [(e.src, e.dst) for e in ctx.edges if e.src in keys and e.dst in keys]


def _successor_map(keys: list[str], edges: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Adjacency, deduplicated and sorted so traversal order is input-independent."""
    successors: dict[str, set[str]] = {k: set() for k in keys}
    for src, dst in edges:
        successors[src].add(dst)
    return {k: sorted(v) for k, v in successors.items()}


def _components(keys: list[str], successors: dict[str, list[str]]) -> list[list[str]]:
    """Strongly connected components, via an explicit-stack Tarjan.

    Iterative on purpose: a catalog may hold MAX_OBJECTS (500) objects and a
    recursive Tarjan would put a frame per node on the Python stack. Each
    component is returned with its members sorted; the component order is fixed
    by the sorted key and successor order, so the result depends only on the
    graph, not on how the catalog listed it.
    """
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    pending: list[str] = []
    components: list[list[str]] = []
    counter = 0

    for root in keys:
        if root in index:
            continue
        index[root] = low[root] = counter
        counter += 1
        pending.append(root)
        on_stack.add(root)
        # Each frame is (node, how many of its successors we have consumed).
        work: list[list] = [[root, 0]]
        while work:
            node, cursor = work[-1]
            if cursor < len(successors[node]):
                work[-1][1] = cursor + 1
                nxt = successors[node][cursor]
                if nxt not in index:
                    index[nxt] = low[nxt] = counter
                    counter += 1
                    pending.append(nxt)
                    on_stack.add(nxt)
                    work.append([nxt, 0])
                elif nxt in on_stack:
                    low[node] = min(low[node], index[nxt])
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
            if low[node] == index[node]:
                # None, not "", so the sentinel cannot collide with a real key:
                # an empty-string key would skip the loop and drop a node from
                # component_of, surfacing later as a KeyError.
                member: str | None = None
                component: list[str] = []
                while member != node:
                    member = pending.pop()
                    on_stack.discard(member)
                    component.append(member)
                components.append(sorted(component))
    return components


def compute_depths(ctx: PipelineContext) -> dict[str, int]:
    """Lineage depth per object key: the longest chain of *components* above it.

    0 for objects nothing feeds; otherwise one more than the deepest component
    that reaches it. Counted in components, not objects, so it is not a hop
    count once cycles exist: in a -> c, c <-> d, d -> e -> f, e is at depth 2
    though the longest path of objects reaching it is 3 hops. On an acyclic
    catalog every component is a single object and the two coincide.

    Depth never decreases across a known edge. For every edge (src, dst) either
    depth[dst] > depth[src], or src and dst are mutually reachable -- inside the
    same dependency cycle -- in which case they share a depth. Since depth
    becomes a ring index downstream, that is what keeps every edge pointing
    outward.

    Cycles are handled by condensing each strongly connected component to a
    single node. The condensation is acyclic by construction, so the longest
    path to a component is well defined and one Kahn pass over it terminates:
    every component is dequeued exactly once and every edge between components
    is relaxed exactly once. A component's depth is the longest chain of
    components reaching it, and all its members take that depth. Relaxing
    individual edges to a fixed point instead would never settle -- a cycle
    would inflate its own members without bound.

    A component with no incoming edge from outside itself is a source at depth
    0, whether it is one object or a cycle. So a cycle that nothing feeds starts
    at 0 rather than being pushed past the rest of the graph, and a chain
    hanging below a cycle steps up hop by hop from there.
    """
    keys = sorted(obj.key for obj in ctx.objects)
    edges = _known_edges(ctx)
    successors = _successor_map(keys, edges)

    components = _components(keys, successors)
    component_of = {key: i for i, members in enumerate(components) for key in members}

    # Condense: keep only edges that leave their component. Self-loops and
    # in-cycle edges disappear here, which is what makes the rest acyclic.
    ids = range(len(components))
    condensed: dict[int, set[int]] = {i: set() for i in ids}
    for src, dst in edges:
        tail, head = component_of[src], component_of[dst]
        if tail != head:
            condensed[tail].add(head)
    in_degree: dict[int, int] = dict.fromkeys(ids, 0)
    for heads in condensed.values():
        for head in heads:
            in_degree[head] += 1

    component_depth: dict[int, int] = dict.fromkeys(ids, 0)
    queue = deque(i for i in ids if in_degree[i] == 0)
    while queue:
        tail = queue.popleft()
        # Kahn order guarantees every predecessor of tail was dequeued before
        # it, so component_depth[tail] is final at this point.
        for head in sorted(condensed[tail]):
            component_depth[head] = max(component_depth[head], component_depth[tail] + 1)
            in_degree[head] -= 1
            if in_degree[head] == 0:
                queue.append(head)

    return {key: component_depth[component_of[key]] for key in keys}


def has_known_edges(ctx: PipelineContext) -> bool:
    """True when at least one edge has both endpoints in the catalog.

    False means no lineage could be determined at all, which the renderer says
    out loud in the status strip: lineage comes from view SQL only, so a
    tables-only database is indistinguishable from one with no dependencies.
    """
    return bool(_known_edges(ctx))


def isolated_keys(ctx: PipelineContext) -> set[str]:
    """Object keys with no lineage edge in either direction.

    Note: signals.LineageParticipation derives the same connectedness from the
    same definition of a known edge, deliberately duplicated so that module
    stays independent of this one. The two *differ in meaning* when the catalog
    has no known edges: this function reports every object as isolated, while
    the signal scores them all 1.0 so the map does not go dark. Keep both in
    step if either changes.
    """
    connected: set[str] = set()
    for src, dst in _known_edges(ctx):
        connected.add(src)
        connected.add(dst)
    return {obj.key for obj in ctx.objects} - connected


# The DAG planner grew past the 500-line rule and moved to its own module;
# these re-exports keep every existing import (`tycoon_city.sim.layout`) valid.
from .town_plan import (  # noqa: E402
    BAND_GAP,
    GRID_MIN,
    H_LANE_CAP,
    LANE_CAP,
    MARGIN,
    NEIGHBOUR_PITCH,
    ROW_PITCH,
    SUBURB_PER_ROW,
    TRACK_PITCH,
    DagPlan,
    DistrictPlan,
    StreetFeature,
    plan_dag_layout,
)

__all__ = [
    "BAND_GAP",
    "GRID_MIN",
    "H_LANE_CAP",
    "LANE_CAP",
    "MARGIN",
    "NEIGHBOUR_PITCH",
    "ROW_PITCH",
    "SUBURB_PER_ROW",
    "TRACK_PITCH",
    "DagPlan",
    "DistrictPlan",
    "StreetFeature",
    "compute_depths",
    "has_known_edges",
    "isolated_keys",
    "plan_dag_layout",
]
