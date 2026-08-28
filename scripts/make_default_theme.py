"""Draw the committed default spritesheet with pygame primitives."""

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

TILE = 16

STYLES = ["industrial", "commercial", "residential"]

# Per-style palette: base building color, light (highlight) edge, dark (roof/
# shadow) band, and lit vs. unlit window colors.
STYLE_COLORS: dict[str, dict[str, tuple[int, int, int]]] = {
    "industrial": {
        "base": (176, 86, 58),
        "light": (206, 124, 92),
        "dark": (104, 46, 30),
        "window_lit": (255, 188, 96),
        "window_dim": (118, 66, 48),
    },
    "commercial": {
        "base": (74, 111, 165),
        "light": (122, 154, 202),
        "dark": (38, 62, 100),
        "window_lit": (226, 238, 255),
        "window_dim": (54, 82, 122),
    },
    "residential": {
        "base": (138, 143, 121),
        "light": (172, 176, 152),
        "dark": (88, 92, 76),
        "window_lit": (255, 222, 148),
        "window_dim": (108, 108, 92),
    },
}

PAD_COLOR = (150, 150, 140)

SIMPLE_COLORS = {
    "road": (90, 90, 90),
    "power_line": (200, 200, 60),
    "plant": (200, 60, 60),
    "water": (60, 110, 200),
    "vehicle": (240, 240, 60),
}

GRASS_BASE = (60, 140, 70)
GRASS_ALT_BASE = (67, 150, 79)
GRASS_FLECK_OFFSET = -10
# Deterministic fleck positions so the texture reads as noise, not a grid.
GRASS_FLECKS = ((3, 4), (9, 2), (5, 10), (12, 12), (2, 13), (13, 6))


def _draw_grass(sheet: pygame.Surface, x0: int, *, alt: bool) -> None:
    base = GRASS_ALT_BASE if alt else GRASS_BASE
    fleck = tuple(max(0, c + GRASS_FLECK_OFFSET) for c in base)
    rect = pygame.Rect(x0, 0, TILE, TILE)
    pygame.draw.rect(sheet, base, rect)
    for dx, dy in GRASS_FLECKS:
        sheet.set_at((x0 + dx, dy), fleck)


def _draw_simple(sheet: pygame.Surface, x0: int, color: tuple[int, int, int]) -> None:
    rect = pygame.Rect(x0, 0, TILE, TILE)
    pygame.draw.rect(sheet, color, rect)
    pygame.draw.rect(sheet, tuple(max(0, c - 40) for c in color), rect, 1)


def _draw_lot(sheet: pygame.Surface, x0: int, style: str, level: int) -> None:
    """Draw a lot sprite whose footprint, height, and lit-window count scale
    with `level` (1..8), using the per-style palette for differentiation."""
    colors = STYLE_COLORS[style]
    pygame.draw.rect(sheet, PAD_COLOR, pygame.Rect(x0, 0, TILE, TILE))

    # Footprint widens and the building grows taller (anchored to the tile's
    # bottom edge) as level increases, giving a "bigger block" read at a glance.
    inset = max(0, round(5 - (level - 1) * 5 / 7))
    height = min(15 - inset, 3 + level)
    top = 15 - height
    left = x0 + inset
    width = TILE - 2 * inset
    building = pygame.Rect(left, top, width, height)
    pygame.draw.rect(sheet, colors["base"], building)

    # Roof/shadow band on top, highlight edge on the left for a pseudo-3D read.
    roof_h = min(height, 1 if level < 5 else 2)
    pygame.draw.rect(sheet, colors["dark"], (left, top, width, roof_h))
    if top + roof_h <= 15:
        pygame.draw.line(sheet, colors["light"], (left, top + roof_h), (left, 15), 1)

    # Window grid below the roof band; the first `level` slots (row-major) are
    # lit, the rest are dim, so lit-window count visibly scales with level.
    win_top = top + roof_h + 1
    avail_h = 15 - win_top
    if avail_h <= 0:
        return
    cols = max(1, (width - 2) // 3)
    rows = max(1, avail_h // 2)
    lit_count = min(cols * rows, level)
    slot = 0
    for r in range(rows):
        for c in range(cols):
            wx = left + 2 + c * 3
            wy = win_top + r * 2
            if wx > x0 + TILE - 2 or wy > 15:
                continue
            color = colors["window_lit"] if slot < lit_count else colors["window_dim"]
            sheet.set_at((wx, wy), color)
            slot += 1


def _sprite_names() -> list[str]:
    names = ["grass", "grass_alt", *SIMPLE_COLORS.keys()]
    names += [f"lot_{style}_{level}" for style in STYLES for level in range(1, 9)]
    return names


def build(out_dir: Path) -> Path:
    pygame.init()
    pygame.display.set_mode((1, 1))

    names = _sprite_names()
    sheet = pygame.Surface((len(names) * TILE, TILE), pygame.SRCALPHA)

    for i, name in enumerate(names):
        x0 = i * TILE
        if name == "grass":
            _draw_grass(sheet, x0, alt=False)
        elif name == "grass_alt":
            _draw_grass(sheet, x0, alt=True)
        elif name in SIMPLE_COLORS:
            _draw_simple(sheet, x0, SIMPLE_COLORS[name])
        else:
            _, style, level = name.split("_")
            _draw_lot(sheet, x0, style, int(level))

    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "spritesheet.png"
    pygame.image.save(sheet, str(target))
    pygame.quit()
    return target


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    written = build(root / "themes" / "default")
    print(f"wrote {written}")
