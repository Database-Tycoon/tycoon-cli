"""Reading .tycoon/metadata.duckdb, pinned against the real database's shape:
`success` NULL everywhere, `rows_affected` NULL everywhere."""

from datetime import datetime, timedelta

import duckdb

from tests.fixtures.tycoon_factory import RunSpec, make_tycoon_project
from tycoon_city.catalog.run_history import read_run_history


def _metadata(tmp_path, **kwargs):
    root = make_tycoon_project(tmp_path / "fx", **kwargs)
    return root / ".tycoon" / "metadata.duckdb"


def test_ok_is_derived_never_read_from_the_success_column(tmp_path):
    """The factory writes `success` as NULL on every row, exactly like the real
    database. Anything reading that column gets NULL -> falsy for every run;
    these assertions can only pass on the derived rule."""
    path = _metadata(
        tmp_path,
        runs=(
            RunSpec("good", "run", datetime(2026, 8, 1)),
            RunSpec("bad", "run", datetime(2026, 8, 2), models_error=2),
            RunSpec("test-fail", "test", datetime(2026, 8, 3), tests_failed=1),
        ),
    )

    history = read_run_history(path)

    by_id = {run.invocation_id: run for run in history.runs}
    assert by_id["good"].ok is True
    assert by_id["bad"].ok is False
    assert by_id["test-fail"].ok is False


def test_runs_come_newest_first_and_node_results_take_the_latest(tmp_path):
    path = _metadata(
        tmp_path,
        runs=(
            RunSpec("old", "run", datetime(2026, 7, 1), nodes=(("model.fx_dbt.m", "error", 1.0),)),
            RunSpec("new", "run", datetime(2026, 8, 1), nodes=(("model.fx_dbt.m", "success", 2.0),)),
        ),
    )

    history = read_run_history(path)

    assert [run.invocation_id for run in history.runs] == ["new", "old"]
    assert history.latest.invocation_id == "new"
    result = history.node_results["model.fx_dbt.m"]
    assert result.status == "success"
    assert result.execution_time_s == 2.0


def test_prefer_target_filters_and_the_fallback_is_named(tmp_path):
    runs = (
        RunSpec("dev-1", "run", datetime(2026, 8, 1), target="dev"),
        RunSpec("prod-1", "run", datetime(2026, 8, 2), target="prod"),
    )
    path = _metadata(tmp_path, runs=runs)

    preferred = read_run_history(path, prefer_target="prod")
    assert [r.invocation_id for r in preferred.runs] == ["prod-1"]

    # Asked for a target that never ran: keep everything, name what happened.
    fallback = read_run_history(path, prefer_target="staging")
    assert len(fallback.runs) == 2
    assert any("run history" in note for note in fallback.notes)


def _two_targets(tmp_path):
    return _metadata(
        tmp_path,
        runs=(
            RunSpec("dev-1", "run", datetime(2026, 8, 1), target="dev"),
            RunSpec("prod-1", "run", datetime(2026, 8, 2), target="prod"),
        ),
    )


def _claims_a_single_target(notes):
    """Notes that assert every retained run came from one named target."""
    return [n for n in notes if "from target '" in n or "filtered to target '" in n]


# --- prefer_target, one test per branch. The law under all four: a note may
# --- only state what actually happened to `runs`.


def test_prefer_target_that_matches_filters_and_says_what_it_hid(tmp_path):
    history = read_run_history(_two_targets(tmp_path), prefer_target="prod")

    assert [r.invocation_id for r in history.runs] == ["prod-1"]
    assert any("filtered to target 'prod'" in n and "dev" in n for n in history.notes), history.notes


def test_prefer_target_that_is_the_only_target_claims_no_filtering(tmp_path):
    """Nothing was excluded, so nothing may be reported as excluded."""
    path = _metadata(
        tmp_path,
        runs=(
            RunSpec("dev-1", "run", datetime(2026, 8, 1), target="dev"),
            RunSpec("dev-2", "run", datetime(2026, 8, 2), target="dev"),
        ),
    )

    history = read_run_history(path, prefer_target="dev")

    assert len(history.runs) == 2
    assert not any("hiding" in n for n in history.notes), history.notes


def test_prefer_target_that_matches_nothing_never_claims_a_filter(tmp_path):
    """THE bug. `prefer_target='staging'` matched no run, so the runs stayed
    unfiltered -- and the note said "run history from target 'dev'", naming a
    filter that never ran and the wrong target with it."""
    history = read_run_history(_two_targets(tmp_path), prefer_target="staging")

    # Precondition: the runs really were left unfiltered, spanning both
    # targets. Without this the note assertions below prove nothing.
    assert {r.target for r in history.runs} == {"dev", "prod"}

    assert _claims_a_single_target(history.notes) == [], history.notes
    note = " ".join(history.notes)
    assert "staging" in note and "dev" in note and "prod" in note, history.notes


def test_prefer_target_that_matches_nothing_with_one_target_present(tmp_path):
    path = _metadata(tmp_path, runs=(RunSpec("dev-1", "run", datetime(2026, 8, 1), target="dev"),))

    history = read_run_history(path, prefer_target="staging")

    assert [r.invocation_id for r in history.runs] == ["dev-1"]
    assert any("no run history for target 'staging'" in n for n in history.notes), history.notes


def test_a_single_target_without_a_preference_is_named(tmp_path):
    path = _metadata(tmp_path, runs=(RunSpec("dev-1", "run", datetime(2026, 8, 1), target="dev"),))

    history = read_run_history(path)

    assert any("run history from target 'dev'" in n for n in history.notes), history.notes


