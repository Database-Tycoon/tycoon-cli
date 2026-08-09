"""Table-level lineage from SQL text: which objects a view reads.

The sibling of `column_lineage.py` one grain coarser — that module traces
columns through a statement, this one decides whether a street exists between
two objects at all. Same posture: sqlglot with the duckdb dialect, and SQL it
cannot parse costs precision rather than the whole scan.

A view's stored definition is the only lineage a plain DuckDB file carries
(`duckdb_dependencies()` is empty in practice and dbt is not always there), so
this scan is the floor everything else is unioned on top of.
"""

import logging
import re
from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

from .column_lineage import DIALECT
from .models import CatalogObject, Edge

logger = logging.getLogger(__name__)


def _qualified_pattern(schema: str, name: str) -> re.Pattern[str]:
    s = re.escape(schema.lower())
    n = re.escape(name.lower())
    return re.compile(rf'\b"?{s}"?\s*\.\s*"?{n}"?\b')


def _bare_pattern(name: str) -> re.Pattern[str]:
    return re.compile(rf"\b{re.escape(name.lower())}\b")


def _bare_references(sql: str) -> set[str] | None:
    """The unqualified table names this SQL actually reads, lowercased — or
    None when sqlglot cannot parse it at all.

    Parsing rather than scanning is the whole point. A `\\bstatus\\b` search over
    the view's text matches inside string literals and comments, so on a real
    catalog a table called `status` or `date` wires itself to nearly every
    view and the city fills with streets nobody built. sqlglot only reports
    names that occupy a table position.

    Schema-qualified references are deliberately *not* returned: those are
    matched by `_qualified_pattern` against the raw text, which already
    tolerates quoting and spacing sqlglot would normalise away.
    """
    try:
        expression = sqlglot.parse_one(sql, dialect=DIALECT)
    except SqlglotError as error:
        logger.debug("lineage scan: cannot parse view SQL (%s)", error)
        return None
    if expression is None:
        return None
    if isinstance(expression, (exp.Create, exp.Insert)):
        # DuckDB stores a view as `CREATE VIEW v AS SELECT ...`; the target
        # `v` is a Table node too, and it is written, not read.
        inner = expression.expression
        if inner is None:
            return set()
        expression = inner
    return {table.name.lower() for table in expression.find_all(exp.Table) if table.name and not table.text("db")}


def _strip_literals_and_comments(sql: str) -> str:
    """String literals and `--`/`/* */` comments blanked out, quoted
    identifiers kept.

    Only ever used on the fallback path, where sqlglot could not parse the
    statement and the regex scan is all that is left. Blanking the places a
    table name cannot legally appear is what keeps `'status changed'` and
    `-- fix the status column` from inventing a street. A single pass rather
    than three substitutions, because a quote inside a comment and a `--`
    inside a literal each break the other ordering. Double quotes are
    identifiers in DuckDB and stay.
    """
    out: list[str] = []
    i, n = 0, len(sql)
    while i < n:
        ch = sql[i]
        if ch == "'":
            j = i + 1
            while j < n:
                if sql[j] != "'":
                    j += 1
                elif j + 1 < n and sql[j + 1] == "'":  # '' is an escaped quote
                    j += 2
                else:
                    break
            out.append(" ")
            i = j + 1
        elif ch == '"':
            end = sql.find('"', i + 1)
            end = n - 1 if end == -1 else end
            out.append(sql[i : end + 1])
            i = end + 1
        elif sql.startswith("--", i):
            end = sql.find("\n", i)
            i = n if end == -1 else end
            out.append(" ")
        elif sql.startswith("/*", i):
            end = sql.find("*/", i)
            i = n if end == -1 else end + 2
            out.append(" ")
        else:
            out.append(ch)
            i += 1
    return "".join(out)


@dataclass(frozen=True)
class SqlScan:
    """What the SQL scan found, and how well it knew it.

    `bare_pairs` are the edges matched on an **unqualified** table name alone —
    `from orders` rather than `from raw.orders`. They are inferences, not
    facts: the name was in a table position and it was unambiguous across the
    catalog, which is the best this scan can do and is still weaker than a
    schema-qualified reference or a declared dependency. The loader counts them
    so a diagnostic can say when lineage has become mostly guesswork; nothing
    downstream treats them as a separate provenance, because the wire format's
    `provenance` enum is a client contract.
    """

    edges: tuple[Edge, ...]
    bare_pairs: frozenset[tuple[str, str]]


