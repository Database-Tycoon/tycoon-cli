"""The raw database's dlt destination: a MotherDuck target lands in MotherDuck, a path stays a file."""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import duckdb
import pytest

from tycoon.ingestion import runner
from tycoon.ingestion.destination import raw_destination
from tycoon.ingestion.runner import IngestionError, run_source
from tycoon.ingestion.source_manager import _SHIMS
from tycoon.project import SourceConfig


@pytest.fixture(autouse=True)
def _never_reach_motherduck(request, monkeypatch):
    """Unit tests must not open md: connections (no token means a browser sign-in prompt)."""
    if request.node.get_closest_marker("e2e"):
        return
    real = duckdb.connect

    def guarded(database=":memory:", *args, **kwargs):
        assert not str(database).startswith(("md:", "motherduck:")), f"unit test opened {database}"
        return real(database, *args, **kwargs)

    monkeypatch.setattr(duckdb, "connect", guarded)


@pytest.fixture
def md_token(monkeypatch):
    monkeypatch.setattr("tycoon.ingestion.destination._has_pyarrow", lambda: True)
    monkeypatch.setenv("MOTHERDUCK_TOKEN", "not-a-real-token")
    monkeypatch.delenv("motherduck_token", raising=False)


@pytest.fixture
def no_md_token(monkeypatch):
    monkeypatch.delenv("MOTHERDUCK_TOKEN", raising=False)
    monkeypatch.delenv("motherduck_token", raising=False)


class TestRawDestination:
    @pytest.mark.parametrize("target", ["md:x", "motherduck:x"])
    def test_motherduck_targets_get_the_motherduck_destination(self, target, md_token):
        dest = raw_destination(target)
        assert dest.destination_name == "motherduck"
        assert dest.config_params["credentials"] == "md:x"

    @pytest.mark.parametrize("target", ["data/raw.duckdb", "/abs/md:backup/raw.duckdb", "C:\\data\\raw.duckdb"])
    def test_paths_get_the_duckdb_destination(self, target, no_md_token):
        assert raw_destination(target).destination_name == "duckdb"

    def test_path_object_is_accepted(self, tmp_path, no_md_token):
        assert raw_destination(tmp_path / "raw.duckdb").destination_name == "duckdb"

    def test_missing_token_names_the_variable(self, no_md_token):
        with pytest.raises(IngestionError, match="MOTHERDUCK_TOKEN"):
            raw_destination("md:x")

    def test_missing_pyarrow_says_what_to_install(self, md_token, monkeypatch):
        monkeypatch.setattr("tycoon.ingestion.destination._has_pyarrow", lambda: False)
        with pytest.raises(IngestionError, match="needs pyarrow"):
            raw_destination("md:x")

    def test_token_in_the_query_string_is_enough(self, no_md_token, monkeypatch):
        monkeypatch.setattr("tycoon.ingestion.destination._has_pyarrow", lambda: True)
        assert raw_destination("md:x?motherduck_token=abc").destination_name == "motherduck"


