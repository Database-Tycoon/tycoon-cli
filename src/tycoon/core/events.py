from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, Field


class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    source_id: str
    runtime_id: str
    timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class RunStarted(BaseEvent):
    event_type: Literal["run_started"] = "run_started"
    options: dict = Field(default_factory=dict)


class RunCompleted(BaseEvent):
    event_type: Literal["run_completed"] = "run_completed"
    load_id: str = ""
    duration_seconds: float = 0.0
    rows_loaded: dict[str, int] = Field(default_factory=dict)
    tables_created: list[str] = Field(default_factory=list)
    tables_updated: list[str] = Field(default_factory=list)


class RunFailed(BaseEvent):
    event_type: Literal["run_failed"] = "run_failed"
    error: str
    partial_load_id: str = ""


class SchemaSnapshot(BaseEvent):
    event_type: Literal["schema_snapshot"] = "schema_snapshot"
    tables: dict[str, list[str]] = Field(default_factory=dict)


class DbtRunCompleted(BaseEvent):
    event_type: Literal["dbt_run_completed"] = "dbt_run_completed"
    command: str
    target: str
    models_run: int = 0
    models_passed: int = 0
    models_errored: int = 0
    duration_seconds: float = 0.0


Event = Annotated[
    RunStarted | RunCompleted | RunFailed | SchemaSnapshot | DbtRunCompleted,
    Field(discriminator="event_type"),
]
