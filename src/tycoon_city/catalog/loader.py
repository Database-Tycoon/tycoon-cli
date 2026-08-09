import dataclasses
import logging
from pathlib import Path

import duckdb

from .column_lineage import ColumnEdge, derive_column_lineage
from .dbt_manifest import join_manifest, read_manifest, read_source_freshness
from .errors import CatalogError
from .models import CatalogObject, Edge, PipelineContext, canonical_keys
from .osi import discover_osi_path, join_semantics, read_osi
from .retention import cap_catalog, drop_duplicate_keys
from .run_history import RunHistory, read_run_history
from .sql_lineage import scan_view_sql
from .tycoon_project import TycoonProjectInfo, read_project_info

logger = logging.getLogger(__name__)

# `MAX_OBJECTS` is deliberately NOT re-exported here. `catalog.retention` reads
# it and decides the cap; a second binding in this module would be a second
# name for one rule, and two names for one rule stop agreeing.
__all__ = ["load_catalog", "load_context"]

# A MotherDuck catalog, e.g. "md:my_db" or a share URL "md:_share/name/uuid".
_MD_PREFIX = "md:"


def _is_motherduck(source: str) -> bool:
    return source.startswith(_MD_PREFIX)


def _database_name_for(source: str) -> str:
    """The name to show in the status strip.

    For a file that is its stem. For MotherDuck it is the catalog name: the
    segment after `md:`, or the middle segment of a share URL
    (`md:_share/<name>/<uuid>`), since neither `_share` nor a UUID tells anyone
    which database they are looking at.
    """
    if not _is_motherduck(source):
        return Path(source).stem
    rest = source[len(_MD_PREFIX) :]
    parts = [p for p in rest.split("/") if p]
    if parts and parts[0] == "_share" and len(parts) >= 2:
        return parts[1]
    return parts[0] if parts else rest


def _scan_catalog(
    con: duckdb.DuckDBPyConnection,
) -> tuple[list[tuple], list[tuple]]:
    """Tables and views belonging to the *connected* database only.

    The `database_name = current_database()` filter is load-bearing, not
    defensive. `duckdb_tables()` and `duckdb_views()` list every **attached**
    database. Against a local file nothing is attached, so an unscoped query
    looks correct; MotherDuck attaches every database and share in the account
    on connect, so an unscoped query would merge a whole account into one city
    and exhaust MAX_OBJECTS with objects the caller never asked for.

    `current_database()` is unaffected by ATTACH, so it names the connection's
    own database in both cases and needs no MotherDuck special-casing.
    """
    tables = con.execute(
        "select schema_name, table_name, estimated_size, table_oid "
        "from duckdb_tables() where not internal and database_name = current_database()"
    ).fetchall()
    view_rows = con.execute(
        "select schema_name, view_name, sql, view_oid "
        "from duckdb_views() where not internal and database_name = current_database()"
    ).fetchall()
    return tables, view_rows


def _scan_columns(con: duckdb.DuckDBPyConnection) -> dict[str, tuple[tuple[str, str], ...]]:
    """Measured column structure per object key: (name, type) in table order.
    Same database_name scoping as the catalog scan, same reason."""
    rows = con.execute(
        "select schema_name, table_name, column_name, data_type "
        "from duckdb_columns() where not internal and database_name = current_database() "
        "order by schema_name, table_name, column_index"
    ).fetchall()
    columns: dict[str, list[tuple[str, str]]] = {}
    for schema, table, name, data_type in rows:
        columns.setdefault(f"{schema}.{table}", []).append((name, data_type))
    return {key: tuple(value) for key, value in columns.items()}


def load_catalog(path: Path | str) -> PipelineContext:
    """A catalog on its own: no manifest, no run history, no semantics."""
    return _load_base(path)[0]


