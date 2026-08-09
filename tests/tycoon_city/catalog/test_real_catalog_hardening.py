"""What a real client catalog does to the loader that a fixture never did.

Every fixture here is adversarial on purpose and says so in its own
preconditions: the wrong-axis trap in this repo is a test asserting the right
value on an axis that cannot fail, and a "hostile" catalog that is not
actually hostile makes every guard below unfalsifiable. So each test first
proves its fixture really has the shape it claims -- more views than the cap,
two objects that really do collide on one key, a schema that really is
uppercase against a metadata table that really is lowercase -- and only then
asserts WHICH objects survived.

Nothing here touches a real catalog; `~/clients/dogfood` is never read.
"""

import duckdb
import pytest

from tests.fixtures.tycoon_factory import ModelSpec, SourceSpec, make_tycoon_project
from tycoon_city.catalog import loader, retention
from tycoon_city.catalog.loader import load_catalog, load_context
from tycoon_city.catalog.models import CatalogObject
from tycoon_city.catalog.retention import MAX_OBJECTS, _cap_note, _cap_objects
from tycoon_city.export.build import build_city
from tycoon_city.sim.signals import LastBuildAt
from tycoon_city.theme_data import load_theme_data, theme_dir


def _style_rules():
    return load_theme_data(theme_dir("default")).style_rules


# --- the cap: whole neighbourhoods, not 500 disconnected views --------------


def _paired_catalog(schemas: int, per_schema: int):
    """`per_schema` (view, table) pairs in each schema; each view reads its own
    table by a schema-qualified name. Nothing else connects to anything."""
    objects: list[CatalogObject] = []
    view_sql: dict[str, str] = {}
    for s in range(schemas):
        for i in range(per_schema):
            table = CatalogObject(schema=f"s{s}", name=f"t{i}", kind="table", row_count=100 + i)
            view = CatalogObject(schema=f"s{s}", name=f"v{i}", kind="view", row_count=0)
            objects.extend((table, view))
            view_sql[view.key] = f"select * from s{s}.t{i}"
    objects.sort(key=lambda o: o.key)
    return objects, view_sql


def test_the_cap_keeps_each_view_with_the_table_it_reads():
    """A catalog of 1,200 objects, 600 of them views.

    The rule this replaces kept views wholesale, so it spent the entire budget
    on views and retained NO tables: measured on a 2,060-object catalog that
    left 500 buildings and 59 streets, because every table those views read
    had been dropped. Retention has to keep pairs, not kinds.
    """
    objects, view_sql = _paired_catalog(schemas=3, per_schema=200)
    views = [o for o in objects if o.kind == "view"]
    tables = [o for o in objects if o.kind == "table"]

    # Preconditions: the fixture is really adversarial. More views than the
    # whole budget is what makes "views first" fatal rather than merely crude.
    assert len(objects) == 1200
    assert len(views) > MAX_OBJECTS, "fewer views than the cap: the old rule would have passed"
    assert len(tables) > MAX_OBJECTS

    kept = _cap_objects(objects, view_sql)
    kept_keys = {o.key for o in kept}

    assert len(kept) == MAX_OBJECTS
    kept_views = [o for o in kept if o.kind == "view"]
    kept_tables = [o for o in kept if o.kind == "table"]
    # WHICH objects survived, not merely how many: every retained view has the
    # table it reads standing next to it, so every one of them keeps a street.
    assert kept_views, "no views retained -- lineage cannot exist"
    assert kept_tables, "no tables retained -- this is the failure being fixed"
    for view in kept_views:
        source = f"{view.schema}.t{view.name[1:]}"
        assert source in kept_keys, f"{view.key} was retained without the table it reads"
    assert len(kept_views) == len(kept_tables) == MAX_OBJECTS // 2

    # And no schema is silently deleted: districts are 1:1 with schemas.
    assert {o.schema for o in kept} == {o.schema for o in objects}


