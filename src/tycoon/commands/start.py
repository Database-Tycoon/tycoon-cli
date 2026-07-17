"""tycoon start — launch the long-running servers."""

from __future__ import annotations

import json
import signal
import subprocess
import threading
from pathlib import Path

import typer

from tycoon.config import config
from tycoon.utils.console import console, error, header, info, success, warn

_SERVER_NAMES = ["rill", "quack"]

_PID_FILE = Path(".tycoon") / "run" / "pids.json"


def _pid_file() -> Path:
    return config.root / _PID_FILE


def write_pids(pids: dict[str, int]) -> None:
    path = _pid_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pids, indent=2))


def clear_pids() -> None:
    path = _pid_file()
    if path.exists():
        path.unlink()


def start_cmd(
    skip: list[str] = typer.Option(
        [], "--skip", help="Server(s) to skip. Repeatable: --skip rill"
    ),
    only: list[str] = typer.Option(
        [], "--only", help="Only start these server(s). Repeatable: --only rill"
    ),
) -> None:
    """Start the Rill dashboard and Quack warehouse server.

    All servers run as background processes in this session.
    Press Ctrl-C or run `tycoon stop` to shut everything down.
    """
    targets = _resolve_targets(skip, only)
    if not targets:
        error("No servers to start.")
        raise typer.Exit(1)

    _preflight_checks(targets)
    if not targets:
        error("No servers to start.")
        raise typer.Exit(1)

    pids: dict[str, int] = {}
    procs: dict[str, subprocess.Popen] = {}
    header("Tycoon")

    for name in targets:
        proc = _start_server(name)
        if proc is not None:
            procs[name] = proc
            pids[name] = proc.pid

    if pids:
        write_pids(pids)

    console.print()
    _print_urls(targets)
    console.print()
    info("Press [bold]Ctrl-C[/bold] or run [bold]tycoon stop[/bold] to shut down.")

    shutdown = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: shutdown.set())
    signal.signal(signal.SIGTERM, lambda *_: shutdown.set())
    shutdown.wait()

    console.print()
    info("Shutting down...")
    for proc in procs.values():
        try:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            pass
    clear_pids()
    info("Done.")


def _resolve_targets(skip: list[str], only: list[str]) -> list[str]:
    if only:
        unknown = [n for n in only if n not in _SERVER_NAMES]
        for u in unknown:
            warn(f"Unknown server: {u} (choices: {', '.join(_SERVER_NAMES)})")
        return [n for n in only if n in _SERVER_NAMES]
    return [n for n in _SERVER_NAMES if n not in skip]


def _preflight_checks(targets: list[str]) -> None:
    """Warn if required binaries are missing before starting."""
    if "rill" in targets:
        import shutil
        if not shutil.which("rill"):
            warn("rill not found — skipping.")
            targets.remove("rill")

    if "quack" in targets:
        from tycoon import quack
        if not quack.extension_available():
            info("Quack extension unavailable (needs duckdb core_nightly) — serving the warehouse in file mode.")
            targets.remove("quack")
        else:
            quack.ensure_token(config.root)


def _start_server(name: str) -> subprocess.Popen | None:
    from tycoon.constants import PORTS

    if name == "rill":
        return subprocess.Popen(
            ["rill", "start", str(config.rill_dir)],
            cwd=config.root,
        )

    if name == "quack":
        from tycoon import quack
        return quack.start_server(config.root, port=PORTS["quack"])

    return None


def _print_urls(targets: list[str]) -> None:
    from tycoon.constants import PORTS
    lines = {
        "rill":  ("Rill dashboards", f"http://localhost:{PORTS['rill']}"),
        "quack": ("Quack warehouse", f"quack:localhost:{PORTS['quack']}"),
    }
    for name in targets:
        if name in lines:
            label, url = lines[name]
            success(f"{label}: [bold]{url}[/bold]")
