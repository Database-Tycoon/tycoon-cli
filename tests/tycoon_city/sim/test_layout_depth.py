import sys
from collections import deque

from tycoon_city.catalog.models import CatalogObject, Edge, PipelineContext
from tycoon_city.sim.layout import compute_depths, isolated_keys


def _ctx(objects, edges=()):
    return PipelineContext("demo", tuple(objects), tuple(edges))


def _obj(schema, name):
    return CatalogObject(schema, name, "table", 0)


def test_linear_chain_increments_depth():
    ctx = _ctx(
        [_obj("raw", "a"), _obj("stg", "b"), _obj("mart", "c")],
        [Edge("raw.a", "stg.b"), Edge("stg.b", "mart.c")],
    )
    assert compute_depths(ctx) == {"raw.a": 0, "stg.b": 1, "mart.c": 2}


def test_diamond_takes_longest_path():
    # a -> b -> d and a -> c -> d; d must be 2, not 1.
    ctx = _ctx(
        [_obj("s", "a"), _obj("s", "b"), _obj("s", "c"), _obj("s", "d")],
        [
            Edge("s.a", "s.b"),
            Edge("s.a", "s.c"),
            Edge("s.b", "s.d"),
            Edge("s.c", "s.d"),
        ],
    )
    assert compute_depths(ctx) == {"s.a": 0, "s.b": 1, "s.c": 1, "s.d": 2}


def test_isolated_object_is_depth_zero():
    ctx = _ctx([_obj("raw", "lonely")])
    assert compute_depths(ctx) == {"raw.lonely": 0}


def test_unfed_cycle_is_a_source():
    # a -> b is a clean chain; c <-> d is a cycle that nothing feeds.
    #
    # The {c, d} component has no incoming edge from outside itself, so it is a
    # source and lands at depth 0 -- like the isolated object above, and for the
    # same reason. Its two members share one depth because every edge inside a
    # component runs between mutually reachable objects.
    #
    # This asserted 2 (the acyclic maximum plus one) until the depth pass was
    # rebuilt on component condensation. That value encoded a fallback rather
    # than a design: it was whatever Kahn's algorithm had left unresolved, and it
    # made a cycle's depth depend on the length of unrelated chains elsewhere in
    # the catalog. The owner ruled that the source reading governs.
    ctx = _ctx(
        [_obj("s", "a"), _obj("s", "b"), _obj("s", "c"), _obj("s", "d")],
        [Edge("s.a", "s.b"), Edge("s.c", "s.d"), Edge("s.d", "s.c")],
    )
    depths = compute_depths(ctx)
    assert depths["s.a"] == 0
    assert depths["s.b"] == 1
    assert depths["s.c"] == 0
    assert depths["s.d"] == 0


def test_edges_referencing_unknown_keys_are_ignored():
    ctx = _ctx([_obj("raw", "a")], [Edge("raw.a", "gone.b")])
    assert compute_depths(ctx) == {"raw.a": 0}


def _reachable_pairs(edges):
    """Transitive closure of the edge set, as a set of (src, dst) pairs."""
    succ: dict[str, set[str]] = {}
    for e in edges:
        succ.setdefault(e.src, set()).add(e.dst)
        succ.setdefault(e.dst, set())
    pairs = set()
    for start in succ:
        seen = set()
        queue = deque(succ[start])
        while queue:
            node = queue.popleft()
            if node in seen:
                continue
            seen.add(node)
            pairs.add((start, node))
            queue.extend(succ.get(node, ()))
    return pairs


def _assert_depth_never_decreases(ctx):
    """For every known edge: depth strictly increases, or the ends are in a cycle."""
    depths = compute_depths(ctx)
    keys = {obj.key for obj in ctx.objects}
    known = [e for e in ctx.edges if e.src in keys and e.dst in keys]
    reachable = _reachable_pairs(known)
    for edge in known:
        mutual = (edge.src, edge.dst) in reachable and (edge.dst, edge.src) in reachable
        if mutual:
            assert depths[edge.dst] == depths[edge.src], f"{edge} spans a cycle unevenly"
        else:
            assert depths[edge.dst] > depths[edge.src], f"{edge} decreases or flattens depth: {depths}"


