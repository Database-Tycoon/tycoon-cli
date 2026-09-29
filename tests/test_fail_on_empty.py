"""Issue #240: opt-in --fail-on-empty turns an empty glob match, or a run
that loads zero rows, into a non-zero exit recorded as RunFailed."""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest

from tycoon.cli import app
from tycoon.core.events import RunCompleted, RunFailed, RunStarted
from tycoon.ingestion import runner
from tycoon.ingestion.runner import IngestionError, run_source
from tycoon.project import ResourceConfig, SourceConfig
from tests.test_templates_e2e import _init_template, _rebind_config, _seed_widgets_csv


def _write_csv(path: Path, rows: int) -> None:
    lines = ["id,value"] + [f"{i},v{i}" for i in range(1, rows + 1)]
    path.write_text("\n".join(lines) + "\n")


def _ledger(meta: Path) -> list:
    from tycoon.metadata_backends.duckdb_file import DuckDBFileBackend

    with DuckDBFileBackend(meta, read_only=True) as b:
        return b.query_events()


@pytest.fixture
def ledger_path(tmp_path: Path, monkeypatch) -> Path:
    import tycoon.observability as observability

    meta = tmp_path / ".tycoon" / "metadata.duckdb"
    monkeypatch.setattr(observability, "metadata_db_path", lambda _root: meta)
    return meta


@pytest.fixture
def pipeline_cleanup() -> Iterator[list[str]]:
    names: list[str] = []
    yield names
    for name in names:
        shutil.rmtree(Path.home() / ".dlt" / "pipelines" / name, ignore_errors=True)


def _arcade(input_dir: Path, players_glob: str) -> SourceConfig:
    return SourceConfig(
        type="filesystem",
        schema="raw_fail_on_empty",
        resources=[
            ResourceConfig(table_name="test_gh240_foe_games", path=str(input_dir), file_glob="games.csv"),
            ResourceConfig(table_name="test_gh240_foe_players", path=str(input_dir), file_glob=players_glob),
        ],
    )


class TestRunSourceFailOnEmpty:
    def test_unmatched_glob_fails_before_loading_and_records_run_failed(self, tmp_path, ledger_path, pipeline_cleanup):
        name = "test_gh240_foe_partial"
        pipeline_cleanup.append(name)
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        _write_csv(input_dir / "games.csv", rows=2)

        with pytest.raises(IngestionError, match=r"nomatch\*\.csv.*--fail-on-empty"):
            run_source(name, _arcade(input_dir, "nomatch*.csv"), tmp_path / "raw.duckdb", fail_on_empty=True)

        events = _ledger(ledger_path)
        assert [type(e) for e in events] == [RunStarted, RunFailed]
        assert "nomatch*.csv" in events[1].error
        assert not (tmp_path / "raw.duckdb").exists()

    def test_zero_row_load_fails_after_the_run(self, tmp_path, ledger_path, monkeypatch):
        extract_info = SimpleNamespace(metrics={"1": [{"hints": {"issues": {"write_disposition": "replace"}}}]})
        trace = SimpleNamespace(last_normalize_info=SimpleNamespace(row_counts={}), last_extract_info=extract_info)
        pipeline = SimpleNamespace(last_trace=trace)
        load_info = SimpleNamespace(loads_ids=["1"])
        monkeypatch.setattr(runner, "_run_catalog", lambda *_args, **_kwargs: (pipeline, load_info))
        monkeypatch.setattr(runner, "_capture_and_refresh_safe", lambda *_args, **_kwargs: None)

        with pytest.raises(IngestionError, match="loaded 0 rows"):
            run_source("gh", SourceConfig(type="github", schema="raw_gh"), tmp_path / "raw.duckdb", fail_on_empty=True)

        assert [type(e) for e in _ledger(ledger_path)] == [RunStarted, RunFailed]

    def test_incremental_run_with_no_new_records_passes(self, tmp_path, ledger_path, monkeypatch):
        """A quiet incremental merge is a normal sync, not an empty run."""
        import dlt

        @dlt.resource(name="issues", write_disposition="merge", primary_key="id")
        def issues(updated=dlt.sources.incremental("updated")):
            yield from [{"id": 1, "updated": 1}, {"id": 2, "updated": 2}]

        pipeline = dlt.pipeline(
            pipeline_name="gh240_foe_incremental",
            destination=dlt.destinations.duckdb(str(tmp_path / "incremental.duckdb")),
            dataset_name="raw_gh",
            pipelines_dir=str(tmp_path / "pipelines"),
        )
        pipeline.run(issues())
        monkeypatch.setattr(runner, "_run_catalog", lambda *_args, **_kwargs: (pipeline, pipeline.run(issues())))
        monkeypatch.setattr(runner, "_capture_and_refresh_safe", lambda *_args, **_kwargs: None)

        run_source("gh", SourceConfig(type="github", schema="raw_gh"), tmp_path / "raw.duckdb", fail_on_empty=True)

        events = _ledger(ledger_path)
        assert [type(e) for e in events] == [RunStarted, RunCompleted]
        assert events[1].rows_loaded == {}
        assert events[1].zero_rows is False

    def test_default_still_records_zero_row_completion(self, tmp_path, ledger_path, pipeline_cleanup):
        name = "test_gh240_foe_default"
        pipeline_cleanup.append(name)
        (tmp_path / "input").mkdir()

        _pipeline, load_info = run_source(name, _arcade(tmp_path / "input", "nomatch*.csv"), tmp_path / "raw.duckdb")

        assert load_info is None
        events = _ledger(ledger_path)
        assert [type(e) for e in events] == [RunStarted, RunCompleted]
        assert events[1].zero_rows is True

    def test_matching_globs_pass_under_fail_on_empty(self, tmp_path, ledger_path, pipeline_cleanup):
        name = "test_gh240_foe_healthy"
        pipeline_cleanup.append(name)
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        _write_csv(input_dir / "games.csv", rows=2)
        _write_csv(input_dir / "players.csv", rows=3)

        _pipeline, load_info = run_source(
            name, _arcade(input_dir, "players.csv"), tmp_path / "raw.duckdb", fail_on_empty=True
        )

        assert load_info is not None
        completed = [e for e in _ledger(ledger_path) if isinstance(e, RunCompleted)]
        assert len(completed) == 1
        assert completed[0].zero_rows is False


