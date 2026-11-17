"""tycoon setup — build a project-local ``.venv`` on a supported interpreter (#57)."""

from __future__ import annotations

import typer

from tycoon.config import config
from tycoon.constants import DEFAULT_SETUP_PYTHON
from tycoon.utils.console import console, error, header, info, next_steps, success, warn
from tycoon.venv import DEFAULT_INSTALL_SPEC, create_venv, find_uv, venv_path


def setup_cmd(
    python: str = typer.Option(
        DEFAULT_SETUP_PYTHON,
        "--python",
        help=(
            "Python version for the project `.venv` (major.minor). Must be in "
            "tycoon's supported range. uv downloads it if it isn't installed."
        ),
    ),
    install_spec: str = typer.Option(
        DEFAULT_INSTALL_SPEC,
        "--from",
        help=(
            "Package spec to install into the new env. Defaults to the published "
            "`database-tycoon`; pass `-e <path>` for an editable dev checkout "
            "(an absolute path, not `-e .`, which would self-reference this project)."
        ),
    ),
    no_install: bool = typer.Option(
        False,
        "--no-install",
        help="Create and pin the `.venv` but skip installing tycoon into it.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Rebuild the `.venv` if one already exists (re-resolves dependencies fresh).",
    ),
    no_prompt: bool = typer.Option(
        False,
        "--no-prompt",
        help="Skip confirmation prompts. For CI / scripted bootstrap.",
    ),
) -> None:
    """Create a project-local ``.venv`` with a supported Python via uv.

    tycoon runs dbt out of the same interpreter it lives in, so a mismatched
    Python is the most common first-mile failure. ``setup`` owns the
    environment: it seeds a ``pyproject.toml`` beside ``tycoon.yml`` (if one
    doesn't already exist), builds one ``.venv`` on a supported interpreter
    via ``uv sync``, pins it with ``.python-version``, and installs tycoon +
    its dbt/dlt/duckdb stack into it, writing ``uv.lock`` for reproducibility.
    """
    if not config.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    project_root = config.root
    header("Tycoon Setup")

    if find_uv() is None:
        # create_venv would also catch this, but failing here keeps the message
        # at the top before we've touched anything.
        error(
            "uv is not installed. tycoon uses uv to build the project environment.\n"
            "  Install it with:  curl -LsSf https://astral.sh/uv/install.sh | sh\n"
            "  then re-run `tycoon setup`."
        )
        raise typer.Exit(1)

    target = venv_path(project_root)
    if target.exists() and not force and not no_prompt:
        recreate = typer.confirm(
            f"{target} already exists. Rebuild it? (re-resolves dependencies fresh)",
            default=False,
        )
        if not recreate:
            info("Left the existing environment in place. Nothing to do.")
            raise typer.Exit(0)
        force = True

    info(f"Building {target} on Python {python} via uv...")
    if no_install:
        info("Skipping tycoon install (--no-install).")

    with console.status(f"Building {target} via uv..."):
        result = create_venv(
            project_root,
            python,
            install_spec=None if no_install else install_spec,
            force=force,
        )

    if not result.ok:
        error(result.message)
        raise typer.Exit(1)

    success(result.message)
    warn(
        "This new environment is separate from the interpreter running tycoon "
        "right now — activate it so subsequent commands use it."
    )
    next_steps(
        ("source .venv/bin/activate", "use the new environment"),
        ("tycoon doctor", "confirm the interpreter is now in range"),
    )
