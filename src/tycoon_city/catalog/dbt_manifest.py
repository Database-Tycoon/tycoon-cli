"""Read a dbt manifest and resolve its nodes onto catalog objects.

The crux is the join, and one rule is load-bearing: **the join key is
`f"{schema}.{alias}"`, matched case-insensitively, with the catalog's spelling
canonical — never the unique_id's last segment.** In dogfood the last segment
happens to match for all 40 models; that is luck, not contract. An `alias:`
override makes the table name differ from the model name, and two models named
`daily` in different schemas would collapse onto one key. The fixture factory
carries both shapes so the tests cannot pass on the lucky path.

Everything else degrades, never fails: a missing manifest returns None, a
mismatched target (dogfood's manifest says `dogfood_dev` while prod lives in
MotherDuck) is *measured* via `join_rate` and surfaced as a note, and sources
outside the catalog are dropped and counted.
"""

import dataclasses
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from .models import Edge

logger = logging.getLogger(__name__)

# The jinja subset worth resolving without a jinja engine: config blocks
# vanish, ref()/source() become relation names. Anything fancier (loops,
# var(), macros) leaves `{{`/`{%` behind and the model is counted out of
# column lineage rather than mis-parsed.
_JINJA_CONFIG = re.compile(r"\{\{\s*config\(.*?\)\s*\}\}", re.DOTALL)
_JINJA_REF = re.compile(r"\{\{\s*ref\(\s*'([^']+)'\s*(?:,\s*'([^']+)'\s*)?\)\s*\}\}")
_JINJA_SOURCE = re.compile(r"\{\{\s*source\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)\s*\}\}")
_JINJA_ANY = re.compile(r"\{[{%]")


def _resolve_model_sql(
    node: dict,
    model_relation: dict[str, str],
    source_relation: dict[tuple[str, str], str],
) -> str | None:
    """The model's SQL as something a SQL parser can read, or None.

    `compiled_code` is authoritative when the manifest carries it (a compile
    or run happened); otherwise `raw_code` with the resolvable jinja subset
    substituted. Residual jinja means None — better no bridges than bridges
    traced through mangled SQL.
    """
    compiled = node.get("compiled_code")
    if compiled:
        return compiled
    raw = node.get("raw_code")
    if not raw:
        return None
    sql = _JINJA_CONFIG.sub("", raw)
    sql = _JINJA_REF.sub(lambda m: model_relation.get(m.group(2) or m.group(1), m.group(0)), sql)
    sql = _JINJA_SOURCE.sub(lambda m: source_relation.get((m.group(1), m.group(2)), m.group(0)), sql)
    return None if _JINJA_ANY.search(sql) else sql


# Below this, the manifest probably describes a different warehouse (wrong
# target); the note names the state instead of letting lineage look broken.
LOW_JOIN_RATE = 0.5


@dataclass(frozen=True)
class TestRef:
    """A declared test: its unique_id, human name, and column (None for
    relation-level and singular tests)."""

    unique_id: str
    name: str
    column: str | None


@dataclass(frozen=True)
class NodeContext:
    """What dbt declares about a node beyond lineage: the semantic layer the
    inspector surfaces. All optional in real manifests; empty strings and
    tuples mean 'not documented', which the UI renders as absent."""

    description: str
    materialized: str
    tags: tuple[str, ...]
    owner: str | None
    column_docs: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclass(frozen=True)
class ManifestIndex:
    """The manifest reduced to what the city needs, keyed for joining.

    `key_of` maps unique_id -> lowercase "schema.alias" for models and
    sources. `tests_by_key` attaches TestRefs to the lowercase key of the node
    they test (via `attached_node`, falling back to a sole `depends_on` entry —
    real singular tests carry `attached_node: None`).
    """

    key_of: dict[str, str]
    model_dependencies: dict[str, tuple[str, ...]]  # model unique_id -> dep unique_ids
    tests_by_key: dict[str, tuple[TestRef, ...]]
    source_ids: frozenset[str]
    context_of: dict[str, NodeContext]  # unique_id -> declared context
    # unique_id -> parseable SQL (compiled, or raw with ref/source resolved);
    # models whose jinja could not be resolved are counted, not guessed at.
    sql_of: dict[str, str] = dataclasses.field(default_factory=dict)
    models_without_sql: int = 0


