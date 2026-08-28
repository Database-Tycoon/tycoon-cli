"""The Apache Ossie (OSI) reader and its join onto catalog objects.

Two habits here are deliberate, and both are reactions to this repo's dominant
defect — a test asserting the right value on an axis that cannot fail:

* Nothing asserts merely that relationships are non-empty. A count passes on
  the wrong pair and on the wrong DIRECTION, and direction is the one fact an
  OSI relationship exists to carry (many-to-one is the spec's invariant). Every
  test below names which object is the "many" and which is the "one".
* Fixture preconditions are asserted. A YAML whose datasets silently stopped
  matching the catalog would make several of these tests vacuously green.
"""

from pathlib import Path

import pytest

from tests.fixtures.tycoon_factory import make_tycoon_project
from tycoon_city.catalog.loader import load_context
from tycoon_city.catalog.osi import (
    OSI_FILENAMES,
    discover_osi_path,
    join_semantics,
    read_osi,
)

REPO = Path(__file__).resolve().parents[2]
SHIPPED_DEMO_MODEL = REPO / "src" / "tycoon_city" / "demo" / "semantic.yml"

# The factory warehouse holds staging.stg_orders, marts.fct_revenue (an ALIAS
# override -- the model is `fct_revenue_model`), staging.daily and marts.daily.
GOOD_MODEL = """
osi_version: "0.1"
datasets:
  - name: orders
    schema: staging
    table: stg_orders
    primary_key: [id]
    ai_context:
      synonyms: [orders, order lines]
      instructions: One row per order.
  - name: revenue
    schema: marts
    table: fct_revenue
    primary_key: [id]
relationships:
  - name: revenue_to_orders
    type: many_to_one
    from: revenue
    to: orders
    keys:
      - from: id
        to: id
"""


def _project(tmp_path, model_yaml: str | None, filename: str = "semantic.yml") -> Path:
    root = make_tycoon_project(tmp_path / "fx")
    if model_yaml is not None:
        path = root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(model_yaml)
    return root


# ---------------------------------------------------------------------------
# Absence stays named
# ---------------------------------------------------------------------------


def test_a_missing_semantic_model_is_a_note_never_an_error(tmp_path):
    root = _project(tmp_path, None)

    ctx = load_context(root)

    assert ctx.semantic_relationships == ()
    assert ctx.ai_context_by_key == {}
    assert "no semantic model -- joins from lineage only" in ctx.notes


def test_nothing_is_inferred_from_sql(tmp_path):
    """Provenance discipline: a project with real lineage and no OSI file
    declares no joins. A join guessed from SQL is a weaker fact that already
    exists as lineage, and this module must never manufacture the stronger one."""
    root = _project(tmp_path, None)

    ctx = load_context(root)

    assert ctx.edges, "precondition: the factory project has manifest lineage"
    assert ctx.semantic_relationships == ()


def test_corrupt_yaml_degrades_like_a_missing_model(tmp_path):
    root = _project(tmp_path, "datasets: [\n  - name: broken\n")

    ctx = load_context(root)

    assert ctx.semantic_relationships == ()
    assert "semantic model unreadable -- joins from lineage only" in ctx.notes


def test_a_malformed_section_degrades_to_absence_and_the_rest_still_loads(tmp_path):
    """`relationships` written as a mapping costs the joins and nothing else --
    the datasets in the same file still resolve."""
    model = GOOD_MODEL.replace(
        "relationships:\n  - name: revenue_to_orders",
        "relationships:\n  revenue_to_orders:",
    ).replace("    type: many_to_one\n", "")

    ctx = load_context(_project(tmp_path, model))

    assert ctx.semantic_relationships == ()
    assert "staging.stg_orders" in ctx.ai_context_by_key, "datasets must survive"
    assert any("`relationships` is not a list" in note for note in ctx.notes), ctx.notes


