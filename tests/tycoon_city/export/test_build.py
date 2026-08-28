"""`build_city` must stay the same setup `app.run_app` performs.

The point of the module is that a screenshot, an exported `city.json` and the
interactive app describe one city. `stills` and the exporter now share the code
path; `app` still has its own copy, so the first test here is what keeps the two
honest until `app` is deleted in Phase D. It retires with `app.py`.
"""

import os
from pathlib import Path

import pytest

from tycoon_city.catalog.errors import CatalogError
from tycoon_city.catalog.loader import load_catalog
from tycoon_city.export.build import build_city
from tycoon_city.export.city_json import _focus
from tycoon_city.sim.channels import DEFAULT_BINDINGS, apply_signals
from tycoon_city.sim.generator import generate_city
from tycoon_city.theme_data import load_theme_data, theme_dir

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

DEMO_DB = Path(__file__).resolve().parents[2] / "demo.duckdb"


@pytest.fixture
def style_rules():
    return load_theme_data(theme_dir("default")).style_rules


def test_build_city_matches_the_apps_own_setup(style_rules):
    """Same catalog, same city, same derived state as `run_app` builds by hand."""
    ctx, city = build_city(DEMO_DB, style_rules)

    expected_ctx = load_catalog(DEMO_DB)
    expected_city = generate_city(expected_ctx, style_rules)
    apply_signals(expected_city, expected_ctx, DEFAULT_BINDINGS)

    assert ctx == expected_ctx
    assert city.tiles == expected_city.tiles
    assert city.plant_xy == expected_city.plant_xy
    assert city.districts == expected_city.districts
    assert city.edge_rates == expected_city.edge_rates
    assert city.lots == expected_city.lots


def test_build_city_derives_visual_state(style_rules):
    """Without `apply_signals` every lot would carry the generator's placeholder
    density of 1, which is a plausible-looking value -- so assert that the
    catalog's spread actually reached the lots."""
    _, city = build_city(DEMO_DB, style_rules)

    densities = {lot.target_density for lot in city.lots.values()}
    assert len(densities) > 1, "signals never ran: every lot is at the placeholder"


def test_focus_is_the_bbox_of_lots_and_plant(style_rules):
    """The framing policy, formerly pinned against `app._built_tiles` (retired
    with the 2D renderer in Phase D): the opening frame is the box around every
    LOT tile plus the plant -- roads deliberately excluded. Asserted against
    the tile grid, not against `city.lots`, which is `_focus`'s own input."""
    from tycoon_city.sim.tiles import TileKind

    _, city = build_city(DEMO_DB, style_rules)
    focus = _focus(city)

    xs = [x for y, row in enumerate(city.tiles) for x, k in enumerate(row) if k is TileKind.LOT]
    ys = [y for y, row in enumerate(city.tiles) for x, k in enumerate(row) if k is TileKind.LOT]
    xs.append(city.plant_xy[0])
    ys.append(city.plant_xy[1])

    assert focus == {
        "min_x": min(xs),
        "min_y": min(ys),
        "max_x": max(xs),
        "max_y": max(ys),
    }


def test_missing_database_raises_catalog_error(tmp_path, style_rules):
    with pytest.raises(CatalogError):
        build_city(tmp_path / "nope.duckdb", style_rules)
