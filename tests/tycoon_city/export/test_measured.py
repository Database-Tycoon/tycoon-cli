"""The three MEASURED blocks — budget, usage, weather — and their lies.

Each block has one specific way to say something false, and each of those gets
a test that fails on the WRONG axis, not just a non-empty one:

* budget: a $0 bill that came from a missing measurement, indistinguishable
  from local DuckDB's genuine $0.
* usage: null rendered as "unused".
* weather: `clear` cells emitted when nothing has been judged — a lie the
  loader already names ("no source freshness snapshot"), and the one this file
  spends the most assertions on.

The weather tests hand-count WHICH district gets fog and assert the
preconditions that make the count meaningful (the fixture really does have a
late source; it really does feed a schema two hops away). "cells is non-empty"
would pass on the wrong districts, which is this repo's dominant defect.
"""

from datetime import datetime

import pytest

from tests.fixtures.tycoon_factory import (
    ModelSpec,
    RunSpec,
    SourceSpec,
    make_tycoon_project,
    write_sources_json,
)
from tycoon_city.catalog.loader import load_context
from tycoon_city.export.city_json import city_document
from tycoon_city.export.measured import NO_VERDICTS_NOTE, _budget, _usage_by_key, _weather
from tycoon_city.pricing import DEFAULT_PRICES, PriceBook
from tycoon_city.sim.channels import DEFAULT_BINDINGS, apply_signals
from tycoon_city.sim.generator import generate_city
from tycoon_city.theme_data import load_theme_data, theme_dir


@pytest.fixture
def theme():
    return load_theme_data(theme_dir("default"))


def _document(ctx, theme, pricing=None):
    city = generate_city(ctx, theme.style_rules)
    apply_signals(city, ctx, DEFAULT_BINDINGS, now=datetime(2026, 8, 6, 12, 0))
    return city_document(ctx, city, theme, pricing)


# ---------------------------------------------------------------------------
# WEATHER — fog covers the districts a late source FEEDS
# ---------------------------------------------------------------------------

# raw.late is the late one. It feeds staging.stg_late (1 hop), which feeds
# mart.mart_late (2 hops). raw.ontime is judged and passing. island.orphan has
# no lineage at all, so no judged source reaches it and it must get NO cell.
_WEATHER_SOURCES = (SourceSpec("raw", "late"), SourceSpec("raw", "ontime"))
_WEATHER_MODELS = (
    ModelSpec("staging", "stg_late", depends_on=("source.fx_dbt.raw.late",)),
    ModelSpec("staging", "stg_ontime", depends_on=("source.fx_dbt.raw.ontime",)),
    ModelSpec("mart", "mart_late", depends_on=("model.fx_dbt.stg_late",)),
    ModelSpec("island", "orphan"),
)


def _weather_project(tmp_path, verdicts):
    root = make_tycoon_project(tmp_path / "fx", models=_WEATHER_MODELS, sources=_WEATHER_SOURCES, tests=())
    if verdicts:
        write_sources_json(root, verdicts)
    return load_context(root)


def test_fog_lands_on_the_districts_the_late_source_feeds_not_its_own(tmp_path):
    """The whole point of the walk, asserted per district by name.

    The preconditions come first on purpose: without them "staging is fogged"
    could pass on a fixture where nothing is late and every district is fogged
    by a bug.
    """
    ctx = _weather_project(
        tmp_path,
        {
            "source.fx_dbt.raw.late": ("error", "2026-08-04T00:00:00"),
            "source.fx_dbt.raw.ontime": ("pass", "2026-08-06T11:00:00"),
        },
    )

    # Precondition 1: the fixture really has one late source and one fine one.
    assert ctx.source_freshness_by_key["raw.late"].status == "error"
    assert ctx.source_freshness_by_key["raw.ontime"].status == "pass"
    # Precondition 2: it really feeds a district two hops downstream.
    pairs = {(e.src, e.dst) for e in ctx.edges}
    assert ("raw.late", "staging.stg_late") in pairs
    assert ("staging.stg_late", "mart.mart_late") in pairs
    # Precondition 3: there really is a district nothing judged can reach.
    assert {obj.schema for obj in ctx.objects} == {"raw", "staging", "mart", "island"}

    weather = _weather(ctx)
    by_schema = {cell["schema"]: cell for cell in weather["cells"]}

    # Hand-counted from the fixture above, district by district.
    assert by_schema["staging"] == {
        "schema": "staging",
        "condition": "fog",
        "worst_source": "raw.late",
        "verdict": "error",
        "hops": 1,
    }
    assert by_schema["mart"] == {
        "schema": "mart",
        "condition": "fog",
        "worst_source": "raw.late",
        "verdict": "error",
        "hops": 2,
    }
    # THE rule: the late source does not rain on its own district. `raw` holds
    # raw.late itself, and it is CLEAR.
    assert by_schema["raw"]["condition"] == "clear"
    assert by_schema["raw"]["worst_source"] is None
    # Partial coverage: no judged source reaches `island`, so it gets no cell
    # at all rather than a comforting `clear`.
    assert "island" not in by_schema
    assert "1 district has no judged source upstream" in weather["note"]


