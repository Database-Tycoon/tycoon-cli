"""The export path must import with pygame genuinely unavailable.

This is what makes the emitter deployable in a slim image with no SDL, and it is
a stronger claim than `tests/sim/test_no_pygame.py` makes. That one asserts
pygame is absent from `sys.modules` after the import, which a *lazy* import
inside a function body satisfies while still crashing the moment the function
runs. Here pygame is made unimportable first, so any import of it -- at module
level or deferred -- raises.

Run in a subprocess because the block has to be installed before `tycoon_city` is
imported at all, and pytest has already imported pygame by this point.
"""

import subprocess
import sys

# Every module the export path touches, named as string literals. A rename that
# misses these turns the guard off silently, which is precisely how this repo
# has broken guards before -- so the last assertion checks the block itself
# works, and `test_the_block_actually_blocks_pygame` proves the harness can fail.
_MODULES = (
    "tycoon_city.export",
    "tycoon_city.export.blocks",
    "tycoon_city.export.build",
    "tycoon_city.export.city_json",
    "tycoon_city.export.cli",
    "tycoon_city.theme_data",
    "tycoon_city.webserve",
)

_BLOCK = """
import sys

class _Blocked:
    def find_module(self, name, path=None):
        return self.find_spec(name, path)

    def find_spec(self, name, path=None, target=None):
        if name == "pygame" or name.startswith("pygame."):
            raise ImportError("pygame is blocked for this test")
        return None

sys.meta_path.insert(0, _Blocked())
"""


def _run(body: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", _BLOCK + body],
        capture_output=True,
        text=True,
    )


def test_export_path_imports_without_pygame():
    imports = "\n".join(f"import {name}" for name in _MODULES)
    body = f"""
{imports}
import sys
assert "pygame" not in sys.modules, "the export path pulled pygame in"
"""

    result = _run(body)

    assert result.returncode == 0, result.stderr


def test_exporting_a_catalog_works_without_pygame(tmp_path):
    """Importing cleanly is not enough -- the CLI must run end to end, which is
    what catches a pygame import deferred into a function body."""
    db = tmp_path / "fx.duckdb"
    out = tmp_path / "out"

    import duckdb

    con = duckdb.connect(str(db))
    con.execute("create schema raw")
    con.execute("create table raw.orders as select * from range(5) t(id)")
    con.execute("create view main.v_orders as select * from raw.orders")
    con.close()

    body = f"""
import json, sys
from pathlib import Path
from tycoon_city.export.cli import main

assert main([{str(db)!r}, {str(out)!r}]) == 0
document = json.loads((Path({str(out)!r}) / "city.json").read_text())
assert document["database"]["object_count"] == 2
assert (Path({str(out)!r}) / "spritesheet.png").exists()
assert "pygame" not in sys.modules, "exporting pulled pygame in"
"""

    result = _run(body)

    assert result.returncode == 0, result.stderr


def test_the_block_actually_blocks_pygame():
    """The counterweight. Without this, a broken block would make every test
    above pass by importing pygame perfectly happily."""
    result = _run("import pygame")

    assert result.returncode != 0
    assert "pygame is blocked for this test" in result.stderr
