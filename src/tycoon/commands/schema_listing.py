"""Schema listings for `tycoon data schema`: one row per table, local or MotherDuck.

Split out of `commands/db.py`, which keeps the commands themselves. Nothing
here reads project config; callers pass the database path or target.
"""

from __future__ import annotations

from collections.abc import Callable
from fnmatch import fnmatchcase
from pathlib import Path

import duckdb

from tycoon.config import display_target, redact_secrets
from tycoon.utils.duckdb_utils import db_file_size_mb, get_row_count, get_tables, quote_identifier

SchemaRow = tuple[str, str, str]

# A listed table: (schema, table, ...) where any further columns are extra
# detail the caller's describe callback reads, e.g. MotherDuck's table type
# and catalog estimate.
ListedTable = tuple

DLT_TABLE_PREFIX = "_dlt_"


def _select_tables(
    tables: list[ListedTable], schema_pattern: str | None, include_dlt: bool
) -> tuple[list[ListedTable], int]:
    """Tables in the schemas matching ``schema_pattern``, and how many dlt tables were left out."""
    if schema_pattern is not None:
        pattern = schema_pattern.lower()
        tables = [row for row in tables if fnmatchcase(row[0].lower(), pattern)]
    if include_dlt:
        return tables, 0
    kept = [row for row in tables if not row[1].startswith(DLT_TABLE_PREFIX)]
    return kept, len(tables) - len(kept)


def _table_rows(tables: list[ListedTable], hidden_dlt: int, describe: Callable[[ListedTable], str]) -> list[SchemaRow]:
    """The Tables summary row, then one row per table with the detail ``describe`` returns."""
    detail = f"{len(tables)}"
    if hidden_dlt:
        detail += f" ({hidden_dlt} {DLT_TABLE_PREFIX}* hidden, --include-dlt shows them)"
    rows: list[SchemaRow] = [("  Tables", "", detail)]
    for table in tables:
        rows.append((f"  {table[0]}.{table[1]}", "", describe(table)))
    return rows


def _count_detail(count: int | None) -> str:
    return f"{count:,} rows" if count is not None else "empty"


def _local_schema_rows(
    db_path: Path, label: str, schema_pattern: str | None, include_dlt: bool
) -> tuple[list[SchemaRow], int]:
    size = db_file_size_mb(db_path)
    if size is None:
        return [(label, "WARN", "not found")], 0
    tables, hidden_dlt = _select_tables(get_tables(db_path), schema_pattern, include_dlt)
    rows = [(label, "OK", f"{size:.1f} MB")]
    rows.extend(_table_rows(tables, hidden_dlt, lambda t: _count_detail(get_row_count(db_path, t[0], t[1]))))
    return rows, len(tables)


def _estimate_detail(table_type: str, estimate: int | None) -> str:
    if table_type == "VIEW":
        return "view (use --exact to count)"
    if estimate is None:
        return "no estimate (use --exact to count)"
    return f"~{estimate:,} {'row' if estimate == 1 else 'rows'} (estimate)"


def _motherduck_schema_rows(
    target: str,
    label: str,
    schema_pattern: str | None = None,
    include_dlt: bool = False,
    exact: bool = False,
) -> tuple[list[SchemaRow], int]:
    """Schema rows for a MotherDuck database, read over one connection.

    Row counts come from the catalog's estimate unless ``exact`` is set.
    Filtering happens first, so --exact runs count(*) only on the tables
    that are shown.
    """
    try:
        con = duckdb.connect(target)
        try:
            # An md: connection attaches every database on the account, so
            # scope the listing to the one the target names. duckdb_tables()
            # has no row for a view, and an attached catalog may report no
            # estimate for a table, so the estimate can be NULL for either.
            listed = con.execute(
                "SELECT t.table_schema, t.table_name, t.table_type, d.estimated_size "
                "FROM information_schema.tables t "
                "LEFT JOIN duckdb_tables() d ON d.database_name = t.table_catalog "
                "AND d.schema_name = t.table_schema AND d.table_name = t.table_name "
                "WHERE t.table_catalog = current_database() "
                "AND t.table_schema NOT IN ('information_schema', 'pg_catalog') "
                "ORDER BY t.table_schema, t.table_name"
            ).fetchall()
            tables, hidden_dlt = _select_tables(listed, schema_pattern, include_dlt)

            def describe(table: ListedTable) -> str:
                s, name, table_type, estimate = table
                if not exact:
                    return _estimate_detail(table_type, estimate)
                result = con.execute(f"SELECT count(*) FROM {quote_identifier(s)}.{quote_identifier(name)}").fetchone()
                return _count_detail(result[0] if result else None)

            rows: list[SchemaRow] = [(f"{label} database", "OK", f"MotherDuck {display_target(target)}")]
            rows.extend(_table_rows(tables, hidden_dlt, describe))
        finally:
            con.close()
    except duckdb.Error as exc:
        return [(f"{label} database", "WARN", f"MotherDuck {display_target(target)}: {redact_secrets(str(exc))}")], 0
    return rows, len(tables)
