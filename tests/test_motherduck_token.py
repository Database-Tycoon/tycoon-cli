"""Commands refuse an md: target with no token instead of starting a browser sign-in (#460).

Every test points ``HOME`` at a temporary directory and clears both token
variables, so the developer's own ``~/.duckdb/motherduck_token`` and
environment are never read, and ``duckdb.connect`` on an ``md:`` target is
faked or forbidden: nothing here reaches MotherDuck.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
import typer

from tycoon import motherduck
from tycoon.cli import app
from tycoon.motherduck import has_motherduck_token, missing_token_message, require_motherduck_token


@pytest.fixture
def home(tmp_path: Path, monkeypatch) -> Path:
    """An empty HOME and no token in the environment."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("MOTHERDUCK_TOKEN", raising=False)
    monkeypatch.delenv("motherduck_token", raising=False)
    return home


def _store_token(home: Path, content: str = "stored-token\n") -> Path:
    path = home / ".duckdb" / "motherduck_token"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def _flat(output: str) -> str:
    return " ".join(output.split())


class TestHasMotherDuckToken:
    def test_nothing_available(self, home):
        assert not has_motherduck_token("md:x")

    @pytest.mark.parametrize("name", ["MOTHERDUCK_TOKEN", "motherduck_token"])
    def test_environment_variable(self, home, monkeypatch, name):
        monkeypatch.setenv(name, "env-token")
        assert has_motherduck_token("md:x")

    def test_blank_environment_variable_is_not_a_token(self, home, monkeypatch):
        monkeypatch.setenv("MOTHERDUCK_TOKEN", "  ")
        assert not has_motherduck_token("md:x")

    @pytest.mark.parametrize(
        "target",
        [
            "md:x?motherduck_token=abc",
            "motherduck:x?motherduck_token=abc",
            "md:x?attach_mode=single&motherduck_token=abc",
            "md:x?MOTHERDUCK_TOKEN=abc",
        ],
    )
    def test_token_in_the_connection_string(self, home, target):
        assert has_motherduck_token(target)

    @pytest.mark.parametrize("target", ["md:x?motherduck_token=", "md:x?motherduck_token=&a=b", "md:motherduck_token"])
    def test_empty_or_misplaced_token_in_the_string_is_not_a_token(self, home, target):
        assert not has_motherduck_token(target)

    def test_stored_token_file_is_not_a_token(self, home):
        # DuckDB 1.5.4 still opens the browser sign-in with only this file present.
        _store_token(home)
        assert not has_motherduck_token("md:x")


class TestRequireMotherDuckToken:
    @pytest.mark.parametrize(
        "target", ["data/warehouse.duckdb", "/abs/md:backup/warehouse.duckdb", "C:\\data\\w.duckdb", ":memory:"]
    )
    def test_local_targets_never_reach_the_lookup(self, home, monkeypatch, target):
        def forbidden(_target: str) -> bool:
            raise AssertionError("a local target must not look for a MotherDuck token")

        monkeypatch.setattr(motherduck, "has_motherduck_token", forbidden)
        require_motherduck_token(target)

    @pytest.mark.parametrize("target", ["md:x", "motherduck:x", "MD:x"])
    def test_motherduck_target_without_a_token_exits_1(self, home, target, capsys):
        with pytest.raises(typer.Exit) as exc:
            require_motherduck_token(target)
        assert exc.value.exit_code == 1
        assert "MOTHERDUCK_TOKEN" in _flat(capsys.readouterr().err)

    def test_motherduck_target_with_a_token_returns(self, home, monkeypatch):
        monkeypatch.setenv("MOTHERDUCK_TOKEN", "env-token")
        require_motherduck_token("md:x")

    def test_message_is_one_line_and_drops_the_query_string(self):
        message = missing_token_message("md:x?attach_mode=single")
        assert "\n" not in message
        assert "md:x" in message
        assert "attach_mode" not in message
        assert "MOTHERDUCK_TOKEN" in message


def _project(tmp_path: Path, monkeypatch, warehouse: str = "data/warehouse.duckdb", raw: str = "data/raw.duckdb"):
    from tycoon.config import TycoonConfig

    root = tmp_path / "project"
    root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname = "test"\n')
    (root / "tycoon.yml").write_text(
        f"name: test\nsources: {{}}\ndatabase:\n  warehouse: '{warehouse}'\n  raw: '{raw}'\n"
    )
    monkeypatch.setattr("tycoon.commands.db.config", TycoonConfig(project_root=root))
    return root


@pytest.fixture
def connects(monkeypatch) -> list[str]:
    """Record every duckdb.connect; an md: target gets an in-memory database instead of MotherDuck."""
    calls: list[str] = []
    real_connect = duckdb.connect

    def fake_connect(database: str = ":memory:", **kwargs):
        calls.append(str(database))
        if str(database).lower().startswith(("md:", "motherduck:")):
            return real_connect(":memory:")
        return real_connect(database, **kwargs)

    monkeypatch.setattr(duckdb, "connect", fake_connect)
    return calls


def _md_calls(calls: list[str]) -> list[str]:
    return [c for c in calls if c.lower().startswith(("md:", "motherduck:"))]


