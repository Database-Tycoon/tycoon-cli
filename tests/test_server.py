"""Tests for the FastAPI server app and routes."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from tycoon.server.app import create_app
from tycoon.server.subprocess_manager import RunInfo, SubprocessManager


@pytest.fixture
def client():
    """Create a FastAPI TestClient for the top-level app."""
    application = create_app()
    return TestClient(application)


@pytest.fixture
def routes_client():
    """Create a TestClient for the /api routes + websocket endpoints."""
    from fastapi import FastAPI

    from tycoon.server import routes, websocket

    application = FastAPI()
    application.include_router(routes.router)
    application.include_router(websocket.router)
    return TestClient(application)


class TestRootEndpoint:

    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_json(self, client):
        response = client.get("/")
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_ok(self, client):
        data = client.get("/health").json()
        assert data["status"] == "ok"


class TestCheckUpdatesEndpoint:
    """`/check-updates` queries PyPI; mock httpx to stay offline in tests."""

    def test_update_available(self, client, monkeypatch):
        import tycoon.server.app as app_mod

        fake_response = MagicMock()
        fake_response.raise_for_status.return_value = None
        fake_response.json.return_value = {"info": {"version": "999.999.999"}}
        fake_get = MagicMock(return_value=fake_response)
        monkeypatch.setattr(app_mod, "__version__", "0.1.2", raising=False)
        # httpx is imported inside the route; patch at module level
        import httpx

        monkeypatch.setattr(httpx, "get", fake_get)

        data = client.get("/check-updates").json()
        assert data["update_available"] is True
        assert data["latest_version"] == "999.999.999"

    def test_http_error_returned_gracefully(self, client, monkeypatch):
        import httpx

        def boom(*args, **kwargs):
            raise httpx.HTTPError("upstream down")

        monkeypatch.setattr(httpx, "get", boom)

        data = client.get("/check-updates").json()
        assert "error" in data
        assert "upstream down" in data["error"]


# ---------------------------------------------------------------------------
# /api/status — the dashboard's main polling endpoint
# ---------------------------------------------------------------------------


class TestStatusRoute:

    def test_status_returns_expected_top_level_keys(self, routes_client):
        data = routes_client.get("/api/status").json()
        for key in ("project", "sources", "services", "databases", "dbt", "busy", "active_run_id"):
            assert key in data

    def test_status_busy_false_when_no_active_run(self, routes_client):
        from tycoon.server.subprocess_manager import subprocess_manager

        # Fresh state: no active run
        subprocess_manager._active_run_id = None  # type: ignore[attr-defined]

        data = routes_client.get("/api/status").json()
        assert data["busy"] is False

    def test_status_services_include_configured_ports(self, routes_client):
        from tycoon.constants import PORTS

        data = routes_client.get("/api/status").json()
        for name, port in PORTS.items():
            assert name in data["services"]
            assert data["services"][name]["port"] == port


# ---------------------------------------------------------------------------
# /api/run/pipeline/{source_name} — input validation paths
# ---------------------------------------------------------------------------


class TestRunPipelineRoute:

    def test_unknown_source_returns_404(self, routes_client, monkeypatch):
        from tycoon.server import routes as routes_mod
        from tycoon.server.subprocess_manager import subprocess_manager

        subprocess_manager._active_run_id = None  # type: ignore[attr-defined]

        # Empty sources map
        fake_config = MagicMock()
        fake_config.sources = {}
        monkeypatch.setattr(routes_mod, "config", fake_config)

        response = routes_client.post("/api/run/pipeline/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_busy_returns_409(self, routes_client, monkeypatch):
        from tycoon.server.subprocess_manager import subprocess_manager

        # Inject a fake active run that looks busy
        fake_run = MagicMock()
        fake_run.process.returncode = None
        subprocess_manager._runs["fake"] = fake_run  # type: ignore[attr-defined]
        subprocess_manager._active_run_id = "fake"  # type: ignore[attr-defined]

        try:
            response = routes_client.post("/api/run/pipeline/whatever")
            assert response.status_code == 409
        finally:
            subprocess_manager._active_run_id = None  # type: ignore[attr-defined]
            subprocess_manager._runs.pop("fake", None)  # type: ignore[attr-defined]


class TestRunDbtRoute:

    def test_busy_returns_409(self, routes_client):
        from tycoon.server.subprocess_manager import subprocess_manager

        fake_run = MagicMock()
        fake_run.process.returncode = None
        subprocess_manager._runs["fake2"] = fake_run  # type: ignore[attr-defined]
        subprocess_manager._active_run_id = "fake2"  # type: ignore[attr-defined]

        try:
            response = routes_client.post("/api/run/dbt")
            assert response.status_code == 409
        finally:
            subprocess_manager._active_run_id = None  # type: ignore[attr-defined]
            subprocess_manager._runs.pop("fake2", None)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Websocket: /ws/logs/{run_id}
# ---------------------------------------------------------------------------


class TestLogsWebsocket:
    """Exercises the websocket streaming endpoint via TestClient.websocket_connect."""

    def test_unknown_run_id_closes_with_error(self, routes_client):
        from tycoon.server.subprocess_manager import subprocess_manager

        # Clean state: no runs registered
        subprocess_manager._runs.clear()  # type: ignore[attr-defined]

        with routes_client.websocket_connect("/ws/logs/unknown-id") as ws:
            msg = ws.receive_text()
            assert "unknown run_id" in msg

    def test_finished_run_replays_buffered_lines_and_closes(self, routes_client):
        from tycoon.server.subprocess_manager import subprocess_manager

        fake_process = MagicMock()
        fake_process.returncode = 0  # already exited
        fake_process.stdout = None
        run = RunInfo(
            run_id="done-1",
            cmd=["echo"],
            process=fake_process,
            log_lines=["line-a", "line-b"],
            finished=True,
        )
        subprocess_manager._runs["done-1"] = run  # type: ignore[attr-defined]

        try:
            with routes_client.websocket_connect("/ws/logs/done-1") as ws:
                assert ws.receive_text() == "line-a"
                assert ws.receive_text() == "line-b"
                assert ws.receive_text() == "[done]"
        finally:
            subprocess_manager._runs.pop("done-1", None)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# SubprocessManager — existing coverage plus state transitions
# ---------------------------------------------------------------------------


class TestSubprocessManager:

    def test_initial_not_busy(self):
        manager = SubprocessManager()
        assert manager.is_busy() is False

    def test_initial_no_active_run(self):
        manager = SubprocessManager()
        assert manager.active_run_id is None

    def test_get_run_returns_none_for_unknown(self):
        manager = SubprocessManager()
        assert manager.get_run("nonexistent") is None

    def test_is_busy_flips_false_when_process_exited(self):
        """Busy state should auto-clear once the underlying process returns."""
        manager = SubprocessManager()

        fake_process = MagicMock()
        fake_process.returncode = None
        run = RunInfo(run_id="r1", cmd=["x"], process=fake_process)
        manager._runs["r1"] = run
        manager._active_run_id = "r1"
        assert manager.is_busy() is True

        # Process exits
        fake_process.returncode = 0
        assert manager.is_busy() is False
        assert manager.active_run_id is None
        assert run.finished is True
