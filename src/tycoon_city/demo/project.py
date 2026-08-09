"""The demo catalog, generated fresh — the city `tycoon-city demo` serves.

**Why this is generated and not baked.** Almost every fact this project exists
to show is a TIME: a pipeline that ran twenty minutes ago, a mart nobody has
rebuilt in three weeks, a source stuck since yesterday, a schema that drifted on
Tuesday, a failure cascade two hours back. Freeze those into a file in the
wheel and the demo decays — a month after a release the "fresh pipeline" reads
a month old, every building is stale, the weather is uniformly bad and the city
that is supposed to show the fresh/stale contrast shows one flat colour. That
is a stale render shipped as a feature, which is the one thing this repo is
most careful about everywhere else.

So the project is written at start-up, with every timestamp measured backwards
from *now*. It costs a couple of seconds and a temp directory (see
`tycoon_city.demo.materialise`), needs no checkout, no `scripts/`, and no write
access anywhere but `$TMPDIR`.

The named scenarios, all visible at once:
- a **fresh pipeline**: staging built minutes ago from a dlt load an hour old
- a **stale mart**: `mart.mart__forgotten` last built 21 days ago -> heavy decay
- a **failing test** on `mart.mart__revenue` -> red condition marker
- a **warning test** on `staging.stg_orders` -> amber marker
- a **build error** on `mart.mart__broken` -> red tint
- an object with **no history at all** (`scratch.experiment`) -> full colour,
  the unknown-is-not-stale case standing next to the stale one
- a **failure cascade**: the `fail-fast` run errors on `staging.stg_customers`
  and dbt reports four skips behind it -> `runs/<id>.json` carries a
  `failure_cascade` with three members, and the two skips it must NOT claim
  (see the run's own comment for the hand-count)
- a **semantic model**: `semantic.yml` ships beside this module and is copied
  into the project root, where the loader finds it by convention -> declared
  joins, one of them on a pair that also has lineage, one composite, plus
  ai_context on two objects
"""

import shutil
from datetime import UTC, datetime, timedelta
from importlib.resources import files
from pathlib import Path

import duckdb

from .factory import (
    ModelSpec,
    RunSpec,
    SourceSpec,
    TestSpec,
    make_tycoon_project,
    write_schema_changes,
    write_sources_json,
)

# The hand-written OSI semantic model, shipped as package data beside this
# module. `src/tycoon_city/demo/semantic.yml` is the same file for the in-repo
# generator; `tests/test_demo_project.py` asserts the two stay byte-identical,
# because a silently diverging copy is worse than either.
SEMANTIC_FILE = "semantic.yml"