def test_unknown_keys_are_ignored_forward_compatibly(tmp_path):
    model = GOOD_MODEL + "\nverticals:\n  - name: from_a_later_spec\nowner: someone\n"

    ctx = load_context(_project(tmp_path, model))

    assert [(r.many, r.one) for r in ctx.semantic_relationships] == [("marts.fct_revenue", "staging.stg_orders")]


# ---------------------------------------------------------------------------
# The join: which objects, and which way round
# ---------------------------------------------------------------------------


def test_a_declared_join_resolves_onto_the_named_pair_in_the_declared_direction(tmp_path):
    ctx = load_context(_project(tmp_path, GOOD_MODEL))

    keys = {obj.key for obj in ctx.objects}
    assert {"marts.fct_revenue", "staging.stg_orders"} <= keys, "precondition: both objects exist"

    assert len(ctx.semantic_relationships) == 1
    rel = ctx.semantic_relationships[0]
    # The whole point: `revenue` is the MANY side and `orders` is the ONE side,
    # exactly as the YAML declared it. Swapping them must fail here.
    assert rel.many == "marts.fct_revenue"
    assert rel.one == "staging.stg_orders"
    assert rel.name == "revenue_to_orders"
    assert rel.keys == (("id", "id"),)
    assert rel.composite is False


def test_the_alias_override_is_joined_on_the_table_name_not_the_model_name(tmp_path):
    """`marts.fct_revenue` is the table; `fct_revenue_model` is the dbt model.
    An OSI file binds to the RELATION, so a join through the model name would
    resolve to nothing."""
    ctx = load_context(_project(tmp_path, GOOD_MODEL))

    assert ctx.semantic_relationships[0].many == "marts.fct_revenue"
    assert "marts.fct_revenue_model" not in {obj.key for obj in ctx.objects}


def test_catalog_spelling_is_canonical(tmp_path):
    """The declaration shouts; the catalog decides how the object is spelled.
    Anything else puts the same building on the map twice under two names."""
    ctx = load_context(_project(tmp_path, GOOD_MODEL.replace("schema: marts", "schema: MARTS")))

    rel = ctx.semantic_relationships[0]
    assert rel.many == "marts.fct_revenue"
    assert set(ctx.ai_context_by_key) == {"marts.fct_revenue", "staging.stg_orders"}


def test_a_mixed_case_catalog_matches_and_keeps_its_own_spelling(tmp_path):
    """The half of the canonical-spelling law that a lowercase warehouse cannot
    test. DuckDB will happily hold quoted, mixed-case identifiers; the
    declaration here is lowercase, so a case-SENSITIVE lookup drops both joins
    silently, and echoing the declaration's spelling back would put the same
    building on the map under a second name. (Measured: without this test, a
    mutant replacing `canonical_keys` with an exact-match dict survives the
    whole suite -- every factory object is already lowercase.)"""
    model = read_osi(_project(tmp_path, GOOD_MODEL) / "semantic.yml")
    assert model is not None

    joined = join_semantics(model, {"Marts.Fct_Revenue", "Staging.Stg_Orders"})

    assert [(rel.many, rel.one) for rel in joined.relationships] == [("Marts.Fct_Revenue", "Staging.Stg_Orders")]
    assert set(joined.datasets_by_key) == {"Marts.Fct_Revenue", "Staging.Stg_Orders"}
    assert not [note for note in joined.notes if "did not match" in note], joined.notes


def test_composite_keys_keep_every_pair_in_declaration_order(tmp_path):
    model = GOOD_MODEL.replace(
        "      - from: id\n        to: id\n",
        "      - from: id\n        to: id\n      - from: name\n        to: name\n",
    )

    ctx = load_context(_project(tmp_path, model))

    rel = ctx.semantic_relationships[0]
    assert rel.keys == (("id", "id"), ("name", "name"))
    assert rel.composite is True


