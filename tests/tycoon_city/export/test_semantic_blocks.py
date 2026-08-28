"""`joins[]` and `objects[].semantic` on the wire.

Asserted on a **re-parsed document**, not on the dict handed to the serialiser,
for the reason the header of `test_city_json.py` gives: a document that
serialises wrongly passes every assertion made on the dict.

The wrong-axis hazard this file is written against: "`joins` is non-empty" is
true for the wrong pair, for the wrong key columns, and for the direction
reversed. Every assertion below names the pair AND which side is the "one".
"""

import json

import pytest

from tycoon_city.catalog.models import CatalogObject, Edge, PipelineContext
from tycoon_city.catalog.osi import AiContext, SemanticDataset, SemanticRelationship
from tycoon_city.export.city_json import city_document, dumps
from tycoon_city.sim.channels import DEFAULT_BINDINGS, apply_signals
from tycoon_city.sim.generator import generate_city
from tycoon_city.theme_data import load_theme_data, theme_dir


@pytest.fixture
def theme():
    return load_theme_data(theme_dir("default"))


def _obj(schema, name, rows=10):
    return CatalogObject(schema=schema, name=name, kind="table", row_count=rows)


OBJECTS = (
    _obj("staging", "stg_customers", 1_200),
    _obj("mart", "mart__revenue", 8_000),
    _obj("mart", "dim__customers", 1_200),
)
# stg_customers is a build input of mart__revenue: the ONE side flows INTO the
# many side, so the lineage edge runs the opposite way to the join. dim__
# customers is built from nothing here -- the dim-joined-but-never-built case.
EDGES = (Edge("staging.stg_customers", "mart.mart__revenue", provenance="manifest"),)

RELATIONSHIPS = (
    SemanticRelationship(
        name="revenue_to_staged_customer",
        many="mart.mart__revenue",
        one="staging.stg_customers",
        keys=(("customer_id", "id"),),
    ),
    SemanticRelationship(
        name="revenue_to_customer_status",
        many="mart.mart__revenue",
        one="mart.dim__customers",
        keys=(("customer_id", "id"), ("recognised_on", "created_at")),
    ),
)

DATASETS = {
    "mart.mart__revenue": SemanticDataset(
        name="revenue",
        relation="mart.mart__revenue",
        primary_key=("id",),
        unique_keys=(("customer_id", "recognised_on"),),
        ai_context=AiContext(
            instructions="One row per recognised revenue line.",
            synonyms=("revenue", "sales"),
            example_queries=("Revenue by month",),
        ),
    ),
    "mart.dim__customers": SemanticDataset(name="customer_dim", relation="mart.dim__customers", primary_key=("id",)),
}


def _document(ctx, theme) -> dict:
    city = generate_city(ctx, theme.style_rules)
    apply_signals(city, ctx, DEFAULT_BINDINGS)
    return json.loads(dumps(city_document(ctx, city, theme)))


@pytest.fixture
def declared(theme):
    ctx = PipelineContext(
        database_name="fx",
        objects=OBJECTS,
        edges=EDGES,
        semantic_relationships=RELATIONSHIPS,
        ai_context_by_key=DATASETS,
    )
    return _document(ctx, theme)


@pytest.fixture
def undeclared(theme):
    return _document(PipelineContext(database_name="fx", objects=OBJECTS, edges=EDGES), theme)


# ---------------------------------------------------------------------------
# joins[]
# ---------------------------------------------------------------------------


def test_a_join_names_its_pair_its_direction_and_its_key_columns(declared):
    joins = declared["joins"]
    assert len(joins) == 2, "precondition: both declared joins are on the map"

    simple = [j for j in joins if j["name"] == "revenue_to_staged_customer"]
    assert len(simple) == 1
    join = simple[0]
    # Direction, spelled out: revenue is the MANY side, the staged customer
    # dimension is the ONE side. Swapping these must fail here.
    assert join["many"] == "mart.mart__revenue"
    assert join["one"] == "staging.stg_customers"
    assert join["cardinality"] == "many_to_one"
    # [many-side column, one-side column] -- also an axis that can be swapped.
    assert join["keys"] == [["customer_id", "id"]]
    assert join["composite"] is False
    assert join["provenance"] == "declared"


