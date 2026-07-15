from __future__ import annotations

import json
from typing import get_args

from tycoon.core.events import DbtRunCompleted, Event, RunCompleted


def test_run_completed_row_counts():
    e = RunCompleted(
        source_id="chess",
        runtime_id="dlt-managed",
        rows_loaded={"games": 123},
        tables_created=["games"],
    )
    assert e.rows_loaded["games"] == 123
    assert e.tables_created == ["games"]
    data = json.loads(e.model_dump_json())
    assert data["rows_loaded"]["games"] == 123


def test_dbt_run_completed_round_trip():
    e = DbtRunCompleted(
        source_id="dbt",
        runtime_id="dbt",
        command="build",
        target="dev",
        models_run=5,
        models_errored=0,
        duration_seconds=4.2,
    )
    restored = DbtRunCompleted.model_validate_json(e.model_dump_json())
    assert restored.models_run == 5


def test_event_union_includes_all_types():
    type_names = {t.__name__ for t in get_args(get_args(Event)[0])}
    assert "RunCompleted" in type_names
    assert "DbtRunCompleted" in type_names