def _load_base(path: Path | str) -> tuple[PipelineContext, frozenset[tuple[str, str]]]:
    """`load_catalog`, plus which edges rest on a bare name alone.

    The pair set rides alongside rather than on the context because
    `_load_tycoon_project` unions manifest edges over these and needs to
    recount afterwards: a bare-name guess the manifest independently declares
    stops being a guess.
    """
    source = str(path)
    if not _is_motherduck(source):
        # MotherDuck catalogs are not filesystem paths, so the existence check
        # only applies to files.
        if not Path(source).exists():
            raise CatalogError(f"Database file not found: {source}")

    try:
        con = duckdb.connect(source, read_only=True)
    except duckdb.Error as exc:
        raise CatalogError(
            f"Could not open database '{source}' (it may be invalid or locked by a writer): {exc}"
        ) from exc

    try:
        try:
            tables, view_rows = _scan_catalog(con)
        except duckdb.Error as exc:
            raise CatalogError(f"Could not read catalog from '{source}': {exc}") from exc

        oid_to_key: dict[int, str] = {}
        for s, n, _size, oid in tables:
            oid_to_key[oid] = f"{s}.{n}"
        for s, n, _sql, oid in view_rows:
            oid_to_key[oid] = f"{s}.{n}"

        # oid_to_key is already scoped to this database, so dependency rows that
        # reference foreign objects resolve to None and are dropped there.
        dependency_edges = _fetch_dependency_edges(con, oid_to_key)
        try:
            columns_by_key = _scan_columns(con)
        except duckdb.Error:  # a missing function costs the facade, not the city
            columns_by_key = {}
    finally:
        con.close()

    objects: list[CatalogObject] = [
        CatalogObject(schema=s, name=n, kind="table", row_count=int(size or 0)) for s, n, size, _oid in tables
    ]
    view_sql: dict[str, str] = {}
    for s, n, sql, _oid in view_rows:
        objects.append(CatalogObject(schema=s, name=n, kind="view", row_count=0))
        view_sql[f"{s}.{n}"] = sql or ""

    # (schema, name) breaks the tie two colliding keys would otherwise leave to
    # the order DuckDB happened to list them in — see `_drop_duplicate_keys`.
    objects.sort(key=lambda o: (o.key, o.schema, o.name))

    # Before anything is keyed by `key`, make sure `key` identifies one object.
    objects, duplicate_note = drop_duplicate_keys(objects)
    if duplicate_note is not None:
        logger.warning("%s", duplicate_note)
        # A view that lost the collision must take its SQL with it, or the
        # table that won would be scanned as though it had a definition.
        surviving_views = {o.key for o in objects if o.kind == "view"}
        view_sql = {k: v for k, v in view_sql.items() if k in surviving_views}

    objects, cap_note = cap_catalog(objects, view_sql)

    kept = {o.key for o in objects}
    view_sql = {k: v for k, v in view_sql.items() if k in kept}
    columns_kept = {k: v for k, v in columns_by_key.items() if k in kept}

    # Column-level lineage from view SQL. Tables sqlglot traces that the
    # regex scan missed become table edges too — a street exists iff an edge
    # exists, and a proven column read is the strongest possible proof.
    view_lineage = derive_column_lineage({k: v for k, v in view_sql.items() if k in kept}, columns_kept)
    traced_edges = [Edge(src=e.src, dst=e.dst) for e in view_lineage.edges]
    edges, bare_pairs = _derive_edges(objects, view_sql, dependency_edges, traced_edges)

    notes: list[str] = []
    if duplicate_note is not None:
        notes.append(duplicate_note)
    if cap_note is not None:
        notes.append(cap_note)
    if view_lineage.unparsed:
        notes.append(f"no column lineage for {view_lineage.unparsed} views (unparseable SQL)")
    # A `.` inside a SCHEMA name makes `schema.name` ambiguous to split, and
    # `column_lineage` has to split it to tell sqlglot what the tables are. The
    # street survives (it is matched on the whole key); the skybridges do not.
    dotted = sum(1 for o in objects if "." in o.schema)
    if dotted:
        notes.append(
            f"{dotted} objects are in a schema whose name contains a '.'; their column-level lineage cannot be traced"
        )

    return PipelineContext(
        database_name=_database_name_for(source),
        objects=tuple(objects),
        edges=edges,
        notes=tuple(notes),
        columns_by_key=columns_kept,
        column_edges=view_lineage.edges,
        bare_name_edges=_count_bare(edges, bare_pairs),
    ), bare_pairs