def test_successor_of_a_cycle_sits_deeper_than_the_cycle():
    # Reviewer-verified regression: a -> x, c <-> d, c -> x. x is a successor of
    # c, so it must not land at a lower depth than c.
    ctx = _ctx(
        [_obj("s", "a"), _obj("s", "x"), _obj("s", "c"), _obj("s", "d")],
        [Edge("s.a", "s.x"), Edge("s.c", "s.d"), Edge("s.d", "s.c"), Edge("s.c", "s.x")],
    )
    depths = compute_depths(ctx)
    assert depths["s.x"] > depths["s.c"]
    _assert_depth_never_decreases(ctx)


def test_chain_below_a_cycle_steps_up_hop_by_hop():
    # c <-> d then c -> e -> f. The chain must not collapse onto one depth.
    ctx = _ctx(
        [_obj("s", "c"), _obj("s", "d"), _obj("s", "e"), _obj("s", "f")],
        [Edge("s.c", "s.d"), Edge("s.d", "s.c"), Edge("s.c", "s.e"), Edge("s.e", "s.f")],
    )
    depths = compute_depths(ctx)
    assert depths["s.e"] > depths["s.c"]
    assert depths["s.e"] > depths["s.d"]
    assert depths["s.f"] > depths["s.e"]
    _assert_depth_never_decreases(ctx)


def test_uneven_diamond_takes_the_long_branch():
    # a -> b -> c -> z, plus the shortcut a -> z. z must be 3, from the long
    # branch, not 1 from the shortcut.
    #
    # test_diamond_takes_longest_path uses a *symmetric* diamond -- both
    # branches length 2 -- so despite its name it cannot tell longest from
    # shortest. Mutation testing proved it: swapping max for min in the
    # relaxation left all 99 tests green. Only unequal-length converging paths
    # catch that, and a min-relaxation here makes edge c -> z decrease depth,
    # which is the exact bug this fix exists to prevent.
    ctx = _ctx(
        [_obj("s", "a"), _obj("s", "b"), _obj("s", "c"), _obj("s", "z")],
        [Edge("s.a", "s.b"), Edge("s.b", "s.c"), Edge("s.c", "s.z"), Edge("s.a", "s.z")],
    )
    assert compute_depths(ctx) == {"s.a": 0, "s.b": 1, "s.c": 2, "s.z": 3}
    _assert_depth_never_decreases(ctx)


def test_depth_never_decreases_across_a_known_edge():
    graphs = [
        # Clean chain.
        ([("s", "a"), ("s", "b"), ("s", "c")], [("s.a", "s.b"), ("s.b", "s.c")]),
        # Diamond, symmetric branches.
        (
            [("s", "a"), ("s", "b"), ("s", "c"), ("s", "d")],
            [("s.a", "s.b"), ("s.a", "s.c"), ("s.b", "s.d"), ("s.c", "s.d")],
        ),
        # Uneven diamond: a 3-hop branch racing a 1-hop shortcut. Without this
        # shape the whole list is blind to a shortest-path relaxation.
        (
            [("s", "a"), ("s", "b"), ("s", "c"), ("s", "z")],
            [("s.a", "s.b"), ("s.b", "s.c"), ("s.c", "s.z"), ("s.a", "s.z")],
        ),
        # Uneven diamond where the shortcut lands mid-branch instead.
        (
            [("s", "a"), ("s", "b"), ("s", "c"), ("s", "d"), ("s", "z")],
            [
                ("s.a", "s.b"),
                ("s.b", "s.c"),
                ("s.c", "s.d"),
                ("s.d", "s.z"),
                ("s.a", "s.d"),
                ("s.b", "s.z"),
            ],
        ),
        # Uneven paths converging past a cycle: the long branch runs through
        # c <-> d, so the component condensation has to be right too.
        (
            [("s", "a"), ("s", "c"), ("s", "d"), ("s", "e"), ("s", "z")],
            [
                ("s.a", "s.c"),
                ("s.c", "s.d"),
                ("s.d", "s.c"),
                ("s.d", "s.e"),
                ("s.e", "s.z"),
                ("s.a", "s.z"),
            ],
        ),
        # Cycle fed from outside, then draining into a chain.
        (
            [("s", "a"), ("s", "c"), ("s", "d"), ("s", "e"), ("s", "f")],
            [
                ("s.a", "s.c"),
                ("s.c", "s.d"),
                ("s.d", "s.c"),
                ("s.d", "s.e"),
                ("s.e", "s.f"),
            ],
        ),
        # Three-node cycle with a shortcut edge into a shared successor.
        (
            [("s", "a"), ("s", "b"), ("s", "c"), ("s", "z")],
            [
                ("s.a", "s.b"),
                ("s.b", "s.c"),
                ("s.c", "s.a"),
                ("s.a", "s.z"),
                ("s.b", "s.z"),
            ],
        ),
        # Two independent roots converging far downstream.
        (
            [("s", "a"), ("s", "b"), ("s", "m"), ("s", "n"), ("s", "z")],
            [("s.a", "s.m"), ("s.b", "s.n"), ("s.m", "s.z"), ("s.n", "s.z")],
        ),
    ]
    for objects, edges in graphs:
        ctx = _ctx([_obj(s, n) for s, n in objects], [Edge(a, b) for a, b in edges])
        _assert_depth_never_decreases(ctx)


