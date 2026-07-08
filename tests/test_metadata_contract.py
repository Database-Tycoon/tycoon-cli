from __future__ import annotations

import pytest

from tycoon.core.events import DbtRunCompleted, RunCompleted, RunStarted
from tycoon.core.metadata import EventFilter


@pytest.fixture(params=["duckdb_file"])
def backend(request, tmp_path):
    if request.param == "duckdb_file":
        from tycoon.metadata_backends.duckdb_file import DuckDBFileBackend
        with DuckDBFileBackend(tmp_path / ".tycoon" / "metadata.duckdb") as b:
            yield b


def test_append_and_query_basic(backend):
    event = RunStarted(source_id="chess", runtime_id="dlt-managed")
    backend.append_event(event)
    events = backend.query_events()
    assert len(events) == 1
    assert events[0].source_id == "chess"


def test_query_run_completed_with_rows_loaded(backend):
    event = RunCompleted(
        source_id="chess",
        runtime_id="dlt-managed",
        rows_loaded={"games": 123},
    )
    backend.append_event(event)
    results = backend.query_events(EventFilter(event_type="run_completed"))
    assert len(results) == 1
    assert results[0].rows_loaded == {"games": 123}


def test_append_and_query_dbt_run_completed(backend):
    event = DbtRunCompleted(
        source_id="dbt",
        runtime_id="dbt",
        command="build",
        target="dev",
        models_run=3,
    )
    backend.append_event(event)
    results = backend.query_events(EventFilter(event_type="dbt_run_completed"))
    assert len(results) == 1
    assert results[0].models_run == 3


def test_filter_by_source_id(backend):
    backend.append_event(RunStarted(source_id="chess", runtime_id="dlt-managed"))
    backend.append_event(RunStarted(source_id="github", runtime_id="dlt-managed"))
    results = backend.query_events(EventFilter(source_id="chess"))
    assert len(results) == 1
    assert results[0].source_id == "chess"


def test_upsert_and_read_snapshot(backend):
    backend.upsert_snapshot("schema", "chess", {"tables": ["games"]})
    result = backend.read_snapshot("schema", "chess")
    assert result == {"tables": ["games"]}


def test_upsert_overwrites_snapshot(backend):
    backend.upsert_snapshot("schema", "chess", {"tables": ["games"]})
    backend.upsert_snapshot("schema", "chess", {"tables": ["games", "players"]})
    result = backend.read_snapshot("schema", "chess")
    assert result == {"tables": ["games", "players"]}


def test_read_nonexistent_snapshot_returns_none(backend):
    result = backend.read_snapshot("schema", "nonexistent")
    assert result is None
