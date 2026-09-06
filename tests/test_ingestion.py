"""Ingestion module import and decorator tests.

These tests verify that pipeline modules can be imported and that dlt
decorators are properly applied. They do NOT call any external APIs.
"""

from __future__ import annotations

import importlib

import pytest


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

        out = _normalize_rest_api_config({"base_url": "https://x", "resources": ["a", "b"]})
        assert out["resources"] == ["a", "b"]

    def test_normalize_drops_empty_resource_entries(self):
        """`resources: 'a,,b, ,'` shouldn't produce empty strings."""
        from tycoon.ingestion.runner import _normalize_rest_api_config

        out = _normalize_rest_api_config({"base_url": "https://x", "resources": "a,,b, ,"})
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

    def _make_source_config(self, file_glob: str) -> SourceConfig:
        from tycoon.project import SourceConfig

        return SourceConfig(
            type="filesystem",
            schema="raw_files",
            config={"path": "data/input", "file_glob": file_glob},
        )

    def test_csv_glob_returns_dlt_source(self):
        """CSV glob should pipe through read_csv, producing a transformer resource.

        gh-223: the flat shape now goes through _build_filesystem_resource
        with a placeholder name (renamed again by run_source() after the
        tycoon source's own name), so the resource name is the placeholder,
        not dlt's default "read_csv" — only is_transformer distinguishes
        the dispatch here.
        """
        from tycoon.ingestion.runner import _build_filesystem_source

        source_config = self._make_source_config("*.csv")
        result = _build_filesystem_source(source_config)
        assert result is not None
        assert result.is_transformer is True

    def test_parquet_glob_returns_dlt_source(self):
        """Parquet glob should pipe through read_parquet, producing a transformer resource."""
        from tycoon.ingestion.runner import _build_filesystem_source

        source_config = self._make_source_config("*.parquet")
        result = _build_filesystem_source(source_config)
        assert result is not None
        assert result.is_transformer is True

    def test_unknown_glob_returns_raw_filesystem_source(self):
        """An unrecognised glob should fall back to the raw filesystem resource."""
        from tycoon.ingestion.runner import _build_filesystem_source

        source_config = self._make_source_config("**/*.json")
        result = _build_filesystem_source(source_config)
        assert result is not None
        # Raw filesystem source is not a transformer
        assert result.is_transformer is False

    def test_resources_list_returns_one_named_resource_per_entry(self):
        """gh-224/gh-225: a multi-resource source builds one resource per
        entry, each renamed to its own table_name, not the shared source name."""
        from tycoon.ingestion.runner import _build_filesystem_source
        from tycoon.project import ResourceConfig, SourceConfig

        source_config = SourceConfig(
            type="filesystem",
            schema="raw_arcade",
            resources=[
                ResourceConfig(table_name="arcade_games", path="data/input", file_glob="games.csv"),
                ResourceConfig(table_name="sensor_readings", path="/tmp/data", file_glob="**/*.parquet"),
            ],
        )
        result = _build_filesystem_source(source_config)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].name == "arcade_games"
        assert result[1].name == "sensor_readings"


