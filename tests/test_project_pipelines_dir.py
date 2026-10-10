"""Each project runs its dlt pipelines in its own working directory (gh-394).

The source under test is a catalog source whose installed ``_run.py`` shim
builds its own ``dlt.pipeline`` without a ``pipelines_dir``, the shape every
shim already installed in a project has. Every test runs with a temporary
HOME, so dlt's shared directory is ``<tmp>/home/.dlt/pipelines``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

import tycoon.config as cfg_mod
from tycoon.config import TycoonConfig
from tycoon.ingestion import pipeline_state as ps
from tycoon.ingestion import runner
from tycoon.project import SourceConfig

_SHIM = """\
import dlt


def run_pipeline(name, source_config, raw_db_path, max_records=None):
    project = source_config.config["project"]
    upto = int(source_config.config["upto"])

    @dlt.resource(name="events", write_disposition="append")
    def events(cursor=dlt.sources.incremental("id", initial_value=0)):
        yield [{"id": i, "project": project} for i in range(1, upto + 1) if i > cursor.start_value]

    pipeline = dlt.pipeline(
        pipeline_name=name,
        destination=dlt.destinations.duckdb(str(raw_db_path)),
        dataset_name=source_config.schema_name,
    )
    return pipeline, pipeline.run(events())
"""


@pytest.fixture(autouse=True)
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sys_path_copy: None) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    for var in ("DLT_DATA_DIR", "XDG_DATA_HOME", "RESTORE_FROM_DESTINATION"):
        monkeypatch.delenv(var, raising=False)
    for module in ("github", "github._run"):
        monkeypatch.delitem(sys.modules, module, raising=False)

    sources_dir = tmp_path / "sources"
    (sources_dir / "github").mkdir(parents=True)
    (sources_dir / "github" / "__init__.py").write_text("")
    (sources_dir / "github" / "_run.py").write_text(_SHIM)
    monkeypatch.setattr(runner, "resolve_sources_dir", lambda _root: sources_dir)
    monkeypatch.setattr(runner, "_capture_and_refresh_safe", lambda *_a, **_k: None)
    return home


def _project(tmp_path: Path, name: str, monkeypatch: pytest.MonkeyPatch) -> TycoonConfig:
    root = tmp_path / name
    root.mkdir(exist_ok=True)
    cfg = TycoonConfig(project_root=root)
    monkeypatch.setattr(cfg_mod, "config", cfg)
    return cfg


def _source(project: str, upto: int) -> SourceConfig:
    return SourceConfig(type="github", schema="raw_github", config={"project": project, "upto": str(upto)})


def _run(cfg: TycoonConfig, project: str, upto: int) -> None:
    runner.run_source("github", _source(project, upto), cfg.root / "raw.duckdb")


def _run_before_upgrade(cfg: TycoonConfig, project: str, upto: int) -> None:
    """Run the shim the way tycoon did before gh-394, in dlt's shared directory."""
    runner._run_catalog("github", "github", _source(project, upto), cfg.root / "raw.duckdb")


def _rows(cfg: TycoonConfig) -> tuple[int, int]:
    con = duckdb.connect(str(cfg.root / "raw.duckdb"), read_only=True)
    try:
        row = con.execute("SELECT count(*), count(DISTINCT id) FROM raw_github.events").fetchone()
    finally:
        con.close()
    assert row is not None
    return row[0], row[1]


def test_same_named_sources_in_two_projects_load_no_duplicates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    a = _project(tmp_path, "project_a", monkeypatch)
    _run(a, "a", 10)
    b = _project(tmp_path, "project_b", monkeypatch)
    _run(b, "b", 5)
    _run(b, "b", 6)
    a = _project(tmp_path, "project_a", monkeypatch)
    _run(a, "a", 12)

    assert _rows(a) == (12, 12)
    assert _rows(b) == (6, 6)


def test_the_shared_dir_before_the_upgrade_loads_duplicates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    a = _project(tmp_path, "project_a", monkeypatch)
    _run_before_upgrade(a, "a", 10)
    b = _project(tmp_path, "project_b", monkeypatch)
    _run_before_upgrade(b, "b", 5)
    _run_before_upgrade(b, "b", 6)
    a = _project(tmp_path, "project_a", monkeypatch)
    _run_before_upgrade(a, "a", 12)

    assert _rows(a) == (16, 12)


def test_runs_in_the_project_dir_and_leaves_the_env_as_it_was(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated: Path
) -> None:
    a = _project(tmp_path, "project_a", monkeypatch)
    _run(a, "a", 3)

    assert (ps.project_pipelines_dir(a.root) / "github" / "state.json").is_file()
    assert not (isolated / ".dlt" / "pipelines" / "github").exists()
    assert "DLT_DATA_DIR" not in os.environ


