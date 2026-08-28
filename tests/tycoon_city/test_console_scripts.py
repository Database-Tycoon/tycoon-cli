"""The city addon's console scripts exist and answer --help.

The contract docs (docs/city/city-json-v1.md, run-json-v1.md), the guide, and
web/package.json's demo-data script all invoke ``tycoon-city-export``; the
server's argparse names itself ``tycoon-city``. These entry points lived in
pipeline-city's pyproject and must survive the absorb — a doc whose quickstart
invokes a command the wheel doesn't install is the bug this test pins.

Subprocess-driven for the same reason as test_e2e_demo_arc.py: console-script
wiring drift after packaging changes is invisible to in-process tests.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest


@pytest.mark.subprocess_e2e
@pytest.mark.parametrize("script", ["tycoon-city-export", "tycoon-city"])
def test_console_script_answers_help(script: str) -> None:
    binary = shutil.which(script)
    assert binary, (
        f"`{script}` not on PATH — declare it in [project.scripts] "
        "(run via `uv run pytest` so the venv's bin dir is active)"
    )
    result = subprocess.run([binary, "--help"], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert script in result.stdout
