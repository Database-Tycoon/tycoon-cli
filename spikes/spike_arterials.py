"""Spikes 4-5: does the routed network read as a city, and is every ending dressed?

Not a test — the look-first sheet for `dbtycoon.sim.town_arterials`,
`town_hierarchy` and `town_endings`, which are reachable from `scripts/` and
nowhere else. The plan itself is assembled by `spike_v5plan.build`, shared with
the 3D bridge. `plan_dag_layout` is still the only planner the app, the contract
and the tests reach.

Spike 4's three questions stand:

  * **Is the pavement EARNED?** Only a street a lineage edge was routed over is
    paved; the rest is dirt.
  * **Does the hierarchy read?** `--measure carriers` (Stephen's pick,
    2026-08-06) against `--measure closure`; `--ab` renders both.
  * **Is sprawl still priced?** Paved length per destination, and whether the
    38-fixture RANKING survives.

Spike 5 adds three more, and they are what the new columns are for:

  * **Is every ending DRESSED, over dirt as well as pavement?** `NAKED` is
    property S7 extended, measured off the emitted pads; `CAPS`/`cap%` is the
    number that actually judges the grammar, because a cap is the taxonomy's
    last resort and is supposed to be rare enough to be a smell.
  * **Is there ONE root?** `net` counts connected components (theme 5 wants 1)
    and `umb` says whether the map-edge umbilical was placed.
  * **Do wide roads cross like roads or pool like a plaza?** `slab` is the
    biggest avenue-crossing square in tiles and `avT%` the share of road TILES
    painted three wide — the honest cost of a per-LINE width. `--no-junction`
    turns the rule off, which is the A/B.

Usage (Pillow is not a runtime dependency; bring it in for the spike):

    uv run --with pillow python scripts/spike_arterials.py
    uv run --with pillow python scripts/spike_arterials.py --no-junction
    uv run --with pillow python scripts/spike_arterials.py --ab
    uv run --with pillow python scripts/spike_arterials.py --detail cap-500
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spike_fixtures import load_fixtures  # noqa: E402
from spike_lattice import OUT_DIR, contact_sheet, detail  # noqa: E402
from spike_streetmetrics import (  # noqa: E402
    class_histogram,
    components,
    downtown_treed,
    footprint_fill,
    junction_squares,
    land_shares,
    leaf_ends,
    loops_by_texture,
    orphan_tiles,
    paved_per_destination,
    road_tiles,
    seam_geometry,
    spearman,
    surface_split,
    v4_per_destination,
    width_tile_shares,
)
from spike_streetpaint import (  # noqa: E402
    ab_sheet,
    arterial_image,
    lot_tiles,
    naked_lots,
    row_caption,
)
from spike_v5plan import arterial_fingerprint, build, shuffle_check  # noqa: E402

from dbtycoon.catalog.models import PipelineContext  # noqa: E402
from dbtycoon.sim.layout import _known_edges, plan_dag_layout  # noqa: E402
from dbtycoon.sim.town_arterials import JOIN, PAVED, plan_arterials  # noqa: E402
from dbtycoon.sim.town_endings import CAP, kind_histogram, naked_ends  # noqa: E402
from dbtycoon.sim.town_hierarchy import (  # noqa: E402
    WIDTH_MEASURE,
    spine_run,
    step_down_violations,
    touching_violations,
    unit_tiles,
)
from dbtycoon.sim.town_zoning import CELL_SIZE, door_unit  # noqa: E402

# --- the sheet -------------------------------------------------------------


def join_dry_run(ctx: PipelineContext) -> tuple[int, int, int]:
    """Exercise the OSI-B seam without emitting anything: a SECOND
    `plan_arterials` call over the same lattice with `surface=JOIN`.

    The declared pairs used here are synthetic (every same-schema pair that is
    NOT a measured edge), because `joins[]` is not plumbed into the spike bench
    — the point is only that the second call routes over the first one's plan,
    snaps onto its arterials, and can never repaint observed pavement as
    declared. Returns `(join units, paved units overwritten, unrouted)`.
    """
    b = build(ctx)
    schema_of = {obj.key: obj.schema for obj in ctx.objects}
    measured = set(b.edges)
    keys = sorted(b.zone.slot_of)
    declared = sorted(
        (a, c)
        for i, a in enumerate(keys)
        for c in keys[i + 1 :]
        if schema_of.get(a) == schema_of.get(c) and (a, c) not in measured
    )[:24]
    doors = {key: door_unit(slot) for key, slot in b.zone.slot_of.items()}
    after = plan_arterials(b.lattice, doors, declared, surface=JOIN, base=b.plan)
    joins = sum(1 for u in after.units if after.surface_of[u] == JOIN)
    lost = sum(1 for u in after.units if b.plan.surface_of[u] == PAVED and after.surface_of[u] != PAVED)
    return joins, lost, len(after.unrouted) - len(b.plan.unrouted)


def main() -> None:
    args = sys.argv[1:]
    only = args[args.index("--detail") + 1] if "--detail" in args else None
    cell = int(args[args.index("--cell") + 1]) if "--cell" in args else CELL_SIZE
    measure = args[args.index("--measure") + 1] if "--measure" in args else WIDTH_MEASURE
    both = "--ab" in args
    junction = "--no-junction" not in args
    tag = f"-{measure}" + ("" if cell == CELL_SIZE else f"-cell{cell}") + ("" if junction else "-nojunction")
    # The A/B sheet is big and is for ONE decision, so it shows the six fixtures
    # with the most lineage to decide it on — chosen by edge count then by name,
    # never by eye, so the sheet cannot be curated into an answer.
    OUT_DIR.mkdir(exist_ok=True)

    fixtures = load_fixtures(only)
    if not fixtures:
        raise SystemExit(f"no fixture named {only!r}")
    ab_names = {
        name
        for name, _ctx in sorted(
            fixtures,
            key=lambda item: (-len(set(_known_edges(item[1]))), item[0]),
        )[:6]
    }

    rows: list[tuple[str, Image.Image, str]] = []
    pairs: list[tuple[str, Image.Image, Image.Image, str, str]] = []
    print(
        f"{'fixture':<16}{'grid':>11}{'paved':>7}{'dirt':>6}{'p%':>5}"
        f"{'alley':>6}{'strt':>5}{'aven':>5}{'av%':>5}{'STEP':>5}{'spine':>6}"
        f"{'loops':>6}{'dtree':>6}{'leaf':>5}{'NAKED':>6}{'ends':>5}{'CAPS':>5}{'cap%':>5}"
        f"{'slab':>5}{'avT%':>5}{'fill%':>6}{'net':>4}{'umb':>4}"
        f"{'trim':>5}{'seam':>5}{'NOFRT':>6}{'pav%':>5}{'blt%':>5}{'pav/dst':>8}"
        f"{'v5area':>8}{'ratio':>7}  fingerprint      shuf"
    )
    failures: list[str] = []
    totals = Counter()
    v5_sprawl: list[float] = []
    v4_sprawl: list[float] = []
    v5_area = v4_area = 0
    loops_all: dict[str, list[int]] = {}
    paved_share: list[int] = []
    built_share: list[int] = []
    for name, ctx in fixtures:
        b = build(ctx, cell, measure, junction)
        v4 = plan_dag_layout(ctx)
        paved, dirt = surface_split(b.plan, b.units)
        alley, street, avenue = class_histogram(b.width)
        n_units = max(alley + street + avenue, 1)
        violations = step_down_violations(b.width, frozenset(b.stubs & set(b.units)))
        totals["touching"] += touching_violations(b.width, frozenset(b.stubs & set(b.units)))
        # SPIKE 5's S7: read off the emitted pads, not off the intent that
        # produced them, and over dirt exactly as over pavement.
        naked = naked_ends(b.units, b.tiles, b.endings)
        # How many endings there ARE to dress. Reported beside NAKED because
        # zero-out-of-two and zero-out-of-seven-hundred are not the same claim,
        # and this bench turns out to be the first (trap 4: a degenerate fixture
        # makes a guard unfalsifiable and the suite will not tell you).
        leaves = sum(1 for _u in leaf_ends(b.units))
        histogram = kind_histogram(b.endings)
        n_ends = max(len(b.endings), 1)
        _slab_total, slab, _wide = junction_squares(b.units, b.tiles)
        wide_share, _road = width_tile_shares(b.units, b.tiles, unit_tiles)
        lots = lot_tiles(b)
        seam0 = seam_geometry(b.precincts, b.tiles)
        seam1 = orphan_tiles(b.precincts, b.tiles, b.roads, lots)
        paved_tiles = len(road_tiles(tuple(b.plan.paved()), b.tiles, unit_tiles) & b.roads)
        per_dst = paved_per_destination(paved_tiles, b.edges)
        shares = land_shares(b.tiles, b.roads, lots)
        paved_share.append(shares[0])
        built_share.append(shares[1])
        loops = loops_by_texture(b.precincts, b.units)
        for texture, (n, closed, mu) in loops.items():
            row = loops_all.setdefault(texture, [0, 0, 0])
            row[0] += n
            row[1] += closed
            row[2] += mu
        area, v4a = b.tiles.width * b.tiles.height, v4.width * v4.height
        v5_area += area
        v4_area += v4a
        if b.edges:
            v5_sprawl.append(per_dst)
            v4_sprawl.append(v4_per_destination(v4, b.edges))
        totals["paved"] += paved
        totals["dirt"] += dirt
        totals["alley"] += alley
        totals["street"] += street
        totals["avenue"] += avenue
        totals["naked"] += len(naked)
        totals["leaves"] += leaves
        totals["endings"] += len(b.endings)
        totals["islands"] += max(0, components(b.units) - 1)
        totals["no_umbilical"] += 0 if b.umbilical is not None or not b.units else 1
        totals["slab"] += slab
        for kind, n in histogram.items():
            totals[f"end_{kind}"] += n
        totals["trimmed"] += len(b.trimmed)
        totals["seam0"] += seam0
        totals["seam1"] += seam1
        totals["violations"] += len(violations)
        totals["unrouted"] += len(b.plan.unrouted)
        totals["no_frontage"] += len(naked_lots(b))

        digest = arterial_fingerprint(ctx, cell, measure, junction)
        ok, other = shuffle_check(ctx, cell, measure, digest, junction)
        if not ok:
            failures.append(f"{name}: {digest} vs shuffled {other}")
        closed_total = sum(mu for _n, _c, mu in loops.values())
        print(
            f"{name:<16}{b.tiles.width:>5}x{b.tiles.height:<5}{paved:>7}{dirt:>6}"
            f"{100 * paved // max(paved + dirt, 1):>4}%"
            f"{alley:>6}{street:>5}{avenue:>5}{100 * avenue // n_units:>4}%"
            f"{len(violations):>5}{spine_run(b.width):>6}"
            f"{closed_total:>6}{downtown_treed(b.precincts, b.units):>6}"
            f"{leaves:>5}{len(naked):>6}{len(b.endings):>5}{histogram[CAP]:>5}"
            f"{100 * histogram[CAP] // n_ends:>4}%"
            f"{slab:>5}{wide_share:>4}%{footprint_fill(b.tiles):>5}%"
            f"{components(b.units):>4}{('y' if b.umbilical else '-'):>4}"
            f"{len(b.trimmed):>5}{seam1:>5}"
            f"{len(naked_lots(b)):>6}{shares[0]:>4}%{shares[1]:>4}%"
            f"{per_dst:>8.1f}{area:>8}"
            f"{(f'{area / v4a:.2f}x' if v4a else '-'):>7}"
            f"  {digest} {'OK ' if ok else 'DIFFERS'}"
        )
        image = arterial_image(b)
        rows.append((name, image, row_caption(b, measure)))
        if both and (only or name in ab_names):
            other_measure = "closure" if measure == "carriers" else "carriers"
            c = build(ctx, cell, other_measure, junction)
            pairs.append(
                (
                    name,
                    image,
                    arterial_image(c),
                    row_caption(b, measure),
                    row_caption(c, other_measure),
                )
            )

    if only:
        out = OUT_DIR / f"v5-arterials-detail-{only.replace('/', '_')}{tag}.png"
        detail(only, rows[0][1], rows[0][2], out)
        if both:
            ab_sheet(pairs, OUT_DIR / f"v5-width-measure-ab-{only.replace('/', '_')}.png")
    elif both:
        out = OUT_DIR / f"v5-width-measure-ab{'' if cell == CELL_SIZE else f'-cell{cell}'}.png"
        ab_sheet(pairs, out)
    else:
        out = OUT_DIR / f"v5-arterials-contact-sheet{tag}.png"
        contact_sheet(
            rows,
            out,
            title=(
                f"streets v5 SPIKE 5 - dressed endings, the umbilical and the junction rule: "
                f"{len(rows)} fixtures, cell_size={cell}, WIDTH_MEASURE={measure}"
                f"{'' if junction else ', JUNCTION RULE OFF'}"
            ),
            subtitle=(
                "earth = dirt; grey->white = paved alley/street/avenue; bone = lot, "
                "terracotta = whole-block; endings: green apron, YELLOW bulb, white plaza, "
                "orange dock, blue map-edge, MAGENTA cap (the smell)"
            ),
        )
    print(
        f"\nsurfaces: paved={totals['paved']} dirt={totals['dirt']} "
        f"({100 * totals['paved'] // max(totals['paved'] + totals['dirt'], 1)}% earned)"
    )
    width_total = max(totals["alley"] + totals["street"] + totals["avenue"], 1)
    print(
        f"width classes: alley={totals['alley']} street={totals['street']} "
        f"avenue={totals['avenue']} ({100 * totals['avenue'] // width_total}% avenue)"
    )
    print(
        f"STEP-DOWN VIOLATIONS after the fixpoint = {totals['violations']}"
        f"   (stricter alley-touches-avenue reading: {totals['touching']} junctions)"
    )
    print(
        f"NAKED ENDINGS = {totals['naked']} of {totals['leaves']} places the network ENDS "
        f"(trimmed {totals['trimmed']} dangling units)"
    )
    ends_total = max(totals["endings"], 1)
    print(
        "endings: "
        + "  ".join(f"{kind}={totals[f'end_{kind}']}" for kind in ("apron", "bulb", "plaza", "dock", "map_edge", "cap"))
        + f"   (cap share {100 * totals['end_cap'] // ends_total}% — the smell)"
    )
    print(
        f"one root: {totals['islands']} island subnetworks over the bench, "
        f"{totals['no_umbilical']} fixtures with no umbilical"
    )
    print(f"biggest avenue-crossing slab, summed over the bench = {totals['slab']} tiles")
    print(f"lots with no frontage = {totals['no_frontage']}   unrouted edges = {totals['unrouted']}")
    print(
        f"seam tiles: before={totals['seam0']} after={totals['seam1']} "
        f"({100 * totals['seam0'] // max(v5_area, 1)}% -> "
        f"{100 * totals['seam1'] // max(v5_area, 1)}% of the v5 grid)"
    )
    if paved_share:
        pv, bl = sorted(paved_share), sorted(built_share)
        print(
            f"settled land: paved median={pv[len(pv) // 2]}% (max {pv[-1]}%)   "
            f"built median={bl[len(bl) // 2]}% (min {bl[0]}%)"
        )
    for texture, (n, closed, mu) in sorted(loops_all.items()):
        print(f"loops {texture:<11} {closed}/{n} precincts with a closed loop, total mu={mu}")
    print(f"total grid area  v5={v5_area}  v4={v4_area}  ratio={v5_area / max(v4_area, 1):.2f}x")
    print(
        f"sprawl (paved length per distinct destination) vs v4: "
        f"spearman={spearman(v5_sprawl, v4_sprawl):+.3f} over {len(v5_sprawl)} fixtures"
    )
    joins, lost, unrouted = join_dry_run(load_fixtures("random-0")[0][1])
    print(
        f"join seam dry run (random-0, synthetic declared pairs): {joins} units became join, "
        f"{lost} paved units overwritten, {unrouted} unroutable"
    )
    print("shuffled-input determinism: " + ("ALL IDENTICAL" if not failures else "FAILED"))
    for line in failures:
        print(f"  {line}")
    print(f"image -> {out}")


if __name__ == "__main__":
    main()