def test_first_run_after_upgrade_ignores_a_cursor_another_project_moved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated: Path
) -> None:
    a = _project(tmp_path, "project_a", monkeypatch)
    _run_before_upgrade(a, "a", 10)
    b = _project(tmp_path, "project_b", monkeypatch)
    _run_before_upgrade(b, "b", 5)
    _run_before_upgrade(b, "b", 6)
    shared_state = (isolated / ".dlt" / "pipelines" / "github" / "state.json").read_bytes()

    a = _project(tmp_path, "project_a", monkeypatch)
    _run(a, "a", 12)

    assert _rows(a) == (12, 12)
    assert (isolated / ".dlt" / "pipelines" / "github" / "state.json").read_bytes() == shared_state


def test_first_run_after_upgrade_keeps_a_single_projects_cursor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated: Path
) -> None:
    a = _project(tmp_path, "project_a", monkeypatch)
    _run_before_upgrade(a, "a", 10)

    _run(a, "a", 12)

    assert _rows(a) == (12, 12)
    assert (isolated / ".dlt" / "pipelines" / "github" / "state.json").is_file()


def test_a_users_dlt_data_dir_is_left_alone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mine = tmp_path / "my_dlt"
    monkeypatch.setenv("DLT_DATA_DIR", str(mine))
    a = _project(tmp_path, "project_a", monkeypatch)

    _run(a, "a", 3)

    assert (mine / "pipelines" / "github" / "state.json").is_file()
    assert not ps.project_dlt_data_dir(a.root).exists()


def test_unreadable_raw_database_fails_the_run_without_touching_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    a = _project(tmp_path, "project_a", monkeypatch)
    _run_before_upgrade(a, "a", 3)
    (a.root / "raw.duckdb").unlink()
    (a.root / "raw.duckdb").write_text("not a duckdb file")

    with pytest.raises(runner.IngestionError, match="Nothing was changed"):
        _run(a, "a", 5)
    assert not ps.project_dlt_data_dir(a.root).exists()


class TestDoctor:
    def _messages(self, monkeypatch: pytest.MonkeyPatch, cfg: TycoonConfig) -> list[tuple[str, str]]:
        from tycoon.commands import doctor

        seen: list[tuple[str, str]] = []
        for level in ("info", "warn", "success"):
            monkeypatch.setattr(doctor, level, lambda msg, _level=level: seen.append((_level, msg)))
        monkeypatch.setattr(doctor, "config", cfg)
        doctor._check_dlt_state()
        return seen

    def _with_source(self, cfg: TycoonConfig) -> TycoonConfig:
        (cfg.root / "tycoon.yml").write_text(
            "name: demo\ndatabase:\n  raw: raw.duckdb\nsources:\n  github:\n    type: github\n    schema: raw_github\n"
        )
        return TycoonConfig(project_root=cfg.root)

    def test_reports_the_carry_over_the_next_run_will_do(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        a = _project(tmp_path, "project_a", monkeypatch)
        _run_before_upgrade(a, "a", 10)
        b = _project(tmp_path, "project_b", monkeypatch)
        _run_before_upgrade(b, "b", 5)
        _run_before_upgrade(b, "b", 6)

        messages = self._messages(monkeypatch, self._with_source(a))

        assert len(messages) == 1
        level, msg = messages[0]
        assert level == "info"
        assert "dlt state for 'github': the next run will restore its state from the raw database" in msg

    def test_reports_ok_once_the_project_has_its_own_state(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        a = _project(tmp_path, "project_a", monkeypatch)
        _run_before_upgrade(a, "a", 10)
        _run(a, "a", 12)

        messages = self._messages(monkeypatch, self._with_source(a))

        assert messages == [("success", f"dlt state: kept per project in {ps.project_pipelines_dir(a.root)}.")]

    def test_warns_when_dlt_data_dir_is_shared(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DLT_DATA_DIR", str(tmp_path / "shared"))
        a = _project(tmp_path, "project_a", monkeypatch)

        messages = self._messages(monkeypatch, self._with_source(a))

        assert [level for level, _ in messages] == ["warn"]
        assert "DLT_DATA_DIR is set" in messages[0][1]


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
class TestKeptOutOfGit:
    def _ignored(self, repo: Path, path: str) -> bool:
        result = subprocess.run(["git", "check-ignore", "-q", path], cwd=repo, check=False)
        return result.returncode == 0

    def test_scaffolded_gitignore_ignores_the_dlt_dir(self, tmp_path: Path) -> None:
        from tycoon.scaffolding.templates import _GITIGNORE_CONTENT

        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
        (tmp_path / ".gitignore").write_text(_GITIGNORE_CONTENT)

        assert self._ignored(tmp_path, ".tycoon/dlt/pipelines/github/state.json")

    def test_existing_project_without_the_entry_is_still_covered(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
        (tmp_path / ".gitignore").write_text(".env\n")
        with ps.project_pipelines_env(tmp_path):
            pass
        state = ps.project_pipelines_dir(tmp_path) / "github" / "state.json"
        state.parent.mkdir(parents=True)
        state.write_text("{}")

        assert self._ignored(tmp_path, str(state.relative_to(tmp_path)))
