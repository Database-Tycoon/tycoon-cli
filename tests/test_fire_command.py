"""Tests for `tycoon fire`, `tycoon repair` and `tycoon firehouse` (PTC-126).

Each test builds a small real project: a tycoon.yml, dbt's own
`target/run_results.json`, and a metadata DB populated through the real
`capture_dbt` path, so the commands read exactly what a user's project holds.
Assertions target names and counts rather than table layout, so column-width
changes in Rich don't break them.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from tycoon.cli import app
from tycoon.observability import capture_dbt, ensure_schema, metadata_db_path

_TYCOON_YML = "name: test\nversion: 0.1.0\nsources: {}\n"


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


def _seed_source_freshness(root: Path, rows: list[tuple[str, str, str | None]]) -> None:
    """Hand-seed the `source_freshness` table the fire module reads (see the xfail below)."""
    meta = metadata_db_path(root)
    ensure_schema(meta)
    with duckdb.connect(str(meta)) as con:
        con.execute("CREATE TABLE source_freshness (name VARCHAR, freshness_status VARCHAR, max_loaded_at TIMESTAMP)")
        for row in rows:
            con.execute("INSERT INTO source_freshness VALUES (?, ?, ?)", list(row))


@pytest.fixture
def project(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / "tycoon.yml").write_text(_TYCOON_YML)
    from tycoon.commands import fire as fire_mod
    from tycoon.config import TycoonConfig

    monkeypatch.setattr(fire_mod, "config", TycoonConfig(project_root=tmp_path))
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def no_project(tmp_path: Path, monkeypatch) -> Path:
    from tycoon.commands import fire as fire_mod
    from tycoon.config import TycoonConfig

    monkeypatch.setattr(fire_mod, "config", TycoonConfig(project_root=tmp_path))
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Shared: every command refuses to run outside a project
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("command", ["fire", "repair", "firehouse"])
def test_requires_tycoon_yml(no_project, cli_runner, command):
    result = cli_runner.invoke(app, [command])
    assert result.exit_code == 1
    assert "No tycoon.yml found" in result.output


def test_commands_are_registered_at_the_top_level(cli_runner):
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ("fire", "repair", "firehouse"):
        assert name in result.output


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

    @pytest.mark.xfail(
        strict=True,
        reason="fire counts dbt model build errors (status 'error') as fires; a fire is one failing test",
    )
    def test_a_model_build_error_is_not_a_fire(self, project, cli_runner):
        _write_run_results(
            project / "dbt_project",
            "inv-a",
            [_result("model.p.orders", "error"), _result("test.p.nn_id", "fail")],
        )
        result = cli_runner.invoke(app, ["fire"])
        assert "1 building(s) on fire" in result.output

    @pytest.mark.xfail(
        strict=True,
        reason="the latest run is picked with MAX(invocation_id), a UUID, not by started_at",
    )
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
# tycoon repair
# ---------------------------------------------------------------------------


class TestRepair:
    def test_without_metadata_db(self, project, cli_runner):
        result = cli_runner.invoke(app, ["repair"])
        assert result.exit_code == 0
        assert "No metadata database found" in result.output

    def test_no_stale_sources_means_no_vans(self, project, cli_runner):
        _seed_source_freshness(project, [("orders", "pass", "2026-09-01 10:00:00")])
        result = cli_runner.invoke(app, ["repair"])
        assert result.exit_code == 0
        assert "All sources within SLA" in result.output
        assert "orders" not in result.output

    def test_one_van_per_source_past_sla(self, project, cli_runner):
        _seed_source_freshness(
            project,
            [
                ("orders", "warn", "2026-09-01 10:00:00"),
                ("payments", "error", None),
                ("customers", "pass", "2026-09-01 10:00:00"),
            ],
        )
        result = cli_runner.invoke(app, ["repair"])
        assert result.exit_code == 0
        assert "orders" in result.output
        assert "payments" in result.output
        assert "customers" not in result.output
        assert "2 source(s) past SLA" in result.output
        assert "One contractor van dispatched per call" in result.output

    @pytest.mark.xfail(
        strict=True,
        reason="repair reads a source_freshness table that no tycoon capture creates; stale sources never get a van",
    )
    def test_stale_source_from_dbt_source_freshness_gets_a_van(self, project, cli_runner):
        dbt_dir = project / "dbt_project"
        _capture(project, "inv-a", [_result("model.p.orders", "success")])
        (dbt_dir / "target" / "sources.json").write_text(
            json.dumps(
                {
                    "metadata": {"invocation_id": "inv-fresh"},
                    "results": [
                        {
                            "unique_id": "source.p.shop.orders",
                            "status": "error",
                            "max_loaded_at": "2026-08-01T00:00:00Z",
                        }
                    ],
                }
            )
        )
        result = cli_runner.invoke(app, ["repair"])
        assert "orders" in result.output
        assert "1 source(s) past SLA" in result.output


# ---------------------------------------------------------------------------
# tycoon firehouse
# ---------------------------------------------------------------------------


class TestFirehouse:
    def test_no_data_at_all(self, project, cli_runner):
        result = cli_runner.invoke(app, ["firehouse"])
        assert result.exit_code == 0
        assert "No data available" in result.output

    def test_counts_fleets_from_an_exported_city(self, project, cli_runner):
        city = {
            "firehouse": {"x": 12, "y": -4},
            "lots": [
                {"test_status": "fail"},
                {"test_status": "fail"},
                {"test_status": "pass", "freshness_status": "warn"},
                {"freshness_status": "error"},
                {"freshness_status": "pass"},
            ],
        }
        (project / "city.json").write_text(json.dumps(city))
        result = cli_runner.invoke(app, ["firehouse"])
        assert result.exit_code == 0
        assert "Firehouse at (12, -4)" in result.output
        assert _count_for(result.output, "Fire trucks on duty") == 2
        assert _count_for(result.output, "Contractor vans on duty") == 2
        assert "never that a fix is running" in _flat(result.output)

    def test_counts_fleets_from_metadata_without_a_map(self, project, cli_runner):
        _capture(project, "inv-a", [_result("test.p.nn_id", "fail"), _result("test.p.ok", "pass")])
        result = cli_runner.invoke(app, ["firehouse"])
        assert result.exit_code == 0
        assert "No exported city.json" in result.output
        assert _count_for(result.output, "Fire trucks on duty") == 1
        assert _count_for(result.output, "Contractor vans on duty") == 0
        assert "never that a fix is running" in _flat(result.output)


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
