"""Scratch databases for tests that talk to a real MotherDuck account.

Every statement that creates or drops a database goes through ``_checked_name``,
so a test (or a bug) that passes a real catalog name is refused before any SQL
is sent.
"""

from __future__ import annotations

import os
import re
import secrets
import sys
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import duckdb
import pytest

SCRATCH_PREFIX = "tycoon_e2e_scratch_"
TOKEN_ENV = "MOTHERDUCK_TOKEN"
_SUFFIX_RE = re.compile(r"[a-z0-9_]+")
STALE_AFTER = timedelta(hours=24)


class ScratchDatabaseError(ValueError):
    """Raised when asked to touch a database outside the scratch namespace."""


def _checked_name(name: str) -> str:
    suffix = name[len(SCRATCH_PREFIX) :]
    if not name.startswith(SCRATCH_PREFIX) or not _SUFFIX_RE.fullmatch(suffix):
        raise ScratchDatabaseError(f"refusing to touch {name!r}: scratch databases must start with {SCRATCH_PREFIX!r}")
    return name


def new_scratch_name() -> str:
    return f"{SCRATCH_PREFIX}{secrets.token_hex(4)}"


def create_scratch_database(con: duckdb.DuckDBPyConnection, name: str) -> None:
    con.execute(f'CREATE DATABASE "{_checked_name(name)}"')


def drop_scratch_database(con: duckdb.DuckDBPyConnection, name: str) -> None:
    con.execute(f'DROP DATABASE IF EXISTS "{_checked_name(name)}"')


def database_exists(con: duckdb.DuckDBPyConnection, name: str) -> bool:
    rows = con.execute("SELECT 1 FROM duckdb_databases() WHERE database_name = ?", [name]).fetchall()
    return bool(rows)


def sweep_stale_scratch_databases(
    con: duckdb.DuckDBPyConnection, older_than: timedelta = STALE_AFTER, now: datetime | None = None
) -> list[str]:
    """Drop scratch databases created more than ``older_than`` ago; return their names.

    A cancelled or timed-out run skips the fixture's ``finally`` and orphans its database.
    The creation time comes from ``md_information_schema.databases.created_ts``. Only
    names that pass ``_checked_name`` are dropped; anything else is ignored.
    """
    cutoff = (now or datetime.now(UTC)) - older_than
    rows = con.execute("SELECT name, created_ts FROM md_information_schema.databases").fetchall()
    dropped: list[str] = []
    for name, created in rows:
        try:
            _checked_name(name)
        except ScratchDatabaseError:
            continue
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        if created < cutoff:
            drop_scratch_database(con, name)
            dropped.append(name)
    return dropped


@pytest.fixture
def motherduck_scratch_db() -> Iterator[str]:
    """Yield ``md:tycoon_e2e_scratch_<hex>``, a fresh database dropped on teardown.

    Skips when ``MOTHERDUCK_TOKEN`` is unset.
    """
    if not os.environ.get(TOKEN_ENV):
        pytest.skip(f"{TOKEN_ENV} is not set")
    name = new_scratch_name()
    con = duckdb.connect("md:")
    try:
        create_scratch_database(con, name)
        yield f"md:{name}"
    finally:
        try:
            drop_scratch_database(con, name)
        finally:
            con.close()


if __name__ == "__main__":
    if not os.environ.get(TOKEN_ENV):
        sys.exit(f"{TOKEN_ENV} is not set")
    _con = duckdb.connect("md:")
    try:
        print("dropped stale scratch databases:", sweep_stale_scratch_databases(_con))
    finally:
        _con.close()