def test_the_cap_deals_neighbourhoods_round_robin_so_no_schema_vanishes():
    """One schema large enough to eat the whole budget alphabetically first."""
    objects, view_sql = _paired_catalog(schemas=1, per_schema=400)
    small, small_sql = _paired_catalog(schemas=1, per_schema=60)
    renamed = [CatalogObject(schema="zz_small", name=o.name, kind=o.kind, row_count=o.row_count) for o in small]
    objects += renamed
    view_sql.update(
        {f"zz_small.{key.split('.')[1]}": sql.replace("s0.", "zz_small.") for key, sql in small_sql.items()}
    )
    objects.sort(key=lambda o: o.key)

    # Precondition: `s0` alone is bigger than the budget, so an alphabetical
    # pass never reaches `zz_small` at all.
    assert sum(1 for o in objects if o.schema == "s0") > MAX_OBJECTS

    kept = _cap_objects(objects, view_sql)
    assert {o.schema for o in kept} == {"s0", "zz_small"}
    assert sum(1 for o in kept if o.schema == "zz_small") >= 100


def test_the_cap_keeps_a_dotted_schema_neighbourhood_together():
    """A schema whose name contains a `.` must not come apart at the cap.

    The retention scan resolves `"a.b"."t"` by matching the whole reference,
    not by splitting the token on its first dot -- which would read the schema
    as `"a` and drop the table the view reads.
    """
    objects, view_sql = _paired_catalog(schemas=1, per_schema=400)
    table = CatalogObject(schema="a.b", name="t", kind="table", row_count=1)
    view = CatalogObject(schema="a.b", name="v", kind="view", row_count=0)
    objects += [table, view]
    view_sql[view.key] = 'select * from "a.b"."t"'
    objects.sort(key=lambda o: o.key)

    # Preconditions: the cap fires, and the dotted key really is ambiguous to
    # split -- `a.b.t` reads as schema `a` table `b.t` just as well.
    assert len(objects) > MAX_OBJECTS
    assert table.key == "a.b.t" and table.key.partition(".")[0] == "a"

    kept = {o.key for o in _cap_objects(objects, view_sql)}
    assert "a.b.v" in kept
    assert "a.b.t" in kept, "the dotted-schema view kept its street's other end?"


def test_a_catalog_with_no_view_sql_still_keeps_the_largest_tables():
    """The old rule's behaviour, unchanged where it was right: with nothing to
    read the neighbourhood pass is a no-op and size decides."""
    objects = [CatalogObject(schema="main", name=f"t{i}", kind="table", row_count=i) for i in range(600)]
    kept = _cap_objects(objects, {})
    assert len(kept) == MAX_OBJECTS
    assert max(o.row_count for o in objects if o.key not in {k.key for k in kept}) < min(o.row_count for o in kept)


def test_the_cap_note_names_the_kinds_and_the_lost_districts():
    before = [CatalogObject(schema=f"s{i}", name="t", kind="table", row_count=1) for i in range(10)] + [
        CatalogObject(schema="s0", name="v", kind="view", row_count=0)
    ]
    after = [o for o in before if o.schema in {"s0", "s1"}]
    # Precondition: this really did lose whole schemas, not just objects.
    assert len({o.schema for o in before} - {o.schema for o in after}) == 8

    note = _cap_note(before, after)
    assert "11 objects" in note
    assert "1 of 1 views" in note
    assert "2 of 10 tables" in note
    assert "8 schemas dropped entirely" in note


def test_the_cap_note_stays_quiet_about_districts_when_none_were_lost():
    before = [CatalogObject(schema="s", name=f"t{i}", kind="table", row_count=1) for i in range(3)]
    assert "dropped entirely" not in _cap_note(before, before[:2])