def test_self_loop_terminates_and_returns_a_depth():
    ctx = _ctx([_obj("s", "a")], [Edge("s.a", "s.a")])
    assert compute_depths(ctx) == {"s.a": 0}


def test_two_disjoint_cycles_terminate():
    ctx = _ctx(
        [_obj("s", "a"), _obj("s", "b"), _obj("s", "c"), _obj("s", "d")],
        [
            Edge("s.a", "s.b"),
            Edge("s.b", "s.a"),
            Edge("s.c", "s.d"),
            Edge("s.d", "s.c"),
        ],
    )
    depths = compute_depths(ctx)
    assert set(depths) == {"s.a", "s.b", "s.c", "s.d"}
    assert depths["s.a"] == depths["s.b"]
    assert depths["s.c"] == depths["s.d"]


def test_depths_are_independent_of_input_ordering():
    objects = [_obj("s", "a"), _obj("s", "b"), _obj("s", "c"), _obj("s", "d")]
    edges = [Edge("s.a", "s.b"), Edge("s.b", "s.c"), Edge("s.c", "s.b"), Edge("s.c", "s.d")]
    forward = compute_depths(_ctx(objects, edges))
    reversed_ = compute_depths(_ctx(list(reversed(objects)), list(reversed(edges))))
    assert forward == reversed_


def _stack_depth() -> int:
    """Frames currently on the stack, so a limit can be set relative to here."""
    depth = 0
    frame = sys._getframe()
    while frame is not None:
        depth += 1
        frame = frame.f_back
    return depth


def test_a_catalog_at_the_loader_cap_terminates_without_deep_recursion():
    # MAX_OBJECTS, the loader's cap, is 500 -- so this uses 500. One long cycle
    # plus a chain hanging off it: a naive relax-to-a-fixed-point would never
    # settle, and a recursive Tarjan would need a frame per node.
    #
    # The recursion limit is the point of this test. Without lowering it, 500
    # nodes sit comfortably under Python's default 1000 and a textbook recursive
    # Tarjan passes -- mutation testing confirmed it did. The limit is set
    # relative to the current stack so the headroom is real but far below the
    # node count: an implementation that recurses per node cannot fit in it.
    names = [f"n{i:03d}" for i in range(500)]
    objects = [_obj("s", n) for n in names]
    edges = [Edge(f"s.{a}", f"s.{b}") for a, b in zip(names, names[1:], strict=False)]
    edges.append(Edge(f"s.{names[199]}", "s.n000"))  # closes a 200-node cycle
    ctx = _ctx(objects, edges)

    original = sys.getrecursionlimit()
    # try/finally, not a bare call: a failure here must not leave every later
    # test running under a crippled interpreter limit.
    try:
        sys.setrecursionlimit(_stack_depth() + 60)
        depths = compute_depths(ctx)
    finally:
        sys.setrecursionlimit(original)

    assert len(depths) == 500
    assert depths["s.n000"] == depths["s.n199"]  # one component
    assert depths["s.n399"] > depths["s.n200"]  # the tail still steps up
    assert depths["s.n499"] > depths["s.n399"]  # ...all the way out


def test_isolated_keys_finds_only_edgeless_objects():
    ctx = _ctx(
        [_obj("raw", "a"), _obj("stg", "b"), _obj("raw", "orphan")],
        [Edge("raw.a", "stg.b")],
    )
    assert isolated_keys(ctx) == {"raw.orphan"}


def test_isolated_keys_ignores_edges_to_unknown_keys():
    # An edge pointing at an object that is not in the catalog does not rescue
    # raw.a from isolation -- it has no edge to anything that exists.
    ctx = _ctx([_obj("raw", "a")], [Edge("raw.a", "gone.b")])
    assert isolated_keys(ctx) == {"raw.a"}
