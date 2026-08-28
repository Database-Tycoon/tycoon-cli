"""Theme parsing, with no rendering dependency.

A theme is a directory holding `theme.toml` and `spritesheet.png`. Everything in
the TOML is renderer-neutral data — names, labels, colours, zone-style rules, and
sprite rectangles into the atlas — so parsing it does not need pygame. Only
turning those rectangles into blittable surfaces does, and that lives in
`render/theme.py`.

Splitting it this way is what lets the JSON exporter (and therefore a container
with no SDL installed) read a theme. `render.theme.load_theme` is a thin wrapper
over `load_theme_data`, so there is one parser and no chance of the two drifting.
"""

import tomllib
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from .sim.tiles import ZoneStyle

DEFAULT_LOGO_TEXT = "DATABASE TYCOON"
DEFAULT_THEME_NAME = "default"


# Themes ship as package data under tycoon_city/themes/, so they resolve the same
# from a repo checkout and from an installed wheel. Resolving them relative to
# __file__ does not: from site-packages a parents[n]/"themes" walk lands in the
# venv's lib directory, where no themes exist.
def theme_dir(name: str) -> Path:
    """Directory holding the named theme's `theme.toml` and `spritesheet.png`.

    Anchored on the `tycoon_city` package rather than on `tycoon_city.themes`, which
    has no `__init__.py` and so is not an importable anchor.

    Returns a real filesystem path. Wheels install unzipped, so
    `importlib.resources.files` yields a `Path` here; a zipimported install
    would need `importlib.resources.as_file` instead, which nothing in this
    project does today.
    """
    return Path(str(files("tycoon_city"))) / "themes" / name


@dataclass(frozen=True)
class ThemeData:
    """A parsed theme, free of any rendering type.

    `sprites` maps a sprite name to its `(x, y, w, h)` rectangle in the
    spritesheet. Kept as a plain tuple rather than a `pygame.Rect` so this
    module imports nothing from the renderer — a web client wants the same
    numbers as UV offsets.
    """

    name: str
    logo_text: str
    labels: dict[str, str]
    colors: dict[str, tuple[int, int, int]]
    style_rules: list[tuple[str, ZoneStyle]]
    sprites: dict[str, tuple[int, int, int, int]]
    spritesheet_path: Path


def load_theme_data(path: Path) -> ThemeData:
    """Parse a theme directory. Reads `theme.toml`; never opens the spritesheet."""
    path = Path(path)
    with open(path / "theme.toml", "rb") as handle:
        data = tomllib.load(handle)

    sprites = {name: (int(c[0]), int(c[1]), int(c[2]), int(c[3])) for name, c in data.get("sprites", {}).items()}
    colors = {name: (int(v[0]), int(v[1]), int(v[2])) for name, v in data.get("colors", {}).items()}
    style_rules = [(rule["pattern"], ZoneStyle[rule["style"]]) for rule in data.get("style_rules", [])]

    return ThemeData(
        name=data.get("name", DEFAULT_THEME_NAME),
        logo_text=data.get("logo_text", DEFAULT_LOGO_TEXT),
        labels=dict(data.get("labels", {})),
        colors=colors,
        style_rules=style_rules,
        sprites=sprites,
        spritesheet_path=path / "spritesheet.png",
    )
