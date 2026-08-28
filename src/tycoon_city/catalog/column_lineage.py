"""Column-level lineage: which source columns feed which output columns.

The skybridge feature's data layer. For every object we hold SQL for — a
view's definition, or a dbt model's compiled/cleaned code — sqlglot traces
each *measured* output column (from ``duckdb_columns()``, never the SQL's own
claims) back to the catalog columns it reads. The result is a set of
``ColumnEdge`` records the exporter attaches to the table-level edges.

Everything degrades per object, never fails: SQL that sqlglot cannot parse,
or a column it cannot trace, costs exactly that object/column its bridges.
The caller counts what was skipped — absence stays named.
"""

import logging
from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.lineage import lineage

logger = logging.getLogger(__name__)

DIALECT = "duckdb"


@dataclass(frozen=True)
class ColumnEdge:
    """One column feeding another: `src.src_col -> dst.dst_col`, object keys
    in the catalog's canonical spelling."""

    src: str
    src_col: str
    dst: str
    dst_col: str


@dataclass(frozen=True)
class ColumnLineage:
    edges: tuple[ColumnEdge, ...]
    unparsed: int  # objects whose SQL sqlglot could not parse/trace at all


def _schema_dict(
    columns_by_key: dict[str, tuple[tuple[str, str], ...]],
) -> dict[str, dict[str, dict[str, str]]]:
    """columns_by_key ("schema.table" -> ((name, type), ...)) as the nested
    mapping sqlglot's qualifier wants. Needed to expand `select *` and to
    attribute unqualified column names in multi-table joins."""
    schema: dict[str, dict[str, dict[str, str]]] = {}
    for key, columns in columns_by_key.items():
        schema_name, _, table = key.partition(".")
        schema.setdefault(schema_name, {})[table] = {name: type_ for name, type_ in columns}
    return schema


def _leaf_sources(node) -> set[tuple[str, str]]:
    """(table, column) pairs at the leaves of a sqlglot lineage tree. A leaf
    whose expression is a Table reads from the catalog; anything else (a
    literal, an unresolvable subquery) contributes nothing."""
    found: set[tuple[str, str]] = set()
    stack = [node]
    while stack:
        n = stack.pop()
        if n.downstream:
            stack.extend(n.downstream)
            continue
        if isinstance(n.expression, exp.Table):
            table = n.expression
            schema_name = table.text("db")
            name = table.name
            column = n.name.rpartition(".")[2]
            if schema_name and name and column:
                found.add((f"{schema_name}.{name}".lower(), column))
    return found


def derive_column_lineage(
    sql_by_dst: dict[str, str],
    columns_by_key: dict[str, tuple[tuple[str, str], ...]],
) -> ColumnLineage:
    """Trace every measured column of every dst object through its SQL.

    Matching back to the catalog is case-insensitive with the catalog's
    spelling canonical, same rule as the manifest join.
    """
    canonical = {key.lower(): key for key in columns_by_key}
    schema = _schema_dict(columns_by_key)

    edges: set[ColumnEdge] = set()
    unparsed = 0
    for dst_key, sql in sorted(sql_by_dst.items()):
        out_columns = columns_by_key.get(dst_key)
        if not sql or not out_columns:
            continue
        try:
            expression = sqlglot.parse_one(sql, dialect=DIALECT)
        except SqlglotError as error:
            logger.debug("column lineage: cannot parse %s: %s", dst_key, error)
            unparsed += 1
            continue
        if isinstance(expression, (exp.Create, exp.Insert)):
            inner = expression.find(exp.Select) or expression.find(exp.Union)
            if inner is None:
                unparsed += 1
                continue
            expression = inner
        traced_any = False
        for name, _type in out_columns:
            try:
                node = lineage(name, expression.copy(), schema=schema, dialect=DIALECT)
            except SqlglotError as error:
                logger.debug("column lineage: %s.%s: %s", dst_key, name, error)
                continue
            traced_any = True
            for src_low, src_col in _leaf_sources(node):
                src = canonical.get(src_low)
                if src is not None and src != dst_key:
                    edges.add(ColumnEdge(src=src, src_col=src_col, dst=dst_key, dst_col=name))
        if not traced_any:
            unparsed += 1

    return ColumnLineage(
        edges=tuple(sorted(edges, key=lambda e: (e.dst, e.dst_col, e.src, e.src_col))),
        unparsed=unparsed,
    )
