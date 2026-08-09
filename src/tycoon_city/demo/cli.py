"""`tycoon-city demo` — the whole product, with nothing to set up first.

For the conference laptop, and for anyone who wants to look at a city before
deciding whether to point this at their own warehouse. It materialises the demo
project (`tycoon_city.demo.project`) into a temp directory and serves it exactly
as `tycoon-city <path>` would: same server, same routes, same document. Nothing
here is a special "demo mode" in the renderer — a demo that took a different
code path would stop being evidence about the product.

Two dependencies it deliberately does NOT have:

- `scripts/make_demo_tycoon.py`, which needs a checkout. An installed wheel has
  no `scripts/`, and the whole promise of the subcommand is `pip install` then
  one word.
- write access to anything but `$TMPDIR`.

It DOES need a built web bundle, exactly as the server always has — the
JavaScript is not in the wheel. The error below says so in the three ways you
might have one.
"""

import argparse
import logging
import os
import signal
import sys
from pathlib import Path

from ..webserve import DEFAULT_HOST, DEFAULT_PORT, DIST_ENV, HOST_ENV, _default_dist, serve
from . import materialise

# Where the demo lands. The lens picker and the guided tour are the first-run
# experience -- the picker opens itself on a browser that has never chosen, and
# `?tour=1` is what turns a pretty map into an explained one. A first-time
# viewer dropped on a bare `/` gets neither and has to guess.
DEMO_QUERY = "?tour=1"


def main(argv: list[str]) -> int:
    """`argv` is everything AFTER the `demo` word."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(
        prog="tycoon-city demo",
        description=(
            "Serve a generated demo catalog -- a whole tycoon project with runs, "
            "tests, a failure cascade, freshness verdicts and a semantic model. "
            "Nothing to install and nothing written outside a temp directory."
        ),
    )
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", DEFAULT_PORT)))
    parser.add_argument(
        "--host",
        default=os.environ.get(HOST_ENV, DEFAULT_HOST),
        # Same env var as the ordinary server, so `docker run ... tycoon-city demo`
        # inherits the image's 0.0.0.0 and needs no flag. The DEFAULT is still
        # loopback -- but note this catalog is synthetic, so widening it
        # exposes nothing of yours.
        help=f"Interface to bind (default: ${HOST_ENV}, else {DEFAULT_HOST})",
    )
    parser.add_argument("--theme", default="default")
    parser.add_argument("--dist", default=None, help=f"Built web bundle directory (default: ${DIST_ENV})")
    args = parser.parse_args(argv)

    dist_arg = args.dist or os.environ.get(DIST_ENV)
    dist = Path(dist_arg) if dist_arg else _default_dist()
    if dist is None or not dist.is_dir():
        print(
            "no web bundle to serve the demo with. Get one by:\n"
            "  cd web && npm install && npm run build   (a checkout)\n"
            "  docker run --rm -p 8000:8000 tycoon-city    (no Python at all)\n"
            f"  --dist <dir> / ${DIST_ENV}              (a bundle you already built)",
            file=sys.stderr,
        )
        return 1

    if Path("demo").exists():
        # Ambiguity, named rather than resolved by guessing: `demo` is the
        # subcommand, and a directory of that name is reached as `./demo`.
        print(
            "note: `demo` is a subcommand -- serving the built-in demo project, "
            "not ./demo. Use `tycoon-city ./demo` for the directory.",
            file=sys.stderr,
        )

    # SIGTERM raises KeyboardInterrupt too, so `docker stop` and a plain `kill`
    # unwind through the same `finally` that Ctrl-C does and take the temp
    # directory with them. Without this the default SIGTERM handler kills the
    # process outright and leaves a few megabytes of demo project behind.
    signal.signal(signal.SIGTERM, signal.default_int_handler)

    print("building the demo project (timestamps are generated fresh)...", file=sys.stderr)
    with materialise() as project:
        print(f"demo project at {project}", file=sys.stderr)
        print(f"open http://{args.host}:{args.port}/{DEMO_QUERY}", file=sys.stderr)
        try:
            serve(str(project), dist, args.theme, args.port, args.host)
        except KeyboardInterrupt:
            print("", file=sys.stderr)
    return 0
