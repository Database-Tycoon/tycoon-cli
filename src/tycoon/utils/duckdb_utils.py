"""DuckDB helper utilities."""

from __future__ import annotations

from pathlib import Path

import duckdb


def get_row_count(db_path: Path, schema: str, table: str) -> int | None:
    """Return row count for a table, or None if it doesn't exist."""
    if not db_path.exists():
        return None
    try:
        con = duckdb.connect(str(db_path), read_only=True)
        result = con.execute(f"SELECT count(*) FROM {schema}.{table}").fetchone()
        con.close()
        return result[0] if result else None
    except duckdb.Error:
        return None


def get_tables(db_path: Path) -> list[tuple[str, str]]:
    """Return list of (schema, table_name) pairs."""
    if not db_path.exists():
        return []
    try:
        con = duckdb.connect(str(db_path), read_only=True)
        rows = con.execute(
            "SELECT table_schema, table_name FROM information_schema.tables "
            "WHERE table_schema NOT IN ('information_schema', 'pg_catalog') "
            "ORDER BY table_schema, table_name"
        ).fetchall()
        con.close()
        return rows
    except duckdb.Error:
        return []


def db_file_size_mb(db_path: Path) -> float | None:
    """Return file size in MB, or None if missing."""
    if not db_path.exists():
        return None
    return db_path.stat().st_size / (1024 * 1024)


def remove_wal(db_path: Path) -> bool:
    """Remove stale WAL file if it exists. Returns True if removed."""
    wal = db_path.with_suffix(".duckdb.wal")
    if wal.exists():
        wal.unlink()
        return True
    return False
