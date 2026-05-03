"""Shared fixtures for the tycoon test suite."""

from __future__ import annotations

import pytest
from pathlib import Path


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


@pytest.fixture(autouse=True)
def _stub_local_llm_probe(monkeypatch):
    """Default-stub LM Studio / Ollama port probes so tests that drive
    the init wizard don't behave differently depending on whether the
    developer has Ollama or LM Studio running locally.

    Tests that specifically exercise auto-detection override this by
    re-patching ``_probe_local_llm`` after the fixture runs.
    """
    from tycoon.commands import ask as ask_mod

    monkeypatch.setattr(
        ask_mod, "_probe_local_llm", lambda _url: (False, 0, "stub: no probe")
    )
