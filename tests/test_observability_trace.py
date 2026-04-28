"""Tests for dlt trace capture (v0.1.3 — observability v2a).

These tests exercise ``capture_dlt_trace_from_dict`` with a hand-built
trace dict that mirrors what ``PipelineTrace.asdict()`` produces on a real
run. Working from a dict avoids a hard dependency on dlt's internal
pickle format in the test fixtures.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import duckdb

from tycoon.observability import (
    capture_dlt_trace,
    capture_dlt_trace_from_dict,
    capture_dlt_trace_safe,
    ensure_schema,
    export_to_parquet,
    metadata_db_path,
)


def _sample_trace(
    transaction_id: str = "txn-001",
    pipeline_name: str = "sample_pipeline",
    step_exception: str | None = None,
) -> dict:
    """Hand-built trace dict in the shape of ``PipelineTrace.asdict()``."""
    started = datetime(2026, 4, 19, 10, 0, 0, tzinfo=timezone.utc)
    extract_end = datetime(2026, 4, 19, 10, 0, 5, tzinfo=timezone.utc)
    normalize_end = datetime(2026, 4, 19, 10, 0, 6, tzinfo=timezone.utc)
    load_end = datetime(2026, 4, 19, 10, 0, 8, tzinfo=timezone.utc)

    load_packages = [
        {
            "load_id": "1234567890.000001",
            "jobs": [
                {
                    "job_id": "widgets.abc.insert_values",
                    "table_name": "widgets",
                    "file_format": "insert_values",
                    "file_size": 2048,
                    "elapsed": 0.5,
                    "state": "completed_jobs",
                    "failed_message": None,
                    "created_at": "2026-04-19 10:00:06+00:00",
                },
                {
                    "job_id": "orders.def.insert_values",
                    "table_name": "orders",
                    "file_format": "insert_values",
                    "file_size": 4096,
                    "elapsed": 0.6,
                    "state": "completed_jobs",
                    "failed_message": None,
                    "created_at": "2026-04-19 10:00:07+00:00",
                },
            ],
        }
    ]

    return {
        "transaction_id": transaction_id,
        "pipeline_name": pipeline_name,
        "started_at": started,
        "finished_at": load_end,
        "engine_version": 1,
        "steps": [
            {
                "step": "extract",
                "started_at": started,
                "finished_at": extract_end,
                "step_exception": None,
                "step_info": {},
            },
            {
                "step": "normalize",
                "started_at": extract_end,
                "finished_at": normalize_end,
                "step_exception": None,
                "step_info": {},
            },
            {
                "step": "load",
                "started_at": normalize_end,
                "finished_at": load_end,
                "step_exception": step_exception,
                "step_info": {"load_packages": load_packages},
            },
        ],
    }


class TestCaptureDltTraceFromDict:
    def test_inserts_run_steps_and_jobs(self, tmp_path: Path) -> None:
        meta = metadata_db_path(tmp_path)
        ensure_schema(meta)

        txn = capture_dlt_trace_from_dict(meta, _sample_trace())
        assert txn == "txn-001"

        con = duckdb.connect(str(meta), read_only=True)
        try:
            runs = con.execute(
                "SELECT transaction_id, pipeline_name, duration_s, success "
                "FROM dlt_trace_runs"
            ).fetchall()
            assert runs == [("txn-001", "sample_pipeline", 8.0, True)]

            steps = con.execute(
                "SELECT step FROM dlt_trace_steps "
                "WHERE transaction_id = 'txn-001' ORDER BY started_at"
            ).fetchall()
            assert [s[0] for s in steps] == ["extract", "normalize", "load"]

            jobs = con.execute(
                "SELECT job_id, table_name, file_size_bytes "
                "FROM dlt_trace_jobs WHERE transaction_id = 'txn-001' "
                "ORDER BY job_id"
            ).fetchall()
            assert len(jobs) == 2
            assert jobs[0][1] == "orders"
            assert jobs[0][2] == 4096
        finally:
            con.close()

    def test_is_idempotent_per_transaction_id(self, tmp_path: Path) -> None:
        meta = metadata_db_path(tmp_path)
        ensure_schema(meta)

        first = capture_dlt_trace_from_dict(meta, _sample_trace())
        second = capture_dlt_trace_from_dict(meta, _sample_trace())

        assert first == "txn-001"
        assert second is None  # already captured

        con = duckdb.connect(str(meta), read_only=True)
        try:
            count = con.execute(
                "SELECT COUNT(*) FROM dlt_trace_runs"
            ).fetchone()
            assert count == (1,)
            job_count = con.execute(
                "SELECT COUNT(*) FROM dlt_trace_jobs"
            ).fetchone()
            assert job_count == (2,)
        finally:
            con.close()

    def test_skips_missing_transaction_id(self, tmp_path: Path) -> None:
        meta = metadata_db_path(tmp_path)
        ensure_schema(meta)

        trace = _sample_trace()
        trace["transaction_id"] = None
        result = capture_dlt_trace_from_dict(meta, trace)
        assert result is None

        con = duckdb.connect(str(meta), read_only=True)
        try:
            count = con.execute("SELECT COUNT(*) FROM dlt_trace_runs").fetchone()
            assert count == (0,)
        finally:
            con.close()

    def test_records_step_exception(self, tmp_path: Path) -> None:
        meta = metadata_db_path(tmp_path)
        ensure_schema(meta)

        trace = _sample_trace(step_exception="429 rate-limited")
        capture_dlt_trace_from_dict(meta, trace)

        con = duckdb.connect(str(meta), read_only=True)
        try:
            row = con.execute(
                "SELECT success, exception FROM dlt_trace_runs"
            ).fetchone()
            assert row == (False, "429 rate-limited")
            exc_step = con.execute(
                "SELECT step_exception FROM dlt_trace_steps WHERE step = 'load'"
            ).fetchone()
            assert exc_step == ("429 rate-limited",)
        finally:
            con.close()


class TestCaptureDltTraceFromDisk:
    def test_missing_trace_file_is_noop(self, tmp_path: Path) -> None:
        meta = metadata_db_path(tmp_path)
        ensure_schema(meta)
        pipelines_dir = tmp_path / "fake_dlt_home"

        result = capture_dlt_trace(meta, "nonexistent_pipeline", pipelines_dir)
        assert result is None

    def test_safe_wrapper_swallows_missing_pipeline(self, tmp_path: Path) -> None:
        meta = metadata_db_path(tmp_path)
        ensure_schema(meta)

        capture_dlt_trace_safe(meta, None)  # explicit no-op on missing name
        capture_dlt_trace_safe(meta, "nope", pipelines_dir=tmp_path / "x")
        # Just make sure neither call raised.

    def test_reads_real_pickle(self, tmp_path: Path) -> None:
        """Pickle a trace dict directly — the loader's fallback path handles
        the no-asdict case, which is enough for a disk round-trip test
        without needing dlt's ``PipelineTrace`` class in the fixture."""
        import pickle

        pipelines_dir = tmp_path / "dlt_home"
        pipeline_dir = pipelines_dir / "sample_pipeline"
        pipeline_dir.mkdir(parents=True)
        with (pipeline_dir / "trace.pickle").open("wb") as f:
            pickle.dump(_sample_trace(), f)

        meta = metadata_db_path(tmp_path)
        ensure_schema(meta)

        txn = capture_dlt_trace(meta, "sample_pipeline", pipelines_dir)
        assert txn == "txn-001"


class TestTraceParquetExport:
    def test_trace_tables_included(self, tmp_path: Path) -> None:
        """The new trace tables should be part of the Parquet export."""
        meta = metadata_db_path(tmp_path)
        ensure_schema(meta)
        capture_dlt_trace_from_dict(meta, _sample_trace())

        parquet_dir = tmp_path / "parquet"
        exported = export_to_parquet(meta, parquet_dir)

        assert "dlt_trace_runs" in exported
        assert "dlt_trace_steps" in exported
        assert "dlt_trace_jobs" in exported
        assert exported["dlt_trace_runs"].exists()
