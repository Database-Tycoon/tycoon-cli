"""Recipe doctest harness.

Runs marked code blocks from ``README.md`` and ``docs/recipes/*.md`` as
subprocesses against the installed ``tycoon`` binary, asserting exit 0
for each. The point: catch CI-escaped bugs in the seam between the CLI
and what users actually type — the original motivation was [#32][32]
(``rest_api`` ingest broken in v0.1.5 and shipped to PyPI with every
gate green) plus the Rich ``[extra]`` bracket strip both fixed in
v0.1.6, neither of which an in-process test could see.

Marker convention:

    <!-- tycoon-test: mode=offline -->
    ```bash
    tycoon init --template csv-import --name demo
    tycoon data sources run files
    ```

The harness:

- Discovers every marker + the bash fence that immediately follows.
- Runs each block via ``bash -e -o pipefail`` in a fresh tmp dir per
  block. ``HOME`` is rebound so dbt / Nao / tycoon caches don't leak
  into the dev environment.
- Asserts exit 0; on failure prints the block, stdout, and stderr.
- ``mode=offline`` (default): run on every PR via ci.yml.
- ``mode=online``: skipped unless ``--run-online`` is passed. nightly-e2e.yml
  passes the flag so contract drift against real upstream APIs surfaces
  daily.

See ``tests/README.md`` for the marker grammar and how to add new
blocks.

[32]: https://github.com/Database-Tycoon/tycoon-cli/issues/32
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# <!-- tycoon-test: key=val [key=val ...] --> followed (after any
# whitespace / blank lines) by a ```bash ... ``` fence. The marker and
# the fence must be in the same markdown file.
_MARKER_RE = re.compile(
    r"<!--\s*tycoon-test:\s*(?P<args>[^>]*?)\s*-->\s*\n\s*```bash\n(?P<body>.*?)\n```",
    re.DOTALL,
)

_VALID_MODES = {"offline", "online"}


@dataclass(frozen=True)
class RecipeBlock:
    source: Path
    line: int
    mode: str
    body: str

    @property
    def id(self) -> str:
        rel = self.source.relative_to(PROJECT_ROOT).as_posix()
        return f"{rel}:L{self.line}"


def _parse_marker_args(raw: str, source: Path, line: int) -> dict[str, str]:
    out: dict[str, str] = {}
    for token in raw.split():
        if "=" not in token:
            raise ValueError(
                f"{source}:{line}: tycoon-test marker token missing '=': {token!r}"
            )
        k, v = token.split("=", 1)
        out[k] = v
    return out


def _doc_paths() -> list[Path]:
    paths: list[Path] = []
    readme = PROJECT_ROOT / "README.md"
    if readme.exists():
        paths.append(readme)
    recipes_dir = PROJECT_ROOT / "docs" / "recipes"
    if recipes_dir.exists():
        paths.extend(sorted(recipes_dir.glob("*.md")))
    return paths


def _collect_blocks() -> list[RecipeBlock]:
    blocks: list[RecipeBlock] = []
    for doc in _doc_paths():
        text = doc.read_text(encoding="utf-8")
        for match in _MARKER_RE.finditer(text):
            line = text[: match.start()].count("\n") + 1
            args = _parse_marker_args(match.group("args"), doc, line)
            mode = args.get("mode", "offline")
            if mode not in _VALID_MODES:
                raise ValueError(
                    f"{doc}:{line}: invalid mode={mode!r} "
                    f"(expected one of {sorted(_VALID_MODES)})"
                )
            blocks.append(
                RecipeBlock(
                    source=doc,
                    line=line,
                    mode=mode,
                    body=match.group("body").strip(),
                )
            )
    return blocks


_BLOCKS = _collect_blocks()


def pytest_configure(config: pytest.Config) -> None:  # pragma: no cover - registration
    config.addinivalue_line(
        "markers",
        "recipe: marker for recipe doctest blocks extracted from README/docs.",
    )


@pytest.mark.recipe
@pytest.mark.parametrize("block", _BLOCKS, ids=[b.id for b in _BLOCKS])
def test_recipe_block(
    block: RecipeBlock, tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    if block.mode == "online" and not request.config.getoption("--run-online"):
        pytest.skip("online block; pass --run-online to enable (nightly only)")

    tycoon_bin = shutil.which("tycoon")
    assert tycoon_bin, (
        "`tycoon` binary not on PATH — recipe doctests require an installed "
        "tycoon. Run via `uv run pytest` so the venv's bin dir is active."
    )

    env = os.environ.copy()
    # Isolate dbt / Nao / tycoon caches from the developer's real $HOME so
    # a recipe block that writes ~/.dbt/profiles.yml or similar doesn't
    # leak into the local environment.
    env["HOME"] = str(tmp_path)
    # Stub LM Studio / Ollama probes so any block that touches `tycoon ask`
    # doesn't hang waiting on a port that isn't listening in CI.
    env["TYCOON_DISABLE_LLM_PROBE"] = "1"

    result = subprocess.run(  # noqa: S603 - intentional subprocess for CLI surface test
        ["bash", "-e", "-o", "pipefail", "-c", block.body],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        pytest.fail(
            f"Recipe block at {block.id} (mode={block.mode}) exited "
            f"{result.returncode}\n"
            f"--- block ---\n{block.body}\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}\n"
        )
