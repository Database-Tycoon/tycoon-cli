"""dbt sources that live outside the rendered warehouse (gh-387).

The real-world shape is nyc_data: every source says `database: raw`, a separate
attached DuckDB file (or an S3 DuckLake), so none of them is an object in the
warehouse the city reads. They are still in the manifest, and a staging model
that reads one must name it as an upstream instead of claiming it has none.

Asserted on a re-parsed `city.json`, because the inspector reads the wire
document, not the loader's context. `tycoon_city` is imported inside the
helpers, never at module level: collection would otherwise load it into the
process and break `test_city_command`'s check that the CLI starts without it.
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

MODEL_SPECS = (
    {
        "schema": "staging",
        "name": "stg_citibike__stations",
        "depends_on": ("source.fx_dbt.raw_citibike.station_information",),
        "raw_code": "select 1 as id from {{ source('raw_citibike', 'station_information') }}",
    },
    {
        "schema": "staging",
        "name": "stg_orders",
        "depends_on": ("source.fx_dbt.raw.orders", "source.fx_dbt.raw_citibike.station_status"),
    },
    {"schema": "marts", "name": "fct_stations", "depends_on": ("model.fx_dbt.stg_citibike__stations",)},
)

SOURCE_SPECS = (
    {"schema": "raw", "name": "orders"},
    {"schema": "raw_citibike", "name": "station_information", "database": "raw"},
    {"schema": "raw_citibike", "name": "station_status", "database": "raw"},
)


def _document(root) -> dict:
    from tycoon_city.export import build_city, city_document, dumps
    from tycoon_city.theme_data import load_theme_data, theme_dir

    theme = load_theme_data(theme_dir("default"))
    ctx, city = build_city(root, theme.style_rules, now=datetime(2026, 8, 2))
    return json.loads(dumps(city_document(ctx, city, theme)))


def _object(doc: dict, key: str) -> dict:
    return next(obj for obj in doc["objects"] if obj["key"] == key)


@pytest.fixture
def project(tmp_path):
    from tycoon_city.demo.factory import ModelSpec, SourceSpec, make_tycoon_project

    return make_tycoon_project(
        tmp_path / "fx",
        models=tuple(ModelSpec(**spec) for spec in MODEL_SPECS),
        sources=tuple(SourceSpec(**spec) for spec in SOURCE_SPECS),
        tests=(),
    )


def test_a_source_outside_the_warehouse_is_named_as_upstream(project):
    doc = _document(project)

    staging = _object(doc, "staging.stg_citibike__stations")
    assert staging["dbt"]["external_upstream"] == [
        {
            "name": "raw_citibike.station_information",
            "relation": "raw.raw_citibike.station_information",
            "freshness_status": None,
        }
    ]
    assert not any(edge["dst"] == "staging.stg_citibike__stations" for edge in doc["edges"])


def test_a_source_inside_the_warehouse_stays_an_edge_not_a_stub(project):
    doc = _document(project)

    orders = _object(doc, "staging.stg_orders")
    assert [s["name"] for s in orders["dbt"]["external_upstream"]] == ["raw_citibike.station_status"]
    assert any((e["src"], e["dst"]) == ("raw.orders", "staging.stg_orders") for e in doc["edges"])


def test_a_model_that_reads_only_models_has_no_external_upstream(project):
    doc = _document(project)

    assert _object(doc, "marts.fct_stations")["dbt"]["external_upstream"] == []


def test_an_external_source_carries_its_dbt_freshness_verdict(project):
    from tycoon_city.demo.factory import write_sources_json

    write_sources_json(project, {"source.fx_dbt.raw_citibike.station_information": ("warn", None)})

    doc = _document(project)

    (stub,) = _object(doc, "staging.stg_citibike__stations")["dbt"]["external_upstream"]
    assert stub["freshness_status"] == "warn"
