"""Tests for tycoon.layers — layer classification for dbt + sources."""

from __future__ import annotations

import json
from pathlib import Path

from tycoon.layers import (
    Layer,
    LayerClassification,
    Vendor,
    classify_dbt_models,
    classify_dlt_sources,
    classify_fivetran_sources,
    filter_by_layer,
    load_manifest,
)


# -- helpers --------------------------------------------------------------------


def _node(
    name: str,
    *,
    rtype: str = "model",
    file_path: str = "",
    schema: str = "main",
    meta: dict | None = None,
) -> dict:
    """Minimal manifest-node shape for tests."""
    return {
        "resource_type": rtype,
        "name": name,
        "schema": schema,
        "original_file_path": file_path,
        "config": {"meta": meta or {}},
    }


def _manifest(nodes: dict[str, dict]) -> dict:
    return {"nodes": nodes}


# -- dbt manifest classification -----------------------------------------------


class TestClassifyDbtModelsFolderConvention:
    """Folder convention is the default — no overrides needed."""

    def test_staging_folder_maps_to_staging_layer(self) -> None:
        m = _manifest(
            {
                "model.p.stg_orders": _node(
                    "stg_orders", file_path="models/staging/stg_orders.sql"
                )
            }
        )
        [c] = classify_dbt_models(m)
        assert c.layer is Layer.STAGING
        assert c.vendor is Vendor.DBT
        assert c.name == "stg_orders"
        assert c.identifier == "dbt:model.p.stg_orders"

    def test_intermediate_folder(self) -> None:
        m = _manifest(
            {
                "model.p.int_x": _node(
                    "int_x", file_path="models/intermediate/int_x.sql"
                )
            }
        )
        [c] = classify_dbt_models(m)
        assert c.layer is Layer.INTERMEDIATE

    def test_marts_folder(self) -> None:
        m = _manifest(
            {"model.p.fct_o": _node("fct_o", file_path="models/marts/fct_o.sql")}
        )
        [c] = classify_dbt_models(m)
        assert c.layer is Layer.MART

    def test_aliased_folder_names(self) -> None:
        """`core/` and `published/` are common aliases for marts."""
        m = _manifest(
            {
                "model.p.fct_a": _node(
                    "fct_a", file_path="models/core/fct_a.sql"
                ),
                "model.p.fct_b": _node(
                    "fct_b", file_path="models/published/fct_b.sql"
                ),
            }
        )
        layers = {c.name: c.layer for c in classify_dbt_models(m)}
        assert layers == {"fct_a": Layer.MART, "fct_b": Layer.MART}

    def test_nested_folder_classifies_by_top_level(self) -> None:
        """models/staging/finance/stg_invoices.sql still classifies as staging."""
        m = _manifest(
            {
                "model.p.stg_inv": _node(
                    "stg_inv",
                    file_path="models/staging/finance/stg_invoices.sql",
                )
            }
        )
        [c] = classify_dbt_models(m)
        assert c.layer is Layer.STAGING

    def test_unknown_folder_is_unclassified(self) -> None:
        """A model in `models/scratch/` falls through to UNCLASSIFIED."""
        m = _manifest(
            {"model.p.x": _node("x", file_path="models/scratch/x.sql")}
        )
        [c] = classify_dbt_models(m)
        assert c.layer is Layer.UNCLASSIFIED

    def test_no_file_path_is_unclassified(self) -> None:
        """Defensive: a node without original_file_path doesn't crash."""
        m = _manifest({"model.p.x": _node("x", file_path="")})
        [c] = classify_dbt_models(m)
        assert c.layer is Layer.UNCLASSIFIED


class TestClassifyDbtModelsMetaOverride:
    """meta.tycoon_layer trumps folder convention."""

    def test_per_model_meta_overrides_folder(self) -> None:
        m = _manifest(
            {
                "model.p.scratch_real_mart": _node(
                    "scratch_real_mart",
                    file_path="models/scratch/scratch_real_mart.sql",
                    meta={"tycoon_layer": "mart"},
                )
            }
        )
        [c] = classify_dbt_models(m)
        assert c.layer is Layer.MART

    def test_meta_is_case_insensitive(self) -> None:
        m = _manifest(
            {
                "model.p.x": _node(
                    "x", file_path="", meta={"tycoon_layer": "STAGING"}
                )
            }
        )
        [c] = classify_dbt_models(m)
        assert c.layer is Layer.STAGING

    def test_typoed_meta_falls_back_to_folder(self) -> None:
        """User-typo'd meta value shouldn't crash — fall through to folder."""
        m = _manifest(
            {
                "model.p.stg_x": _node(
                    "stg_x",
                    file_path="models/staging/stg_x.sql",
                    meta={"tycoon_layer": "mrt"},
                )
            }
        )
        [c] = classify_dbt_models(m)
        assert c.layer is Layer.STAGING


