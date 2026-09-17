"""Schema precincts: one neighbourhood per schema, dealt into rings by depth.

Split out of `town_plan.py` on 2026-09-12 when the planner passed the
500-line rule. The seam is the planner's first stage: `schema_precincts`
decides WHICH neighbourhoods exist and WHERE each sits on the cell grid.
`town_plan.plan_dag_layout` takes the placed precincts from here and turns
them into a lattice, lots, doors and routes. `town_plan` re-exports this
module's API, so `tycoon_city.sim.town_plan.schema_precincts` remains the
import path of record.

Imports no pygame and holds no rendering concepts.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

from ..catalog.models import PipelineContext
from .layout import _known_edges, compute_depths, longest_chain_depths
from .town_blocks import Precinct
from .town_texture import fit_blocks, texture_for
from .town_zoning import block_demand

NEIGHBOURHOOD_GAP = 1  # empty cells between blobs: Stephen's "mild ~2x" gap
CIVIC_CORE_CELLS = 3  # central cells reserved for the plant + civic buildings

__all__ = ["CIVIC_CORE_CELLS", "NEIGHBOURHOOD_GAP", "schema_precincts"]


def schema_precincts(ctx: PipelineContext, gap: int = NEIGHBOURHOOD_GAP) -> tuple[Precinct, ...]:
    """One placed precinct per schema, in RINGS radiating from the town centre.

    Stephen, 2026-08-14, inverting his 2026-08-10 order: density radiates
    OUTWARD. The gold/mart neighbourhoods are downtown — hugging the civic
    core, premium regardless of table size — ringed by the major int
    neighbourhoods, fanning out to the smaller source neighbourhoods on the
    periphery. Longer routes (a source on the edge reaching a mart downtown
    crosses every ring between) are the accepted price.

    The ring index is the schema's LONGEST-CHAIN depth over the cross-schema
    edge graph (`longest_chain_depths`, cycles condensed), inverted — NOT the
    mean of its members' depths. Mean depth cannot express the directive: on
    dogfood it lands `mart` and `int` in one band, and the whole point is
    that mart sits inside int.

    Within a ring the deal order decides who gets the side centres — the
    kerbs nearest downtown's cross streets. Ties are broken decisively
    (Stephen, same directive: no dwelling, no compromises), in order:

    1. more distinct schemas fed (cross-schema fan-out) — the busiest
       supplier gets the closest kerb;
    2. more members — density tapers laterally as well as radially, so the
       bigger neighbourhood holds the middle of its side;
    3. schema name — determinism's last word.

    `town_blocks.plan_precincts` keys on `(depth, schema)`; this keys on schema
    alone. Kept here rather than as a parameter over there because
    `town_blocks.py` sits at 499 lines against the 500-line law and must be
    SPLIT at its next change, not grown by a second grouping rule.
    """
    keys = sorted(obj.key for obj in ctx.objects)
    if not keys:
        return ()
    schema_of = {obj.key: obj.schema for obj in ctx.objects}
    depths = compute_depths(ctx)
    max_depth = max(depths[k] for k in keys)
    size_band = block_demand(ctx)

    members_of: dict[str, list[str]] = {}
    for key in keys:
        members_of.setdefault(schema_of[key], []).append(key)

    def mean_depth(members: list[str]) -> Fraction:
        """Exact, never a float: this decides geometry, and a tie that resolved
        differently per machine would move whole neighbourhoods."""
        return Fraction(sum(depths[k] for k in members), len(members))

    # Fan-in per schema: the heaviest in-degree among its members decides how
    # much elbow room the neighbourhood claims from its ring neighbours.
    in_deg: dict[str, int] = dict.fromkeys(keys, 0)
    for src, dst in _known_edges(ctx):
        if src != dst and dst in in_deg:
            in_deg[dst] += 1

    # The cross-schema graph: ring rank (longest chain, cycles condensed) and
    # fan-out (distinct schemas fed — tiebreaker 1).
    schemas = sorted(members_of)
    cross = sorted({(schema_of[s], schema_of[d]) for s, d in _known_edges(ctx) if schema_of[s] != schema_of[d]})
    rank = longest_chain_depths(schemas, cross)
    feeds: dict[str, set[str]] = {s: set() for s in schemas}
    for s, d in cross:
        feeds[s].add(d)

    sized: list[Precinct] = []
    for schema in sorted(members_of, key=lambda s: (mean_depth(members_of[s]), s)):
        members = tuple(sorted(members_of[schema]))
        depth = int(mean_depth(list(members)))
        texture = texture_for(depth, max_depth)
        shape, blocks_x, blocks_y, capacity = fit_blocks(texture, lambda s, m=members, t=texture: size_band(m, t, s))
        sized.append(
            Precinct(
                pid=schema,
                schema=schema,
                depth=depth,
                band=0,
                texture=texture,
                members=members,
                capacity=capacity,
                block_w=shape[0],
                block_h=shape[1],
                blocks_x=blocks_x,
                blocks_y=blocks_y,
                cell_x=0,
                cell_y=0,
            )
        )

    def gravity(p: Precinct) -> int:
        """Extra lateral cells around a heavy precinct — capped so one huge
        fan-in cannot blow the map apart."""
        return min(3, max(in_deg[m] for m in p.members) // 3)

    # Ring placement. The civic core reserves the central cells; each depth
    # band is one ring, its precincts dealt round-robin onto the four sides
    # of the bounding box everything inside it occupies. A side keeps a
    # running cursor from its centre outward (alternating sign) so siblings
    # spread along the ring instead of stacking — and when a cursor would
    # overshoot its side, the shell CLOSES and a new one opens around it: a
    # band of 500 one-schema precincts must wrap into concentric shells,
    # not march down four ever-longer arms (measured: the unwrapped cursor
    # built a 2055x1462-tile cross for the loader-cap catalog and planning
    # took 38s; wrapped it is a compact blob again).
    core = CIVIC_CORE_CELLS
    x0, y0, x1, y1 = 0, 0, core, core  # occupied bbox, exclusive on x1/y1
    placed: list[Precinct] = []
    bands: dict[int, list[Precinct]] = {}
    for p in sized:
        bands.setdefault(rank[p.schema], []).append(p)
    for band in bands.values():
        # Deal order within a ring = the tiebreaker ladder in the docstring.
        band.sort(key=lambda p: (-len(feeds[p.schema]), -len(p.members), p.schema))

    # reverse=True is the inversion: the deepest schemas take ring 0, flush
    # against the civic core, and depth-0 sources land on the outermost ring.
    for ring, depth in enumerate(sorted(bands, reverse=True)):
        frozen = (x0, y0, x1, y1)  # this ring rests on the bbox as it was
        cursors = {side: 0 for side in "nesw"}
        side_i = 0
        for p in bands[depth]:
            g = gravity(p)
            # A deterministic lateral stagger (name-derived, never a wall
            # clock or RNG) so opposite rings do not mirror each other —
            # the axial symmetry read as a diagram, not a town.
            stagger = (sum(map(ord, p.pid)) + ring) % 3 - 1
            fx0, fy0, fx1, fy1 = frozen
            side = "nesw"[side_i % 4]
            span = (fx1 - fx0) if side in "ns" else (fy1 - fy0)
            need = (p.cells_w if side in "ns" else p.cells_h) + gap + g
            if abs(cursors[side]) > span // 2 + need:
                # This shell is full on every side by the time one side
                # overshoots this far: close it and open the next one.
                frozen = (x0, y0, x1, y1)
                cursors = {s: 0 for s in "nesw"}
                side_i = 0
                fx0, fy0, fx1, fy1 = frozen
                side = "nesw"[0]
            # FLUSH against the frozen bbox radially — a ring that floats a
            # gap away shares no lattice line with the city inside it, and a
            # street that touches nothing is a neighbourhood no route can
            # reach (measured: 3 of 12 routes dropped at gap 1). The organic
            # spacing lives in the LATERAL cursor instead.
            if side in "ns":
                centre = (fx0 + fx1 - p.cells_w) // 2
                off = cursors[side]
                cursors[side] = -off + (p.cells_w + gap + g if off <= 0 else -(p.cells_w + gap + g))
                cx = centre + off + stagger
                cy = fy0 - p.cells_h if side == "n" else fy1
            else:
                centre = (fy0 + fy1 - p.cells_h) // 2
                off = cursors[side]
                cursors[side] = -off + (p.cells_h + gap + g if off <= 0 else -(p.cells_h + gap + g))
                cy = centre + off + stagger
                cx = fx0 - p.cells_w if side == "w" else fx1
            placed.append(replace(p, band=ring, cell_x=cx, cell_y=cy))
            x0, y0 = min(x0, cx), min(y0, cy)
            x1, y1 = max(x1, cx + p.cells_w), max(y1, cy + p.cells_h)
            side_i += 1

    # Cell coordinates must be non-negative: shift the whole city.
    dx, dy = -min(0, x0), -min(0, y0)
    return tuple(replace(p, cell_x=p.cell_x + dx, cell_y=p.cell_y + dy) for p in placed)
