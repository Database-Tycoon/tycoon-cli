from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .column_lineage import ColumnEdge
    from .dbt_manifest import NodeContext, SourceFreshness, TestRef
    from .osi import SemanticDataset, SemanticRelationship
    from .run_history import RunHistory

# Where an edge's knowledge comes from, most-authoritative first. "manifest"
# is declared lineage (dbt), "duckdb" is the engine's own dependency catalog,
# "view_sql" is the regex scan over view definitions. Precedence decides the
# *tag* when several sources agree an edge exists; existence is a union.
Provenance = Literal["manifest", "duckdb", "view_sql"]


def canonical_keys(keys: set[str] | frozenset[str]) -> dict[str, str]:
    """Lowercase catalog key -> the catalog's own spelling of it.

    The one law every external declaration joins onto the catalog by: match
    case-insensitively, **emit the catalog's spelling**. The warehouse, not a
    manifest or a semantic model, is the authority on what things are called,
    so a YAML that says `MART.DIM__CUSTOMERS` must still resolve to the object
    the rest of the document calls `mart.dim__customers` — otherwise the same
    building appears twice under two names. `dbt_manifest.join_manifest`
    applies the identical rule inline; this is where new joiners get it from
    rather than deriving a third variant.
    """
    return {key.lower(): key for key in keys}


@dataclass(frozen=True)
class CatalogObject:
    schema: str
    name: str
    kind: Literal["table", "view"]
    row_count: int

    @property
    def key(self) -> str:
        return f"{self.schema}.{self.name}"


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    provenance: Provenance = "view_sql"


@dataclass(frozen=True)
class PipelineContext:
    database_name: str
    objects: tuple[CatalogObject, ...]
    edges: tuple[Edge, ...]
    # All of these default so every hand-built context in the tests stays
    # valid. Run history and the manifest maps only exist when a tycoon
    # project supplied them; notes carry the degradation ladder's messages.
    runs: RunHistory | None = None
    notes: tuple[str, ...] = ()
    # Catalog key -> dbt model unique_id, and catalog key -> attached test
    # unique_ids, both in the catalog's own spelling. The temporal signals
    # (Phase F) join run history through these.
    dbt_nodes_by_key: dict[str, str] = dataclasses.field(default_factory=dict)
    tests_by_key: dict[str, tuple[TestRef, ...]] = dataclasses.field(default_factory=dict)
    # Declared semantics (description, materialization, tags, owner) and dbt's
    # own source-freshness SLA verdicts, both in catalog spelling.
    dbt_context_by_key: dict[str, NodeContext] = dataclasses.field(default_factory=dict)
    # Measured column structure: (name, type) in table order, from
    # duckdb_columns(). The schema-as-architecture features build on this.
    columns_by_key: dict[str, tuple[tuple[str, str], ...]] = dataclasses.field(default_factory=dict)
    source_freshness_by_key: dict[str, SourceFreshness] = dataclasses.field(default_factory=dict)
    # Column-level lineage (skybridges), traced by sqlglot from view SQL and
    # dbt model code. A subset of `edges` at the column grain.
    column_edges: tuple[ColumnEdge, ...] = ()
    # DECLARED semantics, from an Apache Ossie (OSI) file — never inferred from
    # SQL. Relationships are always many-to-one and carry both catalog keys in
    # the catalog's own spelling; `ai_context_by_key` holds the declaring
    # dataset (its keys plus its ai_context) per catalog key. Both empty when
    # no semantic model was found, which is the ordinary case.
    semantic_relationships: tuple[SemanticRelationship, ...] = ()
    ai_context_by_key: dict[str, SemanticDataset] = dataclasses.field(default_factory=dict)
    # How many surviving edges rest on an UNQUALIFIED table name alone (`from
    # orders`, not `from raw.orders`). Not a provenance — `provenance` is a
    # three-value client contract and these edges are `view_sql` like any
    # other — but a measure of how much of this catalog's lineage is inference
    # rather than fact. `scripts/readiness.py` reports the mix, because a
    # catalog whose streets are mostly bare-name matches is one step from the
    # hairball where a table called `status` wires itself to every view.
    bare_name_edges: int = 0

    @property
    def total_rows(self) -> int:
        return sum(o.row_count for o in self.objects)

    @property
    def object_count(self) -> int:
        return len(self.objects)