class TestRunSource:
    def _run(self, monkeypatch, raw_db_path):
        pipeline = MagicMock()
        pipeline.run.return_value = SimpleNamespace(raise_on_failed_jobs=lambda: None)
        factory = MagicMock(return_value=pipeline)
        monkeypatch.setattr(runner.dlt, "pipeline", factory)
        monkeypatch.setattr(runner, "_NATIVE_BUILDERS", {"fake": lambda _cfg: object()})
        for hook in ("_complete_run", "_capture_and_refresh_safe", "_emit_event_safe"):
            monkeypatch.setattr(runner, hook, lambda *a, **k: None)
        run_source("src", SourceConfig(type="fake", schema="raw_src"), raw_db_path)
        return factory.call_args.kwargs

    def test_md_raw_reaches_dlt_pipeline_with_motherduck(self, monkeypatch, md_token):
        kwargs = self._run(monkeypatch, "md:x_raw")
        assert kwargs["destination"].destination_name == "motherduck"
        assert kwargs["dataset_name"] == "raw_src"

    def test_long_prefix_reaches_dlt_pipeline_with_motherduck(self, monkeypatch, md_token):
        assert self._run(monkeypatch, "motherduck:x_raw")["destination"].destination_name == "motherduck"

    def test_local_path_still_reaches_dlt_pipeline_with_duckdb(self, monkeypatch, tmp_path, no_md_token):
        kwargs = self._run(monkeypatch, tmp_path / "raw.duckdb")
        assert kwargs["destination"].destination_name == "duckdb"
        assert kwargs["destination"].config_params["credentials"] == str(tmp_path / "raw.duckdb")

    def test_md_raw_without_token_is_a_clear_error_not_a_trace(self, monkeypatch, no_md_token):
        with pytest.raises(IngestionError, match="MOTHERDUCK_TOKEN is not set in the environment"):
            self._run(monkeypatch, "md:x_raw")

    @pytest.mark.parametrize("name", ["nyc-dot", "mta-gtfs", "mta-bus-speeds"])
    def test_demo_pipelines_stay_local_only(self, name, monkeypatch, md_token):
        monkeypatch.setattr(runner, "_emit_event_safe", lambda *a, **k: None)
        with pytest.raises(IngestionError, match="only writes a local raw DuckDB file"):
            run_source(name, SourceConfig(type="rest_api", schema="raw"), "md:x_raw")

    def test_missing_database_says_how_to_create_it(self, monkeypatch, md_token):
        factory = MagicMock()
        factory.return_value.run.side_effect = RuntimeError('Failed to attach: no database/share named "x_raw" found')
        monkeypatch.setattr(runner.dlt, "pipeline", factory)
        monkeypatch.setattr(runner, "_NATIVE_BUILDERS", {"fake": lambda _cfg: object()})
        monkeypatch.setattr(runner, "_emit_event_safe", lambda *a, **k: None)
        with pytest.raises(IngestionError, match='CREATE DATABASE "x_raw"'):
            run_source("src", SourceConfig(type="fake", schema="raw_src"), "md:x_raw")

    def test_catalog_shim_written_before_motherduck_support_is_refused(self, monkeypatch, tmp_path, md_token):
        pkg = tmp_path / "github"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "_run.py").write_text("dest = dlt.destinations.duckdb(str(raw_db_path))\n")
        monkeypatch.setattr(runner, "resolve_sources_dir", lambda _root: tmp_path)
        monkeypatch.setattr(runner, "_emit_event_safe", lambda *a, **k: None)
        with pytest.raises(IngestionError, match="before MotherDuck support"):
            run_source("gh", SourceConfig(type="github", schema="raw_gh"), "md:x_raw")


