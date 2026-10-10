"""Regression tests for the per-layer "last build" line in `tycoon data status` (gh-390)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb
import pytest

from tycoon.cli import app
from tycoon.config import TycoonConfig
from tycoon.observability import capture_dbt, metadata_db_path


def _model_node(name: str, folder: str) -> dict:
    return {
        "resource_type": "model",
        "name": name,
        "schema": "main",
        "original_file_path": f"models/{folder}/{name}.sql",
        "config": {"meta": {}},
    }


def _write_run_results(dbt_dir: Path, unique_ids: list[str], started_at: datetime) -> None:
    """Write a run_results.json shaped like dbt's, which has no top-level ``success`` key."""
    stamp = started_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    results = [
        {
            "unique_id": uid,
            "status": "success",
            "execution_time": 0.5,
            "timing": [{"name": "execute", "started_at": stamp, "completed_at": stamp}],
            "adapter_response": {"rows_affected": 1},
            "message": "OK",
        }
        for uid in unique_ids
    ]
    payload = {
        "metadata": {"invocation_id": "inv-390", "dbt_version": "1.12.0", "generated_at": stamp},
        "args": {"which": "build", "target": "dev"},
        "results": results,
        "elapsed_time": 1.0,
    }
    (dbt_dir / "target" / "run_results.json").write_text(json.dumps(payload))


@pytest.fixture
def status_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TycoonConfig:
    (tmp_path / "tycoon.yml").write_text(
        "name: test\nversion: 0.1.0\ndatabase:\n  raw: data/raw.duckdb\n"
        "  warehouse: data/warehouse.duckdb\nsources: {}\n"
    )
    from tycoon.commands import status as status_mod

    cfg = TycoonConfig(project_root=tmp_path)
    monkeypatch.setattr(status_mod, "config", cfg)
    monkeypatch.chdir(tmp_path)

    target = cfg.dbt_project_dir / "target"
    target.mkdir(parents=True)
    nodes = {
        "model.p.stg_orders": _model_node("stg_orders", "staging"),
        "model.p.int_orders": _model_node("int_orders", "intermediate"),
        "model.p.fct_orders": _model_node("fct_orders", "marts"),
    }
    (target / "manifest.json").write_text(json.dumps({"nodes": nodes}))
    return cfg


def _summary_lines(stdout: str) -> list[str]:
    return [line.strip() for line in stdout.splitlines() if "last build" in line]


class TestLayerLastBuild:
    def test_layers_built_by_a_captured_run_show_its_age(self, status_project: TycoonConfig, cli_runner) -> None:
        started = datetime.now(tz=UTC) - timedelta(hours=2)
        _write_run_results(status_project.dbt_project_dir, ["model.p.stg_orders", "model.p.fct_orders"], started)
        assert capture_dbt(metadata_db_path(status_project.root), status_project.dbt_project_dir) == "inv-390"

        result = cli_runner.invoke(app, ["data", "status"])

        assert result.exit_code == 0, result.stdout
        assert _summary_lines(result.stdout) == [
            "1 model(s) — last build 2h ago",
            "1 model(s) — last build never",
            "1 model(s) — last build 2h ago",
        ]

    def test_ledger_with_null_success_still_counts_successful_nodes(self, status_project: TycoonConfig) -> None:
        from tycoon.commands.status import _query_layer_last_build

        started = datetime.now(tz=UTC) - timedelta(hours=2)
        _write_run_results(status_project.dbt_project_dir, ["model.p.stg_orders"], started)
        meta = metadata_db_path(status_project.root)
        capture_dbt(meta, status_project.dbt_project_dir)
        with duckdb.connect(str(meta), read_only=True) as con:
            assert con.execute("SELECT count(*), count(success) FROM dbt_runs").fetchone() == (1, 0)

        assert _query_layer_last_build(meta, ["model.p.stg_orders"]) is not None
        assert _query_layer_last_build(meta, ["model.p.fct_orders"]) is None

    @pytest.mark.parametrize("tz", ["UTC", "America/New_York", "Asia/Tokyo"])
    def test_build_age_does_not_depend_on_local_time_zone(self, status_project: TycoonConfig, tz: str) -> None:
        started = datetime.now(tz=UTC) - timedelta(hours=2)
        _write_run_results(status_project.dbt_project_dir, ["model.p.stg_orders"], started)
        meta = metadata_db_path(status_project.root)
        script = (
            "import sys\n"
            "from pathlib import Path\n"
            "from tycoon.commands.status import _freshness_label, _query_layer_last_build\n"
            "from tycoon.observability import capture_dbt\n"
            "meta, dbt_dir = Path(sys.argv[1]), Path(sys.argv[2])\n"
            "capture_dbt(meta, dbt_dir)\n"
            "built = _query_layer_last_build(meta, ['model.p.stg_orders'])\n"
            "print(_freshness_label(built)[0])\n"
        )
        # DuckDB fixes its session time zone when the process starts, so a
        # non-UTC zone can only be exercised from a fresh interpreter.
        out = subprocess.run(
            [sys.executable, "-c", script, str(meta), str(status_project.dbt_project_dir)],
            env={**os.environ, "TZ": tz},
            capture_output=True,
            text=True,
            check=True,
        )

        assert out.stdout.strip() == "2h ago"
