"""Tests for nao_config.yaml generation. Covers issues #5, #9, #10."""

from __future__ import annotations

from pathlib import Path


from tycoon.config import TycoonConfig
from tycoon.nao import (
    AGENTS_MD_SENTINEL,
    _expand_schema_globs,
    build_agents_md,
    build_nao_config,
    write_agents_md,
)
from tycoon.project import (
    AskConfig,
    DatabaseConfig,
    StackConfig,
    TycoonProject,
    WarehouseType,
)


def _make_cfg(
    tmp_path: Path,
    *,
    warehouse: str = "data/warehouse.duckdb",
    warehouse_type: WarehouseType = WarehouseType.duckdb,
    ask: AskConfig | None = None,
) -> TycoonConfig:
    project = TycoonProject(
        name="demo",
        database=DatabaseConfig(raw="data/raw.duckdb", warehouse=warehouse),
        stack=StackConfig(warehouse=warehouse_type),
        ask=ask,
    )
    cfg = TycoonConfig(project_root=tmp_path)
    cfg._project = project  # type: ignore[attr-defined]
    return cfg


class TestWarehousePath:

    def test_local_duckdb_is_relative(self, tmp_path):
        cfg = _make_cfg(tmp_path)
        result = build_nao_config(cfg)
        # .tycoon/nao/ → ../../data/warehouse.duckdb
        assert result["databases"][0]["path"].endswith("data/warehouse.duckdb")
        assert result["databases"][0]["path"].startswith("..")

    def test_motherduck_url_passes_through_verbatim(self, tmp_path):
        """#5: md:<catalog> must NOT be path-joined."""
        cfg = _make_cfg(
            tmp_path,
            warehouse="md:demo_catalog",
            warehouse_type=WarehouseType.motherduck,
        )
        result = build_nao_config(cfg)
        assert result["databases"][0]["path"] == "md:demo_catalog"


class TestSchemaGlobs:

    def test_expand_bare_schema_names(self):
        assert _expand_schema_globs(["mart"]) == ["mart.*"]
        assert _expand_schema_globs(["mart", "staging"]) == ["mart.*", "staging.*"]

    def test_leaves_qualified_patterns_untouched(self):
        assert _expand_schema_globs(["mart.users", "raw_*.events"]) == [
            "mart.users",
            "raw_*.events",
        ]

    def test_include_schemas_written_as_globs(self, tmp_path):
        """#10: include_schemas: [mart] should yield include: [mart.*]."""
        cfg = _make_cfg(
            tmp_path,
            ask=AskConfig(include_schemas=["mart"], exclude_schemas=["pg_catalog"]),
        )
        result = build_nao_config(cfg)
        db = result["databases"][0]
        assert db["include"] == ["mart.*"]
        assert db["exclude"] == ["pg_catalog.*"]


class TestAccessorsRename:

    def test_emits_templates_not_accessors(self, tmp_path):
        """#9: nao 0.1.x renamed `accessors` → `templates`."""
        cfg = _make_cfg(tmp_path)
        result = build_nao_config(cfg)
        db = result["databases"][0]
        assert "templates" in db
        assert "accessors" not in db
        assert db["templates"] == ["columns", "preview"]


class TestAgentsMd:
    """AGENTS.md auto-generation: a pointer file at the project root telling
    coding agents where the synced Nao context lives."""

    def test_build_includes_project_name(self, tmp_path):
        cfg = _make_cfg(tmp_path)
        body = build_agents_md(cfg)
        assert "demo" in body
        assert ".tycoon/nao/databases" in body
        assert ".tycoon/nao/repos/dbt" in body
        assert ".tycoon/nao/RULES.md" in body

    def test_build_contains_sentinel(self, tmp_path):
        cfg = _make_cfg(tmp_path)
        body = build_agents_md(cfg)
        assert AGENTS_MD_SENTINEL in body[:200]

    def test_write_creates_file_when_missing(self, tmp_path):
        cfg = _make_cfg(tmp_path)
        wrote, path = write_agents_md(cfg)
        assert wrote is True
        assert path == tmp_path / "AGENTS.md"
        assert AGENTS_MD_SENTINEL in path.read_text()

    def test_write_overwrites_when_sentinel_present(self, tmp_path):
        cfg = _make_cfg(tmp_path)
        target = tmp_path / "AGENTS.md"
        # Pre-existing tycoon-owned file with stale content
        target.write_text(f"{AGENTS_MD_SENTINEL}\n# stale demo\nstale content\n")
        wrote, _ = write_agents_md(cfg)
        assert wrote is True
        body = target.read_text()
        assert "stale content" not in body
        assert ".tycoon/nao/databases" in body  # fresh content

    def test_write_preserves_user_authored_file(self, tmp_path):
        """A pre-existing AGENTS.md without our sentinel must NOT be touched."""
        cfg = _make_cfg(tmp_path)
        target = tmp_path / "AGENTS.md"
        original = "# my hand-rolled AGENTS file\nDo not touch.\n"
        target.write_text(original)
        wrote, path = write_agents_md(cfg)
        assert wrote is False
        assert path == target
        assert target.read_text() == original
