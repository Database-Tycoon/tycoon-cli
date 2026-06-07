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


class TestBuildRestApiSource:
    """Regression tests for issue #32: rest_api source build broke because
    `tycoon data sources add rest_api` writes a flat config to tycoon.yml,
    but dlt's `rest_api_source` requires the wrapped RESTAPIConfig shape."""

    def test_normalize_wraps_flat_base_url_under_client(self):
        from tycoon.ingestion.runner import _normalize_rest_api_config

        out = _normalize_rest_api_config(
            {
                "base_url": "https://pokeapi.co/api/v2/",
                "resources": "pokemon,berry,type",
            }
        )
        assert out["client"] == {"base_url": "https://pokeapi.co/api/v2/"}
        assert "base_url" not in out
        assert out["resources"] == ["pokemon", "berry", "type"]

    def test_normalize_passes_through_already_wrapped_config(self):
        """Hand-authored / pre-wrapped shapes shouldn't be re-wrapped."""
        from tycoon.ingestion.runner import _normalize_rest_api_config

        already_wrapped = {
            "client": {"base_url": "https://api.example.com", "auth": {"token": "x"}},
            "resources": [{"name": "users", "endpoint": "users"}],
        }
        out = _normalize_rest_api_config(already_wrapped)
        assert out["client"]["base_url"] == "https://api.example.com"
        assert out["client"]["auth"] == {"token": "x"}
        # resources list passed through unchanged
        assert out["resources"] == [{"name": "users", "endpoint": "users"}]

    def test_normalize_handles_list_resources(self):
        """Resources arriving as a list (hand-authored) stay a list."""
        from tycoon.ingestion.runner import _normalize_rest_api_config

        out = _normalize_rest_api_config(
            {"base_url": "https://x", "resources": ["a", "b"]}
        )
        assert out["resources"] == ["a", "b"]

    def test_normalize_drops_empty_resource_entries(self):
        """`resources: 'a,,b, ,'` shouldn't produce empty strings."""
        from tycoon.ingestion.runner import _normalize_rest_api_config

        out = _normalize_rest_api_config(
            {"base_url": "https://x", "resources": "a,,b, ,"}
        )
        assert out["resources"] == ["a", "b"]

    def test_build_rest_api_source_constructs_dlt_source(self):
        """End-to-end: the flat config that tycoon.yml stores produces a
        valid dlt source. Before the fix, dlt's validator raised
        `Path '.': missing required fields {'client'}`."""
        from tycoon.ingestion.runner import _build_rest_api_source
        from tycoon.project import SourceConfig

        sc = SourceConfig(
            type="rest_api",
            schema="raw_pokeapi",
            config={
                "base_url": "https://pokeapi.co/api/v2/",
                "resources": "pokemon,berry,type",
            },
        )
        source = _build_rest_api_source(sc)
        resource_names = {r.name for r in source.resources.values()}
        assert {"pokemon", "berry", "type"}.issubset(resource_names)


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


# ---------------------------------------------------------------------------
# dlt write_disposition contract — replace / append / merge
# ---------------------------------------------------------------------------


class TestWriteDispositionContract:
    """Lock in the row-level contract of dlt's three write modes against
    DuckDB. These tests use small in-process resources (no network) so
    a regression in either dlt or duckdb-destination wiring shows up
    immediately, not only when running the live e2e suite.

    The modes:

    - replace : second load wipes the table and writes only the new rows.
    - append  : second load adds rows on top of the first; primary key
                duplication is allowed.
    - merge   : second load upserts on the declared primary key; second
                batch's values win for matching keys, novel keys land.
    """

    def _run_two_loads(
        self,
        tmp_path,
        *,
        write_disposition: str,
        primary_key: str | None = None,
    ) -> list[tuple]:
        """Load two batches with the given disposition; return the final
        (id, name) rows ordered by id."""
        import dlt

        first = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        second = [{"id": 2, "name": "B-updated"}, {"id": 3, "name": "c"}]

        kwargs: dict = {"name": "items", "write_disposition": write_disposition}
        if primary_key is not None:
            kwargs["primary_key"] = primary_key

        @dlt.resource(**kwargs)
        def items_first():
            yield from first

        @dlt.resource(**kwargs)
        def items_second():
            yield from second

        db_path = tmp_path / "raw.duckdb"
        pipeline = dlt.pipeline(
            pipeline_name="write_mode_test",
            destination=dlt.destinations.duckdb(str(db_path)),
            dataset_name="raw_test",
            pipelines_dir=str(tmp_path / "_dlt"),
        )
        pipeline.run(items_first())
        pipeline.run(items_second())

        import duckdb

        con = duckdb.connect(str(db_path), read_only=True)
        try:
            return sorted(
                con.execute("SELECT id, name FROM raw_test.items").fetchall(),
                key=lambda r: (r[0], r[1]),
            )
        finally:
            con.close()

    def test_replace_keeps_only_second_batch(self, tmp_path):
        rows = self._run_two_loads(tmp_path, write_disposition="replace")
        assert rows == [(2, "B-updated"), (3, "c")], rows

    def test_append_keeps_both_batches(self, tmp_path):
        rows = self._run_two_loads(tmp_path, write_disposition="append")
        # 2 + 2 = 4 rows total. Two rows have id=2 (one from each batch);
        # we sort by (id, name) so the order is deterministic.
        assert rows == [(1, "a"), (2, "B-updated"), (2, "b"), (3, "c")], rows

    def test_merge_upserts_on_primary_key(self, tmp_path):
        rows = self._run_two_loads(
            tmp_path, write_disposition="merge", primary_key="id"
        )
        # id=1 carries from batch 1; id=2 wins from batch 2; id=3 added.
        assert rows == [(1, "a"), (2, "B-updated"), (3, "c")], rows


