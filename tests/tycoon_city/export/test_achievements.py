"""The `achievements` block: named coverage milestones, and the two ways it lies.

The wrong-axis hazards this file is written against, both named in the brief:

* **"`achievements` is non-empty"** passes on the wrong milestones, with the
  wrong terms, counted over the wrong universe. So every assertion below names
  a milestone by `id` and pins hand-counted `have` / `need` / `short`, and the
  fixture's preconditions are asserted first — a coverage count of 2 proves
  nothing unless the fixture really does document exactly two objects.
* **"`met is False`"** passes when the real defect is that the milestone should
  be **UNKNOWN**. The decisive test is a PAIR of catalogs with the same objects
  and the same (absent) documentation, differing only in whether a dbt manifest
  was ever read: one must be a measured `have: 0`, the other must be unknown
  with `met: null`. Either one alone is satisfied by the bug.

The fixture is also built to defeat a third escape specific to the mart
milestone: its reporting layer lives in a schema called `analytics`, while the
schema literally named `mart` holds an INTERMEDIATE model. A "mart" defined by
schema name gets both of those wrong, and gets them wrong in a way that a
demo-shaped fixture (everything terminal sitting in `mart`) cannot see.
"""

import dataclasses
import json

import duckdb
import pytest

from tests.fixtures.tycoon_factory import (
    ModelSpec,
    RunSpec,
    SourceSpec,
    TestSpec,
    make_tycoon_project,
    write_sources_json,
)
from tycoon_city.catalog.loader import load_context
from tycoon_city.catalog.osi import AiContext, SemanticDataset, SemanticRelationship
from tycoon_city.export.achievements import (
    NO_FRESHNESS_NOTE,
    NO_MANIFEST_NOTE,
    NO_TEST_RESULTS_NOTE,
    NOTHING_TO_MEASURE_NOTE,
    STATE_MET,
    STATE_UNKNOWN,
    STATE_UNMET,
    _achievements,
)
from tycoon_city.export.city_json import city_document, dumps
from tycoon_city.sim.channels import DEFAULT_BINDINGS, apply_signals
from tycoon_city.sim.generator import generate_city
from tycoon_city.theme_data import load_theme_data, theme_dir

# --- the fixture catalog ---------------------------------------------------
#
#   raw.orders -> staging.stg_orders -+-> mart.int_bridge -> analytics.rpt_signed
#                                     |
#   raw.events -> staging.stg_events -+-> analytics.rpt_dirt
#
#   island.lonely: no lineage at all.
#   scratch.experiment: in the warehouse, in NO dbt project (added straight to
#     the duckdb file below) — the object that makes "every catalog object" and
#     "every dbt-managed object" two different universes. Without it, a
#     coverage denominator computed over `dbt_context_by_key` scores exactly
#     the same and nothing here could tell the two apart.
#
# Chosen against the schema names on purpose. The two TERMINAL objects sit in
# `analytics`; the object in the schema called `mart` is an intermediate with a
# downstream, so it is not a mart. `island.lonely` has no inbound edge, so it
# is not the end of a pipeline either — it is a building with no streets.

MODELS = (
    ModelSpec(
        "staging",
        "stg_orders",
        depends_on=("source.fx_dbt.raw.orders",),
        description="Typed, deduplicated orders.",
    ),
    ModelSpec("staging", "stg_events", depends_on=("source.fx_dbt.raw.events",)),
    ModelSpec("mart", "int_bridge", depends_on=("model.fx_dbt.stg_orders",)),
    ModelSpec(
        "analytics",
        "rpt_signed",
        depends_on=("model.fx_dbt.int_bridge",),
        description="The signed report.",
    ),
    ModelSpec(
        "analytics",
        "rpt_dirt",
        depends_on=("model.fx_dbt.stg_orders", "model.fx_dbt.stg_events"),
    ),
    ModelSpec("island", "lonely"),
)

SOURCES = (SourceSpec("raw", "orders"), SourceSpec("raw", "events"))