def test_a_capped_load_keeps_lineage_end_to_end(tmp_path, monkeypatch):
    """The same rule through the real loader, at a size a test can afford."""
    db = tmp_path / "capped.duckdb"
    con = duckdb.connect(str(db))
    for i in range(6):
        con.execute(f"create table t{i} as select * from range({i + 1}) r(id)")
        con.execute(f"create view v{i} as select id from t{i}")
    con.close()
    monkeypatch.setattr(retention, "MAX_OBJECTS", 6)

    ctx = load_catalog(db)

    # Preconditions: the cap fired, and there were more views than budget/2.
    assert ctx.object_count == 6
    assert any("12 objects" in note for note in ctx.notes), ctx.notes
    kinds = {obj.key: obj.kind for obj in ctx.objects}
    assert sum(1 for k in kinds.values() if k == "view") == 3
    assert sum(1 for k in kinds.values() if k == "table") == 3
    # Every retained view kept the table it reads, so every one has a street.
    for key, kind in kinds.items():
        if kind == "view":
            assert f"main.t{key[-1]}" in kinds
    assert len(ctx.edges) == 3


# --- hostile identifiers ----------------------------------------------------


def test_two_objects_that_collide_on_one_key_do_not_crash_the_layout(tmp_path):
    """`a.b`.`c` and `a`.`b.c` are different objects with the same catalog key.

    DuckDB allows a `.` inside an identifier, so this is a real catalog, not a
    contrivance. Before the fix the second object silently replaced the first
    in every key-addressed map, and `plan_dag_layout` then died on the schema
    that was left holding no placed lot (`min() iterable argument is empty`).
    """
    db = tmp_path / "dots.duckdb"
    con = duckdb.connect(str(db))
    con.execute('create schema "a.b"')
    con.execute('create schema "a"')
    con.execute('create table "a.b"."c" as select 1 as id')
    con.execute('create table "a"."b.c" as select 2 as id')
    con.close()

    # Precondition: the warehouse really holds two objects, and they really do
    # produce one key. Without this the test could pass on a catalog of one.
    with duckdb.connect(str(db), read_only=True) as reader:
        tables, _views = loader._scan_catalog(reader)
    assert len(tables) == 2
    assert len({f"{schema}.{name}" for schema, name, _size, _oid in tables}) == 1

    ctx = load_catalog(db)

    assert ctx.object_count == 1
    # Deterministic: the winner cannot depend on the order DuckDB listed them.
    assert ctx.objects[0].schema == "a"
    assert ctx.objects[0].name == "b.c"
    assert any("collide" in note and "1 object" in note for note in ctx.notes), ctx.notes

    # The crash itself.
    _ctx, city = build_city(db, _style_rules())
    assert len(city.lots) == 1


def test_hostile_identifiers_survive_the_whole_pipeline(tmp_path):
    """Unicode, spaces, embedded quotes, 200 characters, and mixed case."""
    long_name = "x" * 200
    db = tmp_path / "hostile.duckdb"
    con = duckdb.connect(str(db))
    con.execute('create schema "Mixed Case"')
    con.execute('create schema "café"')
    con.execute('create table "Mixed Case"."Order Details" as select 1 as id')
    con.execute('create view "Mixed Case"."v Details" as select id from "Mixed Case"."Order Details"')
    con.execute('create table "café"."naïve_ünïcode" as select 2 as id')
    con.execute('create table "café"."quo""te" as select 3 as id')
    con.execute(f'create table "café"."{long_name}" as select 4 as id')
    con.close()

    ctx = load_catalog(db)

    # Precondition: the names really did survive the scan unmangled.
    keys = {obj.key for obj in ctx.objects}
    assert 'café.quo"te' in keys
    assert f"café.{long_name}" in keys
    assert ctx.object_count == 5

    # A space inside both the schema and the object name still yields lineage.
    assert ("Mixed Case.Order Details", "Mixed Case.v Details") in {(edge.src, edge.dst) for edge in ctx.edges}
    _ctx, city = build_city(db, _style_rules())
    assert len(city.lots) == 5


