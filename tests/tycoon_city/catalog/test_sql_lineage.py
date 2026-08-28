"""Table-level lineage from view SQL: a street exists only where a table is
actually read.

The defect these pin: the old scan matched an unqualified table name anywhere
in the lowercased SQL, string literals and comments included. On a real
catalog a table called `status` or `date` therefore wired itself to nearly
every view, and the city filled with streets nobody built.
"""

import duckdb

from tycoon_city.catalog.loader import load_catalog
from tycoon_city.catalog.models import CatalogObject
from tycoon_city.catalog.sql_lineage import _bare_references, derive_edges_from_sql


def _obj(schema, name, kind="table", rows=1):
    return CatalogObject(schema=schema, name=name, kind=kind, row_count=rows)


def _pairs(edges):
    return {(e.src, e.dst) for e in edges}


def test_a_name_inside_a_string_literal_is_not_a_read(tmp_path):
    """`select 'status changed' as msg` must not connect the view to a table
    called `status`. The literal survives into DuckDB's stored view SQL, so
    this is the real text the scan sees."""
    db = tmp_path / "literal.duckdb"
    con = duckdb.connect(str(db))
    con.execute("create schema raw")
    con.execute("create table raw.orders as select 1 as id")
    con.execute("create table main.status as select 1 as code")
    con.execute("create view main.v_msg as select id, 'status changed' as msg from raw.orders")
    con.close()

    ctx = load_catalog(db)

    stored = next(o for o in ctx.objects if o.key == "main.v_msg")
    assert stored.kind == "view"
    pairs = _pairs(ctx.edges)
    # Precondition: the view really does read something, so an empty edge set
    # cannot be what makes this pass.
    assert ("raw.orders", "main.v_msg") in pairs
    assert ("main.status", "main.v_msg") not in pairs, "a string literal invented a street"


def test_a_comment_is_not_a_read():
    """DuckDB strips comments out of a stored view definition, so this runs
    against `derive_edges_from_sql` directly -- the function still has to be
    right for the dbt/manifest SQL that does carry comments."""
    objects = [_obj("raw", "orders"), _obj("main", "status"), _obj("main", "v", kind="view")]
    sql = {
        "main.v": "create view v as select id from raw.orders -- recheck the status table\n",
    }

    pairs = _pairs(derive_edges_from_sql(objects, sql))

    assert ("raw.orders", "main.v") in pairs
    assert ("main.status", "main.v") not in pairs, "a comment invented a street"


def test_a_column_named_like_a_table_is_not_a_read(tmp_path):
    """The case only parsing can get right. `select status from raw.orders`
    puts the word `status` in a *column* position; no regex over the text can
    tell that from a table reference, and on a real catalog a table called
    `status` or `date` therefore joined itself to nearly every view."""
    db = tmp_path / "column.duckdb"
    con = duckdb.connect(str(db))
    con.execute("create schema raw")
    con.execute("create table raw.orders as select 1 as id, 'ok' as status")
    con.execute("create table main.status as select 1 as code")
    con.execute("create view main.v_cols as select id, status from raw.orders")
    con.close()

    ctx = load_catalog(db)

    pairs = _pairs(ctx.edges)
    assert ("raw.orders", "main.v_cols") in pairs
    assert ("main.status", "main.v_cols") not in pairs, "a column name invented a street"


def test_a_real_unqualified_reference_still_derives_the_edge(tmp_path):
    """The true positive the scan exists for. `search_path` resolves the name
    at creation time but the stored SQL keeps it bare, exactly as a hand-written
    view on a client catalog does."""
    db = tmp_path / "bare.duckdb"
    con = duckdb.connect(str(db))
    con.execute("create schema raw")
    con.execute("create table raw.orders as select 1 as id")
    con.execute("set search_path='raw'")
    con.execute("create view main.v_bare as select * from orders")
    stored = con.execute("select sql from duckdb_views() where view_name = 'v_bare'").fetchone()[0]
    con.close()

    # Precondition: DuckDB really did keep the reference unqualified, so the
    # qualified matcher cannot be what makes this pass.
    assert "raw.orders" not in stored.lower(), stored

    ctx = load_catalog(db)

    assert ("raw.orders", "main.v_bare") in _pairs(ctx.edges)


def test_unqualified_reference_through_a_join_and_a_cte():
    """Table positions the parser finds and a `\\bname\\b` scan would too --
    kept so the sqlglot rewrite cannot pass by finding nothing."""
    objects = [
        _obj("raw", "orders"),
        _obj("raw", "customers"),
        _obj("main", "v", kind="view"),
    ]
    sql = {
        "main.v": (
            "create view v as with recent as (select * from orders) select * from recent join customers using (id)"
        )
    }

    pairs = _pairs(derive_edges_from_sql(objects, sql))

    assert ("raw.orders", "main.v") in pairs
    assert ("raw.customers", "main.v") in pairs


def test_unparseable_sql_falls_back_to_a_scan_that_still_skips_literals():
    """sqlglot cannot parse this, so the regex fallback runs -- degraded, but
    not absent, and not credulous either: the literal must still not count."""
    broken = (
        "create view v as select * from orders "
        "where note = 'status pending' and x in ((("  # unbalanced: unparseable
    )
    # Precondition: this really is on the fallback path.
    assert _bare_references(broken) is None, "sqlglot parsed it; the fallback never ran"

    objects = [_obj("raw", "orders"), _obj("main", "status"), _obj("main", "v", kind="view")]

    pairs = _pairs(derive_edges_from_sql(objects, {"main.v": broken}))

    assert ("raw.orders", "main.v") in pairs, "the fallback lost a real read"
    assert ("main.status", "main.v") not in pairs, "the fallback matched inside a literal"


def test_patterns_are_compiled_per_object_not_per_pair(monkeypatch):
    """The scan is an O(n*m) loop over (view, object). Compiling the patterns
    inside it made a 500-object catalog do a quarter of a million
    `re.compile` calls per load; they belong outside."""
    from tycoon_city.catalog import sql_lineage

    objects = [_obj("raw", f"t{i}") for i in range(40)]
    objects += [_obj("marts", f"v{i}", kind="view") for i in range(20)]
    view_sql = {f"marts.v{i}": f"create view v{i} as select * from raw.t{i}" for i in range(20)}

    compiles = []
    for name in ("_qualified_pattern", "_bare_pattern"):
        real = getattr(sql_lineage, name)

        def counting(*args, _real=real, _name=name):
            compiles.append(_name)
            return _real(*args)

        monkeypatch.setattr(sql_lineage, name, counting)

    edges = derive_edges_from_sql(objects, view_sql)

    # Precondition: the pair loop really ran (20 views x 60 objects).
    assert len(edges) >= 20
    assert len(compiles) <= 2 * len(objects), (
        f"{len(compiles)} compiles for {len(objects)} objects and "
        f"{len(view_sql)} views -- that is per-pair, not per-object"
    )