TESTS = (
    TestSpec("t_fail", attached_node="model.fx_dbt.rpt_dirt"),
    TestSpec("t_warn", attached_node="model.fx_dbt.stg_orders"),
    TestSpec("t_pass", attached_node="model.fx_dbt.int_bridge"),
)

RUNS = (
    RunSpec(
        "build-1",
        "build",
        nodes=(
            *((m.unique_id, "success", 1.0) for m in MODELS),
            ("test.fx_dbt.t_fail", "fail", 0.1),
            ("test.fx_dbt.t_warn", "warn", 0.1),
            ("test.fx_dbt.t_pass", "pass", 0.1),
        ),
    ),
)

# Injected rather than written as YAML: the OSI reader has its own suite
# (`tests/catalog/test_osi.py`), and what this file is about is what the
# emitter COUNTS. One declared join, on the pair that paves `rpt_signed`;
# `rpt_dirt` is the mart with only a dirt track.
RELATIONSHIPS = (
    SemanticRelationship(
        name="signed_to_bridge",
        many="analytics.rpt_signed",
        one="mart.int_bridge",
        keys=(("id", "id"),),
    ),
)
DATASETS = {
    "analytics.rpt_signed": SemanticDataset(
        name="signed",
        relation="analytics.rpt_signed",
        primary_key=("id",),
        ai_context=AiContext(instructions="The signed report.", synonyms=("signed",)),
    ),
    # Declared but NOT annotated: a dataset someone named without signage. It
    # must count towards nothing, which is what keeps `old_town_signed` from
    # being "declared at all" wearing another name.
    "mart.int_bridge": SemanticDataset(name="bridge", relation="mart.int_bridge", primary_key=("id",)),
}

EXPECTED_IDS = [
    "documented_buildings",
    "tested_buildings",
    "sources_under_sla",
    "old_town_signed",
    "marts_paved",
    "fires_out",
]

MILESTONE_FIELDS = {"id", "name", "description", "state", "met", "have", "need", "short", "note"}


@pytest.fixture
def theme():
    return load_theme_data(theme_dir("default"))


def _project(tmp_path, name, *, freshness=True):
    root = make_tycoon_project(tmp_path / name, models=MODELS, sources=SOURCES, tests=TESTS, runs=RUNS)
    # A table the dbt project knows nothing about, written straight into the
    # warehouse — the real shape (`scratch.experiment` in demo-tycoon).
    con = duckdb.connect(str(root / "data" / "fx.duckdb"))
    con.execute("create schema if not exists scratch")
    con.execute("create table scratch.experiment as select 1 as id")
    con.close()
    if freshness:
        # raw.orders is judged; raw.events is a source nobody ran freshness on.
        write_sources_json(root, {"source.fx_dbt.raw.orders": ("pass", "2026-08-06T10:00:00")})
    loaded = load_context(root)
    return dataclasses.replace(loaded, semantic_relationships=RELATIONSHIPS, ai_context_by_key=DATASETS)


@pytest.fixture
def ctx(tmp_path):
    """The full catalog: manifest, tests, run results, one freshness verdict,
    and an injected OSI model. Every milestone's evidence is present, so every
    milestone must be MEASURED and none of them unknown."""
    return _project(tmp_path, "fx")


def _by_id(block) -> dict:
    return {m["id"]: m for m in block["milestones"]}


# --- preconditions ----------------------------------------------------------


def test_the_fixture_is_shaped_the_way_every_count_below_assumes(ctx):
    """Asserted first because every hand-count downstream is meaningless if the
    fixture drifted: the manifest really joined, exactly two objects carry a
    description, the schema called `mart` really does hold a non-terminal
    model, and the reporting layer really is called something else."""
    keys = {obj.key for obj in ctx.objects}
    assert keys == {
        "raw.orders",
        "raw.events",
        "staging.stg_orders",
        "staging.stg_events",
        "mart.int_bridge",
        "analytics.rpt_signed",
        "analytics.rpt_dirt",
        "island.lonely",
        "scratch.experiment",
    }
    assert ctx.dbt_context_by_key, "the manifest joined onto this catalog"
    # The universe separator: a real catalog object dbt has never heard of.
    assert "scratch.experiment" not in ctx.dbt_context_by_key
    assert len(ctx.dbt_context_by_key) == 8, "everything else IS dbt-managed"
    documented = {k for k, c in ctx.dbt_context_by_key.items() if c.description.strip()}
    assert documented == {"staging.stg_orders", "analytics.rpt_signed"}
    # The trap: an object in the schema literally called `mart`, with a
    # downstream, so schema-name matching and lineage disagree about it.
    assert any(e.src == "mart.int_bridge" for e in ctx.edges)
    assert {e.dst for e in ctx.edges if e.src == "staging.stg_orders"} == {
        "mart.int_bridge",
        "analytics.rpt_dirt",
    }
    assert set(ctx.source_freshness_by_key) == {"raw.orders"}, "raw.events is unjudged"


