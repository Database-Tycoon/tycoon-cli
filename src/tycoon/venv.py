"""Manage a project-local ``.venv`` via uv (#57).

tycoon runs dbt out of the same interpreter it lives in (it resolves dbt at
``Path(sys.executable).parent / "dbt"``) and imports ``dlt``/``duckdb``
in-process. So the single most reliable onboarding step is to own the
environment: every project gets its own ``pyproject.toml`` and a
project-local ``.venv`` on a *supported* interpreter, with tycoon
(+ dbt + dlt + duckdb) installed into it, rather than inheriting whatever
``python3`` the user happens to have.

This module is the subprocess-isolated core behind ``tycoon setup`` and
``tycoon doctor --fix``. uv does the heavy lifting: ``uv sync`` auto-downloads
a python-build-standalone CPython if the machine only has an unsupported one
(e.g. 3.14), resolves and installs every dependency declared in the project's
``pyproject.toml``, and writes ``uv.lock`` so the exact same environment is
reproducible later by anyone with just ``uv sync`` (no ``tycoon setup``
required, no dependency on this module at all).

Everything that shells out goes through ``subprocess.run`` at module scope so
tests can patch ``tycoon.venv.subprocess.run`` (mirroring the source_installer
pattern) without ever creating a real environment.
"""

from __future__ import annotations

import re
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

# PEP 508 project names allow letters, digits, and `.`/`-`/`_`; anything else
# in a directory name (spaces, etc.) gets folded to `-`.
_INVALID_NAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")

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


def _project_name(project_root: Path) -> str:
    """Derive a PEP 508-safe project name from the project directory name."""
    name = _INVALID_NAME_CHARS.sub("-", project_root.name).strip("-")
    return name or "tycoon-project"


def _write_pyproject(project_root: Path, install_spec: str | None) -> None:
    """Seed a minimal pyproject.toml, if this project doesn't already have one.

    An existing pyproject.toml (hand-written, or from an earlier `tycoon
    setup`) is left untouched. ``install_spec`` is only pre-declared here
    when it's the plain default (`database-tycoon`) — a custom override
    (dev checkout, pinned version) is layered on afterward via `uv add`
    instead, so it isn't installed from PyPI first just to be replaced.
    """
    target = project_root / "pyproject.toml"
    if target.exists():
        return
    deps = f'    "{DEFAULT_INSTALL_SPEC}",\n' if install_spec == DEFAULT_INSTALL_SPEC else ""
    target.write_text(
        "[project]\n"
        f'name = "{_project_name(project_root)}"\n'
        'version = "0.1.0"\n'
        f'requires-python = "{python_range_str()}"\n'
        "dependencies = [\n"
        f"{deps}"
        "]\n"
    )


def _add_command(uv: str, project_root: Path, install_spec: str) -> list[str]:
    """Build the `uv add` command for a custom install_spec override.

    Mirrors the pip-style forms `--from` already documented: `-e <path>`,
    a bare local path, or a plain (optionally version-pinned) requirement.
    """
    spec = install_spec.strip()
    base = [uv, "--project", str(project_root), "add"]
    if spec.startswith("-e "):
        return [*base, "--editable", spec[3:].strip()]
    if spec in (".", "..") or spec.startswith(("./", "../", "/", "~")):
        return [*base, "--editable", spec]
    return [*base, spec]


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
    3. Refuse to clobber an existing ``.venv`` unless ``force`` (which
       removes it, and any ``uv.lock``, for a clean re-resolve).
    4. Write ``.python-version`` in the project dir to pin the interpreter.
    5. Seed ``pyproject.toml`` if this project doesn't already have one.
    6. ``uv sync`` — creates ``.venv`` (uv fetches the interpreter if
       needed), resolves, and installs whatever the project declares.
    7. A custom ``install_spec`` (dev checkout, pinned version) is layered
       on via ``uv add`` (skipped for the plain default, already declared
       in step 5, and skipped entirely when ``install_spec`` is None).

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
    if target.exists():
        if not force:
            return VenvResult(
                ok=False,
                venv_path=target,
                message=(
                    f"{target} already exists. Re-run with --force to recreate it "
                    "(this removes the existing environment)."
                ),
            )
        shutil.rmtree(target)
        lock = project_root / "uv.lock"
        if lock.exists():
            lock.unlink()

    # Step 4: pin the interpreter for the project dir. Safe here — it only ever
    # broke CI when placed at the package repo root.
    (project_root / ".python-version").write_text(f"{python_version}\n")

    # Step 5: seed pyproject.toml (no-op if the project already has one).
    _write_pyproject(project_root, install_spec)

    # Step 6: create + populate the venv from pyproject.toml. `uv sync`
    # downloads a python-build-standalone CPython if none matching is
    # installed, then resolves and installs, writing uv.lock.
    sync = subprocess.run(
        [uv, "--project", str(project_root), "sync"],
        capture_output=True,
        text=True,
    )
    if sync.returncode != 0:
        return VenvResult(
            ok=False,
            venv_path=target,
            message=f"`uv sync` failed:\n{sync.stderr.strip() or sync.stdout.strip()}",
        )

    # Step 7: a custom install_spec (dev checkout, pinned version) replaces
    # the default `database-tycoon` dependency via `uv add`.
    if install_spec and install_spec != DEFAULT_INSTALL_SPEC:
        add = subprocess.run(
            _add_command(uv, project_root, install_spec),
            capture_output=True,
            text=True,
        )
        if add.returncode != 0:
            return VenvResult(
                ok=False,
                venv_path=target,
                message=(
                    f"Created {target} but installing '{install_spec}' failed:\n"
                    f"{add.stderr.strip() or add.stdout.strip()}"
                ),
            )

    pinned = "" if not install_spec else f" with '{install_spec}'"
    return VenvResult(
        ok=True,
        venv_path=target,
        message=f"Created {target} on Python {python_version}{pinned}.",
    )
