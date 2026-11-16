"""Tests for ``tycoon data run-all``'s dbt step.

Regression tests for #439 (run-all ran whichever dbt was first on PATH
instead of the one next to tycoon's Python) and #326 (run-all recorded no
``dbt_runs`` / ``dbt_nodes`` rows, while ``transform build`` did).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

from tycoon.cli import app

pytestmark = pytest.mark.usefixtures("fake_venv")


def _rebind_config(monkeypatch, project: Path) -> None:
    """Point the module-level ``config`` singletons at ``project``.

    run-all reads its own config via ``load_config()``, but the dbt
    recording path it shares with ``transform`` reads the singleton.
    """
    import tycoon.config as cfg_mod
    from tycoon.commands import transform as transform_mod
    from tycoon.config import TycoonConfig

    cfg = TycoonConfig(project_root=project)
    monkeypatch.setattr(transform_mod, "config", cfg)
    monkeypatch.setattr(cfg_mod, "config", cfg)


def _write_stub_dbt(bin_dir: Path) -> Path:
    bin_dir.mkdir(parents=True, exist_ok=True)
    dbt = bin_dir / "dbt"
    dbt.write_text("#!/bin/sh\nexit 0\n")
    dbt.chmod(0o755)
    return dbt


def _invoke_ok(cli_runner, args: list[str]) -> None:
    result = cli_runner.invoke(app, args)
    stderr = result.stderr if result.stderr_bytes else ""
    assert result.exit_code == 0, (
        f"{' '.join(args)} failed (exit {result.exit_code}):\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{stderr}\n"
        f"--- exception ---\n{result.exception!r}"
    )


@pytest.mark.parametrize("global_dbt_on_path", [True, False], ids=["global-dbt-on-path", "no-dbt-on-path"])
def test_run_all_uses_the_dbt_next_to_python(cli_runner, tmp_path, monkeypatch, global_dbt_on_path):
    project = tmp_path / "project"
    (project / "dbt_project").mkdir(parents=True)
    (project / "tycoon.yml").write_text("name: test\nsources: {}\n")
    monkeypatch.chdir(project)
    _rebind_config(monkeypatch, project)

    venv_dbt = _write_stub_dbt(tmp_path / "venv" / "bin")
    monkeypatch.setattr(sys, "executable", str(venv_dbt.parent / "python"))
    path_dir = tmp_path / "global" / "bin"
    path_dir.mkdir(parents=True)
    if global_dbt_on_path:
        _write_stub_dbt(path_dir)
    monkeypatch.setenv("PATH", str(path_dir))

    calls: list[list[str]] = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    _invoke_ok(cli_runner, ["data", "run-all", "--skip-ingest"])

    assert calls, "run-all did not invoke dbt"
    assert calls[0][:2] == [str(venv_dbt), "build"]


@pytest.mark.offline_e2e
def test_run_all_records_dbt_runs_like_transform_build(cli_runner, tmp_path, monkeypatch):
    project = tmp_path / "csv-import"
    project.mkdir()
    monkeypatch.chdir(project)
    _invoke_ok(cli_runner, ["init", "--template", "csv-import"])
    _rebind_config(monkeypatch, project)
    metadata_db = project / ".tycoon" / "metadata.duckdb"

    def build_rows() -> tuple[int, int]:
        con = duckdb.connect(str(metadata_db), read_only=True)
        try:
            runs = con.execute("SELECT count(*) FROM dbt_runs WHERE command = 'build'").fetchone()
            nodes = con.execute(
                "SELECT count(*) FROM dbt_nodes WHERE status = 'success' AND node_name LIKE '%stg_widgets%'"
            ).fetchone()
        finally:
            con.close()
        assert runs is not None and nodes is not None
        return runs[0], nodes[0]

    _invoke_ok(cli_runner, ["data", "run-all"])
    runs, nodes = build_rows()
    assert runs == 1, f"run-all should record one dbt 'build' run, got {runs}"
    assert nodes >= 1, "run-all should record the successful stg_widgets node"

    _invoke_ok(cli_runner, ["data", "transform", "build"])
    runs, _ = build_rows()
    assert runs == 2, f"transform build should add a second dbt 'build' run, got {runs}"
