"""Tests for tycoon.project — tycoon.yml parsing and validation."""

from __future__ import annotations

from tycoon.project import (
    DatabaseConfig,
    SCHEMA_VERSION,
    SourceConfig,
    TycoonProject,
    load_project,
    migrate_project,
    save_project,
)


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
        yml.write_text("name: env-test\ndatabase:\n  raw: ${TEST_DB_PATH}\n  warehouse: data/wh.duckdb\n")
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

    def test_save_does_not_leak_fivetran_secret_or_flatten_env_ref(self, tmp_path, monkeypatch):
        """save_project must never write the expanded Fivetran secret back to
        disk, nor mask it to ``**********`` — the hand-authored env-ref block
        is preserved verbatim (regression for #60)."""
        monkeypatch.setenv("FIVETRAN_API_SECRET", "super-secret-value")
        yml = tmp_path / "tycoon.yml"
        yml.write_text(
            "name: ft\n"
            "stack:\n"
            "  ingestion: fivetran\n"
            "  ingestion_metadata:\n"
            "    api_key: ak_123\n"
            "    api_secret: ${FIVETRAN_API_SECRET}\n"
            "    group_id: grp_1\n"
        )
        loaded = load_project(tmp_path)
        assert loaded is not None
        assert loaded.stack.ingestion_metadata is not None
        # In-memory the secret is expanded for use, but masked in any repr.
        assert loaded.stack.ingestion_metadata.api_secret.get_secret_value() == "super-secret-value"
        assert "super-secret-value" not in repr(loaded.stack.ingestion_metadata)

        # A subsequent save (e.g. triggered by `sources add`) must keep the
        # on-disk block exactly as authored.
        save_project(loaded, tmp_path)
        on_disk = yml.read_text()
        assert "${FIVETRAN_API_SECRET}" in on_disk
        assert "super-secret-value" not in on_disk  # no expanded-secret leak
        assert "**********" not in on_disk  # not corrupted by SecretStr masking


class TestConfigIntegration:
    def test_config_reads_tycoon_yml(self, tmp_path):
        from tycoon.config import TycoonConfig

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        yml = tmp_path / "tycoon.yml"
        yml.write_text(
            "name: integration-test\ndatabase:\n  raw: data/custom_raw.duckdb\n  warehouse: data/custom_wh.duckdb\n"
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
            "name: src-test\nsources:\n  my-api:\n    type: rest_api\n    schema: raw_api\n"
        )
        cfg = TycoonConfig(project_root=tmp_path)
        assert "my-api" in cfg.sources


class TestRuntimesAndMetadata:
    """T2-1: runtimes: and metadata: fields on TycoonProject."""

    def test_existing_yml_loads_without_new_fields(self, tmp_path):
        """A tycoon.yml with no runtimes/metadata keys must load with defaults."""
        (tmp_path / "tycoon.yml").write_text("name: legacy-project\n")
        p = load_project(tmp_path)
        assert p is not None
        assert p.runtimes == {}
        assert p.metadata.backend == "duckdb_file"
        assert p.metadata.path == ".tycoon/metadata.duckdb"

    def test_runtimes_field_parses(self, tmp_path):
        """runtimes: block with mixed types should parse into RuntimeEntry objects."""
        (tmp_path / "tycoon.yml").write_text(
            "name: runtimes-test\n"
            "runtimes:\n"
            "  shopify:\n"
            "    type: dlt-managed\n"
            "  custom_pipeline:\n"
            "    type: dlt-project\n"
            "    path: pipelines/custom\n"
            "  fivetran_sync:\n"
            "    type: fivetran\n"
        )
        p = load_project(tmp_path)
        assert p is not None
        assert set(p.runtimes) == {"shopify", "custom_pipeline", "fivetran_sync"}
        assert p.runtimes["shopify"].type == "dlt-managed"
        assert p.runtimes["shopify"].path is None
        assert p.runtimes["custom_pipeline"].type == "dlt-project"
        assert p.runtimes["custom_pipeline"].path == "pipelines/custom"
        assert p.runtimes["fivetran_sync"].type == "fivetran"

    def test_metadata_field_parses(self, tmp_path):
        """metadata: block with custom values should override defaults."""
        (tmp_path / "tycoon.yml").write_text(
            "name: metadata-test\nmetadata:\n  backend: duckdb_file\n  path: .tycoon/custom_meta.duckdb\n"
        )
        p = load_project(tmp_path)
        assert p is not None
        assert p.metadata.backend == "duckdb_file"
        assert p.metadata.path == ".tycoon/custom_meta.duckdb"


