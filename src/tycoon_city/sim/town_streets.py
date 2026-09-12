"""Street features: how a road is allowed to END, and the S7 stub check.

Stephen, 2026-08-05: "there needs to be a clear definition for when and where
a road is allowed to end, and what that looks like." The taxonomy is
`docs/road-grammar.md`'s legal-ending table; this module ships the three
endings a lineage street actually produces, dresses every route endpoint with
one, and detects the naked stubs that remain (property S7). The planner
(`town_plan`) decides the routes; nothing here decides where a building sits.

Imports no pygame and holds no rendering concepts.
"""

from dataclasses import dataclass

# `facing` is the compass direction from the feature tile TOWARD the building
# it serves.
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


def plan_street_features(
    routes: dict[tuple[str, str], tuple[tuple[int, int], ...]],
    lots: dict[str, tuple[int, int]],
    big: frozenset[str],
    depth: dict[str, int],
    access_road: tuple[tuple[int, int], ...],
    firehouse_xy: tuple[int, int],
    doors: dict[str, tuple[int, int]] | None = None,
) -> tuple[StreetFeature, ...]:
    """Dress every road ending. Derived facts only.

    A street ends where it meets a building. Routes run DOOR to DOOR (the
    planner's contract): each endpoint is already the last road tile before
    the building it serves, so the ending is the endpoint itself, facing the
    adjacent tile of its own lot's footprint. An endpoint that does not
    touch its lot's footprint (the zoning placed the anchor elsewhere in the
    block) is left undressed rather than dressed toward a guess. The
    firehouse's access road ends at a civic building, which is its own
    legal ending.

    Kind precedence is `plaza` > `dock` > `apron`, because the two special
    reads can overlap on one building (a raw source can also be a 2x2) and only
    the plaza carries pad geometry: keeping it first is what makes "a pad wider
    than one tile is a plaza" true, which is the invariant the renderer reads.
    """
    features: set[StreetFeature] = set()

    def footprint(key: str) -> set[tuple[int, int]]:
        x0, y0 = lots[key]
        size = 2 if key in big else 1
        return {(x0 + dx, y0 + dy) for dx in range(size) for dy in range(size)}

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
        if kind is PLAZA and key in big:
            # A 2x2 lot's forecourt spans its whole frontage, on the street
            # beside the lot: two tiles tall for an east/west arrival, two
            # tiles wide for a north/south one (lattice routes arrive on
            # either axis). The ground along a frontage is street or pad by
            # construction, never another building; property S7 checks the
            # pad came out paved.
            if step[0]:
                y, h = lots[key][1], 2
            elif step[1]:
                x, w = lots[key][0], 2
        features.add(StreetFeature(kind=kind, x=x, y=y, facing=facing, w=w, h=h))

    def dress_endpoint(road: tuple[int, int], key: str) -> None:
        if key not in lots:
            return  # an upstream data bug must surface as S7, never a raise
        lot = footprint(key)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            toward = (road[0] + dx, road[1] + dy)
            if toward in lot:
                dress(road, toward, key)
                return

    for (src, dst), route in sorted(routes.items()):
        if not route:
            continue
        dress_endpoint(route[0], src)
        dress_endpoint(route[-1], dst)

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
