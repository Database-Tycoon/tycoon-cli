"""Tests for tycoon.project — tycoon.yml parsing and validation."""

from __future__ import annotations

import os

from tycoon.project import TycoonProject, SourceConfig, DatabaseConfig, load_project, save_project


class TestTycoonProject:

    def test_default_project(self):
        p = TycoonProject()
        assert p.name == "my-project"
        assert p.version == "0.1.0"
        assert p.database.raw == "data/raw.duckdb"
        assert p.database.warehouse == "data/warehouse.duckdb"
        assert p.sources == {}

    def test_custom_project(self):
        p = TycoonProject(
            name="test-project",
            database=DatabaseConfig(raw="my/raw.db", warehouse="my/wh.db"),
            sources={
                "my-source": SourceConfig(
                    type="rest_api",
                    schema="raw_test",
                    config={"base_url": "https://example.com"},
                ),
            },
        )
        assert p.name == "test-project"
        assert p.database.raw == "my/raw.db"
        assert len(p.sources) == 1
        assert p.sources["my-source"].type == "rest_api"
        assert p.sources["my-source"].schema_name == "raw_test"


class TestLoadSave:

    def test_load_missing_file_returns_none(self, tmp_path):
        assert load_project(tmp_path) is None

    def test_round_trip(self, tmp_path):
        project = TycoonProject(
            name="round-trip",
            sources={
                "src1": SourceConfig(type="sql_database", schema="raw_src1"),
            },
        )
        save_project(project, tmp_path)
        loaded = load_project(tmp_path)
        assert loaded is not None
        assert loaded.name == "round-trip"
        assert "src1" in loaded.sources
        assert loaded.sources["src1"].type == "sql_database"

    def test_env_var_interpolation(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TEST_DB_PATH", "custom/my.duckdb")
        yml = tmp_path / "tycoon.yml"
        yml.write_text(
            "name: env-test\n"
            "database:\n"
            "  raw: ${TEST_DB_PATH}\n"
            "  warehouse: data/wh.duckdb\n"
        )
        loaded = load_project(tmp_path)
        assert loaded is not None
        assert loaded.database.raw == "custom/my.duckdb"

    def test_env_var_with_default(self, tmp_path):
        yml = tmp_path / "tycoon.yml"
        yml.write_text(
            "name: default-test\n"
            "database:\n"
            "  raw: ${NONEXISTENT_VAR:-fallback/raw.duckdb}\n"
            "  warehouse: data/wh.duckdb\n"
        )
        loaded = load_project(tmp_path)
        assert loaded is not None
        assert loaded.database.raw == "fallback/raw.duckdb"


class TestConfigIntegration:

    def test_config_reads_tycoon_yml(self, tmp_path):
        from tycoon.config import TycoonConfig

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        yml = tmp_path / "tycoon.yml"
        yml.write_text(
            "name: integration-test\n"
            "database:\n"
            "  raw: data/custom_raw.duckdb\n"
            "  warehouse: data/custom_wh.duckdb\n"
        )
        cfg = TycoonConfig(project_root=tmp_path)
        assert cfg.has_project_file
        assert cfg.raw_db == tmp_path / "data" / "custom_raw.duckdb"
        assert cfg.local_db == tmp_path / "data" / "custom_wh.duckdb"

    def test_config_falls_back_without_tycoon_yml(self, tmp_path):
        from tycoon.config import TycoonConfig

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        cfg = TycoonConfig(project_root=tmp_path)
        assert not cfg.has_project_file
        assert "raw.duckdb" in str(cfg.raw_db)

    def test_config_sources_empty_without_yml(self, tmp_path):
        from tycoon.config import TycoonConfig

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        cfg = TycoonConfig(project_root=tmp_path)
        assert cfg.sources == {}

    def test_config_sources_from_yml(self, tmp_path):
        from tycoon.config import TycoonConfig

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "tycoon.yml").write_text(
            "name: src-test\n"
            "sources:\n"
            "  my-api:\n"
            "    type: rest_api\n"
            "    schema: raw_api\n"
        )
        cfg = TycoonConfig(project_root=tmp_path)
        assert "my-api" in cfg.sources
