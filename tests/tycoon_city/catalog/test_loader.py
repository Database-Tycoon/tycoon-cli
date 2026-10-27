import duckdb
import pytest

from tycoon_city.catalog.errors import CatalogError
from tycoon_city.catalog.loader import (
    _database_name_for,
    is_motherduck,
    _scan_catalog,
    load_catalog,
)


def _make_db(path):
    con = duckdb.connect(str(path))
    con.execute("create schema raw")
    con.execute("create table raw.orders as select * from range(5) t(id)")
    con.execute("create view main.v_orders as select * from raw.orders")
    con.close()


def test_load_catalog_reads_objects(tmp_path):
    db = tmp_path / "fx.duckdb"
    _make_db(db)

    ctx = load_catalog(db)

    keys = {o.key for o in ctx.objects}
    assert "raw.orders" in keys
    assert "main.v_orders" in keys
    assert ctx.database_name == "fx"

    orders = next(o for o in ctx.objects if o.key == "raw.orders")
    assert orders.kind == "table"
    assert orders.row_count == 5

    v_orders = next(o for o in ctx.objects if o.key == "main.v_orders")
    assert v_orders.kind == "view"
    assert ctx.object_count == 2
    assert ctx.total_rows == 5


def test_scan_catalog_ignores_attached_databases(tmp_path):
    """`_scan_catalog` must return only the connected database's objects.

    `duckdb_tables()`/`duckdb_views()` list every ATTACHED database. Against a
    local file nothing is attached, so an unscoped query looks correct -- but
    MotherDuck attaches every database and share in the account on connect, so
    an unscoped query merges a whole account into one city.

    This asserts on `_scan_catalog` with a live ATTACH rather than on
    `load_catalog`, because ATTACH is session-scoped: it cannot be persisted
    into a file, so a `load_catalog` test would open a fresh connection with
    nothing attached and pass without ever creating the condition.
    """
    primary = tmp_path / "primary.duckdb"
    other = tmp_path / "other.duckdb"

    con = duckdb.connect(str(primary))
    con.execute("create schema raw")
    con.execute("create table raw.mine as select 1 as i")
    con.execute("create view raw.mine_v as select * from raw.mine")
    con.close()

    con = duckdb.connect(str(other))
    con.execute("create schema raw")
    con.execute("create table raw.theirs as select 1 as i")
    con.execute("create view raw.theirs_v as select * from raw.theirs")
    con.close()

    con = duckdb.connect(str(primary), read_only=True)
    try:
        con.execute(f"attach '{other}' as other (read_only)")
        # The attach is live: without scoping both databases would be visible.
        visible = {r[0] for r in con.execute("select database_name from duckdb_tables()").fetchall()}
        assert visible == {"primary", "other"}, f"fixture did not attach: {visible}"

        tables, views = _scan_catalog(con)
        assert [(s, n) for s, n, _sz, _oid in tables] == [("raw", "mine")]
        assert [(s, n) for s, n, _sql, _oid in views] == [("raw", "mine_v")]
    finally:
        con.close()


@pytest.mark.parametrize("prefix", ["md:", "motherduck:"])
def test_motherduck_source_is_not_treated_as_a_file_path(prefix, monkeypatch):
    """`md:` and `motherduck:` catalogs are not filesystem paths.

    The existence check must be skipped for them, and the displayed name must be
    the catalog rather than a path stem. The connection is mocked: with no token
    a real `md:` connect opens a browser sign-in.
    """
    assert is_motherduck(f"{prefix}my_db")
    assert not is_motherduck("/tmp/my_db.duckdb")
    assert not is_motherduck("/tmp/backup-md:/my_db.duckdb")

    assert _database_name_for(f"{prefix}my_db") == "my_db"
    # Share URLs: neither "_share" nor a UUID names the database usefully.
    assert _database_name_for(f"{prefix}_share/dogfood_dbt_prod/b0614b23-ed92") == "dogfood_dbt_prod"
    assert _database_name_for("/tmp/demo.duckdb") == "demo"

    # A missing catalog must not raise "Database file not found" -- that
    # message would send the user looking for a file that was never meant to
    # exist. It fails at connect instead.
    attempted = []

    def refuse(database, *args, **kwargs):
        attempted.append(database)
        raise duckdb.IOException("mocked: no connection")

    monkeypatch.setattr("tycoon_city.catalog.loader.duckdb.connect", refuse)
    with pytest.raises(CatalogError) as exc:
        load_catalog(f"{prefix}definitely_not_a_real_catalog_xyz")
    assert attempted == [f"{prefix}definitely_not_a_real_catalog_xyz"]
    assert "not found" not in str(exc.value).lower()


def test_a_motherduck_prefix_is_not_a_directory_or_file_to_look_for(tmp_path):
    from tycoon_city.pricing import DEFAULT_PRICE_BOOK, resolve_price_book
    from tycoon_city.webserve import _fingerprint

    assert resolve_price_book("motherduck:some_db") == DEFAULT_PRICE_BOOK
    assert _fingerprint("motherduck:some_catalog") is None
    assert _fingerprint(str(tmp_path / "not_a_project_dir")) is not None