class TestFilesystemConfigValidation:
    """gh-223: filesystem sources fail loudly on missing config instead of
    silently defaulting, and warn (without failing) on a local glob that
    matches nothing."""

    def test_missing_path_raises_instead_of_defaulting_to_cwd(self):
        """Previously: cfg.get("bucket_url", cfg.get("path", ".")) silently
        scanned the current working directory when neither key was set."""
        from tycoon.ingestion.runner import IngestionError, _build_filesystem_source
        from tycoon.project import SourceConfig

        source_config = SourceConfig(type="filesystem", schema="raw_files", config={"file_glob": "*.csv"})
        with pytest.raises(IngestionError, match="path"):
            _build_filesystem_source(source_config)

    def test_resource_missing_path_raises(self):
        from tycoon.ingestion.runner import IngestionError, _build_filesystem_source
        from tycoon.project import ResourceConfig, SourceConfig

        source_config = SourceConfig(
            type="filesystem",
            schema="raw_arcade",
            resources=[ResourceConfig(table_name="games", path="", file_glob="games.csv")],
        )
        with pytest.raises(IngestionError, match="games"):
            _build_filesystem_source(source_config)

    def test_local_glob_with_no_matches_warns_not_fails(self, tmp_path, capsys):
        """A typo'd glob shouldn't look identical to a genuinely empty source."""
        from tycoon.ingestion.runner import _build_filesystem_source
        from tycoon.project import SourceConfig

        empty_dir = tmp_path / "input"
        empty_dir.mkdir()

        source_config = SourceConfig(
            type="filesystem",
            schema="raw_files",
            config={"path": str(empty_dir), "file_glob": "*.csv"},
        )
        result = _build_filesystem_source(source_config)  # must not raise
        assert result is not None
        assert "no files matched" in capsys.readouterr().out.lower()

    def test_local_glob_with_matches_does_not_warn(self, tmp_path, capsys):
        from tycoon.ingestion.runner import _build_filesystem_source
        from tycoon.project import SourceConfig

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "data.csv").write_text("id\n1\n")

        source_config = SourceConfig(
            type="filesystem",
            schema="raw_files",
            config={"path": str(input_dir), "file_glob": "*.csv"},
        )
        _build_filesystem_source(source_config)
        assert "no files matched" not in capsys.readouterr().out.lower()

    def test_remote_bucket_url_skips_the_local_glob_check(self, capsys):
        """S3/GCS/Azure aren't supported yet (see the parent tracking issue's
        deferred scope) — the local-glob check must not misfire on them."""
        from tycoon.ingestion.runner import _build_filesystem_source
        from tycoon.project import SourceConfig

        source_config = SourceConfig(
            type="filesystem",
            schema="raw_files",
            config={"path": "s3://some-bucket/data", "file_glob": "*.csv"},
        )
        _build_filesystem_source(source_config)  # must not raise or warn
        assert "no files matched" not in capsys.readouterr().out.lower()


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
            assert native in CATALOG, f"{native} should still appear in the catalog for browsing"


class TestUnexpandedEnvVarCheck:
    """Regression test for Stephen's review on gh-224 / PR #230: a resource's
    own path/file_glob can carry an unexpanded ${VAR} just like the flat
    config shape, and it needs the same diagnostic — otherwise a typo'd or
    unset env var silently loads zero rows with no error anywhere."""

    def test_flat_config_value_detected(self):
        from tycoon.ingestion.runner import _check_unexpanded_env_vars
        from tycoon.project import SourceConfig

        source_config = SourceConfig(
            type="rest_api",
            schema="raw_api",
            config={"base_url": "${API_BASE_URL}"},
        )
        assert _check_unexpanded_env_vars(source_config) == [("base_url", "${API_BASE_URL}")]

    def test_resource_path_and_glob_detected(self):
        from tycoon.ingestion.runner import _check_unexpanded_env_vars
        from tycoon.project import ResourceConfig, SourceConfig

        source_config = SourceConfig(
            type="filesystem",
            schema="raw_files",
            resources=[
                ResourceConfig(table_name="widgets", path="${DATA_DIR}/widgets", file_glob="*.csv"),
                ResourceConfig(table_name="gadgets", path="/tmp/gadgets", file_glob="${GADGET_GLOB}"),
            ],
        )
        bad_pairs = _check_unexpanded_env_vars(source_config)
        assert ("resources[0].path", "${DATA_DIR}") in bad_pairs
        assert ("resources[1].file_glob", "${GADGET_GLOB}") in bad_pairs

    def test_no_bad_pairs_when_fully_expanded(self):
        from tycoon.ingestion.runner import _check_unexpanded_env_vars
        from tycoon.project import ResourceConfig, SourceConfig

        source_config = SourceConfig(
            type="filesystem",
            schema="raw_files",
            resources=[ResourceConfig(table_name="widgets", path="/data/widgets", file_glob="*.csv")],
        )
        assert _check_unexpanded_env_vars(source_config) == []

    def test_run_source_warns_for_unexpanded_var_on_native_dispatch(self, tmp_path, capsys):
        """End-to-end: before this fix, only the catalog dispatch path
        (_run_catalog) called _check_unexpanded_env_vars, so a native
        builder (filesystem, rest_api, sql_database) never warned about an
        unexpanded ${VAR} at all, flat config included. Uses the flat shape
        here since it's what this layer's filesystem builder reads; a
        resources-shaped source runs through the same warning call.

        The bad var is scoped to a bounded glob (*.csv under a
        nonexistent literal directory), not "**/*", so a miss resolves to
        zero matches instead of walking the whole working tree.
        """
        import shutil
        from pathlib import Path

        from tycoon.ingestion.runner import run_source
        from tycoon.project import SourceConfig

        raw_db_path = tmp_path / "raw.duckdb"
        pipeline_name = "test_gh224_unexpanded_env_var"
        try:
            source_config = SourceConfig(
                type="filesystem",
                schema="raw_test",
                config={"path": "${UNSET_TYCOON_TEST_VAR}", "file_glob": "*.csv"},
            )
            run_source(pipeline_name, source_config, raw_db_path=raw_db_path)

            out = capsys.readouterr().out.lower()
            assert "config key 'path'" in out
            assert "${unset_tycoon_test_var}" in out
        finally:
            shutil.rmtree(Path.home() / ".dlt" / "pipelines" / pipeline_name, ignore_errors=True)


