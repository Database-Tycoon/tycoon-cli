"""Point Database Tycoon at a REAL catalog and report what breaks or degrades.

    uv run python scripts/readiness.py <path-to-db-or-project> [--names]

One command that exercises the whole stack -- catalog scan, manifest, column
lineage, run history, semantic model, layout, `city.json`, the run documents --
against a catalog nobody here has ever seen. Exits non-zero if anything is
outright broken, so it doubles as a smoke test.

**Safe to run on client data.** The default output is aggregate and
non-identifying -- counts, distributions, timings, degradation notes, the
presence or absence of each signal -- and no object, schema or column name, no
SQL, description or path is printed unless you pass `--names` (`--verbose` is
a synonym). The loader's notes are the one place client text could ride along,
so `_Redactor` blanks every identifier this run saw out of them first. The
point is that the default output is pasteable into a chat window without
leaking a client's schema. Read-only throughout; nothing is written outside a
temporary directory.
"""

import argparse
import re
import shutil
import sys
import tempfile
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dbtycoon.catalog import loader as loader_mod  # noqa: E402
from dbtycoon.catalog import retention as retention_mod  # noqa: E402
from dbtycoon.catalog.errors import CatalogError  # noqa: E402
from dbtycoon.catalog.models import PipelineContext  # noqa: E402
from dbtycoon.catalog.tycoon_project import read_project_info  # noqa: E402
from dbtycoon.export.blocks import decode_rle  # noqa: E402
from dbtycoon.export.city_json import city_document, dumps  # noqa: E402
from dbtycoon.export.cli import export_city  # noqa: E402
from dbtycoon.sim.channels import DEFAULT_BINDINGS, apply_signals  # noqa: E402
from dbtycoon.sim.generator import generate_city  # noqa: E402
from dbtycoon.sim.layout import compute_depths, isolated_keys  # noqa: E402
from dbtycoon.sim.tiles import TileKind  # noqa: E402
from dbtycoon.theme_data import load_theme_data, theme_dir  # noqa: E402

# The refresh loop is the product: pressing R re-serialises a cached city when
# nothing changed and reloads everything when a file behind the source did.
COMFORTABLE_S = 1.0
TOLERABLE_S = 3.0

# Above this share, lineage is mostly guesses from unqualified table names --
# the hairball failure mode, where a table called `status` wires itself to half
# the city. Qualified and declared edges are facts; bare names are inferences.
BARE_NAME_ALARM = 0.5

# Past this, `city.json` stops being a document a browser fetches and starts
# being a download: a 500-object catalog of long chains measured 63 MB.
BIG_DOCUMENT_BYTES = 8_000_000


class _Redactor:
    """Blank every identifier this catalog contains out of a string. Applied to
    the loader's notes, which are count-shaped by design but may quote a dbt
    target. Longest first, so a schema name that prefixes a key leaves no tail."""

    def __init__(self, names: set[str]) -> None:
        useful = sorted((n for n in names if len(n) >= 3), key=len, reverse=True)
        self._pattern = re.compile("|".join(re.escape(n) for n in useful)) if useful else None

    def __call__(self, text: str) -> str:
        return self._pattern.sub("<redacted>", text) if self._pattern else text


def _identifiers(ctx: PipelineContext) -> set[str]:
    names: set[str] = set(ctx.columns_by_key) | set(ctx.dbt_nodes_by_key.values())
    for obj in ctx.objects:
        names.update((obj.schema, obj.name, obj.key))
    for columns in ctx.columns_by_key.values():
        names.update(name for name, _type in columns)
    for refs in ctx.tests_by_key.values():
        names.update(ref.unique_id for ref in refs)
    if ctx.runs is not None:
        names.update(run.target for run in ctx.runs.runs if run.target)
        names.update(ctx.runs.node_results)
        names.update(ctx.runs.dlt_loaded_at)
    return {n for n in names if n}


