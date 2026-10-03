"""Issue #240: a run that loaded zero rows is recorded as such in the ledger,
and `data status` / `data history` report it as a warning rather than a
healthy sync."""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from tycoon.cli import app
from tycoon.core.events import RunCompleted, RunStarted
from tycoon.ingestion.runner import _build_run_completed, run_source
from tycoon.project import ResourceConfig, SourceConfig
from tycoon.utils.console import console
from tests.test_history import _seed_events, _write_tycoon_yml
from tests.test_templates_e2e import _init_template, _rebind_config, _seed_widgets_csv


def _fake_pipeline(row_counts: dict[str, int] | None, write_disposition: str | dict = "replace") -> SimpleNamespace:
    normalize_info = SimpleNamespace(row_counts=row_counts)
    hints = {"files": {"write_disposition": write_disposition}, "_dlt_pipeline_state": {"write_disposition": "append"}}
    extract_info = SimpleNamespace(metrics={"1": [{"hints": hints}]})
    return SimpleNamespace(
        last_trace=SimpleNamespace(last_normalize_info=normalize_info, last_extract_info=extract_info)
    )


def _write_csv(path: Path, rows: int) -> None:
    lines = ["id,value"] + [f"{i},v{i}" for i in range(1, rows + 1)]
    path.write_text("\n".join(lines) + "\n")


def _ledger(meta: Path) -> list:
    from tycoon.metadata_backends.duckdb_file import DuckDBFileBackend

    with DuckDBFileBackend(meta, read_only=True) as b:
        return b.query_events()


@pytest.fixture
def ledger_path(tmp_path: Path, monkeypatch) -> Iterator[Path]:
    """Point the runner's metadata backend at a scratch ledger."""
    import tycoon.observability as observability

    meta = tmp_path / ".tycoon" / "metadata.duckdb"
    monkeypatch.setattr(observability, "metadata_db_path", lambda _root: meta)
    yield meta


@pytest.fixture
def pipeline_cleanup() -> Iterator[list[str]]:
    names: list[str] = []
    yield names
    for name in names:
        shutil.rmtree(Path.home() / ".dlt" / "pipelines" / name, ignore_errors=True)


class TestRunCompletedEvent:
    def test_ledger_rows_written_before_the_fields_existed_still_load(self, tmp_path):
        from tycoon.metadata_backends.duckdb_file import _EVENT_ADAPTER

        stored = (
            '{"event_id": "e1", "event_type": "run_completed", "source_id": "files", '
            '"runtime_id": "dlt-managed", "timestamp": "2026-09-01T10:00:00Z", '
            '"load_id": "123", "duration_seconds": 1.5, "rows_loaded": {"files": 10}, '
            '"tables_created": ["files"], "tables_updated": []}'
        )

        event = _EVENT_ADAPTER.validate_json(stored)

        assert isinstance(event, RunCompleted)
        assert event.zero_rows is False
        assert event.warnings == []

    @pytest.mark.parametrize("row_counts", [None, {}, {"files": 0}, {"_dlt_loads": 1, "files": 0}])
    def test_empty_or_all_zero_counts_are_flagged(self, row_counts):
        event = _build_run_completed("files", _fake_pipeline(row_counts), SimpleNamespace(loads_ids=["1"]), 0.1)

        assert event.zero_rows is True

    def test_loaded_rows_are_not_flagged(self):
        event = _build_run_completed("files", _fake_pipeline({"files": 2, "other": 3}), None, 0.1)

        assert event.zero_rows is False

    def test_empty_replace_table_is_flagged_when_another_table_loaded(self):
        """Rows in a sibling table don't hide a replace table that was emptied."""
        event = _build_run_completed("files", _fake_pipeline({"files": 0, "other": 3}), None, 0.1)

        assert event.zero_rows is True
        assert event.warnings == ["'files' loaded 0 rows with write_disposition 'replace', so its table is now empty."]

    @pytest.mark.parametrize(
        "write_disposition", ["append", "merge", {"disposition": "merge", "strategy": "delete-insert"}]
    )
    def test_zero_rows_without_replace_are_not_flagged(self, write_disposition):
        """Append and merge runs with no new records leave the table as it was."""
        event = _build_run_completed("files", _fake_pipeline({}, write_disposition), None, 0.1)

        assert event.zero_rows is False

    def test_dict_replace_disposition_is_flagged(self):
        event = _build_run_completed("files", _fake_pipeline({}, {"disposition": "replace"}), None, 0.1)

        assert event.zero_rows is True

    def test_unmatched_glob_is_flagged_without_replace(self):
        warning = "'files': no files matched glob 'nomatch*.csv' under 'data'."
        event = _build_run_completed("files", _fake_pipeline({}, "append"), None, 0.1, [warning])

        assert event.zero_rows is True