class TestRenderedErrors:
    """The CLI prints errors through Rich, which eats `[...]` as markup."""

    def test_missing_pyarrow_command_survives_rendering(self, tmp_path, monkeypatch, cli_runner, md_token):
        from tycoon.cli import app

        (tmp_path / "tycoon.yml").write_text(
            "name: t\ndatabase:\n  raw: 'md:t_raw'\n  warehouse: 'md:t'\nsources:\n  s:\n    type: rest_api\n    schema: raw_s\n"
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("tycoon.ingestion.destination._has_pyarrow", lambda: False)
        monkeypatch.setattr(runner, "_emit_event_safe", lambda *a, **k: None)

        result = cli_runner.invoke(app, ["data", "sources", "run", "s"])

        assert result.exit_code == 1
        assert "pip install pyarrow" in " ".join(result.output.split())


class TestCatalogShimTarget:
    """A catalog `_run.py` outlives upgrades and may be hand-edited, so what it receives must not change."""

    SHIM = (
        "class _Info:\n"
        "    def raise_on_failed_jobs(self):\n"
        "        pass\n\n"
        "RECEIVED = []\n\n"
        "def run_pipeline(name, source_config, raw_db_path, max_records=None):\n"
        "    RECEIVED.append(raw_db_path)\n"
        "    raw_db_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "    return object(), _Info()\n"
    )

    @pytest.fixture
    def sources_dir(self, monkeypatch, tmp_path):
        pkg = tmp_path / "sources" / "hubspot"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        (pkg / "_run.py").write_text(self.SHIM)
        monkeypatch.setattr(runner, "resolve_sources_dir", lambda _root: tmp_path / "sources")
        monkeypatch.setattr(runner, "_complete_run", lambda *a, **k: None)
        monkeypatch.setattr(runner, "_capture_and_refresh_safe", lambda *a, **k: None)
        monkeypatch.setattr(runner, "_emit_event_safe", lambda *a, **k: None)
        monkeypatch.syspath_prepend(str(tmp_path / "sources"))
        monkeypatch.delitem(sys.modules, "hubspot", raising=False)
        monkeypatch.delitem(sys.modules, "hubspot._run", raising=False)
        yield tmp_path / "sources"
        sys.modules.pop("hubspot", None)
        sys.modules.pop("hubspot._run", None)

    def test_local_project_keeps_receiving_a_path(self, sources_dir, tmp_path):
        raw = tmp_path / "data" / "raw.duckdb"
        run_source("hs", SourceConfig(type="hubspot", schema="raw_hs"), str(raw))
        received = sys.modules["hubspot._run"].RECEIVED
        assert received == [raw]
        assert isinstance(received[0], Path)
        assert raw.parent.is_dir()

    def test_unreadable_shim_for_a_motherduck_raw_names_the_file(self, sources_dir, monkeypatch, md_token):
        (sources_dir / "hubspot" / "_run.py").unlink()
        monkeypatch.setattr(runner, "is_source_installed", lambda *a, **k: True)
        with pytest.raises(IngestionError, match="missing, unreadable, or was written before"):
            run_source("hs", SourceConfig(type="hubspot", schema="raw_hs"), "md:x_raw")


def test_every_shim_builds_its_destination_through_the_helper():
    assert _SHIMS
    for source_type, shim in _SHIMS.items():
        assert "destination=raw_destination(raw_db_path)" in shim, source_type
        assert "dlt.destinations.duckdb" not in shim, source_type


class TestSourcesCommands:
    @pytest.fixture
    def project(self, tmp_path, monkeypatch):
        (tmp_path / "tycoon.yml").write_text(
            "name: t\ndatabase:\n  raw: 'md:t_raw'\n  warehouse: 'md:t'\nsources:\n  s:\n    type: rest_api\n    schema: raw_s\n"
        )
        monkeypatch.chdir(tmp_path)
        calls: list[object] = []

        def fake_run_source(**kwargs):
            calls.append(kwargs["raw_db_path"])
            return None, None

        monkeypatch.setattr("tycoon.ingestion.runner.run_source", fake_run_source)
        return calls

    @pytest.mark.parametrize(
        "argv",
        [
            ["data", "sources", "run", "s"],
            ["data", "sources", "run-all"],
            ["data", "run-all", "--skip-transform"],
        ],
    )
    def test_commands_hand_the_runner_the_raw_target(self, project, cli_runner, argv):
        from tycoon.cli import app

        result = cli_runner.invoke(app, argv)
        assert result.exit_code == 0, result.output
        assert project == ["md:t_raw"]


@pytest.mark.e2e
@pytest.mark.skipif(not os.environ.get("MOTHERDUCK_TOKEN"), reason="MOTHERDUCK_TOKEN not set")
@pytest.mark.parametrize("scheme", ["md", "motherduck"])
def test_rows_land_in_a_real_motherduck_database(scheme, tmp_path, monkeypatch):
    pytest.importorskip("pyarrow", reason="dlt's MotherDuck loader needs pyarrow (dlt[parquet])")
    import dlt

    import tycoon.config as cfg_mod

    prefix = "tycoon_e2e_scratch_"
    name = f"{prefix}a{secrets.token_hex(3)}"
    monkeypatch.setenv("DLT_DATA_DIR", str(tmp_path / "dlt"))
    monkeypatch.setattr(cfg_mod, "config", cfg_mod.TycoonConfig(project_root=tmp_path))

    @dlt.resource(name="items")
    def items():
        yield [{"id": 1}, {"id": 2}]

    monkeypatch.setattr(runner, "_NATIVE_BUILDERS", {"fake": lambda _cfg: items()})
    admin = duckdb.connect("md:")
    assert name.startswith(prefix)
    admin.execute(f'CREATE DATABASE "{name}"')
    try:
        run_source("src", SourceConfig(type="fake", schema="raw_src"), f"{scheme}:{name}")
        assert admin.execute(f'SELECT count(*) FROM "{name}".raw_src.items').fetchone() == (2,)
    finally:
        assert name.startswith(prefix)
        admin.execute(f'DROP DATABASE IF EXISTS "{name}"')
        admin.close()
