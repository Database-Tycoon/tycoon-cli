"""Spike 1: does the streets v5 FOOTPRINT read as a city plan with no buildings?

Not a test — the look-first instrument for `dbtycoon.sim.town_blocks`, which is
reachable from here and nowhere else. Draws each fixture's precincts tinted by
texture with every lattice line on top, over the same fixture bench Spike 0 uses
(`scripts/spike_contact_sheet.py`), so the two sheets are directly comparable.

The two questions to answer by LOOKING, before any v5 rule earns a test:

  * **Grid monotony.** The failure mode is a circuit board — a uniform mesh
    that says nothing about the warehouse. Texture contrast (industrial sparse
    and wide, downtown tight, suburban staggered) is what has to defeat it, and
    the contact sheet is where that either shows at a glance or does not.
  * **The west->east depth reading.** Raw land on the left, marts on the right,
    visible in the LAND and not only in the streets. It survives or it does
    not; the render is the verdict.

Printed alongside: block count and aspect ratio per texture, every precinct's
dimensions, grid area against the v4 baseline (recomputed here from
`plan_dag_layout`, so the comparison is like for like), the share of settled
land that came out as pavement at one- and two-tile cells, and the lattice
fingerprint under three shuffles of the input order — the same determinism
harness Spike 0 points at v4, because the shuffled-input property is the one
most likely to rot as v5 grows.

Usage (Pillow is not a runtime dependency; bring it in for the spike):

    uv run --with pillow python scripts/spike_lattice.py
    uv run --with pillow python scripts/spike_lattice.py --detail demo-tycoon
    uv run --with pillow python scripts/spike_lattice.py --cell 2
    uv run --with pillow python scripts/spike_lattice.py --no-arterial

`--cell` re-resolves the SAME lattice at a bigger cell and is the honest test
of whether pavement is a block-grammar problem or a `resolve_coordinates` dial.
`--no-arterial` drops the northern east-west spine, which is the A/B for "does
the footprint read as one city or as scattered islands".
"""

from __future__ import annotations

import hashlib
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spike_fixtures import load_fixtures, shuffled  # noqa: E402

from dbtycoon.catalog.models import PipelineContext  # noqa: E402
from dbtycoon.sim.layout import plan_dag_layout  # noqa: E402
from dbtycoon.sim.town_blocks import (  # noqa: E402
    Lattice,
    TileMap,
    plan_lattice,
    plan_precincts,
    resolve_coordinates,
)
from dbtycoon.sim.town_texture import DOWNTOWN, INDUSTRIAL, SUBURBAN  # noqa: E402

OUT_DIR = Path(__file__).resolve().parents[1] / "spike-out"

COL_BG = (26, 28, 32)
COL_GRASS = (58, 132, 66)
# Texture tints — deliberately far apart in hue, because "can you tell the
# districts apart" is half of what this sheet is for.
TEXTURE_COLOURS = {
    INDUSTRIAL: (150, 102, 66),  # rust: raw land, works and yards
    DOWNTOWN: (96, 108, 150),  # slate: the dense core
    SUBURBAN: (108, 160, 96),  # green: the fringe
}
COL_SPINE = (232, 232, 236)  # arterials, brightest
COL_EDGE = (150, 152, 160)
COL_INTERNAL = (104, 106, 114)
ROLE_COLOURS = {"spine": COL_SPINE, "edge": COL_EDGE, "internal": COL_INTERNAL}
COL_TEXT = (232, 232, 236)
COL_DIM = (150, 152, 160)

THUMB = 210
LABEL_H = 26
PAD = 8
COLUMNS = 6


