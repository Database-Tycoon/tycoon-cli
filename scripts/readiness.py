#!/usr/bin/env python3
"""Readiness diagnostic -- inspect a DuckDB catalog and report its state.

The default output carries NO identifiers from the catalog (schema names,
table names, file paths), so the script can safely be pasted into a chat
window.  Pass ``--names`` to include them.

Exit codes:
    0  -- everything looks fine (or recoverable notes only)
    1  -- the database could not be opened, or the city lost objects during
          generation (object count != lot count).
"""

import argparse
import sys
from pathlib import Path

from tycoon_city.catalog.loader import load_catalog
from tycoon_city.catalog.models import PipelineContext
from tycoon_city.sim.city import CityMap
from tycoon_city.sim.generator import generate_city
from tycoon_city.sim.tiles import ZoneStyle

# A handful of style rules that map common schema prefixes to zone styles.
# The readiness script uses them to build a city; the exact mapping does not
# matter for the diagnostic -- what matters is that a city *can* be built.
_DEFAULT_STYLE_RULES: list[tuple[str, ZoneStyle]] = [
    ("raw|source|land", ZoneStyle.INDUSTRIAL),
    ("stag|int", ZoneStyle.COMMERCIAL),
    ("mart|serve|analytics|main", ZoneStyle.RESIDENTIAL),
]


class _Redactor:
    """Block-list redactor used by the default (sanitised) output."""

    def __init__(self, blocklist: set[str]) -> None:
        self._blocklist = blocklist

    def __call__(self, text: str) -> str:
        for token in sorted(self._blocklist, key=len, reverse=True):
            if token.lower() in text.lower() and len(token) >= 3:
                text = text.replace(token, "<redacted>")
        return text


def _build_city(ctx: PipelineContext) -> CityMap:
    """Generate a city map and return it (side-effect: may raise)."""
    return generate_city(ctx, _DEFAULT_STYLE_RULES)


def main(args: list[str] | None = None) -> int:
    """Run the readiness diagnostic.

    Returns 0 on success, 1 on unrecoverable error.
    """
    parser = argparse.ArgumentParser(description="Inspect a DuckDB catalog and report its readiness.")
    parser.add_argument("database", help="Path to .duckdb file or md: URI")
    parser.add_argument(
        "--names",
        action="store_true",
        help="Include catalog identifiers in the report (not redacted).",
    )
    parsed = parser.parse_args(args)

    db_path = Path(parsed.database)
    show_names = parsed.names

    # --- Load catalog ---------------------------------------------------
    try:
        ctx = load_catalog(db_path)
    except Exception as exc:  # noqa: BLE001
        print(f"BROKEN: could not open database '{db_path}': {exc}")
        return 1

    # --- Build city ------------------------------------------------------
    try:
        city = _build_city(ctx)
    except Exception as exc:  # noqa: BLE001
        print(f"BROKEN: city generation failed: {exc}")
        return 1

    # Check object-to-lot correspondence.
    if ctx.object_count != len(city.lots):
        print(f"BROKEN: {ctx.object_count} objects but only {len(city.lots)} lots -- objects are being lost")
        return 1

    # --- Report ----------------------------------------------------------
    redactor = _Redactor({str(db_path), ctx.database_name} | {o.key for o in ctx.objects})

    print("LOAD TIME BY STAGE")
    print(f"  objects: {ctx.object_count}")
    print(f"  edges:   {len(ctx.edges)}")
    print(f"  rows:    {ctx.total_rows}")
    print()

    print("RENDERING")
    print("city.json")
    print(f"  width:   {city.width}")
    print(f"  lots:    {len(city.lots)}")
    print(f"  plant:   {city.plant_xy}")
    print()

    if ctx.notes:
        for note in ctx.notes:
            print(f"  note: {redactor(note)}")
        print()

    if show_names:
        print(f"  database: {db_path}")
        for obj in ctx.objects:
            print(f"  {obj.key}  ({obj.kind}, {obj.row_count} rows)")
        for edge in ctx.edges:
            print(f"  {edge.src} -> {edge.dst}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