# One identifier: a bare word or a double-quoted name (`""` escapes a quote),
# optionally followed by `.` and another. Used ONLY by `mentioned_keys`.
_IDENTIFIER = r'(?:"(?:[^"]|"")*"|[\w$]+)'
# Two groups, not a `partition('.')` on the match: `"a.b"."c"` is a schema
# with a dot in its name, and splitting on the first dot would read it as the
# schema `"a` — the same lossy split that costs those objects their column
# lineage would then cost them their retention too.
_REFERENCE = re.compile(rf"(?P<first>{_IDENTIFIER})(?:\s*\.\s*(?P<second>{_IDENTIFIER}))?")


def _unquote(token: str) -> str:
    token = token.strip()
    if token.startswith('"') and token.endswith('"') and len(token) >= 2:
        return token[1:-1].replace('""', '"').lower()
    return token.lower()


def mentioned_keys(objects: list[CatalogObject], view_sql: dict[str, str]) -> dict[str, frozenset[str]]:
    """Which catalog objects each view's SQL *mentions* — a deliberate
    over-approximation, used only to decide what the MAX_OBJECTS cap retains.

    `derive_edges_from_sql` remains the only authority on whether an edge
    exists: it parses, it refuses ambiguous bare names, and it runs on the
    retained set afterwards. This one has a different job and therefore a
    different bar. Retention has to happen *before* edges can be derived (the
    edge deriver takes the retained set as its input), and it has to be cheap
    at 2,000+ objects, so this is one linear tokenising pass per view rather
    than a parse per view times a pattern per object.

    Over-approximating is the safe direction here and under-approximating is
    not: keeping a table nothing reads costs one lot, while dropping a table a
    retained view reads costs that view its street — the exact failure this
    function exists to prevent.
    """
    by_key = {obj.key.lower(): obj.key for obj in objects}
    name_counts: dict[str, int] = {}
    for obj in objects:
        low = obj.name.lower()
        name_counts[low] = name_counts.get(low, 0) + 1
    by_name = {obj.name.lower(): obj.key for obj in objects if name_counts[obj.name.lower()] == 1}

    mentioned: dict[str, frozenset[str]] = {}
    for view_key, sql in view_sql.items():
        if not sql:
            continue
        found: set[str] = set()
        # Literals and comments blanked first: a table named `status` must not
        # be retained because someone wrote `-- status changed` in a view.
        for match in _REFERENCE.finditer(_strip_literals_and_comments(sql)):
            first, second = match.group("first"), match.group("second")
            if second is not None:
                key = by_key.get(f"{_unquote(first)}.{_unquote(second)}")
            else:
                key = by_name.get(_unquote(first))
            if key is not None and key != view_key:
                found.add(key)
        if found:
            mentioned[view_key] = frozenset(found)
    return mentioned


def derive_edges_from_sql(objects: list[CatalogObject], view_sql: dict[str, str]) -> list[Edge]:
    """The scan's edges. `scan_view_sql` is the same work with its confidence
    kept; this spelling is what every caller and test has used since v1."""
    return list(scan_view_sql(objects, view_sql).edges)


def scan_view_sql(objects: list[CatalogObject], view_sql: dict[str, str]) -> SqlScan:
    name_counts: dict[str, int] = {}
    for o in objects:
        key = o.name.lower()
        name_counts[key] = name_counts.get(key, 0) + 1

    # Compiled once per object, not once per (view, object) pair: the pair
    # loop is O(n^2), and at the 500-object cap that was a quarter of a
    # million `re.compile` calls per load.
    candidates = [(o, _qualified_pattern(o.schema, o.name), o.name.lower(), _bare_pattern(o.name)) for o in objects]

    edges: list[Edge] = []
    bare_pairs: set[tuple[str, str]] = set()
    for view in objects:
        sql = view_sql.get(view.key)
        if sql is None:
            continue
        low = sql.lower()
        referenced = _bare_references(sql)
        # Unparseable SQL still gets a scan, over text with the literals and
        # comments removed — degraded, never absent.
        scanned = low if referenced is not None else _strip_literals_and_comments(low)
        for other, qualified, bare_name, bare in candidates:
            if other.key == view.key:
                continue
            if qualified.search(low):
                edges.append(Edge(src=other.key, dst=view.key))
                continue
            if name_counts[bare_name] != 1:  # ambiguous across schemas: no guess
                continue
            hit = bare_name in referenced if referenced is not None else bare.search(scanned)
            if hit:
                edges.append(Edge(src=other.key, dst=view.key))
                bare_pairs.add((other.key, view.key))
    return SqlScan(edges=tuple(edges), bare_pairs=frozenset(bare_pairs))
