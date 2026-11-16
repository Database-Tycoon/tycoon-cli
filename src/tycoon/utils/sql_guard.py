"""Classify SQL as read-only so ``data query`` can refuse writes on MotherDuck."""

from __future__ import annotations

import logging

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

_UNPARSEABLE = "a statement tycoon could not parse"
_KEYWORDS = {"truncatetable": "TRUNCATE"}


def refused_statement(sql: str) -> str | None:
    """Name the first statement in ``sql`` that is not provably read-only.

    ``None`` means every statement is a SELECT, WITH, ``FROM tbl``-first
    query, ``TABLE tbl``, VALUES, set operation, DESCRIBE, SHOW, SUMMARIZE,
    PIVOT, UNPIVOT or EXPLAIN of one of those. Anything sqlglot cannot parse or
    classify is refused, and so is a query too deeply nested to parse.

    Only the statement type is checked. Function calls inside a SELECT, such
    as ``nextval('s')`` or ``read_csv('path')``, are not inspected.
    """
    sqlglot_logger = logging.getLogger("sqlglot")
    previous_level = sqlglot_logger.level
    # sqlglot warns on stderr when it falls back to a generic Command (EXPLAIN,
    # SHOW DATABASES); that is expected here and not for the user to read.
    sqlglot_logger.setLevel(logging.ERROR)
    try:
        for statement in sqlglot.parse(sql, read="duckdb"):
            if statement is None:
                continue
            refused = _refusal(statement)
            if refused is not None:
                return refused
    except (SqlglotError, RecursionError):
        return _UNPARSEABLE
    finally:
        sqlglot_logger.setLevel(previous_level)
    return None


def _refusal(statement: exp.Expression) -> str | None:
    """None when ``statement`` is read-only, else a keyword naming what it is."""
    if isinstance(statement, exp.Subquery):
        return _refusal(statement.this)
    if isinstance(statement, exp.Select):
        return "SELECT ... INTO" if statement.args.get("into") is not None else None
    if isinstance(statement, (exp.SetOperation, exp.Describe, exp.Show, exp.Pivot, exp.Summarize, exp.Values)):
        return None
    if isinstance(statement, exp.Alias) and isinstance(statement.this, exp.Column):
        # sqlglot reads `TABLE t` and `CHECKPOINT db` as a column with an alias.
        keyword = statement.this.name.upper()
        return None if keyword == "TABLE" else keyword
    if isinstance(statement, exp.Column):
        return statement.name.upper()
    if isinstance(statement, exp.Command):
        keyword = str(statement.this).upper()
        if keyword == "SHOW":
            return None
        if keyword == "EXPLAIN":
            return _explained_refusal(statement.text("expression"))
        return keyword
    return _KEYWORDS.get(statement.key, statement.key.upper())


def _explained_refusal(rest: str) -> str | None:
    """Classify what an EXPLAIN runs; ``EXPLAIN ANALYZE`` executes its statement."""
    rest = rest.strip()
    if rest.startswith("("):
        depth = 0
        for index, char in enumerate(rest):
            depth += (char == "(") - (char == ")")
            if depth == 0:
                rest = rest[index + 1 :]
                break
        else:
            return "EXPLAIN"
    else:
        words = rest.split(None, 1)
        if words and words[0].upper() == "ANALYZE":
            rest = words[1] if len(words) > 1 else ""
    if not rest.strip():
        return "EXPLAIN"
    return refused_statement(rest)