def test_no_verdicts_emits_no_cells_even_though_sources_exist(tmp_path):
    """THE honesty rule. Sources exist, `dbt source freshness` never ran, and
    the loader says so — emitting four `clear` cells here would render
    clear-because-unknown as clear-because-fine."""
    ctx = _weather_project(tmp_path, verdicts=None)

    # Precondition: this is the state the loader names, not a source-free
    # catalog where all-clear would at least be vacuous.
    assert "no source freshness snapshot (run `dbt source freshness`)" in ctx.notes
    assert ctx.source_freshness_by_key == {}
    assert len({obj.schema for obj in ctx.objects}) == 4

    weather = _weather(ctx)
    assert weather["cells"] == []
    assert weather["note"] == NO_VERDICTS_NOTE


def test_cells_are_sorted_by_schema_and_cover_every_reachable_district(tmp_path):
    ctx = _weather_project(
        tmp_path,
        {
            "source.fx_dbt.raw.late": ("error", "2026-08-04T00:00:00"),
            "source.fx_dbt.raw.ontime": ("pass", "2026-08-06T11:00:00"),
        },
    )
    schemas = [cell["schema"] for cell in _weather(ctx)["cells"]]
    assert schemas == sorted(schemas)
    assert schemas == ["mart", "raw", "staging"]


# A warn-only branch and an error-only branch that meet downstream: the
# precedence rule needs a district reached by both.
_PRECEDENCE_SOURCES = (SourceSpec("raw", "warned"), SourceSpec("raw", "broken"))
_PRECEDENCE_MODELS = (
    ModelSpec("amber", "a", depends_on=("source.fx_dbt.raw.warned",)),
    ModelSpec("grey", "g", depends_on=("source.fx_dbt.raw.broken",)),
    ModelSpec("both", "b", depends_on=("model.fx_dbt.a", "model.fx_dbt.g")),
)


def test_error_beats_warn_where_two_late_sources_meet(tmp_path):
    root = make_tycoon_project(tmp_path / "fx", models=_PRECEDENCE_MODELS, sources=_PRECEDENCE_SOURCES, tests=())
    write_sources_json(
        root,
        {
            "source.fx_dbt.raw.warned": ("warn", "2026-08-05T00:00:00"),
            "source.fx_dbt.raw.broken": ("error", "2026-08-01T00:00:00"),
        },
    )
    ctx = load_context(root)

    # Precondition: `both` really is downstream of BOTH branches, or the
    # precedence rule never gets a chance to fire.
    pairs = {(e.src, e.dst) for e in ctx.edges}
    assert ("amber.a", "both.b") in pairs
    assert ("grey.g", "both.b") in pairs

    by_schema = {cell["schema"]: cell for cell in _weather(ctx)["cells"]}
    # A warn alone is overcast, not fog: the two verdicts must stay distinct.
    assert by_schema["amber"]["condition"] == "overcast"
    assert by_schema["amber"]["verdict"] == "warn"
    assert by_schema["grey"]["condition"] == "fog"
    # Where they meet, the worse one wins and names itself.
    assert by_schema["both"]["condition"] == "fog"
    assert by_schema["both"]["worst_source"] == "raw.broken"
    assert by_schema["both"]["hops"] == 2


# ---------------------------------------------------------------------------
# USAGE — run appearances, and the null that is not "unused"
# ---------------------------------------------------------------------------

_USAGE_MODELS = (
    ModelSpec("staging", "busy", depends_on=("source.fx_dbt.raw.orders",)),
    ModelSpec("staging", "once", depends_on=("source.fx_dbt.raw.orders",)),
    ModelSpec("staging", "never", depends_on=("source.fx_dbt.raw.orders",)),
)


def _usage_project(tmp_path, runs):
    root = make_tycoon_project(
        tmp_path / "fx",
        models=_USAGE_MODELS,
        sources=(SourceSpec("raw", "orders"),),
        tests=(),
        runs=runs,
    )
    return load_context(root)


