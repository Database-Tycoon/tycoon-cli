"""Reading tycoon.yml: only the needed keys, drift tolerated by construction."""

import pytest

from tests.fixtures.tycoon_factory import make_tycoon_project
from tycoon_city.catalog.tycoon_project import read_project_info


def test_not_a_project_reads_as_none(tmp_path):
    assert read_project_info(tmp_path) is None


def test_reads_pointers_resolved_relative_to_the_root(tmp_path):
    root = make_tycoon_project(tmp_path / "fx")

    info = read_project_info(root)

    assert info is not None
    assert info.name == "fx"
    assert info.warehouse_path == root / "data" / "fx.duckdb"
    assert info.manifest_path == root / "dbt" / "target" / "manifest.json"
    assert info.metadata_db_path == root / ".tycoon" / "metadata.duckdb"


def test_drift_keys_are_ignored_by_construction(tmp_path):
    """Real tycoon.yml files carry keys the CLI's own model lacks (`ask:`,
    `stack.orchestrator`). Reading must not even notice them."""
    root = make_tycoon_project(tmp_path / "fx", drift_keys=True)

    info = read_project_info(root)

    assert info is not None and info.name == "fx"


def test_env_var_interpolation(tmp_path, monkeypatch):
    monkeypatch.setenv("FX_DATA", "data")
    root = make_tycoon_project(tmp_path / "fx", warehouse_value="${FX_DATA}/fx.duckdb")

    info = read_project_info(root)

    assert info.warehouse_path == root / "data" / "fx.duckdb"


def test_unknown_env_var_is_left_visible_not_erased(tmp_path, monkeypatch):
    monkeypatch.delenv("FX_NOPE", raising=False)
    root = make_tycoon_project(tmp_path / "fx", warehouse_value="${FX_NOPE}/fx.duckdb")

    info = read_project_info(root)

    # A visibly wrong path (that will fail loudly downstream) beats a silently
    # truncated one that opens the wrong file.
    assert "${FX_NOPE}" in str(info.warehouse_path)


def test_missing_warehouse_key_is_an_error_not_a_none(tmp_path):
    root = tmp_path / "broken"
    root.mkdir()
    (root / "tycoon.yml").write_text("name: broken\n")

    with pytest.raises(ValueError, match="database.warehouse"):
        read_project_info(root)


def test_absent_manifest_and_metadata_read_as_none_paths(tmp_path):
    root = make_tycoon_project(tmp_path / "fx", with_manifest=False, with_metadata=False)

    info = read_project_info(root)

    assert info.manifest_path is None
    assert info.metadata_db_path is None


def test_v0_1_11_schema_version_and_custom_metadata_path(tmp_path):
    """tycoon-cli v0.1.11 adds schema_version: 2 and metadata.path configuration block."""
    root = tmp_path / "v11_proj"
    root.mkdir()
    meta_dir = root / "custom_meta"
    meta_dir.mkdir()
    meta_file = meta_dir / "custom_history.duckdb"
    meta_file.write_bytes(b"duckdb")
    (root / "data").mkdir()
    (root / "data" / "wh.duckdb").write_bytes(b"duckdb")

    yml_content = """
name: v11_proj
schema_version: 2
database:
  warehouse: data/wh.duckdb
metadata:
  backend: duckdb_file
  path: custom_meta/custom_history.duckdb
"""
    (root / "tycoon.yml").write_text(yml_content)

    info = read_project_info(root)

    assert info is not None
    assert info.name == "v11_proj"
    assert info.warehouse_path == root / "data" / "wh.duckdb"
    assert info.metadata_db_path == meta_file
