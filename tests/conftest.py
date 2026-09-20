"""Shared fixtures for the tycoon test suite."""

from __future__ import annotations

from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-online",
        action="store_true",
        default=False,
        help=(
            "Run recipe doctest blocks marked `mode=online` "
            "(`tests/test_recipe_doctests.py`). Hits real upstream APIs; "
            "intended for the nightly-e2e workflow, not per-PR CI."
        ),
    )


@pytest.fixture
def tmp_config(tmp_path: Path):
    """Create a TycoonConfig pointing at a temp directory."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
    from tycoon.config import TycoonConfig

    cfg = TycoonConfig(project_root=tmp_path)
    cfg.ensure_data_dir()
    return cfg


@pytest.fixture
def cli_runner():
    """Typer CLI test runner."""
    from typer.testing import CliRunner

    return CliRunner()


@pytest.fixture
def fake_venv(monkeypatch):
    """Fake a successful `.venv` build instead of shelling out to real uv.

    `tycoon init` builds the project's own environment as part of scaffolding
    (gh-262), so every test that invokes `init` end to end would otherwise
    try to run a real `uv venv` + `uv pip install database-tycoon` against
    PyPI. Opt a module in with `pytestmark = pytest.mark.usefixtures("fake_venv")`
    rather than making this autouse repo-wide; tests that specifically
    exercise venv-building (find_uv missing, create_venv failing, ...)
    override this locally with their own patch.
    """
    from tycoon import venv as venv_mod

    monkeypatch.setattr("tycoon.commands.init.find_uv", lambda: "/usr/bin/uv")
    monkeypatch.setattr(
        "tycoon.commands.init.create_venv",
        lambda target, *a, **k: venv_mod.VenvResult(
            ok=True, message="Created .venv (faked)", venv_path=target / ".venv"
        ),
    )
