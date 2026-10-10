"""Regression tests for issue #240: a local glob that matches no files must
not run a "replace" load, which would truncate a table that already holds
rows while every signal reports success."""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path

import duckdb
import pytest

from tycoon.cli import app
from tycoon.ingestion.runner import run_source
from tycoon.project import ResourceConfig, SourceConfig
from tests.test_templates_e2e import _init_template, _rebind_config, _seed_widgets_csv


def _row_count(raw_db_path: Path, schema: str, table: str) -> int:
    con = duckdb.connect(str(raw_db_path), read_only=True)
    try:
        row = con.execute(f'SELECT count(*) FROM {schema}."{table}"').fetchone()
    finally:
        con.close()
    assert row is not None
    return row[0]


def _write_csv(path: Path, rows: int) -> None:
    lines = ["id,value"] + [f"{i},v{i}" for i in range(1, rows + 1)]
    path.write_text("\n".join(lines) + "\n")


@pytest.fixture
def pipeline_cleanup() -> Iterator[list[str]]:
    names: list[str] = []
    yield names
    for name in names:
        shutil.rmtree(Path.home() / ".dlt" / "pipelines" / name, ignore_errors=True)


class TestEmptyGlobLeavesTableUntouched:
    def test_empty_glob_rerun_keeps_previously_loaded_rows(self, tmp_path, pipeline_cleanup, capsys):
        name = "test_gh240_sales"
        pipeline_cleanup.append(name)
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        _write_csv(input_dir / "sales.csv", rows=10)
        raw_db_path = tmp_path / "raw.duckdb"

        first = SourceConfig(
            type="filesystem", schema="raw_files", config={"path": str(input_dir), "file_glob": "*.csv"}
        )
        run_source(name, first, raw_db_path=raw_db_path)
        assert _row_count(raw_db_path, "raw_files", name) == 10

        typo = SourceConfig(
            type="filesystem", schema="raw_files", config={"path": str(input_dir), "file_glob": "nomatch*.csv"}
        )
        _pipeline, load_info = run_source(name, typo, raw_db_path=raw_db_path)

        assert _row_count(raw_db_path, "raw_files", name) == 10
        assert load_info is None
        assert "left as it was" in capsys.readouterr().out

    def test_empty_glob_under_file_url_keeps_previously_loaded_rows(self, tmp_path, pipeline_cleanup):
        """A ``file://`` bucket is local, so the empty-glob guard applies to it too."""
        name = "test_gh240_file_url"
        pipeline_cleanup.append(name)
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        _write_csv(input_dir / "sales.csv", rows=6)
        raw_db_path = tmp_path / "raw.duckdb"

        def config(file_glob: str) -> SourceConfig:
            return SourceConfig(
                type="filesystem", schema="raw_files", config={"path": input_dir.as_uri(), "file_glob": file_glob}
            )

        run_source(name, config("*.csv"), raw_db_path=raw_db_path)
        assert _row_count(raw_db_path, "raw_files", name) == 6

        _pipeline, load_info = run_source(name, config("nomatch*.csv"), raw_db_path=raw_db_path)

        assert load_info is None
        assert _row_count(raw_db_path, "raw_files", name) == 6

    def test_one_empty_resource_does_not_stop_the_others(self, tmp_path, pipeline_cleanup):
        name = "test_gh240_arcade"
        pipeline_cleanup.append(name)
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        _write_csv(input_dir / "games.csv", rows=2)
        _write_csv(input_dir / "players.csv", rows=4)
        raw_db_path = tmp_path / "raw.duckdb"

        def arcade(players_glob: str) -> SourceConfig:
            return SourceConfig(
                type="filesystem",
                schema="raw_arcade",
                resources=[
                    ResourceConfig(table_name="test_gh240_games", path=str(input_dir), file_glob="games.csv"),
                    ResourceConfig(table_name="test_gh240_players", path=str(input_dir), file_glob=players_glob),
                ],
            )

        run_source(name, arcade("players.csv"), raw_db_path=raw_db_path)
        _write_csv(input_dir / "games.csv", rows=3)
        _pipeline, load_info = run_source(name, arcade("nomatch*.csv"), raw_db_path=raw_db_path)

        assert load_info is not None
        assert _row_count(raw_db_path, "raw_arcade", "test_gh240_games") == 3
        assert _row_count(raw_db_path, "raw_arcade", "test_gh240_players") == 4


@pytest.mark.offline_e2e
def test_sources_run_reports_nothing_to_load(cli_runner, tmp_path, monkeypatch):
    """The CLI exits 0 but says "nothing to load" instead of "load complete"
    once the input directory has emptied out."""
    project = tmp_path / "csv-import-empty"
    project.mkdir()
    monkeypatch.chdir(project)
    _init_template(cli_runner, "csv-import")
    input_dir = project / "data" / "input"
    _seed_widgets_csv(input_dir, count=5)
    _rebind_config(monkeypatch, project)
    try:
        assert cli_runner.invoke(app, ["data", "sources", "run", "files"]).exit_code == 0
        for csv in input_dir.glob("*.csv"):
            csv.unlink()

        result = cli_runner.invoke(app, ["data", "sources", "run", "files"])

        assert result.exit_code == 0
        assert "nothing to load" in result.stdout
        assert "load complete" not in result.stdout
        assert _row_count(project / "data" / "files_raw.duckdb", "raw_files", "files") == 5
    finally:
        shutil.rmtree(Path.home() / ".dlt" / "pipelines" / "files", ignore_errors=True)
