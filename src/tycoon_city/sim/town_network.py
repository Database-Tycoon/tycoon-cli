"""The street network's graph work: routing, bridging, thinning, access.

Split out of `town_plan.py` on 2026-08-10 when the thinned street network
pushed it past the 500-line law. Everything here is pure tile-set algebra —
deterministic (fixed N/E/S/W neighbour order, sorted tie-breaks, no RNG, no
clock), because two exports of one catalog must produce the same bytes.

Imports no pygame and holds no rendering concepts.
"""

from __future__ import annotations

from collections import deque
from heapq import heapify, heappop, heappush

Tile = tuple[int, int]

_NESW = ((0, -1), (1, 0), (0, 1), (-1, 0))


def bfs_route(road: frozenset[Tile], start: Tile, goal: Tile) -> tuple[Tile, ...]:
    """Shortest drivable path, with a DETERMINISTIC tie-break.

    Neighbours are visited in a fixed N/E/S/W order and the queue is FIFO, so
    equal-length paths always resolve the same way. That is not a nicety: two
    exports of one catalog must produce the same bytes, and a set-iteration
    order would break that on the first rehash.
    """
    if start == goal:
        return (start,)
    if start not in road or goal not in road:
        return ()
    prev: dict[Tile, Tile] = {start: start}
    queue = deque([start])
    while queue:
        at = queue.popleft()
        for dx, dy in _NESW:
            nxt = (at[0] + dx, at[1] + dy)
            if nxt in road and nxt not in prev:
                prev[nxt] = at
                if nxt == goal:
                    path = [nxt]
                    while path[-1] != start:
                        path.append(prev[path[-1]])
                    return tuple(reversed(path))
                queue.append(nxt)
    return ()


def _component(start: Tile, members: set[Tile] | frozenset[Tile]) -> set[Tile]:
    seen, stack = {start}, [start]
    while stack:
        cx, cy = stack.pop()
        for dx, dy in _NESW:
            nxt = (cx + dx, cy + dy)
            if nxt in members and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def _components(members: set[Tile] | frozenset[Tile]) -> list[set[Tile]]:
    comps: list[set[Tile]] = []
    left = set(members)
    while left:
        c = _component(min(left), left)
        comps.append(c)
        left -= c
    comps.sort(key=lambda c: (-len(c), min(c)))
    return comps


def _join(
    body: set[Tile],
    islands: list[set[Tile]],
    walkable: set[Tile],
    cheap: set[Tile] | frozenset[Tile],
    streets: set[Tile],
    grow: set[Tile],
) -> None:
    """ONE multi-source cheapest-path pass from `body`; every island then
    joins along its cheapest recorded entry path (added to `grow` in place).

    Costs, not walls: `cheap` tiles (the lattice) cost 1, open ground 4, and
    open ground beside an existing street 12 — measured plain BFS let grass
    connectors hug streets and gave the street tiles a third neighbour on
    every step (up to 25 S8 violations on the random family); pricing the
    hug makes bridges cross perpendicular instead. Not a minimal Steiner
    tree — an island connects to the ORIGINAL body even when a sibling
    island sits closer — but one O(area log area) pass instead of one per
    island, which is what lets a 500-object catalog finish.
    """

    def price(t: Tile) -> int:
        if t in cheap:
            return 1
        beside = any((t[0] + dx, t[1] + dy) in streets for dx, dy in _NESW)
        return 12 if beside else 4

    dist: dict[Tile, int] = {t: 0 for t in body}
    prev: dict[Tile, Tile] = {t: t for t in body}
    heap: list[tuple[int, Tile]] = [(0, t) for t in sorted(body)]
    heapify(heap)
    while heap:
        d, at = heappop(heap)
        if d > dist.get(at, d):
            continue
        for dx, dy in _NESW:
            nxt = (at[0] + dx, at[1] + dy)
            if nxt not in walkable:
                continue
            nd = d + price(nxt)
            if nd < dist.get(nxt, nd + 1):
                dist[nxt] = nd
                prev[nxt] = at
                heappush(heap, (nd, nxt))

    for island in islands:
        reachable = [t for t in island if t in dist]
        if not reachable:
            continue  # ground the walk cannot cross; the island stays as-is
        at = min(reachable, key=lambda t: (dist[t], t))
        while at not in body:
            grow.add(at)
            at = prev[at]