def lattice_image(lattice: Lattice, tiles: TileMap) -> Image.Image:
    """One pixel per tile: precinct land tinted by texture, lines on top.

    Lines are drawn per ROLE (arterial brightest, block interiors dimmest) so
    the hierarchy that hierarchy-widths will later make physical is already
    legible as value — if the plan only reads once every street is a different
    width, that is worth knowing now.
    """
    img = Image.new("RGB", (max(tiles.width, 1), max(tiles.height, 1)), COL_GRASS)
    px = img.load()
    texture_of = {p.pid: p.texture for p in lattice.precincts}
    for pid, x, y, w, h in tiles.precinct_rects:
        colour = TEXTURE_COLOURS[texture_of[pid]]
        for ix in range(x, min(x + w, img.width)):
            for iy in range(y, min(y + h, img.height)):
                px[ix, iy] = colour
    # Painted in role order so a brighter arterial always wins the tile it
    # shares with a precinct edge.
    for role in ("internal", "edge", "spine"):
        wanted = ROLE_COLOURS[role]
        for seg in lattice.segments:
            if seg.role != role:
                continue
            for x, y in _segment_tiles(seg, tiles):
                if 0 <= x < img.width and 0 <= y < img.height:
                    px[x, y] = wanted
    return img


def _segment_tiles(seg, tiles: TileMap) -> list[tuple[int, int]]:
    """Re-walk one segment's tiles for painting. `resolve_coordinates` already
    returns the union; this only exists so the render can colour by role, and
    it must use the SAME resolved widths or a role's paint lands off its
    street."""
    k = seg.key
    if k.axis == "v":
        span = range(tiles.h_at[k.start], tiles.h_at[k.end] + tiles.h_w[k.end])
        return [(x, y) for x in _run(tiles.v_at[k.line], tiles.v_w[k.line]) for y in span]
    span = range(tiles.v_at[k.start], tiles.v_at[k.end] + tiles.v_w[k.end])
    return [(x, y) for y in _run(tiles.h_at[k.line], tiles.h_w[k.line]) for x in span]


def _run(at: int, width: int) -> range:
    return range(at, at + width)


def lattice_fingerprint(ctx: PipelineContext) -> str:
    """sha256 over the whole lattice: every precinct's placement and sizing,
    and every segment. The same instrument Spike 0 points at v4, so a v5
    placement change can be proven neutral or deliberate rather than argued
    about."""
    precincts = plan_precincts(ctx)
    lattice = plan_lattice(precincts)
    parts = [f"lines {lattice.v_lines}x{lattice.h_lines}"]
    for p in lattice.precincts:
        parts.append(
            f"precinct {p.pid} d{p.depth} b{p.band} {p.texture} cap{p.capacity} "
            f"{p.blocks_x}x{p.blocks_y} @{p.cell_x},{p.cell_y} {sorted(p.members)}"
        )
    for s in lattice.segments:
        parts.append(f"seg {s.key.axis} {s.key.line} {s.key.start}-{s.key.end} {s.role} {s.pid}")
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:16]


def shuffle_check(ctx: PipelineContext, digest: str) -> tuple[bool, str]:
    """Three permutations of the input order, because one can accidentally
    reproduce the original on a tiny catalog and examine nothing."""
    for seed in (1, 2, 3):
        other = lattice_fingerprint(shuffled(ctx, seed))
        if other != digest:
            return False, other
    return True, digest


def _paved(tiles: TileMap) -> str:
    """Share of the SETTLED land that is pavement rather than lot.

    Measured against the precincts' own footprint, never the whole grid, so the
    margins and the open ground east of a narrow precinct cannot flatter it.
    Past about 40% the plan is spending more on street than on city.

    At `cell_size=1` no block shape can reach that: a one-tile lot bought with
    a one-tile street is a 1:1 trade, and a w-by-2 block's floor is
    1 - 2w/(3(w+1)) — a third even as w runs away, and the short-axis rule is
    what stops w running away. Doubling the CELL is the lever (41% against
    61% on this bench), and that is a lot-size decision for the lots spike,
    not something the lattice can decide.
    """
    land = {
        (x, y) for _pid, rx, ry, rw, rh in tiles.precinct_rects for x in range(rx, rx + rw) for y in range(ry, ry + rh)
    }
    if not land:
        return "-"
    return f"{100 * len(land & set(tiles.road_tiles)) // len(land)}%"


def fit(img: Image.Image, box: int) -> Image.Image:
    scale = min(box / img.width, box / img.height)
    size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    return img.resize(size, Image.NEAREST if scale >= 1 else Image.BOX)


