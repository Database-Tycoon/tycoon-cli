"""Manage a project-local ``.venv`` via uv (#57).

tycoon runs dbt out of the same interpreter it lives in (it resolves dbt at
``Path(sys.executable).parent / "dbt"``) and imports ``dlt``/``duckdb``
in-process. So the single most reliable onboarding step is to own the
environment: create one project-local ``.venv`` on a *supported* interpreter
and install tycoon (+ dbt + dlt + duckdb) into it, rather than inheriting
whatever ``python3`` the user happens to have.

This module is the subprocess-isolated core behind ``tycoon setup`` and
``tycoon doctor --fix``. uv does the heavy lifting: ``uv venv --python <X>``
auto-downloads a python-build-standalone CPython if the machine only has an
unsupported one (e.g. 3.14), so there are zero manual interpreter installs.

Everything that shells out goes through ``subprocess.run`` at module scope so
tests can patch ``tycoon.venv.subprocess.run`` (mirroring the source_installer
pattern) without ever creating a real environment.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from tycoon.constants import (
    DEFAULT_SETUP_PYTHON,
    MAX_PYTHON_EXCLUSIVE,
    MIN_PYTHON,
    python_range_str,
)

# uv standalone installer one-liner — printed when uv is absent. We *point* at
# it rather than piping curl|sh ourselves: running a network installer is a
# large, hard-to-reverse side effect the user should trigger deliberately.
UV_INSTALL_HINT = "curl -LsSf https://astral.sh/uv/install.sh | sh"

# Default package spec installed into the new env. Overridable (e.g. `-e .` for
# a dev checkout, or a pinned version) so the same flow serves both onboarding
# and contributors.
DEFAULT_INSTALL_SPEC = "database-tycoon"


@dataclass
class VenvResult:
    """Outcome of a ``.venv`` build. ``ok`` gates the CLI's exit code."""

    ok: bool
    message: str
    venv_path: Path | None = None


def find_uv() -> str | None:
    """Return the path to the ``uv`` binary, or None if it isn't on PATH."""
    return shutil.which("uv")


def parse_python_version(spec: str) -> tuple[int, int]:
    """Parse a ``major.minor`` string into a tuple.

    Accepts ``"3.13"`` or ``"3.13.2"`` (patch is ignored). Raises
    ``ValueError`` on anything that isn't ``<int>.<int>[.<int>]``.
    """
    parts = spec.strip().split(".")
    if len(parts) < 2:
        raise ValueError(f"Expected a major.minor version like '3.13', got '{spec}'.")
    try:
        major, minor = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ValueError(f"Invalid Python version '{spec}'.") from exc
    return (major, minor)


def is_supported_version(version: tuple[int, int]) -> bool:
    """True if ``version`` is within tycoon's supported range ``[MIN, MAX)``."""
    return MIN_PYTHON <= version < MAX_PYTHON_EXCLUSIVE


def venv_path(project_root: Path) -> Path:
    """The project-local ``.venv`` directory."""
    return project_root / ".venv"


def venv_python(project_root: Path) -> Path:
    """Path to the venv's interpreter (POSIX ``bin/`` layout)."""
    return venv_path(project_root) / "bin" / "python"


def create_venv(
    project_root: Path,
    python_version: str = DEFAULT_SETUP_PYTHON,
    *,
    install_spec: str | None = DEFAULT_INSTALL_SPEC,
    force: bool = False,
) -> VenvResult:
    """Build a project-local ``.venv`` on a supported interpreter via uv.

    Steps, each short-circuiting to a friendly ``VenvResult`` on failure:

    1. Validate ``python_version`` is in the supported range.
    2. Require ``uv`` on PATH (point at the installer otherwise).
    3. Refuse to clobber an existing ``.venv`` unless ``force``.
    4. ``uv venv --python <X> <root>/.venv`` (uv fetches the interpreter).
    5. Write ``.python-version`` in the project dir to pin it.
    6. Install ``install_spec`` into the new env (skipped when None).

    Pure orchestration — all I/O is ``subprocess.run`` or small file writes,
    so it's exercised in tests with ``subprocess.run`` patched.
    """
    try:
        parsed = parse_python_version(python_version)
    except ValueError as exc:
        return VenvResult(ok=False, message=str(exc))

    if not is_supported_version(parsed):
        return VenvResult(
            ok=False,
            message=(
                f"Python {python_version} is outside tycoon's supported range "
                f"({python_range_str()}). dbt-core / dbt-duckdb have no wheels for "
                f"3.14 yet — pick {DEFAULT_SETUP_PYTHON}."
            ),
        )

    uv = find_uv()
    if uv is None:
        return VenvResult(
            ok=False,
            message=(
                "uv is not installed. tycoon uses uv to build the project "
                f"environment. Install it with:\n\n    {UV_INSTALL_HINT}\n\n"
                "then re-run `tycoon setup`."
            ),
        )

    target = venv_path(project_root)
    if target.exists() and not force:
        return VenvResult(
            ok=False,
            venv_path=target,
            message=(
                f"{target} already exists. Re-run with --force to recreate it "
                "(this removes the existing environment)."
            ),
        )

    # Step 4: create the venv. `uv venv --python 3.13 <path>` downloads a
    # python-build-standalone CPython if none matching is installed.
    create = subprocess.run(
        [uv, "venv", "--python", python_version, str(target)],
        capture_output=True,
        text=True,
    )
    if create.returncode != 0:
        return VenvResult(
            ok=False,
            venv_path=target,
            message=f"`uv venv` failed:\n{create.stderr.strip() or create.stdout.strip()}",
        )

    # Step 5: pin the interpreter for the project dir. Safe here — it only ever
    # broke CI when placed at the package repo root.
    (project_root / ".python-version").write_text(f"{python_version}\n")

    # Step 6: install tycoon (+ its dbt/dlt/duckdb deps) into the new env.
    if install_spec:
        install = subprocess.run(
            [uv, "pip", "install", "--python", str(venv_python(project_root)), install_spec],
            capture_output=True,
            text=True,
        )
        if install.returncode != 0:
            return VenvResult(
                ok=False,
                venv_path=target,
                message=(
                    f"Created {target} but installing '{install_spec}' failed:\n"
                    f"{install.stderr.strip() or install.stdout.strip()}"
                ),
            )

    pinned = "" if not install_spec else f" with '{install_spec}'"
    return VenvResult(
        ok=True,
        venv_path=target,
        message=f"Created {target} on Python {python_version}{pinned}.",
    )
