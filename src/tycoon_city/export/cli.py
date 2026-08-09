"""`tycoon-city-export <db> <out_dir> [--theme name] [--pricing file]` -- a renderer's input.

Produces a directory a static host can serve as-is: `city.json` plus the
spritesheet it names, plus the run documents (`runs.json` and `runs/<id>.json`)
laid out under the same names the server routes them at, plus `meta.json`.
Without the run documents a static export would silently lose replay -- the one
thing "self-contained" must not mean. Nothing here needs a display, so it runs
in a slim image.
"""

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..catalog.errors import CatalogError
from ..catalog.models import PipelineContext
from ..pricing import PricingError, resolve_price_book
from ..theme_data import load_theme_data, theme_dir
from .build import build_city
from .city_json import city_document, dumps
from .run_json import dumps as run_dumps
from .run_json import run_document, run_file_name, runs_index

CITY_JSON = "city.json"
RUNS_JSON = "runs.json"
RUNS_DIR = "runs"
META_JSON = "meta.json"

META_FORMAT = "database-tycoon.meta"
META_VERSION = 1

# The two things a `generated_at` can honestly be, and their wordings live here
# so neither producer invents its own. A client shows the first as "exported N
# ago" and the second as "as of N ago" -- the age of ITS OWN fetch, which is
# all it can know.
EXPORTED_NOTE = "written by tycoon-city-export; city.json in this directory was produced at generated_at"
SERVED_LIVE_NOTE = (
    "served live: city.json is generated per request, so its age is the age of your "
    "fetch and this document has no export time to give"
)


def meta_document(generated_at: datetime | None) -> dict[str, Any]:
    """The `meta.json` sibling: when the `city.json` beside it was produced.

    **Why this is a separate document.** `city.json` v1 is byte-stable by law
    (`docs/city-json-v1.md`) -- no uuid, no timestamp, no path, no seed -- which
    is what makes a committed golden and a cross-language contract test
    possible. A generation time is exactly the kind of fact that would break
    that, so it lives beside the document instead, the same way `runs.json`
    does. Nothing here may ever be folded back into the contract emitter.

    **Why it is needed at all.** A client with no `meta.json` can only measure
    the age of its own fetch, which is right for a live server (the document
    was built for that request) and wrong for a static export, where a
    week-old `city.json` on a CDN would otherwise read "as of 3s ago".

    `generated_at` is **nullable, and null is a fact**: it says this producer
    has no export time to give, so the client must fall back to its fetch time
    and say so. That is what the server emits, and it is the same state a
    client reaches when `meta.json` is absent entirely -- an export written
    before this document existed.
    """
    stamp = None
    if generated_at is not None:
        # Whole seconds, UTC, `Z`: a sub-second export time is noise, and one
        # spelling keeps `Date.parse` on the client side unambiguous.
        stamp = generated_at.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "format": META_FORMAT,
        "version": META_VERSION,
        "generated_at": stamp,
        "note": SERVED_LIVE_NOTE if stamp is None else EXPORTED_NOTE,
    }


def meta_dumps(doc: dict[str, Any]) -> str:
    """Indented like every other document here, and newline-terminated."""
    return json.dumps(doc, indent=2) + "\n"


def export_city(
    db_path: str,
    out_dir: str,
    theme_name: str = "default",
    pricing_path: str | None = None,
) -> list[Path]:
    """Write `city.json`, `meta.json` and the spritesheet into `out_dir`; return
    what was written.

    The spritesheet is copied rather than referenced in place so the output
    directory is self-contained -- `theme.spritesheet` in the document is a bare
    filename resolved next to `city.json`.

    `meta.json` carries the one fact `city.json` may not: when it was produced.
    Without it a static host's viewer measures the age of its own fetch and a
    week-old export reads as seconds old. See `meta_document`.

    `pricing_path` is `--pricing`; without it a `pricing.toml` beside the
    catalog is used, and without that the built-in local-DuckDB book, which
    is free. See `tycoon_city.pricing`.
    """
    theme = load_theme_data(theme_dir(theme_name))
    pricing = resolve_price_book(db_path, pricing_path)
    ctx, city = build_city(db_path, theme.style_rules)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    city_path = out / CITY_JSON
    city_path.write_text(dumps(city_document(ctx, city, theme, pricing)), encoding="utf-8")

    # Taken AFTER the city is written, so the stamp can never be older than the
    # document it describes.
    meta_path = out / META_JSON
    meta_path.write_text(meta_dumps(meta_document(datetime.now(UTC))), encoding="utf-8")

    sheet_path = out / theme.spritesheet_path.name
    shutil.copyfile(theme.spritesheet_path, sheet_path)
    return [city_path, meta_path, sheet_path, *_export_runs(ctx, out)]


def _export_runs(ctx: PipelineContext, out: Path) -> list[Path]:
    """`runs.json` plus one document per replayable run, at the same paths the
    server serves them from -- so a client written against the routes works
    unchanged against a static copy.

    `runs.json` is written even when there is no history: it carries the notes
    that say why, and a client that 404s on the index cannot tell "no runs"
    from "wrong host".
    """
    index = runs_index(ctx)
    index_path = out / RUNS_JSON
    index_path.write_text(run_dumps(index), encoding="utf-8")
    written = [index_path]

    runs_dir = out / RUNS_DIR
    for header in index["runs"]:
        name = run_file_name(header["id"])
        if name is None:
            # An id that cannot be a filename is refused, never sanitised into
            # some other run's name. Real invocation_ids are uuids.
            print(f"skipping run {header['id']!r}: not a safe file name", file=sys.stderr)
            continue
        runs_dir.mkdir(parents=True, exist_ok=True)
        path = runs_dir / name
        path.write_text(run_dumps(run_document(ctx, header["id"])), encoding="utf-8")
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tycoon-city-export",
        description="Export a DuckDB catalog as city.json for a renderer.",
    )
    parser.add_argument("db_path", help="Path to a DuckDB database file, or an md: catalog")
    parser.add_argument("out_dir", help="Directory to write city.json, meta.json and the spritesheet into")
    parser.add_argument("--theme", default="default", help="Theme name shipped under tycoon_city/themes/")
    parser.add_argument(
        "--pricing",
        default=None,
        help=(
            "TOML file declaring the compute rate the budget block is billed at "
            "(default: pricing.toml beside the catalog, else local DuckDB, free)"
        ),
    )
    args = parser.parse_args(argv)

    try:
        written = export_city(args.db_path, args.out_dir, args.theme, args.pricing)
    except (CatalogError, PricingError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    for path in written:
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
