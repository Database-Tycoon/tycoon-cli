"""tycoon data — data pipeline management."""

from __future__ import annotations

import typer

app = typer.Typer(help="Data pipeline — sources, ingestion, transforms, and exploration.")


def _register() -> None:
    """Wire sub-commands. Called once at import to avoid circular imports."""
    from tycoon.commands import db, history, observability, sources, transform
    from tycoon.commands.explore import analyze_cmd
    from tycoon.commands.run_all import run_all_cmd
    from tycoon.commands.status import status_cmd
    from tycoon.commands.sync_cmd import sync_cmd

    app.add_typer(sources.app, name="sources")
    app.add_typer(transform.app, name="transform")
    app.add_typer(history.app, name="history")
    app.add_typer(observability.app, name="observability")
    app.command(name="query")(db.query)
    app.command(name="schema")(db.schema)
    app.command(name="clean")(db.clean)
    app.command(name="analyze")(analyze_cmd)
    app.command(name="run-all")(run_all_cmd)
    app.command(name="status")(status_cmd)
    app.command(name="sync")(sync_cmd)


_register()
