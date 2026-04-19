"""Smoke tests for the Dagster orchestration layer.

These tests don't run Dagster jobs — they verify that the ``Definitions``
object loads without ``DagsterInvalidDefinitionError`` and has the
expected shape. That class of bug (issue #4 in the legacy repo) is the
main failure mode we want CI to catch at import time.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


class TestDefinitionsImport:
    """`tycoon.orchestration.definitions` must import cleanly."""

    def test_defs_importable(self):
        """Import should not raise DagsterInvalidDefinitionError."""
        from tycoon.orchestration.definitions import defs

        assert defs is not None

    def test_defs_has_rill_asset(self):
        """rill_build is always in the asset graph — it has no dynamic deps."""
        from tycoon.orchestration.definitions import all_assets

        names = [getattr(a, "__name__", None) for a in all_assets]
        # rill_build is a plain function-asset; its identity survives
        assert any("rill_build" in str(a) or n == "rill_build" for a, n in zip(all_assets, names))

    def test_defs_has_dlt_resource(self):
        """The dlt resource is always configured, even without sources."""
        from tycoon.orchestration.definitions import resources

        assert "dlt" in resources

    def test_all_assets_is_a_list(self):
        from tycoon.orchestration.definitions import all_assets

        assert isinstance(all_assets, list)


class TestBuildIngestionAssets:
    """`build_ingestion_assets` factory must handle present and absent configs."""

    def test_returns_empty_list_when_no_project_file(self, tmp_path: Path):
        """No tycoon.yml → no ingestion assets (CLI source repo case)."""
        from tycoon.orchestration.assets import ingestion as ingestion_mod

        # Point PROJECT_DIR at a dir without tycoon.yml
        with patch.object(ingestion_mod, "PROJECT_DIR", tmp_path):
            assets = ingestion_mod.build_ingestion_assets()
            assert assets == []

    def test_one_asset_per_source(self, tmp_path: Path):
        from tycoon.orchestration.assets import ingestion as ingestion_mod

        # Stand up a minimal tycoon.yml with two sources
        (tmp_path / "tycoon.yml").write_text(
            "name: test\n"
            "version: 0.1.0\n"
            "database:\n"
            "  raw: data/raw.duckdb\n"
            "  warehouse: data/warehouse.duckdb\n"
            "sources:\n"
            "  src_a:\n"
            "    type: rest_api\n"
            "    schema: raw_src_a\n"
            "  src_b:\n"
            "    type: rest_api\n"
            "    schema: raw_src_b\n"
        )

        with patch.object(ingestion_mod, "PROJECT_DIR", tmp_path):
            assets = ingestion_mod.build_ingestion_assets()
            assert len(assets) == 2

    def test_asset_name_dash_to_underscore(self, tmp_path: Path):
        """dlt source names can have dashes; asset keys must be valid Python identifiers."""
        from tycoon.orchestration.assets import ingestion as ingestion_mod

        (tmp_path / "tycoon.yml").write_text(
            "name: test\n"
            "version: 0.1.0\n"
            "database:\n"
            "  raw: data/raw.duckdb\n"
            "  warehouse: data/warehouse.duckdb\n"
            "sources:\n"
            "  my-dash-source:\n"
            "    type: rest_api\n"
            "    schema: raw_my_dash_source\n"
        )

        with patch.object(ingestion_mod, "PROJECT_DIR", tmp_path):
            assets = ingestion_mod.build_ingestion_assets()
            assert len(assets) == 1
            # The asset's key_prefix / name should use underscores
            asset_key = assets[0].keys_by_output_name["result"]
            assert "-" not in str(asset_key)


class TestResourceFactories:
    """Resource constructors should return valid Dagster resources without
    requiring the underlying service (dbt / dlt) to actually be reachable."""

    def test_dlt_resource_factory(self):
        from tycoon.orchestration.resources import get_dlt_resource

        r = get_dlt_resource()
        assert r is not None

    def test_dbt_resource_factory_returns_cli_resource(self):
        from dagster_dbt import DbtCliResource

        from tycoon.orchestration.resources import get_dbt_resource

        r = get_dbt_resource()
        assert isinstance(r, DbtCliResource)


class TestAssetJobSelection:
    """Regression cover for issue #13 (legacy): full_pipeline_job selection
    must mix AssetKeys and AssetsDefinitions cleanly without DagsterError."""

    def test_full_pipeline_job_defined_when_sources_and_dbt_present(self):
        """If both ingestion sources and dbt assets exist, the combo job
        should be present in `all_jobs` without raising.

        The CI source repo has no tycoon.yml, so `all_jobs` is empty; this
        test documents the invariant and asserts the list shape regardless.
        """
        from tycoon.orchestration.definitions import all_jobs

        assert isinstance(all_jobs, list)
        # Each job has a .name attribute
        for j in all_jobs:
            assert hasattr(j, "name")