MODELS = (
    ModelSpec(
        "staging",
        "stg_orders",
        depends_on=("source.fx_dbt.raw.orders",),
        rows=50_000,
        description="One row per order, deduplicated and typed from the raw feed.",
        tags=("hourly", "core"),
        owner="data-eng",
        raw_code=(
            "{{ config(materialized='table') }}\n"
            "select id, cast(payload->>'name' as varchar) as name,\n"
            "  cast(payload->>'amount' as double) as amount,\n"
            "  current_timestamp as created_at\n"
            "from {{ source('raw', 'orders') }}"
        ),
    ),
    ModelSpec(
        "staging",
        "stg_customers",
        depends_on=("source.fx_dbt.raw.customers",),
        rows=1_200,
        description="Current customer dimension staging.",
        tags=("hourly",),
        owner="data-eng",
        raw_code=(
            "{{ config(materialized='table') }}\n"
            "select id, cast(payload->>'name' as varchar) as name,\n"
            "  cast(null as double) as amount, current_timestamp as created_at\n"
            "from {{ source('raw', 'customers') }}"
        ),
    ),
    ModelSpec(
        "mart",
        "mart__revenue",
        depends_on=("model.fx_dbt.stg_orders", "model.fx_dbt.stg_customers"),
        rows=8_000,
        description="Recognised revenue by day and customer. Feeds the CEO dashboard.",
        tags=("daily", "finance"),
        owner="stephen",
        columns=(
            ("id", "BIGINT"),
            ("customer_id", "BIGINT"),
            ("amount", "DECIMAL(12,2)"),
            ("recognised_on", "DATE"),
            ("channel", "VARCHAR"),
            ("metadata", "JSON"),
        ),
        column_docs={
            "amount": "Recognised amount in USD.",
            "recognised_on": "Revenue recognition date, not invoice date.",
        },
        raw_code=(
            "{{ config(materialized='table') }}\n"
            "select o.id, c.id as customer_id,\n"
            "  cast(o.amount as decimal(12,2)) as amount,\n"
            "  cast(o.created_at as date) as recognised_on,\n"
            "  o.name as channel, cast(null as json) as metadata\n"
            "from {{ ref('stg_orders') }} o\n"
            "join {{ ref('stg_customers') }} c on c.id = o.id"
        ),
    ),
    ModelSpec(
        "mart",
        "mart__forgotten",
        depends_on=("model.fx_dbt.stg_orders",),
        rows=900,
        description="A legacy rollup nobody has rebuilt in weeks.",
        tags=("deprecated",),
        # Real projects always have a model column lineage cannot trace; the
        # jinja loop keeps the "no column lineage for N models" note demoable.
        raw_code="{% for s in var('schemas') %} select 1 {% endfor %}",
    ),
    ModelSpec(
        "mart",
        "mart__broken",
        depends_on=("model.fx_dbt.stg_customers",),
        rows=0,
        raw_code="select id, name, amount, created_at from {{ ref('stg_customers') }}",
    ),
    # Two dims cut from the SAME source as mart__broken: with it they form a
    # sibling BLOCK — three touching buildings served by one delivery trunk.
    ModelSpec(
        "mart",
        "dim__customers",
        depends_on=("model.fx_dbt.stg_customers",),
        rows=1_200,
        description="Customer dimension.",
        owner="data-eng",
        raw_code="select id, name, amount, created_at from {{ ref('stg_customers') }}",
    ),
    ModelSpec(
        "mart",
        "dim__customer_status",
        depends_on=("model.fx_dbt.stg_customers",),
        rows=400,
        description="Status rollup dimension.",
        owner="data-eng",
        raw_code="select id, name, amount, created_at from {{ ref('stg_customers') }}",
    ),
    # No dbt node, no test, no history: the unknown case.
    ModelSpec("scratch", "experiment", rows=42),
)

SOURCES = (
    SourceSpec("raw", "orders", rows=60_000),
    SourceSpec("raw", "customers", rows=1_500),
)

TESTS = (
    TestSpec("not_null_revenue_amount", attached_node="model.fx_dbt.mart__revenue", column="amount"),
    TestSpec("accepted_values_order_status", attached_node="model.fx_dbt.stg_orders", column="status"),
    # A passing test: the green roof marker, distinguishing tested-and-passing
    # from never-tested.
    TestSpec("unique_stg_customers_id", attached_node="model.fx_dbt.stg_customers", column="id"),
)


