"""The streets v5 pipeline, assembled once — the thing every spike 5/6 tool runs.

Not a test, and not a module: `scripts/spike_arterials.py` (the 2D sheet) and
`scripts/spike_city_json.py` (the 3D bridge) both need the SAME plan, and a
second assembly order would make the two pictures disagree about a city they
both claim to be showing. Split out of `spike_arterials.py` at the line law
when spike 5 pushed it past 500 lines.

`plan_dag_layout` is still the only planner the app, the contract and the tests
reach; everything here is reachable from `scripts/` and nowhere else.

The ORDER is the architectural claim, and it is why hierarchy widths were cheap:

    precincts -> slots -> lattice -> ROUTING -> width classes -> junction rule
             -> the ONE prefix sum (`resolve_coordinates`) -> endings

Routing happens entirely in lattice space over `town_arterials`' unit graph with
DOORS as endpoints. Width classes are decided after it. `resolve_coordinates`
runs once, last, and is handed the final widths. Only then does anything know a
tile exists — which is what lets the endings taxonomy attach to a building's
real kerb.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spike_fixtures import shuffled  # noqa: E402
from spike_streetmetrics import road_tiles  # noqa: E402

from dbtycoon.catalog.models import PipelineContext  # noqa: E402
from dbtycoon.sim.layout import _known_edges, compute_depths  # noqa: E402
from dbtycoon.sim.town_arterials import (  # noqa: E402
    downstream_reach,
    measure_carriers,
    measure_closure,
    plan_arterials,
    trim_dangles,
)
from dbtycoon.sim.town_blocks import (  # noqa: E402
    INTERNAL,
    plan_lattice,
    plan_precincts,
    resolve_coordinates,
)
from dbtycoon.sim.town_endings import (  # noqa: E402
    door_kinds,
    plan_endings,
    plan_umbilical,
)
from dbtycoon.sim.town_hierarchy import (  # noqa: E402
    BUCKETS,
    WIDTH_MEASURE,
    avenue_lines,
    classify,
    line_widths,
    step_down,
    unit_tiles,
)
from dbtycoon.sim.town_rows import big_lots  # noqa: E402
from dbtycoon.sim.town_zoning import (  # noqa: E402
    CELL_SIZE,
    block_demand,
    door_unit,
    plan_slots,
    plan_zoning,
    solid_blocks,
    unit_cover,
)


class Built:
    """One fixture, planned all the way through. Plain attributes on purpose —
    this is a spike harness, not a contract."""

    __slots__ = (
        "carriers_measure",
        "cover",
        "ctx",
        "dressed",
        "edges",
        "endings",
        "lattice",
        "plan",
        "precincts",
        "roads",
        "stubs",
        "tiles",
        "trimmed",
        "umbilical",
        "units",
        "width",
        "zone",
    )


def important_leaves(ctx: PipelineContext, edges: list[tuple[str, str]]) -> frozenset[str]:
    """The marts that earn a PLAZA rather than an apron: a sink (nothing reads
    it) that at least two things feed. Measured, like every other v5 number —
    "important" cannot be a name pattern or a style rule."""
    feeds: dict[str, int] = {}
    outgoing: set[str] = set()
    for src, dst in edges:
        feeds[dst] = feeds.get(dst, 0) + 1
        outgoing.add(src)
    return frozenset(k for k, n in feeds.items() if n >= 2 and k not in outgoing)


def build(
    ctx: PipelineContext,
    cell: int = CELL_SIZE,
    measure: str = WIDTH_MEASURE,
    junction: bool = True,
) -> Built:
    """precincts -> slots -> lattice -> ROUTING -> widths -> the one prefix sum.

    The order is the claim. Routing happens entirely in lattice space over
    `town_arterials`' unit graph with doors as endpoints; width classes are
    decided after it; `resolve_coordinates` runs once, last, and is handed the
    FINAL widths. Nothing before it reserves a tile.
    """
    out = Built()
    out.ctx = ctx
    precincts = plan_precincts(ctx, demand=block_demand(ctx))
    slots = plan_slots(ctx, precincts)
    lattice = plan_lattice(precincts, solid=solid_blocks(slots))
    doors = {key: door_unit(slot) for key, slot in slots.items()}
    edges = sorted({(s, d) for s, d in _known_edges(ctx) if s != d})

    plan = plan_arterials(lattice, doors, edges)

    # What a road END is allowed to be: a door (apron / dock / plaza), a unit
    # carrying a route (its far end IS a door), or a suburban cul-de-sac stub
    # (bulb). Everything else that dangles is the naked stub theme 7 forbids.
    stubs = frozenset(
        (seg.key.axis, seg.key.line, pos)
        for seg in lattice.segments
        if seg.role == INTERNAL
        for pos in range(seg.key.start, seg.key.end)
    )
    dressed = frozenset(set(doors.values()) | {u for u in plan.units if plan.carriers[u]} | stubs)
    units, trimmed = trim_dangles(plan, dressed)

    reach = downstream_reach(sorted(o.key for o in ctx.objects), edges)
    values = measure_carriers(plan) if measure == "carriers" else measure_closure(plan, reach)
    width = classify(plan, values, BUCKETS[measure], units)
    width = step_down(width, exempt=frozenset(stubs & set(units)))

    # The junction rule (spike 5): only the lines that EARNED an avenue over
    # most of their own length, and at most one per axis, resolve three tiles
    # wide. `None` here is spike 4's behaviour and the A/B (`--no-junction`).
    allow = avenue_lines(width) if junction else None
    v_width, h_width = line_widths(width, lattice.v_lines, lattice.h_lines, allow)
    tiles = resolve_coordinates(lattice, cell_size=cell, v_width=v_width, h_width=h_width)
    cover = unit_cover(units)

    out.precincts, out.lattice, out.plan = precincts, lattice, plan
    out.edges, out.stubs, out.dressed = edges, stubs, dressed
    out.units, out.trimmed, out.width = units, trimmed, width
    out.tiles, out.cover = tiles, cover
    out.zone = plan_zoning(ctx, lattice, tiles, cover)
    out.roads = road_tiles(units, tiles, unit_tiles)

    # Spike 5: one root, then every ending dressed — over dirt as well.
    out.umbilical = plan_umbilical(tiles, units)
    kinds = door_kinds(
        tuple(sorted(slots)),
        big_lots(ctx),
        compute_depths(ctx),
        important_leaves(ctx, edges),
        frozenset(src for src, _dst in edges),
    )
    out.endings = plan_endings(tiles, units, out.zone.slot_of, kinds, frozenset(stubs & set(units)), out.umbilical)
    if out.umbilical is not None:
        out.roads = out.roads | set(out.umbilical.road)
    return out


# --- determinism -----------------------------------------------------------


def arterial_fingerprint(ctx: PipelineContext, cell: int, measure: str, junction: bool = True) -> str:
    """sha256 over the ROUTED network: every surviving unit with its surface,
    its carrying edges and its width class, every route, every resolved line
    width, every door — and, from spike 5, every dressed ENDING and the
    umbilical.

    A third harness beside the lattice and zoning ones. Routing is where a
    float cost or a dict-order tiebreak would hide: it would pass every other
    check on this bench and produce a different city on a customer's catalog.
    The endings join it because the taxonomy reads `big_lots` and a
    downstream-edge count, both of which are exactly the shape of input a
    non-sorted walk would reorder.
    """
    b = build(ctx, cell, measure, junction)
    parts = [f"grid {b.tiles.width}x{b.tiles.height} lines {b.lattice.v_lines}x{b.lattice.h_lines}"]
    parts += [f"vw {list(b.tiles.v_w)}", f"hw {list(b.tiles.h_w)}"]
    for unit in b.units:
        parts.append(f"unit {unit} {b.plan.surface_of[unit]} w{b.width[unit]} carriers{list(b.plan.carriers[unit])}")
    for edge in sorted(b.plan.routes):
        parts.append(f"route {edge} {list(b.plan.routes[edge])}")
    parts.append(f"unrouted {list(b.plan.unrouted)}")
    for key in sorted(b.zone.slot_of):
        parts.append(f"door {key} {door_unit(b.zone.slot_of[key])} {b.zone.door_of[key]}")
    for e in b.endings:
        parts.append(f"ending {e.kind} {e.x},{e.y} {e.w}x{e.h} {e.facing} {e.key}")
    parts.append(f"umbilical {b.umbilical.node if b.umbilical else None}")
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:16]


def shuffle_check(
    ctx: PipelineContext, cell: int, measure: str, digest: str, junction: bool = True
) -> tuple[bool, str]:
    for seed in (1, 2, 3):
        other = arterial_fingerprint(shuffled(ctx, seed), cell, measure, junction)
        if other != digest:
            return False, other
    return True, digest