@pytest.fixture
def emptied_csv_project(cli_runner, tmp_path, monkeypatch) -> Iterator[Path]:
    """A csv-import project that loaded once, then had its inputs deleted."""
    project = tmp_path / "csv-import-fail-on-empty"
    project.mkdir()
    monkeypatch.chdir(project)
    _init_template(cli_runner, "csv-import")
    input_dir = project / "data" / "input"
    _seed_widgets_csv(input_dir, count=5)
    _rebind_config(monkeypatch, project)
    assert cli_runner.invoke(app, ["data", "sources", "run", "files"]).exit_code == 0
    for csv in input_dir.glob("*.csv"):
        csv.unlink()
    yield project
    shutil.rmtree(Path.home() / ".dlt" / "pipelines" / "files", ignore_errors=True)


def _last_event(project: Path):
    return _ledger(project / ".tycoon" / "metadata.duckdb")[-1]


@pytest.mark.offline_e2e
class TestFailOnEmptyCli:
    @pytest.mark.parametrize(
        "command",
        [
            ["data", "sources", "run", "files", "--fail-on-empty"],
            ["data", "sources", "run-all", "--fail-on-empty"],
            ["data", "run-all", "--skip-transform", "--fail-on-empty"],
        ],
    )
    def test_empty_glob_exits_non_zero(self, cli_runner, emptied_csv_project, command):
        result = cli_runner.invoke(app, command)

        assert result.exit_code == 1
        assert "--fail-on-empty" in result.output
        assert isinstance(_last_event(emptied_csv_project), RunFailed)

    @pytest.mark.parametrize(
        "command",
        [
            ["data", "sources", "run", "files"],
            ["data", "sources", "run-all"],
            ["data", "run-all", "--skip-transform"],
        ],
    )
    def test_without_the_flag_exit_code_is_unchanged(self, cli_runner, emptied_csv_project, command):
        result = cli_runner.invoke(app, command)

        assert result.exit_code == 0
        assert "nothing to load" in result.output
        last = _last_event(emptied_csv_project)
        assert isinstance(last, RunCompleted)
        assert last.zero_rows is True
