"""Tests for tycoon.yml security validation.

Covers #62 (allowlist-scoped ${VAR} interpolation) and #65 (identifier
constraints on source/schema/table names + path containment for
dbt_project_dir / rill_dir).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from tycoon.config import TycoonConfig
from tycoon.project import SourceConfig, TycoonProject, load_project


def _write_yml(root: Path, body: str) -> None:
    (root / "tycoon.yml").write_text(body)


class TestInterpolationAllowlist:
    """#62 — ${VAR} expands only in credential/path fields; elsewhere it stays literal."""

    def test_database_paths_expand(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TYCOON_TEST_DB", "custom/raw.duckdb")
        _write_yml(tmp_path, "database:\n  raw: ${TYCOON_TEST_DB}\n")
        loaded = load_project(tmp_path)
        assert loaded is not None
        assert loaded.database.raw == "custom/raw.duckdb"

    def test_source_config_values_expand(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TYCOON_TEST_TOKEN", "tok_123")
        _write_yml(
            tmp_path,
            "sources:\n"
            "  github:\n"
            "    type: rest_api\n"
            "    schema: raw_github\n"
            "    config:\n"
            "      token: ${TYCOON_TEST_TOKEN}\n",
        )
        loaded = load_project(tmp_path)
        assert loaded is not None
        assert loaded.sources["github"].config["token"] == "tok_123"

    def test_nested_source_config_values_expand(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TYCOON_TEST_URL", "https://api.example.com")
        _write_yml(
            tmp_path,
            "sources:\n"
            "  api:\n"
            "    type: rest_api\n"
            "    schema: raw_api\n"
            "    config:\n"
            "      client:\n"
            "        base_url: ${TYCOON_TEST_URL}\n",
        )
        loaded = load_project(tmp_path)
        assert loaded is not None
        assert loaded.sources["api"].config["client"]["base_url"] == "https://api.example.com"

    def test_sync_source_uri_expands(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TYCOON_TEST_CATALOG", "md:prod_catalog")
        _write_yml(
            tmp_path,
            "sync:\n"
            "  sources:\n"
            "    - from: ${TYCOON_TEST_CATALOG}\n",
        )
        loaded = load_project(tmp_path)
        assert loaded is not None
        assert loaded.sync is not None
        assert loaded.sync.sources[0].from_ == "md:prod_catalog"

    def test_project_name_stays_literal(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MOTHERDUCK_TOKEN_TEST_ONLY", "sekrit-token")
        _write_yml(tmp_path, "name: ${MOTHERDUCK_TOKEN_TEST_ONLY}\n")
        loaded = load_project(tmp_path)
        assert loaded is not None
        assert loaded.name == "${MOTHERDUCK_TOKEN_TEST_ONLY}"

    def test_notify_label_stays_literal(self, tmp_path, monkeypatch):
        # notify.label flows into the webhook payload — a prime exfil target.
        monkeypatch.setenv("AWS_SECRET_TEST_ONLY", "aws-sekrit")
        _write_yml(tmp_path, "notify:\n  label: ${AWS_SECRET_TEST_ONLY}\n")
        loaded = load_project(tmp_path)
        assert loaded is not None
        assert loaded.notify.label == "${AWS_SECRET_TEST_ONLY}"
        assert "aws-sekrit" not in (loaded.notify.label or "")

    def test_default_syntax_in_allowed_field(self, tmp_path):
        _write_yml(
            tmp_path,
            "sources:\n"
            "  api:\n"
            "    type: rest_api\n"
            "    schema: raw_api\n"
            "    config:\n"
            "      token: ${TYCOON_UNSET_VAR_XYZ:-fallback-token}\n",
        )
        loaded = load_project(tmp_path)
        assert loaded is not None
        assert loaded.sources["api"].config["token"] == "fallback-token"

    def test_default_syntax_in_blocked_field_stays_literal(self, tmp_path):
        _write_yml(tmp_path, "version: ${TYCOON_UNSET_VAR_XYZ:-1.2.3}\n")
        loaded = load_project(tmp_path)
        assert loaded is not None
        assert loaded.version == "${TYCOON_UNSET_VAR_XYZ:-1.2.3}"


class TestSourceNameValidation:
    """#65 — source map keys must be identifier-safe (hyphens allowed for CLI/template UX)."""

    def test_underscore_and_hyphen_names_accepted(self):
        p = TycoonProject(
            sources={
                "my_api": SourceConfig(type="rest_api", schema="raw_my_api"),
                "nyc-dot": SourceConfig(type="rest_api", schema="raw_nyc_dot"),
            }
        )
        assert set(p.sources) == {"my_api", "nyc-dot"}

    @pytest.mark.parametrize(
        "bad_name",
        [
            "../evil",
            "foo'); DROP TABLE users; --",
            "a/b",
            "źródło",
            "name with spaces",
            "-leading-hyphen",
            "1starts_with_digit",
            "",
        ],
    )
    def test_malicious_source_names_rejected(self, bad_name):
        with pytest.raises(ValidationError, match="source name"):
            TycoonProject(
                sources={bad_name: SourceConfig(type="rest_api", schema="raw_x")}
            )

    def test_error_names_offending_key(self):
        with pytest.raises(ValidationError, match=r"\.\./evil"):
            TycoonProject(
                sources={"../evil": SourceConfig(type="rest_api", schema="raw_x")}
            )

    def test_rejected_at_load_time(self, tmp_path):
        _write_yml(
            tmp_path,
            "sources:\n"
            "  ../escape:\n"
            "    type: rest_api\n"
            "    schema: raw_x\n",
        )
        with pytest.raises(ValidationError, match="source name"):
            load_project(tmp_path)


class TestSchemaAndTableValidation:
    """#65 — schema/table names become SQL identifiers; constrain accordingly."""

    def test_valid_schema_accepted(self):
        src = SourceConfig(type="rest_api", schema="raw_github")
        assert src.schema_name == "raw_github"

    @pytest.mark.parametrize(
        "bad_schema",
        ["raw; DROP TABLE x", "../etc", "raw-hyphen", "raw schema", "1raw", ""],
    )
    def test_malicious_schema_rejected(self, bad_schema):
        with pytest.raises(ValidationError, match="schema"):
            SourceConfig(type="rest_api", schema=bad_schema)

    def test_valid_tables_accepted(self):
        src = SourceConfig(type="sql_database", schema="raw_db", tables=["users", "orders"])
        assert src.tables == ["users", "orders"]

    @pytest.mark.parametrize(
        "bad_table",
        ["users'); --", "../../secrets", "users; DROP", "tab le"],
    )
    def test_malicious_table_rejected(self, bad_table):
        with pytest.raises(ValidationError, match="table"):
            SourceConfig(type="sql_database", schema="raw_db", tables=[bad_table])


class TestPathContainment:
    """#65 — dbt_project_dir / rill_dir must resolve within the project's parent dir."""

    @staticmethod
    def _make_project(root: Path, **fields: str) -> TycoonConfig:
        root.mkdir(parents=True, exist_ok=True)
        lines = "".join(f"{k}: {v}\n" for k, v in fields.items())
        (root / "tycoon.yml").write_text(f"name: containment-test\n{lines}")
        return TycoonConfig(project_root=root)

    def test_in_project_dbt_dir_accepted(self, tmp_path):
        cfg = self._make_project(tmp_path / "proj", dbt_project_dir="dbt_project")
        assert cfg.dbt_project_dir == (tmp_path / "proj" / "dbt_project").resolve()

    def test_sibling_dbt_dir_accepted(self, tmp_path):
        # The init wizard's default layout: dbt lives NEXT TO the project root.
        cfg = self._make_project(tmp_path / "proj", dbt_project_dir="../proj-dbt")
        assert cfg.dbt_project_dir == (tmp_path / "proj-dbt").resolve()

    def test_absolute_system_path_rejected(self, tmp_path):
        cfg = self._make_project(tmp_path / "proj", dbt_project_dir="/etc/cron.d")
        with pytest.raises(ValueError, match="dbt_project_dir"):
            _ = cfg.dbt_project_dir

    def test_traversal_beyond_parent_rejected(self, tmp_path):
        cfg = self._make_project(tmp_path / "proj", dbt_project_dir="../../../escape")
        with pytest.raises(ValueError, match="outside the project's parent"):
            _ = cfg.dbt_project_dir

    def test_rill_dir_traversal_rejected(self, tmp_path):
        cfg = self._make_project(tmp_path / "proj", rill_dir="../../../../rill")
        with pytest.raises(ValueError, match="rill_dir"):
            _ = cfg.rill_dir

    def test_rill_dir_sibling_accepted(self, tmp_path):
        cfg = self._make_project(tmp_path / "proj", rill_dir="../proj-rill")
        assert cfg.rill_dir == (tmp_path / "proj-rill").resolve()

    def test_newline_in_path_rejected_at_validation(self):
        with pytest.raises(ValidationError, match="NUL, newline"):
            TycoonProject(dbt_project_dir="dbt\nproject")

    def test_carriage_return_in_rill_dir_rejected(self):
        with pytest.raises(ValidationError, match="NUL, newline"):
            TycoonProject(rill_dir="rill\rdir")

    def test_nul_in_profiles_dir_rejected(self):
        with pytest.raises(ValidationError, match="NUL, newline"):
            TycoonProject(dbt_profiles_dir="profiles\x00dir")


class TestTopLevelProjectBoundary:
    """A project in a top-level dir (/app) must not degrade containment to /."""

    def _config_at(self, root: str):
        from tycoon.config import TycoonConfig

        return TycoonConfig(project_root=Path(root))

    def test_etc_rejected_for_top_level_root(self, monkeypatch):
        cfg = self._config_at("/app")
        cfg._project = TycoonProject(name="t", dbt_project_dir="/etc/cron.d")
        with pytest.raises(ValueError, match="outside"):
            _ = cfg.dbt_project_dir

    def test_in_project_path_accepted_for_top_level_root(self):
        cfg = self._config_at("/app")
        cfg._project = TycoonProject(name="t", dbt_project_dir="dbt")
        assert cfg.dbt_project_dir == Path("/app/dbt")


class TestSourceTypeValidation:
    """SourceConfig.type reaches dlt init argv and filesystem paths."""

    def test_known_types_accepted(self):
        for src_type in ("rest_api", "sql_database", "filesystem", "google_sheets"):
            SourceConfig(type=src_type, schema_name="raw")

    @pytest.mark.parametrize("bad", ["../evil", "rest api", "rest-api", "a;b", "", "1type"])
    def test_unsafe_types_rejected(self, bad):
        with pytest.raises(ValidationError, match="not a valid identifier"):
            SourceConfig(type=bad, schema_name="raw")
