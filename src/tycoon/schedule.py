"""Local scheduled pipeline runs (#48) — launchd / systemd-user wrapper.

Once `tycoon data run-all` works, the next question is "how do I run this every
morning?" The local-first answer is one command instead of hand-writing cron /
launchd / systemd units. `tycoon schedule` wraps the platform-native scheduler:
macOS launchd LaunchAgents, Linux ``systemd --user`` timers. No daemon, no
cloud.

This module is the platform glue — spec validation, unit-file rendering, and
the add/list/remove/status primitives. The scheduler calls (``launchctl`` /
``systemctl``) go through ``subprocess.run`` at module scope so tests can patch
them while exercising the real file rendering against a temp HOME.
"""

from __future__ import annotations

import plistlib
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# launchd label prefix / systemd unit prefix — also the glob key for `list`.
LAUNCHD_PREFIX = "com.databasetycoon."
SYSTEMD_PREFIX = "tycoon-"

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_CADENCES = ("daily", "hourly", "weekly")


class ScheduleError(RuntimeError):
    """Raised with a user-facing message for invalid specs / scheduler failures."""


@dataclass
class ScheduleSpec:
    """A scheduled tycoon run."""

    name: str
    args: list[str]              # tycoon args, e.g. ["data", "run-all", "--notify"]
    hour: int = 4
    minute: int = 0
    cadence: str = "daily"       # daily | hourly | weekly
    weekday: int = 1             # 1=Mon .. 7=Sun (weekly only)
    project_root: Path = field(default_factory=Path.cwd)


# ---------------------------------------------------------------------------
# Validation / helpers
# ---------------------------------------------------------------------------


def validate_name(name: str) -> None:
    if not _NAME_RE.match(name):
        raise ScheduleError(
            f"Invalid schedule name '{name}'. Use lowercase letters, digits, and "
            "hyphens (e.g. 'daily-refresh')."
        )


def _reject_control_chars(spec: ScheduleSpec) -> None:
    """Refuse argv tokens / project paths carrying line breaks or NUL (#67).

    systemd unit files are line-oriented INI: a newline smuggled through a
    quoted `--command` token (shlex.split preserves them) or a directory name
    would inject extra unit directives that run on every timer fire. launchd
    is immune (plistlib escapes everything), but no legitimate value contains
    these characters, so reject on every platform before rendering.
    """
    for value in [*spec.args, str(spec.project_root)]:
        if any(c in value for c in ("\n", "\r", "\0")):
            raise ScheduleError(
                "Schedule command arguments and project path must not contain "
                "newline, carriage-return, or NUL characters."
            )


