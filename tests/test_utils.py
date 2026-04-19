"""Tests for utility modules — process, duckdb_utils, console."""

from __future__ import annotations

from pathlib import Path

import duckdb
from rich.table import Table

from tycoon.utils.process import is_port_in_use, command_exists
from tycoon.utils.duckdb_utils import (
    db_file_size_mb,
    get_tables,
    get_row_count,
    remove_wal,
)
from tycoon.utils.console import status_table, success, warn, error, info


# ---------------------------------------------------------------------------
# Port checking
# ---------------------------------------------------------------------------


class TestPortChecking:

    def test_is_port_in_use_returns_bool(self):
        result = is_port_in_use(59999)
        assert isinstance(result, bool)

    def test_unused_high_port_returns_false(self):
        # Port 59999 is extremely unlikely to be in use
        assert is_port_in_use(59999) is False

    def test_command_exists_python(self):
        assert command_exists("python") is True

    def test_command_exists_nonexistent(self):
        assert command_exists("nonexistent_command_xyz_12345") is False


# ---------------------------------------------------------------------------
# DuckDB utils
# ---------------------------------------------------------------------------


class TestDuckDBUtils:

    def test_db_file_size_mb_missing_file(self, tmp_path: Path):
        assert db_file_size_mb(tmp_path / "missing.duckdb") is None

    def test_get_tables_missing_file(self, tmp_path: Path):
        assert get_tables(tmp_path / "missing.duckdb") == []

    def test_get_row_count_missing_file(self, tmp_path: Path):
        assert get_row_count(tmp_path / "missing.duckdb", "main", "test") is None

    def test_get_row_count_with_data(self, tmp_path: Path):
        db_path = tmp_path / "test.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute("CREATE SCHEMA IF NOT EXISTS test_schema")
        con.execute("CREATE TABLE test_schema.sample (id INTEGER, name VARCHAR)")
        con.execute("INSERT INTO test_schema.sample VALUES (1, 'a'), (2, 'b'), (3, 'c')")
        con.close()

        count = get_row_count(db_path, "test_schema", "sample")
        assert count == 3

    def test_get_tables_with_data(self, tmp_path: Path):
        db_path = tmp_path / "test.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute("CREATE SCHEMA IF NOT EXISTS s1")
        con.execute("CREATE TABLE s1.t1 (id INTEGER)")
        con.execute("CREATE TABLE s1.t2 (id INTEGER)")
        con.close()

        tables = get_tables(db_path)
        schemas_and_names = [(s, t) for s, t in tables]
        assert ("s1", "t1") in schemas_and_names
        assert ("s1", "t2") in schemas_and_names

    def test_db_file_size_mb_with_file(self, tmp_path: Path):
        db_path = tmp_path / "test.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute("CREATE TABLE t (id INTEGER)")
        con.close()

        size = db_file_size_mb(db_path)
        assert size is not None
        assert size >= 0

    def test_remove_wal_no_wal(self, tmp_path: Path):
        db_path = tmp_path / "test.duckdb"
        db_path.touch()
        assert remove_wal(db_path) is False

    def test_remove_wal_with_wal(self, tmp_path: Path):
        db_path = tmp_path / "test.duckdb"
        db_path.touch()
        wal_path = db_path.with_suffix(".duckdb.wal")
        wal_path.touch()
        assert wal_path.exists()
        assert remove_wal(db_path) is True
        assert not wal_path.exists()


# ---------------------------------------------------------------------------
# Console helpers
# ---------------------------------------------------------------------------


class TestConsoleHelpers:

    def test_status_table_returns_table(self):
        rows = [("Component", "OK", "detail")]
        result = status_table(rows)
        assert isinstance(result, Table)

    def test_status_table_with_title(self):
        rows = [("A", "OK", "ok")]
        result = status_table(rows, title="Custom Title")
        assert isinstance(result, Table)
        assert result.title == "Custom Title"

    def test_success_does_not_raise(self):
        success("test message")

    def test_warn_does_not_raise(self):
        warn("test message")

    def test_error_does_not_raise(self):
        error("test message")

    def test_info_does_not_raise(self):
        info("test message")
