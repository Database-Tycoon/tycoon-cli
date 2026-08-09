"""Spike 0: the BEFORE picture — every fixture city on one labelled sheet.

Not a test — a look-first instrument for the streets v5 blocks-first pivot, and
it changes NOTHING in the planner: it only reads `plan_dag_layout`. Three
instruments, all printed and one drawn:

1. **The contact sheet.** Every fixture in `spike_fixtures` rendered as a
   thumbnail on one PNG, labelled with its name and grid. The question it
   answers for Stephen is blunt: *can you tell these cities apart at thumbnail
   size?* Downscaling is honest area-averaging, so a network too thin to
   survive a thumbnail disappears here exactly as it does on a laptop screen.

2. **The determinism fingerprint.** sha256 over the plan's whole structural
   output (grid, lots, routes, lanes, features, districts, the civic strip).
   Any later change to placement can then be PROVEN neutral or deliberate
   rather than argued about. The SHUFFLED-INPUT variant re-fingerprints the
   same catalog with `ctx.objects` and `ctx.edges` permuted: a plan that reads
   its inputs in arrival order instead of sorted order fails there and nowhere
   else, and that is the property most likely to rot as v5 lands.

3. **The size budget.** Grid area, `city.json` bytes and RLE run count per
   fixture — the numbers a blocks-first layout has to be compared against,
   because more streets means more runs means a bigger document.

Usage (Pillow is not a runtime dependency; bring it in for the spike):

    uv run --with pillow python scripts/spike_contact_sheet.py
    uv run --with pillow python scripts/spike_contact_sheet.py --detail random-3
    uv run --with pillow python scripts/spike_contact_sheet.py --no-budget
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spike_fixtures import load_fixtures, shuffled  # noqa: E402

from dbtycoon.catalog.models import PipelineContext  # noqa: E402
from dbtycoon.export.city_json import city_document, dumps  # noqa: E402
from dbtycoon.sim.channels import DEFAULT_BINDINGS, apply_signals  # noqa: E402
from dbtycoon.sim.generator import generate_city  # noqa: E402
from dbtycoon.sim.layout import DagPlan, plan_dag_layout  # noqa: E402
from dbtycoon.theme_data import load_theme_data, theme_dir  # noqa: E402

OUT_DIR = Path(__file__).resolve().parents[1] / "spike-out"

# The palette of `scripts/spike_road_defects.py`, so the two instruments can be
# read side by side.
COL_BG = (26, 28, 32)
COL_GRASS = (58, 132, 66)
COL_ROAD = (110, 110, 116)
COL_LANE = (140, 140, 148)
COL_LOT = (60, 90, 200)
COL_PLANT = (200, 80, 80)
COL_POWER = (230, 210, 80)
COL_PLAZA = (245, 245, 235)
COL_DOCK = (120, 40, 170)
COL_APRON = (90, 210, 230)
COL_TEXT = (232, 232, 236)
COL_DIM = (150, 152, 160)
FEATURE_COLOURS = {"apron": COL_APRON, "dock": COL_DOCK, "plaza": COL_PLAZA}

THUMB = 210  # the thumbnail box, in pixels — deliberately small
LABEL_H = 26
PAD = 8
COLUMNS = 6


# --------------------------------------------------------------------------
# 1. The picture.
# --------------------------------------------------------------------------


def plan_image(plan: DagPlan) -> Image.Image:
    """One pixel per tile: the plan as ground truth, before any scaling."""
    img = Image.new("RGB", (max(plan.width, 1), max(plan.height, 1)), COL_GRASS)
    px = img.load()

    def put(t: tuple[int, int], colour: tuple[int, int, int]) -> None:
        if 0 <= t[0] < img.width and 0 <= t[1] < img.height:
            px[t[0], t[1]] = colour

    for route in plan.routes.values():
        for t in route[1:-1]:
            put(t, COL_ROAD)
    for t in plan.lane_tiles:
        put(t, COL_LANE)
    for t in plan.access_road:
        put(t, COL_ROAD)
    for t in plan.power_tiles:
        put(t, COL_POWER)
    for f in plan.street_features:
        for dx in range(f.w):
            for dy in range(f.h):
                put((f.x + dx, f.y + dy), FEATURE_COLOURS.get(f.kind, COL_PLAZA))
    big = set(plan.big_lots)
    for key, (x, y) in plan.positions.items():
        span = 2 if key in big else 1
        for dx in range(span):
            for dy in range(span):
                put((x + dx, y + dy), COL_LOT)
    put(plan.plant_xy, COL_PLANT)
    return img


def fit(img: Image.Image, box: int) -> Image.Image:
    """Scale into a box: NEAREST up (keep the tile grid crisp), BOX down (area
    average — the honest thumbnail, where a one-tile street really does fade)."""
    scale = min(box / img.width, box / img.height)
    size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    return img.resize(size, Image.NEAREST if scale >= 1 else Image.BOX)


def contact_sheet(rows: list[tuple[str, DagPlan]], out: Path) -> None:
    cols = COLUMNS
    n_rows = (len(rows) + cols - 1) // cols
    cell_w, cell_h = THUMB + PAD * 2, THUMB + LABEL_H + PAD * 2
    sheet = Image.new("RGB", (cols * cell_w, n_rows * cell_h + 30), COL_BG)
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (PAD, 8),
        f"streets v4 — the BEFORE picture: {len(rows)} fixture cities, same scale rule, thumbnail size",
        fill=COL_TEXT,
    )
    for i, (name, plan) in enumerate(rows):
        cx, cy = (i % cols) * cell_w, (i // cols) * cell_h + 30
        thumb = fit(plan_image(plan), THUMB)
        sheet.paste(thumb, (cx + PAD + (THUMB - thumb.width) // 2, cy + PAD))
        draw.rectangle(
            [cx + PAD - 1, cy + PAD - 1, cx + PAD + THUMB, cy + PAD + THUMB],
            outline=(70, 72, 80),
        )
        draw.text((cx + PAD, cy + PAD + THUMB + 4), name, fill=COL_TEXT)
        draw.text(
            (cx + PAD, cy + PAD + THUMB + 15),
            f"{plan.width}x{plan.height}  lots={len(plan.positions)} routes={len(plan.routes)}",
            fill=COL_DIM,
        )
    sheet.save(out)


def detail(name: str, plan: DagPlan, out: Path) -> None:
    """One city, big enough to read tile by tile."""
    img = plan_image(plan)
    scale = max(1, min(1600 // max(img.width, 1), 1600 // max(img.height, 1)))
    big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    sheet = Image.new("RGB", (big.width + 2 * PAD, big.height + 2 * PAD + 18), COL_BG)
    sheet.paste(big, (PAD, PAD))
    ImageDraw.Draw(sheet).text(
        (PAD, big.height + PAD + 4),
        f"{name}  {plan.width}x{plan.height}  scale={scale}px/tile  "
        f"lots={len(plan.positions)} routes={len(plan.routes)} "
        f"features={len(plan.street_features)}",
        fill=COL_TEXT,
    )
    sheet.save(out)


# --------------------------------------------------------------------------
# 2. The fingerprint harness.
# --------------------------------------------------------------------------


def plan_fingerprint(plan: DagPlan) -> str:
    """sha256 over EVERY structural field of the plan, sorted.

    Deliberately not `repr(plan)`: dict ordering in a repr follows insertion,
    which would make the digest depend on the very arrival order the shuffled
    variant is trying to test. Every collection is re-sorted here.
    """
    parts: list[str] = [
        f"grid {plan.width}x{plan.height}",
        f"plant {plan.plant_xy}",
        f"library {plan.library_xy}",
        f"firehouse {plan.firehouse_xy}",
        f"access {list(plan.access_road)}",
        f"orphans {sorted(plan.orphans)}",
        f"big {sorted(plan.big_lots)}",
        f"power {sorted(plan.power_tiles)}",
        f"lanes {sorted(plan.lane_tiles)}",
    ]
    for key in sorted(plan.positions):
        parts.append(f"lot {key} {plan.positions[key]}")
    for pair in sorted(plan.routes):
        parts.append(f"route {pair} {list(plan.routes[pair])}")
    for d in sorted(plan.districts, key=lambda d: (d.schema, d.x, d.y)):
        parts.append(f"district {d.schema} {d.x} {d.y} {d.w} {d.h}")
    for f in sorted(plan.street_features, key=lambda f: (f.kind, f.x, f.y, f.facing or "")):
        parts.append(f"feature {f.kind} {f.x} {f.y} {f.facing} {f.w} {f.h}")
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:16]


def shuffle_check(ctx: PipelineContext, digest: str) -> tuple[bool, str]:
    """Fingerprint the plan under three permutations of the input order.

    A single shuffle can accidentally reproduce the original order on a tiny
    catalog, which would make the check pass without examining anything; three
    seeds make that vanishingly unlikely and cost nothing.
    """
    for seed in (1, 2, 3):
        other = plan_fingerprint(plan_dag_layout(shuffled(ctx, seed)))
        if other != digest:
            return False, other
    return True, digest


# --------------------------------------------------------------------------
# 3. The size budget.
# --------------------------------------------------------------------------


def size_budget(ctx: PipelineContext) -> tuple[int, int, int]:
    """(grid area, city.json bytes, RLE run count) for one catalog."""
    theme = load_theme_data(theme_dir("default"))
    city = generate_city(ctx, theme.style_rules)
    apply_signals(city, ctx, DEFAULT_BINDINGS, now=None)
    doc = city_document(ctx, city, theme)
    return city.width * city.height, len(dumps(doc).encode()), len(doc["grid"]["tiles_rle"]) // 2


def main() -> None:
    args = sys.argv[1:]
    want_budget = "--no-budget" not in args
    only = args[args.index("--detail") + 1] if "--detail" in args else None
    OUT_DIR.mkdir(exist_ok=True)

    fixtures = load_fixtures(only)
    if not fixtures:
        raise SystemExit(f"no fixture named {only!r}")

    rows: list[tuple[str, DagPlan]] = []
    print(
        f"{'fixture':<16}{'grid':>11}{'area':>8}{'lots':>6}{'road':>6}"
        f"{'bytes':>9}{'runs':>7}  {'fingerprint':<18}shuffled"
    )
    total_bytes = 0
    failures: list[str] = []
    for name, ctx in fixtures:
        plan = plan_dag_layout(ctx)
        rows.append((name, plan))
        digest = plan_fingerprint(plan)
        ok, other = shuffle_check(ctx, digest)
        if not ok:
            failures.append(f"{name}: {digest} vs shuffled {other}")
        road = len({t for r in plan.routes.values() for t in r[1:-1]} | set(plan.lane_tiles))
        area, nbytes, runs = size_budget(ctx) if want_budget else (plan.width * plan.height, 0, 0)
        total_bytes += nbytes
        print(
            f"{name:<16}{plan.width:>5}x{plan.height:<5}{area:>8}{len(plan.positions):>6}"
            f"{road:>6}{nbytes:>9}{runs:>7}  {digest:<18}{'OK' if ok else 'DIFFERS'}"
        )

    if only:
        out = OUT_DIR / f"v4-detail-{only.replace('/', '_')}.png"
        detail(only, rows[0][1], out)
    else:
        out = OUT_DIR / "v4-contact-sheet.png"
        contact_sheet(rows, out)
    print(f"\ncities={len(rows)} total_city_json_bytes={total_bytes}")
    print("shuffled-input determinism: " + ("ALL IDENTICAL" if not failures else "FAILED"))
    for line in failures:
        print(f"  {line}")
    print(f"image -> {out}")


if __name__ == "__main__":
    main()
