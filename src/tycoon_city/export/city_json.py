"""The `city.json` v1 wire format: assemble the document, and serialise it.

`docs/city-json-v1.md` is normative; this module is its only producer. The
per-section builders live in `blocks` -- this file is the list of blocks a
document is made of, in wire order, plus `dumps`. Three properties are
load-bearing and each has a test:

* **Byte-stable.** Same catalog and theme in, identical bytes out, so a golden
  file can be committed and a client can be tested against it. Every collection
  is sorted on a key that cannot tie, floats are rounded, and nothing carries a
  timestamp or a path.
* **No pygame.** Nothing here or in what it imports touches SDL.
* **No engine.** Lots carry `target_density`, never the tweened `density`, so a
  client animates the grow-in itself and this module never has to run ticks.

Imports `sim` for the enums and `has_known_edges` rather than restating either.
The builder names re-exported below are part of the module's surface: callers
have imported `encode_rle`, `TILE_KINDS` and `_focus` from here since v1.
"""

import json
from typing import Any

from ..catalog.models import PipelineContext
from ..pricing import PriceBook
from ..sim.city import CityMap
from ..sim.layout import has_known_edges
from ..theme_data import ThemeData
from .achievements import _achievements
from .blocks import (
    RATE_PRECISION,
    TILE_KINDS,
    _columns,
    _dbt_block,
    _districts,
    _edges,
    _focus,
    _joins,
    _lots,
    _objects,
    _replay,
    _street_features,
    _theme,
    decode_rle,
    encode_rle,
)
from .measured import _budget, _usage_by_key, _weather

FORMAT = "database-tycoon.city"
VERSION = 1

# The re-exports are the module's back-compatible surface, not decoration:
# `_focus` and the rest have been imported from here since v1 (tests and the
# webserver both do it), so moving them into `blocks` must not move their
# import path. Listing them here is also what tells the linter they are
# deliberate re-exports rather than dead imports.
__all__ = [
    "FORMAT",
    "RATE_PRECISION",
    "TILE_KINDS",
    "VERSION",
    "_achievements",
    "_budget",
    "_columns",
    "_dbt_block",
    "_districts",
    "_edges",
    "_focus",
    "_joins",
    "_lots",
    "_objects",
    "_replay",
    "_street_features",
    "_theme",
    "_usage_by_key",
    "_weather",
    "city_document",
    "decode_rle",
    "dumps",
    "encode_rle",
]


def city_document(
    ctx: PipelineContext,
    city: CityMap,
    theme: ThemeData,
    pricing: PriceBook | None = None,
) -> dict[str, Any]:
    """The whole `city.json` document as plain data, ready for `dumps`.

    `city` must already have had `apply_signals` run over it -- `build_city` does
    that -- or every lot ships the generator's placeholder density.

    `pricing` is the declared compute rate the `budget` block is billed at; the
    built-in local-DuckDB book (free) is used when the caller has none. It is
    the only *declared* number in the document — everything else is measured —
    which is why the block repeats its `price_source` on the wire.

    All five of the 2026-08-06 reserved seams are now filled: `budget`,
    `weather` and `objects[].usage` by `measured` (all three measured), `joins`
    and `objects[].semantic` by the OSI loader (both declared). Each still
    emits unconditionally, and each stays empty (`null` / `[]`) on a catalog
    that has nothing to say — most catalogs, for the semantic pair.
    """
    return {
        "format": FORMAT,
        "version": VERSION,
        "database": {
            "name": ctx.database_name,
            "object_count": ctx.object_count,
            "total_rows": ctx.total_rows,
            # False means no lineage could be determined at all, which is a
            # different fact from "nothing depends on anything" and the client
            # says so out loud rather than dimming every building.
            "has_known_edges": has_known_edges(ctx),
            # The degradation ladder's messages (missing manifest, locked run
            # metadata, low join rate...) — shown by the client, because a
            # named absence must never render as a silently broken feature.
            "notes": list(ctx.notes),
        },
        "grid": {
            "width": city.width,
            "height": city.height,
            "tile_kinds": list(TILE_KINDS),
            "tiles_rle": encode_rle(city.tiles),
        },
        "plant": {"x": city.plant_xy[0], "y": city.plant_xy[1]},
        # Civic buildings: the library shelves the city's context; the
        # firehouse dispatches fire response. Null on hand-built maps.
        "library": ({"x": city.library_xy[0], "y": city.library_xy[1]} if city.library_xy else None),
        "firehouse": ({"x": city.firehouse_xy[0], "y": city.firehouse_xy[1]} if city.firehouse_xy else None),
        "focus": _focus(city),
        "districts": _districts(city),
        "street_features": _street_features(city),
        "lots": _lots(city),
        # Measured run appearances ride on each object as `usage`; a key the
        # history says nothing about stays null — unknown, never unused.
        "objects": _objects(ctx, _usage_by_key(ctx)),
        "edges": _edges(ctx, city),
        # DECLARED joins from an OSI semantic model — a separate array, never
        # folded onto `edges`: a join is not a claim that data moved.
        "joins": _joins(ctx),
        "replay": _replay(ctx),
        # The compute bill: measured load at a declared rate. null when the
        # run history knows nothing — never an invented zero.
        "budget": _budget(ctx, pricing),
        # Source freshness as weather over the districts a late source FEEDS.
        # Always an object; empty cells + a note when nothing is judged.
        "weather": _weather(ctx),
        # Named coverage milestones, STATELESS: each one is "true right now",
        # counted from real artifacts. A milestone whose evidence was never
        # read is `unknown`, never `unmet` — the same law as weather's.
        "achievements": _achievements(ctx),
        "theme": _theme(theme),
    }


# A sentinel chosen so it cannot occur in the document's own text: a NUL is not
# legal raw in a JSON string, so `json.dumps` escapes it to a six-character
# backslash-u sequence that no schema, object or label name coming out of DuckDB
# or a TOML file will produce. The count check in `dumps` is the actual
# guarantee; this reasoning only explains why it never fires.
_RLE_TOKEN = "\x00tiles_rle\x00"


def dumps(doc: dict[str, Any]) -> str:
    """Serialise byte-stably: `indent=2` throughout, except the run-length array.

    `tiles_rle` goes on one line. That is not cosmetic -- it is the difference
    between a viable format and a broken one. Measured on 500 one-object schemas,
    the case `plan_layout` says no spacing candidate can compact: 905x905 tiles,
    278,161 runs because 500 radial arterials shred every grass row they cross,
    and one line per number costs **2.8 MB** (6.1 MB as nested pairs) against
    1.1 MB collapsed. The plan's expectation that grass dominance would keep the
    run count low holds on realistic catalogs and fails badly on that one.

    Everything else stays indented so the document is reviewable in a diff.
    """
    runs = doc["grid"]["tiles_rle"]
    shell = dict(doc)
    shell["grid"] = {**doc["grid"], "tiles_rle": _RLE_TOKEN}

    text = json.dumps(shell, indent=2, ensure_ascii=False)
    token = json.dumps(_RLE_TOKEN, ensure_ascii=False)
    if text.count(token) != 1:
        raise ValueError(f"expected exactly one tiles_rle placeholder, found {text.count(token)}")
    return text.replace(token, json.dumps(runs, separators=(",", ":"))) + "\n"
