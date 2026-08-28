"""Build `demo-tycoon/` — a synthetic tycoon project rich enough to demo
Phase F, which dogfood is too thin for (its dlt tables are empty and its runs
cluster on one day).

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
- a **semantic model**: `src/tycoon_city/demo/semantic.yml` is copied to
  `demo-tycoon/semantic.yml`, where the loader finds it by the project-root
  convention -> declared joins, one of them on a pair that also has lineage,
  one composite, plus ai_context on two objects

Usage:
    uv run python scripts/make_demo_tycoon.py [out_dir]
    uv run tycoon-city demo-tycoon/
"""

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from tests.fixtures.tycoon_factory import (  # noqa: E402
    ModelSpec,
    RunSpec,
    SourceSpec,
    TestSpec,
    make_tycoon_project,
    write_sources_json,
)

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


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "demo-tycoon"
    if out.exists():
        import shutil

        shutil.rmtree(out)  # regenerate from scratch: the factory never overwrites
    now = datetime.now(UTC).replace(tzinfo=None)

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

    runs = scheduled + (
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

    root = make_tycoon_project(out, models=MODELS, sources=SOURCES, tests=TESTS, runs=runs)

    # dbt's own source-freshness verdicts: orders loaded an hour ago (pass),
    # customers stuck since yesterday (error) -- the late-source cone.
    # Schema drift two days ago on stg_customers: the construction crane.
    from tests.fixtures.tycoon_factory import write_schema_changes

    write_schema_changes(root, {"model.fx_dbt.stg_customers": ago(days=2)})

    write_sources_json(
        root,
        {
            "source.fx_dbt.raw.orders": ("pass", ago(hours=1).isoformat()),
            "source.fx_dbt.raw.customers": ("error", ago(hours=26).isoformat()),
        },
    )

    # A dlt load an hour ago feeds the raw schema's freshness.
    import duckdb

    con = duckdb.connect(str(root / ".tycoon" / "metadata.duckdb"))
    con.execute(
        "insert into dlt_runs values ('raw', 'load-9', 0, ?, 'hash', ?)",
        [ago(hours=1), now],
    )
    con.execute(
        "insert into dlt_rows_by_table values ('raw', 'orders', 'load-9', 4200, ?)",
        [now],
    )
    con.close()

    # The hand-written OSI semantic model. It lives in `scripts/` because
    # `demo-tycoon/` is generated (and gitignored) and this rmtree would take
    # it with the rest; copying keeps the file tracked and reviewable.
    import shutil as _shutil

    _shutil.copyfile(REPO / "src" / "tycoon_city" / "demo" / "semantic.yml", root / "semantic.yml")

    # Add requests.json
    (root / "requests.json").write_text(
        json.dumps(
            [
                {
                    "id": "req-1",
                    "priority": "CRITICAL",
                    "type": "ORDER",
                    "created_at": ago(hours=1).isoformat(),
                },
                {
                    "id": "req-2",
                    "priority": "HIGH",
                    "type": "CUSTOMER",
                    "created_at": ago(hours=2).isoformat(),
                },
                {
                    "id": "req-3",
                    "priority": "LOW",
                    "type": "ORDER",
                    "created_at": ago(hours=3).isoformat(),
                },
            ],
            indent=2,
        )
    )

    print(f"demo tycoon project at {root}")
    print(f"  serve it:  uv run tycoon-city {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
