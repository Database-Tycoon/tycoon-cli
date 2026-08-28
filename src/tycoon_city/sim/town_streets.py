"""The streets: channels, trunks, tile-by-tile routes, and merged lane width.

The routing half of the DAG planner (`town_rows` decided columns and rows;
`town_plan` orchestrates and adds the civic strip, the suburb and the plates).
Split out of `town_plan.py` on 2026-08-05 at the seam the streets v4 blueprint
named. Nothing here decides where a building sits.

Streets v2 (Stephen's redirect, 2026-08-05): "The lineage connections between
each model node should be matched by a street style grid that literally
connects the two. There shouldn't be other buildings in the way." So every edge
is routed through a CHANNEL between columns on its destination group's trunk
track — road land no building may occupy. Long edges reserve a pass-through row
in each intermediate column (a dummy slot, shared by every edge bound for the
same destination), so their street crosses the column without ever meeting a
building.

Sprawl is the point, not a bug — but it is priced per DESTINATION, not per edge
(streets v2.1, "combine the small roads together if they lead to the same
place"). Edges converging on one destination merge like tributaries: they share
one vertical trunk per channel and one pass-through row per intermediate
column, so a pure fan-in of twelve edges is no wider than a fan-in of two. Each
*distinct* destination group (plus each loop edge) widens its channel by
TRACK_PITCH, so a genuinely tangled DAG — many destinations wired from many
places — still paves itself into an ugly, sprawling city while a clean pipeline
earns a tight village. The city's silhouette is a legibility verdict on the
warehouse.

Imports no pygame and holds no rendering concepts.
"""

from dataclasses import dataclass

from .town_rows import FIRST_COL_X, SitePlan

TRACK_PITCH = 2  # channel tracks: 1 street column + 1 grass column
# Merged trunks keep their combined thickness (Stephen: "two models merging
# becomes a two lane road"): a trunk is as many lanes wide as the flows that
# have merged at that point, capped like a real highway. Horizontal shared
# runs widen one row at most — building rows are only ROW_PITCH apart.
LANE_CAP = 4
H_LANE_CAP = 2


# Streets v4 (Stephen, 2026-08-05): "there needs to be a clear definition for
# when and where a road is allowed to end, and what that looks like." The
# taxonomy is `docs/road-grammar.md`'s legal-ending table; this stage ships the
# three endings a lineage street actually produces. `facing` is the compass
# direction from the feature tile TOWARD the building it serves.
FACING = {(1, 0): "e", (-1, 0): "w", (0, 1): "s", (0, -1): "n"}

APRON = "apron"  # an ordinary building's driveway: half-tile pad at its face
DOCK = "dock"  # a depth-0 source (or the plant): the industrial truck court
PLAZA = "plaza"  # a 2x2 lot or a civic building: the paved forecourt / vista


@dataclass(frozen=True)
class StreetFeature:
    """How one road END is dressed — a derived fact, never an invention.

    Every feature is read off a route endpoint (or the firehouse's access road)
    plus the lot metadata already in the plan: the tile is the last ROAD tile
    before a building, `facing` points at that building, and `kind` is what the
    building IS. A naked stub — a road that just stops — is what property S7
    (`find_naked_stubs`, below) detects; it is a test-suite check, not a
    request-path exception, so a real geometry defect fails a build rather
    than a `/city.json` request.

    `w`/`h` describe the pad's ground plan, NW-anchored at (x, y). Only a plaza
    against a 2x2 lot grows past 1x1: it spans the whole shared face, so a
    downtown block gets a forecourt the width of its frontage instead of a
    one-tile nick. Those extra tiles become ROAD-kind pavement (the generator
    paints them like lane tiles, under the same grass-only guard).
    """

    kind: str
    x: int
    y: int
    facing: str | None = None
    w: int = 1
    h: int = 1


def _feature_sort_key(f: StreetFeature) -> tuple:
    """(kind, x, y) is the contract's order; the rest only breaks ties, which
    happen when one tile serves two buildings (a one-tile street between two
    lots is both an approach and an arrival). `facing or ""` because None and a
    string are not comparable and a future kind may have no facing."""
    return (f.kind, f.x, f.y, f.facing or "", f.w, f.h)


