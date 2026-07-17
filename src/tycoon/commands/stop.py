"""tycoon stop — kill running tycoon servers."""

from __future__ import annotations

import os
import signal

import typer

from tycoon.constants import PORTS
from tycoon.utils.console import info, success, warn

_SERVER_NAMES = ["rill", "quack"]
_SERVER_PORTS = {name: PORTS[name] for name in _SERVER_NAMES}


def stop_cmd(
    services: list[str] = typer.Argument(
        default=None,
        help="Specific server(s) to stop. Defaults to all (rill, quack).",
    ),
) -> None:
    """Stop tycoon servers started by `tycoon start`."""
    from tycoon.commands.start import _pid_file, clear_pids

    targets = list(services) if services else _SERVER_NAMES

    pid_file = _pid_file()
    if pid_file.exists():
        _stop_via_pid_file(pid_file, targets)
    else:
        # Fallback: find processes by port using lsof
        info("No PID file found — finding processes by port...")
        _stop_via_ports(targets)

    clear_pids()


def _stop_via_pid_file(pid_file, targets: list[str]) -> None:
    import json

    pids: dict[str, int] = json.loads(pid_file.read_text())
    stopped_any = False

    for name in targets:
        pid = pids.get(name)
        if pid is None:
            warn(f"{name}: not in PID file")
            continue
        stopped_any = True
        _kill_pid(name, pid)

    if not stopped_any:
        info("Nothing to stop.")


def _stop_via_ports(targets: list[str]) -> None:
    import subprocess

    stopped_any = False
    for name in targets:
        port = _SERVER_PORTS.get(name)
        if port is None:
            continue
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
        )
        pids = [int(p) for p in result.stdout.strip().splitlines() if p.strip()]
        if not pids:
            info(f"{name}: nothing on port {port}")
            continue
        for pid in pids:
            _kill_pid(name, pid)
            stopped_any = True

    if not stopped_any:
        info("Nothing to stop.")


def _kill_pid(name: str, pid: int) -> None:
    """Kill *pid* and all of its descendants (SIGTERM, then SIGKILL stragglers)."""
    import time

    # Collect the full process tree (children first, then the root)
    all_pids = _collect_tree(pid)

    any_killed = False
    for p in all_pids:
        try:
            os.kill(p, signal.SIGTERM)
            any_killed = True
        except (ProcessLookupError, PermissionError):
            pass

    if not any_killed:
        warn(f"{name}: process {pid} not found (already stopped?)")
        return

    # Give processes a moment to exit, then SIGKILL survivors
    time.sleep(1)
    for p in all_pids:
        try:
            os.kill(p, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass

    success(f"Stopped {name} (PID {pid} + {len(all_pids) - 1} children)")


def _collect_tree(pid: int) -> list[int]:
    """Return all PIDs in the process tree rooted at *pid*, children first."""
    import subprocess

    children: list[int] = []
    try:
        result = subprocess.run(
            ["pgrep", "-P", str(pid)],
            capture_output=True,
            text=True,
        )
        for child in result.stdout.strip().splitlines():
            child_pid = int(child.strip())
            children.extend(_collect_tree(child_pid))
    except (ValueError, OSError):
        pass
    return children + [pid]
