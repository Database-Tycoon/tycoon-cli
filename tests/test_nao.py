"""Tests for the Nao config generator."""

from __future__ import annotations

from pathlib import Path

import pytest

from tycoon.config import TycoonConfig
from tycoon.nao import build_nao_config


def _write_project(root: Path, warehouse: str, stack_warehouse: str = "duckdb") -> None:
    """Write a minimal tycoon.yml at ``root`` with the given warehouse path."""
    (root / "pyproject.toml").write_text('[project]\nname = "test"\n')
    (root / "tycoon.yml").write_text(
        "name: test\n"
        "version: 0.1.0\n"
        "database:\n"
        "  raw: data/raw.duckdb\n"
        f"  warehouse: {warehouse}\n"
        "dbt_project_dir: dbt\n"
        "sources: {}\n"
        "stack:\n"
        "  ingestion: dlt\n"
        "  ingestion_managed: false\n"
        f"  warehouse: {stack_warehouse}\n"
        "  transformation: dbt\n"
        "  transformation_managed: false\n"
        "  bi: none\n"
        "  bi_managed: false\n"
        "  orchestrator: none\n"
        "  orchestrator_managed: false\n"
    )


class TestBuildNaoConfig:

    def test_local_duckdb_path_is_relative(self, tmp_path: Path):
        _write_project(tmp_path, warehouse="data/warehouse.duckdb")
        cfg = TycoonConfig(project_root=tmp_path)

        nao_cfg = build_nao_config(cfg)

        db_path = nao_cfg["databases"][0]["path"]
        # Relative from .tycoon/nao/ back out to data/warehouse.duckdb
        assert db_path.endswith("warehouse.duckdb")
        assert not db_path.startswith("md:")

    def test_motherduck_url_passes_through_verbatim(self, tmp_path: Path):
        """Regression: `md:<catalog>` must NOT be path-joined. Nao's DuckDB
        backend accepts the URL as-is via `ibis.duckdb.connect(database=...)`.
        """
        _write_project(
            tmp_path,
            warehouse="md:my_catalog",
            stack_warehouse="motherduck",
        )
        cfg = TycoonConfig(project_root=tmp_path)

        nao_cfg = build_nao_config(cfg)

        db_path = nao_cfg["databases"][0]["path"]
        assert db_path == "md:my_catalog"

    def test_no_project_falls_back_to_default_path(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        cfg = TycoonConfig(project_root=tmp_path)

        nao_cfg = build_nao_config(cfg)

        db_path = nao_cfg["databases"][0]["path"]
        assert not db_path.startswith("md:")
        assert db_path.endswith("warehouse.duckdb")
