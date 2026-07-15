"""Tests for constants module — ports and generic defaults."""

from __future__ import annotations

from tycoon import constants


class TestPorts:

    def test_ports_are_integers(self):
        for name, port in constants.PORTS.items():
            assert isinstance(port, int), f"Port for {name} should be int"

    def test_ports_are_unique(self):
        values = list(constants.PORTS.values())
        assert len(values) == len(set(values)), "All ports must be unique"

    def test_expected_keys_present(self):
        expected_keys = {"duckdb_ui", "dbt_docs", "rill"}
        assert expected_keys.issubset(set(constants.PORTS.keys()))


class TestSocrataDefaults:

    def test_page_size_is_positive_int(self):
        assert isinstance(constants.SOCRATA_PAGE_SIZE, int)
        assert constants.SOCRATA_PAGE_SIZE > 0
