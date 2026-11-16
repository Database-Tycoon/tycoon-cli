"""The scratch-database helper refuses anything outside its namespace (no token needed)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from tests.motherduck_scratch import (
    SCRATCH_PREFIX,
    ScratchDatabaseError,
    create_scratch_database,
    drop_scratch_database,
    new_scratch_name,
    sweep_stale_scratch_databases,
)

PROTECTED = ["dogfood_dlt_prod", "dogfood_sqlmesh_prod", "my_db", "sample_data", "", "tycoon_e2e_scratch_", "md:my_db"]
UNICODE = [
    "tycoon_e2e_scratch_\uff41\uff42",
    "tycoon_e2e_scratch_\u00b2",
    "tycoon_e2e_scratch_\u0663",
    "tycoon_e2e_scratch_AB",
]
INJECTION = ['tycoon_e2e_scratch_x"; DROP DATABASE my_db; --', "tycoon_e2e_scratch_a b", "TYCOON_E2E_SCRATCH_ab"]


@pytest.mark.parametrize("name", PROTECTED + INJECTION + UNICODE)
def test_create_and_drop_refuse_foreign_names(name: str) -> None:
    con = MagicMock()
    with pytest.raises(ScratchDatabaseError):
        create_scratch_database(con, name)
    with pytest.raises(ScratchDatabaseError):
        drop_scratch_database(con, name)
    con.execute.assert_not_called()


def test_scratch_names_are_prefixed_and_unique() -> None:
    names = {new_scratch_name() for _ in range(20)}
    assert len(names) == 20
    assert all(n.startswith(SCRATCH_PREFIX) for n in names)


def test_valid_name_reaches_the_connection() -> None:
    con = MagicMock()
    name = new_scratch_name()
    create_scratch_database(con, name)
    con.execute.assert_called_once_with(f'CREATE DATABASE "{name}"')


def test_sweeper_drops_only_old_scratch_databases() -> None:
    now = datetime(2026, 1, 10, tzinfo=UTC)
    old = now - timedelta(days=2)
    fresh = now - timedelta(hours=1)
    con = MagicMock()
    con.execute.return_value.fetchall.return_value = [
        ("tycoon_e2e_scratch_old1", old),
        ("tycoon_e2e_scratch_new1", fresh),
        ("my_db", old),
        ("dogfood_dlt_prod", old),
        ("tycoon_e2e_scratch_", old),
    ]
    assert sweep_stale_scratch_databases(con, now=now) == ["tycoon_e2e_scratch_old1"]
    statements = [c.args[0] for c in con.execute.call_args_list]
    assert statements == [
        "SELECT name, created_ts FROM md_information_schema.databases",
        'DROP DATABASE IF EXISTS "tycoon_e2e_scratch_old1"',
    ]
