"""Streets v5, SPIKE 1: the bare LATTICE — city blocks before any building.

**Not wired into anything.** `plan_dag_layout` is still the only planner the
app, the contract and the tests reach; nothing here is imported by `layout`,
`town_plan`, `city_json` or any test. The callers are `scripts/spike_lattice.py`
and `town_zoning`, which render it so it can be JUDGED before a rule is written
(four spec-first geometry attempts have been wrong in this repo).

The v4 planner is a layered-DAG diagram: depth columns, routing channels, every
street an A->B path, every ending a dead end, no closed blocks. v5 rebuilds
placement around city BLOCKS, decided entirely in **lattice space** — block,
line and cell indices — and converted to tiles by exactly ONE function that
runs last (`resolve_coordinates`). That is what makes hierarchy widths cheap
later: widths are computed after routing and coordinates fall out of a prefix
sum over the FINAL widths, so nothing reserves width pessimistically.

What this round decides, and nothing more:

  precinct  a schema band at a depth, promoted from a row range to a
            rectangular PLOT OF LAND, west->east by depth so the raw->marts
            reading lives in the land; north->south by v4's own band order.
  texture   DERIVED from depth, never styled: depth 0 industrial, max depth
            suburban, everything between downtown (road-grammar theme 4).
  blocks    demand -> a block SHAPE the band can fill (`town_texture`) and an
            arrangement of those near-square ON THE GROUND, plus the lines
            those blocks imply.

**No routing.** Lots are spike 2's (`town_zoning`, which sizes bands through
the `demand` hook and marks whole-block buildings through `solid`).

Spike 3 moved the block SHAPE out to `town_texture`: it is no longer a per-
texture constant but a per-precinct fit, because a band of three objects handed
a block sized for eight is why v5 came out larger than v4 on sparse catalogs.
`Precinct.block_w`/`block_h` are that fit; everything downstream reads them and
nothing reads `BLOCK_CELLS` except the fitter. Pure and deterministic: sorted
everywhere, integer arithmetic only (band order compares exact `Fraction`s,
never float means).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from fractions import Fraction
from math import isqrt

from ..catalog.models import PipelineContext
from .layout import _known_edges, compute_depths
from .town_rows import big_lots, plan_site
from .town_texture import SUBURBAN, block_capacity, fit_blocks, texture_for

# `town_rows.big_lots` priced in CELLS: 2x2 costs what four 1x1s cost.
BIG_CELLS = 4

V, H = "v", "h"
SPINE, EDGE, INTERNAL = "spine", "edge", "internal"
_ROLE_RANK = {SPINE: 0, EDGE: 1, INTERNAL: 2}


@dataclass(frozen=True)
class Precinct:
    """A schema band at a depth, as a rectangle of blocks in lattice space.
    `cell_x`/`cell_y` are the NW corner in CELL coordinates — tiles and widths
    are `resolve_coordinates`' business, once routing has had its say.

    `block_w`/`block_h` are the SHAPE one of this precinct's blocks has, fitted
    to the band's own demand by `town_texture.fit_blocks` — same grain for every
    block of the precinct, but a 3-lot band gets a 3x1 bar where a 9-lot band
    gets 4x2s. Every block of a precinct is the same shape; the variation is
    between precincts, which is what keeps the district reading uniform."""

    pid: str  # "<depth>:<schema>", unique and sortable
    schema: str
    depth: int
    band: int  # north->south order within the depth column
    texture: str
    members: tuple[str, ...]
    capacity: int  # cells demanded by the members, per `demand`
    block_w: int
    block_h: int
    blocks_x: int
    blocks_y: int
    cell_x: int
    cell_y: int

    @property
    def shape(self) -> tuple[int, int]:
        return self.block_w, self.block_h

    @property
    def block_cells(self) -> int:
        """Lots one of this precinct's blocks holds — every cell is fronted."""
        return self.block_w * self.block_h

    @property
    def cells_w(self) -> int:
        return self.blocks_x * self.block_w

    @property
    def cells_h(self) -> int:
        return self.blocks_y * self.block_h

    @property
    def blocks(self) -> int:
        return self.blocks_x * self.blocks_y


