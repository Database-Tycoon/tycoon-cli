"""One setup path from a database path to a city with its visual state derived.

`tycoon_city.export.cli` and `tycoon_city.webserve` both start here, so the exported
`city.json` and the served one describe the same city by construction rather
than by two call sites being kept in step.

Deliberately no engine or camera: those are presentation, and presentation
lives in the web client now (the pygame renderer retired in Phase D).
"""

import os
import re
from datetime import datetime
from pathlib import Path

from ..catalog.errors import CatalogError
from ..catalog.loader import load_context
from ..catalog.models import PipelineContext
from ..sim.channels import DEFAULT_BINDINGS, VisualChannel, apply_signals
from ..sim.city import CityMap
from ..sim.generator import generate_city
from ..sim.tiles import ZoneStyle


# A copy of `tycoon.motherduck`'s token check: the renderer does not import
# `tycoon`. The prefixes mirror `tycoon.project.is_motherduck`: `md:` and
# `motherduck:`, matched case-insensitively as DuckDB does. Keep the two in step.
_MD_PREFIXES = ("md:", "motherduck:")
_TOKEN_ENV_NAMES = ("MOTHERDUCK_TOKEN", "motherduck_token")
_QUERY_TOKEN_RE = re.compile(r"[?&]motherduck_token=[^&\s]", re.IGNORECASE)


def _has_motherduck_token(source: str) -> bool:
    """A token in the environment, in the `md:` string, or stored by an earlier browser sign-in."""
    if any(os.environ.get(name, "").strip() for name in _TOKEN_ENV_NAMES):
        return True
    if _QUERY_TOKEN_RE.search(source):
        return True
    stored = Path.home() / ".duckdb" / "motherduck_token"
    try:
        return stored.is_file() and stored.stat().st_size > 0
    except OSError:
        return False


def require_motherduck_token(db_path: str | Path) -> None:
    """Raise `CatalogError` for an `md:` or `motherduck:` catalog with no token (#460).

    Without one, DuckDB starts a browser sign-in and blocks until it finishes.
    A file or directory returns at once and never reaches the lookup.
    """
    source = str(db_path)
    if not source.lower().startswith(_MD_PREFIXES) or _has_motherduck_token(source):
        return
    name = source.split("?", 1)[0]
    raise CatalogError(f"No MotherDuck token for {name}: export MOTHERDUCK_TOKEN and run again.")


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

    Raises `CatalogError` if the source cannot be opened or read, or is an
    `md:` catalog with no MotherDuck token.
    """
    require_motherduck_token(db_path)
    ctx = load_context(db_path)
    city = generate_city(ctx, style_rules)
    # `now` is injected for determinism (tests, byte-stable goldens on
    # runs-free catalogs); None means the wall clock, which is what the
    # exporter and server want.
    apply_signals(city, ctx, DEFAULT_BINDINGS if bindings is None else bindings, now=now)
    return ctx, city
