"""`tycoon data sync` — cloud → local DuckDB snapshots.

Implements the spec from issue #12. Snapshots one or more DuckDB-attachable
sources (``md:<catalog>`` for MotherDuck, ``/path/to/other.duckdb`` for a
local file) into a single destination DuckDB file. Designed for offline-dev
loops where running every query against prod is slow / fragile / risky.

v0.1.4 scope (intentionally narrow):

- One direction only: pull from cloud → local. No reverse sync.
- Full replace per table (default), append, and skip-existing modes.
- ``md:`` and local-DuckDB sources only. Postgres / Snowflake / BigQuery
  land later as their respective DuckDB ATTACH stories settle.
- No incremental sync. v1 is a baseline-snapshot tool, not a replica.

The summary returned by :func:`sync_to_local` is written for both human
display and machine consumption — every table copy emits a row with
source URL, schema, table, and row count.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import duckdb

from tycoon.project import SyncSourceSpec


_SYSTEM_SCHEMAS = frozenset(
    {
        "information_schema",
        "pg_catalog",
        "system",
        "main_pg_catalog",  # DuckDB sometimes namespaces these per-attached-db
    }
)


@dataclass
class SyncedTable:
    """One row of the sync summary."""

    source: str
    schema: str
    table: str
    rows: int


@dataclass
class SyncResult:
    """Aggregate result of a sync run."""

    dest: Path
    tables: list[SyncedTable] = field(default_factory=list)

    @property
    def total_rows(self) -> int:
        return sum(t.rows for t in self.tables)


def _alias_for(url: str) -> str:
    """Produce a DuckDB-safe ATTACH alias for a source URL."""
    # md:dogfood_dbt_prod  → dogfood_dbt_prod
    # ./other.duckdb       → other
    # /abs/foo.duckdb      → foo
    if url.startswith("md:"):
        candidate = url[3:]
    else:
        candidate = Path(url).stem
    # Strip everything that isn't a SQL identifier char
    safe = "".join(c if (c.isalnum() or c == "_") else "_" for c in candidate)
    return safe or "src"


def _attach_sql(url: str, alias: str) -> str:
    """Build the ATTACH statement for a source URL.

    Sources are always attached READ_ONLY — `tycoon data sync` is a
    one-way pull and should never mutate the source.
    """
    if url.startswith("md:"):
        # MotherDuck — relies on MOTHERDUCK_TOKEN env var (or active OAuth).
        return f"ATTACH '{url}' AS {alias} (READ_ONLY)"
    # Local DuckDB file.
    return f"ATTACH '{url}' AS {alias} (READ_ONLY)"


def _matches_any(name: str, patterns: Iterable[str]) -> bool:
    """fnmatch ``name`` against any of ``patterns``. Empty list = match nothing."""
    return any(fnmatch.fnmatchcase(name, p) for p in patterns)


def _list_source_tables(
    con: duckdb.DuckDBPyConnection,
    alias: str,
    schemas_glob: list[str],
    tables_glob: list[str],
) -> list[tuple[str, str]]:
    """List ``(schema, table)`` pairs from the attached source matching the globs.

    System schemas (``information_schema``, ``pg_catalog``, etc.) are always
    excluded — they're never useful in a local snapshot.
    """
    rows = con.execute(
        """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_catalog = ?
          AND table_type IN ('BASE TABLE', 'VIEW')
        ORDER BY table_schema, table_name
        """,
        [alias],
    ).fetchall()
    return [
        (schema, table)
        for schema, table in rows
        if schema not in _SYSTEM_SCHEMAS
        and _matches_any(schema, schemas_glob)
        and _matches_any(table, tables_glob)
    ]


def _quote(identifier: str) -> str:
    """Double-quote a SQL identifier and escape any embedded quotes."""
    return '"' + identifier.replace('"', '""') + '"'


def _table_exists(
    con: duckdb.DuckDBPyConnection, schema: str, table: str
) -> bool:
    """True if a base table named ``schema.table`` already exists in the dest db."""
    row = con.execute(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = ? AND table_name = ?
        """,
        [schema, table],
    ).fetchone()
    return row is not None


def _copy_one(
    con: duckdb.DuckDBPyConnection,
    alias: str,
    schema: str,
    table: str,
    mode: str,
) -> int | None:
    """Copy one source table into the destination. Returns row count copied,
    or ``None`` if the table was skipped (skip-existing mode).
    """
    src = f"{_quote(alias)}.{_quote(schema)}.{_quote(table)}"
    dest_schema_q = _quote(schema)
    dest_table_q = _quote(table)
    dest = f"{dest_schema_q}.{dest_table_q}"

    con.execute(f"CREATE SCHEMA IF NOT EXISTS {dest_schema_q}")

    if mode == "replace":
        con.execute(f"CREATE OR REPLACE TABLE {dest} AS SELECT * FROM {src}")
    elif mode == "append":
        if _table_exists(con, schema, table):
            con.execute(f"INSERT INTO {dest} SELECT * FROM {src}")
        else:
            con.execute(f"CREATE TABLE {dest} AS SELECT * FROM {src}")
    elif mode == "skip-existing":
        if _table_exists(con, schema, table):
            return None
        con.execute(f"CREATE TABLE {dest} AS SELECT * FROM {src}")
    else:
        raise ValueError(f"Unknown sync mode: {mode!r}. Expected replace | append | skip-existing.")

    row = con.execute(f"SELECT COUNT(*) FROM {dest}").fetchone()
    return int(row[0]) if row else 0


def sync_to_local(
    sources: list[SyncSourceSpec],
    to_path: Path,
    mode: str = "replace",
) -> SyncResult:
    """Snapshot one or more DuckDB-attachable sources into a local DuckDB file.

    ``to_path`` is created if missing. Each source is ATTACHed READ_ONLY,
    its non-system schemas are filtered by the spec's ``schemas`` /
    ``tables`` globs, and each matching table is copied per ``mode``:

    - ``replace`` (default): destination table is dropped and recreated.
    - ``append``: rows added to an existing destination table; created if
      missing. Watch for duplicate-row drift across re-runs — by design,
      the sync command does not deduplicate.
    - ``skip-existing``: destination table is left alone if it already
      exists; created if missing. Useful for first-run-only seeding.

    Returns a :class:`SyncResult` with one :class:`SyncedTable` per copy.
    Skipped tables (``skip-existing`` mode where the dest already exists)
    are not included in the result; this matches the "summary of what
    changed" framing in the issue.
    """
    to_path.parent.mkdir(parents=True, exist_ok=True)

    result = SyncResult(dest=to_path)
    con = duckdb.connect(str(to_path))
    try:
        for spec in sources:
            alias = _alias_for(spec.from_)
            con.execute(_attach_sql(spec.from_, alias))
            try:
                tables = _list_source_tables(con, alias, spec.schemas, spec.tables)
                for schema, table in tables:
                    rows = _copy_one(con, alias, schema, table, mode)
                    if rows is not None:
                        result.tables.append(
                            SyncedTable(
                                source=spec.from_,
                                schema=schema,
                                table=table,
                                rows=rows,
                            )
                        )
            finally:
                con.execute(f"DETACH DATABASE {_quote(alias)}")
    finally:
        con.close()
    return result
