"""``refused_statement`` classifies SQL for the MotherDuck write guard (#309)."""

from __future__ import annotations

import pytest

from tycoon.utils.sql_guard import refused_statement

ALLOWED = [
    "SELECT 1",
    "select * from t where x = 1;",
    "  SELECT 1  ;  ;",
    "-- leading comment\nSELECT 1",
    "/* block */ SELECT 1 /* ; DROP TABLE t */",
    "SELECT ';' AS semicolon",
    "WITH a AS (SELECT 1 AS i) SELECT * FROM a",
    "WITH a AS (SELECT 1 AS i) FROM a",
    "FROM tbl",
    "FROM tbl WHERE x = 1",
    "FROM range(3)",
    "FROM t SELECT a",
    "(SELECT 1)",
    "SELECT 1 UNION SELECT 2",
    "SELECT 1 EXCEPT SELECT 2",
    "(SELECT 1) UNION ALL (SELECT 2)",
    "DESCRIBE tbl",
    "DESC tbl",
    "DESCRIBE SELECT 1",
    "SHOW TABLES",
    "SHOW ALL TABLES",
    "SHOW DATABASES",
    "SUMMARIZE tbl",
    "SUMMARIZE SELECT 1",
    "PIVOT t ON a USING sum(b)",
    "UNPIVOT t ON a, b",
    "TABLE t",
    "VALUES (1)",
    "EXPLAIN (FORMAT JSON) SELECT 1",
    "EXPLAIN (ANALYZE) SELECT 1",
    "EXPLAIN SELECT 1",
    "explain analyze select 1",
    "-- c\nEXPLAIN SELECT * FROM t",
    "SELECT 1; SELECT 2",
    "SELECT read_csv('data.csv')",
    "",
    "   ;  ",
]

REFUSED = [
    ("DROP TABLE t", "DROP"),
    ("/* x */ DROP TABLE t", "DROP"),
    ("-- SELECT\nDROP TABLE t", "DROP"),
    ("INSERT INTO t VALUES (1)", "INSERT"),
    ("UPDATE t SET a = 1", "UPDATE"),
    ("DELETE FROM t", "DELETE"),
    ("TRUNCATE t", "TRUNCATE"),
    ("CREATE TABLE t AS SELECT 1", "CREATE"),
    ("CREATE OR REPLACE TABLE t AS SELECT 1", "CREATE"),
    ("ALTER TABLE t ADD COLUMN a INT", "ALTER"),
    ("WITH a AS (SELECT 1) INSERT INTO t SELECT * FROM a", "INSERT"),
    ("WITH a AS (SELECT 1) DELETE FROM t", "DELETE"),
    ("MERGE INTO t USING s ON t.a = s.a WHEN MATCHED THEN DELETE", "MERGE"),
    ("COPY t TO 'x.csv'", "COPY"),
    ("COPY (SELECT 1) TO 'x.csv'", "COPY"),
    ("ATTACH 'x.db'", "ATTACH"),
    ("DETACH x", "DETACH"),
    ("INSTALL httpfs", "INSTALL"),
    ("LOAD httpfs", "LOAD"),
    ("CALL pragma_version()", "CALL"),
    ("PRAGMA table_info('t')", "PRAGMA"),
    ("SET threads = 1", "SET"),
    ("USE other", "USE"),
    ("VACUUM", "VACUUM"),
    ("CHECKPOINT", "CHECKPOINT"),
    ("EXPORT DATABASE 'x'", "a statement tycoon could not parse"),
    ("SELECT * INTO new_t FROM t", "SELECT ... INTO"),
    ("SELECT 1; DROP TABLE t", "DROP"),
    ("SELECT ';' ; DROP TABLE t", "DROP"),
    ("SELECT 1;\n-- done\nINSERT INTO t VALUES (1)", "INSERT"),
    ("EXPLAIN ANALYZE DROP TABLE t", "DROP"),
    ("EXPLAIN ANALYZE INSERT INTO t VALUES (1)", "INSERT"),
    ("EXPLAIN", "EXPLAIN"),
    ("CHECKPOINT mydb", "CHECKPOINT"),
    ("TABLE s.t", "a statement tycoon could not parse"),
    ("EXPLAIN FORMAT JSON SELECT 1", "a statement tycoon could not parse"),
    ("EXPLAIN (FORMAT JSON, ANALYZE) DROP TABLE t", "DROP"),
    ("EXPLAIN (ANALYZE) INSERT INTO t VALUES (1)", "INSERT"),
    ("SELECT ((1)", "a statement tycoon could not parse"),
    ("SELEC 1 FROM", "a statement tycoon could not parse"),
]


@pytest.mark.parametrize("sql", ALLOWED)
def test_read_only_statements_pass(sql: str) -> None:
    assert refused_statement(sql) is None


@pytest.mark.parametrize(("sql", "expected"), REFUSED)
def test_everything_else_is_refused(sql: str, expected: str) -> None:
    assert refused_statement(sql) == expected


def test_explain_does_not_log_sqlglot_warnings(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING", logger="sqlglot"):
        assert refused_statement("EXPLAIN SELECT 1") is None
    assert caplog.records == []


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT " + "(" * 500 + "1" + ")" * 500,
        "SELECT * FROM " + "(SELECT * FROM " * 250 + "t" + ")" * 250,
    ],
    ids=["nested-parens", "nested-subqueries"],
)
def test_deeply_nested_sql_is_refused_not_raised(sql: str) -> None:
    assert refused_statement(sql) == "a statement tycoon could not parse"


def test_function_calls_inside_select_are_not_inspected() -> None:
    assert refused_statement("SELECT nextval('s')") is None