def test_key_pairs_read_the_three_legal_spellings(tmp_path):
    """A mapping, a two-item list, and a bare string (same column both sides).
    Composite is simply more than one pair -- no separate syntax."""
    model = GOOD_MODEL.replace(
        "      - from: id\n        to: id\n",
        "      - {many: id, one: other_id}\n      - [name, other_name]\n      - amount\n",
    )

    ctx = load_context(_project(tmp_path, model))

    assert ctx.semantic_relationships[0].keys == (
        ("id", "other_id"),
        ("name", "other_name"),
        ("amount", "amount"),
    )


def test_a_join_that_is_not_many_to_one_is_dropped_and_counted_not_flipped(tmp_path):
    """many-to-one is the spec's invariant. Inverting someone's one-to-many
    declaration to make it fit would silently reverse the direction signage."""
    model = GOOD_MODEL.replace("type: many_to_one", "type: one_to_many")

    ctx = load_context(_project(tmp_path, model))

    assert ctx.semantic_relationships == ()
    assert any("not many-to-one and are not modelled" in note for note in ctx.notes), ctx.notes


# ---------------------------------------------------------------------------
# The typo case: unmatched declarations are counted, never dropped in silence
# ---------------------------------------------------------------------------


TYPO_MODEL = """
datasets:
  - name: orders
    schema: staging
    table: stg_orders
  - name: revenue
    schema: marts
    table: fct_revenue
  - name: ghost
    schema: marts
    table: fct_revenu          # the typo: one letter short, no such table
relationships:
  - name: revenue_to_orders
    from: revenue
    to: orders
    keys: [{from: id, to: id}]
  - name: ghost_to_orders
    from: ghost
    to: orders
    keys: [{from: id, to: id}]
"""


def test_an_unmatched_declaration_is_counted_into_a_note(tmp_path):
    """One typo in a hand-written YAML costs a road. A road missing for a
    reason must not look like a road nobody declared."""
    ctx = load_context(_project(tmp_path, TYPO_MODEL))

    # Precondition: the correct half still resolved, so this is a partial
    # failure and not a file that failed to load at all.
    assert [(r.many, r.one) for r in ctx.semantic_relationships] == [("marts.fct_revenue", "staging.stg_orders")]
    assert "1 of 2 declared joins did not match a catalog object" in ctx.notes
    assert "1 of 3 declared datasets did not match a catalog object" in ctx.notes


def test_a_fully_matching_model_says_nothing_about_unmatched_declarations(tmp_path):
    """The other half of the guard: the note must not fire when nothing is
    missing, or it stops meaning anything."""
    ctx = load_context(_project(tmp_path, GOOD_MODEL))

    assert not [note for note in ctx.notes if "did not match a catalog object" in note], ctx.notes


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("filename", OSI_FILENAMES)
def test_every_conventional_filename_is_found_at_the_project_root(tmp_path, filename):
    root = _project(tmp_path / filename, GOOD_MODEL, filename=filename)

    assert discover_osi_path(root) == root / filename


def test_the_tycoon_yml_key_overrides_the_convention(tmp_path):
    root = _project(tmp_path, GOOD_MODEL, filename="models/fx.osi.yml")
    (root / "semantic.yml").write_text("datasets: []\n")
    config = root / "tycoon.yml"
    config.write_text(config.read_text() + "\nsemantic_model: models/fx.osi.yml\n")

    assert discover_osi_path(root) == root / "models" / "fx.osi.yml"
    ctx = load_context(root)
    assert [r.name for r in ctx.semantic_relationships] == ["revenue_to_orders"]


def test_a_tycoon_yml_pointer_at_nothing_is_named_not_silently_conventional(tmp_path):
    """A broken pointer is a different fact from 'no semantic model', and
    falling back to the convention would hide the misconfiguration."""
    root = _project(tmp_path, GOOD_MODEL)
    config = root / "tycoon.yml"
    config.write_text(config.read_text() + "\nsemantic_model: models/missing.yml\n")

    ctx = load_context(root)

    assert ctx.semantic_relationships == ()
    assert "semantic model declared in tycoon.yml but not found" in ctx.notes


