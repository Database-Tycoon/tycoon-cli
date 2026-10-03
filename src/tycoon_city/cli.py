"""`tycoon-city` -- the renderer's own console script, as a Typer app.

`tycoon city` (in the `tycoon` package) is the integrated entry point: it finds
your project and hands the renderer an absolute path. This is the renderer
alone, for a catalog with no project around it, and for renderer development.

It is Typer rather than argparse so that `tycoon-city --help` and
`tycoon-city demo --help` render the way every other tycoon command does; the
two surfaces used to sit side by side looking like two different tools. The
argparse `main()` in `webserve` stays for `python -m tycoon_city.webserve` and
the Docker image, and both surfaces land in the same `run_server` and
`demo.cli.run` -- one server, one demo, two ways to type each.
"""

from __future__ import annotations

from pathlib import Path

import click
import typer
from typer.core import TyperGroup

from . import webserve

SERVE_COMMAND = "serve"


class _PathOrCommand(TyperGroup):
    """`tycoon-city path/to/db.duckdb` is the documented shorthand for
    `tycoon-city serve path/to/db.duckdb`, and this is where it stays legal.

    A positional argument on the GROUP would have been simpler, but Click
    consumes a group's own arguments before it looks for a subcommand, so
    `tycoon-city demo` would have served a catalog called "demo" and
    `tycoon-city demo --help` would have printed the wrong help. Routing here
    keeps `demo` a real subcommand with its own help, and keeps the bare
    invocation (`tycoon-city`, path from $DATABASE_TYCOON_DB) working through
    Click's ordinary parsing, env vars included.
    """

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if not args or (args[0] not in self.commands and args[0] not in ctx.help_option_names):
            args = [SERVE_COMMAND, *args]
        return super().parse_args(ctx, args)


# Mirrors `tycoon.cli.app`'s rendering settings on purpose -- plain help, no
# Rich boxes, a `-h` alias -- so the two scripts' help screens are one style.
# Duplicated rather than imported: tycoon_city does not depend on tycoon.
app = typer.Typer(
    name="tycoon-city",
    cls=_PathOrCommand,
    add_completion=False,
    pretty_exceptions_enable=False,
    rich_markup_mode=None,
    context_settings={"help_option_names": ["-h", "--help"]},
    help=(
        "Serve the interactive Database Tycoon city for a DuckDB catalog. "
        "`tycoon-city PATH` is shorthand for `tycoon-city serve PATH`."
    ),
)


@app.command(name=SERVE_COMMAND)
def serve_cmd(
    db_path: str = typer.Argument(
        None,
        envvar=webserve.DB_ENV,
        show_default=False,
        help="DuckDB file, md: catalog, or tycoon project directory.",
    ),
    dist: Path = typer.Option(
        None,
        "--dist",
        envvar=webserve.DIST_ENV,
        help="Built web bundle directory (defaults to the one shipped with tycoon).",
    ),
    theme: str = typer.Option("default", "--theme", envvar=webserve.THEME_ENV, help="Visual theme to render with."),
    pricing: Path = typer.Option(
        None,
        "--pricing",
        help=(
            "TOML file declaring the compute rate the budget block is billed at "
            "(default: pricing.toml beside the catalog, else local DuckDB, free)."
        ),
    ),
    port: int = typer.Option(webserve.DEFAULT_PORT, "--port", envvar="PORT", help="Port to serve on."),
    host: str = typer.Option(
        webserve.DEFAULT_HOST,
        "--host",
        envvar=webserve.HOST_ENV,
        help=(
            "Interface to bind. The city names real schemas, tables and columns -- "
            "pass 0.0.0.0 only when you mean to publish them."
        ),
    ),
) -> None:
    """Serve the interactive Database Tycoon city for a DuckDB catalog.

    Examples:

      tycoon-city path/to/warehouse.duckdb

      tycoon-city serve md:my_catalog --port 8080

      tycoon-city                     (path from $DATABASE_TYCOON_DB)
    """
    try:
        code = webserve.run_server(
            db_path=db_path,
            dist=dist,
            theme=theme,
            pricing=str(pricing) if pricing is not None else None,
            port=port,
            host=host,
        )
    except KeyboardInterrupt:
        raise typer.Exit(0)
    raise typer.Exit(code)


@app.command(name="demo")
def demo_cmd(
    port: int = typer.Option(webserve.DEFAULT_PORT, "--port", envvar="PORT", help="Port to serve on."),
    host: str = typer.Option(
        webserve.DEFAULT_HOST,
        "--host",
        envvar=webserve.HOST_ENV,
        help="Interface to bind. The demo catalog is synthetic, so widening it exposes nothing of yours.",
    ),
    theme: str = typer.Option("default", "--theme", help="Visual theme to render with."),
    dist: Path = typer.Option(
        None,
        "--dist",
        envvar=webserve.DIST_ENV,
        help="Built web bundle directory (defaults to the one shipped with tycoon).",
    ),
) -> None:
    """Serve a generated demo catalog with nothing to set up.

    A whole tycoon project -- runs, tests, a failure cascade, freshness
    verdicts and a semantic model -- generated into a temp directory and
    served exactly as an ordinary serve would. Same server, same routes, same
    document; only the catalog is invented. Nothing is written outside $TMPDIR.
    """
    # Lazy: the generator writes DuckDB files, and an ordinary serve must never
    # load it.
    from .demo import cli as demo_cli

    try:
        code = demo_cli.run(port=port, host=host, theme=theme, dist=dist)
    except KeyboardInterrupt:
        raise typer.Exit(0)
    raise typer.Exit(code)