@dataclass(frozen=True)
class StreetPlan:
    """Every street the lineage asks for, as tiles."""

    col_x: dict[int, int]  # depth -> the x of that building column
    positions: dict[str, tuple[int, int]]  # real nodes AND pass-through slots
    routes: dict[tuple[str, str], tuple[tuple[int, int], ...]]
    lane_tiles: tuple[tuple[int, int], ...]
    right_edge: int  # x just past the last channel — the grid's west-to-east span


def plan_streets(site: SitePlan, depth: dict[str, int]) -> StreetPlan:
    """Channels, tracks, routes and lanes, from a site whose rows are fixed."""
    chains, node_layer, columns = site.chains, site.node_layer, site.columns
    rows_of, block_of, big = site.rows_of, site.block_of, site.big

    # Channel population: forward segments leave their tail's column; loop
    # segments (same-depth, in-cycle) use the channel east of their column.
    channel_segs: dict[int, list[tuple[str, str]]] = {}
    for seg in site.forward_segments:
        channel_segs.setdefault(node_layer[seg[0]], []).append(seg)
    loop_segs = [(s, d) for (s, d), chain in chains.items() if len(chain) == 2 and depth[s] == depth[d]]
    for seg in loop_segs:
        channel_segs.setdefault(node_layer[seg[0]], []).append(seg)
    loop_set = set(loop_segs)

    # A TRACK UNIT is what claims a vertical track in a channel: one per
    # distinct forward head (all segments converging on that head — the
    # destination group's trunk) plus one per loop edge. All same-group
    # segments in a channel share one head: the shared dummy, or the
    # destination itself in its final channel.
    channel_units: dict[int, list[tuple[str, str] | str]] = {}
    for ly, segs in channel_segs.items():
        # Same-block heads collapse onto one unit: siblings fed by the same
        # sources share one delivery trunk into the block.
        heads = sorted({block_of.get(b, b) for (a, b) in segs if (a, b) not in loop_set})
        channel_units[ly] = list(heads) + sorted(set(segs) & loop_set)

    # Lanes a unit's trunk may grow to: its tributary count, capped. Loops
    # stay single-lane.
    def unit_lanes(ly: int, unit) -> int:
        if not isinstance(unit, str):
            return 1  # a loop edge
        tributaries = sum(1 for (a, b) in channel_segs[ly] if b == unit and (a, b) not in loop_set)
        return min(max(tributaries, 1), LANE_CAP)

    # A STRAIGHT unit: every tributary enters at its head's row, so its street
    # never turns — no trunk, no reserved channel width. This is what collapses
    # a warehouse of 1:1 hops (raw -> staging, aligned by the float rule) from
    # a ladder of L-streets into a comb of straight ones.
    straight_units: set[tuple[int, str]] = set()
    for ly, units in channel_units.items():
        for u in units:
            if not isinstance(u, str):
                continue  # loop edges always detour through their channel
            segs = [s for s in channel_segs[ly] if s not in loop_set and block_of.get(s[1], s[1]) == u]
            if segs and all(rows_of[a] == rows_of[b] for a, b in segs):
                straight_units.add((ly, u))

    # Column x positions; each channel is as wide as its TURNING units' lanes
    # demand (a merged trunk keeps its combined thickness, so it reserves the
    # room; straight units reserve nothing).
    col_x: dict[int, int] = {}
    x = FIRST_COL_X
    for ly in sorted(columns):
        col_x[ly] = x
        # 1 building column + 2 pad + (lanes + 1 gap) per turning unit + 2
        # pad; with every unit single-lane this is the old 5 + TRACK_PITCH*n.
        x += 5 + sum(unit_lanes(ly, u) + 1 for u in channel_units.get(ly, []) if (ly, u) not in straight_units)

    positions: dict[str, tuple[int, int]] = {n: (col_x[node_layer[n]], rows_of[n]) for n in rows_of}

    # One vertical track per turning unit, sorted by exit row so neighbouring
    # trunks rarely weave. Tributaries run east along their own row to the
    # trunk, merge vertically on it, and leave together at the head's row.
    # Straight units' segments never turn, so their track x is unobservable —
    # any value between the endpoints paints the same street.
    track_x: dict[tuple[str, str], int] = {}
    for ly, units in channel_units.items():
        live = [u for u in units if (ly, u) not in straight_units]
        live.sort(
            key=lambda u: (positions[u][1], 0, u, "") if isinstance(u, str) else (positions[u[1]][1], 1, u[0], u[1])
        )
        unit_x: dict = {}
        cursor = col_x[ly] + 3
        for u in live:
            unit_x[u] = cursor
            cursor += unit_lanes(ly, u) + 1  # its lanes, then one grass gap
        for seg in channel_segs[ly]:
            unit = seg if seg in loop_set else block_of.get(seg[1], seg[1])
            track_x[seg] = unit_x.get(unit, col_x[ly] + 1)

    def segment_path(a: str, b: str) -> list[tuple[int, int]]:
        (ax, ay), (bx, by) = positions[a], positions[b]
        if a in big:
            ax += 1  # a 2x2 lot's outbound street leaves from its east face
        tx = track_x[(a, b)]
        path = [(sx, ay) for sx in range(ax, tx + 1)]
        if ay != by:
            step = 1 if by > ay else -1
            path += [(tx, sy) for sy in range(ay + step, by + step, step)]
        # bx may be east (forward) or back west (loop edge): walk either way.
        # (tx, by) is already the path's last tile — continue one past it.
        xstep = 1 if bx >= tx else -1
        if xstep < 0 and b in big:
            bx += 1  # a loop street arrives at the big lot's east face
        path += [(sx, by) for sx in range(tx + xstep, bx + xstep, xstep)]
        return path

    routes: dict[tuple[str, str], tuple[tuple[int, int], ...]] = {}
    for (s, d), chain in chains.items():
        path: list[tuple[int, int]] = []
        for a, b in zip(chain, chain[1:], strict=False):
            seg = segment_path(a, b)
            path += seg if not path else seg[1:]
        routes[(s, d)] = tuple(path)

    lane_tiles = _lane_tiles(routes, positions, sorted(depth), big)
    return StreetPlan(
        col_x=col_x,
        positions=positions,
        routes=routes,
        lane_tiles=lane_tiles,
        right_edge=x,
    )