class TestRealDltPipelines:
    """The flag against a real dlt pipeline loading into a temp DuckDB."""

    @staticmethod
    def _pipeline(tmp_path: Path, name: str):
        import dlt

        return dlt.pipeline(
            pipeline_name=name,
            destination=dlt.destinations.duckdb(str(tmp_path / f"{name}.duckdb")),
            dataset_name="raw",
            pipelines_dir=str(tmp_path / "pipelines"),
        )

    def test_incremental_merge_with_no_new_records_is_not_flagged(self, tmp_path):
        import dlt

        @dlt.resource(name="orders", write_disposition="merge", primary_key="id")
        def orders(updated=dlt.sources.incremental("updated")):
            yield from [{"id": 1, "updated": 1}, {"id": 2, "updated": 2}]

        pipeline = self._pipeline(tmp_path, "gh240_incremental")
        first = _build_run_completed("orders", pipeline, pipeline.run(orders()), 0.1)
        load_info = pipeline.run(orders())
        second = _build_run_completed("orders", pipeline, load_info, 0.1)

        assert first.zero_rows is False
        assert second.rows_loaded == {}
        assert second.zero_rows is False

    def test_replace_with_no_records_is_flagged(self, tmp_path):
        import dlt

        @dlt.resource(name="orders", write_disposition="replace")
        def orders(rows):
            yield from rows

        pipeline = self._pipeline(tmp_path, "gh240_replace")
        pipeline.run(orders([{"id": 1}]))
        load_info = pipeline.run(orders([]))
        event = _build_run_completed("orders", pipeline, load_info, 0.1)

        assert event.zero_rows is True

    def test_empty_replace_resource_beside_one_that_loaded_is_flagged(self, tmp_path):
        """A replace dimension emptied in the same run as an append fact table that loaded (review of #299)."""
        import dlt

        @dlt.resource(name="res_a", write_disposition="replace")
        def res_a():
            yield from []

        @dlt.resource(name="res_b", write_disposition="append")
        def res_b():
            yield from [{"id": 1}, {"id": 2}]

        pipeline = self._pipeline(tmp_path, "gh240_mixed")
        event = _build_run_completed("mixed", pipeline, pipeline.run([res_a(), res_b()]), 0.1)

        assert event.rows_loaded == {"res_b": 2}
        assert event.zero_rows is True
        assert any("'res_a' loaded 0 rows" in w for w in event.warnings)

    def test_quiet_append_beside_a_replace_that_loaded_is_not_flagged(self, tmp_path):
        import dlt

        @dlt.resource(name="dim", write_disposition="replace")
        def dim():
            yield from [{"id": 1}]

        @dlt.resource(name="facts", write_disposition="append")
        def facts():
            yield from []

        pipeline = self._pipeline(tmp_path, "gh240_quiet_append")
        event = _build_run_completed("mixed", pipeline, pipeline.run([dim(), facts()]), 0.1)

        assert event.zero_rows is False
        assert event.warnings == []

    def test_empty_replace_resource_with_its_own_table_name_is_flagged(self, tmp_path):
        """Row counts are keyed by the normalized table name, not the resource name."""
        import dlt

        @dlt.resource(name="Customers", table_name="DimCustomers", write_disposition="replace")
        def customers():
            yield from []

        @dlt.resource(name="orders", write_disposition="append")
        def orders():
            yield from [{"id": 1}]

        pipeline = self._pipeline(tmp_path, "gh240_table_name")
        event = _build_run_completed("mixed", pipeline, pipeline.run([customers(), orders()]), 0.1)

        assert event.zero_rows is True
        assert any("'dim_customers' loaded 0 rows" in w for w in event.warnings)

    def test_replace_parent_with_rows_is_not_flagged_by_its_child_tables(self, tmp_path):
        import dlt

        @dlt.resource(name="orders", write_disposition="replace")
        def orders():
            yield from [{"id": 1, "lines": [{"sku": "a"}, {"sku": "b"}]}]

        pipeline = self._pipeline(tmp_path, "gh240_nested")
        event = _build_run_completed("orders", pipeline, pipeline.run(orders()), 0.1)

        assert event.zero_rows is False


