"""Tests for nao_config.yaml generation. Covers issues #5, #9, #10."""

from __future__ import annotations

from pathlib import Path


from tycoon.config import TycoonConfig
from tycoon.nao import _expand_schema_globs, build_nao_config
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