# --- the shape of the block -------------------------------------------------


def test_the_block_is_these_six_milestones_in_this_order(ctx):
    block = _achievements(ctx)
    assert [m["id"] for m in block["milestones"]] == EXPECTED_IDS
    for milestone in block["milestones"]:
        assert set(milestone) == MILESTONE_FIELDS, milestone["id"]
        assert milestone["state"] in (STATE_MET, STATE_UNMET, STATE_UNKNOWN)


def test_every_milestone_is_measurable_on_a_fully_evidenced_catalog(ctx):
    """The control for the unknown tests below: with all four artifacts read,
    NOTHING may come back unknown. A guard that only ever sees unknown states
    cannot tell the two apart."""
    block = _achievements(ctx)
    assert [m["state"] for m in block["milestones"]] == [STATE_UNMET] * 6
    assert block["note"] == "0 of 6 milestones met; every milestone's terms are measurable here"


# --- the hand-counted terms -------------------------------------------------


def test_documentation_coverage_counts_descriptions_over_the_whole_city(ctx):
    """`need` is 9, the whole catalog — not 8, the dbt-managed part of it. The
    milestone is about the CITY: an undocumented building is undocumented
    whether or not dbt is the one that would have documented it, and
    `scratch.experiment` is exactly the building that separates the two
    denominators."""
    milestone = _by_id(_achievements(ctx))["documented_buildings"]
    assert (milestone["have"], milestone["need"]) == (2, 9)
    assert milestone["short"] == [
        "analytics.rpt_dirt",
        "island.lonely",
        "mart.int_bridge",
        "raw.events",
        "raw.orders",
        "scratch.experiment",
        "staging.stg_events",
    ]
    assert milestone["state"] == STATE_UNMET and milestone["met"] is False


def test_test_coverage_counts_the_objects_a_declared_test_is_attached_to(ctx):
    assert set(ctx.tests_by_key) == {
        "analytics.rpt_dirt",
        "staging.stg_orders",
        "mart.int_bridge",
    }
    milestone = _by_id(_achievements(ctx))["tested_buildings"]
    assert (milestone["have"], milestone["need"]) == (3, 9)
    assert "analytics.rpt_signed" in milestone["short"]
    assert "scratch.experiment" in milestone["short"]


def test_source_sla_counts_lineage_origins_and_leaves_the_orphan_out(ctx):
    """`island.lonely` has no inbound edge, so a naive "nothing feeds it, it
    must be a source" rule would sweep it in and make `need` 3. It also feeds
    nothing, which is what excludes it."""
    milestone = _by_id(_achievements(ctx))["sources_under_sla"]
    assert (milestone["have"], milestone["need"]) == (1, 2)
    assert milestone["short"] == ["raw.events"]


def test_marts_are_terminal_in_lineage_not_the_schema_called_mart(ctx):
    """The definition test. Schema-name matching would count `mart.int_bridge`
    (need 3, and a paved mart that is not a mart) and would miss both
    `analytics` reports entirely."""
    milestone = _by_id(_achievements(ctx))["marts_paved"]
    assert (milestone["have"], milestone["need"]) == (1, 2)
    assert milestone["short"] == ["analytics.rpt_dirt"]
    assert "mart.int_bridge" not in milestone["short"]
    assert "island.lonely" not in milestone["short"]
    # The declared join is what paves `rpt_signed`; district membership is
    # reported, and the two marts share one district.
    assert "across 1 district" in milestone["note"]