def test_usage_null_means_unknown_and_stands_beside_a_measured_neighbour(tmp_path):
    """`staging.never` was never built; `staging.busy` was built twice. Both
    are on the map. A test that only checked "never is null" would pass on an
    emitter that emitted null for everything."""
    ctx = _usage_project(
        tmp_path,
        runs=(
            RunSpec(
                "r1",
                "run",
                datetime(2026, 8, 1, 0, 0),
                nodes=(("model.fx_dbt.busy", "success", 2.0),),
            ),
            RunSpec(
                "r2",
                "run",
                datetime(2026, 8, 3, 0, 0),
                nodes=(("model.fx_dbt.busy", "success", 4.0),),
            ),
        ),
    )
    usage = _usage_by_key(ctx)

    assert usage["staging.busy"] == {
        "source": "runs",
        "runs_seen": 2,
        "window_days": 2.0,
        "rate_per_day": 0.5,
    }
    # Unknown, not zero: `never` is absent from the map entirely, which the
    # emitter turns into a null `usage` — and null must not render as unused.
    assert "staging.never" not in usage
    assert "staging.once" not in usage


def test_one_run_reports_itself_but_refuses_a_rate(tmp_path):
    """One appearance is a fact worth stating; a cadence from one data point
    is not. `rate_per_day` is null, and `runs_seen` still says 1."""
    ctx = _usage_project(
        tmp_path,
        runs=(
            RunSpec(
                "r1",
                "run",
                datetime(2026, 8, 1, 0, 0),
                nodes=(("model.fx_dbt.once", "success", 1.0),),
            ),
        ),
    )
    entry = _usage_by_key(ctx)["staging.once"]
    assert entry["runs_seen"] == 1
    assert entry["window_days"] == 0.0
    assert entry["rate_per_day"] is None


def test_a_backfill_burst_is_floored_at_one_hour(tmp_path):
    """Three builds six minutes apart. The real span is 0.008 days, so an
    unfloored rate would claim ~240 builds a day. The floor says 48 — the same
    floor the road-load overlay applies, because it is the same function."""
    ctx = _usage_project(
        tmp_path,
        runs=tuple(
            RunSpec(
                f"r{i}",
                "run",
                datetime(2026, 8, 1, 0, 6 * i),
                nodes=(("model.fx_dbt.busy", "success", 1.0),),
            )
            for i in range(3)
        ),
    )
    entry = _usage_by_key(ctx)["staging.busy"]
    assert entry["runs_seen"] == 3
    # The window reported is the one that actually happened, unfloored.
    assert entry["window_days"] == pytest.approx(12 / (60 * 24), abs=1e-6)
    # 2 intervals / (1/24 day) = 48, not 240.
    assert entry["rate_per_day"] == pytest.approx(48.0)


def test_usage_rides_on_the_object_record(tmp_path, theme):
    """The wire shape, on a re-read document rather than on the dict the
    builder returned."""
    ctx = _usage_project(
        tmp_path,
        runs=(
            RunSpec(
                "r1",
                "run",
                datetime(2026, 8, 1, 0, 0),
                nodes=(("model.fx_dbt.busy", "success", 2.0),),
            ),
            RunSpec(
                "r2",
                "run",
                datetime(2026, 8, 3, 0, 0),
                nodes=(("model.fx_dbt.busy", "success", 4.0),),
            ),
        ),
    )
    records = {o["key"]: o for o in _document(ctx, theme)["objects"]}
    assert records["staging.busy"]["usage"]["source"] == "runs"
    assert records["staging.never"]["usage"] is None


# ---------------------------------------------------------------------------
# BUDGET — the bill, and the two zeros that must never be confused
# ---------------------------------------------------------------------------


def test_no_run_history_leaves_the_budget_null_and_the_absence_named(tmp_path):
    """Not a $0 bill. The catalog already carries the note that says why."""
    root = make_tycoon_project(tmp_path / "fx", with_metadata=False)
    ctx = load_context(root)

    assert ctx.runs is None
    assert "no run metadata (.tycoon/metadata.duckdb)" in ctx.notes
    assert _budget(ctx) is None


def test_metadata_with_no_runs_in_it_is_still_null(tmp_path):
    ctx = _usage_project(tmp_path, runs=())
    assert ctx.runs is not None  # the database opened; it simply holds nothing
    assert "no run history yet" in ctx.notes
    assert _budget(ctx) is None