def _count_bare(edges: tuple[Edge, ...], bare_pairs: frozenset[tuple[str, str]]) -> int:
    """How many SURVIVING edges are bare-name guesses.

    Counted against the final set, not against the scan: an edge the manifest
    also declares comes out tagged `manifest` and is no longer a guess, so a
    project whose dbt lineage confirms the scan must not be reported as
    hairball-shaped.
    """
    return sum(1 for e in edges if e.provenance == "view_sql" and (e.src, e.dst) in bare_pairs)


def _fetch_dependency_edges(con: duckdb.DuckDBPyConnection, oid_to_key: dict[int, str]) -> list[Edge]:
    """Best-effort lineage from DuckDB's internal dependency catalog.

    DuckDB does not track view-on-table dependencies by default, so this
    commonly returns no rows; that is normal, not an error. Any failure to
    query the function at all (e.g. unsupported on an older DuckDB build)
    is likewise treated as "no dependency-derived edges" rather than a
    CatalogError, since the SQL-text scan in ``_derive_edges`` is the
    primary source of lineage.
    """
    try:
        rows = con.execute("select objid, refobjid from duckdb_dependencies()").fetchall()
    except duckdb.Error:
        return []

    edges: list[Edge] = []
    for objid, refobjid in rows:
        dst = oid_to_key.get(objid)
        src = oid_to_key.get(refobjid)
        if src is None or dst is None or src == dst:
            continue
        edges.append(Edge(src=src, dst=dst, provenance="duckdb"))
    return edges


def _union_edges(*groups: list[Edge] | tuple[Edge, ...]) -> tuple[Edge, ...]:
    """Union by (src, dst), first group wins the provenance tag.

    Edges can only be present or absent, so union is correct; when several
    sources agree an edge exists, the caller's ordering — most authoritative
    first (manifest > duckdb > view_sql) — decides whose tag survives.
    """
    seen: set[tuple[str, str]] = set()
    deduped: list[Edge] = []
    for group in groups:
        for edge in group:
            pair = (edge.src, edge.dst)
            if pair not in seen:
                seen.add(pair)
                deduped.append(edge)
    deduped.sort(key=lambda e: (e.src, e.dst))
    return tuple(deduped)


def _derive_edges(
    objects: list[CatalogObject],
    view_sql: dict[str, str],
    dependency_edges: list[Edge],
    traced_edges: list[Edge] | None = None,
) -> tuple[tuple[Edge, ...], frozenset[tuple[str, str]]]:
    keep = {o.key for o in objects}
    kept_dependency = [e for e in dependency_edges if e.src != e.dst and e.src in keep and e.dst in keep]
    scan = scan_view_sql(objects, view_sql)
    return (
        _union_edges(kept_dependency, scan.edges, traced_edges or []),
        scan.bare_pairs,
    )


# --- The Phase E dispatcher: files stay exactly as they were; directories are
# --- tycoon projects and get the enriched path.


def _find_tycoon_root(path: Path) -> Path | None:
    """The nearest ancestor holding a tycoon.yml, if any. Used only to log a
    suggestion — a plain-file load is never silently enriched."""
    for parent in path.resolve().parents:
        if (parent / "tycoon.yml").is_file():
            return parent
    return None


