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


def _project_name(project_root: Path) -> str:
    """Derive a PEP 508-safe project name from the project directory name.

    A PEP 508 name must start and end with a letter or digit; mid-string
    `.`/`_`/`-` are fine. Also guards against colliding with the
    `database-tycoon` dependency itself (a project directory literally
    named that would otherwise self-reference).
    """
    name = _INVALID_NAME_CHARS.sub("-", project_root.name).strip("._-")
    if not name or name == DEFAULT_INSTALL_SPEC:
        return "tycoon-project"
    return name


def _write_pyproject(project_root: Path) -> None:
    """Seed a minimal pyproject.toml, if this project doesn't already have one.

    An existing pyproject.toml (hand-written, or from an earlier `tycoon
    setup`) is left untouched. Dependencies are never pre-declared here,
    `create_venv` always installs `install_spec` afterward via `uv add`,
    which is idempotent and handles both the fresh-skeleton case and an
    existing pyproject that doesn't yet declare it.
    """
    target = project_root / "pyproject.toml"
    if target.exists():
        return
    target.write_text(
        "[project]\n"
        f'name = "{_project_name(project_root)}"\n'
        'version = "0.1.0"\n'
        f'requires-python = "{python_range_str()}"\n'
        "dependencies = [\n"
        "]\n"
    )


def _add_command(uv: str, project_root: Path, python_version: str, install_spec: str) -> list[str]:
    """Build the `uv add` command for an install_spec.

    Only the explicit pip-style `-e <path>` form needs translation (uv's
    own flag is `--editable`, not `-e`); everything else, including a bare
    local path to a wheel/sdist or a source checkout, passes straight
    through for uv to classify itself.
    """
    spec = install_spec.strip()
    base = [uv, "--project", str(project_root), "add", "--python", python_version]
    if spec.startswith("-e "):
        path = str(Path(spec[3:].strip()).expanduser())
        return [*base, "--editable", path]
    return [*base, spec]


def _run(cmd: list[str]) -> tuple[bool, str]:
    """Run a uv subprocess, returning (ok, stderr-or-stdout on failure)."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return True, ""
    return False, result.stderr.strip() or result.stdout.strip()


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
    4. Write ``.python-version`` in the project dir to pin the interpreter.
    5. Seed ``pyproject.toml`` if this project doesn't already have one
       (no dependencies declared yet, so this is safe even when one
       already exists with its own unrelated dependencies).
    6. ``uv sync --python <version>``, creates ``.venv`` (uv fetches the
       interpreter if needed) and installs whatever the project already
       declares. ``force`` adds ``--upgrade`` so an existing `.venv`/
       `uv.lock` is reconciled and re-resolved in place rather than
       deleted outright, uv's own job, and safe for a stray non-directory
       `.venv` (a symlink, a plain file) that a manual `rmtree` isn't.
    7. ``install_spec`` (the default `database-tycoon`, a pinned version,
       or a dev checkout) is installed via ``uv add --python <version>``,
       idempotent, so it runs every time ``install_spec`` is given rather
       than only when it differs from the default, skipped entirely when
       ``install_spec`` is None (``--no-install``).

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
                message=f"{target} already exists. Re-run with --force to rebuild it.",
            )

    # Step 4: pin the interpreter for the project dir. Safe here — it only ever
    # broke CI when placed at the package repo root.
    (project_root / ".python-version").write_text(f"{python_version}\n")

    # Step 5: seed pyproject.toml (no-op if the project already has one).
    _write_pyproject(project_root)

    # Step 6: create + reconcile the venv. `--python` pins the exact
    # interpreter explicitly rather than relying on `.python-version` alone,
    # which `UV_PYTHON` would otherwise silently outrank. `--upgrade` under
    # `force` re-resolves fresh instead of deleting `.venv`/`uv.lock`.
    sync_cmd = [uv, "--project", str(project_root), "sync", "--python", python_version]
    if force:
        sync_cmd.append("--upgrade")
    ok, err = _run(sync_cmd)
    if not ok:
        return VenvResult(ok=False, venv_path=target, message=f"`uv sync` failed:\n{err}")

    # `UV_PROJECT_ENVIRONMENT` or a `[tool.uv.workspace]` root above this
    # project can redirect uv to build the environment somewhere other than
    # `<project_root>/.venv`, don't claim success for a path that isn't real.
    if not target.exists():
        return VenvResult(
            ok=False,
            venv_path=target,
            message=(
                f"`uv sync` succeeded but {target} doesn't exist. Something in this "
                "project's uv configuration (UV_PROJECT_ENVIRONMENT, a [tool.uv.workspace] "
                "root above it, or similar) is redirecting where the environment gets built."
            ),
        )

    # Step 7: install_spec (default, pinned version, or dev checkout) via
    # `uv add`, idempotent, so an already-declared dependency is a no-op.
    if install_spec:
        ok, err = _run(_add_command(uv, project_root, python_version, install_spec))
        if not ok:
            return VenvResult(
                ok=False,
                venv_path=target,
                message=f"Created {target} but installing '{install_spec}' failed:\n{err}",
            )

    pinned = "" if not install_spec else f" with '{install_spec}'"
    return VenvResult(
        ok=True,
        venv_path=target,
        message=f"Created {target} on Python {python_version}{pinned}.",
    )