def test_old_town_signed_counts_ai_context_not_merely_being_declared(ctx):
    """`mart.int_bridge` HAS a declared dataset and no `ai_context`. Counting
    declarations instead of signage would score it, and the milestone would
    silently become "objects the semantic model mentions"."""
    milestone = _by_id(_achievements(ctx))["old_town_signed"]
    assert (milestone["have"], milestone["need"]) == (1, 9)
    assert "mart.int_bridge" in milestone["short"]
    assert "analytics.rpt_signed" not in milestone["short"]


def test_a_warning_test_is_not_a_fire(ctx):
    """`staging.stg_orders` ran a test that WARNED. A fire is a failure; an
    amber marker is not one, and folding warn into fail would make `have` 1."""
    milestone = _by_id(_achievements(ctx))["fires_out"]
    assert (milestone["have"], milestone["need"]) == (2, 3)
    assert milestone["short"] == ["analytics.rpt_dirt"]
    assert "staging.stg_orders" not in milestone["short"]


# --- unknown is not zero ----------------------------------------------------
#
# The pair. Same three objects, same absence of any description; the only
# difference is whether a dbt manifest was ever read.

BARE_MODELS = (
    ModelSpec("staging", "a", depends_on=("source.fx_dbt.raw.orders",)),
    ModelSpec("mart", "b", depends_on=("model.fx_dbt.a",)),
)
BARE_SOURCES = (SourceSpec("raw", "orders"),)


def _bare(tmp_path, name, *, with_manifest):
    root = make_tycoon_project(
        tmp_path / name,
        models=BARE_MODELS,
        sources=BARE_SOURCES,
        tests=(),
        runs=(),
        with_manifest=with_manifest,
    )
    return load_context(root)


def test_a_manifest_with_no_descriptions_is_a_measured_zero(tmp_path):
    ctx = _bare(tmp_path, "documented", with_manifest=True)
    assert ctx.dbt_context_by_key, "the manifest joined — the terms ARE knowable"
    assert not any(c.description.strip() for c in ctx.dbt_context_by_key.values())
    milestone = _by_id(_achievements(ctx))["documented_buildings"]
    assert milestone["state"] == STATE_UNMET
    assert milestone["met"] is False
    assert milestone["have"] == 0
    assert milestone["need"] == 3
    assert milestone["short"] == ["mart.b", "raw.orders", "staging.a"]


def test_no_manifest_at_all_is_unknown_and_never_a_zero(tmp_path):
    """The same catalog with the manifest removed. `have: 0` here would invent
    a failure out of an absence — the documentation may be immaculate in a
    manifest this export never got."""
    ctx = _bare(tmp_path, "unknown", with_manifest=False)
    assert not ctx.dbt_context_by_key and not ctx.dbt_nodes_by_key
    milestone = _by_id(_achievements(ctx))["documented_buildings"]
    assert milestone["state"] == STATE_UNKNOWN
    # Both readings have to refuse: the discriminator, and the flag a client
    # that only looks at `met` would switch on.
    assert milestone["met"] is None
    assert milestone["met"] is not False
    assert milestone["have"] is None and milestone["need"] is None
    assert milestone["short"] == []
    assert milestone["note"] == NO_MANIFEST_NOTE


def test_a_catalog_with_nothing_to_measure_is_all_unknown_plus_a_note(tmp_path):
    """No manifest, no semantic model, no freshness verdicts, no test results:
    six zeroes would render absence as failure. Every milestone is unknown and
    the block says why."""
    ctx = _bare(tmp_path, "nothing", with_manifest=False)
    block = _achievements(ctx)
    assert [m["state"] for m in block["milestones"]] == [STATE_UNKNOWN] * 6
    assert not any(m["met"] is False for m in block["milestones"])
    assert not any(m["have"] == 0 for m in block["milestones"])
    assert block["note"] == NOTHING_TO_MEASURE_NOTE


