"""Phase F: the temporal signals and the rule that must survive every review —
**unknown never renders as stale.**"""

from datetime import datetime

import pytest

from tests.fixtures.tycoon_factory import RunSpec, make_tycoon_project
from tycoon_city.catalog.loader import load_context
from tycoon_city.sim.channels import (
    CHANNEL_KIND,
    DEFAULT_BINDINGS,
    VisualChannel,
    apply_signals,
    as_naive_utc,
)
from tycoon_city.sim.generator import generate_city
from tycoon_city.sim.signals import (
    BUILD_STATUS_VOCABULARY,
    REGISTRY,
    TEST_STATUS_VOCABULARY,
)

NOW = datetime(2026, 8, 4, 12, 0, 0)


def _city(ctx):
    city = generate_city(ctx, [])
    apply_signals(city, ctx, DEFAULT_BINDINGS, now=NOW)
    return city


def test_THE_RULE_unknown_never_renders_as_stale(tmp_path):
    """A catalog with no run history at all: every temporal field must be None
    (unknown), never zero, never an ancient age, never a failure status."""
    root = make_tycoon_project(tmp_path / "fx", with_metadata=False)
    city = _city(load_context(root))

    for lot in city.lots.values():
        assert lot.last_build_age_s is None
        assert lot.build_status is None
        assert lot.test_status is None


def test_covered_objects_get_ages_and_statuses(tmp_path):
    root = make_tycoon_project(
        tmp_path / "fx",
        runs=(
            RunSpec(
                "run-1",
                "run",
                datetime(2026, 8, 4, 10, 0),  # two hours before NOW
                nodes=(("model.fx_dbt.stg_orders", "success", 1.0),),
            ),
            RunSpec(
                "test-1",
                "test",
                datetime(2026, 8, 4, 11, 0),
                tests_failed=1,
                nodes=(("test.fx_dbt.not_null_stg_orders_id", "fail", 0.1),),
            ),
        ),
    )
    city = _city(load_context(root))

    stg = city.lots["staging.stg_orders"]
    assert stg.last_build_age_s == pytest.approx(2 * 3600)
    assert stg.build_status == "success"
    assert stg.test_status == "fail"  # the attached test failed

    # An object the history never touched stays fully unknown.
    other = city.lots["marts.fct_revenue"]
    assert other.last_build_age_s is None
    assert other.build_status is None
    assert other.test_status is None


def test_any_failing_test_fails_the_object(tmp_path):
    root = make_tycoon_project(
        tmp_path / "fx",
        runs=(
            RunSpec(
                "test-1",
                "test",
                datetime(2026, 8, 4, 11, 0),
                nodes=(
                    ("test.fx_dbt.not_null_stg_orders_id", "pass", 0.1),
                    ("test.fx_dbt.assert_revenue_positive", "fail", 0.1),
                ),
            ),
        ),
    )
    ctx = load_context(root)
    city = _city(ctx)

    # assert_revenue_positive attaches (via depends_on fallback) to the
    # alias-overridden model, whose table is marts.fct_revenue.
    assert city.lots["marts.fct_revenue"].test_status == "fail"
    assert city.lots["staging.stg_orders"].test_status == "pass"


def test_status_vocabularies_are_contained(tmp_path):
    """Whatever words the metadata holds, the signals emit only their frozen
    vocabulary — unrecognised build words map to 'partial', unrecognised test
    words to 'fail' (for a test result, an unknown word is not reassurance)."""
    root = make_tycoon_project(
        tmp_path / "fx",
        runs=(
            RunSpec(
                "weird",
                "run",
                datetime(2026, 8, 4, 11, 0),
                nodes=(
                    ("model.fx_dbt.stg_orders", "reused", 0.1),  # not in vocab
                    ("test.fx_dbt.not_null_stg_orders_id", "wat", 0.1),
                ),
            ),
        ),
    )
    ctx = load_context(root)

    builds = REGISTRY["build_status"].compute(ctx)
    tests = REGISTRY["test_status"].compute(ctx)

    assert set(builds.values()) <= BUILD_STATUS_VOCABULARY
    assert set(tests.values()) <= TEST_STATUS_VOCABULARY
    assert builds["staging.stg_orders"] == "partial"
    assert tests["staging.stg_orders"] == "fail"


