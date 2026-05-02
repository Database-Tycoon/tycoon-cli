"""``tycoon docs`` — local docs site.

Shells out to MkDocs Material (the same tooling used to build the public
docs at https://database-tycoon.github.io/tycoon-cli/) so contributors
have one command to read the docs locally.

Requires the ``[docs]`` extra:

    pip install 'database-tycoon[docs]'
    tycoon docs serve
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import typer

from tycoon.utils.console import error, info, next_steps, success


app = typer.Typer(help="Local documentation site.")


def _mkdocs_executable() -> str | None:
    """Return the venv-colocated `mkdocs` binary if available, else None.

    Mirrors `_nao_executable` and `_dbt_executable` — prefer the binary
    next to ``sys.executable`` so we hit the version pinned in the
    project's environment rather than a globally-installed one.
    """
    venv_mkdocs = Path(sys.executable).parent / "mkdocs"
    if venv_mkdocs.exists():
        return str(venv_mkdocs)
    return shutil.which("mkdocs")


def _resolve_docs_root() -> Path | None:
    """Find the directory containing ``mkdocs.yml``.

    Tycoon runs from a clone of the source repo for now (``tycoon docs``
    isn't useful inside a user's project — there's no docs to serve there).
    Walk up from CWD looking for ``mkdocs.yml`` so the command works from
    any subdir of the source checkout.
    """
    for parent in [Path.cwd(), *Path.cwd().parents]:
        if (parent / "mkdocs.yml").exists():
            return parent
    return None


@app.command(name="serve")
def docs_serve(
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind."),
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        help="Host interface to bind to. Default keeps the server local-only.",
    ),
    no_open: bool = typer.Option(
        False, "--no-open", help="Don't try to open a browser."
    ),
) -> None:
    """Build the docs and serve them locally with hot-reload.

    Runs ``mkdocs serve`` against the project's ``mkdocs.yml``. The site
    rebuilds whenever you save a file under ``docs/``; refresh the
    browser to see changes.
    """
    mkdocs = _mkdocs_executable()
    if mkdocs is None:
        error(
            "MkDocs is not installed. Install the docs extra: "
            "[bold]pip install 'database-tycoon[docs]'[/bold]"
        )
        raise typer.Exit(1)

    root = _resolve_docs_root()
    if root is None:
        error(
            "No [bold]mkdocs.yml[/bold] found in the current directory or any "
            "parent. `tycoon docs serve` runs from a clone of the source repo."
        )
        raise typer.Exit(1)

    info(
        f"Serving docs from [bold]{root / 'docs'}[/bold] on "
        f"[bold]http://{host}:{port}[/bold]"
    )
    cmd = [mkdocs, "serve", "--dev-addr", f"{host}:{port}"]
    if no_open:
        cmd.append("--no-livereload")  # mkdocs doesn't have --no-open; quietest equivalent

    try:
        subprocess.run(cmd, cwd=str(root), check=False)
    except KeyboardInterrupt:
        # mkdocs prints its own shutdown message; just exit cleanly.
        pass


@app.command(name="build")
def docs_build(
    strict: bool = typer.Option(
        False, "--strict", help="Fail on warnings (broken links, missing pages, ...)."
    ),
) -> None:
    """One-shot build of the docs into ``site/`` without serving.

    Useful before committing — the same check runs in CI when public
    docs hosting is wired up.
    """
    mkdocs = _mkdocs_executable()
    if mkdocs is None:
        error(
            "MkDocs is not installed. Install the docs extra: "
            "[bold]pip install 'database-tycoon[docs]'[/bold]"
        )
        raise typer.Exit(1)

    root = _resolve_docs_root()
    if root is None:
        error("No [bold]mkdocs.yml[/bold] found in the current directory or any parent.")
        raise typer.Exit(1)

    cmd = [mkdocs, "build"]
    if strict:
        cmd.append("--strict")
    result = subprocess.run(cmd, cwd=str(root), check=False)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)

    success(f"Docs built to [bold]{root / 'site'}[/bold]")
    next_steps(
        ("tycoon docs serve", "preview locally"),
    )
