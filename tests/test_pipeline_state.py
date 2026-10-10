"""Per-project dlt working directories and the state carry-over (gh-394).

Every test runs with a temporary HOME, so dlt's shared directory is
``<tmp>/home/.dlt/pipelines`` and the real ``~/.dlt`` is never touched.
"""

from __future__ import annotations

import importlib
import os
from pathlib import Path

import dlt
import duckdb
import pytest

from tycoon.ingestion import pipeline_state as ps


@pytest.fixture(autouse=True)
def isolated_dlt_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("DLT_DATA_DIR", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.delenv("RESTORE_FROM_DESTINATION", raising=False)
    return home


def _events(project: str, upto: int):
    @dlt.resource(name="events", write_disposition="append")
    def events(cursor=dlt.sources.incremental("id", initial_value=0)):
        yield [{"id": i, "project": project} for i in range(1, upto + 1) if i > cursor.start_value]

    return events


def _run(raw_db: Path, dataset: str, project: str, upto: int, pipelines_dir: Path | None = None) -> None:
    pipeline = dlt.pipeline(
        pipeline_name="github",
        pipelines_dir=str(pipelines_dir) if pipelines_dir else None,
        destination=dlt.destinations.duckdb(str(raw_db)),
        dataset_name=dataset,
    )
    pipeline.run(_events(project, upto))


def _rows(raw_db: Path, dataset: str) -> tuple[int, int]:
    con = duckdb.connect(str(raw_db), read_only=True)
    try:
        row = con.execute(f"SELECT count(*), count(DISTINCT id) FROM {dataset}.events").fetchone()
    finally:
        con.close()
    assert row is not None
    return row[0], row[1]


def _plan(raw_db: Path, dataset: str, project_root: Path) -> ps.StatePlan:
    return ps.plan_carry_over(
        "github", dataset, raw_db, ps.project_pipelines_dir(project_root), ps.shared_pipelines_dir()
    )


def _run_in_project(project_root: Path, raw_db: Path, dataset: str, project: str, upto: int) -> ps.StatePlan:
    """What the runner does: plan, carry over, then run inside the project dir."""
    plan = _plan(raw_db, dataset, project_root)
    with ps.project_pipelines_env(project_root):
        ps.carry_over(plan)
        _run(raw_db, dataset, project, upto)
    return plan


class TestLocations:
    def test_shared_dir_is_dlts_default(self, isolated_dlt_home: Path) -> None:
        assert ps.shared_pipelines_dir() == isolated_dlt_home / ".dlt" / "pipelines"

    def test_project_dir_sits_next_to_project_sources(self, tmp_path: Path) -> None:
        assert ps.project_pipelines_dir(tmp_path) == tmp_path / ".tycoon" / "dlt" / "pipelines"

    def test_generic_source_identity(self) -> None:
        assert ps.pipeline_identity("github", "raw_github") == ("github", "raw_github")

    @pytest.mark.parametrize("source_name", sorted(ps.LEGACY_PIPELINE_IDENTITIES))
    def test_legacy_identity_matches_its_module(
        self, source_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from tycoon.ingestion.runner import _LEGACY_PIPELINES

        seen: dict[str, str] = {}

        class _Stop(Exception):
            pass

        def fake_pipeline(**kwargs: str) -> None:
            seen.update(kwargs)
            raise _Stop

        mod = importlib.import_module(_LEGACY_PIPELINES[source_name])
        monkeypatch.setattr(mod.dlt, "pipeline", fake_pipeline)
        with pytest.raises(_Stop):
            mod.run_pipeline(raw_db_path=tmp_path / "raw.duckdb", max_records=1)

        assert ps.pipeline_identity(source_name, "ignored") == (seen["pipeline_name"], seen["dataset_name"])


class TestPlan:
    def test_nothing_to_do_without_shared_state(self, tmp_path: Path) -> None:
        plan = _plan(tmp_path / "raw.duckdb", "raw_github", tmp_path / "project")
        assert plan.action is ps.CarryOver.NOT_NEEDED

    def test_nothing_to_do_once_the_project_has_state(self, tmp_path: Path) -> None:
        raw_db = tmp_path / "raw.duckdb"
        _run(raw_db, "raw_github", "a", 3)
        project = tmp_path / "project"
        (ps.project_pipelines_dir(project) / "github").mkdir(parents=True)

        assert _plan(raw_db, "raw_github", project).action is ps.CarryOver.NOT_NEEDED

    def test_fresh_when_the_project_never_loaded_this_dataset(self, tmp_path: Path) -> None:
        _run(tmp_path / "other.duckdb", "raw_other", "other", 3)

        plan = _plan(tmp_path / "raw.duckdb", "raw_github", tmp_path / "project")

        assert plan.action is ps.CarryOver.FRESH

    def test_copy_when_shared_state_is_this_projects_own(self, tmp_path: Path) -> None:
        raw_db = tmp_path / "a.duckdb"
        _run(raw_db, "raw_a", "a", 10)

        assert _plan(raw_db, "raw_a", tmp_path / "project").action is ps.CarryOver.COPY

    def test_restore_when_another_project_moved_the_shared_cursor(self, tmp_path: Path) -> None:
        _run(tmp_path / "a.duckdb", "raw_a", "a", 10)
        _run(tmp_path / "b.duckdb", "raw_b", "b", 5)

        plan = _plan(tmp_path / "a.duckdb", "raw_a", tmp_path / "project")

        assert plan.action is ps.CarryOver.RESTORE_FROM_DESTINATION

    def test_copy_when_mismatched_but_restore_is_off(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _run(tmp_path / "a.duckdb", "raw_a", "a", 10)
        _run(tmp_path / "b.duckdb", "raw_b", "b", 5)
        monkeypatch.setenv("RESTORE_FROM_DESTINATION", "false")

        assert _plan(tmp_path / "a.duckdb", "raw_a", tmp_path / "project").action is ps.CarryOver.COPY_UNVERIFIED

    def test_copy_when_the_dataset_has_no_stored_state(self, tmp_path: Path) -> None:
        _run(tmp_path / "other.duckdb", "raw_other", "other", 3)
        raw_db = tmp_path / "raw.duckdb"
        con = duckdb.connect(str(raw_db))
        con.execute("CREATE SCHEMA raw_github; CREATE TABLE raw_github.events (id INTEGER)")
        con.close()

        assert _plan(raw_db, "raw_github", tmp_path / "project").action is ps.CarryOver.COPY_UNVERIFIED

    def test_unreadable_raw_database_changes_nothing(self, tmp_path: Path) -> None:
        _run(tmp_path / "other.duckdb", "raw_other", "other", 3)
        raw_db = tmp_path / "raw.duckdb"
        raw_db.write_text("not a duckdb file")
        project = tmp_path / "project"

        with pytest.raises(ps.StateCarryOverError, match="Nothing was changed"):
            _plan(raw_db, "raw_github", project)
        assert not project.exists()


class TestCarryOver:
    def test_copies_and_leaves_the_shared_dir_alone(self, tmp_path: Path) -> None:
        raw_db = tmp_path / "a.duckdb"
        _run(raw_db, "raw_a", "a", 10)
        shared = ps.shared_pipelines_dir() / "github"
        before = sorted(p.relative_to(shared) for p in shared.rglob("*"))
        project = tmp_path / "project"

        ps.carry_over(_plan(raw_db, "raw_a", project))

        copied = ps.project_pipelines_dir(project) / "github"
        assert (copied / "state.json").read_bytes() == (shared / "state.json").read_bytes()
        assert sorted(p.relative_to(shared) for p in shared.rglob("*")) == before
        assert [p.name for p in ps.project_pipelines_dir(project).iterdir()] == ["github"]

    @pytest.mark.parametrize("action", [ps.CarryOver.RESTORE_FROM_DESTINATION, ps.CarryOver.FRESH])
    def test_other_plans_copy_nothing(self, tmp_path: Path, action: ps.CarryOver) -> None:
        shared = tmp_path / "shared" / "github"
        shared.mkdir(parents=True)
        (shared / "state.json").write_text("{}")
        plan = ps.StatePlan("github", action, "", shared, tmp_path / "project" / "github")

        ps.carry_over(plan)

        assert not plan.project_dir.exists()


class TestProjectPipelinesEnv:
    def test_points_dlt_at_the_project_and_restores_the_env(self, tmp_path: Path) -> None:
        with ps.project_pipelines_env(tmp_path) as pipelines:
            assert pipelines == ps.project_pipelines_dir(tmp_path)
            assert os.environ["DLT_DATA_DIR"] == str(ps.project_dlt_data_dir(tmp_path))
            from dlt.common.pipeline import get_dlt_pipelines_dir

            assert Path(get_dlt_pipelines_dir()) == pipelines
        assert "DLT_DATA_DIR" not in os.environ

    def test_restores_the_env_after_an_error(self, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError), ps.project_pipelines_env(tmp_path):
            raise RuntimeError("boom")
        assert "DLT_DATA_DIR" not in os.environ

    def test_keeps_its_directory_out_of_git(self, tmp_path: Path) -> None:
        with ps.project_pipelines_env(tmp_path):
            pass
        assert (ps.project_dlt_data_dir(tmp_path) / ".gitignore").read_text().splitlines()[-1] == "*"

    def test_leaves_a_users_own_dlt_data_dir_alone(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DLT_DATA_DIR", str(tmp_path / "mine"))

        with ps.project_pipelines_env(tmp_path / "project") as pipelines:
            assert pipelines is None
            assert os.environ["DLT_DATA_DIR"] == str(tmp_path / "mine")
        assert not (tmp_path / "project").exists()


class TestUpgradeDoesNotDuplicateRows:
    """The issue's repro, followed by the first run after the upgrade."""

    def test_polluted_shared_cursor_is_not_carried_over(self, tmp_path: Path) -> None:
        a_db, b_db = tmp_path / "a.duckdb", tmp_path / "b.duckdb"
        _run(a_db, "raw_a", "a", 10)
        _run(b_db, "raw_b", "b", 5)

        plan = _run_in_project(tmp_path / "project_a", a_db, "raw_a", "a", 12)

        assert plan.action is ps.CarryOver.RESTORE_FROM_DESTINATION
        assert _rows(a_db, "raw_a") == (12, 12)

    def test_shared_dir_today_loads_duplicates(self, tmp_path: Path) -> None:
        a_db, b_db = tmp_path / "a.duckdb", tmp_path / "b.duckdb"
        _run(a_db, "raw_a", "a", 10)
        _run(b_db, "raw_b", "b", 5)
        _run(a_db, "raw_a", "a", 12)

        assert _rows(a_db, "raw_a") == (17, 12)

    @pytest.mark.parametrize(
        ("restore", "expected"),
        [("true", ps.CarryOver.COPY), ("false", ps.CarryOver.COPY_UNVERIFIED)],
    )
    def test_single_project_keeps_its_cursor(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, restore: str, expected: ps.CarryOver
    ) -> None:
        monkeypatch.setenv("RESTORE_FROM_DESTINATION", restore)
        a_db = tmp_path / "a.duckdb"
        _run(a_db, "raw_a", "a", 10)

        plan = _run_in_project(tmp_path / "project_a", a_db, "raw_a", "a", 12)

        assert plan.action is expected
        assert _rows(a_db, "raw_a") == (12, 12)

    @pytest.mark.parametrize("restore", ["true", "false"])
    def test_second_project_starts_from_its_own_state(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, restore: str
    ) -> None:
        monkeypatch.setenv("RESTORE_FROM_DESTINATION", restore)
        a_db, b_db = tmp_path / "a.duckdb", tmp_path / "b.duckdb"
        _run(a_db, "raw_a", "a", 10)

        plan = _run_in_project(tmp_path / "project_b", b_db, "raw_b", "b", 5)

        assert plan.action is ps.CarryOver.FRESH
        assert _rows(b_db, "raw_b") == (5, 5)
        assert (ps.shared_pipelines_dir() / "github" / "state.json").is_file()