def _runs(now: datetime) -> tuple[RunSpec, ...]:
    """Every run, dated backwards from `now`. The offsets ARE the demo."""

    def ago(**kwargs) -> datetime:
        return now - timedelta(**kwargs)

    # A week of scheduled history: stg_orders every 6 hours (the busy street),
    # stg_customers and mart__revenue daily. This is what feeds the road-load
    # overlay — cadence x mean cost = warehouse-seconds/day per street.
    scheduled = tuple(
        RunSpec(
            f"sched-{i}",
            "run",
            ago(hours=6 * i + 3),
            nodes=(
                ("model.fx_dbt.stg_orders", "success", 2.1),
                *(
                    (
                        ("model.fx_dbt.stg_customers", "success", 0.8),
                        ("model.fx_dbt.mart__revenue", "success", 14.5),
                    )
                    if i % 4 == 0
                    else ()
                ),
            ),
        )
        for i in range(28)  # 7 days of 6-hourly runs
    )

    return scheduled + (
        # Three weeks ago: the last time mart__forgotten was touched.
        RunSpec(
            "old-run",
            "run",
            ago(days=21),
            nodes=(("model.fx_dbt.mart__forgotten", "success", 3.2),),
        ),
        # Two hours ago: the FAILURE CASCADE, the run replay's headline. A
        # `dbt build --fail-fast`: staging.stg_customers errors, dbt abandons
        # the invocation and reports everything it had not finished as
        # skipped. Hand-counted, so the demo exercises all three of the
        # cascade's tests (docs/run-json-v1.md) rather than "everything
        # dimmed":
        #
        #   IN the cascade (skipped AND downstream of the failure AND later):
        #     mart.mart__broken, mart.dim__customer_status, mart.mart__revenue
        #   OUT, because it is NOT downstream: staging.stg_orders -- skipped by
        #     the same fail-fast abort, and it sorts AFTER the failure on
        #     object_key, so only the reachability test can exclude it. That is
        #     deliberate: a fixture excluded by alphabetical luck proves
        #     nothing.
        #   OUT, because dbt BUILT it: mart.dim__customers is downstream of the
        #     failure and dbt still reported success, so the walk must leave it
        #     lit. The record relays dbt's verdict; it never infers a blast
        #     radius.
        #
        # It sits inside the newest-20 replay window on purpose (third in the
        # picker), and every node in it is rebuilt by `fresh-run` twenty
        # minutes later, so the city's steady state is unchanged -- the
        # cascade lives in the run document, where replay reads it.
        RunSpec(
            "fail-fast",
            "build",
            ago(hours=2),
            models_error=1,
            nodes=(
                ("model.fx_dbt.stg_customers", "error", 0.6),
                ("model.fx_dbt.stg_orders", "skipped", 0.0),
                ("model.fx_dbt.mart__revenue", "skipped", 0.0),
                ("model.fx_dbt.mart__broken", "skipped", 0.0),
                ("model.fx_dbt.dim__customer_status", "skipped", 0.0),
                ("model.fx_dbt.dim__customers", "success", 1.1),
            ),
        ),
        # Minutes ago: the fresh pipeline, with one build error. It rebuilds
        # the two dims as well, so the fail-fast run above leaves no skipped
        # building behind in the city's current state.
        RunSpec(
            "fresh-run",
            "run",
            ago(minutes=20),
            models_error=1,
            nodes=(
                ("model.fx_dbt.stg_orders", "success", 2.1),
                ("model.fx_dbt.stg_customers", "success", 0.8),
                ("model.fx_dbt.mart__revenue", "success", 4.5),
                ("model.fx_dbt.dim__customers", "success", 1.0),
                ("model.fx_dbt.dim__customer_status", "success", 0.5),
                ("model.fx_dbt.mart__broken", "error", 0.3),
            ),
        ),
        # Just now: tests -- one failing, one warning.
        RunSpec(
            "fresh-tests",
            "test",
            ago(minutes=5),
            tests_failed=1,
            nodes=(
                ("test.fx_dbt.not_null_revenue_amount", "fail", 0.4),
                ("test.fx_dbt.accepted_values_order_status", "warn", 0.2),
                ("test.fx_dbt.unique_stg_customers_id", "pass", 0.1),
            ),
        ),
    )


def semantic_source() -> Path:
    """The packaged OSI model. Anchored on the package, not on `__file__`:
    the same reason `theme_dir` is (see `tycoon_city.theme_data`)."""
    return Path(str(files("tycoon_city.demo"))) / SEMANTIC_FILE


def build_demo_project(root: Path, now: datetime | None = None) -> Path:
    """Write the demo tycoon project under `root` and return it.

    `now` is injectable so a test can pin the clock; the default is the real
    one, which is the entire point of generating rather than baking.
    """
    # Naive UTC, matching what the metadata database and dbt artifacts store:
    # the loader compares these against `datetime.now()` without a zone.
    stamp = (now or datetime.now(UTC)).replace(tzinfo=None)

    def ago(**kwargs) -> datetime:
        return stamp - timedelta(**kwargs)

    project = make_tycoon_project(root, models=MODELS, sources=SOURCES, tests=TESTS, runs=_runs(stamp))

    # Schema drift two days ago on stg_customers: the construction crane.
    write_schema_changes(project, {"model.fx_dbt.stg_customers": ago(days=2)})

    # dbt's own source-freshness verdicts: orders loaded an hour ago (pass),
    # customers stuck since yesterday (error) -- the late-source cone.
    write_sources_json(
        project,
        {
            "source.fx_dbt.raw.orders": ("pass", ago(hours=1).isoformat()),
            "source.fx_dbt.raw.customers": ("error", ago(hours=26).isoformat()),
        },
    )

    # A dlt load an hour ago feeds the raw schema's freshness.
    con = duckdb.connect(str(project / ".tycoon" / "metadata.duckdb"))
    con.execute(
        "insert into dlt_runs values ('raw', 'load-9', 0, ?, 'hash', ?)",
        [ago(hours=1), stamp],
    )
    con.execute(
        "insert into dlt_rows_by_table values ('raw', 'orders', 'load-9', 4200, ?)",
        [stamp],
    )
    con.close()

    shutil.copyfile(semantic_source(), project / SEMANTIC_FILE)
    return project
