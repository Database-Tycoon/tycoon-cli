import subprocess
import sys


def test_sim_imports_without_pygame():
    code = (
        "import tycoon_city.sim.layout, "
        "tycoon_city.sim.signals, sys; "
        "assert 'pygame' not in sys.modules, 'sim must not import pygame'"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