# --- stage timing: the loader has no timing hooks and should not grow any for
# a diagnostic, so this wraps its collaborators for the duration of one load.
# Each name is patched on the module that CALLS it -- `from x import y` binds
# `y` into the caller's namespace, so patching it elsewhere times nothing.


def _on(module, *attrs):
    return [(module, attr) for attr in attrs]


_STAGES = {
    "catalog scan": _on(loader_mod, "_scan_catalog", "_scan_columns", "_fetch_dependency_edges"),
    "table lineage": _on(loader_mod, "scan_view_sql") + _on(retention_mod, "mentioned_keys"),
    "column lineage": _on(loader_mod, "derive_column_lineage"),
    "dbt manifest": _on(loader_mod, "read_manifest", "join_manifest", "read_source_freshness"),
    "semantic model": _on(loader_mod, "read_osi", "join_semantics"),
    "run history": _on(loader_mod, "read_run_history"),
}


@contextmanager
def _stage_timings():
    elapsed: dict[str, float] = {}
    saved = []
    for stage, targets in _STAGES.items():
        for module, attr in targets:
            original = getattr(module, attr)
            saved.append((module, attr, original))

            def wrapper(*args, _fn=original, _stage=stage, **kwargs):
                start = time.perf_counter()
                try:
                    return _fn(*args, **kwargs)
                finally:
                    elapsed[_stage] = elapsed.get(_stage, 0.0) + time.perf_counter() - start

            setattr(module, attr, wrapper)
    try:
        yield elapsed
    finally:
        for module, attr, original in saved:
            setattr(module, attr, original)


def _raw_scan(source: str) -> tuple[int, int] | None:
    """(tables, views) as the warehouse holds them, BEFORE the cap. Uses the
    loader's own scan, so it cannot drift into a second opinion about what
    belongs to the connected database."""
    import duckdb

    path = source
    if not source.startswith("md:") and Path(source).is_dir():
        info = read_project_info(source)
        if info is None:
            return None
        path = str(info.warehouse_path)
    try:
        con = duckdb.connect(path, read_only=True)
    except duckdb.Error:
        return None
    try:
        tables, views = loader_mod._scan_catalog(con)
    except duckdb.Error:
        return None
    finally:
        con.close()
    return len(tables), len(views)


# --- report helpers ---------------------------------------------------------


class Report:
    def __init__(self) -> None:
        self.broken: list[str] = []
        self.warnings: list[str] = []

    def line(self, text: str = "") -> None:
        print(text)

    def head(self, text: str) -> None:
        print()
        print(text)
        print("-" * len(text))

    def kv(self, label: str, value) -> None:
        print(f"  {label:<34} {value}")

    def broke(self, text: str) -> None:
        self.broken.append(text)

    def warn(self, text: str) -> None:
        self.warnings.append(text)


def _histogram(counts: Counter, limit: int = 12) -> str:
    items = sorted(counts.items())
    text = ", ".join(f"{k}:{v}" for k, v in items[:limit])
    return text + (f", ... (+{len(items) - limit} more)" if len(items) > limit else "")


def _verdict(seconds: float) -> str:
    if seconds <= COMFORTABLE_S:
        return "comfortable"
    return "noticeable" if seconds <= TOLERABLE_S else "uncomfortable"


# --- the sections -----------------------------------------------------------


def _report_timings(report: Report, stages: dict[str, float], cold: float) -> None:
    report.head("LOAD TIME BY STAGE")
    for stage in _STAGES:
        report.kv(stage, f"{stages.get(stage, 0.0):8.3f}s")
    report.kv("everything else", f"{max(cold - sum(stages.values()), 0.0):8.3f}s")
    report.kv("TOTAL catalog load", f"{cold:8.3f}s")


