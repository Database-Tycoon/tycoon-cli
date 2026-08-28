"""Build a synthetic tycoon project on disk, shaped like the real thing.

**It lives in the package, not under `tests/`, because it has two callers
now**: the test suite, which reaches it through the re-export at
`tests/fixtures/tycoon_factory.py`, and `tycoon-city demo`, which materialises a
project at runtime out of an installed wheel — where `tests/` does not exist.
One producer of project-shaped fixtures, as with every other document here;
two would drift apart the first time dbt's metadata schema moved.

Every shape here was copied from a real project (dogfood, 2026-08-04), not
invented — that is the whole point of the factory:

- `tycoon.yml` carries `stack.orchestrator` and, with `drift_keys=True`, an
  `ask:` block — keys absent from the CLI's pydantic model, present in real
  files. It never carries `schema_version`.
- The manifest is v12. Test nodes may have `attached_node: None` (real singular
  tests do) with `depends_on.nodes` as the only link. Sources may name a
  database that is not this warehouse (dogfood's raw lives in MotherDuck).
- `dbt_runs.success` is NULL on every real row, and `dbt_nodes.rows_affected`
  is NULL on all 244 — the factory writes NULLs so no test can accidentally
  depend on reading them.

No test touches `~/clients/dogfood`; this factory is its stand-in.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import duckdb


@dataclass(frozen=True)
class ModelSpec:
    schema: str
    name: str
    alias: str | None = None  # dbt `alias:` override; the table is named this
    depends_on: tuple[str, ...] = ()  # unique_ids
    materialized: str = "table"
    rows: int = 10
    description: str = ""
    tags: tuple[str, ...] = ()
    owner: str | None = None
    # (name, duckdb type) pairs; a small typed mix by default so column
    # features (facade windows, the inspector table) have material.
    columns: tuple[tuple[str, str], ...] = (
        ("id", "BIGINT"),
        ("name", "VARCHAR"),
        ("amount", "DOUBLE"),
        ("created_at", "TIMESTAMP"),
    )
    column_docs: dict[str, str] | None = None
    # The model's jinja-SQL, like real manifests carry (dogfood has raw_code
    # on all 40 models and compiled_code on none). None emits "" — a model
    # column lineage cannot trace, which is itself a real shape.
    raw_code: str | None = None

    @property
    def unique_id(self) -> str:
        return f"model.fx_dbt.{self.name}"

    @property
    def table_name(self) -> str:
        return self.alias or self.name


@dataclass(frozen=True)
class SourceSpec:
    schema: str
    name: str
    database: str = "fx"  # set to something else to model an external source
    rows: int = 100

    @property
    def unique_id(self) -> str:
        return f"source.fx_dbt.{self.schema}.{self.name}"


@dataclass(frozen=True)
class TestSpec:
    name: str
    attached_node: str | None  # None models a real singular test
    depends_on: tuple[str, ...] = ()
    column: str | None = None

    @property
    def unique_id(self) -> str:
        return f"test.fx_dbt.{self.name}"


@dataclass(frozen=True)
class RunSpec:
    invocation_id: str
    command: str = "run"
    started_at: datetime = datetime(2026, 8, 1, 2, 0, 0)
    target: str = "dev"
    models_error: int = 0
    tests_failed: int = 0
    # (node unique_id, status, execution_time_s)
    nodes: tuple[tuple[str, str, float], ...] = ()


DEFAULT_MODELS = (
    # raw_code shapes mirror real projects: a config block plus source()/ref()
    # calls, resolvable without a jinja engine. stg_daily's is left None (-> "")
    # so the default project always carries one untraceable model.
    ModelSpec(
        "staging",
        "stg_orders",
        depends_on=("source.fx_dbt.raw.orders",),
        raw_code=(
            "{{ config(materialized='table') }}\n"
            "select id, cast(payload->>'name' as varchar) as name,\n"
            "  cast(null as double) as amount, current_timestamp as created_at\n"
            "from {{ source('raw', 'orders') }}"
        ),
    ),
    ModelSpec(
        "marts",
        "fct_revenue_model",
        alias="fct_revenue",  # the alias-override case: table name != model name
        depends_on=("model.fx_dbt.stg_orders",),
        raw_code=(
            "{{ config(materialized='table') }}\nselect id, name, amount, created_at from {{ ref('stg_orders') }}"
        ),
    ),
    # The same-table-name-two-schemas pair. dbt forbids duplicate *model*
    # names in a project, so the realistic shape is two models whose aliases
    # collide: both tables are called "daily", one per schema. Joining on any
    # bare name — model or table — would conflate them.
    ModelSpec("staging", "stg_daily", alias="daily", depends_on=("source.fx_dbt.raw.orders",)),
    ModelSpec(
        "marts",
        "mart_daily",
        alias="daily",
        depends_on=("model.fx_dbt.stg_orders",),
        # ref('stg_daily') must resolve to staging.daily (the ALIAS, not the
        # model name) or the traced SQL reads from a table that does not exist.
        raw_code="select id, name, amount, created_at from {{ ref('stg_daily') }}",
    ),
)

DEFAULT_SOURCES = (
    SourceSpec("raw", "orders"),
    # Lives in another database entirely — must be dropped and counted.
    SourceSpec("ext", "events", database="somewhere_else"),
)

DEFAULT_TESTS = (
    TestSpec("not_null_stg_orders_id", attached_node="model.fx_dbt.stg_orders"),
    # attached_node None with depends_on fallback, like real singular tests.
    TestSpec(
        "assert_revenue_positive",
        attached_node=None,
        depends_on=("model.fx_dbt.fct_revenue_model",),
    ),
)


# --- The failure-cascade project ------------------------------------------
#
# One DAG, shaped so a replay's three questions have hand-countable answers:
# a failure, the skips dbt reported behind it, a skip that is NOT downstream of
# it, and a model that IS downstream and was built anyway.
#
#   raw.orders -> staging.stg_orders -+-> mart.zz_fail -+-> mart.aa_skip -> mart.bb_skip_deep
#                                     |                 +-> mart.cc_built
#                                     +-> mart.zzz_skip_unrelated
#
# Every name is chosen against the alphabet, because order ties break on
# object_key and a fixture that is right by alphabetical luck is this repo's
# signature defect: `aa_skip`/`bb_skip_deep` sort BEFORE the failure that
# caused them, and `zzz_skip_unrelated` sorts AFTER it -- so the cascade's
# "reachable" test and its "later" test each have to do their own work.
CASCADE_MODELS = (
    ModelSpec("staging", "stg_orders", depends_on=("source.fx_dbt.raw.orders",), rows=500),
    ModelSpec("mart", "zz_fail", depends_on=("model.fx_dbt.stg_orders",), rows=10),
    ModelSpec("mart", "aa_skip", depends_on=("model.fx_dbt.zz_fail",), rows=10),
    ModelSpec("mart", "bb_skip_deep", depends_on=("model.fx_dbt.aa_skip",), rows=10),
    ModelSpec("mart", "cc_built", depends_on=("model.fx_dbt.zz_fail",), rows=10),
    ModelSpec("mart", "zzz_skip_unrelated", depends_on=("model.fx_dbt.stg_orders",), rows=10),
)

CASCADE_SOURCES = (SourceSpec("raw", "orders", rows=1000),)

CASCADE_TESTS = (TestSpec("check_orders", attached_node="model.fx_dbt.stg_orders"),)

CASCADE_RUNS = (
    # The whole build: a success, a failure, three skips, one downstream model
    # dbt built anyway, and a failing test (no building of its own).
    RunSpec(
        "build-1",
        "build",
        datetime(2026, 8, 2, 3, 0),
        models_error=1,
        tests_failed=1,
        nodes=(
            ("model.fx_dbt.stg_orders", "success", 1.5),
            ("model.fx_dbt.zz_fail", "error", 0.4),
            ("model.fx_dbt.aa_skip", "skipped", 0.0),
            ("model.fx_dbt.bb_skip_deep", "skipped", 0.0),
            ("model.fx_dbt.cc_built", "success", 0.9),
            ("model.fx_dbt.zzz_skip_unrelated", "skipped", 0.0),
            ("test.fx_dbt.check_orders", "fail", 0.2),
        ),
    ),
    # A partial selection: the link between the failure and the skip
    # (`aa_skip`) never ran, so the reconstruction cannot place the two in
    # order and must not claim a cascade it cannot see.
    RunSpec(
        "partial-1",
        "build",
        datetime(2026, 8, 2, 4, 0),
        models_error=1,
        nodes=(
            ("model.fx_dbt.zz_fail", "error", 0.4),
            ("model.fx_dbt.bb_skip_deep", "skipped", 0.0),
        ),
    ),
    # A status word outside every vocabulary in `sim.signals`: the record must
    # relay it, not fold it.
    RunSpec(
        "odd-1",
        "run",
        datetime(2026, 8, 2, 5, 0),
        nodes=(("model.fx_dbt.stg_orders", "partial success", 1.0),),
    ),
)


def make_cascade_project(root: Path, runs: tuple[RunSpec, ...] = CASCADE_RUNS) -> Path:
    """The cascade project above, on disk. Shared by the run-document, export
    and server tests so all three replay the same hand-counted DAG."""
    return make_tycoon_project(
        root,
        models=CASCADE_MODELS,
        sources=CASCADE_SOURCES,
        tests=CASCADE_TESTS,
        runs=runs,
    )


def make_tycoon_project(
    root: Path,
    *,
    models: tuple[ModelSpec, ...] = DEFAULT_MODELS,
    sources: tuple[SourceSpec, ...] = DEFAULT_SOURCES,
    tests: tuple[TestSpec, ...] = DEFAULT_TESTS,
    runs: tuple[RunSpec, ...] | None = None,
    drift_keys: bool = False,
    with_manifest: bool = True,
    with_metadata: bool = True,
    warehouse_value: str = "data/fx.duckdb",
) -> Path:
    """Write the project under `root` and return `root`.

    The warehouse is **tables-only** — every model materialises as a table, no
    views — because that is the case the whole backend exists to fix: view-SQL
    lineage yields zero edges there.
    """
    root.mkdir(parents=True, exist_ok=True)

    drift = ""
    if drift_keys:
        drift = "\nask:\n  reviewer: someone\n  channel: '#data'\n"
    (root / "tycoon.yml").write_text(
        f"""name: fx