def parse_time(at: str) -> tuple[int, int]:
    """Parse ``HH:MM`` into (hour, minute). Raises ScheduleError on bad input."""
    m = re.match(r"^(\d{1,2}):(\d{2})$", at.strip())
    if not m:
        raise ScheduleError(f"Invalid --at '{at}'. Expected HH:MM (24h), e.g. 04:00.")
    hour, minute = int(m.group(1)), int(m.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ScheduleError(f"Invalid time '{at}'. Hour 0-23, minute 0-59.")
    return hour, minute


def current_platform() -> str:
    """Return 'darwin', 'linux', or the raw sys.platform for anything else."""
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform.startswith("linux"):
        return "linux"
    return sys.platform


def tycoon_program() -> list[str]:
    """Resolve how to invoke tycoon from a scheduler context (no inherited PATH).

    Prefer the absolute ``tycoon`` console script next to the interpreter;
    fall back to ``<python> -m tycoon``.
    """
    script = shutil.which("tycoon")
    if script:
        return [script]
    return [sys.executable, "-m", "tycoon"]


def log_dir(name: str, home: Path | None = None) -> Path:
    home = home or Path.home()
    return home / ".local" / "share" / "tycoon" / "schedule" / name


def log_file(name: str, home: Path | None = None) -> Path:
    return log_dir(name, home) / "run.log"


# ---------------------------------------------------------------------------
# launchd (macOS)
# ---------------------------------------------------------------------------


def launch_agents_dir(home: Path | None = None) -> Path:
    home = home or Path.home()
    return home / "Library" / "LaunchAgents"


def launchd_label(name: str) -> str:
    return f"{LAUNCHD_PREFIX}{name}"


def launchd_plist_path(name: str, home: Path | None = None) -> Path:
    return launch_agents_dir(home) / f"{launchd_label(name)}.plist"


def render_launchd_plist(spec: ScheduleSpec, home: Path | None = None) -> bytes:
    """Render the LaunchAgent plist for ``spec`` as bytes."""
    interval: dict[str, int]
    if spec.cadence == "hourly":
        interval = {"Minute": spec.minute}
    elif spec.cadence == "weekly":
        interval = {"Weekday": spec.weekday % 7, "Hour": spec.hour, "Minute": spec.minute}
    else:  # daily
        interval = {"Hour": spec.hour, "Minute": spec.minute}

    log = log_file(spec.name, home)
    plist = {
        "Label": launchd_label(spec.name),
        "ProgramArguments": tycoon_program() + spec.args,
        "StartCalendarInterval": interval,
        "WorkingDirectory": str(spec.project_root),
        "StandardOutPath": str(log),
        "StandardErrorPath": str(log),
        "RunAtLoad": False,
    }
    return plistlib.dumps(plist)


# ---------------------------------------------------------------------------
# systemd --user (Linux)
# ---------------------------------------------------------------------------


def systemd_user_dir(home: Path | None = None) -> Path:
    home = home or Path.home()
    return home / ".config" / "systemd" / "user"


def systemd_unit_base(name: str) -> str:
    return f"{SYSTEMD_PREFIX}{name}"


def _systemd_oncalendar(spec: ScheduleSpec) -> str:
    if spec.cadence == "hourly":
        return f"*-*-* *:{spec.minute:02d}:00"
    if spec.cadence == "weekly":
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day = days[(spec.weekday - 1) % 7]
        return f"{day} *-*-* {spec.hour:02d}:{spec.minute:02d}:00"
    return f"*-*-* {spec.hour:02d}:{spec.minute:02d}:00"  # daily


def _systemd_quote(arg: str) -> str:
    """Quote one argv token per systemd.service "Command lines" rules.

    Double-quote the token, escaping backslash and double-quote, and double
    ``$``/``%`` so systemd's env-var and specifier expansion can't rewrite
    argument content — the same argv-preserving discipline plistlib gives
    the launchd path, so tokens always round-trip verbatim.
    """
    escaped = arg.replace("%", "%%").replace("$", "$$")
    escaped = escaped.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_systemd_service(spec: ScheduleSpec, home: Path | None = None) -> str:
    # WorkingDirectory takes its value literally (systemd does no quote
    # removal on single-path settings), so it is emitted raw; `add()` rejects
    # the control characters that could break out of its line.
    exec_start = " ".join(_systemd_quote(a) for a in tycoon_program() + spec.args)
    log = log_file(spec.name, home)
    return (
        "[Unit]\n"
        f"Description=tycoon scheduled run: {spec.name}\n\n"
        "[Service]\n"
        "Type=oneshot\n"
        f"WorkingDirectory={spec.project_root}\n"
        f"ExecStart={exec_start}\n"
        f"StandardOutput=append:{log}\n"
        f"StandardError=append:{log}\n"
    )


def render_systemd_timer(spec: ScheduleSpec) -> str:
    return (
        "[Unit]\n"
        f"Description=tycoon schedule timer: {spec.name}\n\n"
        "[Timer]\n"
        f"OnCalendar={_systemd_oncalendar(spec)}\n"
        "Persistent=true\n\n"
        "[Install]\n"
        "WantedBy=timers.target\n"
    )


# ---------------------------------------------------------------------------
# add / list / remove / status (platform-dispatched)
# ---------------------------------------------------------------------------


def add(spec: ScheduleSpec, home: Path | None = None) -> str:
    """Install a schedule. Returns a human-readable confirmation.

    Raises ScheduleError on an unsupported platform or a scheduler failure.
    """
    validate_name(spec.name)
    _reject_control_chars(spec)
    home = home or Path.home()
    plat = current_platform()
    log_dir(spec.name, home).mkdir(parents=True, exist_ok=True)

    if plat == "darwin":
        path = launchd_plist_path(spec.name, home)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(render_launchd_plist(spec, home))
        _run(["launchctl", "unload", str(path)], check=False)  # idempotent reload
        _run(["launchctl", "load", str(path)])
        return f"Scheduled '{spec.name}' via launchd ({path})."

    if plat == "linux":
        unit_dir = systemd_user_dir(home)
        unit_dir.mkdir(parents=True, exist_ok=True)
        base = systemd_unit_base(spec.name)
        (unit_dir / f"{base}.service").write_text(render_systemd_service(spec, home))
        (unit_dir / f"{base}.timer").write_text(render_systemd_timer(spec))
        _run(["systemctl", "--user", "daemon-reload"])
        _run(["systemctl", "--user", "enable", "--now", f"{base}.timer"])
        return f"Scheduled '{spec.name}' via systemd --user ({base}.timer)."

    raise ScheduleError(
        f"Scheduling isn't supported on this platform ({plat}). On Windows, use "
        "Task Scheduler to run `tycoon "
        + " ".join(spec.args)
        + "` — see the docs."
    )


def list_schedules(home: Path | None = None) -> list[str]:
    """Return the names of tycoon-managed schedules on this platform."""
    home = home or Path.home()
    plat = current_platform()
    if plat == "darwin":
        d = launch_agents_dir(home)
        if not d.exists():
            return []
        names = [
            p.stem[len(LAUNCHD_PREFIX):]
            for p in sorted(d.glob(f"{LAUNCHD_PREFIX}*.plist"))
        ]
        return names
    if plat == "linux":
        d = systemd_user_dir(home)
        if not d.exists():
            return []
        return [
            p.stem[len(SYSTEMD_PREFIX):]
            for p in sorted(d.glob(f"{SYSTEMD_PREFIX}*.timer"))
        ]
    return []


def remove(name: str, home: Path | None = None) -> str:
    """Unload + delete a schedule's unit files. Raises if it doesn't exist."""
    validate_name(name)
    home = home or Path.home()
    plat = current_platform()

    if plat == "darwin":
        path = launchd_plist_path(name, home)
        if not path.exists():
            raise ScheduleError(f"No schedule named '{name}'.")
        _run(["launchctl", "unload", str(path)], check=False)
        path.unlink()
        return f"Removed schedule '{name}'."

    if plat == "linux":
        base = systemd_unit_base(name)
        unit_dir = systemd_user_dir(home)
        timer = unit_dir / f"{base}.timer"
        service = unit_dir / f"{base}.service"
        if not timer.exists() and not service.exists():
            raise ScheduleError(f"No schedule named '{name}'.")
        _run(["systemctl", "--user", "disable", "--now", f"{base}.timer"], check=False)
        for f in (timer, service):
            if f.exists():
                f.unlink()
        _run(["systemctl", "--user", "daemon-reload"], check=False)
        return f"Removed schedule '{name}'."

    raise ScheduleError(f"Scheduling isn't supported on this platform ({plat}).")


def tail_log(name: str, lines: int = 20, home: Path | None = None) -> str | None:
    """Return the last ``lines`` of a schedule's run log, or None if absent."""
    path = log_file(name, home)
    if not path.exists():
        return None
    try:
        content = path.read_text(errors="replace").splitlines()
    except OSError:
        return None
    return "\n".join(content[-lines:])


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a scheduler command, raising ScheduleError on failure when check."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ScheduleError(f"Failed to run {cmd[0]}: {exc}") from exc
    if check and result.returncode != 0:
        raise ScheduleError(
            f"`{' '.join(cmd)}` failed (exit {result.returncode}):\n"
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result