class TestFilesystemResourceNaming:
    """Regression test for issue #222: two filesystem sources sharing a
    schema, each pointed at a different file, used to collide into one
    table because dlt's read_csv() transformer always names its resource
    "read_csv" regardless of which tycoon source built it. run_source()
    now renames the resource after the tycoon source's own name."""

    def test_two_filesystem_sources_land_in_separate_tables(self, tmp_path):
        import shutil
        from pathlib import Path

        import duckdb

        from tycoon.ingestion.runner import run_source
        from tycoon.project import SourceConfig

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "a.csv").write_text("id,value\n1,foo\n2,bar\n")
        (input_dir / "b.csv").write_text("id,value\n1,baz\n")

        raw_db_path = tmp_path / "raw.duckdb"
        pipeline_names = ["test_gh222_source_a", "test_gh222_source_b"]

        try:
            for name, glob in zip(pipeline_names, ["a.csv", "b.csv"]):
                source_config = SourceConfig(
                    type="filesystem",
                    schema="raw_test",
                    config={"path": str(input_dir), "file_glob": glob},
                )
                run_source(name, source_config, raw_db_path=raw_db_path)

            con = duckdb.connect(str(raw_db_path), read_only=True)
            tables = {
                row[0]
                for row in con.sql(
                    "select table_name from information_schema.tables where table_schema = 'raw_test'"
                ).fetchall()
            }
            con.close()

            assert "test_gh222_source_a" in tables
            assert "test_gh222_source_b" in tables
        finally:
            for name in pipeline_names:
                shutil.rmtree(Path.home() / ".dlt" / "pipelines" / name, ignore_errors=True)