version: 0.1.0

database:
  raw: data/raw.duckdb
  warehouse: {warehouse_value}

dbt_project_dir: dbt
sources: {{}}

stack:
  ingestion: dlt
  ingestion_managed: false
  warehouse: duckdb
  transformation: dbt
  transformation_managed: false
  orchestrator: none
  orchestrator_managed: false
{drift}"""
    )

    _write_warehouse(root / "data" / "fx.duckdb", models, sources)
    if with_manifest:
        _write_manifest(root / "dbt" / "target" / "manifest.json", models, sources, tests)
    if with_metadata:
        if runs is None:
            runs = _default_runs(models, tests)
        _write_metadata(root / ".tycoon" / "metadata.duckdb", runs)
    return root


def _write_warehouse(path: Path, models: tuple[ModelSpec, ...], sources: tuple[SourceSpec, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    schemas = {m.schema for m in models} | {s.schema for s in sources if s.database == "fx"}
    for schema in sorted(schemas):
        con.execute(f'create schema if not exists "{schema}"')

    def _create(schema: str, table: str, columns: tuple[tuple[str, str], ...], rows: int) -> None:
        extra = ", ".join(f'cast(null as {ctype}) as "{cname}"' for cname, ctype in columns if cname != "id")
        select = f"id{', ' + extra if extra else ''}"
        con.execute(f'create table "{schema}"."{table}" as select {select} from range({rows}) t(id)')

    for m in models:
        _create(m.schema, m.table_name, m.columns, m.rows)
    for s in sources:
        if s.database == "fx":  # external sources exist only in the manifest
            _create(s.schema, s.name, (("id", "BIGINT"), ("payload", "JSON")), s.rows)
    con.close()


def _write_manifest(
    path: Path,
    models: tuple[ModelSpec, ...],
    sources: tuple[SourceSpec, ...],
    tests: tuple[TestSpec, ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    nodes: dict = {}
    for m in models:
        nodes[m.unique_id] = {
            "unique_id": m.unique_id,
            "resource_type": "model",
            "name": m.name,
            "schema": m.schema,
            "alias": m.table_name,
            "database": "fx",
            "description": m.description,
            "tags": list(m.tags),
            "meta": {"owner": m.owner} if m.owner else {},
            "columns": {name: {"name": name, "description": desc} for name, desc in (m.column_docs or {}).items()},
            "depends_on": {"macros": [], "nodes": list(m.depends_on)},
            "config": {"materialized": m.materialized},
            "raw_code": m.raw_code or "",
        }
    for t in tests:
        nodes[t.unique_id] = {
            "unique_id": t.unique_id,
            "resource_type": "test",
            "name": t.name,
            "column_name": getattr(t, "column", None),
            "schema": "main_dbt_test__audit",
            "alias": t.name,
            "database": "fx",
            "attached_node": t.attached_node,
            "depends_on": {"macros": [], "nodes": list(t.depends_on)},
            "config": {"materialized": "test"},
        }
    manifest = {
        "metadata": {"dbt_schema_version": "https://schemas.getdbt.com/dbt/manifest/v12.json"},
        "nodes": nodes,
        "sources": {
            s.unique_id: {
                "unique_id": s.unique_id,
                "resource_type": "source",
                "schema": s.schema,
                "name": s.name,
                "source_name": s.schema,  # real manifests carry the source block's name
                "identifier": s.name,
                "database": s.database,
            }
            for s in sources
        },
    }
    path.write_text(json.dumps(manifest))


def write_sources_json(root: Path, verdicts: dict[str, tuple[str, str | None]]) -> None:
    """Write dbt's source-freshness artifact: unique_id -> (status, max_loaded_at)."""
    path = root / "dbt" / "target" / "sources.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "results": [
                    {"unique_id": uid, "status": status, "max_loaded_at": loaded}
                    for uid, (status, loaded) in verdicts.items()
                ]
            }
        )
    )


