"""Tests for DuckDB Quack integration (#42).

Most tests mock the protocol so they're deterministic and offline. One
real serve→attach round-trip runs when the (core_nightly) extension is
available, exercising the actual `quack.connect` SQL.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tycoon import quack
from tycoon.cli import app


# ---------------------------------------------------------------------------
# Token lifecycle
# ---------------------------------------------------------------------------


class TestTokenLifecycle:
    def test_load_returns_none_when_absent(self, tmp_path):
        assert quack.load_token(tmp_path) is None

    def test_ensure_creates_persists_and_is_idempotent(self, tmp_path):
        token = quack.ensure_token(tmp_path)
        assert token
        # Persisted and re-readable.
        assert quack.load_token(tmp_path) == token
        # Idempotent — second call returns the same token, no churn.
        assert quack.ensure_token(tmp_path) == token

    def test_ensure_adds_gitignore_entry(self, tmp_path):
        quack.ensure_token(tmp_path)
        gitignore = (tmp_path / ".gitignore").read_text()
        assert ".tycoon/" in gitignore

    def test_ensure_preserves_other_secret_keys(self, tmp_path):
        import yaml

        path = quack.secrets_path(tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump({"other": {"k": "v"}}))
        quack.ensure_token(tmp_path)
        data = yaml.safe_load(path.read_text())
        assert data["other"] == {"k": "v"}
        assert data["quack"]["token"]


# ---------------------------------------------------------------------------
# Command construction / probes
# ---------------------------------------------------------------------------


class TestServeAndProbes:
    def test_serve_command_shape(self, tmp_path):
        cmd = quack.serve_command(tmp_path / "wh.duckdb", "SEKRIT")
        assert cmd[0] == "duckdb"
        assert "INSTALL quack FROM core_nightly" in cmd[2]
        assert "quack_serve('quack:localhost', token => 'SEKRIT')" in cmd[2]
        assert cmd[-1].endswith("wh.duckdb")

    def test_is_server_running_delegates_to_port_check(self):
        with patch("tycoon.quack.is_port_in_use", return_value=True) as p:
            assert quack.is_server_running() is True
            p.assert_called_once_with(quack.QUACK_PORT)

    def test_extension_available_false_without_binary(self):
        with patch("shutil.which", return_value=None):
            assert quack.extension_available() is False

    def test_extension_available_true_on_clean_load(self):
        ok = MagicMock(returncode=0)
        with patch("shutil.which", return_value="/usr/bin/duckdb"), \
             patch("subprocess.run", return_value=ok):
            assert quack.extension_available() is True

    def test_extension_available_false_on_load_failure(self):
        bad = MagicMock(returncode=1)
        with patch("shutil.which", return_value="/usr/bin/duckdb"), \
             patch("subprocess.run", return_value=bad):
            assert quack.extension_available() is False


# ---------------------------------------------------------------------------
# `tycoon start` preflight folding
# ---------------------------------------------------------------------------


class TestStartPreflight:
    def _bind(self, tmp_path, monkeypatch):
        from tycoon.commands import start as start_mod
        from tycoon.config import TycoonConfig

        monkeypatch.setattr(start_mod, "config", TycoonConfig(project_root=tmp_path))

    def test_quack_dropped_when_extension_unavailable(self, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        from tycoon.commands.start import _preflight_checks

        targets = ["quack"]
        with patch("tycoon.quack.extension_available", return_value=False):
            _preflight_checks(targets)
        assert "quack" not in targets
        # No token written when we bailed.
        assert quack.load_token(tmp_path) is None

    def test_quack_kept_and_token_ensured_when_available(self, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        from tycoon.commands.start import _preflight_checks

        targets = ["quack"]
        with patch("tycoon.quack.extension_available", return_value=True):
            _preflight_checks(targets)
        assert "quack" in targets
        assert quack.load_token(tmp_path) is not None


# ---------------------------------------------------------------------------
# `tycoon data query` attaches via Quack when the server is up
# ---------------------------------------------------------------------------


class TestQueryViaQuack:
    def _bind(self, tmp_path, monkeypatch):
        (tmp_path / "tycoon.yml").write_text(
            "name: t\nversion: 0.1.0\n"
            "database:\n  raw: data/raw.duckdb\n  warehouse: data/warehouse.duckdb\n"
            "sources: {}\n"
        )
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\n')
        from tycoon.commands import db as db_mod
        from tycoon.config import TycoonConfig

        monkeypatch.setattr(db_mod, "config", TycoonConfig(project_root=tmp_path))

    def test_warehouse_query_routes_through_quack(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)

        fake_con = MagicMock()
        fake_con.execute.return_value = fake_con
        fake_con.description = [("answer",)]
        fake_con.fetchall.return_value = [(42,)]

        with patch("tycoon.quack.load_token", return_value="tok"), \
             patch("tycoon.quack.is_server_running", return_value=True), \
             patch("tycoon.quack.connect", return_value=fake_con) as connect:
            result = cli_runner.invoke(app, ["data", "query", "SELECT 42 AS answer"])

        assert result.exit_code == 0, result.output
        connect.assert_called_once_with("tok")
        assert "Quack" in result.output  # label flags the routing

    def test_raw_query_never_uses_quack(self, cli_runner, tmp_path, monkeypatch):
        """--raw is file-based; the Quack server only holds the warehouse."""
        self._bind(tmp_path, monkeypatch)
        with patch("tycoon.quack.connect") as connect, \
             patch("tycoon.quack.is_server_running", return_value=True):
            result = cli_runner.invoke(app, ["data", "query", "SELECT 1", "--raw"])
        # raw.duckdb doesn't exist in the tmp project → file-path error, and we
        # must never have tried to attach via Quack for a --raw query.
        connect.assert_not_called()
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Real serve → attach round-trip (skipped if the extension can't load)
# ---------------------------------------------------------------------------


class TestRealRoundTrip:
    def test_connect_reads_live_warehouse(self):
        if not quack.extension_available():
            pytest.skip("quack extension not available (core_nightly)")
        if quack.is_server_running():
            pytest.skip(f"port {quack.QUACK_PORT} already in use")

        import duckdb

        token = "roundtrip_token"
        srv = duckdb.connect()
        srv.execute(quack._LOAD_QUACK)
        srv.execute("CREATE TABLE hello AS SELECT 42 AS answer, 'world' AS who;")
        srv.execute(f"CALL quack_serve('{quack.QUACK_URI}', token => '{token}');")
        try:
            con = quack.connect(token)
            # Unqualified table name resolves because connect() does `USE`.
            rows = con.execute("SELECT answer, who FROM hello;").fetchall()
            con.close()
            assert rows == [(42, "world")]
        finally:
            srv.execute(f"CALL quack_stop('{quack.QUACK_URI}');")
            srv.close()