def bridge_lattice(
    lattice_road: frozenset[Tile],
    anchors: set[Tile],
    open_ground: frozenset[Tile],
) -> frozenset[Tile]:
    """The drivable body for routing: the lattice, bridged into one piece.

    The staggered ring placement can SPLIT the lattice — a precinct can rest
    on the bounding-box line without its frame overlapping any inner segment
    (measured: random seed 5 left 8 of 13 edges unroutable). Only the
    lattice components that carry an anchor (a door) earn a bridge; an
    empty fragment stays an island nobody needed.
    """
    if not lattice_road:
        return lattice_road
    comps = _components(lattice_road)
    bearing = [c for c in comps if c & anchors]
    if len(bearing) <= 1:
        return lattice_road
    body = bearing[0]
    grow: set[Tile] = set(lattice_road)
    _join(
        body,
        bearing[1:],
        walkable=set(lattice_road) | set(open_ground),
        cheap=lattice_road,
        streets=set(lattice_road),
        grow=grow,
    )
    return frozenset(grow)


def connected_street_net(
    drivable: frozenset[Tile],
    needed: set[Tile],
    open_ground: frozenset[Tile] = frozenset(),
) -> set[Tile]:
    """The street network: the needed tiles, made ONE component.

    `needed` (route tiles + every lot's door) can land as islands; each
    island is joined to the main body by the cheapest path, largest
    component first (see `_join` for the costs and the single-pass shape).
    A street may cross grass, never a building. S8 is re-measured by the
    suite rather than assumed, because an off-lattice connector is new
    geometry the lattice construction never promised.
    """
    walkable = set(drivable) | set(open_ground)
    keep = set(needed) & walkable
    if not keep:
        return keep
    comps = _components(keep)
    if len(comps) == 1:
        return keep
    _join(
        comps[0],
        comps[1:],
        walkable=walkable,
        cheap=drivable,
        streets=set(drivable) | keep,
        grow=keep,
    )
    return keep


def access_road(road: frozenset[Tile], firehouse_xy: Tile, blocked: frozenset[Tile] = frozenset()) -> tuple[Tile, ...]:
    """A civic street from the firehouse to the nearest street, over OPEN
    ground — a downtown station is surrounded by buildings, and a street
    that plows through one is not a street. BFS with the fixed N/E/S/W
    order, so the path is deterministic.

    The RoadNet rule is absolute — every vehicle class drives on roads — so a
    firehouse with no road touching it is a dispatch that cannot leave.
    """
    if not road:
        return ()
    xs = [x for x, _ in road] + [firehouse_xy[0]]
    ys = [y for _, y in road] + [firehouse_xy[1]]
    lo_x, hi_x = min(xs) - 2, max(xs) + 2
    lo_y, hi_y = min(ys) - 2, max(ys) + 2
    prev: dict[Tile, Tile] = {firehouse_xy: firehouse_xy}
    frontier = deque([firehouse_xy])
    found: Tile | None = None
    while frontier and found is None:
        at = frontier.popleft()
        for dx, dy in _NESW:
            nxt = (at[0] + dx, at[1] + dy)
            if nxt in prev or nxt in blocked:
                continue
            if not (lo_x <= nxt[0] <= hi_x and lo_y <= nxt[1] <= hi_y):
                continue
            prev[nxt] = at
            if nxt in road:
                found = nxt
                break
            frontier.append(nxt)
    if found is None:
        return ()
    path = [found]
    while path[-1] != firehouse_xy:
        path.append(prev[path[-1]])
    # The station tile itself is the firehouse, not road; keep the rest.
    return tuple(reversed(path[:-1]))
