from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tycoon.core.events import DbtRunCompleted, RunCompleted, RunFailed
from tycoon.core.metadata import MetadataBackend


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    source_id: str
    runtime_id: str
    status: str
    started_at: datetime
    duration_seconds: float
    rows_total: int
    command: str | None = None


@dataclass(frozen=True)
class RunDetail:
    summary: RunSummary
    rows_by_table: dict[str, int]
    tables_created: list[str]
    error: str | None


class HistoryRepository:
    def __init__(self, backend: MetadataBackend) -> None:
        self._backend = backend

    def list_runs(self, limit: int | None = 20) -> list[RunSummary]:
        events = self._backend.query_events()
        summaries: list[RunSummary] = []
        for e in events:
            if isinstance(e, RunCompleted):
                summaries.append(RunSummary(
                    run_id=e.load_id or e.event_id,
                    source_id=e.source_id,
                    runtime_id=e.runtime_id,
                    status="success",
                    started_at=e.timestamp,
                    duration_seconds=e.duration_seconds,
                    rows_total=sum((e.rows_loaded or {}).values()),
                ))
            elif isinstance(e, RunFailed):
                summaries.append(RunSummary(
                    run_id=e.event_id,
                    source_id=e.source_id,
                    runtime_id=e.runtime_id,
                    status="failed",
                    started_at=e.timestamp,
                    duration_seconds=0.0,
                    rows_total=0,
                ))
            elif isinstance(e, DbtRunCompleted):
                summaries.append(RunSummary(
                    run_id=e.event_id,
                    source_id=e.source_id,
                    runtime_id=e.runtime_id,
                    status="success" if e.models_errored == 0 else "failed",
                    started_at=e.timestamp,
                    duration_seconds=e.duration_seconds,
                    rows_total=e.models_run,
                    command=e.command,
                ))
        summaries.sort(key=lambda s: s.started_at, reverse=True)
        if limit is not None:
            return summaries[:limit]
        return summaries

    def get_run(self, run_id_prefix: str) -> RunDetail | None:
        events = self._backend.query_events()
        matches: list[tuple[RunSummary, object]] = []

        for e in events:
            if isinstance(e, RunCompleted):
                eid = e.load_id or e.event_id
                if eid.startswith(run_id_prefix):
                    matches.append((RunSummary(
                        run_id=eid,
                        source_id=e.source_id,
                        runtime_id=e.runtime_id,
                        status="success",
                        started_at=e.timestamp,
                        duration_seconds=e.duration_seconds,
                        rows_total=sum((e.rows_loaded or {}).values()),
                    ), e))
            elif isinstance(e, RunFailed):
                if e.event_id.startswith(run_id_prefix):
                    matches.append((RunSummary(
                        run_id=e.event_id,
                        source_id=e.source_id,
                        runtime_id=e.runtime_id,
                        status="failed",
                        started_at=e.timestamp,
                        duration_seconds=0.0,
                        rows_total=0,
                    ), e))
            elif isinstance(e, DbtRunCompleted):
                if e.event_id.startswith(run_id_prefix):
                    matches.append((RunSummary(
                        run_id=e.event_id,
                        source_id=e.source_id,
                        runtime_id=e.runtime_id,
                        status="success" if e.models_errored == 0 else "failed",
                        started_at=e.timestamp,
                        duration_seconds=e.duration_seconds,
                        rows_total=e.models_run,
                        command=e.command,
                    ), e))

        if len(matches) == 0:
            return None
        if len(matches) > 1:
            ids = ", ".join(s.run_id for s, _ in matches)
            raise ValueError(f"Ambiguous prefix '{run_id_prefix}' matches {len(matches)} runs: {ids}")

        summary, event = matches[0]

        if isinstance(event, RunCompleted):
            return RunDetail(
                summary=summary,
                rows_by_table=event.rows_loaded or {},
                tables_created=event.tables_created or [],
                error=None,
            )
        if isinstance(event, RunFailed):
            return RunDetail(
                summary=summary,
                rows_by_table={},
                tables_created=[],
                error=event.error,
            )
        if isinstance(event, DbtRunCompleted):
            return RunDetail(
                summary=summary,
                rows_by_table={},
                tables_created=[],
                error=None,
            )
        return None
