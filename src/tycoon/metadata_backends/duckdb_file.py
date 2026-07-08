from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
from pydantic import TypeAdapter

from tycoon.core.events import BaseEvent, Event
from tycoon.core.metadata import EventFilter

_EVENT_ADAPTER: TypeAdapter = TypeAdapter(Event)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS events (
    event_id    TEXT PRIMARY KEY,
    event_type  TEXT NOT NULL,
    source_id   TEXT NOT NULL,
    runtime_id  TEXT NOT NULL,
    timestamp   TIMESTAMPTZ NOT NULL,
    payload     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
    kind        TEXT NOT NULL,
    key         TEXT NOT NULL,
    blob        TEXT NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (kind, key)
);
"""


class DuckDBFileBackend:
    def __init__(self, path: Path, read_only: bool = False) -> None:
        self._path = path
        self._read_only = read_only
        self._con: duckdb.DuckDBPyConnection | None = None

    def __enter__(self) -> DuckDBFileBackend:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._con = duckdb.connect(str(self._path), read_only=self._read_only)
        if not self._read_only:
            self._con.execute(_SCHEMA_SQL)
        return self

    def __exit__(self, *args: object) -> None:
        if self._con is not None:
            self._con.close()
            self._con = None

    def append_event(self, event: BaseEvent) -> None:
        assert self._con is not None
        self._con.execute(
            """
            INSERT INTO events (event_id, event_type, source_id, runtime_id, timestamp, payload)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                event.event_id,
                event.event_type,
                event.source_id,
                event.runtime_id,
                event.timestamp,
                event.model_dump_json(),
            ],
        )

    def query_events(self, filter: EventFilter | None = None) -> list[BaseEvent]:
        assert self._con is not None
        where_clauses: list[str] = []
        params: list[object] = []

        if filter is not None:
            if filter.source_id is not None:
                where_clauses.append("source_id = ?")
                params.append(filter.source_id)
            if filter.event_type is not None:
                where_clauses.append("event_type = ?")
                params.append(filter.event_type)
            if filter.since is not None:
                where_clauses.append("timestamp >= ?")
                params.append(filter.since)

        where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        rows = self._con.execute(
            f"SELECT payload FROM events {where} ORDER BY timestamp ASC",
            params,
        ).fetchall()

        return [_EVENT_ADAPTER.validate_json(row[0]) for row in rows]

    def upsert_snapshot(self, kind: str, key: str, blob: dict) -> None:
        assert self._con is not None
        now = datetime.now(tz=timezone.utc)
        self._con.execute(
            """
            INSERT INTO snapshots (kind, key, blob, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (kind, key) DO UPDATE SET blob = excluded.blob, updated_at = excluded.updated_at
            """,
            [kind, key, json.dumps(blob), now],
        )

    def read_snapshot(self, kind: str, key: str) -> dict | None:
        assert self._con is not None
        row = self._con.execute(
            "SELECT blob FROM snapshots WHERE kind = ? AND key = ?",
            [kind, key],
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])
