"""Serve the interactive web app over HTTP: static bundle + fresh city.json.

The container's entrypoint, and the successor to the retired stills server.
Deliberately stdlib-only. The web bundle is static files built by Vite; the two
dynamic routes are generated from the database, so editing the database and
pressing R in the app shows the change.

`tycoon-city demo` is the same server over a generated demo catalog, dispatched
from `main` into `tycoon_city.demo.cli` before any path parsing happens.

Endpoints:
    GET /city.json        the contract document, exported fresh per request
    GET /meta.json        when the city.json beside it was produced -- here,
                          always `generated_at: null`, because this one was
                          produced for THIS request (see the route)
    GET /runs.json        the replayable runs, newest first (always 200: no
                          history is an empty list plus the loader's own note)
    GET /runs/<id>.json   one run, step by step; 404 with a JSON body for an
                          id that is not in the known invocation set
    GET /spritesheet.png  the active theme's atlas source
    GET /healthz          JSON catalog counts -- a probe can tell "up" from
                          "up but cannot read the data" (bad volume mount)
    GET /<anything else>  the built web app (index.html, assets/)

The catalog is read once per *change*, not once per request: `_SourceCache`
keys on the mtime and size of every file behind the loaded source, so pressing
R re-serves a parsed catalog until one of those files moves. Signals are
re-derived on every hand-out regardless, because ages are measured from the
wall clock and a frozen clock is a stale render.

Binds to 127.0.0.1 by default. A catalog names a client's schemas, tables and
columns; exposing that on every interface is an opt-in (`--host`), not the
default.
"""

import argparse
import json
import logging
import mimetypes
import os
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from .catalog.errors import CatalogError
from .catalog.models import PipelineContext
from .catalog.tycoon_project import TYCOON_FILE, read_project_info
from .export.build import build_city
from .export.city_json import city_document, dumps

# The meta document has ONE producer, and it is the exporter's. A server that
# spelled its own would be a second source of truth for a two-field document,
# which is exactly how the two halves drift apart.
from .export.cli import META_JSON, meta_document, meta_dumps
from .export.run_json import dumps as run_dumps
from .export.run_json import known_run_ids, run_document, runs_index
from .pricing import DEFAULT_PRICE_BOOK, PriceBook, PricingError, resolve_price_book
from .sim.channels import DEFAULT_BINDINGS, apply_signals
from .sim.city import CityMap
from .theme_data import load_theme_data, theme_dir

logger = logging.getLogger(__name__)

DEFAULT_PORT = 8000
# The one reserved word in the positional slot; everything else is a path.
DEMO_COMMAND = "demo"
# The run-replay routes. `/runs/<id>.json` never becomes a path: the id is
# matched against the known invocation set and the document is built in memory.
META_PATH = f"/{META_JSON}"
RUNS_INDEX_PATH = "/runs.json"
RUN_PREFIX = "/runs/"
RUN_SUFFIX = ".json"
# Loopback, deliberately. See the module docstring; --host / $DATABASE_TYCOON_HOST
# widens it, and the container image sets 0.0.0.0 because that is what a
# published port needs.
DEFAULT_HOST = "127.0.0.1"
# Set by the container; the demo catalog is baked in so a zero-argument
# `docker run` shows a city.
DB_ENV = "DATABASE_TYCOON_DB"
THEME_ENV = "DATABASE_TYCOON_THEME"
DIST_ENV = "DATABASE_TYCOON_WEB_DIST"
HOST_ENV = "DATABASE_TYCOON_HOST"


def _default_dist() -> Path | None:
    """Where the web bundle lives, most specific first.

    A repo checkout's `web/dist` wins over the packaged copy on purpose: a
    developer rebuilding the front end must see their own build, and a
    committed bundle must never shadow it mid-iteration. An installed wheel
    has no checkout, so it falls through to the packaged copy.

    `--dist` and `$DATABASE_TYCOON_WEB_DIST` are already checked ahead of this
    in `main()`; this function does not re-check them.
    """
    repo = Path(__file__).resolve().parents[2] / "web" / "dist"
    if repo.is_dir():
        return repo
    packaged = Path(__file__).resolve().parent / "web_dist"
    return packaged if packaged.is_dir() else None


