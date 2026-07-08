from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel

from tycoon.core.events import BaseEvent


class EventFilter(BaseModel):
    source_id: str | None = None
    event_type: str | None = None
    since: datetime | None = None


class MetadataBackend(Protocol):
    def append_event(self, event: BaseEvent) -> None: ...
    def query_events(self, filter: EventFilter | None = None) -> list[BaseEvent]: ...
    def upsert_snapshot(self, kind: str, key: str, blob: dict) -> None: ...
    def read_snapshot(self, kind: str, key: str) -> dict | None: ...
    def __enter__(self) -> MetadataBackend: ...
    def __exit__(self, *args: object) -> None: ...
