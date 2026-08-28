"""tycoon city — serve the project as an interactive 3D city.

The renderer (``tycoon_city``) ships inside this distribution, so it is always
present and there is no add-on to install. The import still happens inside
:func:`city_cmd` rather than at module scope: the renderer pulls in duckdb and
sqlglot, and no other command should pay that at startup just because this
module was registered.

That makes an ImportError here a damaged install rather than a missing
package, which is why the message reports the underlying error instead of
offering an install command that would not fix anything.

The project-root walk-up is duplicated here rather than imported from
``tycoon.config``. That module builds a cwd-bound singleton at import
(``config = TycoonConfig()``), which reads and validates ``tycoon.yml`` as a
side effect of the import itself, and its public ``load_config()`` helper
raises ``SystemExit`` on a newer ``schema_version``. Serving a directory
should not be able to fail either way, and the singleton's ``root`` is fixed
at import time, so it goes stale the moment anything changes directory.
"""

from __future__ import annotations

from pathlib import Path

import typer

from tycoon.project import PROJECT_FILENAME
from tycoon.utils.console import error, info

# The renderer ships in this wheel, so this line is for a broken install, not
# a missing one. It names the underlying error because "reinstall" is only
# actionable if the user can see what actually failed.
_UNAVAILABLE = (
    "city renderer unavailable ({error}) — this usually means a damaged install; try reinstalling database-tycoon"
)

# A MotherDuck catalog ("md:my_db", "md:_share/name/uuid") is a URI, not a
# filesystem path, and must reach the renderer untouched.
_MD_PREFIX = "md:"


def _project_root() -> Path:
    """Walk up from CWD to the directory holding tycoon.yml, else pyproject.toml."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / PROJECT_FILENAME).exists():
            return parent
        if (parent / "pyproject.toml").exists():
            return parent
    return current


def _serve_target(path: str | None) -> str:
    """Resolve --path (or the project root) into the renderer's positional argument.

    Filesystem paths are made absolute deliberately. ``webserve.main`` dispatches
    ``argv[0] == "demo"`` to the demo-catalog generator *before* argparse runs, so
    a relative ``--path demo`` would silently serve the built-in demo instead of
    the user's directory named ``demo``. An absolute path can never collide.
    """
    if path is None:
        return str(_project_root())
    if path.startswith(_MD_PREFIX):
        return path
    return str(Path(path).resolve())


def city_cmd(
    path: str = typer.Option(
        None,
        "--path",
        help="Project directory, DuckDB file, or md: catalog to render (default: this project).",
    ),
    port: int = typer.Option(8000, "--port", help="Port to serve on."),
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Interface to bind. The city names real schemas, tables and columns."
    ),
    theme: str = typer.Option("default", "--theme", help="Visual theme to render with."),
    dist: Path = typer.Option(
        None, "--dist", help="Built web bundle directory (defaults to the one shipped with tycoon)."
    ),
    pricing: Path = typer.Option(
        None, "--pricing", help="TOML file declaring the compute rate the budget block is billed at."
    ),
) -> None:
    """Serve this project's catalog as an interactive 3D city in the browser.

    Examples:

      tycoon city

      tycoon city --port 8080

      tycoon city --path data/warehouse.duckdb
    """
    try:
        from tycoon_city.webserve import main as serve
    except ImportError as exc:
        error(_UNAVAILABLE.format(error=exc))
        raise typer.Exit(1)

    target = _serve_target(path)

    argv = [target, "--port", str(port), "--host", host, "--theme", theme]
    if dist is not None:
        argv += ["--dist", str(dist)]
    if pricing is not None:
        argv += ["--pricing", str(pricing)]

    info(f"Serving {target} at http://{host}:{port} — Ctrl-C to stop.")
    try:
        code = serve(argv)
    except KeyboardInterrupt:
        raise typer.Exit(0)
    raise typer.Exit(code)
