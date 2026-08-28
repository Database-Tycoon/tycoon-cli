"""One setup path from a database path to a city with its visual state derived.

`tycoon_city.export.cli` and `tycoon_city.webserve` both start here, so the exported
`city.json` and the served one describe the same city by construction rather
than by two call sites being kept in step.

Deliberately no engine or camera: those are presentation, and presentation
lives in the web client now (the pygame renderer retired in Phase D).
"""

from datetime import datetime
from pathlib import Path

from ..catalog.loader import load_context
from ..catalog.models import PipelineContext
from ..sim.channels import DEFAULT_BINDINGS, VisualChannel, apply_signals
from ..sim.city import CityMap
from ..sim.generator import generate_city
from ..sim.tiles import ZoneStyle


def build_city(
    db_path: str | Path,
    style_rules: list[tuple[str, ZoneStyle]],
    bindings: dict[VisualChannel, str] | None = None,
    now: datetime | None = None,
) -> tuple[PipelineContext, CityMap]:
    """Read a catalog, lay it out, and derive visual state from data.

    `db_path` is anything `load_context` dispatches on: a DuckDB file, an
    `md:` catalog, or a **tycoon project directory** — the last of which is
    what gets dbt-manifest lineage and run history onto the map.

    Takes `style_rules` rather than a whole theme so this module needs nothing
    from the renderer; they are the only part of a theme the layout depends on.

    Raises `CatalogError` if the source cannot be opened or read.
    """
    ctx = load_context(db_path)
    city = generate_city(ctx, style_rules)
    # `now` is injected for determinism (tests, byte-stable goldens on
    # runs-free catalogs); None means the wall clock, which is what the
    # exporter and server want.
    apply_signals(city, ctx, DEFAULT_BINDINGS if bindings is None else bindings, now=now)
    return ctx, city