def test_a_dot_inside_a_schema_name_costs_column_lineage_and_says_so(tmp_path):
    """The limitation is real and is therefore named: `schema.name` cannot be
    split back into its parts, and column lineage needs the parts."""
    db = tmp_path / "dotted.duckdb"
    con = duckdb.connect(str(db))
    con.execute('create schema "a.b"')
    con.execute('create table "a.b"."t" as select 1 as id')
    con.execute('create view "a.b"."v" as select id from "a.b"."t"')
    con.close()

    ctx = load_catalog(db)

    # Precondition: the table-level street DOES exist, so the missing column
    # edge is a column-lineage fact and not "the objects never joined at all".
    assert ("a.b.t", "a.b.v") in {(e.src, e.dst) for e in ctx.edges}
    assert ctx.column_edges == ()
    assert any("contains a '.'" in note for note in ctx.notes), ctx.notes


# --- degenerate shapes ------------------------------------------------------


@pytest.mark.parametrize("statements", [(), ("create table t as select 1 as id",)])
def test_an_empty_or_single_object_catalog_still_renders(tmp_path, statements):
    db = tmp_path / f"tiny{len(statements)}.duckdb"
    con = duckdb.connect(str(db))
    for statement in statements:
        con.execute(statement)
    con.close()

    ctx, city = build_city(db, _style_rules())
    assert ctx.object_count == len(statements)
    assert len(city.lots) == len(statements)
    assert city.width > 0 and city.height > 0


# --- mixed case: the joins that silently drop an object ---------------------


def _mixed_case_project(root, warehouse_schema: str, dlt_schema: str):
    """A warehouse and a dlt history that disagree about how a schema is
    spelled -- the ordinary shape of a DuckDB copy of a Snowflake account."""
    make_tycoon_project(
        root,
        models=(ModelSpec("MART", "dim_thing", depends_on=()),),
        sources=(SourceSpec(warehouse_schema, "Orders"),),
        tests=(),
    )
    con = duckdb.connect(str(root / ".tycoon" / "metadata.duckdb"))
    con.execute(
        f"insert into dlt_runs values ('{dlt_schema}', 'load-1', 0, "
        "timestamp '2026-08-02 01:00:00', 'hash', timestamp '2026-08-02 01:00:00')"
    )
    con.close()
    return root


# Both directions, because each side of the join has its own case fold and a
# fixture that exercises only one of them makes the other unfalsifiable --
# which is exactly how the first version of this test let a mutant live.
@pytest.mark.parametrize(("warehouse_schema", "dlt_schema"), [("RAW", "raw"), ("raw", "RAW")])
def test_a_dlt_load_reaches_a_schema_spelled_the_other_way(tmp_path, warehouse_schema, dlt_schema):
    """`LastBuildAt`'s dlt fallback joined `dlt_runs.source_schema` to
    `obj.schema` exactly, while its sibling `RowDelta` case-folded both sides.
    A raw district whose case did not match therefore rendered as never
    loaded -- unknown wearing stale, the one thing this project forbids."""
    root = _mixed_case_project(tmp_path / f"mixed-{warehouse_schema}", warehouse_schema, dlt_schema)
    ctx = load_context(str(root))
    key = f"{warehouse_schema}.Orders"

    # Preconditions: the two sides really do disagree on case, and no other
    # source of a build time covers this object -- otherwise the dlt join is
    # not the axis under test.
    assert key in {obj.key for obj in ctx.objects}
    assert warehouse_schema != dlt_schema
    assert key not in ctx.dbt_nodes_by_key
    assert key not in ctx.source_freshness_by_key

    built = LastBuildAt().compute(ctx)
    assert key in built, f"the schema spelled {warehouse_schema!r} lost its load time"
    assert built[key] == ctx.runs.dlt_loaded_at[dlt_schema.lower()]


# --- partial artifacts ------------------------------------------------------


