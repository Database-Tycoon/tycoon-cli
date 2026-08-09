"""The run documents, asserted on hand-counted keys from a fixture DAG.

Two habits, both reactions to this repo's history:

* **Preconditions are asserted.** A cascade test whose fixture run contains no
  failure and no skip passes on an empty answer. Every test that reads a
  cascade first states what the fixture is made of.
* **Never "non-empty".** The cascade tests name WHICH keys, counted by hand off
  the diagram in `tests/fixtures/tycoon_factory.py`, and name the two keys that
  must be absent — one downstream of the failure that dbt built anyway, one
  skipped model that is not downstream at all. "The cascade is non-empty"
  passes on the wrong cascade.
"""

import json
from datetime import datetime

import pytest

from tests.fixtures.tycoon_factory import RunSpec, make_cascade_project, make_tycoon_project
from tycoon_city.catalog.loader import load_context
from tycoon_city.catalog.models import CatalogObject, Edge, PipelineContext
from tycoon_city.catalog.run_history import MAX_REPLAY_RUNS, RunHistory, RunNode
from tycoon_city.export.build import build_city
from tycoon_city.export.city_json import city_document
from tycoon_city.export.city_json import dumps as city_dumps
from tycoon_city.export.run_json import (
    INDEX_FORMAT,
    NO_HISTORY_NOTE,
    ORDER_RECONSTRUCTED,
    RUN_FORMAT,
    VERSION,
    dumps,
    known_run_ids,
    run_document,
    run_file_name,
    runs_index,
)
from tycoon_city.theme_data import load_theme_data, theme_dir


@pytest.fixture
def ctx(tmp_path):
    return load_context(make_cascade_project(tmp_path / "fx"))


def _reparsed(doc) -> dict:
    """What a client actually receives. Assertions made on the dict handed to
    the serialiser cannot notice a document that serialises wrongly."""
    return json.loads(dumps(doc))


def _keys(steps) -> list[str]:
    return [step["object_key"] for step in steps]


# --- Preconditions ----------------------------------------------------------


def test_the_fixture_run_really_holds_a_success_a_failure_and_a_skip(ctx):
    """Everything below is meaningless if `build-1` is all successes. This is
    the assertion that gives the rest of the file the right to fail."""
    steps = _reparsed(run_document(ctx, "build-1"))["steps"]
    statuses = {step["object_key"]: step["status"] for step in steps}

    assert statuses["staging.stg_orders"] == "success"
    assert statuses["mart.zz_fail"] == "error"
    assert statuses["mart.aa_skip"] == "skipped"
    # And the skips are not all one lump: one is downstream of the failure, one
    # is not, and one downstream model was built anyway.
    assert statuses["mart.zzz_skip_unrelated"] == "skipped"
    assert statuses["mart.cc_built"] == "success"


# --- The index --------------------------------------------------------------


def test_the_index_lists_runs_newest_first_with_derived_ok_and_measured_counts(ctx):
    index = _reparsed(runs_index(ctx))

    assert index["format"] == INDEX_FORMAT
    assert index["version"] == VERSION
    assert index["database"] == "fx"
    assert [run["id"] for run in index["runs"]] == ["odd-1", "partial-1", "build-1"]

    build = next(run for run in index["runs"] if run["id"] == "build-1")
    # `ok` is derived from the counts; the stored `success` column is NULL on
    # every row the factory writes, exactly as in the real database.
    assert build["ok"] is False
    assert build["command"] == "build"
    assert build["started_at"] == "2026-08-02T03:00:00"
    assert build["models_error"] == 1 and build["tests_failed"] == 1
    # Six models have a building here; the failing test does not.
    assert build["step_count"] == 6
    assert build["unmapped_count"] == 1
    assert build["failed_count"] == 1

    odd = next(run for run in index["runs"] if run["id"] == "odd-1")
    assert odd["ok"] is True, "no error models and no failed tests"


def test_the_index_carries_the_loaders_own_words_and_never_404s_without_history(tmp_path):
    """No history is an empty list plus the reason, not an error. The reason is
    the loader's sentence, passed through — two wordings for one fact is how
    they drift."""
    root = make_tycoon_project(tmp_path / "fx", runs=())
    index = _reparsed(runs_index(load_context(root)))

    assert index["runs"] == []
    assert "no run history yet" in index["notes"], "the loader's own sentence"

    # And a catalog with no metadata database at all still gets an index.
    bare = load_context(make_tycoon_project(tmp_path / "bare", with_metadata=False))
    bare_index = _reparsed(runs_index(bare))
    assert bare_index["runs"] == []
    assert "no run metadata (.tycoon/metadata.duckdb)" in bare_index["notes"]
    assert NO_HISTORY_NOTE in bare_index["notes"]