def test_binding_kind_mismatch_fails_fast(tmp_path):
    root = make_tycoon_project(tmp_path / "fx")
    ctx = load_context(root)
    city = generate_city(ctx, [])
    bad = {**DEFAULT_BINDINGS, VisualChannel.DECAY: "row_count"}  # scalar into timestamp

    with pytest.raises(ValueError, match="DECAY consumes timestamp"):
        apply_signals(city, ctx, bad, now=NOW)


def test_every_default_binding_matches_its_channel_kind():
    for channel, name in DEFAULT_BINDINGS.items():
        assert REGISTRY[name].kind == CHANNEL_KIND[channel]


def test_timestamps_normalise_through_one_helper():
    from datetime import UTC, timedelta, timezone

    naive = datetime(2026, 8, 4, 12, 0)
    assert as_naive_utc(naive) == naive  # naive is treated as already-UTC
    aware = datetime(2026, 8, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    assert as_naive_utc(aware) == datetime(2026, 8, 4, 12, 0)
    utc = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    assert as_naive_utc(utc) == naive


def test_idempotent_for_a_fixed_now(tmp_path):
    root = make_tycoon_project(tmp_path / "fx")
    ctx = load_context(root)
    city = generate_city(ctx, [])

    apply_signals(city, ctx, DEFAULT_BINDINGS, now=NOW)
    first = {k: (v.last_build_age_s, v.build_status, v.test_status) for k, v in city.lots.items()}
    apply_signals(city, ctx, DEFAULT_BINDINGS, now=NOW)
    second = {k: (v.last_build_age_s, v.build_status, v.test_status) for k, v in city.lots.items()}

    assert first == second


def test_raw_tables_get_freshness_from_dlt_loads(tmp_path):
    import duckdb

    root = make_tycoon_project(tmp_path / "fx")
    con = duckdb.connect(str(root / ".tycoon" / "metadata.duckdb"))
    con.execute("insert into dlt_runs values ('raw', 'load-1', 0, '2026-08-04 09:00:00', 'h', now())")
    con.close()

    city = _city(load_context(root))

    # raw.orders is a source table no dbt node covers; its schema's dlt load
    # supplies the freshness instead.
    assert city.lots["raw.orders"].last_build_age_s == pytest.approx(3 * 3600)
    assert city.lots["raw.orders"].build_status is None


def test_dbt_source_freshness_verdict_reaches_the_lot(tmp_path):
    """dbt's own SLA judgment (sources.json) lands as freshness_status, and its
    max_loaded_at beats the schema-level dlt timestamp for DECAY."""
    from tests.fixtures.tycoon_factory import write_sources_json

    root = make_tycoon_project(tmp_path / "fx")
    write_sources_json(
        root,
        {
            "source.fx_dbt.raw.orders": ("error", "2026-08-04T06:00:00"),
        },
    )
    city = _city(load_context(root))

    orders = city.lots["raw.orders"]
    assert orders.freshness_status == "error"
    assert orders.last_build_age_s == pytest.approx(6 * 3600)  # NOW is 12:00
    # Objects without a verdict stay unknown -- THE RULE holds for freshness.
    assert city.lots["marts.fct_revenue"].freshness_status is None


def test_missing_sources_json_is_noted_when_sources_exist(tmp_path):
    root = make_tycoon_project(tmp_path / "fx")

    ctx = load_context(root)

    assert any("source freshness" in note for note in ctx.notes)
    assert ctx.source_freshness_by_key == {}


def test_runtime_error_verdict_folds_to_error(tmp_path):
    from tests.fixtures.tycoon_factory import write_sources_json

    root = make_tycoon_project(tmp_path / "fx")
    write_sources_json(root, {"source.fx_dbt.raw.orders": ("runtime error", None)})

    city = _city(load_context(root))

    assert city.lots["raw.orders"].freshness_status == "error"


def test_schema_drift_reaches_the_lot_and_absence_stays_none(tmp_path):
    from tests.fixtures.tycoon_factory import write_schema_changes

    root = make_tycoon_project(tmp_path / "fx")
    write_schema_changes(root, {"model.fx_dbt.stg_orders": datetime(2026, 8, 4, 6, 0)})

    city = _city(load_context(root))

    assert city.lots["staging.stg_orders"].schema_drift_age_s == pytest.approx(6 * 3600)
    assert city.lots["marts.fct_revenue"].schema_drift_age_s is None
