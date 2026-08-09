"""Read an Apache Ossie (OSI) semantic model and resolve it onto catalog objects.

**Apache Ossie** is the Open Semantic Interchange spec (Apache Incubator since
June 2026; Snowflake, dbt Labs, Salesforce, Preset et al.): vendor-neutral YAML
declaring **Datasets** (business entities with fields and keys),
**Relationships** (FK joins between datasets, *always* many-to-one, simple or
composite), **Metrics**, and `ai_context` annotations at every level.

This reader is built to the same discipline as `dbt_manifest`, and for the same
reason — the file is an ENRICHMENT, so a broken one must cost its own features
and nothing else:

* a missing file is a note, never an error;
* a malformed section degrades to absence **with a note**, rather than taking
  the load down;
* unknown keys are never looked at, so spec drift is tolerated by construction;
* declarations that do not match a catalog object are **counted into a note** —
  a hand-written YAML with one typo has to say so out loud, because a join
  silently missing from the city is indistinguishable from a join nobody wrote.

Everything this module produces is **declared** provenance. Nothing here reads
SQL or infers a relationship from a query: a join guessed from SQL is a
different and weaker fact, and it already exists in this codebase as lineage.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .models import canonical_keys
from .tycoon_project import TYCOON_FILE, _interpolate

logger = logging.getLogger(__name__)

# Project-root convention, in preference order. Checked only when `tycoon.yml`
# does not point somewhere explicitly.
OSI_FILENAMES = ("semantic.yml", "semantic.yaml", "osi.yml", "osi.yaml")

# The `tycoon.yml` key that overrides the convention, read the same way
# `tycoon_project` reads everything else there: only the key we need, so an
# unknown neighbouring key is never even looked at.
TYCOON_SEMANTIC_KEY = "semantic_model"

# The spec's invariant. An OSI Relationship is ALWAYS many-to-one, so a file
# that declares anything else is from a dialect this version does not model:
# it is dropped and counted, never flipped around into the shape we wanted.
MANY_TO_ONE = "many_to_one"


# --------------------------------------------------------------------------
# Tolerant scalar readers. Every one of these turns "not the shape I expected"
# into absence, so no branch below has to guard its own input.
# --------------------------------------------------------------------------


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _strings(value: object) -> tuple[str, ...]:
    """A YAML list of strings. A bare string is a one-item list (people write
    `synonyms: revenue`); anything else is dropped rather than stringified into
    nonsense like `"{'a': 1}"`."""
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if not isinstance(value, list):
        return ()
    return tuple(text for item in value if (text := _text(item)))


@dataclass(frozen=True)
class AiContext:
    """OSI's `ai_context`, wherever it appears — model, dataset, field,
    relationship, metric. All-empty means undeclared, and the city renders
    that as absence, never as blank documentation."""

    instructions: str = ""
    synonyms: tuple[str, ...] = ()
    example_queries: tuple[str, ...] = ()

    @property
    def declared(self) -> bool:
        return bool(self.instructions or self.synonyms or self.example_queries)


EMPTY_CONTEXT = AiContext()


def _ai_context(node: object) -> AiContext:
    if not isinstance(node, dict):
        return EMPTY_CONTEXT
    block = node.get("ai_context")
    if not isinstance(block, dict):
        return EMPTY_CONTEXT
    return AiContext(
        instructions=_text(block.get("instructions")),
        synonyms=_strings(block.get("synonyms")),
        example_queries=_strings(block.get("example_queries")),
    )


# --------------------------------------------------------------------------
# The parsed model
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SemanticDataset:
    """One OSI Dataset, plus the physical relation it binds itself to.

    `relation` is what joins onto the catalog: `schema.table` as declared, in
    the file's own spelling. An unqualified name stays unqualified and simply
    fails to match — resolving a bare `orders` against whichever schema happens
    to hold one would be a guess, and this module does not guess.
    """

    name: str
    relation: str
    primary_key: tuple[str, ...] = ()
    unique_keys: tuple[tuple[str, ...], ...] = ()
    ai_context: AiContext = EMPTY_CONTEXT
    # Field name -> its own ai_context. Parsed now (the spec puts annotations at
    # every level); the window-signage phase is what will render it.
    field_context: dict[str, AiContext] = field(default_factory=dict)


@dataclass(frozen=True)
class DeclaredRelationship:
    """A relationship as WRITTEN: endpoints are dataset names, not catalog keys.

    `many`/`one` rather than `from`/`to` because the direction is the fact
    worth keeping: `to` is the "one" side, the dimension the join points at.
    """

    name: str
    many: str
    one: str
    keys: tuple[tuple[str, str], ...]  # (many-side column, one-side column)
    ai_context: AiContext = EMPTY_CONTEXT


@dataclass(frozen=True)
class SemanticMetric:
    """A model-level measure. Parsed and counted; the landmark that renders it
    is a later phase, so its absence from the city gets a note."""

    name: str
    datasets: tuple[str, ...]
    ai_context: AiContext = EMPTY_CONTEXT


@dataclass(frozen=True)
class OsiModel:
    datasets: tuple[SemanticDataset, ...] = ()
    relationships: tuple[DeclaredRelationship, ...] = ()
    metrics: tuple[SemanticMetric, ...] = ()
    ai_context: AiContext = EMPTY_CONTEXT  # model level
    notes: tuple[str, ...] = ()


def _key_pairs(value: object) -> tuple[tuple[str, str], ...]:
    """A relationship's key columns as (many side, one side) pairs.

    Three spellings, all legal: a mapping (`from`/`to`, or `many`/`one`, or
    `column`/`references`), a two-item list, and a bare string when both sides
    spell the column the same way. **A composite key is simply more than one
    pair** — the spec has no separate syntax for it, and neither does this.
    """
    if isinstance(value, (str, dict)):
        value = [value]
    if not isinstance(value, list):
        return ()
    pairs: list[tuple[str, str]] = []
    for item in value:
        if isinstance(item, str):
            if name := _text(item):
                pairs.append((name, name))
        elif isinstance(item, dict):
            left = _text(item.get("from")) or _text(item.get("many")) or _text(item.get("column"))
            right = _text(item.get("to")) or _text(item.get("one")) or _text(item.get("references"))
            if left and right:
                pairs.append((left, right))
        elif isinstance(item, list) and len(item) == 2:
            left, right = _text(item[0]), _text(item[1])
            if left and right:
                pairs.append((left, right))
    return tuple(pairs)


def _read_dataset(node: object) -> SemanticDataset | None:
    if not isinstance(node, dict):
        return None
    name = _text(node.get("name"))
    if not name:
        return None
    schema = _text(node.get("schema"))
    table = _text(node.get("table")) or _text(node.get("identifier")) or name
    unique_keys = tuple(
        keys
        for item in (node.get("unique_keys") if isinstance(node.get("unique_keys"), list) else [])
        if (keys := _strings(item))
    )
    fields = node.get("fields") if isinstance(node.get("fields"), list) else []
    field_context = {
        field_name: context
        for entry in fields
        if isinstance(entry, dict) and (field_name := _text(entry.get("name")))
        if (context := _ai_context(entry)).declared
    }
    return SemanticDataset(
        name=name,
        relation=f"{schema}.{table}" if schema else table,
        primary_key=_strings(node.get("primary_key")),
        unique_keys=unique_keys,
        ai_context=_ai_context(node),
        field_context=field_context,
    )


def _read_metric(node: object) -> SemanticMetric | None:
    if not isinstance(node, dict):
        return None
    name = _text(node.get("name"))
    if not name:
        return None
    datasets = _strings(node.get("datasets")) or _strings(node.get("dataset"))
    return SemanticMetric(name=name, datasets=datasets, ai_context=_ai_context(node))


def _section(data: dict, name: str, notes: list[str]) -> list:
    """One top-level list section. Present-but-not-a-list degrades to absence
    and says so: the other sections still load."""
    value = data.get(name)
    if value is None:
        return []
    if not isinstance(value, list):
        notes.append(f"semantic model: `{name}` is not a list -- section ignored")
        return []
    return value


def read_osi(path: Path) -> OsiModel | None:
    """Parse a semantic model; None when it is missing, unreadable, or not YAML
    mapping at the top. Unreadable degrades to None with a log line rather than
    raising, exactly as `read_manifest` does."""
    try:
        data = yaml.safe_load(Path(path).read_text())
    except (OSError, yaml.YAMLError) as exc:
        logger.warning("could not read semantic model %s: %s", path, exc)
        return None
    if not isinstance(data, dict):
        logger.warning("semantic model %s is not a mapping at the top level", path)
        return None

    notes: list[str] = []

    datasets: list[SemanticDataset] = []
    unreadable_datasets = 0
    for node in _section(data, "datasets", notes):
        parsed = _read_dataset(node)
        if parsed is None:
            unreadable_datasets += 1
        else:
            datasets.append(parsed)
    if unreadable_datasets:
        notes.append(f"{unreadable_datasets} declared datasets were unreadable and skipped")

    relationships: list[DeclaredRelationship] = []
    unreadable_relationships = 0
    other_cardinality = 0
    for node in _section(data, "relationships", notes):
        if not isinstance(node, dict):
            unreadable_relationships += 1
            continue
        declared = _text(node.get("type")) or _text(node.get("cardinality"))
        if declared and declared.lower().replace("-", "_") != MANY_TO_ONE:
            other_cardinality += 1
            continue
        many = _text(node.get("from")) or _text(node.get("many"))
        one = _text(node.get("to")) or _text(node.get("one"))
        keys = _key_pairs(node.get("keys") if "keys" in node else node.get("join_keys"))
        if not many or not one or not keys:
            unreadable_relationships += 1
            continue
        relationships.append(
            DeclaredRelationship(
                name=_text(node.get("name")) or f"{many}_to_{one}",
                many=many,
                one=one,
                keys=keys,
                ai_context=_ai_context(node),
            )
        )
    if unreadable_relationships:
        notes.append(f"{unreadable_relationships} declared joins were unreadable and skipped")
    if other_cardinality:
        # Not flipped into many-to-one: the spec's invariant is what makes the
        # direction meaningful, and inverting someone's declaration to fit is
        # exactly the guess this module refuses to make.
        notes.append(f"{other_cardinality} declared joins are not many-to-one and are not modelled")

    metrics: list[SemanticMetric] = []
    for node in _section(data, "metrics", notes):
        parsed = _read_metric(node)
        if parsed is not None:
            metrics.append(parsed)

    return OsiModel(
        datasets=tuple(datasets),
        relationships=tuple(relationships),
        metrics=tuple(metrics),
        ai_context=_ai_context(data),
        notes=tuple(notes),
    )


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------


def discover_osi_path(root: Path) -> Path | None:
    """Where a project's semantic model lives: the `tycoon.yml` key first, then
    the project-root convention.

    Returns the **declared** path even when it does not exist, so a broken
    pointer can be named as a broken pointer instead of degrading into the
    indistinguishable "no semantic model". None means nothing was declared and
    no conventional file is there.
    """
    root = Path(root)
    config = root / TYCOON_FILE
    if config.is_file():
        try:
            data = yaml.safe_load(config.read_text())
        except yaml.YAMLError:
            data = None
        if isinstance(data, dict) and (declared := _text(data.get(TYCOON_SEMANTIC_KEY))):
            return root / _interpolate(declared)
    for name in OSI_FILENAMES:
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


# --------------------------------------------------------------------------
# The join onto catalog keys
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SemanticRelationship:
    """A relationship RESOLVED onto catalog objects, in catalog spelling.

    Which endpoint is which is the whole point. OSI relationships are always
    many-to-one, so `one` is the dimension the join points at; a record that
    knew only the pair would be ambiguous the moment anything rendered
    direction signage.
    """

    name: str
    many: str
    one: str
    keys: tuple[tuple[str, str], ...]
    ai_context: AiContext = EMPTY_CONTEXT

    @property
    def composite(self) -> bool:
        return len(self.keys) > 1


@dataclass(frozen=True)
class SemanticJoin:
    relationships: tuple[SemanticRelationship, ...]
    datasets_by_key: dict[str, SemanticDataset]
    matched_datasets: int
    total_datasets: int
    matched_relationships: int
    total_relationships: int
    notes: tuple[str, ...]


def join_semantics(model: OsiModel, catalog_keys: set[str]) -> SemanticJoin:
    """Resolve declared datasets and relationships onto a catalog's object keys.

    Matching is case-insensitive with the **catalog's** spelling canonical (see
    `models.canonical_keys`). Declarations that match nothing are dropped and
    counted — never silently — because the one thing a hand-written YAML gets
    wrong is a name, and a typo that costs a road must be visible as a typo.
    """
    canonical = canonical_keys(catalog_keys)

    key_of: dict[str, str] = {}  # dataset name -> catalog key
    datasets_by_key: dict[str, SemanticDataset] = {}
    matched_datasets = 0
    for dataset in model.datasets:
        key = canonical.get(dataset.relation.lower())
        if key is None:
            continue
        matched_datasets += 1
        key_of[dataset.name] = key
        datasets_by_key[key] = dataset

    def _endpoint(name: str) -> str | None:
        # A dataset name first; failing that, a relationship may name the
        # physical relation directly. Both are exact matches, not guesses.
        return key_of.get(name) or canonical.get(name.lower())

    resolved: list[SemanticRelationship] = []
    for rel in model.relationships:
        many, one = _endpoint(rel.many), _endpoint(rel.one)
        if many is None or one is None:
            continue
        resolved.append(
            SemanticRelationship(name=rel.name, many=many, one=one, keys=rel.keys, ai_context=rel.ai_context)
        )

    notes: list[str] = list(model.notes)
    unmatched_datasets = len(model.datasets) - matched_datasets
    if unmatched_datasets:
        notes.append(f"{unmatched_datasets} of {len(model.datasets)} declared datasets did not match a catalog object")
    unmatched_joins = len(model.relationships) - len(resolved)
    if unmatched_joins:
        notes.append(f"{unmatched_joins} of {len(model.relationships)} declared joins did not match a catalog object")
    if model.metrics:
        notes.append(f"{len(model.metrics)} declared metrics (landmarks not yet rendered)")

    return SemanticJoin(
        relationships=tuple(resolved),
        datasets_by_key=datasets_by_key,
        matched_datasets=matched_datasets,
        total_datasets=len(model.datasets),
        matched_relationships=len(resolved),
        total_relationships=len(model.relationships),
        notes=tuple(notes),
    )