def contact_sheet(
    rows: list[tuple[str, Image.Image, str]],
    out: Path,
    title: str | None = None,
    subtitle: str | None = None,
) -> None:
    """The shared sheet layout — spike 2 (`spike_zoning.py`) paints the same
    bench with lots on it and passes its own two header lines."""
    cols = COLUMNS
    n_rows = (len(rows) + cols - 1) // cols
    cell_w, cell_h = THUMB + PAD * 2, THUMB + LABEL_H + PAD * 2
    sheet = Image.new("RGB", (cols * cell_w, n_rows * cell_h + 42), COL_BG)
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (PAD, 8),
        title or (f"streets v5 SPIKE 1 - the bare lattice: {len(rows)} fixtures, no lots, no lineage, no routing"),
        fill=COL_TEXT,
    )
    draw.text(
        (PAD, 22),
        subtitle
        or (
            "land tint = texture (rust industrial / slate downtown / green suburban); "
            "line value = spine > precinct edge > block interior"
        ),
        fill=COL_DIM,
    )
    for i, (name, img, caption) in enumerate(rows):
        cx, cy = (i % cols) * cell_w, (i // cols) * cell_h + 42
        thumb = fit(img, THUMB)
        sheet.paste(thumb, (cx + PAD + (THUMB - thumb.width) // 2, cy + PAD))
        draw.rectangle(
            [cx + PAD - 1, cy + PAD - 1, cx + PAD + THUMB, cy + PAD + THUMB],
            outline=(70, 72, 80),
        )
        draw.text((cx + PAD, cy + PAD + THUMB + 4), name, fill=COL_TEXT)
        draw.text((cx + PAD, cy + PAD + THUMB + 15), caption, fill=COL_DIM)
    sheet.save(out)


def detail(name: str, img: Image.Image, caption: str, out: Path) -> None:
    scale = max(1, min(1600 // max(img.width, 1), 1600 // max(img.height, 1)))
    big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    sheet = Image.new("RGB", (big.width + 2 * PAD, big.height + 2 * PAD + 18), COL_BG)
    sheet.paste(big, (PAD, PAD))
    ImageDraw.Draw(sheet).text((PAD, big.height + PAD + 4), f"{name}  {caption}  scale={scale}px/tile", fill=COL_TEXT)
    sheet.save(out)


def main() -> None:
    args = sys.argv[1:]
    only = args[args.index("--detail") + 1] if "--detail" in args else None
    cell = int(args[args.index("--cell") + 1]) if "--cell" in args else 1
    arterial = "--no-arterial" not in args
    suffix = ("" if arterial else "-no-arterial") + ("" if cell == 1 else f"-cell{cell}")
    OUT_DIR.mkdir(exist_ok=True)

    fixtures = load_fixtures(only)
    if not fixtures:
        raise SystemExit(f"no fixture named {only!r}")

    rows: list[tuple[str, Image.Image, str]] = []
    print(
        f"{'fixture':<16}{'v5 grid':>11}{'aspect':>7}{'v5 area':>9}{'v4 area':>9}{'ratio':>7}"
        f"{'blocks':>7}{'segs':>6}{'paved':>7}{'@cell2':>8}"
        "  fingerprint      shuf   blocks by texture (aspect w:h)"
    )
    totals: Counter[str] = Counter()
    failures: list[str] = []
    v4_total = v5_total = 0
    paved_all: list[int] = []
    aspects: list[float] = []
    for name, ctx in fixtures:
        precincts = plan_precincts(ctx)
        lattice = plan_lattice(precincts, top_arterial=arterial)
        tiles = resolve_coordinates(lattice, cell_size=cell)
        plan = plan_dag_layout(ctx)

        v4_area = plan.width * plan.height
        v5_area = tiles.width * tiles.height
        v4_total += v4_area
        v5_total += v5_area
        by_texture: Counter[str] = Counter()
        # Block shapes now vary per precinct (spike 3), so the summary lists
        # every shape a texture actually used — the fast read on whether
        # trimming has collapsed two textures onto the same block.
        shapes: dict[str, Counter[str]] = {}
        for p in precincts:
            by_texture[p.texture] += p.blocks
            totals[p.texture] += p.blocks
            shapes.setdefault(p.texture, Counter())[f"{p.block_w}:{p.block_h}"] += p.blocks
        shape = "  ".join(
            f"{t[:4]}={by_texture[t]}(" + ",".join(f"{s}x{n}" for s, n in sorted(shapes[t].items())) + ")"
            for t in (INDUSTRIAL, DOWNTOWN, SUBURBAN)
            if by_texture[t]
        )
        blocks = sum(by_texture.values())
        ratio = f"{v5_area / v4_area:.2f}x" if v4_area else "-"
        # How much of the settled land is pavement rather than lot. Measured
        # against the precincts' own footprint, not the whole grid, so the
        # margins and the open ground east of a narrow precinct do not flatter
        # it. Above ~40% the block grammar is spending more on street than on
        # city and will read as a circuit board.
        # `@cell2` re-resolves the SAME lattice with two-tile cells and nothing
        # else changed — the cheapest possible demonstration that street/lot
        # proportion is a `resolve_coordinates` dial and not a block-grammar
        # decision, which is the entire reason the geometry is done in lattice
        # space.
        pct = _paved(tiles)
        pct2 = _paved(resolve_coordinates(lattice, cell_size=cell + 1))
        digest = lattice_fingerprint(ctx)
        ok, other = shuffle_check(ctx, digest)
        if not ok:
            failures.append(f"{name}: {digest} vs shuffled {other}")
        aspect = max(tiles.width, tiles.height) / max(1, min(tiles.width, tiles.height))
        if blocks:
            aspects.append(aspect)
            paved_all.append(int(pct.rstrip("%")))
        print(
            f"{name:<16}{tiles.width:>5}x{tiles.height:<5}{aspect:>6.1f} {v5_area:>8}"
            f"{v4_area:>9}{ratio:>7}"
            f"{blocks:>7}{len(lattice.segments):>6}{pct:>7}{pct2:>8}"
            f"  {digest} {'OK ' if ok else 'DIFFERS'}  {shape}"
        )
        for p in sorted(precincts, key=lambda p: (p.depth, p.band)):
            print(
                f"    d{p.depth} b{p.band} {p.schema:<12} {p.texture:<10} "
                f"members={len(p.members):<4} capacity={p.capacity:<4} "
                f"blocks={p.blocks_x}x{p.blocks_y}  cells={p.cells_w}x{p.cells_h} "
                f"aspect={p.cells_w}:{p.cells_h}  @cell({p.cell_x},{p.cell_y})"
            )
        caption = f"{tiles.width}x{tiles.height}  blocks={blocks}  v4 area x{ratio}"
        rows.append((name, lattice_image(lattice, tiles), caption))

    if only:
        out = OUT_DIR / f"v5-lattice-detail-{only.replace('/', '_')}{suffix}.png"
        detail(only, rows[0][1], rows[0][2], out)
    else:
        out = OUT_DIR / f"v5-lattice-contact-sheet{suffix}.png"
        contact_sheet(rows, out)
    print(f"\nblocks by texture over all fixtures: {dict(sorted(totals.items()))}")
    print(f"total grid area  v5={v5_total}  v4={v4_total}  ratio={v5_total / max(v4_total, 1):.2f}x")
    if paved_all:
        srt = sorted(paved_all)
        asp = sorted(aspects)
        print(
            f"paved  min={srt[0]}%  median={srt[len(srt) // 2]}%  max={srt[-1]}%   "
            f"grid aspect  median={asp[len(asp) // 2]:.2f}  worst={asp[-1]:.2f}  "
            f"(over {len(srt)} settled fixtures, cell_size={cell})"
        )
    print("shuffled-input determinism: " + ("ALL IDENTICAL" if not failures else "FAILED"))
    for line in failures:
        print(f"  {line}")
    print(f"image -> {out}")


if __name__ == "__main__":
    main()
