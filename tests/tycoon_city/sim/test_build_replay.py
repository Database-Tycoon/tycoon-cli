"""The replay schedule: measured durations, reconstructed ordering, named
refusals."""

from datetime import datetime

from tests.fixtures.tycoon_factory import RunSpec, make_tycoon_project
from tycoon_city.catalog.loader import load_context
from tycoon_city.sim.build_replay import (
    RECONSTRUCTED_NOTE,
    ReplayPlan,
    ReplayRefusal,
    plan_replay,
)


def test_downstream_never_starts_before_upstream_finishes(tmp_path):
    root = make_tycoon_project(
        tmp_path / "fx",
        runs=(
            RunSpec(
                "r1",
                "run",
                datetime(2026, 8, 1),
                nodes=(
                    ("model.fx_dbt.stg_orders", "success", 2.0),
                    ("model.fx_dbt.fct_revenue_model", "success", 4.0),
                    ("model.fx_dbt.stg_daily", "success", 1.0),
                    ("model.fx_dbt.mart_daily", "success", 1.0),
                ),
            ),
        ),
    )
    plan = plan_replay(load_context(root))

    assert isinstance(plan, ReplayPlan)
    assert plan.note == RECONSTRUCTED_NOTE
    by_key = {s.object_key: s for s in plan.steps}
    stg = by_key["staging.stg_orders"]
    fct = by_key["marts.fct_revenue"]
    daily = by_key["marts.daily"]
    # The schedule, not the sort order: downstream starts at upstream's finish.
    assert fct.start >= stg.start + stg.duration
    assert daily.start >= stg.start + stg.duration
    # And the span is the scaled target, tolerating rounding.
    assert max(s.start + s.duration for s in plan.steps) <= plan.span_ticks + 1


def test_no_history_is_a_named_refusal(tmp_path):
    root = make_tycoon_project(tmp_path / "fx", with_metadata=False)

    plan = plan_replay(load_context(root))

    assert isinstance(plan, ReplayRefusal)
    assert plan.reason == "no run history to replay"


def test_history_from_another_catalog_is_refused(tmp_path):
    """Model results whose unique_ids mostly do not map onto this catalog
    (foreign manifest, wrong target): animating them would be a lie."""
    root = make_tycoon_project(
        tmp_path / "fx",
        runs=(
            RunSpec(
                "alien",
                "run",
                datetime(2026, 8, 1),
                nodes=(
                    ("model.other.a", "success", 1.0),
                    ("model.other.b", "success", 1.0),
                    ("model.other.c", "success", 1.0),
                    ("model.fx_dbt.stg_orders", "success", 1.0),
                ),
            ),
        ),
    )
    plan = plan_replay(load_context(root))

    assert isinstance(plan, ReplayRefusal)
    assert plan.reason == "run history does not match this catalog"


def test_replay_is_deterministic(tmp_path):
    root = make_tycoon_project(tmp_path / "fx")

    ctx = load_context(root)
    assert plan_replay(ctx) == plan_replay(ctx)