def _report_catalog(report: Report, ctx: PipelineContext, raw: tuple[int, int] | None) -> None:
    report.head("CATALOG")
    kinds = Counter(obj.kind for obj in ctx.objects)
    report.kv("objects", f"{ctx.object_count} ({kinds['table']} tables, {kinds['view']} views)")
    report.kv("schemas", len({obj.schema for obj in ctx.objects}))
    report.kv("total rows", f"{ctx.total_rows:,}")
    report.kv("objects with measured columns", len(ctx.columns_by_key))
    report.kv("columns measured", sum(len(c) for c in ctx.columns_by_key.values()))

    if ctx.object_count == 0:
        report.warn("the catalog holds no objects at all -- there is nothing to render")

    report.head("CAP (MAX_OBJECTS)")
    report.kv("cap", retention_mod.MAX_OBJECTS)
    if raw is None:
        report.kv("catalog size before the cap", "unavailable (could not re-scan)")
        return
    tables, views = raw
    total = tables + views
    report.kv("catalog size before the cap", f"{total} ({tables} tables, {views} views)")
    if total <= retention_mod.MAX_OBJECTS:
        report.kv("fired", "no")
        return
    report.kv("fired", "YES")
    report.kv("dropped", f"{total - ctx.object_count} objects")
    report.kv("tables kept", f"{kinds['table']} of {tables}")
    report.kv("views kept", f"{kinds['view']} of {views}")
    report.warn(f"the cap dropped {total - ctx.object_count} of {total} objects; the city is a subset of this catalog")
    if views and kinds["view"] == 0:
        report.broke("the cap kept no views at all -- view SQL is where lineage comes from")
    if tables and kinds["table"] == 0:
        report.broke("the cap kept no tables at all -- every view's sources were dropped")


def _report_lineage(report: Report, ctx: PipelineContext) -> None:
    report.head("LINEAGE")
    provenance = Counter(edge.provenance for edge in ctx.edges)
    scanned = provenance["view_sql"]
    bare = min(ctx.bare_name_edges, scanned)
    report.kv("edges", len(ctx.edges))
    report.kv("  declared (dbt manifest)", provenance["manifest"])
    report.kv("  engine dependency catalog", provenance["duckdb"])
    report.kv("  view SQL, schema-qualified", scanned - bare)
    report.kv("  view SQL, bare name only", bare)
    report.kv("column-level edges", len(ctx.column_edges))
    report.kv("declared joins (OSI)", len(ctx.semantic_relationships))

    if ctx.edges and bare / len(ctx.edges) > BARE_NAME_ALARM:
        report.warn(
            f"{bare} of {len(ctx.edges)} edges were matched on an unqualified table "
            "name alone -- the hairball failure mode. Expect invented streets"
        )
    if ctx.object_count > 1 and not ctx.edges:
        report.warn("no lineage at all: every building is an orphan, the city has no streets")

    depths = compute_depths(ctx)
    orphans = isolated_keys(ctx)
    report.kv("orphans (no edge either way)", f"{len(orphans)} of {ctx.object_count}")
    report.kv("depth histogram (depth:count)", _histogram(Counter(depths.values())))
    report.kv("deepest chain", max(depths.values(), default=0))
    fan_in = Counter(edge.dst for edge in ctx.edges)
    fan_out = Counter(edge.src for edge in ctx.edges)
    report.kv(
        "widest fan-in / fan-out",
        f"{max(fan_in.values(), default=0)} / {max(fan_out.values(), default=0)}",
    )


