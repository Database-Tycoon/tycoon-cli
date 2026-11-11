"""The city refuses an md: catalog with no token instead of starting a browser sign-in (#460).

HOME points at a temporary directory and both token variables are cleared, so
the developer's own token is never read, and `duckdb.connect` is replaced by a
function that fails the test: nothing here reaches MotherDuck.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from tycoon_city import webserve
from tycoon_city.catalog.errors import CatalogError
from tycoon_city.export import build
from tycoon_city.export.build import build_city, require_motherduck_token
from tycoon_city.export.cli import main as export_main


@pytest.fixture
def home(tmp_path: Path, monkeypatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("MOTHERDUCK_TOKEN", raising=False)
    monkeypatch.delenv("motherduck_token", raising=False)
    return home


@pytest.fixture
def no_connect(monkeypatch) -> list[str]:
    calls: list[str] = []

    def forbidden(database=":memory:", *args, **kwargs):
        calls.append(str(database))
        raise AssertionError(f"duckdb.connect({database!r}) must not run")

    monkeypatch.setattr(duckdb, "connect", forbidden)
    return calls


def _store_token(home: Path, content: str = "stored-token\n") -> None:
    path = home / ".duckdb" / "motherduck_token"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


class TestRequireMotherDuckToken:
    @pytest.mark.parametrize("source", ["md:my_db", "motherduck:my_db", "MD:my_db", "MotherDuck:my_db"])
    def test_no_token_raises_naming_the_variable(self, home, source):
        with pytest.raises(CatalogError, match="MOTHERDUCK_TOKEN"):
            require_motherduck_token(source)

    def test_motherduck_prefix_with_a_token_in_the_string(self, home):
        require_motherduck_token("motherduck:my_db?motherduck_token=abc")

    def test_message_drops_the_query_string(self, home):
        with pytest.raises(CatalogError) as exc:
            require_motherduck_token("md:my_db?attach_mode=single")
        assert "attach_mode" not in str(exc.value)
        assert "md:my_db" in str(exc.value)

    @pytest.mark.parametrize("name", ["MOTHERDUCK_TOKEN", "motherduck_token"])
    def test_environment_token(self, home, monkeypatch, name):
        monkeypatch.setenv(name, "env-token")
        require_motherduck_token("md:my_db")

    def test_token_in_the_connection_string(self, home):
        require_motherduck_token("md:my_db?motherduck_token=abc")

    def test_empty_token_in_the_connection_string_is_not_a_token(self, home):
        with pytest.raises(CatalogError):
            require_motherduck_token("md:my_db?motherduck_token=")

    def test_stored_token_file_is_not_a_token(self, home):
        # DuckDB 1.5.4 still opens the browser sign-in with only this file present.
        _store_token(home)
        with pytest.raises(CatalogError, match="MOTHERDUCK_TOKEN"):
            require_motherduck_token("md:my_db")

    @pytest.mark.parametrize("source", ["/tmp/warehouse.duckdb", "/abs/md:backup/w.duckdb", "demo_project"])
    def test_local_sources_never_reach_the_lookup(self, home, monkeypatch, source):
        def forbidden(_source: str) -> bool:
            raise AssertionError("a local source must not look for a MotherDuck token")

        monkeypatch.setattr(build, "_has_motherduck_token", forbidden)
        require_motherduck_token(source)
        require_motherduck_token(Path(source))


def test_build_city_refuses_before_connecting(home, no_connect):
    with pytest.raises(CatalogError, match="MOTHERDUCK_TOKEN"):
        build_city("md:my_db", style_rules=[])
    assert no_connect == []


def test_export_exits_1_before_connecting(home, no_connect, tmp_path, capsys):
    assert export_main(["md:my_db", str(tmp_path / "out")]) == 1
    assert "MOTHERDUCK_TOKEN" in capsys.readouterr().err
    assert no_connect == []


class TestRunServer:
    def _run(self, monkeypatch, tmp_path: Path, db_path: str) -> list[str]:
        served: list[str] = []
        monkeypatch.setattr(webserve, "serve", lambda db, *args, **kwargs: served.append(db))
        dist = tmp_path / "dist"
        dist.mkdir()
        code = webserve.run_server(db_path=db_path, dist=dist, theme="default", pricing=None, port=0, host="127.0.0.1")
        return [str(code), *served]

    @pytest.mark.parametrize("source", ["md:my_db", "motherduck:my_db", "MD:my_db"])
    def test_no_token_exits_1_and_never_serves(self, home, no_connect, monkeypatch, tmp_path, capsys, source):
        assert self._run(monkeypatch, tmp_path, source) == ["1"]
        err = capsys.readouterr().err
        assert "MOTHERDUCK_TOKEN" in err
        assert len(err.strip().splitlines()) == 1
        assert no_connect == []

    def test_stored_token_file_alone_exits_1_and_never_serves(self, home, no_connect, monkeypatch, tmp_path):
        _store_token(home)
        assert self._run(monkeypatch, tmp_path, "md:my_db") == ["1"]
        assert no_connect == []

    def test_environment_token_serves(self, home, no_connect, monkeypatch, tmp_path):
        monkeypatch.setenv("MOTHERDUCK_TOKEN", "env-token")
        assert self._run(monkeypatch, tmp_path, "md:my_db") == ["0", "md:my_db"]

    def test_local_file_needs_no_token(self, home, no_connect, monkeypatch, tmp_path):
        assert self._run(monkeypatch, tmp_path, str(tmp_path / "w.duckdb")) == ["0", str(tmp_path / "w.duckdb")]