def read_manifest(path: Path) -> ManifestIndex | None:
    """Parse and index a manifest; None when it is missing or unreadable.

    Unreadable degrades to None (with a log line) rather than raising: the
    manifest is an enrichment, and a corrupt one should cost its features, not
    the city.
    """
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("could not read dbt manifest %s: %s", path, exc)
        return None

    key_of: dict[str, str] = {}
    model_dependencies: dict[str, tuple[str, ...]] = {}
    tests: list[tuple[str, TestRef]] = []  # (target unique_id, ref)
    context_of: dict[str, NodeContext] = {}
    model_nodes: dict[str, dict] = {}
    model_relation: dict[str, str] = {}  # model name -> "schema.alias", for ref()

    for unique_id, node in (data.get("nodes") or {}).items():
        kind = node.get("resource_type")
        if kind == "model":
            schema = node.get("schema")
            alias = node.get("alias") or node.get("name")
            if not schema or not alias:
                continue
            key_of[unique_id] = f"{schema}.{alias}".lower()
            deps = tuple((node.get("depends_on") or {}).get("nodes") or ())
            model_dependencies[unique_id] = deps
            context_of[unique_id] = _node_context(node)
            model_nodes[unique_id] = node
            if node.get("name"):
                model_relation[node["name"]] = f"{schema}.{alias}"
        elif kind == "test":
            target = node.get("attached_node")
            if not target:
                deps = [
                    d for d in (node.get("depends_on") or {}).get("nodes") or [] if d.startswith(("model.", "source."))
                ]
                # Only an unambiguous fallback: a test depending on two nodes
                # attaches to neither rather than to a guess.
                target = deps[0] if len(deps) == 1 else None
            if target:
                tests.append(
                    (
                        target,
                        TestRef(
                            unique_id=unique_id,
                            name=node.get("name") or unique_id.rsplit(".", 1)[-1],
                            column=node.get("column_name"),
                        ),
                    )
                )

    source_ids: set[str] = set()
    source_relation: dict[tuple[str, str], str] = {}  # (source_name, name) -> relation
    for unique_id, source in (data.get("sources") or {}).items():
        schema = source.get("schema")
        name = source.get("identifier") or source.get("name")
        if not schema or not name:
            continue
        key_of[unique_id] = f"{schema}.{name}".lower()
        source_ids.add(unique_id)
        context_of[unique_id] = _node_context(source)
        if source.get("source_name") and source.get("name"):
            source_relation[(source["source_name"], source["name"])] = f"{schema}.{name}"

    sql_of: dict[str, str] = {}
    models_without_sql = 0
    for unique_id, node in model_nodes.items():
        sql = _resolve_model_sql(node, model_relation, source_relation)
        if sql is None:
            models_without_sql += 1
        else:
            sql_of[unique_id] = sql

    tests_by_key: dict[str, list[TestRef]] = {}
    for target, ref in tests:
        key = key_of.get(target)
        if key is not None:
            tests_by_key.setdefault(key, []).append(ref)

    return ManifestIndex(
        key_of=key_of,
        model_dependencies=model_dependencies,
        tests_by_key={k: tuple(v) for k, v in tests_by_key.items()},
        source_ids=frozenset(source_ids),
        context_of=context_of,
        sql_of=sql_of,
        models_without_sql=models_without_sql,
    )


def _node_context(node: dict) -> NodeContext:
    meta = node.get("meta") or (node.get("config") or {}).get("meta") or {}
    docs = {
        name: (col.get("description") or "").strip()
        for name, col in (node.get("columns") or {}).items()
        if isinstance(col, dict) and (col.get("description") or "").strip()
    }
    return NodeContext(
        description=(node.get("description") or "").strip(),
        materialized=((node.get("config") or {}).get("materialized") or "").strip(),
        tags=tuple(node.get("tags") or ()),
        owner=meta.get("owner"),
        column_docs=docs,
    )


