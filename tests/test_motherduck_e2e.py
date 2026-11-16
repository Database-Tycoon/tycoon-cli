"""Real MotherDuck round trip. Needs MOTHERDUCK_TOKEN; run with ``pytest -m e2e``."""

from __future__ import annotations

import duckdb
import pytest

from tests.motherduck_scratch import SCRATCH_PREFIX, database_exists, drop_scratch_database

pytestmark = pytest.mark.e2e


def test_scratch_database_round_trip(motherduck_scratch_db: str) -> None:
    url = motherduck_scratch_db
    name = url.removeprefix("md:")
    assert name.startswith(SCRATCH_PREFIX)

    con = duckdb.connect(url)
    try:
        con.execute("CREATE TABLE t (id INTEGER, label VARCHAR)")
        con.execute("INSERT INTO t VALUES (1, 'hello')")
        assert con.execute("SELECT id, label FROM t").fetchall() == [(1, "hello")]
    finally:
        con.close()

    admin = duckdb.connect("md:")
    try:
        assert database_exists(admin, name)
        drop_scratch_database(admin, name)
        assert not database_exists(admin, name)
    finally:
        admin.close()