class TestClassifyDbtModelsResourceTypes:
    """Snapshots and seeds get their own layer regardless of folder."""

    def test_snapshot_classified_as_snapshot(self) -> None:
        m = _manifest(
            {
                "snapshot.p.snap_x": _node(
                    "snap_x", rtype="snapshot", file_path="snapshots/snap_x.sql"
                )
            }
        )
        [c] = classify_dbt_models(m)
        assert c.layer is Layer.SNAPSHOT

    def test_seed_classified_as_seed(self) -> None:
        m = _manifest(
            {
                "seed.p.zip_codes": _node(
                    "zip_codes", rtype="seed", file_path="seeds/zip_codes.csv"
                )
            }
        )
        [c] = classify_dbt_models(m)
        assert c.layer is Layer.SEED

    def test_non_classifiable_resource_types_skipped(self) -> None:
        """Tests, exposures, etc. are not modelled here."""
        m = _manifest(
            {
                "test.p.t": _node("t", rtype="test"),
                "exposure.p.e": _node("e", rtype="exposure"),
                "model.p.stg_x": _node(
                    "stg_x", file_path="models/staging/stg_x.sql"
                ),
            }
        )
        out = classify_dbt_models(m)
        assert len(out) == 1
        assert out[0].name == "stg_x"


class TestLoadManifest:
    """load_manifest is the file-system wrapper around classify_dbt_models."""

    def test_returns_none_when_missing(self, tmp_path: Path) -> None:
        # No target/ directory at all.
        assert load_manifest(tmp_path) is None

    def test_returns_none_when_malformed(self, tmp_path: Path) -> None:
        target = tmp_path / "target"
        target.mkdir()
        (target / "manifest.json").write_text("not json {{{")
        assert load_manifest(tmp_path) is None

    def test_round_trip(self, tmp_path: Path) -> None:
        target = tmp_path / "target"
        target.mkdir()
        m = _manifest(
            {
                "model.p.stg_x": _node(
                    "stg_x", file_path="models/staging/stg_x.sql"
                )
            }
        )
        (target / "manifest.json").write_text(json.dumps(m))
        loaded = load_manifest(tmp_path)
        assert loaded is not None
        [c] = classify_dbt_models(loaded)
        assert c.layer is Layer.STAGING


# -- source classification -----------------------------------------------------


class TestClassifyDltSources:
    def test_dict_input(self) -> None:
        sources = {
            "pokeapi": {"schema_name": "raw_pokeapi", "type": "rest_api"},
            "stripe": {"schema_name": "raw_stripe", "type": "sql_database"},
        }
        out = classify_dlt_sources(sources)
        assert {c.name for c in out} == {"pokeapi", "stripe"}
        assert all(c.vendor is Vendor.DLT for c in out)
        assert all(c.layer is Layer.SOURCE for c in out)
        pokeapi = next(c for c in out if c.name == "pokeapi")
        assert pokeapi.schema == "raw_pokeapi"
        assert pokeapi.identifier == "dlt:raw_pokeapi.pokeapi"

    def test_pydantic_input(self) -> None:
        """SourceConfig pydantic objects work the same as dicts."""
        from tycoon.project import SourceConfig

        cfg = SourceConfig.model_validate(
            {
                "type": "rest_api",
                "config": {"base_url": "https://x"},
                "schema": "raw_pokeapi",
            }
        )
        [c] = classify_dlt_sources({"pokeapi": cfg})
        assert c.schema == "raw_pokeapi"
        assert c.vendor is Vendor.DLT

    def test_empty_block(self) -> None:
        assert classify_dlt_sources({}) == []
        assert classify_dlt_sources(None) == []


class TestClassifyFivetranSources:
    def test_snapshot_rows(self) -> None:
        snapshots = [
            {"name": "orders_pg", "schema_name": "raw_pg", "connector_id": "c1"},
            {
                "name": "stripe_payments",
                "schema_name": "raw_stripe",
                "connector_id": "c2",
            },
        ]
        out = classify_fivetran_sources(snapshots)
        assert {c.name for c in out} == {"orders_pg", "stripe_payments"}
        assert all(c.vendor is Vendor.FIVETRAN for c in out)
        assert all(c.layer is Layer.SOURCE for c in out)

    def test_missing_name_falls_back_to_connector_id(self) -> None:
        [c] = classify_fivetran_sources([{"connector_id": "c1", "schema_name": "raw_x"}])
        assert c.name == "c1"

    def test_empty_input(self) -> None:
        assert classify_fivetran_sources([]) == []


class TestFilterByLayer:
    def test_filters_and_preserves_order(self) -> None:
        items = [
            LayerClassification(Layer.STAGING, Vendor.DBT, "a"),
            LayerClassification(Layer.MART, Vendor.DBT, "b"),
            LayerClassification(Layer.STAGING, Vendor.DBT, "c"),
        ]
        out = filter_by_layer(items, Layer.STAGING)
        assert [c.name for c in out] == ["a", "c"]

    def test_no_match_returns_empty(self) -> None:
        items = [LayerClassification(Layer.STAGING, Vendor.DBT, "a")]
        assert filter_by_layer(items, Layer.MART) == []
