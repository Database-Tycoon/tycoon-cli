"""Property S8's detector: no two consecutive intersection tiles.

Every fixture here exists to make ONE mutant fail, because this repo's dominant
defect is a guard whose fixture cannot express the thing it claims to check
(`docs/handover.md`, trap 4). Named against the mutant each kills:

  `>= 3` -> `>= 4`        killed by two adjacent T-junctions and NOTHING else:
                          a fixture built from crossroads passes either way.
  orthogonal -> diagonal  killed by the diagonal pair, which must stay LEGAL.
  east-only violations    killed by the vertically adjacent pair.
  degree undercount       killed by asserting the T is degree 3, not 2.
"""

from tycoon_city.sim.road_junctions import check_junctions, degrees


def _straight(length: int, y: int = 0) -> set[tuple[int, int]]:
    return {(x, y) for x in range(length)}


def test_a_plain_street_has_no_intersections_at_all():
    report = check_junctions(_straight(6))
    assert report.road_tiles == 6
    assert report.intersections == ()
    assert report.ok
    assert report.largest_clump == 0


def test_two_T_junctions_with_a_street_tile_between_them_are_lawful():
    # Spurs at x=1 and x=3: one plain road tile (x=2) separates the junctions.
    road = _straight(5) | {(1, 1), (3, 1)}
    report = check_junctions(road)
    assert [t for t in report.intersections] == [(1, 0), (3, 0)]
    assert report.four_ways == ()  # both are THREE-way: the >= 3 threshold matters
    assert report.ok
    assert report.largest_clump == 1  # isolated junctions


def test_two_adjacent_T_junctions_violate_S8():
    # The mutant-killer: spurs at x=1 and x=2, so two degree-3 tiles touch.
    # A `>= 4` threshold would call this lawful. It is not.
    road = _straight(5) | {(1, 1), (2, 1)}
    report = check_junctions(road)
    assert degrees(road)[(1, 0)] == 3
    assert degrees(road)[(2, 0)] == 3
    assert report.violations == (((1, 0), (2, 0)),)
    assert not report.ok
    assert report.largest_clump == 2


def test_diagonally_touching_intersections_stay_lawful():
    # (1,0) and (2,1) are intersections but only touch at a corner. Every path
    # a vehicle can drive between them passes a plain street tile, so S8 holds.
    road = _straight(4) | _straight(4, 1) | {(1, -1), (2, 2)}
    report = check_junctions(road)
    inter = set(report.intersections)
    assert (1, 0) in inter and (2, 1) in inter
    assert ((1, 0), (2, 1)) not in report.violations
    # They are not adjacent to each other; any violations here come from the
    # two parallel streets, which is a different fixture's business.
    assert all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in report.violations)


def test_a_vertically_adjacent_pair_is_caught():
    # A violations scan that only looked east would miss this entirely.
    road = {(0, 0), (1, 0), (2, 0), (1, 1), (0, 1), (2, 1), (1, 2)}
    report = check_junctions(road)
    assert degrees(road)[(1, 0)] >= 3
    assert degrees(road)[(1, 1)] >= 3
    assert ((1, 1), (1, 2)) not in report.violations  # (1,2) is a leaf
    assert ((1, 0), (1, 1)) in report.violations


def test_a_solid_block_is_one_intersection_clump_the_size_of_the_plaza():
    # The paved-plaza shape, in miniature: a filled 3x3. The four edge centres
    # are degree 3, the middle is degree 4, the corners are degree 2 — so this
    # fixture also proves the report distinguishes 3 from 4.
    road = {(x, y) for x in range(3) for y in range(3)}
    report = check_junctions(road)
    assert report.road_tiles == 9
    assert report.four_ways == ((1, 1),)
    assert len(report.intersections) == 5
    assert not report.ok
    assert len(report.clumps) == 1
    assert report.largest_clump == 5


def test_report_is_deterministic_and_sorted_largest_clump_first():
    # Two clumps of different sizes, fed in a shuffled order: the big one leads
    # and every tuple is sorted, so the report can back a byte-stable metric.
    big = {(x, y) for x in range(3) for y in range(3)}
    small = _straight(5, 20) | {(1, 21), (2, 21)}
    road = big | small
    first = check_junctions(road)
    again = check_junctions(set(sorted(road, reverse=True)))
    assert first == again
    assert [len(c) for c in first.clumps] == [5, 2]
    assert first.clumps[0] == tuple(sorted(first.clumps[0]))
