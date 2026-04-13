"""Tests for service definitions and the ServiceManager."""

from __future__ import annotations

from tycoon.services.definitions import ServiceDef, get_service_definitions
from tycoon.services.manager import ServiceManager


class TestServiceDefinitions:

    def test_returns_list(self):
        defs = get_service_definitions()
        assert isinstance(defs, list)

    def test_returns_service_def_objects(self):
        defs = get_service_definitions()
        for sd in defs:
            assert isinstance(sd, ServiceDef)

    def test_each_service_has_name_port_command(self):
        defs = get_service_definitions()
        for sd in defs:
            assert isinstance(sd.name, str) and len(sd.name) > 0
            assert isinstance(sd.port, int)
            assert isinstance(sd.command, list)

    def test_expected_services_present(self):
        defs = get_service_definitions()
        names = {sd.name for sd in defs}
        # These should always be present regardless of filesystem state
        for expected in ("duckdb_ui", "dbt_docs", "rill", "tycoon"):
            assert expected in names, f"Expected service '{expected}' not found"


class TestServiceManager:

    def test_can_instantiate(self):
        manager = ServiceManager()
        assert manager is not None

    def test_service_names_returns_list(self):
        manager = ServiceManager()
        names = manager.service_names
        assert isinstance(names, list)
        assert len(names) > 0

    def test_health_returns_bool(self):
        manager = ServiceManager()
        # health check on a known service (should return False since nothing is running)
        result = manager.health("rill")
        assert isinstance(result, bool)

    def test_health_unknown_service_returns_false(self):
        manager = ServiceManager()
        assert manager.health("nonexistent_service") is False
