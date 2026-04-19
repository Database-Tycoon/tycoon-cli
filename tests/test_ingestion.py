"""Ingestion module import and decorator tests.

These tests verify that pipeline modules can be imported and that dlt
decorators are properly applied. They do NOT call any external APIs.
"""

from __future__ import annotations

import importlib


class TestNYCDotPipeline:

    def test_module_imports(self):
        mod = importlib.import_module("tycoon.ingestion.nyc_dot_pipeline")
        assert mod is not None

    def test_has_run_pipeline(self):
        from tycoon.ingestion import nyc_dot_pipeline

        assert hasattr(nyc_dot_pipeline, "run_pipeline")
        assert callable(nyc_dot_pipeline.run_pipeline)

    def test_has_dlt_source(self):
        from tycoon.ingestion import nyc_dot_pipeline

        # The source function should exist (name matches the @dlt.source decorator)
        assert hasattr(nyc_dot_pipeline, "nyc_dot_source")

    def test_has_dlt_resources(self):
        from tycoon.ingestion import nyc_dot_pipeline

        for name in ("traffic_speeds_nbe", "bus_lanes", "traffic_volume_counts"):
            assert hasattr(nyc_dot_pipeline, name), f"Missing resource: {name}"


class TestMTAPipeline:

    def test_module_imports(self):
        mod = importlib.import_module("tycoon.ingestion.mta_pipeline")
        assert mod is not None

    def test_has_run_pipeline(self):
        from tycoon.ingestion import mta_pipeline

        assert hasattr(mta_pipeline, "run_pipeline")
        assert callable(mta_pipeline.run_pipeline)

    def test_has_dlt_source(self):
        from tycoon.ingestion import mta_pipeline

        assert hasattr(mta_pipeline, "mta_source")

    def test_has_dlt_resources(self):
        from tycoon.ingestion import mta_pipeline

        for name in ("gtfs_routes", "gtfs_stops"):
            assert hasattr(mta_pipeline, name), f"Missing resource: {name}"


class TestMTABusSpeedsPipeline:

    def test_module_imports(self):
        mod = importlib.import_module("tycoon.ingestion.mta_bus_speeds_pipeline")
        assert mod is not None

    def test_has_run_pipeline(self):
        from tycoon.ingestion import mta_bus_speeds_pipeline

        assert hasattr(mta_bus_speeds_pipeline, "run_pipeline")
        assert callable(mta_bus_speeds_pipeline.run_pipeline)

    def test_has_dlt_source(self):
        from tycoon.ingestion import mta_bus_speeds_pipeline

        assert hasattr(mta_bus_speeds_pipeline, "mta_bus_speeds_source")

    def test_has_dlt_source_with_datasets(self):
        from tycoon.ingestion import mta_bus_speeds_pipeline

        # Resources are created dynamically inside the source generator,
        # not as module-level attributes. Verify the datasets dict instead.
        assert hasattr(mta_bus_speeds_pipeline, "MTA_BUS_SPEEDS_DATASETS")
        datasets = mta_bus_speeds_pipeline.MTA_BUS_SPEEDS_DATASETS
        assert "2023-2024" in datasets
        assert "2025" in datasets


class TestBuildFilesystemSource:
    """Unit tests for _build_filesystem_source glob-based dispatch."""

    def _make_source_config(self, file_glob: str) -> "SourceConfig":
        from tycoon.project import SourceConfig

        return SourceConfig(
            type="filesystem",
            schema="raw_files",
            config={"path": "data/input", "file_glob": file_glob},
        )

    def test_csv_glob_returns_dlt_source(self):
        """CSV glob should pipe through read_csv, producing a transformer resource."""
        from tycoon.ingestion.runner import _build_filesystem_source

        source_config = self._make_source_config("*.csv")
        result = _build_filesystem_source(source_config)
        assert result is not None
        # Piped sources are DltResource transformers; the name reflects read_csv
        assert result.is_transformer is True
        assert "csv" in result.name.lower()

    def test_parquet_glob_returns_dlt_source(self):
        """Parquet glob should pipe through read_parquet, producing a transformer resource."""
        from tycoon.ingestion.runner import _build_filesystem_source

        source_config = self._make_source_config("*.parquet")
        result = _build_filesystem_source(source_config)
        assert result is not None
        assert result.is_transformer is True
        assert "parquet" in result.name.lower()

    def test_unknown_glob_returns_raw_filesystem_source(self):
        """An unrecognised glob should fall back to the raw filesystem resource."""
        from tycoon.ingestion.runner import _build_filesystem_source

        source_config = self._make_source_config("**/*.json")
        result = _build_filesystem_source(source_config)
        assert result is not None
        # Raw filesystem source is not a transformer
        assert result.is_transformer is False
        assert result.name == "filesystem"


class TestRunSourceDispatch:
    """Regression: native source types (filesystem, rest_api, sql_database)
    must take precedence over the catalog dispatch.

    Catalog dispatch requires ``~/.tycoon/sources/<type>/`` to exist
    (populated by ``dlt init``). On a fresh machine or CI runner that
    directory doesn't exist, so catalog-path dispatch raises
    ``IngestionError("...not installed")`` before the native builder
    can take over. These types ship with dlt core — they don't need
    the catalog install step.
    """

    def test_filesystem_in_native_builders(self):
        """`filesystem` must be in _NATIVE_BUILDERS so catalog is bypassed."""
        from tycoon.ingestion.runner import _NATIVE_BUILDERS

        assert "filesystem" in _NATIVE_BUILDERS

    def test_rest_api_in_native_builders(self):
        from tycoon.ingestion.runner import _NATIVE_BUILDERS

        assert "rest_api" in _NATIVE_BUILDERS

    def test_sql_database_in_native_builders(self):
        from tycoon.ingestion.runner import _NATIVE_BUILDERS

        assert "sql_database" in _NATIVE_BUILDERS

    def test_native_types_also_in_catalog(self):
        """Sanity: native types are ALSO in the catalog (for browsing).
        The dispatch precedence — not the catalog registration — is what
        matters for correctness."""
        from tycoon.ingestion.catalog import CATALOG

        for native in ("rest_api", "filesystem"):
            assert native in CATALOG, (
                f"{native} should still appear in the catalog for browsing"
            )
