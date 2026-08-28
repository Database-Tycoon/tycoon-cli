"""Property S8: no two consecutive intersection tiles.

Stephen, 2026-08-07, after road paint went on all sixteen tile variants and the
west half of the dogfood city turned out to be a solid field of four-way stops:
**"You can't have two consecutive intersection tiles."**

`docs/road-grammar.md` carries the rule and the baseline. The definitions, kept
here because a property has to be falsifiable:

    intersection   a road tile with THREE OR MORE road neighbours (T or 4-way)
    consecutive    orthogonally adjacent

S8 is the constructive form of the no-asphalt-plaza rule S7 could never
express. S7 polices where a road ENDS; nothing policed road AREA, so a tangled
DAG could pave a solid field in which every tile passed S7 while the network
stopped being a network. A contiguous paved area is nothing but mutually
adjacent intersections, so S8 outlaws it by construction.

Deliberately cheap and deliberately dependency-free: it reads a set of road
tiles, nothing more. That is what lets the spike gauntlet use it as a metric and
a test use it as a guard from the same code, and it means the check works on any
candidate router's output before that router is wired to anything.

Imports no pygame, no contract types and no planner.
"""

from dataclasses import dataclass

# Orthogonal only. Roads connect orthogonally, so diagonal touching is not
# adjacency here — two intersections corner-to-corner still have a street tile
# between them along every path a vehicle can drive.
NEIGHBOURS = ((0, -1), (1, 0), (0, 1), (-1, 0))

Tile = tuple[int, int]


@dataclass(frozen=True)
class JunctionReport:
    """What S8 sees. `violations` is the verdict; the rest is why."""

    road_tiles: int
    intersections: tuple[Tile, ...]  # sorted; degree >= 3
    four_ways: tuple[Tile, ...]  # sorted; degree == 4
    violations: tuple[tuple[Tile, Tile], ...]  # sorted adjacent intersection pairs
    clumps: tuple[tuple[Tile, ...], ...]  # connected components of intersections,
    # largest first then sorted, so the report is deterministic

    @property
    def ok(self) -> bool:
        """S8 holds when no two intersections touch."""
        return not self.violations

    @property
    def largest_clump(self) -> int:
        """Tiles in the biggest contiguous run of intersections. 1 is lawful —
        an isolated junction. Anything larger IS the plaza, sized."""
        return len(self.clumps[0]) if self.clumps else 0


def degrees(road: set[Tile]) -> dict[Tile, int]:
    """Road neighbours per road tile — the same N/E/S/W count the renderer's
    `road_mask.ts` computes for its sixteen tile variants. Kept in step with it
    on purpose: a rule measured on a different adjacency than the one drawn is
    a rule about a city nobody is looking at."""
    return {tile: sum(((tile[0] + dx, tile[1] + dy) in road) for dx, dy in NEIGHBOURS) for tile in road}


def check_junctions(road_tiles: set[Tile] | frozenset[Tile]) -> JunctionReport:
    """Measure S8 over a road tile set. Pure, sorted, no I/O."""
    road = set(road_tiles)
    deg = degrees(road)
    intersections = {tile for tile, d in deg.items() if d >= 3}

    # Each unordered adjacent pair once: only look east and south.
    violations = tuple(
        sorted(
            (tile, other)
            for tile in intersections
            for other in ((tile[0] + 1, tile[1]), (tile[0], tile[1] + 1))
            if other in intersections
        )
    )

    seen: set[Tile] = set()
    clumps: list[tuple[Tile, ...]] = []
    for start in sorted(intersections):
        if start in seen:
            continue
        stack, members = [start], []
        seen.add(start)
        while stack:
            tile = stack.pop()
            members.append(tile)
            for dx, dy in NEIGHBOURS:
                nxt = (tile[0] + dx, tile[1] + dy)
                if nxt in intersections and nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        clumps.append(tuple(sorted(members)))
    # Largest first so `largest_clump` is O(1); ties broken by position so the
    # whole report is reproducible.
    clumps.sort(key=lambda c: (-len(c), c))

    return JunctionReport(
        road_tiles=len(road),
        intersections=tuple(sorted(intersections)),
        four_ways=tuple(sorted(tile for tile, d in deg.items() if d == 4)),
        violations=violations,
        clumps=tuple(clumps),
    )