class TestGoogleSheetsShim:
    """The Google Sheets ``_run.py`` shim (#52) is downloaded on demand, so it
    can't be imported normally. We exec the exact shim string that ships in
    ``_SHIMS`` against a mocked ``dlt`` + ``google_sheets`` to verify it
    translates tycoon's flat config into ``google_spreadsheet`` kwargs.
    """

    def _exec_shim(self, monkeypatch, *, config, max_records=None, creds_file=None):
        """Run the shim with fake ``dlt``/``google_sheets`` modules injected.

        Returns the kwargs the shim passed to ``google_spreadsheet`` plus the
        fake source object (so callers can assert ``add_limit`` behaviour).
        """
        import sys
        import types

        captured: dict = {}

        class _FakeSource:
            def __init__(self):
                self.limit = None

            def add_limit(self, n):
                self.limit = n
                return self

        fake_source = _FakeSource()

        def google_spreadsheet(**kwargs):
            captured["kwargs"] = kwargs
            return fake_source

        fake_gs = types.ModuleType("google_sheets")
        fake_gs.google_spreadsheet = google_spreadsheet

        class _FakePipeline:
            def run(self, source):
                captured["ran"] = source
                return "LOAD_INFO"

        fake_dlt = types.ModuleType("dlt")
        fake_dlt.pipeline = lambda **kw: _FakePipeline()
        fake_dlt.destinations = types.SimpleNamespace(
            duckdb=lambda path: ("duckdb", path)
        )

        monkeypatch.setitem(sys.modules, "google_sheets", fake_gs)
        monkeypatch.setitem(sys.modules, "dlt", fake_dlt)

        from tycoon.ingestion.source_manager import _SHIMS

        ns: dict = {}
        exec(_SHIMS["google_sheets"], ns)

        source_config = types.SimpleNamespace(config=config, schema_name="raw_google_sheets")
        pipeline, load_info = ns["run_pipeline"](
            "my-sheet", source_config, "/tmp/raw.duckdb", max_records=max_records
        )
        return captured, fake_source, load_info

    def test_passes_spreadsheet_and_range_subset(self, monkeypatch):
        captured, _src, _ = self._exec_shim(
            monkeypatch,
            config={
                "spreadsheet_url_or_id": "https://docs.google.com/spreadsheets/d/ABC/edit",
                "range_names": "Sheet1, Q1 2026!A1:F",
            },
        )
        kwargs = captured["kwargs"]
        assert kwargs["spreadsheet_url_or_id"].endswith("/d/ABC/edit")
        # Comma-split, trimmed.
        assert kwargs["range_names"] == ["Sheet1", "Q1 2026!A1:F"]

    def test_blank_range_omits_range_names(self, monkeypatch):
        """Empty range → load all sheets: omit the kwarg, let dlt default."""
        captured, _src, _ = self._exec_shim(
            monkeypatch,
            config={"spreadsheet_url_or_id": "ABC", "range_names": ""},
        )
        assert "range_names" not in captured["kwargs"]

    def test_service_account_json_loaded_as_dict(self, monkeypatch, tmp_path):
        key_file = tmp_path / "sa.json"
        key_file.write_text('{"type": "service_account", "project_id": "demo"}')
        captured, _src, _ = self._exec_shim(
            monkeypatch,
            config={"spreadsheet_url_or_id": "ABC", "credentials_path": str(key_file)},
        )
        assert captured["kwargs"]["credentials"] == {
            "type": "service_account",
            "project_id": "demo",
        }

    def test_missing_creds_path_falls_back_to_dlt(self, monkeypatch):
        """A blank/absent key path passes no ``credentials`` — dlt then resolves
        from env / secrets.toml (the ADC / OAuth path)."""
        captured, _src, _ = self._exec_shim(
            monkeypatch,
            config={"spreadsheet_url_or_id": "ABC", "credentials_path": ""},
        )
        assert "credentials" not in captured["kwargs"]

    def test_max_records_applies_limit(self, monkeypatch):
        _captured, source, _ = self._exec_shim(
            monkeypatch,
            config={"spreadsheet_url_or_id": "ABC"},
            max_records=50,
        )
        assert source.limit == 50
