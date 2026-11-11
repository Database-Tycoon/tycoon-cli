"""Tests for `tycoon fire` and `tycoon firehouse` (gh-306).

Each test builds a small real project: a tycoon.yml, dbt's own
`target/run_results.json`, and a metadata DB populated through the real
`capture_dbt` path, so the commands read exactly what a user's project holds.
Assertions target names and counts rather than table layout, so column-width
changes in Rich don't break them.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tycoon.cli import app
from tycoon.observability import capture_dbt, metadata_db_path

_TYCOON_YML = "name: test\nversion: 0.1.0\nschema_version: 2\nsources: {}\n"


def _result(unique_id: str, status: str, started_at: str = "2026-09-01T10:00:00Z") -> dict:
    return {
        "unique_id": unique_id,
        "status": status,
        "timing": [{"name": "execute", "started_at": started_at, "completed_at": started_at}],
        "execution_time": 0.1,
    }


def _write_run_results(dbt_dir: Path, invocation_id: str, results: list[dict]) -> None:
    target = dbt_dir / "target"
    target.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {"invocation_id": invocation_id, "generated_at": "2026-09-01T10:00:00Z"},
        "args": {"which": "build"},
        "results": results,
        "success": all(r["status"] in ("pass", "success") for r in results),
        "elapsed_time": 1.0,
    }
    (target / "run_results.json").write_text(json.dumps(payload))


def _capture(root: Path, invocation_id: str, results: list[dict]) -> None:
    """Write run_results.json and capture it into the metadata DB, like a real run."""
    dbt_dir = root / "dbt_project"
    _write_run_results(dbt_dir, invocation_id, results)
    assert capture_dbt(metadata_db_path(root), dbt_dir) == invocation_id


@pytest.fixture
def project(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / "tycoon.yml").write_text(_TYCOON_YML)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def no_project(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Shared: every command refuses to run outside a project
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("command", ["fire", "firehouse"])
def test_requires_tycoon_yml(no_project, cli_runner, command):
    result = cli_runner.invoke(app, [command])
    assert result.exit_code == 1
    assert "No tycoon.yml found" in result.output


def test_commands_are_registered_at_the_top_level(cli_runner):
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ("fire", "firehouse"):
        assert name in result.output
    assert "repair" not in result.output


# ---------------------------------------------------------------------------
# tycoon fire
# ---------------------------------------------------------------------------


class TestFire:
    def test_no_artifacts_means_no_fires(self, project, cli_runner):
        result = cli_runner.invoke(app, ["fire"])
        assert result.exit_code == 0
        assert "No failures" in result.output
        assert "on fire" not in result.output

    def test_all_green_run_results_means_no_fires(self, project, cli_runner):
        _write_run_results(
            project / "dbt_project",
            "inv-green",
            [_result("model.p.orders", "success"), _result("test.p.nn_id", "pass")],
        )
        result = cli_runner.invoke(app, ["fire"])
        assert result.exit_code == 0
        assert "No failures" in result.output

    def test_one_fire_per_failing_test_from_run_results(self, project, cli_runner):
        # No metadata DB: the command falls back to dbt's own run_results.json.
        _write_run_results(
            project / "dbt_project",
            "inv-a",
            [
                _result("model.p.orders", "success"),
                _result("test.p.nn_id", "fail"),
                _result("test.p.uq_id", "fail"),
                _result("test.p.ok_ts", "pass"),
            ],
        )
        result = cli_runner.invoke(app, ["fire"])
        assert result.exit_code == 0
        assert "nn_id" in result.output
        assert "uq_id" in result.output
        assert "ok_ts" not in result.output
        assert "2 building(s) on fire" in result.output

    def test_one_fire_per_failing_test_from_metadata(self, project, cli_runner):
        _capture(
            project,
            "inv-a",
            [_result("model.p.orders", "success"), _result("test.p.nn_id", "fail"), _result("test.p.ok", "pass")],
        )
        result = cli_runner.invoke(app, ["fire"])
        assert result.exit_code == 0
        assert "nn_id" in result.output
        assert "test.p.ok" not in result.output
        assert "1 building(s) on fire" in result.output

    def test_a_fire_never_claims_a_fix_is_running(self, project, cli_runner):
        _capture(project, "inv-a", [_result("test.p.nn_id", "fail")])
        result = cli_runner.invoke(app, ["fire"])
        assert result.exit_code == 0
        assert "not being fixed" in _flat(result.output)

    @pytest.mark.parametrize("source", ["run_results", "metadata"])
    def test_a_model_build_error_is_not_a_fire(self, project, cli_runner, source):
        results = [_result("model.p.orders", "error"), _result("test.p.nn_id", "fail")]
        if source == "metadata":
            _capture(project, "inv-a", results)
        else:
            _write_run_results(project / "dbt_project", "inv-a", results)
        result = cli_runner.invoke(app, ["fire"])
        assert result.exit_code == 0
        assert "orders" not in result.output
        assert "1 building(s) on fire" in result.output

    def test_a_test_that_errored_is_a_fire(self, project, cli_runner):
        # The city sets a building on fire for a test in 'fail' or 'error'.
        _capture(project, "inv-a", [_result("test.p.nn_id", "error")])
        result = cli_runner.invoke(app, ["fire"])
        assert "nn_id" in result.output
        assert "1 building(s) on fire" in result.output

    def test_fires_are_named_like_dbt_names_them(self, project, cli_runner):
        # Real dbt test ids carry a hash suffix: test.<project>.<name>.<hash>.
        _capture(project, "inv-a", [_result("test.p.not_null_orders_id.8478cd9390", "fail")])
        result = cli_runner.invoke(app, ["fire"])
        assert "not_null_orders_id" in result.output
        assert "test.p." not in result.output
        assert "8478cd9390" not in result.output

    def test_standing_state_reads_the_most_recent_run(self, project, cli_runner):
        # The newer run has the lexically SMALLER id, as random UUIDs often do.
        _capture(project, "ffff-old", [_result("test.p.old_fail", "fail", "2026-09-01T10:00:00Z")])
        _capture(project, "0000-new", [_result("test.p.new_fail", "fail", "2026-09-02T10:00:00Z")])
        result = cli_runner.invoke(app, ["fire"])
        assert "new_fail" in result.output
        assert "old_fail" not in result.output

    def test_run_replays_one_invocation_by_prefix(self, project, cli_runner):
        _capture(project, "aaaa-1111", [_result("test.p.first_fail", "fail", "2026-09-01T10:00:00Z")])
        _capture(project, "bbbb-2222", [_result("test.p.second_fail", "fail", "2026-09-02T10:00:00Z")])
        result = cli_runner.invoke(app, ["fire", "--run", "aaaa"])
        assert result.exit_code == 0
        assert "first_fail" in result.output
        assert "second_fail" not in result.output
        assert "1 building(s) on fire in this run" in result.output

    def test_run_with_no_failures_is_all_green(self, project, cli_runner):
        _capture(project, "aaaa-1111", [_result("test.p.ok", "pass")])
        result = cli_runner.invoke(app, ["fire", "--run", "aaaa"])
        assert result.exit_code == 0
        assert "No failures in this run" in result.output

    def test_run_with_unknown_prefix(self, project, cli_runner):
        _capture(project, "aaaa-1111", [_result("test.p.nn_id", "fail")])
        result = cli_runner.invoke(app, ["fire", "--run", "zzzz"])
        assert result.exit_code == 0
        assert "No run found matching 'zzzz'" in result.output

    def test_run_without_metadata_db(self, project, cli_runner):
        result = cli_runner.invoke(app, ["fire", "--run", "aaaa"])
        assert result.exit_code == 0
        assert "No metadata database found" in result.output


# ---------------------------------------------------------------------------
# tycoon firehouse
# ---------------------------------------------------------------------------


class TestFirehouse:
    def test_no_data_at_all(self, project, cli_runner):
        result = cli_runner.invoke(app, ["firehouse"])
        assert result.exit_code == 0
        assert "No data available" in result.output

    def test_one_truck_per_fire_from_metadata(self, project, cli_runner):
        _capture(
            project,
            "inv-a",
            [_result("test.p.nn_id", "fail"), _result("model.p.orders", "error"), _result("test.p.ok", "pass")],
        )
        result = cli_runner.invoke(app, ["firehouse"])
        assert result.exit_code == 0
        assert _count_for(result.output, "Fire trucks on duty") == 1
        assert "never that a fix is running" in _flat(result.output)

    def test_green_run_results_mean_an_idle_fleet(self, project, cli_runner):
        _write_run_results(project / "dbt_project", "inv-green", [_result("test.p.ok", "pass")])
        result = cli_runner.invoke(app, ["firehouse"])
        assert result.exit_code == 0
        assert _count_for(result.output, "Fire trucks on duty") == 0


def _flat(output: str) -> str:
    """Collapse Rich's soft wraps so a sentence can be matched whole."""
    return " ".join(output.split())


def _count_for(output: str, label: str) -> int:
    """The integer on the table row that starts with ``label``."""
    for line in output.splitlines():
        if label in line:
            digits = [tok for tok in line.replace("│", " ").split() if tok.isdigit()]
            return int(digits[-1])
    raise AssertionError(f"no row labelled {label!r} in:\n{output}")