def _source_files(db_path: str) -> list[Path] | None:
    """Every file a load of `db_path` reads, or None when there are no files
    behind it (an `md:` catalog, or a directory that is not a tycoon project).

    The list, not just the mtimes, is part of the key: a manifest that did not
    exist last request and does now is a change, and it shows up here as a new
    path rather than as a moved one.
    """
    if db_path.startswith("md:"):
        return None
    path = Path(db_path)
    if not path.is_dir():
        return [path]
    try:
        info = read_project_info(path)
    except ValueError:  # a broken tycoon.yml; let the loader report it, uncached
        return None
    if info is None:
        return None
    candidates = (
        path / TYCOON_FILE,
        info.warehouse_path,
        info.manifest_path,
        info.sources_json_path,
        info.metadata_db_path,
        info.requests_json_path,
    )
    return [p for p in candidates if p is not None]


def _fingerprint(db_path: str) -> tuple | None:
    """(path, mtime_ns, size) per source file, or None when the source cannot
    be fingerprinted and therefore must never be cached.

    Size rides along with the mtime because a filesystem with coarse mtimes
    would otherwise let a same-second rewrite pass as unchanged, and serving a
    catalog that has already changed is the one failure this cache may not
    have.

    **WAL sidecars.** DuckDB can leave committed writes in a `.wal` sidecar
    file, so the main file's mtime stays old while the content has changed.
    This is the "mtime/WAL staleness trap" (handover, 2026-08-07). We stat
    the `-wal` sidecar too: if it exists, its mtime+size is included in the
    fingerprint, so a WAL update invalidates the cache and forces a rebuild.
    """
    files = _source_files(db_path)
    if files is None:
        return None
    stamps = []
    for path in files:
        try:
            stat = path.stat()
        except OSError:  # missing right now is itself a state, and a change from present
            stamps.append((str(path), None, None))
        else:
            stamps.append((str(path), stat.st_mtime_ns, stat.st_size))
            # Check for a DuckDB WAL sidecar: `<db_path>-wal`.
            wal_path = Path(str(path) + "-wal")
            if wal_path.exists():
                try:
                    wal_stat = wal_path.stat()
                    stamps.append((str(wal_path), wal_stat.st_mtime_ns, wal_stat.st_size))
                except OSError:
                    stamps.append((str(wal_path), None, None))
    return tuple(stamps)


