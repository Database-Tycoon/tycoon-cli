"""Single-writer subprocess manager for pipeline and dbt runs."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field


@dataclass
class RunInfo:
    """Metadata for a tracked subprocess run."""

    run_id: str
    cmd: list[str]
    process: asyncio.subprocess.Process
    log_lines: list[str] = field(default_factory=list)
    finished: bool = False


class SubprocessManager:
    """Enforces single-writer semantics for pipeline / dbt runs.

    Only one subprocess may be active at a time.  Callers must check
    ``is_busy()`` before starting a new run, or ``start_run`` will raise.
    """

    def __init__(self) -> None:
        self._runs: dict[str, RunInfo] = {}
        self._active_run_id: str | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_busy(self) -> bool:
        """Return True if a subprocess is currently running."""
        if self._active_run_id is None:
            return False
        run = self._runs.get(self._active_run_id)
        if run is None:
            self._active_run_id = None
            return False
        if run.process.returncode is not None:
            run.finished = True
            self._active_run_id = None
            return False
        return True

    async def start_run(self, run_id: str, cmd: list[str]) -> RunInfo:
        """Start a new subprocess.

        Raises ``RuntimeError`` if another run is already active.
        """
        if self.is_busy():
            raise RuntimeError(
                f"Another run is already active: {self._active_run_id}"
            )

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        run_info = RunInfo(run_id=run_id, cmd=cmd, process=process)
        self._runs[run_id] = run_info
        self._active_run_id = run_id
        return run_info

    def get_run(self, run_id: str) -> RunInfo | None:
        """Return the ``RunInfo`` for *run_id*, or ``None``."""
        return self._runs.get(run_id)

    @property
    def active_run_id(self) -> str | None:
        # Refresh staleness check
        self.is_busy()
        return self._active_run_id


# Module-level singleton
subprocess_manager = SubprocessManager()
