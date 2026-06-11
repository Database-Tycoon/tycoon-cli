"""tycoon schedule — add/list/remove/status for local scheduled runs (#48)."""

from __future__ import annotations

import shlex

import typer

from tycoon import schedule as sched
from tycoon.config import config
from tycoon.utils.console import console, error, header, info, success

app = typer.Typer(help="Schedule tycoon commands to run via launchd / systemd.")


@app.command("add")
def add_schedule(
    name: str = typer.Argument(help="Schedule name (lowercase, e.g. 'daily-refresh')."),
    command: str = typer.Option(
        "data run-all",
        "--command",
        "-c",
        help="The tycoon command to run, e.g. \"data run-all --notify\".",
    ),
    at: str = typer.Option("04:00", "--at", help="Time of day (24h HH:MM)."),
    cadence: str = typer.Option(
        "daily",
        "--cadence",
        help="daily (at --at), hourly (at --at's minute), or weekly (--weekday at --at).",
    ),
    weekday: int = typer.Option(1, "--weekday", help="Weekly cadence: 1=Mon .. 7=Sun."),
    notify: bool = typer.Option(
        False, "--notify", help="Append --notify to the scheduled command."
    ),
    force: bool = typer.Option(False, "--force", help="Replace an existing schedule of the same name."),
) -> None:
    """Install a scheduled run of a tycoon command.

    macOS uses a launchd LaunchAgent; Linux uses a ``systemd --user`` timer.
    Output lands in ``~/.local/share/tycoon/schedule/<name>/run.log``.
    """
    if not config.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)

    if cadence not in ("daily", "hourly", "weekly"):
        error("--cadence must be one of: daily, hourly, weekly.")
        raise typer.Exit(2)

    try:
        sched.validate_name(name)
        hour, minute = sched.parse_time(at)
    except sched.ScheduleError as exc:
        error(str(exc))
        raise typer.Exit(2) from exc

    if name in sched.list_schedules() and not force:
        error(f"Schedule '{name}' already exists. Pass --force to replace it.")
        raise typer.Exit(1)

    args = shlex.split(command)
    # Tolerate a redundant leading "tycoon" (e.g. --command "tycoon data run-all")
    # — the wrapper already invokes the tycoon program, so a kept prefix would
    # run `tycoon tycoon data run-all` and fail.
    if args and args[0] == "tycoon":
        args = args[1:]
    if not args:
        error("--command cannot be empty.")
        raise typer.Exit(2)
    if notify and "--notify" not in args:
        args.append("--notify")

    spec = sched.ScheduleSpec(
        name=name,
        args=args,
        hour=hour,
        minute=minute,
        cadence=cadence,
        weekday=weekday,
        project_root=config.root,
    )

    header("Schedule")
    try:
        message = sched.add(spec)
    except sched.ScheduleError as exc:
        error(str(exc))
        raise typer.Exit(1) from exc

    success(message)
    info(f"Runs: tycoon {' '.join(args)}  ({_describe(spec)})")
    info(f"Logs: {sched.log_file(name)}")


@app.command("list")
def list_cmd() -> None:
    """List installed tycoon schedules on this platform."""
    names = sched.list_schedules()
    if not names:
        info("No tycoon schedules installed.")
        return
    header("Schedules")
    for name in names:
        console.print(f"  • [cyan]{name}[/cyan]")


@app.command("remove")
def remove_cmd(
    name: str = typer.Argument(help="Schedule name to remove."),
) -> None:
    """Unload and delete a schedule's unit files."""
    try:
        message = sched.remove(name)
    except sched.ScheduleError as exc:
        error(str(exc))
        raise typer.Exit(1) from exc
    success(message)


@app.command("status")
def status_cmd(
    name: str = typer.Argument(help="Schedule name to inspect."),
    lines: int = typer.Option(20, "--lines", "-n", help="Log lines to show."),
) -> None:
    """Show whether a schedule is installed and tail its most recent log."""
    if name not in sched.list_schedules():
        error(f"No schedule named '{name}'. See `tycoon schedule list`.")
        raise typer.Exit(1)

    header(f"Schedule: {name}")
    success("Installed.")
    log = sched.tail_log(name, lines=lines)
    if log:
        console.print(f"\n[bold]Last log ({sched.log_file(name)}):[/bold]")
        console.print(log)
    else:
        info("No run log yet — the schedule hasn't fired (or produced output) since install.")


def _describe(spec: sched.ScheduleSpec) -> str:
    if spec.cadence == "hourly":
        return f"hourly at :{spec.minute:02d}"
    if spec.cadence == "weekly":
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return f"weekly on {days[(spec.weekday - 1) % 7]} at {spec.hour:02d}:{spec.minute:02d}"
    return f"daily at {spec.hour:02d}:{spec.minute:02d}"