def test_sources_that_exist_but_were_never_judged_are_unknown_not_zero(tmp_path):
    """The gate that the all-unknown catalog cannot exercise: here the SOURCES
    are known (two lineage origins) and only the verdicts are missing. `have: 0
    of 2` would read as "two sources are out of SLA" when nobody ever ran `dbt
    source freshness` — the same lie as an unknown building rendered stale."""
    ctx = _project(tmp_path, "unjudged", freshness=False)
    assert not ctx.source_freshness_by_key
    assert any(e.dst == "staging.stg_orders" for e in ctx.edges), "origins exist"
    milestone = _by_id(_achievements(ctx))["sources_under_sla"]
    assert milestone["state"] == STATE_UNKNOWN
    assert milestone["met"] is None
    assert milestone["have"] is None and milestone["need"] is None
    assert milestone["note"] == NO_FRESHNESS_NOTE


def test_declared_tests_that_never_ran_leave_the_fires_unknown(tmp_path):
    """Tests are declared and nothing has run them. `fires_out` must not report
    the fires as out: an unrun test is not a passing test, and "no fires known"
    is not "no fires"."""
    root = make_tycoon_project(
        tmp_path / "unrun",
        models=BARE_MODELS,
        sources=BARE_SOURCES,
        tests=(TestSpec("t_never", attached_node="model.fx_dbt.a"),),
        runs=(),
    )
    ctx = load_context(root)
    assert ctx.tests_by_key, "a test IS declared"
    assert ctx.runs is not None and not ctx.runs.node_results, "and it never ran"
    milestone = _by_id(_achievements(ctx))["fires_out"]
    assert milestone["state"] == STATE_UNKNOWN
    assert milestone["met"] is None
    # The note has to name the missing artifact, not the empty universe: the
    # difference is what tells someone to go run their tests.
    assert milestone["note"] == NO_TEST_RESULTS_NOTE


def test_an_empty_universe_is_unknown_rather_than_vacuously_met(tmp_path):
    """A catalog with a semantic model but no terminal object has no marts. A
    milestone that is "met" because there was nothing to check is the same lie
    as a zero on a missing measurement, in the opposite colour."""
    ctx = _bare(tmp_path, "nomarts", with_manifest=False)
    # Lineage-free (tables only, no manifest) — so there are no marts at all,
    # while the semantic evidence is present.
    assert not ctx.edges
    ctx = dataclasses.replace(ctx, semantic_relationships=RELATIONSHIPS)
    milestone = _by_id(_achievements(ctx))["marts_paved"]
    assert milestone["state"] == STATE_UNKNOWN
    assert milestone["met"] is None
    assert "nothing to measure" in milestone["note"]


# --- on the wire ------------------------------------------------------------


def test_the_block_rides_the_document_and_survives_serialisation(ctx, theme):
    """Asserted on a RE-PARSED document: a block that serialises wrongly passes
    every assertion made on the dict it came from."""
    city = generate_city(ctx, theme.style_rules)
    apply_signals(city, ctx, DEFAULT_BINDINGS)
    doc = json.loads(dumps(city_document(ctx, city, theme)))
    assert doc["version"] == 1, "achievements are additive"
    assert [m["id"] for m in doc["achievements"]["milestones"]] == EXPECTED_IDS
    assert _by_id(doc["achievements"])["marts_paved"]["short"] == ["analytics.rpt_dirt"]


def test_the_block_is_stateless_and_byte_stable(ctx, theme):
    """Stateless by the 1.0 decision: no minted badge, no first-earned
    timestamp, nothing persisted. Two emits of the same context are identical,
    and the milestone records carry no field that could hold a clock."""
    city = generate_city(ctx, theme.style_rules)
    apply_signals(city, ctx, DEFAULT_BINDINGS)
    first = json.dumps(city_document(ctx, city, theme)["achievements"], ensure_ascii=False)
    second = json.dumps(_achievements(ctx), ensure_ascii=False)
    assert first == second
    for milestone in _achievements(ctx)["milestones"]:
        assert set(milestone) == MILESTONE_FIELDS
        assert not any(field.endswith(("_at", "_ts", "_id")) for field in milestone)