def test_multiple_targets_without_preference_are_named(tmp_path):
    path = _metadata(
        tmp_path,
        runs=(
            RunSpec("a", target="dev", started_at=datetime(2026, 8, 1)),
            RunSpec("b", target="prod", started_at=datetime(2026, 8, 2)),
        ),
    )

    history = read_run_history(path)

    assert len(history.runs) == 2
    assert any("spans targets: dev, prod" in note for note in history.notes)


def test_missing_file_reads_as_none(tmp_path):
    assert read_run_history(tmp_path / "nope.duckdb") is None


def test_a_missing_table_costs_its_signals_only(tmp_path):
    """A metadata db written by an older CLI: dbt_runs exists, dbt_nodes does
    not. Runs must load; node results must be empty; no exception."""
    path = tmp_path / "old.duckdb"
    con = duckdb.connect(str(path))
    con.execute(
        """create table dbt_runs (
            invocation_id varchar, command varchar, started_at timestamp,
            elapsed_s double, success boolean, models_ok integer,
            models_error integer, tests_passed integer, tests_failed integer,
            dbt_version varchar, target_name varchar, captured_at timestamp)"""
    )
    con.execute(
        "insert into dbt_runs values ('r1', 'run', '2026-08-01', 1.0, NULL, 1, 0, 0, 0, '1.11.0', 'dev', '2026-08-01')"
    )
    con.close()

    history = read_run_history(path)

    assert [r.invocation_id for r in history.runs] == ["r1"]
    assert history.node_results == {}
    assert history.dlt_loaded_at == {}


def test_dlt_tables_are_read_when_present(tmp_path):
    path = _metadata(tmp_path)
    con = duckdb.connect(str(path))
    con.execute("insert into dlt_runs values ('toggl', 'load-1', 0, '2026-08-01', 'h', '2026-08-01')")
    con.execute("insert into dlt_rows_by_table values ('toggl', 'time_entries', 'load-1', 123, '2026-08-01')")
    con.close()

    history = read_run_history(path)

    assert history.dlt_loaded_at["toggl"] == datetime(2026, 8, 1)
    assert history.dlt_rows["toggl.time_entries"] == 123


def test_daily_load_is_cadence_times_mean_cost_and_never_a_guess():
    from datetime import datetime, timedelta

    from tycoon_city.catalog.run_history import daily_load_s

    t0 = datetime(2026, 8, 1, 6, 0, 0)
    # 5 builds over exactly 4 days -> 1/day cadence; mean cost 10s -> 10 s/day.
    steady = tuple((t0 + timedelta(days=i), 10.0) for i in range(5))
    assert daily_load_s(steady) == 1.0 * 10.0

    # One build says nothing; a same-instant burst says nothing.
    assert daily_load_s(steady[:1]) is None
    assert daily_load_s(((t0, 5.0), (t0, 5.0))) is None

    # A 10-minute burst is floored to a one-hour span, not thousands/day.
    burst = tuple((t0 + timedelta(minutes=i), 1.0) for i in range(11))
    assert daily_load_s(burst) == (10 / (1 / 24)) * 1.0


def test_run_nodes_keep_every_status_of_one_specific_invocation(tmp_path):
    """`node_results` folds a node's runs down to the newest and
    `build_history` keeps only the successes -- between them the failures and
    skips a single run is MADE of are gone, and no specific run is
    reconstructable. This is the field that fixes that."""
    from tycoon_city.catalog.run_history import RunNode

    path = _metadata(
        tmp_path,
        runs=(
            RunSpec(
                "bad",
                "build",
                datetime(2026, 8, 1),
                models_error=1,
                nodes=(
                    ("model.fx_dbt.zz", "error", 0.4),
                    ("model.fx_dbt.aa", "skipped", 0.0),
                    ("model.fx_dbt.mm", "success", 1.0),
                ),
            ),
            RunSpec(
                "good",
                "build",
                datetime(2026, 8, 2),
                nodes=(("model.fx_dbt.zz", "success", 0.5),),
            ),
        ),
    )

    history = read_run_history(path)

    # Sorted by unique_id, so a document built from it is stable for fixed input.
    assert history.run_nodes["bad"] == (
        RunNode("model.fx_dbt.aa", "skipped", 0.0),
        RunNode("model.fx_dbt.mm", "success", 1.0),
        RunNode("model.fx_dbt.zz", "error", 0.4),
    )
    # The newer success must not overwrite the older failure -- that is exactly
    # what node_results does, and why it cannot serve a replay.
    assert history.node_results["model.fx_dbt.zz"].status == "success"
    assert history.run_nodes["good"] == (RunNode("model.fx_dbt.zz", "success", 0.5),)


def test_run_nodes_are_capped_to_the_newest_invocations(tmp_path):
    """A year of hourly builds is ~9,000 runs; replay is something you do to a
    recent one. The cap is on the newest runs, not on whichever rows came back
    first."""
    from tycoon_city.catalog.run_history import MAX_REPLAY_RUNS

    total = MAX_REPLAY_RUNS + 4
    runs = tuple(
        RunSpec(
            f"run-{i:03d}",
            "run",
            datetime(2026, 8, 1) + timedelta(hours=i),
            nodes=(("model.fx_dbt.m", "success", 1.0),),
        )
        for i in range(total)
    )

    history = read_run_history(_metadata(tmp_path, runs=runs))

    assert len(history.runs) == total, "every RUN is still listed"
    assert set(history.run_nodes) == {f"run-{i:03d}" for i in range(total - MAX_REPLAY_RUNS, total)}
