"""Port checking and PID management utilities."""

from __future__ import annotations

import socket
import subprocess
import shutil


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Return True if something is listening on the given port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def find_pid_on_port(port: int) -> int | None:
    """Return the PID using the given port, or None."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip().split("\n")[0])
    except (subprocess.SubprocessError, ValueError):
        pass
    return None


def command_exists(name: str) -> bool:
    """Check if a command is available on PATH."""
    return shutil.which(name) is not None
