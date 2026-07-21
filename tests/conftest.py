"""Shared fixtures for the tycoon test suite."""

from __future__ import annotations

import pytest
from pathlib import Path


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