def test_local_duckdb_bills_zero_as_a_fact_with_its_reason(tmp_path):
    """$0 *because local DuckDB is free*, standing next to a measured load
    that is emphatically not zero. The note is what tells the two zeros
    apart."""
    ctx = _usage_project(
        tmp_path,
        runs=(
            RunSpec(
                "r1",
                "run",
                datetime(2026, 8, 1, 0, 0),
                nodes=(("model.fx_dbt.busy", "success", 2.0),),
            ),
            RunSpec(
                "r2",
                "run",
                datetime(2026, 8, 3, 0, 0),
                nodes=(("model.fx_dbt.busy", "success", 4.0),),
            ),
        ),
    )
    budget = _budget(ctx)

    assert budget["engine"] == "duckdb"
    assert budget["unit_price_per_s"] == 0.0
    assert budget["daily_cost"] == 0.0
    # The load is real: 1 interval over 2 days x a 3.0s mean cost.
    assert budget["daily_load_s"] == pytest.approx(1.5)
    assert "local DuckDB is free" in budget["note"]
    assert "the load is measured, the bill is zero" in budget["note"]


def test_a_partial_bill_counts_what_it_left_out(tmp_path):
    """4 objects on the map (3 models + 1 source), 1 priced. The other three
    are counted, not folded in at zero."""
    ctx = _usage_project(
        tmp_path,
        runs=(
            RunSpec(
                "r1",
                "run",
                datetime(2026, 8, 1, 0, 0),
                nodes=(("model.fx_dbt.busy", "success", 2.0),),
            ),
            RunSpec(
                "r2",
                "run",
                datetime(2026, 8, 3, 0, 0),
                nodes=(
                    ("model.fx_dbt.busy", "success", 4.0),
                    # One build only: no cadence, so no price.
                    ("model.fx_dbt.once", "success", 9.0),
                ),
            ),
        ),
    )
    assert len(ctx.objects) == 4
    budget = _budget(ctx)

    assert budget["priced_objects"] == 1
    assert budget["unpriced_objects"] == 3
    assert [row["object_key"] for row in budget["by_object"]] == ["staging.busy"]
    assert "priced 1 of 4 objects" in budget["note"]
    assert "3 have too little run history" in budget["note"]


def test_nothing_priceable_reports_unknown_totals_not_a_zero_bill(tmp_path):
    """Builds exist, but only one each, so no cadence exists. The totals are
    NULL — a 0.00 here would be the exact $0-because-unknown this block must
    never emit."""
    ctx = _usage_project(
        tmp_path,
        runs=(
            RunSpec(
                "r1",
                "run",
                datetime(2026, 8, 1, 0, 0),
                nodes=(("model.fx_dbt.busy", "success", 2.0),),
            ),
        ),
    )
    budget = _budget(ctx)

    assert budget is not None  # there IS history; it just cannot be priced
    assert budget["priced_objects"] == 0
    assert budget["daily_load_s"] is None
    assert budget["daily_cost"] is None
    assert "unknown, not a zero bill" in budget["note"]


def test_a_measured_zero_load_is_priced_not_excluded(tmp_path):
    """A model whose builds all took 0.0s has a load of zero that was
    MEASURED. It belongs in the bill; only unknown belongs outside it."""
    ctx = _usage_project(
        tmp_path,
        runs=(
            RunSpec(
                "r1",
                "run",
                datetime(2026, 8, 1, 0, 0),
                nodes=(("model.fx_dbt.busy", "success", 0.0),),
            ),
            RunSpec(
                "r2",
                "run",
                datetime(2026, 8, 3, 0, 0),
                nodes=(("model.fx_dbt.busy", "success", 0.0),),
            ),
        ),
    )
    budget = _budget(ctx)

    assert budget["priced_objects"] == 1
    assert budget["by_object"] == [{"object_key": "staging.busy", "daily_load_s": 0.0, "daily_cost": 0.0}]


def test_a_paid_engine_bills_the_same_load_in_its_own_vocabulary(tmp_path):
    """Engine-neutral: the arithmetic does not change, only the rate and the
    sentence describing how that engine bills."""
    ctx = _usage_project(
        tmp_path,
        runs=(
            RunSpec(
                "r1",
                "run",
                datetime(2026, 8, 1, 0, 0),
                nodes=(("model.fx_dbt.busy", "success", 2.0),),
            ),
            RunSpec(
                "r2",
                "run",
                datetime(2026, 8, 3, 0, 0),
                nodes=(("model.fx_dbt.busy", "success", 4.0),),
            ),
        ),
    )
    book = PriceBook(
        engine="snowflake",
        currency="USD",
        unit_price_per_s=0.001,
        price_source="tests",
        note="Snowflake bills warehouses by the second",
    )
    budget = _budget(ctx, book)

    assert budget["engine"] == "snowflake"
    assert budget["price_source"] == "tests"
    assert budget["daily_cost"] == pytest.approx(0.0015)
    assert "warehouses" in budget["note"]
    # The built-in table keeps the same vocabulary, so no caller has to
    # hand-write the sentence to get it right.
    assert "ducklings" in DEFAULT_PRICES["motherduck"].note
