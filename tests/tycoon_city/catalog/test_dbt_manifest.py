"""The join rules, each pinned against the failure it prevents."""

import json

import pytest

from tycoon_city.catalog.dbt_manifest import join_manifest, read_manifest


def _manifest(tmp_path, nodes=None, sources=None):
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "metadata": {"dbt_schema_version": "v12"},
                "nodes": nodes or {},
                "sources": sources or {},
            }
        )
    )
    return path


def _model(uid, schema, alias, deps=()):
    return {
        "unique_id": uid,
        "resource_type": "model",
        "name": uid.rsplit(".", 1)[-1],
        "schema": schema,
        "alias": alias,
        "depends_on": {"nodes": list(deps)},
        "config": {"materialized": "table"},
    }


def test_missing_or_corrupt_manifest_reads_as_none(tmp_path):
    assert read_manifest(tmp_path / "nope.json") is None
    bad = tmp_path / "bad.json"
    bad.write_text("{ nope")
    assert read_manifest(bad) is None


def test_join_key_is_schema_alias_never_the_unique_id_segment(tmp_path):
    """`alias:` overrides make the table name differ from the model name. A
    join on the unique_id's last segment finds nothing here; the schema.alias
    join must find the table the warehouse actually holds."""
    index = read_manifest(
        _manifest(
            tmp_path,
            nodes={
                "model.p.revenue_model": _model("model.p.revenue_model", "marts", "fct_revenue", deps=("model.p.stg",)),
                "model.p.stg": _model("model.p.stg", "staging", "stg"),
            },
        )
    )

    join = join_manifest(index, {"marts.fct_revenue", "staging.stg"})

    assert join.join_rate == 1.0
    assert {(e.src, e.dst) for e in join.edges} == {("staging.stg", "marts.fct_revenue")}


def test_same_name_in_two_schemas_stays_two_models(tmp_path):
    index = read_manifest(
        _manifest(
            tmp_path,
            nodes={
                "model.p.daily_a": _model("model.p.daily_a", "staging", "daily"),
                "model.p.daily_b": _model("model.p.daily_b", "marts", "daily", deps=("model.p.daily_a",)),
            },
        )
    )

    join = join_manifest(index, {"staging.daily", "marts.daily"})

    assert join.matched_models == 2
    assert {(e.src, e.dst) for e in join.edges} == {("staging.daily", "marts.daily")}


def test_matching_is_case_insensitive_and_the_catalog_spelling_wins(tmp_path):
    """Both sides must fold: the first version of this test gave the catalog
    all-lowercase keys, so a mutant that only lowercased the manifest side
    passed it — the exact wrong-axis shape this repo keeps producing. The
    catalog keys here are mixed-case so *neither* side can skip folding."""
    index = read_manifest(
        _manifest(
            tmp_path,
            nodes={
                "model.p.m": _model("model.p.m", "STAGING", "Orders", deps=("model.p.up",)),
                "model.p.up": _model("model.p.up", "staging", "up"),
            },
        )
    )

    join = join_manifest(index, {"Staging.Orders", "Staging.Up"})

    # Emitted in the catalog's spelling, whatever the manifest wrote.
    assert {(e.src, e.dst) for e in join.edges} == {("Staging.Up", "Staging.Orders")}


def test_low_join_rate_is_measured_and_named(tmp_path):
    """dogfood's manifest points at the dev database while prod is elsewhere:
    that must surface as a named state, never as silently absent lineage."""
    index = read_manifest(
        _manifest(
            tmp_path,
            nodes={f"model.p.m{i}": _model(f"model.p.m{i}", "dev_schema", f"m{i}") for i in range(4)},
        )
    )

    join = join_manifest(index, {"prod_schema.something"})

    assert join.join_rate == 0.0
    assert any("manifest target may not match" in note for note in join.notes)


def test_sources_outside_the_catalog_are_dropped_and_counted(tmp_path):
    index = read_manifest(
        _manifest(
            tmp_path,
            nodes={"model.p.m": _model("model.p.m", "marts", "m", deps=("source.p.raw.here", "source.p.ext.gone"))},
            sources={
                "source.p.raw.here": {
                    "resource_type": "source",
                    "schema": "raw",
                    "name": "here",
                    "identifier": "here",
                },
                "source.p.ext.gone": {
                    "resource_type": "source",
                    "schema": "ext",
                    "name": "gone",
                    "identifier": "gone",
                },
            },
        )
    )

    join = join_manifest(index, {"marts.m", "raw.here"})

    assert {(e.src, e.dst) for e in join.edges} == {("raw.here", "marts.m")}
    assert join.sources_outside == 1
    assert any("1 upstream sources outside this catalog" in n for n in join.notes)


def test_tests_attach_via_attached_node_with_dependency_fallback(tmp_path):
    nodes = {
        "model.p.m": _model("model.p.m", "marts", "m"),
        "test.p.attached": {
            "unique_id": "test.p.attached",
            "resource_type": "test",
            "attached_node": "model.p.m",
            "depends_on": {"nodes": ["model.p.m"]},
        },
        # Real singular tests: attached_node None, one dependency.
        "test.p.singular": {
            "unique_id": "test.p.singular",
            "resource_type": "test",
            "attached_node": None,
            "depends_on": {"nodes": ["model.p.m"]},
        },
        # Ambiguous: two dependencies, no attached_node -- attaches to neither.
        "test.p.ambiguous": {
            "unique_id": "test.p.ambiguous",
            "resource_type": "test",
            "attached_node": None,
            "depends_on": {"nodes": ["model.p.m", "model.p.other"]},
        },
        "model.p.other": _model("model.p.other", "marts", "other"),
    }
    index = read_manifest(_manifest(tmp_path, nodes=nodes))

    assert {ref.unique_id for ref in index.tests_by_key["marts.m"]} == {
        "test.p.attached",
        "test.p.singular",
    }
    for tests in index.tests_by_key.values():
        assert "test.p.ambiguous" not in {ref.unique_id for ref in tests}


def test_self_edges_are_never_emitted(tmp_path):
    index = read_manifest(
        _manifest(
            tmp_path,
            nodes={"model.p.m": _model("model.p.m", "s", "m", deps=("model.p.m",))},
        )
    )

    assert join_manifest(index, {"s.m"}).edges == ()


def test_empty_manifest_joins_at_rate_zero_without_notes(tmp_path):
    """No models means nothing to measure: rate 0.0 but no scary note --
    'manifest may not match' would be a lie about an empty project."""
    join = join_manifest(read_manifest(_manifest(tmp_path)), {"a.b"})

    assert join.join_rate == 0.0
    assert join.total_models == 0
    assert not any("may not match" in n for n in join.notes)


@pytest.mark.parametrize("missing_key", ["schema", "alias"])
def test_nodes_missing_join_fields_are_skipped_not_fatal(tmp_path, missing_key):
    node = _model("model.p.m", "s", "m")
    node[missing_key] = None
    node["name"] = None  # keep alias from falling back to name
    index = read_manifest(_manifest(tmp_path, nodes={"model.p.m": node}))

    assert "model.p.m" not in index.key_of