class TestRunnerLedger:
    def test_nothing_to_load_records_a_zero_row_completion(self, tmp_path, ledger_path, pipeline_cleanup):
        name = "test_gh240_ledger_empty"
        pipeline_cleanup.append(name)
        (tmp_path / "input").mkdir()
        config = SourceConfig(
            type="filesystem",
            schema="raw_files",
            config={"path": str(tmp_path / "input"), "file_glob": "nomatch*.csv"},
        )

        _pipeline, load_info = run_source(name, config, raw_db_path=tmp_path / "raw.duckdb")

        assert load_info is None
        events = _ledger(ledger_path)
        assert [type(e) for e in events] == [RunStarted, RunCompleted]
        completed = events[1]
        assert completed.zero_rows is True
        assert completed.rows_loaded == {}
        assert len(completed.warnings) == 1
        assert "'nomatch*.csv'" in completed.warnings[0]

    def test_partial_run_keeps_rows_and_names_the_empty_glob(self, tmp_path, ledger_path, pipeline_cleanup):
        name = "test_gh240_ledger_partial"
        pipeline_cleanup.append(name)
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        _write_csv(input_dir / "games.csv", rows=2)
        config = SourceConfig(
            type="filesystem",
            schema="raw_ledger_partial",
            resources=[
                ResourceConfig(table_name="test_gh240_games", path=str(input_dir), file_glob="games.csv"),
                ResourceConfig(table_name="test_gh240_players", path=str(input_dir), file_glob="nomatch*.csv"),
            ],
        )

        run_source(name, config, raw_db_path=tmp_path / "raw.duckdb")

        completed = [e for e in _ledger(ledger_path) if isinstance(e, RunCompleted)]
        assert len(completed) == 1
        assert completed[0].zero_rows is False
        assert completed[0].rows_loaded == {"test_gh240_games": 2}
        assert len(completed[0].warnings) == 1
        assert "test_gh240_players" in completed[0].warnings[0]


@pytest.fixture
def status_project(tmp_path: Path, monkeypatch) -> Path:
    from tycoon.commands import history as history_mod
    from tycoon.commands import status as status_mod
    from tycoon.config import TycoonConfig

    _write_tycoon_yml(tmp_path, with_sources=True)
    cfg = TycoonConfig(project_root=tmp_path)
    monkeypatch.setattr(history_mod, "config", cfg)
    monkeypatch.setattr(status_mod, "config", cfg)
    monkeypatch.setattr(console, "width", 200)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _healthy_then_empty() -> list[RunCompleted]:
    return [
        RunCompleted(
            source_id="src_a",
            runtime_id="dlt-managed",
            load_id="healthy-001",
            rows_loaded={"t": 10},
            timestamp=datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
        ),
        RunCompleted(
            source_id="src_a",
            runtime_id="dlt-managed",
            load_id="",
            event_id="emptyrun-0001",
            zero_rows=True,
            warnings=["'src_a': no files matched glob 'nomatch*.csv' under 'data/input'."],
            timestamp=datetime(2026, 9, 2, 10, 0, tzinfo=UTC),
        ),
    ]


class TestStatusZeroRows:
    def test_zero_row_run_does_not_refresh_last_sync(self, status_project, cli_runner):
        _seed_events(status_project, _healthy_then_empty())

        result = cli_runner.invoke(app, ["data", "status"])

        assert result.exit_code == 0
        row = next(line for line in result.stdout.splitlines() if "src_a" in line)
        assert "2026-09-01 10:00" in row
        assert "2026-09-02" not in row
        assert "last run loaded 0 rows" in result.stdout
        assert "nomatch*.csv" in result.stdout

    def test_only_zero_row_runs_read_as_never_synced(self, status_project, cli_runner):
        _seed_events(status_project, _healthy_then_empty()[1:])

        result = cli_runner.invoke(app, ["data", "status"])

        assert result.exit_code == 0
        assert "never" in result.stdout
        assert "last run loaded 0 rows" in result.stdout

    def test_healthy_run_after_an_empty_one_clears_the_warning(self, status_project, cli_runner):
        healthy_again = RunCompleted(
            source_id="src_a",
            runtime_id="dlt-managed",
            load_id="healthy-002",
            rows_loaded={"t": 12},
            timestamp=datetime(2026, 9, 3, 10, 0, tzinfo=UTC),
        )
        _seed_events(status_project, [*_healthy_then_empty(), healthy_again])

        result = cli_runner.invoke(app, ["data", "status"])

        assert result.exit_code == 0
        assert "2026-09-03 10:00" in result.stdout
        assert "0 rows" not in result.stdout

    def test_quiet_incremental_run_advances_last_sync(self, status_project, cli_runner):
        """An unflagged run with no new records is a normal sync."""
        quiet = RunCompleted(
            source_id="src_a",
            runtime_id="dlt-managed",
            load_id="quiet-001",
            timestamp=datetime(2026, 9, 2, 10, 0, tzinfo=UTC),
        )
        _seed_events(status_project, [_healthy_then_empty()[0], quiet])

        result = cli_runner.invoke(app, ["data", "status"])

        assert result.exit_code == 0
        row = next(line for line in result.stdout.splitlines() if "src_a" in line)
        assert "2026-09-02 10:00" in row
        assert "0 rows" not in result.stdout


