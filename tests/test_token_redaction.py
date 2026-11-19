"""A MotherDuck token in a connection string never reaches tycoon's output (gh-510).

`md:analytics?motherduck_token=<secret>` is a supported source form. These
tests drive `data sync` and `tycoon city` with one and check the secret is
absent from what they print. Nothing here connects to MotherDuck: the sync and
the renderer are replaced by fakes, and the one real sync reads a local file.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from tycoon.cli import app
from tycoon.project import SyncSourceSpec
from tycoon.sync import SyncedTable, SyncResult, sync_to_local

SECRET = "SEKRET-gh510"
SOURCE = f"md:analytics?motherduck_token={SECRET}"


@pytest.fixture
def project(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / "tycoon.yml").write_text(
        "name: test\nversion: 0.1.0\ndatabase:\n  raw: data/raw.duckdb\n"
        "  warehouse: data/warehouse.duckdb\nsources: {}\n"
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _output(result) -> str:
    return (result.stdout or "") + (result.stderr or "")


class TestSyncOutput:
    def test_copied_table_lines_drop_the_query_string(self, project, cli_runner, monkeypatch):
        def fake_sync(sources, to, mode):
            return SyncResult(dest=Path(to), tables=[SyncedTable(source=SOURCE, schema="mart", table="t", rows=3)])

        monkeypatch.setattr("tycoon.commands.sync_cmd.sync_to_local", fake_sync)
        result = cli_runner.invoke(app, ["data", "sync", "--from", SOURCE, "--to", "snap.duckdb"])
        out = _output(result)
        assert result.exit_code == 0, out
        assert SECRET not in out
        assert "rows from md:analytics" in out

    def test_sync_failed_message_is_redacted(self, project, cli_runner, monkeypatch):
        def failing_sync(sources, to, mode):
            raise RuntimeError(f"Catalog Error: could not attach '{SOURCE}'")

        monkeypatch.setattr("tycoon.commands.sync_cmd.sync_to_local", failing_sync)
        result = cli_runner.invoke(app, ["data", "sync", "--from", SOURCE, "--to", "snap.duckdb"])
        out = _output(result)
        assert result.exit_code == 1
        assert SECRET not in out
        assert "Sync failed" in out

    def test_skip_reason_is_redacted_before_it_is_cut(self, tmp_path, monkeypatch):
        src = tmp_path / "src.duckdb"
        with duckdb.connect(str(src)) as con:
            con.execute("CREATE SCHEMA mart")
            con.execute("CREATE TABLE mart.t AS SELECT 1 AS id")

        def broken_copy(*args, **kwargs):
            raise duckdb.CatalogException(f"view references {SOURCE}")

        monkeypatch.setattr("tycoon.sync._copy_one", broken_copy)
        result = sync_to_local([SyncSourceSpec(**{"from": str(src)})], tmp_path / "out.duckdb", mode="replace")
        assert len(result.skipped) == 1
        assert SECRET not in result.skipped[0].reason
        assert "md:analytics" in result.skipped[0].reason


def test_city_serving_line_drops_the_query_string(project, cli_runner, monkeypatch):
    served: list[list[str]] = []

    def fake_serve(argv):
        served.append(argv)
        return 0

    monkeypatch.setattr("tycoon_city.webserve.main", fake_serve)
    result = cli_runner.invoke(app, ["city", "--path", SOURCE])
    out = _output(result)
    assert SECRET not in out
    assert "Serving md:analytics" in out
    # The renderer still gets the full string: the token is needed to connect.
    assert served and served[0][0] == SOURCE
