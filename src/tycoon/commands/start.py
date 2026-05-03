"""tycoon start — launch the three long-running servers."""

from __future__ import annotations

import json
import signal
import threading
from pathlib import Path

import typer

from tycoon.config import config
from tycoon.utils.console import console, error, header, info, success, warn

# The servers that run continuously and are not Dagster assets.
_SERVER_NAMES = ["tycoon", "rill", "dagster", "nao"]

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
        [], "--skip", help="Server(s) to skip. Repeatable: --skip nao --skip dagster"
    ),
    only: list[str] = typer.Option(
        [], "--only", help="Only start these server(s). Repeatable: --only rill"
    ),
) -> None:
    """Start the Tycoon web UI, Rill dashboard, Dagster orchestrator, and Nao AI agent.

    All servers run as background processes in this session.
    Press Ctrl-C or run `tycoon stop` to shut everything down.
    """
    from tycoon.services.manager import ServiceManager

    targets = _resolve_targets(skip, only)
    if not targets:
        error("No servers to start.")
        raise typer.Exit(1)

    _preflight_checks(targets)

    manager = ServiceManager()
    header("Tycoon")

    for name in targets:
        manager.start(name)

    # Persist PIDs so `tycoon stop` can kill them from another terminal
    pids = {name: proc.pid for name, proc in manager._processes.items()}
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
    manager.stop_all()
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
    """Warn if required config or binaries are missing before starting."""
    if "tycoon" in targets:
        try:
            import tycoon.server.app  # noqa: F401
        except ImportError:
            warn("tycoon.server.app could not be imported — skipping Tycoon web UI.")
            targets.remove("tycoon")

    if "nao" in targets:
        try:
            import nao_core  # noqa: F401
        except ImportError:
            warn("nao-core is not installed — skipping Nao.")
            targets.remove("nao")
            return
        if not (config.nao_dir / "nao_config.yaml").exists():
            warn("Nao not initialised. Run [bold]tycoon register llm <provider> && tycoon ask sync[/bold] first.")
            targets.remove("nao")

    if "dagster" in targets:
        import shutil
        if not shutil.which("dagster"):
            warn("dagster not found — skipping. Install with: [bold]pip install 'database-tycoon[dagster]'[/bold]")
            targets.remove("dagster")


def _print_urls(targets: list[str]) -> None:
    from tycoon.constants import PORTS
    lines = {
        "tycoon":  ("Tycoon UI",        f"http://localhost:{PORTS['tycoon']}"),
        "rill":    ("Rill dashboards",  f"http://localhost:{PORTS['rill']}"),
        "dagster": ("Dagster UI",       f"http://localhost:{PORTS['dagster']}"),
        "nao":     ("Nao AI queries",   f"http://localhost:{PORTS['nao']}"),
    }
    for name in targets:
        if name in lines:
            label, url = lines[name]
            success(f"{label}: [bold]{url}[/bold]")
