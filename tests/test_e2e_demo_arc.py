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


def _run(
    args: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 90
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - intentional subprocess for CLI surface test
        args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _assert_ok(
    label: str, result: subprocess.CompletedProcess[str]
) -> None:
    if result.returncode != 0:
        pytest.fail(
            f"{label} exited {result.returncode}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}\n"
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
    assert (project / "dbt_project" / "dbt_project.yml").exists(), (
        "dbt_project/ not scaffolded by csv-import template"
    )
    assert (project / "data" / "input" / "widgets.csv").exists(), (
        "sample widgets.csv not seeded by csv-import template"
    )

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
    assert warehouse_db.exists(), (
        f"warehouse db missing after transform: {warehouse_db}"
    )
