"""Steps that run after a load skip a MotherDuck raw database instead of assuming a local file."""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock

import duckdb
import pytest

from tycoon.commands import sources as sources_cmd
from tycoon.config import TycoonConfig
from tycoon.ingestion import runner
from tycoon.ingestion.runner import run_source
from tycoon.project import SourceConfig


@pytest.fixture(autouse=True)
def _never_reach_motherduck(monkeypatch):
    """Unit tests must not open md: connections (no token means a browser sign-in prompt)."""
    real = duckdb.connect

    def guarded(database=":memory:", *args, **kwargs):
        assert not str(database).startswith(("md:", "motherduck:")), f"unit test opened {database}"
        return real(database, *args, **kwargs)

    monkeypatch.setattr(duckdb, "connect", guarded)


def _project(tmp_path, raw: str) -> TycoonConfig:
    (tmp_path / "tycoon.yml").write_text(
        f"name: t\ndatabase:\n  raw: '{raw}'\n  warehouse: 'md:t'\nsources:\n  s:\n    type: rest_api\n    schema: raw_s\n"
    )
    (tmp_path / "dbt_project").mkdir()
    return TycoonConfig(project_root=tmp_path)


class TestRunnerPostLoad:
    @pytest.fixture
    def calls(self, monkeypatch):
        calls = {"legacy_warning": 0, "capture": 0}
        pipeline = MagicMock()
        pipeline.run.return_value = SimpleNamespace(raise_on_failed_jobs=lambda: None)
        source = MagicMock()
        monkeypatch.setattr(runner.dlt, "pipeline", MagicMock(return_value=pipeline))
        monkeypatch.setattr(runner, "_NATIVE_BUILDERS", {"filesystem": lambda _cfg: source})
        monkeypatch.setattr(runner, "_complete_run", lambda *a, **k: None)
        monkeypatch.setattr(runner, "_emit_event_safe", lambda *a, **k: None)
        monkeypatch.setattr(runner, "_unmatched_local_globs", lambda *a: [])

        def count_legacy_warning(*a):
            calls["legacy_warning"] += 1

        monkeypatch.setattr(runner, "_warn_if_legacy_filesystem_table_exists", count_legacy_warning)

        def count_capture(*a):
            calls["capture"] += 1

        monkeypatch.setattr("tycoon.observability.capture_dlt_safe", count_capture)
        monkeypatch.setattr("tycoon.observability.capture_dlt_trace_safe", lambda *a, **k: None)
        monkeypatch.setattr("tycoon.scaffolding.rill_generator.refresh_usage_dashboards", lambda **k: None)
        monkeypatch.setenv("MOTHERDUCK_TOKEN", "not-a-real-token")
        monkeypatch.setattr("tycoon.ingestion.destination._has_pyarrow", lambda: True)
        return calls

    def _run(self, raw):
        run_source("s", SourceConfig(type="filesystem", schema="raw_s"), raw)

    def test_motherduck_raw_skips_the_legacy_table_warning_and_the_capture(self, calls):
        self._run("md:t_raw")
        assert calls == {"legacy_warning": 0, "capture": 0}

    def test_local_raw_keeps_both_steps(self, calls, tmp_path):
        self._run(tmp_path / "raw.duckdb")
        assert calls == {"legacy_warning": 1, "capture": 1}


class TestAutoScaffold:
    def test_motherduck_raw_skips_with_a_note(self, tmp_path, monkeypatch, capsys):
        cfg = _project(tmp_path, "md:t_raw")
        generate = MagicMock()
        monkeypatch.setattr("tycoon.scaffolding.dbt_generator.generate_staging_models", generate)

        sources_cmd._maybe_auto_scaffold("s", cfg.sources["s"], cfg=cfg, scaffold=True)

        generate.assert_not_called()
        assert "database.raw is MotherDuck" in capsys.readouterr().out

    def test_local_raw_still_scaffolds(self, tmp_path, monkeypatch):
        cfg = _project(tmp_path, "data/raw.duckdb")
        generate = MagicMock(return_value=SimpleNamespace(generated=[]))
        monkeypatch.setattr("tycoon.scaffolding.dbt_generator.generate_staging_models", generate)

        sources_cmd._maybe_auto_scaffold("s", cfg.sources["s"], cfg=cfg, scaffold=True)

        assert generate.call_args.kwargs["raw_db_path"] == tmp_path / "data" / "raw.duckdb"


class TestAnalyze:
    @pytest.fixture
    def project(self, tmp_path, monkeypatch):
        _project(tmp_path, "md:t_raw")
        monkeypatch.chdir(tmp_path)

    @pytest.mark.parametrize("argv", [["data", "analyze", "s"], ["data", "analyze", "--all"]])
    def test_motherduck_raw_exits_one_with_a_clear_message(self, project, cli_runner, argv):
        from tycoon.cli import app

        result = cli_runner.invoke(app, argv)

        assert result.exit_code == 1, result.output
        assert "data analyze reads a local raw file, and database.raw is MotherDuck." in " ".join(result.output.split())


def test_unused_ducklake_module_is_gone():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("tycoon.ingestion.ducklake_config")