class TestDataQuery:
    @pytest.mark.parametrize(
        ("args", "warehouse", "raw"),
        [
            ([], "md:x", "data/raw.duckdb"),
            ([], "motherduck:x", "data/raw.duckdb"),
            (["--raw"], "data/warehouse.duckdb", "md:x_raw"),
        ],
    )
    def test_no_token_exits_1_without_connecting(
        self, tmp_path, monkeypatch, home, connects, cli_runner, args, warehouse, raw
    ):
        _project(tmp_path, monkeypatch, warehouse=warehouse, raw=raw)
        result = cli_runner.invoke(app, ["data", "query", *args, "SELECT 1"])
        assert result.exit_code == 1
        assert "MOTHERDUCK_TOKEN" in _flat(result.output)
        assert connects == []

    def test_token_in_environment_connects(self, tmp_path, monkeypatch, home, connects, cli_runner):
        _project(tmp_path, monkeypatch, warehouse="md:x")
        monkeypatch.setenv("MOTHERDUCK_TOKEN", "env-token")
        result = cli_runner.invoke(app, ["data", "query", "SELECT 1"])
        assert result.exit_code == 0, result.output
        assert connects == ["md:x"]

    def test_token_in_connection_string_connects(self, tmp_path, monkeypatch, home, connects, cli_runner):
        _project(tmp_path, monkeypatch, warehouse="md:x?motherduck_token=abc")
        result = cli_runner.invoke(app, ["data", "query", "SELECT 1"])
        assert result.exit_code == 0, result.output
        assert connects == ["md:x?motherduck_token=abc"]

    def test_stored_token_file_alone_exits_1_without_connecting(
        self, tmp_path, monkeypatch, home, connects, cli_runner
    ):
        _project(tmp_path, monkeypatch, warehouse="md:x")
        _store_token(home)
        result = cli_runner.invoke(app, ["data", "query", "SELECT 1"])
        assert result.exit_code == 1
        assert "No MotherDuck token for" in _flat(result.output)
        assert connects == []

    def test_local_warehouse_needs_no_token(self, tmp_path, monkeypatch, home, connects, cli_runner):
        root = _project(tmp_path, monkeypatch)
        (root / "data").mkdir()
        duckdb.connect(str(root / "data" / "warehouse.duckdb")).close()
        connects.clear()
        result = cli_runner.invoke(app, ["data", "query", "SELECT 1"])
        assert result.exit_code == 0, result.output
        assert connects == [str(root / "data" / "warehouse.duckdb")]


class TestDataSchema:
    @pytest.mark.parametrize(
        ("warehouse", "raw"),
        [("md:x", "data/raw.duckdb"), ("data/warehouse.duckdb", "md:x_raw"), ("md:x", "md:x_raw")],
    )
    def test_no_token_exits_1_without_connecting(
        self, tmp_path, monkeypatch, home, connects, cli_runner, warehouse, raw
    ):
        _project(tmp_path, monkeypatch, warehouse=warehouse, raw=raw)
        result = cli_runner.invoke(app, ["data", "schema"])
        assert result.exit_code == 1
        assert "MOTHERDUCK_TOKEN" in _flat(result.output)
        assert _md_calls(connects) == []

    def test_local_project_needs_no_token(self, tmp_path, monkeypatch, home, connects, cli_runner):
        _project(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["data", "schema"])
        assert result.exit_code == 0, result.output
        assert _md_calls(connects) == []


class TestDataSync:
    @pytest.fixture
    def synced(self, tmp_path, monkeypatch) -> list[list[str]]:
        """Run from a project directory and record what sync_to_local was asked to copy, without running it."""
        root = tmp_path / "sync_project"
        root.mkdir()
        (root / "tycoon.yml").write_text(
            "name: test\nsources: {}\ndatabase:\n  raw: data/raw.duckdb\n  warehouse: data/warehouse.duckdb\n"
            "sync:\n  to: data/snapshot.duckdb\n  sources:\n    - from: 'md:prod'\n"
        )
        monkeypatch.chdir(root)
        calls: list[list[str]] = []

        def fake_sync(sources, to, mode="replace"):
            from tycoon.sync import SyncResult

            calls.append([s.from_ for s in sources])
            return SyncResult(dest=to)

        monkeypatch.setattr("tycoon.commands.sync_cmd.sync_to_local", fake_sync)
        return calls

    @pytest.mark.parametrize("source", ["md:prod", "motherduck:prod"])
    def test_no_token_exits_1_before_syncing(self, home, connects, synced, cli_runner, tmp_path, source):
        result = cli_runner.invoke(
            app, ["data", "sync", "--from", str(tmp_path / "local.duckdb"), "--from", source, "--to", "snap.duckdb"]
        )
        assert result.exit_code == 1
        assert "MOTHERDUCK_TOKEN" in _flat(result.output)
        assert synced == []
        assert connects == []

    def test_no_token_with_sources_from_tycoon_yml_exits_1(self, home, connects, synced, cli_runner):
        result = cli_runner.invoke(app, ["data", "sync"])
        assert result.exit_code == 1
        assert "MOTHERDUCK_TOKEN" in _flat(result.output)
        assert synced == []

    def test_env_token_lets_an_existing_sync_block_run(self, home, monkeypatch, synced, cli_runner):
        monkeypatch.setenv("MOTHERDUCK_TOKEN", "env-token")
        result = cli_runner.invoke(app, ["data", "sync"])
        assert result.exit_code == 0, result.output
        assert synced == [["md:prod"]]

    def test_token_in_the_source_string_is_enough(self, home, synced, cli_runner):
        result = cli_runner.invoke(app, ["data", "sync", "--from", "md:prod?motherduck_token=abc", "--to", "s.duckdb"])
        assert result.exit_code == 0, result.output
        assert synced == [["md:prod?motherduck_token=abc"]]

    def test_local_source_needs_no_token(self, home, synced, cli_runner, tmp_path):
        result = cli_runner.invoke(app, ["data", "sync", "--from", str(tmp_path / "a.duckdb"), "--to", "s.duckdb"])
        assert result.exit_code == 0, result.output
        assert synced == [[str(tmp_path / "a.duckdb")]]
