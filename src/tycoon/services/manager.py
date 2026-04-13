"""Service lifecycle manager for the Tycoon demo environment."""

from __future__ import annotations

import os
import signal
import subprocess
import time

from tycoon.services.definitions import ServiceDef, get_service_definitions
from tycoon.utils.console import error, info, success, warn
from tycoon.utils.process import command_exists, is_port_in_use


class ServiceManager:
    """Start, stop, and health-check the suite of local services."""

    def __init__(self) -> None:
        self._processes: dict[str, subprocess.Popen] = {}
        self._definitions: dict[str, ServiceDef] = {
            sd.name: sd for sd in get_service_definitions()
        }
        self._original_sigint: signal.Handlers | None = None
        self._original_sigterm: signal.Handlers | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self, name: str) -> bool:
        """Start a service by name.  Returns True on success."""
        svc = self._definitions.get(name)
        if svc is None:
            error(f"Unknown service: {name}")
            return False

        # The tycoon service itself is handled by uvicorn, not here.
        if name == "tycoon" or not svc.command:
            return False

        # Check if the underlying binary is available.
        binary = svc.command[0]
        if not command_exists(binary):
            warn(f"Skipping {name}: '{binary}' not found on PATH")
            return False

        # Skip if the port is already occupied.
        if is_port_in_use(svc.port):
            warn(f"Skipping {name}: port {svc.port} already in use")
            return False

        info(f"Starting {name} on :{svc.port}")
        proc_env = {**os.environ, **svc.env} if svc.env else None
        try:
            proc = subprocess.Popen(
                svc.command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=svc.cwd,
                env=proc_env,
            )
            self._processes[name] = proc
        except OSError as exc:
            error(f"Failed to start {name}: {exc}")
            return False

        # Wait for the port to become ready.
        if self._wait_for_port(svc.port, timeout=15):
            success(f"{name} is ready on :{svc.port}")
            return True
        else:
            warn(f"{name} started but port {svc.port} not responding yet")
            return True

    def stop(self, name: str) -> None:
        """Terminate a service and wait for exit."""
        proc = self._processes.pop(name, None)
        if proc is None:
            return
        info(f"Stopping {name}")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)

    def stop_all(self) -> None:
        """Stop every managed service."""
        for name in list(self._processes):
            self.stop(name)

    def health(self, name: str) -> bool:
        """Return True if the service port is responding."""
        svc = self._definitions.get(name)
        if svc is None:
            return False
        return is_port_in_use(svc.port)

    # ------------------------------------------------------------------
    # Signal handling
    # ------------------------------------------------------------------

    def install_signal_handlers(self) -> None:
        """Register SIGINT/SIGTERM handlers that call ``stop_all``."""
        def _handler(signum: int, frame: object) -> None:
            self.stop_all()
            raise SystemExit(0)

        self._original_sigint = signal.getsignal(signal.SIGINT)
        self._original_sigterm = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGINT, _handler)
        signal.signal(signal.SIGTERM, _handler)

    def restore_signal_handlers(self) -> None:
        """Restore original signal handlers."""
        if self._original_sigint is not None:
            signal.signal(signal.SIGINT, self._original_sigint)
        if self._original_sigterm is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def service_names(self) -> list[str]:
        """Return the names of all defined services."""
        return list(self._definitions)

    @staticmethod
    def _wait_for_port(port: int, timeout: float = 15, interval: float = 0.5) -> bool:
        """Poll until *port* is open, or *timeout* seconds elapse."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if is_port_in_use(port):
                return True
            time.sleep(interval)
        return False