def test_the_index_names_the_window_when_older_runs_are_hidden(tmp_path):
    """Only the newest MAX_REPLAY_RUNS invocations keep node detail, so only
    they are listed — and the document says so rather than pretending the older
    runs never happened. Absence stays named."""
    extra = 3
    runs = tuple(
        RunSpec(
            f"run-{i:03d}",
            "run",
            datetime(2026, 8, 1, 0, 0) + i * (datetime(2026, 8, 1, 1, 0) - datetime(2026, 8, 1, 0, 0)),
        )
        for i in range(MAX_REPLAY_RUNS + extra)
    )
    ctx = load_context(make_tycoon_project(tmp_path / "fx", runs=runs))
    index = _reparsed(runs_index(ctx))

    assert len(index["runs"]) == MAX_REPLAY_RUNS
    assert index["runs"][0]["id"] == f"run-{MAX_REPLAY_RUNS + extra - 1:03d}", "newest first"
    assert f"showing the newest {MAX_REPLAY_RUNS} of {MAX_REPLAY_RUNS + extra} runs" in (index["notes"])
    # The window is the same one the documents exist for: an id the index does
    # not list is an id the server must 404.
    assert known_run_ids(ctx) == {run["id"] for run in index["runs"]}
    assert run_document(ctx, "run-000") is None


# --- One run ----------------------------------------------------------------


def test_steps_are_dense_and_in_reconstructed_topological_order(ctx):
    """dbt_nodes has durations and no per-node start times (probed 2026-08-06),
    so the order is rebuilt over the city's edges — and the document says which
    it is instead of leaving the client to assume."""
    doc = _reparsed(run_document(ctx, "build-1"))

    assert doc["format"] == RUN_FORMAT
    assert doc["order_source"] == ORDER_RECONSTRUCTED
    assert doc["note"] == "durations measured, ordering reconstructed"
    assert [step["order"] for step in doc["steps"]] == list(range(6)), "dense 0..n-1"
    # Hand-counted off the fixture diagram: the source's model first, then the
    # failure, then its siblings and children in key order.
    assert _keys(doc["steps"]) == [
        "staging.stg_orders",
        "mart.zz_fail",
        "mart.zzz_skip_unrelated",
        "mart.aa_skip",
        "mart.cc_built",
        "mart.bb_skip_deep",
    ]
    # Every step comes after everything it depends on -- the property the list
    # above is one instance of.
    position = {step["object_key"]: step["order"] for step in doc["steps"]}
    for step in doc["steps"]:
        for parent in step["depends_on"]:
            if parent in position:
                assert position[parent] < step["order"], f"{parent} must precede {step}"


def test_status_is_dbts_own_word_relayed_not_folded(ctx):
    """`sim.signals` folds unrecognised words because a visual channel has to
    pick a colour. The record has no such excuse: `partial success` is not in
    BUILD_STATUS_VOCABULARY and must survive the trip unchanged."""
    from tycoon_city.sim.signals import BUILD_STATUS_VOCABULARY

    doc = _reparsed(run_document(ctx, "odd-1"))

    assert "partial success" not in BUILD_STATUS_VOCABULARY, "precondition: an unknown word"
    assert [step["status"] for step in doc["steps"]] == ["partial success"]


def test_what_ran_without_a_building_is_listed_never_dropped(ctx):
    """The failing test node has no lot in this city. Dropping it silently
    would make a six-step document out of a seven-node run."""
    doc = _reparsed(run_document(ctx, "build-1"))

    assert [node["unique_id"] for node in doc["unmapped"]] == ["test.fx_dbt.check_orders"]
    assert doc["unmapped"][0]["node_kind"] == "test"
    assert doc["unmapped"][0]["status"] == "fail"
    assert doc["run"]["step_count"] + doc["run"]["unmapped_count"] == 7


def test_depends_on_is_intersected_with_this_citys_objects():
    """A client cannot draw a road to something that is not on the map, so a
    key that has no object is not offered to it. Hand-built context: the loader
    already filters, and this is the guard for everything that does not."""
    ctx = PipelineContext(
        database_name="fx",
        objects=(CatalogObject(schema="s", name="child", kind="table", row_count=1),),
        # `s.ghost` is NOT in objects: an edge to a building that is not here.
        edges=(Edge(src="s.ghost", dst="s.child"),),
        dbt_nodes_by_key={"s.child": "model.fx.child"},
        runs=RunHistory(
            runs=(_run("only-1"),),
            node_results={},
            dlt_loaded_at={},
            dlt_rows={},
            schema_changed_at={},
            notes=(),
            run_nodes={"only-1": (RunNode("model.fx.child", "success", 1.0),)},
        ),
    )

    doc = _reparsed(run_document(ctx, "only-1"))

    assert _keys(doc["steps"]) == ["s.child"]
    assert doc["steps"][0]["depends_on"] == [], "s.ghost has no building here"


def _run(invocation_id: str):
    from tycoon_city.catalog.run_history import DbtRun

    return DbtRun(
        invocation_id=invocation_id,
        command="run",
        started_at=datetime(2026, 8, 2, 3, 0),
        target="dev",
        ok=True,
        models_error=0,
        tests_failed=0,
        elapsed_s=1.0,
    )


# --- The cascade ------------------------------------------------------------