@dataclass(frozen=True)
class SegKey:
    """One straight run of lattice line: which line, and the span along it.
    For a `v` segment `line` is a vertical-line index and `start`/`end` are
    horizontal-line indices; for an `h` segment it is the other way round.
    `end` is INCLUSIVE of the line it stops on — that is how junctions fuse."""

    axis: str  # V or H
    line: int
    start: int
    end: int


@dataclass(frozen=True)
class Segment:
    key: SegKey
    role: str  # SPINE (city arterial), EDGE (precinct frame), INTERNAL (block)
    pid: str  # the precinct it belongs to; "" for a spine


@dataclass(frozen=True)
class Lattice:
    """The whole city as lines and the land they enclose. No tiles yet."""

    precincts: tuple[Precinct, ...]
    segments: tuple[Segment, ...]
    v_lines: int  # count of vertical-line indices, 0..v_lines-1
    h_lines: int


@dataclass(frozen=True)
class TileMap:
    """The one and only lattice->tile result. `v_at[i]` is the tile x of
    vertical line `i` and `v_w[i]` the width it resolved at — 0 for a line
    index no segment uses. Everything else derives from those prefix sums."""

    width: int
    height: int
    v_at: tuple[int, ...]
    h_at: tuple[int, ...]
    v_w: tuple[int, ...]
    h_w: tuple[int, ...]
    road_tiles: tuple[tuple[int, int], ...]
    # (pid, x, y, w, h) — the precinct's land in tiles, frame lines included.
    precinct_rects: tuple[tuple[str, int, int, int, int], ...]


# --- precincts: land, not diagram ------------------------------------------


def _band_rank(members: list[str], rows_of: dict[str, int]) -> tuple[Fraction, str]:
    """Mean barycenter rank of a schema's members at one depth — v4's own band
    order, read off `plan_site`. Exact `Fraction`, never a float: this decides
    geometry. Orphans fall to the end, then by name."""
    ranked = sorted(rows_of[k] for k in members if k in rows_of)
    if not ranked:
        return Fraction(1 << 30), min(members)
    return Fraction(sum(ranked), len(ranked)), min(members)