class TestHistoryZeroRows:
    def test_list_styles_zero_row_run_as_a_warning(self, status_project, cli_runner):
        _seed_events(status_project, _healthy_then_empty())

        result = cli_runner.invoke(app, ["data", "history"])

        assert result.exit_code == 0
        empty_line = next(line for line in result.stdout.splitlines() if "emptyrun" in line)
        healthy_line = next(line for line in result.stdout.splitlines() if "healthy-" in line)
        assert "✓" not in empty_line
        assert "!" in empty_line
        assert "nothing loaded" in empty_line
        assert "✓" in healthy_line

    def test_show_prints_zero_row_status_and_warnings(self, status_project, cli_runner):
        _seed_events(status_project, _healthy_then_empty())

        result = cli_runner.invoke(app, ["data", "history", "show", "emptyrun"])

        assert result.exit_code == 0
        assert "zero rows" in result.stdout
        assert "nomatch*.csv" in result.stdout


def _healthy_then_partly_empty() -> list[RunCompleted]:
    """A replace table got 0 rows in a run where another table loaded."""
    healthy, _ = _healthy_then_empty()
    return [
        healthy,
        RunCompleted(
            source_id="src_a",
            runtime_id="dlt-managed",
            load_id="",
            event_id="partrun-0001",
            rows_loaded={"facts": 2},
            zero_rows=True,
            warnings=["'dim' loaded 0 rows with write_disposition 'replace', so its table is now empty."],
            timestamp=datetime(2026, 9, 2, 10, 0, tzinfo=UTC),
        ),
    ]


class TestPartlyEmptyRun:
    """A run that loaded rows but left a replace table with none isn't labelled 'nothing loaded'."""

    def test_status_names_the_empty_table_without_claiming_nothing_loaded(self, status_project, cli_runner):
        _seed_events(status_project, _healthy_then_partly_empty())

        result = cli_runner.invoke(app, ["data", "status"])

        assert result.exit_code == 0
        assert "a table in the last run got 0 rows" in result.stdout
        assert "last run loaded 0 rows" not in result.stdout
        assert "'dim' loaded 0 rows" in result.stdout

    def test_history_shows_rows_and_the_empty_table(self, status_project, cli_runner):
        _seed_events(status_project, _healthy_then_partly_empty())

        listing = cli_runner.invoke(app, ["data", "history"])
        shown = cli_runner.invoke(app, ["data", "history", "show", "partrun"])

        part_line = next(line for line in listing.stdout.splitlines() if "partrun" in line)
        assert "!" in part_line
        assert "2 rows, a table got 0" in part_line
        assert "nothing loaded" not in part_line
        assert "a table got zero rows" in shown.stdout


@pytest.mark.offline_e2e
def test_emptied_input_shows_as_zero_rows_in_status_and_history(cli_runner, tmp_path, monkeypatch):
    project = tmp_path / "csv-import-zero-rows"
    project.mkdir()
    monkeypatch.chdir(project)
    _init_template(cli_runner, "csv-import")
    input_dir = project / "data" / "input"
    _seed_widgets_csv(input_dir, count=5)
    _rebind_config(monkeypatch, project)
    from tycoon.commands import history as history_mod
    from tycoon.commands import status as status_mod
    from tycoon.config import TycoonConfig

    cfg = TycoonConfig(project_root=project)
    monkeypatch.setattr(history_mod, "config", cfg)
    monkeypatch.setattr(status_mod, "config", cfg)
    monkeypatch.setattr(console, "width", 200)
    try:
        assert cli_runner.invoke(app, ["data", "sources", "run", "files"]).exit_code == 0
        for csv in input_dir.glob("*.csv"):
            csv.unlink()
        assert cli_runner.invoke(app, ["data", "sources", "run", "files"]).exit_code == 0

        status = cli_runner.invoke(app, ["data", "status"])
        history = cli_runner.invoke(app, ["data", "history"])

        assert "last run loaded 0 rows" in status.stdout
        assert "nothing loaded" in history.stdout
    finally:
        shutil.rmtree(Path.home() / ".dlt" / "pipelines" / "files", ignore_errors=True)