def test_a_composite_join_keeps_every_pair_in_order_and_says_it_is_composite(declared):
    join = next(j for j in declared["joins"] if j["name"] == "revenue_to_customer_status")

    assert join["composite"] is True
    assert join["keys"] == [["customer_id", "id"], ["recognised_on", "created_at"]]
    assert join["many"] == "mart.mart__revenue"
    assert join["one"] == "mart.dim__customers"


def test_a_join_on_a_pair_that_also_has_lineage_names_that_edge(declared):
    """So the renderer marks the existing street instead of laying a parallel
    road. The edge is named in ITS OWN direction, which here is the reverse of
    the join's: the dimension is built into the fact."""
    join = next(j for j in declared["joins"] if j["name"] == "revenue_to_staged_customer")

    assert join["lineage_edge"] == ["staging.stg_customers", "mart.mart__revenue"]
    # The precondition that makes the claim mean something.
    pairs = {(e["src"], e["dst"]) for e in declared["edges"]}
    assert ("staging.stg_customers", "mart.mart__revenue") in pairs
    assert ("mart.mart__revenue", "staging.stg_customers") not in pairs


def test_a_join_with_no_lineage_is_null_there_and_the_edge_is_not_invented(declared):
    """The dim-joined-but-never-built case, and the whole argument for a
    separate `joins[]` array: this pair must gain a join and NOT an edge."""
    join = next(j for j in declared["joins"] if j["name"] == "revenue_to_customer_status")

    assert join["lineage_edge"] is None
    pairs = {(e["src"], e["dst"]) for e in declared["edges"]}
    assert ("mart.mart__revenue", "mart.dim__customers") not in pairs
    assert ("mart.dim__customers", "mart.mart__revenue") not in pairs


def test_declaring_joins_does_not_change_the_lineage_edges(declared, undeclared):
    """A client that reads `edges` and ignores `joins` must render exactly what
    it rendered before this key carried anything."""
    assert declared["edges"] == undeclared["edges"]


def test_a_join_to_an_object_off_the_map_is_not_emitted(theme):
    ctx = PipelineContext(
        database_name="fx",
        objects=OBJECTS,
        edges=EDGES,
        semantic_relationships=RELATIONSHIPS
        + (SemanticRelationship(name="ghost", many="mart.mart__revenue", one="nowhere.at_all", keys=(("a", "b"),)),),
    )

    document = _document(ctx, theme)

    # In emission order, which is (many, one, keys) -- not declaration order.
    assert [j["name"] for j in document["joins"]] == [
        "revenue_to_customer_status",
        "revenue_to_staged_customer",
    ]


def test_joins_are_sorted_byte_stably(declared):
    records = [(j["many"], j["one"], j["keys"]) for j in declared["joins"]]
    assert records == sorted(records)


# ---------------------------------------------------------------------------
# objects[].semantic
# ---------------------------------------------------------------------------


def test_the_semantic_block_carries_the_declared_name_keys_and_ai_context(declared):
    block = next(o for o in declared["objects"] if o["key"] == "mart.mart__revenue")["semantic"]

    assert block["name"] == "revenue", "the business name, not the table name"
    assert block["primary_key"] == ["id"]
    assert block["unique_keys"] == [["customer_id", "recognised_on"]]
    assert block["instructions"] == "One row per recognised revenue line."
    assert block["synonyms"] == ["revenue", "sales"]
    assert block["example_queries"] == ["Revenue by month"]


def test_a_declared_object_with_no_ai_context_is_a_block_not_a_null(declared):
    """Declared-but-unannotated and undeclared are different facts: one is a
    dataset somebody named, the other is a building nobody documented."""
    block = next(o for o in declared["objects"] if o["key"] == "mart.dim__customers")["semantic"]

    assert block is not None
    assert block["primary_key"] == ["id"]
    assert block["instructions"] is None
    assert block["synonyms"] == []


def test_an_undeclared_object_is_null(declared):
    block = next(o for o in declared["objects"] if o["key"] == "staging.stg_customers")["semantic"]

    assert block is None


def test_a_catalog_with_no_semantic_model_emits_the_empty_shapes(undeclared):
    """Most catalogs have no OSI file. They must keep emitting exactly what the
    reserved seam emitted: `[]` and null, never a partially-guessed shape."""
    assert undeclared["joins"] == []
    assert all(o["semantic"] is None for o in undeclared["objects"])