def _report_signals(report: Report, ctx: PipelineContext, doc: dict) -> None:
    report.head("SIGNALS PRESENT (of the whole catalog)")
    total = ctx.object_count or 1
    described = sum(1 for c in ctx.dbt_context_by_key.values() if c.description)
    semantic = sum(1 for entry in doc["objects"] if entry.get("semantic"))
    usage = sum(1 for entry in doc["objects"] if entry.get("usage"))

    def pct(count: int) -> str:
        return f"{count} ({count * 100 // total}%)"

    report.kv("joined to a dbt node", pct(len(ctx.dbt_nodes_by_key)))
    report.kv("with a description", pct(described))
    report.kv("with declared tests", pct(len(ctx.tests_by_key)))
    report.kv("with a freshness verdict", pct(len(ctx.source_freshness_by_key)))
    report.kv("with measured usage", pct(usage))
    report.kv("with a semantic block", pct(semantic))
    report.kv("weather cells", len(doc["weather"]["cells"]))
    report.kv("budget block", "present" if doc["budget"] else "null (nothing priced)")

    report.head("RUN HISTORY")
    if ctx.runs is None:
        report.kv("run history", "absent")
        return
    report.kv("invocations", len(ctx.runs.runs))
    report.kv("replayable invocations", len(ctx.runs.run_nodes))
    report.kv("nodes with a latest result", len(ctx.runs.node_results))
    report.kv("nodes with a build history", len(ctx.runs.build_history))
    replay = doc["replay"]
    steps = f"{len(replay['steps'])} steps" if replay else "null (nothing replayable)"
    report.kv("build-replay schedule", steps)
    known = set(ctx.dbt_nodes_by_key.values())
    for refs in ctx.tests_by_key.values():
        known.update(ref.unique_id for ref in refs)
    orphaned = [node for node in ctx.runs.node_results if node not in known]
    report.kv("run nodes not in this catalog", len(orphaned))