@dataclass(frozen=True)
class ManifestJoin:
    edges: tuple[Edge, ...]  # in the catalog's own spelling, provenance="manifest"
    join_rate: float  # matched models / manifest models
    matched_models: int
    total_models: int
    sources_outside: int  # manifest sources with no catalog object
    notes: tuple[str, ...]
    # Catalog key (canonical spelling) -> model unique_id / test unique_ids.
    # The temporal signals join run history through these.
    nodes_by_key: dict[str, str] = dataclasses.field(default_factory=dict)
    tests_by_key: dict[str, tuple[TestRef, ...]] = dataclasses.field(default_factory=dict)
    context_by_key: dict[str, NodeContext] = dataclasses.field(default_factory=dict)
    # Catalog key -> parseable model SQL, for column-level lineage.
    sql_by_key: dict[str, str] = dataclasses.field(default_factory=dict)
    models_without_sql: int = 0


def join_manifest(index: ManifestIndex, catalog_keys: set[str]) -> ManifestJoin:
    """Resolve the manifest onto a catalog's object keys.

    `catalog_keys` are the catalog's canonical spellings; matching is
    case-insensitive but every emitted edge uses the catalog's spelling — the
    warehouse, not the manifest, is the authority on what things are called.
    """
    canonical = {key.lower(): key for key in catalog_keys}

    model_ids = set(index.model_dependencies)
    matched = {unique_id for unique_id in model_ids if index.key_of.get(unique_id, "") in canonical}
    total = len(model_ids)
    rate = (len(matched) / total) if total else 0.0

    edges: list[Edge] = []
    for model_id, deps in index.model_dependencies.items():
        dst = canonical.get(index.key_of.get(model_id, ""))
        if dst is None:
            continue
        for dep_id in deps:
            src = canonical.get(index.key_of.get(dep_id, ""))
            if src is not None and src != dst:
                edges.append(Edge(src=src, dst=dst, provenance="manifest"))

    sources_outside = sum(1 for sid in index.source_ids if index.key_of.get(sid, "") not in canonical)

    nodes_by_key = {
        canonical[index.key_of[model_id]]: model_id
        for model_id in model_ids
        if index.key_of.get(model_id, "") in canonical
    }
    tests_by_key = {canonical[low_key]: refs for low_key, refs in index.tests_by_key.items() if low_key in canonical}
    context_by_key = {
        canonical[low_key]: context
        for unique_id, context in index.context_of.items()
        if (low_key := index.key_of.get(unique_id, "")) in canonical
    }
    sql_by_key = {
        canonical[low_key]: sql
        for unique_id, sql in index.sql_of.items()
        if (low_key := index.key_of.get(unique_id, "")) in canonical
    }

    notes: list[str] = []
    if total and rate < LOW_JOIN_RATE:
        notes.append(f"dbt manifest matches {rate:.0%} of catalog — manifest target may not match this warehouse")
    if sources_outside:
        notes.append(f"{sources_outside} upstream sources outside this catalog")

    return ManifestJoin(
        edges=tuple(edges),
        join_rate=rate,
        matched_models=len(matched),
        total_models=total,
        sources_outside=sources_outside,
        notes=tuple(notes),
        nodes_by_key=nodes_by_key,
        tests_by_key=tests_by_key,
        context_by_key=context_by_key,
        sql_by_key=sql_by_key,
        models_without_sql=index.models_without_sql,
    )


@dataclass(frozen=True)
class SourceFreshness:
    """One row of `target/sources.json`: dbt's own SLA verdict for a source."""

    status: str  # pass / warn / error / runtime error
    max_loaded_at: str | None  # ISO timestamp string, parsed by the caller


def read_source_freshness(path: Path) -> dict[str, SourceFreshness] | None:
    """`dbt source freshness` verdicts by source unique_id, or None when the
    artifact is missing/unreadable — many projects never run the command, so
    absence is ordinary, not an error."""
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return None
    results = {}
    for row in data.get("results") or []:
        unique_id = row.get("unique_id")
        status = row.get("status")
        if unique_id and status:
            results[unique_id] = SourceFreshness(status=status, max_loaded_at=row.get("max_loaded_at"))
    return results
