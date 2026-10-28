"""Subprocess-driven end-to-end test of the v0.1.6 demo arc.

This test shells out to the real ``tycoon`` binary on PATH (rather than
calling Typer functions in-process like ``test_templates_e2e.py``), so
it catches a class of bug that in-process tests can't see:

- PATH / venv resolution drift (`tycoon` not findable, wrong Python, etc.)
- Rich rendering bugs in user-facing strings (the v0.1.6 ``[extra]``
  bracket strip would have surfaced here)
- Stdout/stderr framing and exit code handling
- Console-script wiring drift after packaging changes

Motivation: [#40][40] (the Tier 1 follow-up to #32). The csv-import
template is the canonical "demo works offline" arc.

[40]: https://github.com/Database-Tycoon/tycoon-cli/issues/40
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


def _tycoon_bin() -> str:
    """Resolve the installed ``tycoon`` binary or skip if not on PATH.

    The subprocess form deliberately uses the binary rather than ``python
    -m tycoon`` so we exercise the same console_script entry point users
    invoke. Run the suite via ``uv run pytest`` so the venv's bin dir is
    on PATH.
    """
    binary = shutil.which("tycoon")
    if not binary:
        pytest.skip(
            "`tycoon` binary not on PATH. Run via `uv run pytest` so the "
            "venv's bin dir is active (or `pip install -e .` first)."
        )
    return binary


def _run(args: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _assert_ok(label: str, result: subprocess.CompletedProcess[str]) -> None:
    if result.returncode != 0:
        pytest.fail(
            f"{label} exited {result.returncode}\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}\n"
        )


@pytest.mark.subprocess_e2e
def test_demo_arc_csv_import(tmp_path: Path) -> None:
    """Run the v0.1.6 demo arc end-to-end via subprocess: init → ingest
    → analyze → transform. Asserts artifacts at each stage so a
    silent-pass regression (e.g. command runs but produces nothing)
    still fails the test.

    Budget: ≤60s on a clean checkout; ≤90s in CI under cache misses.
    """
    tycoon = _tycoon_bin()
    project = tmp_path / "demo"
    project.mkdir()

    env = os.environ.copy()
    # Isolate dbt / Nao / tycoon caches from the developer's real $HOME.
    env["HOME"] = str(tmp_path / "home")
    Path(env["HOME"]).mkdir()
    env["TYCOON_DISABLE_LLM_PROBE"] = "1"
    # Skip the real `uv sync` + PyPI install `tycoon init` now does by
    # default (gh-262), this test exercises the ingestion/transform arc,
    # not environment-building, and a real build is too slow for per-PR CI.
    env["TYCOON_INIT_NO_VENV"] = "1"

    # 1. init
    _assert_ok(
        "tycoon init",
        _run(
            [tycoon, "init", "--template", "csv-import", "--name", "demo"],
            cwd=project,
            env=env,
        ),
    )
    assert (project / "tycoon.yml").exists(), "tycoon.yml not scaffolded"
    assert (project / "dbt_project" / "dbt_project.yml").exists(), "dbt_project/ not scaffolded by csv-import template"
    assert (project / "data" / "input" / "widgets.csv").exists(), "sample widgets.csv not seeded by csv-import template"

    # 2. ingest the bundled CSV
    _assert_ok(
        "tycoon data sources run files",
        _run(
            [tycoon, "data", "sources", "run", "files"],
            cwd=project,
            env=env,
        ),
    )
    raw_db = project / "data" / "files_raw.duckdb"
    assert raw_db.exists(), f"raw db missing after ingest: {raw_db}"

    # 3. analyze (scaffold staging models against the ingested raw)
    _assert_ok(
        "tycoon data analyze files",
        _run(
            [tycoon, "data", "analyze", "files"],
            cwd=project,
            env=env,
        ),
    )

    # 4. transform — full dbt build via the project's profile
    _assert_ok(
        "tycoon data transform run",
        _run(
            [tycoon, "data", "transform", "run"],
            cwd=project,
            env=env,
            timeout=120,
        ),
    )
    warehouse_db = project / "data" / "files_warehouse.duckdb"
    assert warehouse_db.exists(), f"warehouse db missing after transform: {warehouse_db}"


@pytest.mark.subprocess_e2e
def test_run_all_ignores_dbt_on_path(tmp_path: Path) -> None:
    """``data run-all`` must run the dbt next to tycoon's Python (#439).

    PATH holds a stub ``dbt`` that leaves a marker and fails, and does not
    hold the venv's bin dir, so resolving dbt through PATH either runs the
    stub or finds nothing. The run must also record the build in
    ``dbt_runs`` like ``transform build`` does (#326).
    """
    tycoon = _tycoon_bin()
    project = tmp_path / "demo"
    project.mkdir()

    stub_bin = tmp_path / "global-bin"
    stub_bin.mkdir()
    marker = tmp_path / "stub-dbt-ran"
    stub = stub_bin / "dbt"
    stub.write_text(f"#!/bin/sh\ntouch '{marker}'\nexit 3\n")
    stub.chmod(0o755)

    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    Path(env["HOME"]).mkdir()
    env["TYCOON_DISABLE_LLM_PROBE"] = "1"
    env["TYCOON_INIT_NO_VENV"] = "1"
    venv_bin = str(Path(tycoon).resolve().parent)
    kept = [p for p in env.get("PATH", "").split(os.pathsep) if p and str(Path(p).resolve()) != venv_bin]
    env["PATH"] = os.pathsep.join([str(stub_bin), *kept])
    env.pop("VIRTUAL_ENV", None)

    _assert_ok(
        "tycoon init",
        _run([tycoon, "init", "--template", "csv-import", "--name", "demo"], cwd=project, env=env),
    )
    _assert_ok("tycoon data run-all", _run([tycoon, "data", "run-all"], cwd=project, env=env, timeout=180))

    assert not marker.exists(), "run-all ran the dbt on PATH instead of the one next to tycoon's Python"
    assert (project / "data" / "files_warehouse.duckdb").exists(), "warehouse db missing after run-all"

    import duckdb

    con = duckdb.connect(str(project / ".tycoon" / "metadata.duckdb"), read_only=True)
    try:
        row = con.execute("SELECT count(*) FROM dbt_runs WHERE command = 'build'").fetchone()
    finally:
        con.close()
    assert row is not None and row[0] == 1, f"run-all should record one dbt 'build' run, got {row}"
