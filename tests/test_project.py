"""Tests for tycoon.project — tycoon.yml parsing and validation."""

from __future__ import annotations

import yaml

from tycoon.project import (
    DatabaseConfig,
    ResourceConfig,
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


class TestSchemaVersionEnforcement:
    """T2-4: load_project is permissive; save_project preserves schema_version."""

    def test_future_schema_version_loads_without_raise(self, tmp_path):
        """load_project must not raise for a future schema_version — the gate
        lives in load_config() so the import-time singleton never trips it."""
        (tmp_path / "tycoon.yml").write_text(f"name: future\nschema_version: {SCHEMA_VERSION + 1}\n")
        p = load_project(tmp_path)
        assert p is not None
        assert p.schema_version == SCHEMA_VERSION + 1

    def test_save_project_preserves_schema_version(self, tmp_path):
        """save_project preserves whatever schema_version is in the model;
        only migrate_project (via init --upgrade) advances the stamp."""
        (tmp_path / "tycoon.yml").write_text(f"name: old\nschema_version: {SCHEMA_VERSION}\n")
        p = load_project(tmp_path)
        assert p is not None
        save_project(p, tmp_path)
        reloaded = load_project(tmp_path)
        assert reloaded is not None
        assert reloaded.schema_version == SCHEMA_VERSION

    def test_save_project_does_not_stamp_when_absent(self, tmp_path):
        """A project with no schema_version on disk stays unstamped after save_project."""
        (tmp_path / "tycoon.yml").write_text("name: old-project\n")
        p = load_project(tmp_path)
        assert p is not None
        assert p.schema_version is None
        save_project(p, tmp_path)
        reloaded = load_project(tmp_path)
        assert reloaded is not None
        assert reloaded.schema_version is None


_COMMENTED_YML = """\
# Project notes: keep this header.
name: commented
version: "0.1.0"

sources:
  api:
    type: rest_api
    schema: raw_api  # inline note on the schema
    config:
      base_url: https://example.com
  files:
    type: filesystem
    schema: raw_files
    resources:
    - table_name: orders  # orders feed
      path: data/orders
      file_glob: "*.csv"
    - table_name: users
      path: data/users
      file_glob: "*.csv"

# Database section comment.
database:
  raw: data/raw.duckdb
  warehouse: data/warehouse.duckdb
"""


class TestSavePreservesFormatting:
    """gh-177: save_project keeps the user's comments, blank lines, and quoting."""

    def test_add_source_keeps_comments_and_blank_lines(self, tmp_path):
        yml = tmp_path / "tycoon.yml"
        yml.write_text(_COMMENTED_YML)
        project = load_project(tmp_path)
        assert project is not None
        project.sources["api2"] = SourceConfig(type="rest_api", schema="raw_api2", config={"base_url": "https://x"})

        save_project(project, tmp_path)

        on_disk = yml.read_text()
        assert on_disk.startswith("# Project notes: keep this header.\n")
        assert "schema: raw_api  # inline note on the schema" in on_disk
        assert "- table_name: orders  # orders feed" in on_disk
        assert "# Database section comment." in on_disk
        assert "\n\n" in on_disk
        assert 'version: "0.1.0"' in on_disk
        reloaded = load_project(tmp_path)
        assert reloaded is not None
        assert reloaded.sources["api2"].schema_name == "raw_api2"

    def test_remove_source_keeps_unrelated_comments(self, tmp_path):
        yml = tmp_path / "tycoon.yml"
        yml.write_text(_COMMENTED_YML)
        project = load_project(tmp_path)
        assert project is not None
        del project.sources["api"]

        save_project(project, tmp_path)

        on_disk = yml.read_text()
        assert "raw_api" not in on_disk
        assert "inline note on the schema" not in on_disk
        assert on_disk.startswith("# Project notes: keep this header.\n")
        assert "- table_name: orders  # orders feed" in on_disk
        assert "# Database section comment." in on_disk

    def test_editing_a_resource_keeps_its_siblings(self, tmp_path):
        yml = tmp_path / "tycoon.yml"
        yml.write_text(_COMMENTED_YML)
        project = load_project(tmp_path)
        assert project is not None
        resources = project.sources["files"].resources
        assert resources is not None
        resources[1] = ResourceConfig(table_name="users", path="data/people", file_glob="*.csv")

        save_project(project, tmp_path)

        on_disk = yml.read_text()
        assert "path: data/people" in on_disk
        assert "- table_name: orders  # orders feed" in on_disk
        assert 'file_glob: "*.csv"' in on_disk

    def test_unchanged_save_is_a_byte_for_byte_noop(self, tmp_path):
        yml = tmp_path / "tycoon.yml"
        yml.write_text(_COMMENTED_YML)
        save_project(TycoonProject.model_validate(yaml.safe_load(_COMMENTED_YML)), tmp_path)
        first = yml.read_text()
        project = load_project(tmp_path)
        assert project is not None

        save_project(project, tmp_path)

        assert yml.read_text() == first

    def test_env_ref_survives_a_save(self, tmp_path, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "tok-123")
        yml = tmp_path / "tycoon.yml"
        yml.write_text(
            "name: env\nsources:\n  api:\n    type: rest_api\n    schema: raw_api\n"
            "    config:\n      token: ${API_TOKEN}\n"
        )
        project = load_project(tmp_path)
        assert project is not None
        project.name = "env-renamed"

        save_project(project, tmp_path)

        on_disk = yml.read_text()
        assert "token: ${API_TOKEN}" in on_disk
        assert "tok-123" not in on_disk

    def test_saved_key_set_matches_a_fresh_file(self, tmp_path):
        project = TycoonProject(
            name="keys",
            sources={"api": SourceConfig(type="rest_api", schema="raw_api", config={"base_url": "https://x"})},
        )
        fresh_dir = tmp_path / "fresh"
        fresh_dir.mkdir()
        save_project(project, fresh_dir)
        (tmp_path / "tycoon.yml").write_text("# minimal hand-written file\nname: keys\n")

        save_project(project, tmp_path)

        fresh = yaml.safe_load((fresh_dir / "tycoon.yml").read_text())
        assert fresh == project.model_dump(by_alias=True, exclude_none=True, mode="json")
        assert yaml.safe_load((tmp_path / "tycoon.yml").read_text()) == fresh

    def test_removing_the_last_source_keeps_the_next_section_comment(self, tmp_path):
        yml = tmp_path / "tycoon.yml"
        yml.write_text(_COMMENTED_YML)
        project = load_project(tmp_path)
        assert project is not None
        del project.sources["files"]

        save_project(project, tmp_path)

        on_disk = yml.read_text()
        assert "raw_files" not in on_disk
        assert "      base_url: https://example.com\n\n# Database section comment.\ndatabase:\n" in on_disk

    def test_removing_every_source_keeps_the_next_section_comment(self, tmp_path):
        yml = tmp_path / "tycoon.yml"
        yml.write_text(_COMMENTED_YML)
        project = load_project(tmp_path)
        assert project is not None
        project.sources.clear()

        save_project(project, tmp_path)

        assert "sources: {}\n\n# Database section comment.\ndatabase:\n" in yml.read_text()

    def test_adding_a_source_keeps_the_next_section_comment_in_place(self, tmp_path):
        yml = tmp_path / "tycoon.yml"
        yml.write_text(_COMMENTED_YML)
        project = load_project(tmp_path)
        assert project is not None
        project.sources["api2"] = SourceConfig(type="rest_api", schema="raw_api2", config={"base_url": "https://x"})

        save_project(project, tmp_path)

        on_disk = yml.read_text()
        assert "  api2:\n" in on_disk
        assert "    schema: raw_api2\n\n# Database section comment.\ndatabase:\n" in on_disk
        before, after = on_disk.split("# Database section comment.")
        assert "api2" in before
        assert after.startswith("\ndatabase:\n  raw: data/raw.duckdb\n")

    def test_edit_changes_only_the_edited_line(self, tmp_path):
        long_url = "https://example.com/" + "a" * 90 + "?page=1"
        original = _COMMENTED_YML.replace("https://example.com", long_url).replace("    - ", "      - ")
        original = original.replace("      path: data", "        path: data").replace(
            '      file_glob: "*.csv"', '        file_glob: "*.csv"'
        )
        yml = tmp_path / "tycoon.yml"
        yml.write_text(original)
        # The first save fills in the model's defaults; start from that.
        save_project(TycoonProject.model_validate(yaml.safe_load(original)), tmp_path)
        before = yml.read_text()
        project = load_project(tmp_path)
        assert project is not None
        project.version = "0.2.0"

        save_project(project, tmp_path)

        on_disk = yml.read_text()
        assert f"      base_url: {long_url}\n" in on_disk
        assert "      - table_name: orders  # orders feed\n" in on_disk
        assert on_disk == before.replace('version: "0.1.0"', 'version: "0.2.0"')

    def test_unchanged_file_round_trips_byte_for_byte(self, tmp_path):
        from tycoon.yaml_merge import roundtrip_yaml

        ryaml = roundtrip_yaml(_COMMENTED_YML)
        doc = ryaml.load(_COMMENTED_YML)
        out = tmp_path / "out.yml"
        with out.open("w") as f:
            ryaml.dump(doc, f)

        assert out.read_text() == _COMMENTED_YML

    def test_env_refs_survive_add_and_remove(self, tmp_path, monkeypatch):
        monkeypatch.setenv("FAKE_TOKEN", "fake-tok")
        monkeypatch.setenv("FAKE_URL", "https://fake.invalid")
        yml = tmp_path / "tycoon.yml"
        yml.write_text(
            "name: env\nsources:\n  api:\n    type: rest_api\n    schema: raw_api\n"
            "    config:\n      base_url: ${FAKE_URL}\n      token: ${FAKE_TOKEN}\n"
        )
        project = load_project(tmp_path)
        assert project is not None
        project.sources["extra"] = SourceConfig(type="rest_api", schema="raw_extra", config={"base_url": "https://x"})
        save_project(project, tmp_path)
        project = load_project(tmp_path)
        assert project is not None
        del project.sources["extra"]

        save_project(project, tmp_path)

        on_disk = yml.read_text()
        assert "base_url: ${FAKE_URL}" in on_disk
        assert "token: ${FAKE_TOKEN}" in on_disk
        assert "fake-tok" not in on_disk
        assert "fake.invalid" not in on_disk
        assert "extra" not in on_disk


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

        (tmp_path / "tycoon.yml").write_text(f"name: future-project\nschema_version: {SCHEMA_VERSION + 1}\n")

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