def load_context(source: Path | str) -> PipelineContext:
    """Load a catalog from a file, an `md:` catalog, or a tycoon project dir.

    Explicit dispatch, no magic discovery: a `.duckdb` file argument takes the
    plain `load_catalog` path even when it happens to live inside a tycoon
    project (an info log suggests the root); a directory must hold a
    `tycoon.yml` or it is an error, not a guess.
    """
    text = str(source)
    if not _is_motherduck(text) and Path(text).is_dir():
        try:
            info = read_project_info(text)
        except ValueError as exc:
            raise CatalogError(str(exc)) from exc
        if info is None:
            raise CatalogError(
                f"'{text}' is a directory but not a tycoon project (no tycoon.yml); "
                "pass a DuckDB file or an md: catalog instead"
            )
        return _load_tycoon_project(info)

    ctx = load_catalog(source)
    if not _is_motherduck(text):
        root = _find_tycoon_root(Path(text))
        if root is not None:
            logger.info(
                "%s sits inside the tycoon project %s -- pass the project directory to get dbt lineage and run history",
                text,
                root,
            )
    return ctx


def _load_tycoon_project(info: TycoonProjectInfo) -> PipelineContext:
    """The warehouse catalog, enriched with manifest lineage and run history.

    Every rung of the degradation ladder lands in `notes` rather than in an
    exception: a tycoon project with no manifest, or a locked metadata
    database, still renders its structural city and says what is missing.

    Enrichment is dispatched through four phase helpers; each one returns a
    partial context (edges, notes, field assignments) so the orchestration
    stays short and readable.
    """
    ctx, bare_pairs = _load_base(info.warehouse_path)
    notes: list[str] = list(ctx.notes)

    index = read_manifest(info.manifest_path) if info.manifest_path else None

    if index is None:
        notes.append("no dbt manifest -- lineage from SQL scan only")

    # Phase A: manifest lineage + column lineage
    (edges, column_edges, nodes_by_key, tests_by_key, context_by_key, phase_a_notes) = _enrich_manifest(ctx, index)
    notes.extend(phase_a_notes)

    # Phase B: source freshness (always runs; skips silently when no artifacts)
    (freshness_by_key, phase_b_notes) = _enrich_freshness(ctx, index, info.sources_json_path)
    notes.extend(phase_b_notes)

    # Phase C: declared semantics (OSI)
    (semantic_relationships, ai_context_by_key, phase_c_notes) = _enrich_semantics(ctx, info.root)
    notes.extend(phase_c_notes)

    # Phase D: run history
    (runs, phase_d_notes) = _enrich_runs(ctx, index, info.metadata_db_path, nodes_by_key, tests_by_key)
    notes.extend(phase_d_notes)

    return dataclasses.replace(
        ctx,
        bare_name_edges=_count_bare(edges, bare_pairs),
        edges=edges,
        column_edges=column_edges,
        runs=runs,
        notes=tuple(notes),
        dbt_nodes_by_key=nodes_by_key,
        tests_by_key=tests_by_key,
        dbt_context_by_key=context_by_key,
        source_freshness_by_key=freshness_by_key,
        semantic_relationships=semantic_relationships,
        ai_context_by_key=ai_context_by_key,
    )


def _enrich_manifest(
    ctx: PipelineContext,
    index: dict | None,
) -> tuple[tuple[Edge, ...], tuple[ColumnEdge, ...], dict, dict, dict, list[str]]:
    """Manifest lineage + column lineage.

    Returns (edges, column_edges, nodes_by_key, tests_by_key, context_by_key, notes).
    """
    notes: list[str] = []
    edges = ctx.edges
    column_edges = ctx.column_edges
    nodes_by_key: dict = {}
    tests_by_key: dict = {}
    context_by_key: dict = {}

    if index is None:
        return edges, column_edges, nodes_by_key, tests_by_key, context_by_key, notes

    join = join_manifest(index, {obj.key for obj in ctx.objects})
    model_lineage = derive_column_lineage(join.sql_by_key, ctx.columns_by_key)
    traced = [Edge(src=e.src, dst=e.dst, provenance="manifest") for e in model_lineage.edges]
    column_edges = tuple(
        sorted(
            set(model_lineage.edges) | set(ctx.column_edges),
            key=lambda e: (e.dst, e.dst_col, e.src, e.src_col),
        )
    )
    untraceable = join.models_without_sql + model_lineage.unparsed
    if untraceable:
        notes.append(f"no column lineage for {untraceable} dbt models (unresolvable jinja or SQL)")
    edges = _union_edges(join.edges, traced, ctx.edges)
    notes.extend(join.notes)
    nodes_by_key = join.nodes_by_key
    tests_by_key = join.tests_by_key
    context_by_key = join.context_by_key

    return edges, column_edges, nodes_by_key, tests_by_key, context_by_key, notes