def test_the_cascade_names_exactly_the_skips_dbt_reported_downstream(ctx):
    """Three measured facts joined: dbt said `skipped`, the city's edges reach
    it from the failure, and it comes later in the run's order.

    The two absences are the point of the fixture:
    `mart.cc_built` IS downstream of the failure and dbt built it — a blast
    radius would dim it; `mart.zzz_skip_unrelated` IS a later skip but is not
    downstream of the failure at all.
    """
    doc = _reparsed(run_document(ctx, "build-1"))
    skipped_steps = {s["object_key"] for s in doc["steps"] if s["status"] == "skipped"}
    assert skipped_steps == {
        "mart.aa_skip",
        "mart.bb_skip_deep",
        "mart.zzz_skip_unrelated",
    }, "precondition: three skips, only two of them downstream of the failure"

    assert doc["failure_cascade"] == [
        {
            "object_key": "mart.zz_fail",
            "order": 1,
            "skipped": ["mart.aa_skip", "mart.bb_skip_deep"],
        }
    ]


def test_a_skip_the_order_cannot_place_after_the_failure_is_not_dimmed(ctx):
    """`partial-1` ran the failure and `mart.bb_skip_deep` but not the model
    that links them, so the reconstruction puts the skip FIRST (ties break on
    key, and `bb` < `zz`). Reachable and skipped, but not later: the run is not
    evidence that one caused the other, and the document does not say it did.
    An entry is still emitted — "nothing measurable cascaded" is a fact."""
    doc = _reparsed(run_document(ctx, "partial-1"))

    assert _keys(doc["steps"]) == ["mart.bb_skip_deep", "mart.zz_fail"]
    assert doc["steps"][0]["status"] == "skipped" and doc["steps"][1]["status"] == "error"
    assert doc["failure_cascade"] == [{"object_key": "mart.zz_fail", "order": 1, "skipped": []}]


def test_a_failure_that_took_nothing_down_is_still_named(tmp_path):
    """An entry per failure, even when the cascade is empty. A client that only
    ever sees non-empty entries cannot tell "nothing cascaded" from "we did not
    look" -- and a producer that emits nothing here reads as a clean run."""
    runs = (
        RunSpec(
            "solo-fail",
            "build",
            datetime(2026, 8, 2, 6, 0),
            models_error=1,
            nodes=(
                ("model.fx_dbt.stg_orders", "success", 1.5),
                ("model.fx_dbt.zz_fail", "error", 0.4),
            ),
        ),
    )
    ctx = load_context(make_cascade_project(tmp_path / "fx", runs=runs))

    doc = _reparsed(run_document(ctx, "solo-fail"))

    assert [step["status"] for step in doc["steps"]] == ["success", "error"], (
        "precondition: a failure and no skip anywhere in the run"
    )
    assert doc["failure_cascade"] == [{"object_key": "mart.zz_fail", "order": 1, "skipped": []}]


def test_an_unknown_run_id_has_no_document(ctx):
    assert run_document(ctx, "never-happened") is None
    assert run_document(ctx, "../../etc/passwd") is None
    assert "never-happened" not in known_run_ids(ctx)


def test_an_id_that_is_not_a_safe_file_name_is_refused_not_sanitised():
    """The static export turns ids into filenames. Rewriting a bad one would
    file a run's steps under another run's name."""
    assert run_file_name("2f1c9a3e-7c2b-4c1a-9c0e-1f2a3b4c5d6e") == ("2f1c9a3e-7c2b-4c1a-9c0e-1f2a3b4c5d6e.json")
    assert run_file_name("../../etc/passwd") is None
    assert run_file_name("a/b") is None
    assert run_file_name("") is None
    assert run_file_name(".") is None


# --- The hard law -----------------------------------------------------------


def test_no_run_id_and_no_run_timestamp_reaches_city_json(tmp_path):
    """THE SENTINEL. `city.json` v1 is byte-stable and carries no uuid, path,
    seed or timestamp; that is what makes the committed golden and the
    cross-language contract test possible. Run records carry an invocation_id
    and a wall clock, so they live in these documents instead.

    Asserted on the emitted BYTES of the contract document, with the ids and
    timestamps taken from the run documents built off the same context — so the
    two can never drift into agreement by accident.
    """
    root = make_cascade_project(tmp_path / "fx")
    ctx = load_context(root)
    theme = load_theme_data(theme_dir("default"))
    _, city = build_city(str(root), theme.style_rules)
    city_bytes = city_dumps(city_document(ctx, city, theme))

    index = runs_index(ctx)
    assert index["runs"], "precondition: there are runs to leak"

    for header in index["runs"]:
        assert header["id"] not in city_bytes, f"invocation_id {header['id']} leaked"
        assert header["started_at"] not in city_bytes, "a run's wall clock leaked"
        # The date alone, too: a truncated timestamp is still a timestamp.
        assert header["started_at"][:10] not in city_bytes
    # And the replay block city.json does carry names no run.
    replay = json.loads(city_bytes)["replay"]
    assert replay is not None, "precondition: the aggregate replay block exists"
    assert "id" not in replay and "run" not in replay
