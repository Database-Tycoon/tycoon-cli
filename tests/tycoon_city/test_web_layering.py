"""The Phase G import-direction guard, in the spirit of test_no_pygame.py.

The three layers (derived / presentation / simulated) only stay separate if
imports flow one way. Simulated state lives in `web/src/mechanics/`; this
guard greps the actual source files, so a refactor that quietly couples the
layers fails a named test instead of passing silently.

Grep-based on purpose: the web side has no AST tool in this repo's toolchain,
and import statements are syntactically rigid enough that a regex cannot miss
one that would compile.
"""

import re
from pathlib import Path

WEB_SRC = Path(__file__).resolve().parents[2] / "web" / "src"

# What the simulated layer may reach: derived facts (contract), the shared
# deterministic primitives, and nothing else -- no scene, no ui, no three.js.
# roadnet joined 2026-08-05: a deterministic primitive (pure BFS over the
# document's tiles) — vehicles must travel on roads, mechanics included.
MECHANICS_ALLOWED = re.compile(r"^\.\./(contract|sim/paths|sim/rng|sim/roadnet)$")

_IMPORT = re.compile(r"""from\s+["']([^"']+)["']""")


def _imports(path: Path) -> list[str]:
    return _IMPORT.findall(path.read_text())


def test_mechanics_imports_only_facts_and_primitives():
    files = list((WEB_SRC / "mechanics").glob("*.ts"))
    assert files, "the mechanics layer exists"
    for file in files:
        for target in _imports(file):
            assert MECHANICS_ALLOWED.match(target), (
                f"{file.name} imports '{target}' -- the simulated layer may only "
                "read the contract and the deterministic primitives"
            )


def test_nothing_below_main_imports_mechanics():
    """Only the composition root may know the simulated layer exists.

    The root is `main.ts` plus `boot/`: the 2026-08-08 split moved the wiring
    out of main.ts without changing what it is. scene/guest_layer.ts is
    presentation *for* mechanics and may read its types; nothing in the core
    sim, contract, ui or other scene modules may.
    """
    allowed = {"main.ts", "guest_layer.ts"}
    for file in WEB_SRC.rglob("*.ts"):
        if file.parent.name in {"mechanics", "boot"} or file.name in allowed:
            continue
        for target in _imports(file):
            assert "mechanics" not in target, (
                f"{file.relative_to(WEB_SRC)} imports '{target}' -- only the "
                "composition root (main.ts, boot/) and the guest presentation "
                "layer may"
            )


def test_derived_modules_do_not_import_the_simulated_layer_types():
    """contract.ts is the derived seam; it must not even name mechanics."""
    assert "mechanics" not in (WEB_SRC / "contract.ts").read_text()