def _enrich_freshness(
    ctx: PipelineContext,
    index: dict | None,
    sources_json_path: Path | None,
) -> tuple[dict, list[str]]:
    """Source freshness. Returns (freshness_by_key, notes)."""
    notes: list[str] = []
    freshness_by_key: dict = {}

    canonical = canonical_keys({obj.key for obj in ctx.objects})
    freshness = read_source_freshness(sources_json_path) if sources_json_path else None
    if freshness and index is not None:
        for unique_id, verdict in freshness.items():
            key = canonical.get(index.key_of.get(unique_id, ""))
            if key is not None:
                freshness_by_key[key] = verdict
    elif index is not None and index.source_ids:
        notes.append("no source freshness snapshot (run `dbt source freshness`)")

    return freshness_by_key, notes


def _enrich_semantics(
    ctx: PipelineContext,
    root: Path,
) -> tuple[tuple, dict, list[str]]:
    """Declared semantics (OSI). Returns (semantic_relationships, ai_context_by_key, notes)."""
    notes: list[str] = []
    semantic_relationships: tuple = ()
    ai_context_by_key: dict = {}

    osi_path = discover_osi_path(root)
    if osi_path is None:
        notes.append("no semantic model -- joins from lineage only")
    elif not osi_path.is_file():
        notes.append("semantic model declared in tycoon.yml but not found")
    else:
        model = read_osi(osi_path)
        if model is None:
            notes.append("semantic model unreadable -- joins from lineage only")
        else:
            semantics = join_semantics(model, {obj.key for obj in ctx.objects})
            semantic_relationships = semantics.relationships
            ai_context_by_key = semantics.datasets_by_key
            notes.extend(semantics.notes)

    return semantic_relationships, ai_context_by_key, notes


def _enrich_runs(
    ctx: PipelineContext,
    index: dict | None,
    metadata_db_path: Path | None,
    nodes_by_key: dict,
    tests_by_key: dict,
) -> tuple[RunHistory | None, list[str]]:
    """Run history. Returns (runs, notes)."""
    notes: list[str] = []

    if metadata_db_path is None:
        notes.append("no run metadata (.tycoon/metadata.duckdb)")
        return None, notes

    runs = read_run_history(metadata_db_path)
    if runs is None:
        notes.append("run metadata unreadable (locked by a running tycoon command?)")
        return runs, notes

    notes.extend(runs.notes)
    if not runs.runs:
        notes.append("no run history yet")
    elif index is not None:
        notes.extend(_orphan_run_notes(runs, nodes_by_key, tests_by_key))

    return runs, notes


def _orphan_run_notes(runs, nodes_by_key: dict, tests_by_key: dict) -> list[str]:
    """Name the run-history rows that join onto nothing on this map.

    Run history is keyed by dbt `unique_id`, and every temporal signal — build
    age, build status, test status, usage, the whole budget block — reaches an
    object through the manifest's id. Rename a model, point the manifest at a
    different target, or read a metadata database from another project, and
    those signals go dark object by object with nothing to say why. The
    silence is the bug: a building with no build age is supposed to mean
    "never built", not "we mislaid the row".

    Only meaningful once a manifest joined; with no manifest at all *every*
    row is unmatched and the ladder already says why.
    """
    known = set(nodes_by_key.values())
    for refs in tests_by_key.values():
        known.update(ref.unique_id for ref in refs)
    orphans = [node for node in runs.node_results if node not in known]
    if not orphans:
        return []
    return [
        f"{len(orphans)} of {len(runs.node_results)} nodes in the run history do not "
        "match anything in this catalog (renamed or dropped models?)"
    ]