def write_schema_changes(root: Path, changes: dict[str, "datetime"]) -> None:
    """Insert dbt_schema_changes rows: unique_id -> captured_at."""
    con = duckdb.connect(str(root / ".tycoon" / "metadata.duckdb"))
    for unique_id, at in changes.items():
        con.execute(
            "insert into dbt_schema_changes values (?, NULL, 'column_added', ?, 'new_col', NULL, 'VARCHAR', ?)",
            ["inv-drift", unique_id, at],
        )
    con.close()


def _default_runs(models: tuple[ModelSpec, ...], tests: tuple[TestSpec, ...]) -> tuple[RunSpec, ...]:
    model_nodes = tuple((m.unique_id, "success", 1.2) for m in models)
    test_nodes = tuple((t.unique_id, "pass", 0.05) for t in tests)
    return (
        RunSpec("run-1", "run", datetime(2026, 7, 30, 2, 0), nodes=model_nodes),
        RunSpec("run-2", "run", datetime(2026, 8, 1, 2, 0), nodes=model_nodes),
        RunSpec("test-1", "test", datetime(2026, 8, 1, 2, 5), nodes=test_nodes),
    )


def _write_metadata(path: Path, runs: tuple[RunSpec, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    # The real schema, column for column (dogfood, 2026-08-04).
    con.execute(
        """create table dbt_runs (
            invocation_id varchar, command varchar, started_at timestamp,
            elapsed_s double, success boolean, models_ok integer,
            models_error integer, tests_passed integer, tests_failed integer,
            dbt_version varchar, target_name varchar, captured_at timestamp)"""
    )
    con.execute(
        """create table dbt_nodes (
            invocation_id varchar, node_name varchar, resource_type varchar,
            status varchar, execution_time_s double, rows_affected bigint,
            compile_time_s double, message varchar)"""
    )
    con.execute(
        """create table dbt_schema_changes (
            invocation_id varchar, prev_invocation_id varchar, change_type varchar,
            unique_id varchar, column_name varchar, old_value varchar,
            new_value varchar, captured_at timestamp)"""
    )
    con.execute(
        """create table dlt_runs (
            source_schema varchar, load_id varchar, status integer,
            inserted_at timestamp, schema_version_hash varchar, captured_at timestamp)"""
    )
    con.execute(
        """create table dlt_rows_by_table (
            source_schema varchar, table_name varchar, load_id varchar,
            rows_loaded bigint, captured_at timestamp)"""
    )
    for run in runs:
        ok_models = sum(1 for _, s, _ in run.nodes if s == "success")
        ok_tests = sum(1 for _, s, _ in run.nodes if s == "pass")
        con.execute(
            "insert into dbt_runs values (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?)",
            [
                run.invocation_id,
                run.command,
                run.started_at,
                42.0,
                ok_models,
                run.models_error,
                ok_tests,
                run.tests_failed,
                "1.11.0",
                run.target,
                run.started_at,
            ],
        )
        for node_name, status, seconds in run.nodes:
            resource = "test" if node_name.startswith("test.") else "model"
            con.execute(
                "insert into dbt_nodes values (?, ?, ?, ?, ?, NULL, ?, NULL)",
                [run.invocation_id, node_name, resource, status, seconds, 0.01],
            )
    con.close()