def test_a_directory_with_no_semantic_file_discovers_nothing(tmp_path):
    root = _project(tmp_path, None)

    assert discover_osi_path(root) is None


# ---------------------------------------------------------------------------
# ai_context at every level, and metrics
# ---------------------------------------------------------------------------


LAYERED_CONTEXT = """
ai_context:
  instructions: The demo warehouse.
datasets:
  - name: orders
    schema: staging
    table: stg_orders
    unique_keys:
      - [id, name]
    fields:
      - name: amount
        ai_context:
          instructions: In USD.
      - name: name
    ai_context:
      instructions: One row per order.
      synonyms: order lines
      example_queries:
        - Orders by day
metrics:
  - name: order_count
    datasets: [orders]
    ai_context:
      synonyms: [volume]
"""


def test_ai_context_is_read_at_model_dataset_field_and_metric_level(tmp_path):
    model = read_osi(_project(tmp_path, LAYERED_CONTEXT) / "semantic.yml")

    assert model is not None
    assert model.ai_context.instructions == "The demo warehouse."
    dataset = model.datasets[0]
    assert dataset.ai_context.instructions == "One row per order."
    # A bare string is a one-item list; people write it that way.
    assert dataset.ai_context.synonyms == ("order lines",)
    assert dataset.ai_context.example_queries == ("Orders by day",)
    assert dataset.unique_keys == (("id", "name"),)
    # Only fields that declared something are carried: absence stays absence.
    assert set(dataset.field_context) == {"amount"}
    assert dataset.field_context["amount"].instructions == "In USD."
    assert model.metrics[0].ai_context.synonyms == ("volume",)


def test_declared_metrics_are_named_as_not_yet_rendered(tmp_path):
    """A metric is a landmark the city cannot build yet. Parsed, counted, and
    said out loud rather than dropped."""
    ctx = load_context(_project(tmp_path, LAYERED_CONTEXT))

    assert "1 declared metrics (landmarks not yet rendered)" in ctx.notes


def test_an_empty_catalog_matches_nothing_and_says_so(tmp_path):
    model = read_osi(_project(tmp_path, GOOD_MODEL) / "semantic.yml")

    joined = join_semantics(model, set())

    assert joined.relationships == ()
    assert joined.matched_datasets == 0
    assert "2 of 2 declared datasets did not match a catalog object" in joined.notes


# ---------------------------------------------------------------------------
# The shipped demo model -- the fixture the join-street rendering builds against
# ---------------------------------------------------------------------------


def test_the_shipped_demo_model_keeps_its_four_illustrative_cases():
    """`scripts/demo_tycoon_semantic.yml` is copied into `demo-tycoon/` and is
    the first real OSI file in the project. It exists to be illustrative, so
    the properties that make it illustrative are pinned here."""
    model = read_osi(SHIPPED_DEMO_MODEL)

    assert model is not None
    assert model.notes == (), f"the shipped file must parse cleanly: {model.notes}"
    names = {rel.name for rel in model.relationships}
    assert names == {
        "revenue_to_staged_customer",  # pair that ALSO has lineage
        "revenue_to_customer_dim",  # pair with NO lineage (the dim case)
        "revenue_to_customer_status",  # composite
        "order_to_staged_customer",
    }
    composite = [rel.name for rel in model.relationships if len(rel.keys) > 1]
    assert composite == ["revenue_to_customer_status"]
    annotated = {ds.name for ds in model.datasets if ds.ai_context.declared}
    assert annotated == {"revenue", "customer_dim"}
    # Every endpoint names a declared dataset: the shipped file carries no
    # unmatched declaration (the typo case lives in TYPO_MODEL above).
    declared = {ds.name for ds in model.datasets}
    for rel in model.relationships:
        assert {rel.many, rel.one} <= declared, rel.name