def test_run_history_that_names_nothing_in_this_catalog_is_named(tmp_path):
    """Run history joins through dbt unique_ids. Rename a model and every
    temporal signal for it goes dark with nothing to say why."""
    root = make_tycoon_project(tmp_path / "renamed", models=DEFAULT_ONE, sources=(), tests=())
    con = duckdb.connect(str(root / ".tycoon" / "metadata.duckdb"))
    con.execute(
        "insert into dbt_nodes values ('run-1', 'model.fx_dbt.deleted_model', 'model', "
        "'success', 1.0, NULL, 0.01, NULL)"
    )
    con.close()

    ctx = load_context(str(root))

    # Preconditions: a manifest DID join (so "no manifest" is not the cause),
    # and the orphan really is in the history and really is not in the join.
    assert ctx.dbt_nodes_by_key, "no manifest joined; the note would be meaningless"
    assert "model.fx_dbt.deleted_model" in ctx.runs.node_results
    assert "model.fx_dbt.deleted_model" not in set(ctx.dbt_nodes_by_key.values())

    assert any("do not match anything in this catalog" in note for note in ctx.notes), ctx.notes


def test_a_project_with_no_manifest_does_not_claim_orphaned_run_nodes(tmp_path):
    """With no manifest EVERY node is unmatched, and the ladder already says
    so. A second note counting them all would be noise dressed as a finding."""
    root = make_tycoon_project(tmp_path / "nomanifest", models=DEFAULT_ONE, sources=(), tests=(), with_manifest=False)
    ctx = load_context(str(root))

    assert ctx.runs is not None and ctx.runs.node_results  # precondition
    assert not ctx.dbt_nodes_by_key
    assert any("no dbt manifest" in note for note in ctx.notes)
    assert not any("do not match anything" in note for note in ctx.notes), ctx.notes


DEFAULT_ONE = (ModelSpec("staging", "stg_orders", depends_on=()),)


# --- how much of the lineage is a guess -------------------------------------


def test_bare_name_edges_are_counted_and_qualified_ones_are_not(tmp_path):
    db = tmp_path / "bare.duckdb"
    con = duckdb.connect(str(db))
    con.execute("create schema raw")
    con.execute("create table raw.orders as select 1 as id")
    con.execute("create table raw.items as select 1 as id")
    # Two views, one edge each: the first names its source in full, the second
    # relies on the search path.
    con.execute("create view raw.qualified as select id from raw.orders")
    con.execute("create view raw.bare as select id from items")
    con.close()

    ctx = load_catalog(db)
    pairs = {(edge.src, edge.dst) for edge in ctx.edges}

    # Precondition: BOTH edges exist. Counting bare-name edges is only
    # meaningful if the bare one was derived at all.
    assert ("raw.orders", "raw.qualified") in pairs
    assert ("raw.items", "raw.bare") in pairs
    assert ctx.bare_name_edges == 1


def test_a_manifest_declaration_stops_an_edge_being_a_guess(tmp_path):
    """A bare-name match the dbt manifest independently declares is a fact.
    Counting it as guesswork would report a documented project as a hairball."""
    root = tmp_path / "declared"
    make_tycoon_project(
        root,
        models=(
            ModelSpec("staging", "stg_orders", depends_on=()),
            ModelSpec(
                "staging",
                "fct_orders",
                depends_on=("model.fx_dbt.stg_orders",),
                raw_code="select id from {{ ref('stg_orders') }}",
            ),
        ),
        sources=(),
        tests=(),
    )
    # The warehouse is tables-only, so give the scan a view that names its
    # source WITHOUT a schema -- the bare-name path.
    con = duckdb.connect(str(root / "data" / "fx.duckdb"))
    con.execute("create view staging.v_bare as select id from stg_orders")
    con.close()

    plain = load_catalog(root / "data" / "fx.duckdb")
    joined = load_context(str(root))

    # Precondition: on its own, the scan really does call this a guess.
    assert plain.bare_name_edges == 1
    # And the manifest edge is present, tagged, and not double-counted.
    assert any(e.provenance == "manifest" for e in joined.edges)
    assert joined.bare_name_edges == 1  # the view edge; the model edge is declared
    assert {e.provenance for e in joined.edges} == {"manifest", "view_sql"}
