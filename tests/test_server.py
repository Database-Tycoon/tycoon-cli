"""Tests for the FastAPI server app and routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tycoon.server.app import create_app
from tycoon.server.subprocess_manager import SubprocessManager


@pytest.fixture
def client():
    """Create a FastAPI TestClient."""
    application = create_app()
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
