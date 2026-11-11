"""Top-level Typer app — entry point for the `tycoon` CLI."""

from __future__ import annotations

from collections.abc import Callable

import typer
from typer.core import TyperCommand, TyperGroup

import tycoon

_COMMAND_ORDER = [
    "init",
    "setup",
    "register",
    "profiles",
    "semantics",
    "data",
    "start",
    "stop",
    "city",
    "run",
    "notify",
    "schedule",
    "doctor",
    "docs",
]

_SECTIONS = {
    "init": "Project",
    "setup": "Project",
    "register": "Project",
    "profiles": "Project",
    "semantics": "Project",
    "data": "Data Pipeline",
    "start": "Services",
    "stop": "Services",
    "city": "Services",
    "run": "Tools",
    "notify": "Utilities",
    "schedule": "Utilities",
    "doctor": "Utilities",
    "docs": "Utilities",
}


class _ProjectContext(typer.Context):
    def invoke[T](self, callback: Callable[..., T], /, *args: object, **kwargs: object) -> T:
        # Typer handles eager help before invocation. A group that delegates to
        # a subcommand must wait for that subcommand to parse its own options.
        if callback is self.command.callback and self.invoked_subcommand is None:
            from tycoon.config import config

            config.ensure_valid()
        return super().invoke(callback, *args, **kwargs)


def _guard_project_commands(command: TyperCommand | TyperGroup) -> None:
    command.context_class = _ProjectContext
    if isinstance(command, TyperGroup):
        for child in command.commands.values():
            _guard_project_commands(child)


class _OrderedGroup(TyperGroup):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        for name, command in self.commands.items():
            if name not in {"city", "docs", "doctor", "init", "run"}:
                _guard_project_commands(command)

    def list_commands(self, ctx: object) -> list[str]:
        commands = super().list_commands(ctx)
        return sorted(commands, key=lambda c: _COMMAND_ORDER.index(c) if c in _COMMAND_ORDER else 99)

    def format_commands(self, ctx: object, formatter: object) -> None:
        seen: dict[str, list[tuple[str, str]]] = {}
        for name in self.list_commands(ctx):
            cmd = self.commands.get(name)
            if cmd is None or getattr(cmd, "hidden", False):
                continue
            section = _SECTIONS.get(name, "Commands")
            seen.setdefault(section, []).append((name, cmd.get_short_help_str(limit=formatter.width)))
        for section, rows in seen.items():
            with formatter.section(section):
                formatter.write_dl(rows)


_HELP_OPTION_NAMES = ["-h", "--help"]

app = typer.Typer(
    name="tycoon",
    help="Database Tycoon — local-first analytics CLI for exploring any dataset.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode=None,
    cls=_OrderedGroup,
    context_settings={"help_option_names": _HELP_OPTION_NAMES},
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"tycoon {tycoon.__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Print version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Run Database Tycoon commands."""


from tycoon.commands import data, profiles, register, semantics
from tycoon.commands import docs as docs_cmd_mod
from tycoon.commands.city import city_cmd
from tycoon.commands.doctor import doctor_cmd
from tycoon.commands.init import init_cmd
from tycoon.commands.notify import notify_cmd
from tycoon.commands.run import run_cmd
from tycoon.commands.schedule import app as schedule_app
from tycoon.commands.setup import setup_cmd
from tycoon.commands.start import start_cmd
from tycoon.commands.stop import stop_cmd

app.command(name="init")(init_cmd)
app.command(name="setup")(setup_cmd)
app.add_typer(register.app, name="register")
app.add_typer(profiles.app, name="profiles")
app.add_typer(semantics.app, name="semantics")
app.add_typer(data.app, name="data", no_args_is_help=True)
app.add_typer(docs_cmd_mod.app, name="docs")
app.command(name="start")(start_cmd)
app.command(name="stop")(stop_cmd)
app.command(name="city")(city_cmd)
app.command(
    name="run",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)(run_cmd)
app.command(name="notify")(notify_cmd)
app.add_typer(schedule_app, name="schedule")
app.command(name="doctor")(doctor_cmd)