class TestMigrateProject:
    """T2-2: migrate_project writes missing keys and is idempotent."""

    def test_missing_metadata_block_is_written(self, tmp_path):
        """A yml without metadata: gets it added and schema_version stamped."""
        (tmp_path / "tycoon.yml").write_text("name: old-project\nversion: 1.4.2\n")

        modified = migrate_project(tmp_path)

        assert modified is True
        p = load_project(tmp_path)
        assert p is not None
        assert p.metadata.backend == "duckdb_file"
        assert p.metadata.path == ".tycoon/metadata.duckdb"
        assert p.schema_version == SCHEMA_VERSION

    def test_user_version_not_overwritten(self, tmp_path):
        """migrate_project never touches the user's version field."""
        (tmp_path / "tycoon.yml").write_text("name: old-project\nversion: 1.4.2\n")

        migrate_project(tmp_path)
        p = load_project(tmp_path)

        assert p is not None
        assert p.version == "1.4.2"

    def test_comments_preserved(self, tmp_path):
        """Comments and blank lines survive the ruamel.yaml round-trip."""
        original = "# Project config\nname: acme\n\n# owner: data-platform@acme.com\nversion: 1.0.0\n"
        (tmp_path / "tycoon.yml").write_text(original)

        migrate_project(tmp_path)
        result = (tmp_path / "tycoon.yml").read_text()

        assert "# Project config" in result
        assert "# owner: data-platform@acme.com" in result

    def test_second_call_is_no_op(self, tmp_path):
        """Running migrate_project twice returns False on the second call."""
        (tmp_path / "tycoon.yml").write_text("name: old-project\nversion: 0.1.0\n")

        migrate_project(tmp_path)
        modified_again = migrate_project(tmp_path)

        assert modified_again is False

    def test_already_migrated_yml_is_unchanged(self, tmp_path):
        """A yml that already has metadata: and schema_version is left alone."""
        (tmp_path / "tycoon.yml").write_text(
            f"name: current-project\nschema_version: {SCHEMA_VERSION}\n"
            "metadata:\n  backend: duckdb_file\n  path: .tycoon/metadata.duckdb\n"
        )

        modified = migrate_project(tmp_path)

        assert modified is False

    def test_future_schema_version_raises(self, tmp_path):
        """A yml with schema_version newer than SCHEMA_VERSION raises ValueError."""
        import pytest

        (tmp_path / "tycoon.yml").write_text(
            f"name: future-project\nschema_version: {SCHEMA_VERSION + 1}\n"
        )

        with pytest.raises(ValueError, match="newer than this tycoon supports"):
            migrate_project(tmp_path)

    def test_non_integer_schema_version_raises(self, tmp_path):
        """A float schema_version (e.g. 0.2 unquoted in YAML) raises ValueError."""
        import pytest

        (tmp_path / "tycoon.yml").write_text("name: bad-project\nschema_version: 0.2\n")

        with pytest.raises(ValueError, match="must be an integer"):
            migrate_project(tmp_path)

    def test_missing_file_returns_false(self, tmp_path):
        """migrate_project on a directory with no tycoon.yml returns False."""
        assert migrate_project(tmp_path) is False