class TestLegacyFilesystemTableWarning:
    """Regression test for Stephen's review on #229: existing projects on
    the old flat config shape silently start writing to a new table name
    after the gh-222 fix, while their dbt models keep selecting the old,
    now-frozen table. Since that can't be fixed automatically (the old
    table is data, not something safe to drop unprompted), run_source()
    warns whenever the legacy table is still present."""

    def test_warns_when_legacy_table_present(self, tmp_path, capsys):
        import shutil
        from pathlib import Path

        import duckdb

        from tycoon.ingestion.runner import run_source
        from tycoon.project import SourceConfig

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "widgets.csv").write_text("id,value\n1,foo\n")

        raw_db_path = tmp_path / "raw.duckdb"

        # Simulate a project that ingested before the gh-222 fix: the
        # pre-fix generic table already exists in the target schema.
        con = duckdb.connect(str(raw_db_path))
        con.execute("CREATE SCHEMA raw_test")
        con.execute("CREATE TABLE raw_test.read_csv (id INTEGER, value VARCHAR)")
        con.execute("INSERT INTO raw_test.read_csv VALUES (1, 'stale')")
        con.close()

        pipeline_name = "test_gh222_legacy_warning"
        try:
            source_config = SourceConfig(
                type="filesystem",
                schema="raw_test",
                config={"path": str(input_dir), "file_glob": "widgets.csv"},
            )
            run_source(pipeline_name, source_config, raw_db_path=raw_db_path)

            out = capsys.readouterr().out.lower()
            assert "raw_test.read_csv" in out
            assert pipeline_name.lower() in out
        finally:
            shutil.rmtree(Path.home() / ".dlt" / "pipelines" / pipeline_name, ignore_errors=True)

    def test_no_warning_when_no_legacy_table(self, tmp_path, capsys):
        import shutil
        from pathlib import Path

        from tycoon.ingestion.runner import run_source
        from tycoon.project import SourceConfig

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "widgets.csv").write_text("id,value\n1,foo\n")

        raw_db_path = tmp_path / "raw.duckdb"
        pipeline_name = "test_gh222_no_legacy_warning"
        try:
            source_config = SourceConfig(
                type="filesystem",
                schema="raw_test",
                config={"path": str(input_dir), "file_glob": "widgets.csv"},
            )
            run_source(pipeline_name, source_config, raw_db_path=raw_db_path)

            out = capsys.readouterr().out.lower()
            assert "still exists from before" not in out
        finally:
            shutil.rmtree(Path.home() / ".dlt" / "pipelines" / pipeline_name, ignore_errors=True)


class TestMultiResourceFilesystemSource:
    """Regression test for issue #225: a single source with multiple
    resources runs as one pipeline and lands each resource in its own
    table, using each resource's own table_name."""

    def test_two_resources_one_source_land_in_separate_tables(self, tmp_path):
        import shutil
        from pathlib import Path

        import duckdb

        from tycoon.ingestion.runner import run_source
        from tycoon.project import ResourceConfig, SourceConfig

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "games.csv").write_text("id,value\n1,foo\n2,bar\n")
        (input_dir / "players.csv").write_text("id,value\n1,baz\n")

        raw_db_path = tmp_path / "raw.duckdb"
        pipeline_name = "test_gh225_arcade"

        try:
            source_config = SourceConfig(
                type="filesystem",
                schema="raw_test",
                resources=[
                    ResourceConfig(table_name="test_gh225_games", path=str(input_dir), file_glob="games.csv"),
                    ResourceConfig(table_name="test_gh225_players", path=str(input_dir), file_glob="players.csv"),
                ],
            )
            run_source(pipeline_name, source_config, raw_db_path=raw_db_path)

            con = duckdb.connect(str(raw_db_path), read_only=True)
            tables = {
                row[0]
                for row in con.sql(
                    "select table_name from information_schema.tables where table_schema = 'raw_test'"
                ).fetchall()
            }
            games_rows = con.execute('SELECT count(*) FROM raw_test."test_gh225_games"').fetchone()
            players_rows = con.execute('SELECT count(*) FROM raw_test."test_gh225_players"').fetchone()
            con.close()

            assert "test_gh225_games" in tables
            assert "test_gh225_players" in tables
            assert games_rows is not None and games_rows[0] == 2
            assert players_rows is not None and players_rows[0] == 1
        finally:
            shutil.rmtree(Path.home() / ".dlt" / "pipelines" / pipeline_name, ignore_errors=True)


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
        rows = self._run_two_loads(tmp_path, write_disposition="merge", primary_key="id")
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
        fake_dlt.destinations = types.SimpleNamespace(duckdb=lambda path: ("duckdb", path))

        monkeypatch.setitem(sys.modules, "google_sheets", fake_gs)
        monkeypatch.setitem(sys.modules, "dlt", fake_dlt)

        from tycoon.ingestion.source_manager import _SHIMS

        ns: dict = {}
        exec(_SHIMS["google_sheets"], ns)

        source_config = types.SimpleNamespace(config=config, schema_name="raw_google_sheets")
        pipeline, load_info = ns["run_pipeline"]("my-sheet", source_config, "/tmp/raw.duckdb", max_records=max_records)
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
