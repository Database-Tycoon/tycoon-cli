"""Column-level lineage: sqlglot tracing and the jinja-subset resolution.

The tracer's contract: measured output columns (never the SQL's own claims)
traced back to catalog columns, absence counted rather than guessed at.
"""

import json

from tycoon_city.catalog.column_lineage import ColumnEdge, derive_column_lineage
from tycoon_city.catalog.dbt_manifest import join_manifest, read_manifest

RAW = {"raw.events": (("id", "BIGINT"), ("payload", "JSON"), ("ts", "TIMESTAMP"))}


def test_aliases_and_casts_trace_to_the_real_source_column():
    columns = dict(RAW, **{"staging.stg_events": (("event_id", "BIGINT"), ("day", "DATE"))})
    sql = {
        "staging.stg_events": (
            "CREATE VIEW staging.stg_events AS SELECT id AS event_id, CAST(ts AS DATE) AS day FROM raw.events"
        )
    }
    result = derive_column_lineage(sql, columns)
    assert set(result.edges) == {
        ColumnEdge("raw.events", "id", "staging.stg_events", "event_id"),
        ColumnEdge("raw.events", "ts", "staging.stg_events", "day"),
    }
    assert result.unparsed == 0


def test_select_star_expands_through_the_measured_schema():
    """`select *` names no columns; only the measured schema can expand it."""
    columns = dict(RAW, **{"staging.copy": (("id", "BIGINT"), ("payload", "JSON"), ("ts", "TIMESTAMP"))})
    sql = {"staging.copy": "SELECT * FROM raw.events"}
    result = derive_column_lineage(sql, columns)
    assert ColumnEdge("raw.events", "payload", "staging.copy", "payload") in result.edges
    assert len(result.edges) == 3


def test_aggregates_contribute_their_inputs_and_literals_contribute_nothing():
    columns = dict(RAW, **{"marts.daily": (("day", "DATE"), ("n", "BIGINT"), ("tag", "VARCHAR"))})
    sql = {"marts.daily": ("SELECT CAST(ts AS DATE) AS day, count(id) AS n, 'x' AS tag FROM raw.events GROUP BY 1")}
    result = derive_column_lineage(sql, columns)
    assert ColumnEdge("raw.events", "id", "marts.daily", "n") in result.edges
    assert not any(e.dst_col == "tag" for e in result.edges)


def test_unparseable_sql_is_counted_and_costs_only_its_own_object():
    columns = dict(RAW, **{"staging.ok": (("id", "BIGINT"),), "staging.bad": (("id", "BIGINT"),)})
    sql = {
        "staging.ok": "SELECT id FROM raw.events",
        "staging.bad": "SELECT FROM WHERE GROUP",
    }
    result = derive_column_lineage(sql, columns)
    assert result.unparsed == 1
    assert set(result.edges) == {ColumnEdge("raw.events", "id", "staging.ok", "id")}


def test_matching_is_case_insensitive_with_the_catalog_spelling_canonical():
    columns = dict(RAW, **{"staging.upper": (("id", "BIGINT"),)})
    sql = {"staging.upper": "SELECT ID FROM RAW.EVENTS"}
    result = derive_column_lineage(sql, columns)
    assert [e.src for e in result.edges] == ["raw.events"]


# --- The manifest side: raw_code resolved without a jinja engine ------------


def _manifest(tmp_path, nodes, sources=None):
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "metadata": {"dbt_schema_version": "v12"},
                "nodes": nodes,
                "sources": sources or {},
            }
        )
    )
    return path


def _model(uid, schema, alias, raw_code="", compiled_code=None, name=None):
    node = {
        "unique_id": uid,
        "resource_type": "model",
        "name": name or uid.rsplit(".", 1)[-1],
        "schema": schema,
        "alias": alias,
        "depends_on": {"nodes": []},
        "config": {"materialized": "table"},
        "raw_code": raw_code,
    }
    if compiled_code is not None:
        node["compiled_code"] = compiled_code
    return node


def test_config_ref_and_source_resolve_but_residual_jinja_counts_out(tmp_path):
    nodes = {
        "model.p.stg": _model("model.p.stg", "staging", "stg_orders"),
        "model.p.clean": _model(
            "model.p.clean",
            "marts",
            "clean",
            raw_code=(
                "{{ config(materialized='table') }}\n"
                "select id from {{ ref('stg') }} union all "
                "select id from {{ source('raw', 'orders') }}"
            ),
        ),
        "model.p.loopy": _model(
            "model.p.loopy",
            "marts",
            "loopy",
            raw_code="{% for s in sources %} select 1 {% endfor %}",
        ),
    }
    sources = {
        "source.p.raw.orders": {
            "resource_type": "source",
            "schema": "raw",
            "name": "orders",
            "source_name": "raw",
            "identifier": "orders",
        }
    }
    index = read_manifest(_manifest(tmp_path, nodes, sources))

    resolved = index.sql_of["model.p.clean"]
    assert "{{" not in resolved and "{%" not in resolved
    assert "staging.stg_orders" in resolved  # ref -> schema.ALIAS, not model name
    assert "raw.orders" in resolved
    # The empty-raw_code model and the loop model both count out.
    assert "model.p.loopy" not in index.sql_of
    assert index.models_without_sql == 2


def test_two_argument_ref_resolves_by_its_second_argument(tmp_path):
    """`ref('package', 'model')` names the model in arg TWO; resolving by the
    first would look up the package name and leave the jinja unresolved."""
    nodes = {
        "model.p.stg": _model("model.p.stg", "staging", "stg_orders"),
        "model.p.m": _model("model.p.m", "marts", "m", raw_code="select 1 from {{ ref('p', 'stg') }}"),
    }
    index = read_manifest(_manifest(tmp_path, nodes))
    assert index.sql_of["model.p.m"] == "select 1 from staging.stg_orders"


def test_compiled_code_wins_over_raw_code(tmp_path):
    nodes = {
        "model.p.m": _model(
            "model.p.m",
            "marts",
            "m",
            raw_code="select 1 from {{ ref('nope') }}",
            compiled_code="select id from raw.orders",
        )
    }
    index = read_manifest(_manifest(tmp_path, nodes))
    assert index.sql_of["model.p.m"] == "select id from raw.orders"


def test_join_exposes_sql_only_for_matched_models(tmp_path):
    nodes = {
        "model.p.here": _model("model.p.here", "marts", "here", raw_code="select 1"),
        "model.p.gone": _model("model.p.gone", "other", "gone", raw_code="select 2"),
    }
    index = read_manifest(_manifest(tmp_path, nodes))
    join = join_manifest(index, {"marts.here"})
    assert set(join.sql_by_key) == {"marts.here"}
    assert join.models_without_sql == 0