def _report_rendering(report: Report, city, doc: dict, text: str) -> None:
    report.head("RENDERING")
    tiles = Counter(tile for row in city.tiles for tile in row)
    report.kv("grid", f"{city.width} x {city.height} ({city.width * city.height:,} tiles)")
    report.kv("road tiles", tiles[TileKind.ROAD])
    report.kv("lot tiles", tiles[TileKind.LOT])
    report.kv("lots placed", len(city.lots))
    report.kv("districts", len(doc["districts"]))
    report.kv("street features", len(doc["street_features"]))
    size = len(text.encode("utf-8"))
    report.kv("city.json", f"{size:,} bytes")
    report.kv("tiles_rle runs", len(doc["grid"]["tiles_rle"]) // 2)
    # Streets ARE the lineage, so every edge ships its tile path. On a wide
    # grid those paths, not the tiles, are what makes the document big.
    report.kv("edge route points", sum(len(e.get("route") or ()) for e in doc["edges"]))
    if size > BIG_DOCUMENT_BYTES:
        report.warn(
            f"city.json is {size // 1_000_000} MB -- a browser will struggle to fetch and "
            "parse it; the edge routes are what scale with grid width"
        )

    plates = doc["districts"]
    overlaps = sum(
        a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"] and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]
        for i, a in enumerate(plates)
        for b in plates[i + 1 :]
    )
    report.kv("overlapping district plates", overlaps)
    if overlaps:
        report.warn(
            f"{overlaps} district plate pairs overlap -- legal (plates are tint, not land) but labels will stack there"
        )
    try:
        decode_rle(doc["grid"]["tiles_rle"], city.width, city.height)
    except ValueError as exc:
        report.broke(f"tiles_rle does not decode back to the grid: {exc}")


# --- the run ----------------------------------------------------------------


def _load(source: str):
    with _stage_timings() as stages:
        start = time.perf_counter()
        ctx = loader_mod.load_context(source)
        cold = time.perf_counter() - start
    return ctx, stages, cold


def run(source: str, theme_name: str, show_names: bool) -> int:
    report = Report()
    theme = load_theme_data(theme_dir(theme_name))

    md = source.startswith("md:")
    kind = "MotherDuck catalog" if md else "tycoon project directory" if Path(source).is_dir() else "DuckDB file"  # noqa: E501
    report.line("Database Tycoon -- real-catalog readiness")
    report.line(f"source: {source if show_names else kind}")
    report.line(
        "--names: this output CONTAINS catalog identifiers. Do not paste it anywhere public."
        if show_names
        else "output is aggregate only: no object, schema or column names, no SQL, no "
        "descriptions. Pass --names to include them."
    )

    try:
        ctx, stages, cold = _load(source)
    except CatalogError as exc:
        report.line(f"\nBROKEN: the catalog could not be loaded: {exc if show_names else ''}")
        return 1

    redact = (lambda text: text) if show_names else _Redactor(_identifiers(ctx))

    start = time.perf_counter()
    city = generate_city(ctx, theme.style_rules)
    apply_signals(city, ctx, DEFAULT_BINDINGS)
    layout_s, start = time.perf_counter() - start, time.perf_counter()
    doc = city_document(ctx, city, theme)
    text = dumps(doc)
    document_s = time.perf_counter() - start

    _report_timings(report, stages, cold)

    report.head("REFRESH LOOP (pressing R)")
    report.kv("cold: load + layout + document", f"{cold + layout_s + document_s:8.3f}s")
    report.kv("  layout", f"{layout_s:8.3f}s")
    report.kv("  document + serialise", f"{document_s:8.3f}s")
    start = time.perf_counter()
    cached_text = dumps(city_document(ctx, city, theme))
    cached_s = time.perf_counter() - start
    report.kv("cached: re-serve, nothing changed", f"{cached_s:8.3f}s")

    out_dir = Path(tempfile.mkdtemp(prefix="readiness-export-"))
    try:
        start = time.perf_counter()
        written = export_city(source, str(out_dir), theme_name)
        report.kv("static export (dbtycoon-export)", f"{time.perf_counter() - start:8.3f}s")
        report.kv("files written by the export", len(written))
    except Exception as exc:  # noqa: BLE001 -- a diagnostic reports, never raises
        report.broke(f"the static export failed: {type(exc).__name__}")
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)

    report.kv("VERDICT: cold refresh", _verdict(cold + layout_s + document_s))
    report.kv("VERDICT: cached refresh", _verdict(cached_s))

    if cached_text != text:
        report.broke("city.json is not byte-stable: two emits of one city differ")

    raw = None if md else _raw_scan(source)
    _report_catalog(report, ctx, raw)
    _report_lineage(report, ctx)
    _report_signals(report, ctx, doc)
    _report_rendering(report, city, doc, text)

    if ctx.object_count and not city.lots:
        report.broke("the catalog has objects but the city has no lots")
    if len(city.lots) != ctx.object_count:
        report.broke(
            f"{ctx.object_count} objects became {len(city.lots)} lots -- "
            "objects are being lost between the catalog and the map"
        )

    report.head("DEGRADATION NOTES (what the loader said was missing)")
    if not ctx.notes:
        report.line("  (none -- every artifact this catalog offered was read)")
    for note in ctx.notes:
        report.line(f"  - {redact(note)}")

    if show_names:
        report.head("NAMES (--names)")
        report.kv("schemas", ", ".join(sorted({o.schema for o in ctx.objects})))
        depths = sorted(compute_depths(ctx).items(), key=lambda kv: (-kv[1], kv[0]))
        for key, depth in depths[:10]:
            report.kv(f"  depth {depth}", key)

    report.head("VERDICT")
    for finding in report.warnings:
        report.line(f"  DEGRADED: {finding}")
    for finding in report.broken:
        report.line(f"  BROKEN:   {finding}")
    if not report.warnings and not report.broken:
        named = f"; {len(ctx.notes)} named absences above" if ctx.notes else ", nothing degraded"
        report.line(f"  clean: nothing broken{named}")
    return 1 if report.broken else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="readiness.py",
        description="Exercise the whole stack against a real catalog and report what breaks "
        "or degrades. Read-only; safe to run on client data.",
    )
    parser.add_argument("source", help="A DuckDB file, a tycoon project directory, or md:<catalog>")
    parser.add_argument("--theme", default="default")
    parser.add_argument(
        "--names",
        "--verbose",
        dest="names",
        action="store_true",
        help="Include catalog identifiers (schema/object names, the source path) in the output",
    )
    args = parser.parse_args(argv)
    try:
        return run(args.source, args.theme, args.names)
    except Exception as exc:  # noqa: BLE001 -- the harness reports breakage, never traces it
        if args.names:
            raise
        print(f"\nBROKEN: {type(exc).__name__} during the run (--names shows the traceback)")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