class _SourceCache:
    """One built city, reused until a file behind it moves.

    Rebuilding the whole context per request was the cost of the core loop
    (press R, look again): the catalog can only change when a file changes, so
    the fingerprint of those files is the key. A source with no files behind it
    fingerprints as None and is never cached — a wrong hit is worse than a slow
    refresh.

    Two rules keep "stale" impossible:

    - the fingerprint is re-taken *after* the build, and a build that raced a
      write is used but not stored (it would otherwise be filed under the
      stamp of the file it did not read);
    - the signals are re-derived on every hand-out, cache hit or not, because
      last-build age counts from the wall clock and a cached city would freeze
      it. The lock is held across the caller's use of the map for the same
      reason it is held across `apply_signals`: the cached `CityMap` is shared
      mutable state, and this server is threaded.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._key: tuple | None = None
        self._built: tuple[PipelineContext, CityMap] | None = None

    def _built_city(self, db_path: str, style_rules) -> tuple[PipelineContext, CityMap]:
        """Caller holds the lock."""
        fingerprint = _fingerprint(db_path)
        key = None if fingerprint is None else (db_path, fingerprint)
        if self._built is not None and key is not None and self._key == key:
            return self._built
        built = build_city(db_path, style_rules)
        self._built = built
        # Re-taken after the read: if a file moved while the build was running,
        # `key` describes a state nobody read, so store nothing at all.
        self._key = key if _fingerprint(db_path) == fingerprint else None
        return built

    @contextmanager
    def city(self, db_path: str, style_rules) -> Iterator[tuple[PipelineContext, CityMap]]:
        with self._lock:
            ctx, city = self._built_city(db_path, style_rules)
            apply_signals(city, ctx, DEFAULT_BINDINGS)
            yield ctx, city

    def context(self, db_path: str, style_rules) -> PipelineContext:
        with self._lock:
            return self._built_city(db_path, style_rules)[0]


class _Handler(BaseHTTPRequestHandler):
    db_path: str
    theme_name: str
    dist: Path
    # Resolved once at startup, not per request: a mistyped rate file must
    # fail the boot loudly rather than 500 on the first city.json.
    pricing: PriceBook = DEFAULT_PRICE_BOOK
    # Shared by default; `serve` gives each server its own, and the key
    # carries db_path so two sources can never see each other's build.
    cache: _SourceCache = _SourceCache()

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler's spelling)
        path = self.path.split("?", 1)[0]
        try:
            if path == "/healthz":
                self._healthz()
            elif path == "/city.json":
                self._city_json()
            elif path == META_PATH:
                self._meta_json()
            elif path == "/requests.json":
                self._requests_json()
            elif path == RUNS_INDEX_PATH:
                self._runs_json()
            elif path.startswith(RUN_PREFIX) and path.endswith(RUN_SUFFIX):
                self._run_json(path)
            elif path == "/spritesheet.png":
                self._file(theme_dir(self.theme_name) / "spritesheet.png")
            else:
                self._static(path)
        except BrokenPipeError:
            pass
        except Exception:
            logger.exception("error serving %s", self.path)
            self._respond(500, b"internal error", "text/plain")

    def _healthz(self) -> None:
        ctx = self._context()
        if ctx is None:
            return
        body = json.dumps(
            {
                "status": "ok",
                "database": ctx.database_name,
                "objects": ctx.object_count,
                "edges": len(ctx.edges),
            }
        ).encode()
        self._respond(200, body, "application/json")

    def _style_rules(self):
        return load_theme_data(theme_dir(self.theme_name)).style_rules

    def _city_json(self) -> None:
        theme = load_theme_data(theme_dir(self.theme_name))
        try:
            # The document is serialised inside the cache's lock: the cached
            # CityMap is shared, and its signals were just re-derived.
            with self.cache.city(self.db_path, theme.style_rules) as (ctx, city):
                body = dumps(city_document(ctx, city, theme, self.pricing)).encode()
        except CatalogError as exc:
            self._respond(503, str(exc).encode(), "text/plain")
            return
        self._respond(200, body, "application/json")

    def _meta_json(self) -> None:
        """`generated_at: null`, always, and that is the honest answer.

        A served city.json is built for the request that asked for it, so its
        age IS the age of that fetch and there is no earlier moment to report.
        Answering 200 with a null rather than 404 is the point: the client asks
        one question of one document and gets a named "no export time here",
        instead of having to read a missing file as a fact. A static export
        written before this document existed still 404s, and lands on the same
        fallback -- the absence stays named either way.

        Needs no catalog, so it never 503s: this route describes the DOCUMENT's
        provenance, not the database's health (that is /healthz).
        """
        body = meta_dumps(meta_document(None)).encode()
        self._respond(200, body, "application/json")

    def _runs_json(self) -> None:
        """Always 200 for a readable catalog. No history and a metadata database
        locked by a running `tycoon` command are both an empty `runs` list plus
        the loader's own sentence, carried through in `notes` — restating either
        here would create a second wording to keep in sync."""
        ctx = self._context()
        if ctx is None:
            return
        self._respond(200, run_dumps(runs_index(ctx)).encode(), "application/json")

    def _requests_json(self) -> None:
        """Serves requests.json if present, otherwise 404."""
        # This is inefficient: it checks the file system on every request.
        # But this is only done if ?crlf=1 is passed, and requests are not
        # huge, so it's probably fine for now.
        if self.db_path.startswith("md:"):
            self._respond(404, b"not found", "text/plain")
            return

        info = read_project_info(Path(self.db_path))
        if info is None or info.requests_json_path is None or not info.requests_json_path.is_file():
            self._respond(404, b"not found", "text/plain")
            return

        self._file(info.requests_json_path)

    def _run_json(self, path: str) -> None:
        ctx = self._context()
        if ctx is None:
            return
        run_id = unquote(path[len(RUN_PREFIX) : -len(RUN_SUFFIX)])
        # Validated against the known invocation set BEFORE the id is used for
        # anything else. Nothing here opens a file, and this is why nothing can.
        if run_id not in known_run_ids(ctx):
            body = json.dumps({"error": "unknown run", "id": run_id}).encode()
            self._respond(404, body, "application/json")
            return
        self._respond(200, run_dumps(run_document(ctx, run_id)).encode(), "application/json")

    def _context(self) -> PipelineContext | None:
        """The cached context, or None having already answered 503.

        Shares `_SourceCache` with /city.json and /healthz, so a run route
        re-reads the catalog only when a file behind it has moved.
        """
        try:
            return self.cache.context(self.db_path, self._style_rules())
        except CatalogError as exc:
            self._respond(
                503,
                json.dumps({"status": "error", "detail": str(exc)}).encode(),
                "application/json",
            )
            return None

    def _static(self, path: str) -> None:
        name = path.lstrip("/") or "index.html"
        target = (self.dist / name).resolve()
        # The guard, not a nicety: without it ../../ walks out of the bundle.
        if not target.is_relative_to(self.dist.resolve()) or not target.is_file():
            self._respond(404, b"not found", "text/plain")
            return
        self._file(target)

    def _file(self, target: Path) -> None:
        if not target.is_file():
            self._respond(404, b"not found", "text/plain")
            return
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self._respond(200, target.read_bytes(), content_type)

    def _respond(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # The server decides freshness (see _SourceCache); a browser-side copy
        # would survive a file change and make R show stale data.
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        logger.info("%s %s", self.address_string(), format % args)


def serve(
    db_path: str,
    dist: Path,
    theme_name: str,
    port: int,
    host: str = DEFAULT_HOST,
    pricing: PriceBook | None = None,
) -> None:
    handler = type(
        "Handler",
        (_Handler,),
        {
            "db_path": db_path,
            "theme_name": theme_name,
            "dist": dist,
            "cache": _SourceCache(),
            "pricing": pricing or DEFAULT_PRICE_BOOK,
        },
    )
    server = ThreadingHTTPServer((host, port), handler)
    logger.info("serving %s with %s on http://%s:%d", db_path, dist, host, port)
    server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    """The argparse surface: `python -m tycoon_city.webserve [demo] ...`.

    The `tycoon-city` console script is the Typer surface (`tycoon_city.cli`);
    both land in `run_server` / `demo.cli.run`. Env-var defaults live in the
    parsers, not in `run_server`, so the Docker image keeps working unflagged.
    """
    # `demo` is dispatched BEFORE argparse rather than as a subparser: adding
    # subparsers to this parser would turn `python -m tycoon_city.webserve
    # path/to/db.duckdb` -- the positional-path invocation -- into an
    # unknown-command error. The import is local so the demo generator (which
    # writes DuckDB files) never loads for an ordinary serve.
    args_in = sys.argv[1:] if argv is None else argv
    if args_in and args_in[0] == DEMO_COMMAND:
        from .demo.cli import main as demo_main

        return demo_main(args_in[1:])

    parser = argparse.ArgumentParser(
        prog="python -m tycoon_city.webserve",
        description="Serve the interactive Database Tycoon city for a DuckDB catalog.",
        epilog="`tycoon-city demo` (or `python -m tycoon_city.webserve demo`) serves a generated demo catalog with nothing to set up.",
    )
    parser.add_argument(
        "db_path",
        nargs="?",
        default=os.environ.get(DB_ENV),
        help=f"DuckDB file, md: catalog, or tycoon project dir (default: ${DB_ENV})",
    )
    parser.add_argument(
        "--dist",
        default=os.environ.get(DIST_ENV),
        help=f"Built web bundle directory (default: ${DIST_ENV}, else the repo's web/dist)",
    )
    parser.add_argument("--theme", default=os.environ.get(THEME_ENV, "default"))
    parser.add_argument(
        "--pricing",
        default=None,
        help=(
            "TOML file declaring the compute rate the budget block is billed at "
            "(default: pricing.toml beside the catalog, else local DuckDB, free)"
        ),
    )
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", DEFAULT_PORT)))
    parser.add_argument(
        "--host",
        default=os.environ.get(HOST_ENV, DEFAULT_HOST),
        help=(
            f"Interface to bind (default: ${HOST_ENV}, else {DEFAULT_HOST}). "
            "The city names real schemas, tables and columns -- pass 0.0.0.0 "
            "only when you mean to publish them."
        ),
    )
    args = parser.parse_args(args_in)
    return run_server(
        db_path=args.db_path,
        dist=Path(args.dist) if args.dist else None,
        theme=args.theme,
        pricing=args.pricing,
        port=args.port,
        host=args.host,
    )


def run_server(
    *,
    db_path: str | None,
    dist: Path | None,
    theme: str,
    pricing: str | None,
    port: int,
    host: str,
) -> int:
    """Validate the inputs and serve. Returns the process exit code; every
    refusal is one line on stderr naming what was missing."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if not db_path:
        print(f"no database: pass a path or set ${DB_ENV}", file=sys.stderr)
        return 1
    bundle = dist if dist else _default_dist()
    if bundle is None or not bundle.is_dir():
        print(
            f"no web bundle: run `npm run build` in web/, pass --dist, or set ${DIST_ENV}",
            file=sys.stderr,
        )
        return 1

    try:
        price_book = resolve_price_book(db_path, pricing)
    except PricingError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    serve(db_path, bundle, theme, port, host, price_book)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