def plan_street_features(
    routes: dict[tuple[str, str], tuple[tuple[int, int], ...]],
    lots: dict[str, tuple[int, int]],
    big: frozenset[str],
    depth: dict[str, int],
    access_road: tuple[tuple[int, int], ...],
    firehouse_xy: tuple[int, int],
) -> tuple[StreetFeature, ...]:
    """Dress every road ending (streets v4). Derived facts only.

    A street ends where it meets a building, so the endings are exactly the
    route endpoints: the first ROAD tile leaving the source lot and the last
    one before the destination lot (a route with no interior — two lots that
    touch — has no road to dress). The firehouse's access road ends at a civic
    building, which is its own legal ending.

    Kind precedence is `plaza` > `dock` > `apron`, because the two special
    reads can overlap on one building (a raw source can also be a 2x2) and only
    the plaza carries pad geometry: keeping it first is what makes "a pad wider
    than one tile is a plaza" true, which is the invariant the renderer reads.
    """
    features: set[StreetFeature] = set()

    def dress(road: tuple[int, int], toward: tuple[int, int], key: str | None) -> None:
        step = (toward[0] - road[0], toward[1] - road[1])
        facing = FACING[step]
        civic = key is None
        if civic or key in big:
            kind = PLAZA
        elif depth.get(key) == 0:
            kind = DOCK
        else:
            kind = APRON
        x, y, w, h = road[0], road[1], 1, 1
        if kind is PLAZA and key in big and step[0]:
            # A 2x2 lot's forecourt spans its whole frontage — two tiles tall,
            # anchored on the lot's own row. Only the EAST/WEST faces are
            # handled because those are the only faces a street can arrive at:
            # every route's first and last leg is horizontal (a channel's trunk
            # x is always at least two tiles short of the next building column,
            # so the closing horizontal leg is never empty). MEASURED over the
            # whole property sweep plus demo-tycoon and dogfood: 768 endings,
            # not one of them vertical. The only n/s facing in the city is the
            # civic plaza at the firehouse door, and that pad is 1x1.
            # The tile beside a frontage is channel or pad ground by
            # construction, never another building, so there is nothing to
            # yield to here; property S7 checks the pad came out paved.
            y, h = lots[key][1], 2
        features.add(StreetFeature(kind=kind, x=x, y=y, facing=facing, w=w, h=h))

    for (src, dst), route in sorted(routes.items()):
        if len(route) < 2:
            continue
        # Route: [lot_src, road_1, ..., road_n, lot_dst]
        # road_1 is at route[1], road_n is at route[-2]
        # BUT the lot is at route[0] and route[-1].
        # So road ending at src is route[1], road ending at dst is route[-2].
        # If route len is 2 (e.g. lot_src, lot_dst), no road tiles.
        if len(route) < 3:
            continue

        dress(route[1], route[0], src)
        dress(route[-2], route[-1], dst)

    if access_road:
        dress(access_road[0], firehouse_xy, None)

    return tuple(sorted(features, key=_feature_sort_key))