def plan_precincts(
    ctx: PipelineContext,
    demand: Callable[[tuple[str, ...], str, tuple[int, int]], tuple[int, int, int]] | None = None,
) -> tuple[Precinct, ...]:
    """Every (depth, schema) band as a placed rectangle of blocks.

    Placement IS the decision here: west->east by depth so the raw->marts flow
    reads in the LAND, north->south by band order inside each depth column.
    Depth columns share their boundary line (the future avenue), and so do
    stacked precincts; nothing reserves a gap.

    A depth column WRAPS. Round 1 stacked every precinct of a depth in one
    unbroken column, which made near-square true of each precinct and false of
    the city (flat-7x9 came out 15x63 tiles, cap-500 45x103). Each column now
    fills top-to-bottom to a shared target height then starts another to its
    east; the target is `isqrt` of the total land, so the plan lands near
    square whatever the depth histogram is. Every object gets land, orphans
    included — no lineage means depth 0 and a stand in the raw district.

    `demand` is spike 2's band-sizing hook, `(members, texture, shape) ->
    (cells, blocks, spills)`, asked once per CANDIDATE block shape because the answer
    depends on the shape (spike 3). `by_cell` below prices a lot at one cell and
    divides, right for a bare lattice and wrong once buildings land: a big lot
    consumes a WHOLE block whatever its size and a sibling block will not
    straddle a street. `town_zoning.block_demand` knows both.
    """
    keys = sorted(obj.key for obj in ctx.objects)
    if not keys:
        return ()
    schema_of = {obj.key: obj.schema for obj in ctx.objects}
    depths = compute_depths(ctx)
    big = big_lots(ctx)

    edges = sorted({(s, d) for s, d in _known_edges(ctx) if s != d})
    connected = sorted({k for pair in edges for k in pair})
    rows_of: dict[str, int] = {}
    if edges:
        rows_of = dict(plan_site(ctx, edges, {k: depths[k] for k in connected}).rows_of)

    bands: dict[tuple[int, str], list[str]] = {}
    for key in keys:
        bands.setdefault((depths[key], schema_of[key]), []).append(key)
    max_depth = max(depths[k] for k in keys)

    def by_cell(members: tuple[str, ...], _texture: str, shape: tuple[int, int]) -> tuple[int, int, int]:
        cells = sum(BIG_CELLS if k in big else 1 for k in members)
        return cells, -(-cells // block_capacity(shape)), 0

    size_band = demand or by_cell

    # Pass 1: size every band at the origin — sizes decide the wrap target.
    sized: list[Precinct] = []
    for depth in sorted({d for d, _ in bands}):
        texture = texture_for(depth, max_depth)
        column = sorted(
            ((schema, members) for (d, schema), members in bands.items() if d == depth),
            key=lambda item: _band_rank(item[1], rows_of),
        )
        for band, (schema, members) in enumerate(column):
            keys_of_band = tuple(sorted(members))
            shape, blocks_x, blocks_y, capacity = fit_blocks(
                texture, lambda s, m=keys_of_band, t=texture: size_band(m, t, s)
            )
            sized.append(
                Precinct(
                    pid=f"{depth}:{schema}",
                    schema=schema,
                    depth=depth,
                    band=band,
                    texture=texture,
                    members=keys_of_band,
                    capacity=capacity,
                    block_w=shape[0],
                    block_h=shape[1],
                    blocks_x=blocks_x,
                    blocks_y=blocks_y,
                    cell_x=0,
                    cell_y=0,
                )
            )
    target = max(1, isqrt(sum(p.cells_w * p.cells_h for p in sized)))

    # Pass 2: place, wrapping each depth column at that shared target height. A
    # precinct joins the current sub-column while overshooting costs no more
    # than stopping short would (`2*y + h <= 2*target`) — plain next-fit leaves
    # three 4-cell precincts as three sub-columns at target 10, the ribbon.
    #
    # The wrap height is BALANCED per depth (spike 5): a depth that needs `n`
    # sub-columns wraps at `ceil(its own height / n)` rather than at the shared
    # target, so its last sub-column is not the remainder. Next-fit against the
    # shared target is what produced spike 4's L- and T-shaped cities — a depth
    # 2.1 sub-columns tall came out as one full column and one stub, and the
    # empty quadrant beside the stub was the biggest field of grass on the
    # sheet. `n` still comes from the shared target, so the CITY's aspect is
    # decided globally and only the raggedness is fixed locally.
    placed: list[Precinct] = []
    cell_x = 0
    for depth in sorted({p.depth for p in sized}):
        column = [p for p in sized if p.depth == depth]
        tall = sum(p.cells_h for p in column)
        shelves = max(1, -(-tall // max(1, target)))
        wrap = max(1, -(-tall // shelves))
        shelf_x, cell_y, shelf_w = cell_x, 0, 0
        for p in column:
            if cell_y and 2 * cell_y + p.cells_h > 2 * wrap:
                shelf_x, cell_y, shelf_w = shelf_x + shelf_w, 0, 0
            placed.append(replace(p, cell_x=shelf_x, cell_y=cell_y))
            cell_y += p.cells_h
            shelf_w = max(shelf_w, p.cells_w)
        cell_x = shelf_x + shelf_w
    return tuple(sorted(placed, key=lambda p: (p.depth, p.band, p.schema)))


# --- the lattice: which lines exist ----------------------------------------


def _interior_keys(p: Precinct, solid: frozenset[tuple[int, int]]) -> list[SegKey]:
    """The lines INSIDE one precinct's blocks — where texture becomes shape.

    Industrial and downtown have NONE: their whole texture is the block shape
    and the streets are the boundaries between blocks. Round 1 threaded lines
    through both and got a circuit board, every line of it pavement charged
    against a lot that no longer exists.

    Suburban keeps exactly one, and it is a stub rather than a line: a ONE-CELL
    spur off the block's west or east side that dead-ends inside it — the
    cul-de-sac bulb's seed (theme 7) and the dead-end density that reads as
    suburb (theme 2). It alternates on `bx + by + band` so it flips between
    blocks AND stacked precincts; round 1 used `bx + by` and stamped one H down
    the fringe.

    A block in `solid` gets none: theme 3 is verbatim that a building
    consuming a whole block is RINGED by streets, never threaded through, and
    this stub is the only line v5 ever puts inside a block.

    A TRIMMED suburban block gets none either (spike 3): the stub is half the
    block wide, so on a one-cell-wide block it stops being a stub and becomes a
    cross street cutting the block in two, and on a one-cell-tall block it lands
    on the block's own north edge. Both are the moat round 1 paid for. Suburbs
    small enough to be trimmed that far read as suburb from the vertical grain
    alone.
    """
    bw, bh = p.block_w, p.block_h
    if p.texture != SUBURBAN or bw < 2 or bh < 2:
        return []
    out: list[SegKey] = []
    for bx in range(p.blocks_x):
        for by in range(p.blocks_y):
            x0, y0 = p.cell_x + bx * bw, p.cell_y + by * bh
            if (x0, y0) in solid:
                continue
            mid = y0 + bh // 2
            if (bx + by + p.band) % 2 == 0:
                out.append(SegKey(H, mid, x0, x0 + 1))
            else:
                out.append(SegKey(H, mid, x0 + bw - 1, x0 + bw))
    return out


def plan_lattice(
    precincts: tuple[Precinct, ...],
    top_arterial: bool = True,
    solid: frozenset[tuple[int, int]] = frozenset(),
) -> Lattice:
    """Every line the placed precincts imply, as sorted segments.

    Three roles, and the order they resolve in when two coincide: SPINE (a
    depth boundary — the arterial the district drains onto), EDGE (a precinct's
    frame and its block boundaries) and INTERNAL. Segments are deduplicated by
    key but NOT split where they overlap; splitting is routing's job. `solid`
    (`town_zoning.solid_blocks`) is the NW cell of every block one building
    consumes whole; those get no interior line.
    """
    if not precincts:
        return Lattice(precincts=(), segments=(), v_lines=0, h_lines=0)

    v_lines = max(p.cell_x + p.cells_w for p in precincts) + 1
    h_lines = max(p.cell_y + p.cells_h for p in precincts) + 1

    best: dict[SegKey, Segment] = {}

    def add(key: SegKey, role: str, pid: str) -> None:
        if key.end <= key.start:
            return
        current = best.get(key)
        if current is None or _ROLE_RANK[role] < _ROLE_RANK[current.role]:
            best[key] = Segment(key=key, role=role, pid=pid)

    # The arterials: one vertical line at every DEPTH boundary and no others.
    # One continuous spine plus ribs is the strongest city tell (theme 1), but
    # only where there is city: a spine runs exactly as far south as the
    # deepest precinct of the depths it borders. The first spike render
    # promoted every precinct's own east edge instead, and each narrow precinct
    # grew an arterial dangling into open grass. Keyed by DEPTH, not `cell_x`:
    # the column wraps, so one depth owns several sub-columns and only its
    # outer two boundaries are arterial — the seams between them are streets.
    spans: dict[int, tuple[int, int, int]] = {}  # depth -> (x_west, x_east, deep)
    for p in precincts:
        west, east, deep = spans.get(p.depth, (p.cell_x, p.cell_x, 0))
        east, deep = max(east, p.cell_x + p.cells_w), max(deep, p.cell_y + p.cells_h)
        spans[p.depth] = (min(west, p.cell_x), east, deep)
    reach: dict[int, int] = {}
    for _depth, (west, east, deep) in sorted(spans.items()):
        for boundary in (west, east):
            reach[boundary] = max(reach.get(boundary, 0), deep)
    for x in sorted(reach):
        add(SegKey(V, x, 0, reach[x]), SPINE, "")
    # One east-west arterial along the northern edge, tying every depth's
    # spines together. Precincts touch by construction, but only where their
    # widths agree: a narrow band leaves its neighbours' frames meeting nothing
    # and the footprint reads as scattered islands (theme 5). Every depth
    # starts at y=0, so the north edge crosses all of them without cutting a
    # block — the cheapest honest connector until routing exists.
    if top_arterial:
        add(SegKey(H, 0, 0, v_lines - 1), SPINE, "")

    for p in sorted(precincts, key=lambda p: (p.cell_x, p.cell_y, p.pid)):
        bw, bh = p.block_w, p.block_h
        x0, y0 = p.cell_x, p.cell_y
        x1, y1 = x0 + p.cells_w, y0 + p.cells_h
        # The frame.
        add(SegKey(V, x0, y0, y1), EDGE, p.pid)
        add(SegKey(V, x1, y0, y1), EDGE, p.pid)
        add(SegKey(H, y0, x0, x1), EDGE, p.pid)
        add(SegKey(H, y1, x0, x1), EDGE, p.pid)
        # Block boundaries inside the precinct.
        for b in range(1, p.blocks_x):
            add(SegKey(V, x0 + b * bw, y0, y1), EDGE, p.pid)
        for b in range(1, p.blocks_y):
            add(SegKey(H, y0 + b * bh, x0, x1), EDGE, p.pid)
        for key in _interior_keys(p, solid):
            add(key, INTERNAL, p.pid)

    segments = tuple(sorted(best.values(), key=lambda s: (s.key.axis, s.key.line, s.key.start, s.key.end)))
    return Lattice(precincts=precincts, segments=segments, v_lines=v_lines, h_lines=h_lines)


# --- the single lattice -> tile conversion; all above is index arithmetic --


def resolve_coordinates(
    lattice: Lattice,
    margin: int = 3,
    cell_size: int = 3,
    v_width: dict[int, int] | None = None,
    h_width: dict[int, int] | None = None,
) -> TileMap:
    """Turn line indices into tile coordinates by prefix-summing FINAL widths.

    This is the only function in v5 that knows a tile exists, and it runs last.
    `v_width`/`h_width` are per-line street widths, defaulting to 1 for a line
    SOME segment uses and 0 for one no segment uses: hierarchy widths (theme 1,
    road width = downstream dependency count) land by filling those maps in
    after routing, and no earlier pass reserves width for a decision it cannot
    yet make — the point of doing this in lattice space. The ZERO is
    load-bearing: round 1 gave every line a tile whether a street ran there or
    not, leaving a moat between two lots of one block (21389 -> 13619 tiles).

    A cell is `cell_size` tiles square. It was 1 in spike 1: a 1-tile lot
    bought with a 1-tile street is a 1:1 trade and 60% of settled land came out
    pavement, which no block shape can beat. It went to 2 in spike 2 and is
    **3 from spike 5**, which is Stephen's call off the spike-4 sheets: with
    hierarchy widths in, cell 2 measured 65% paved / 29% built on the settled
    land and cell 3 measures 52/39 for 0.22x v4's area instead of 0.15x.
    `--cell 2` is the A/B.
    """
    used_v = {seg.key.line for seg in lattice.segments if seg.key.axis == V}
    used_h = {seg.key.line for seg in lattice.segments if seg.key.axis == H}
    vw = {i: (1 if i in used_v else 0) for i in range(lattice.v_lines)} | (v_width or {})
    hw = {i: (1 if i in used_h else 0) for i in range(lattice.h_lines)} | (h_width or {})

    def prefix(count: int, widths: dict[int, int]) -> tuple[tuple[int, ...], int]:
        """Line index -> tile, plus the span: the cursor lands just past the
        last line's width, so the extent is one margin further on."""
        at: list[int] = []
        cursor = margin
        for i in range(count):
            at.append(cursor)
            cursor += widths[i] + (cell_size if i + 1 < count else 0)
        return tuple(at), (cursor + margin if count else 2 * margin)

    v_at, width = prefix(lattice.v_lines, vw)
    h_at, height = prefix(lattice.h_lines, hw)

    tiles: set[tuple[int, int]] = set()
    for seg in lattice.segments:
        k = seg.key
        if k.axis == V:
            x0, xw = v_at[k.line], vw[k.line]
            y0, y1 = h_at[k.start], h_at[k.end] + hw[k.end]
            for x in range(x0, x0 + xw):
                tiles.update((x, y) for y in range(y0, y1))
        else:
            y0, yw = h_at[k.line], hw[k.line]
            x0, x1 = v_at[k.start], v_at[k.end] + vw[k.end]
            for y in range(y0, y0 + yw):
                tiles.update((x, y) for x in range(x0, x1))

    rects = tuple(
        (
            p.pid,
            v_at[p.cell_x],
            h_at[p.cell_y],
            v_at[p.cell_x + p.cells_w] + vw[p.cell_x + p.cells_w] - v_at[p.cell_x],
            h_at[p.cell_y + p.cells_h] + hw[p.cell_y + p.cells_h] - h_at[p.cell_y],
        )
        for p in sorted(lattice.precincts, key=lambda p: p.pid)
    )
    return TileMap(
        width=width,
        height=height,
        v_at=v_at,
        h_at=h_at,
        v_w=tuple(vw[i] for i in range(lattice.v_lines)),
        h_w=tuple(hw[i] for i in range(lattice.h_lines)),
        road_tiles=tuple(sorted(tiles)),
        precinct_rects=rects,
    )
