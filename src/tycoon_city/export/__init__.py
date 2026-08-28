"""Export layer: a catalog turned into `city.json`, with no renderer attached.

This is the seam between Python and any client. Everything upstream of it --
reading the catalog, planning the layout, deriving visual state from data --
stays in Python; everything downstream is presentation. `docs/city-json-v1.md`
is the normative description of what crosses.

Imports no pygame, so the emitter runs in a slim image with no SDL installed.
Guarded by tests/export/test_no_pygame.py.
"""

from .build import build_city
from .city_json import (
    FORMAT,
    TILE_KINDS,
    VERSION,
    city_document,
    decode_rle,
    dumps,
    encode_rle,
)

__all__ = [
    "FORMAT",
    "TILE_KINDS",
    "VERSION",
    "build_city",
    "city_document",
    "decode_rle",
    "dumps",
    "encode_rle",
]