def find_naked_stubs(
    road_tiles: set[tuple[int, int]],
    lot_tiles: set[tuple[int, int]],
    features: tuple[StreetFeature, ...],
) -> tuple[tuple[int, int], ...]:
    """Road tiles with exactly one orthogonal neighbour and no feature dressing
    them — property S7. Pure: it reports, it never raises. Every tile a
    feature covers is exempt, not just its anchor, because a 2x1 plaza
    dresses both of its tiles."""
    covered = {(f.x + dx, f.y + dy) for f in features for dx in range(f.w) for dy in range(f.h)}
    stubs = []
    for t in road_tiles:
        if t in covered:
            continue
        neighbours = sum(
            1
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))
            if (t[0] + dx, t[1] + dy) in road_tiles or (t[0] + dx, t[1] + dy) in lot_tiles
        )
        if neighbours == 1:
            stubs.append(t)
    return tuple(sorted(stubs))


def feature_tiles(features: tuple[StreetFeature, ...]) -> tuple[tuple[int, int], ...]:
    """Every tile a feature's pad covers, sorted. The generator paves these
    (grass-only): for a 1x1 apron or dock the tile is already ROAD and nothing
    changes, so in practice this is how a plaza's forecourt gets its pavement.
    """
    tiles = {(f.x + dx, f.y + dy) for f in features for dx in range(f.w) for dy in range(f.h)}
    return tuple(sorted(tiles))


def _lane_tiles(
    routes: dict[tuple[str, str], tuple[tuple[int, int], ...]],
    positions: dict[str, tuple[int, int]],
    connected: list[str],
    big: frozenset[str],
) -> tuple[tuple[int, int], ...]:
    """Merged runs keep their combined thickness — but only flows moving the
    SAME WAY merge. Counts are per direction, so two streets CROSSING at right
    angles (one vertical, one horizontal) widen nothing: the old any-direction
    count dropped a single orphan lane tile at every crossing, which read as a
    dead-end stub (Stephen, 2026-08-05). Vertical runs grow east up to
    LANE_CAP lanes, horizontal runs one row south (H_LANE_CAP), into space the
    unit allocation reserved. Corners count as vertical."""
    v_count: dict[tuple[int, int], int] = {}
    h_count: dict[tuple[int, int], int] = {}
    for route in routes.values():
        seen: set[tuple[int, int]] = set()
        for i in range(1, len(route) - 1):
            t = route[i]
            if t in seen:
                continue
            seen.add(t)
            vertical = route[i - 1][0] == t[0] or route[i + 1][0] == t[0]
            counts = v_count if vertical else h_count
            counts[t] = counts.get(t, 0) + 1
    lot_positions = {
        (positions[k][0] + dx, positions[k][1] + dy)
        for k in connected
        for dx in range(2 if k in big else 1)
        for dy in range(2 if k in big else 1)
    }
    tiles: set[tuple[int, int]] = set()
    for (tx0, ty0), c in v_count.items():
        for lane in range(1, min(c, LANE_CAP)):
            tiles.add((tx0 + lane, ty0))
    for (tx0, ty0), c in h_count.items():
        for lane in range(1, min(c, H_LANE_CAP)):
            tiles.add((tx0, ty0 + lane))
    tiles -= lot_positions  # a lane may never claim a building
    return tuple(sorted(tiles))
