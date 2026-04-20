"""Tests for dbt manifest capture + schema diff (v0.1.3 — observability v2b).

These tests exercise the manifest fingerprint / diff pipeline using hand-built
manifest dicts, plus a round-trip through ``capture_dbt_manifest`` writing a
``target/manifest.json`` file.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from tycoon.observability import (
    _diff_fingerprints,
    _extract_manifest_fingerprint,
    capture_dbt_manifest,
    capture_dbt_manifest_safe,
    ensure_schema,
    export_to_parquet,
    metadata_db_path,
)


def _manifest(
    invocation_id: str = "inv-001",
    nodes: dict | None = None,
) -> dict:
    """Return a minimal manifest.json in the shape dbt emits."""
    return {
        "metadata": {
            "invocation_id": invocation_id,
            "generated_at": "2026-04-19T12:00:00.000000Z",
            "dbt_schema_version": "https://schemas.getdbt.com/dbt/manifest/v12.json",
        },
        "nodes": nodes
        if nodes is not None
        else {
            "model.demo.stg_widgets": {
                "unique_id": "model.demo.stg_widgets",
                "resource_type": "model",
                "checksum": {"name": "sha256", "checksum": "aaaa1111"},
                "columns": {
                    "widget_id": {"name": "widget_id", "data_type": "INTEGER"},
                    "quantity": {"name": "quantity", "data_type": "INTEGER"},
                },
            }
        },
    }


class TestExtractFingerprint:
    def test_keeps_only_model_seed_snapshot(self) -> None:
        manifest = {
            "nodes": {
                "model.a.b": {
                    "resource_type": "model",
                    "checksum": {"checksum": "x"},
                    "columns": {"c1": {"data_type": "VARCHAR"}},
                },
                "seed.a.s": {
                    "resource_type": "seed",
                    "checksum": {"checksum": "y"},
                    "columns": {},
                },
                "test.a.t": {"resource_type": "test"},
                "analysis.a.an": {"resource_type": "analysis"},
            }
        }
        fp = _extract_manifest_fingerprint(manifest)
        assert set(fp.keys()) == {"model.a.b", "seed.a.s"}
        assert fp["model.a.b"]["checksum"] == "x"
        assert fp["model.a.b"]["columns"] == {"c1": "VARCHAR"}

    def test_handles_missing_checksum_and_columns(self) -> None:
        manifest = {
            "nodes": {
                "model.a.b": {"resource_type": "model"},
            }
        }
        fp = _extract_manifest_fingerprint(manifest)
        assert fp["model.a.b"]["checksum"] == ""
        assert fp["model.a.b"]["columns"] == {}


class TestDiffFingerprints:
    def test_no_previous_yields_empty_diff(self) -> None:
        curr = _extract_manifest_fingerprint(_manifest())
        assert _diff_fingerprints(None, curr) == []

    def test_model_added(self) -> None:
        prev = {}
        curr = {"model.a.b": {"resource_type": "model", "checksum": "x", "columns": {}}}
        changes = _diff_fingerprints(prev, curr)
        assert len(changes) == 1
        assert changes[0]["change_type"] == "model_added"
        assert changes[0]["unique_id"] == "model.a.b"

    def test_model_removed(self) -> None:
        prev = {"model.a.b": {"resource_type": "model", "checksum": "x", "columns": {}}}
        curr = {}
        changes = _diff_fingerprints(prev, curr)
        assert len(changes) == 1
        assert changes[0]["change_type"] == "model_removed"
        assert changes[0]["unique_id"] == "model.a.b"

    def test_sql_changed(self) -> None:
        prev = {"model.a.b": {"resource_type": "model", "checksum": "aaa", "columns": {}}}
        curr = {"model.a.b": {"resource_type": "model", "checksum": "bbb", "columns": {}}}
        changes = _diff_fingerprints(prev, curr)
        assert [c["change_type"] for c in changes] == ["sql_changed"]
        assert changes[0]["old_value"] == "aaa"
        assert changes[0]["new_value"] == "bbb"

    def test_column_added_removed_and_type_changed(self) -> None:
        prev = {
            "model.a.b": {
                "resource_type": "model",
                "checksum": "x",
                "columns": {"keep": "INTEGER", "drop": "VARCHAR", "retype": "INTEGER"},
            }
        }
        curr = {
            "model.a.b": {
                "resource_type": "model",
                "checksum": "x",
                "columns": {"keep": "INTEGER", "new": "TIMESTAMP", "retype": "BIGINT"},
            }
        }
        changes = _diff_fingerprints(prev, curr)
        types = {c["change_type"]: c for c in changes}
        assert types.keys() == {"column_added", "column_removed", "column_type_changed"}
        assert types["column_added"]["column_name"] == "new"
        assert types["column_added"]["new_value"] == "TIMESTAMP"
        assert types["column_removed"]["column_name"] == "drop"
        assert types["column_type_changed"]["column_name"] == "retype"
        assert types["column_type_changed"]["old_value"] == "INTEGER"
        assert types["column_type_changed"]["new_value"] == "BIGINT"

    def test_first_snapshot_captures_but_records_no_changes(
        self, tmp_path: Path
    ) -> None:
        """Round-trip: writing a manifest.json with no prior snapshot should
        insert the snapshot row and zero change rows."""
        meta = metadata_db_path(tmp_path)
        ensure_schema(meta)
        dbt_dir = tmp_path / "dbt_project"
        (dbt_dir / "target").mkdir(parents=True)
        (dbt_dir / "target" / "manifest.json").write_text(json.dumps(_manifest()))

        result = capture_dbt_manifest(meta, dbt_dir)
        assert result == ("inv-001", 0)

        con = duckdb.connect(str(meta), read_only=True)
        try:
            snap = con.execute(
                "SELECT invocation_id FROM dbt_manifest_snapshots"
            ).fetchall()
            assert snap == [("inv-001",)]
            changes = con.execute(
                "SELECT count(*) FROM dbt_schema_changes"
            ).fetchone()
            assert changes == (0,)
        finally:
            con.close()


class TestCaptureDbtManifestRoundTrip:
    def _write_manifest(self, dbt_dir: Path, manifest: dict) -> None:
        target = dbt_dir / "target"
        target.mkdir(parents=True, exist_ok=True)
        (target / "manifest.json").write_text(json.dumps(manifest))

    def test_two_snapshots_produce_diff_rows(self, tmp_path: Path) -> None:
        meta = metadata_db_path(tmp_path)
        ensure_schema(meta)
        dbt_dir = tmp_path / "dbt_project"

        # First snapshot — baseline. No prior, so no changes recorded.
        self._write_manifest(dbt_dir, _manifest(invocation_id="inv-001"))
        capture_dbt_manifest(meta, dbt_dir)

        # Second snapshot — add a column, drop a column, change SQL.
        second = _manifest(
            invocation_id="inv-002",
            nodes={
                "model.demo.stg_widgets": {
                    "unique_id": "model.demo.stg_widgets",
                    "resource_type": "model",
                    "checksum": {"name": "sha256", "checksum": "zzzz9999"},
                    "columns": {
                        "widget_id": {"data_type": "INTEGER"},
                        # 'quantity' removed
                        "name": {"data_type": "VARCHAR"},
                    },
                }
            },
        )
        self._write_manifest(dbt_dir, second)
        result = capture_dbt_manifest(meta, dbt_dir)
        assert result is not None
        assert result[0] == "inv-002"
        # Expect: sql_changed + column_removed(quantity) + column_added(name)
        assert result[1] == 3

        con = duckdb.connect(str(meta), read_only=True)
        try:
            types = [
                r[0]
                for r in con.execute(
                    "SELECT change_type FROM dbt_schema_changes "
                    "WHERE invocation_id = 'inv-002' ORDER BY change_type"
                ).fetchall()
            ]
            assert types == ["column_added", "column_removed", "sql_changed"]
            prev = con.execute(
                "SELECT DISTINCT prev_invocation_id FROM dbt_schema_changes "
                "WHERE invocation_id = 'inv-002'"
            ).fetchall()
            assert prev == [("inv-001",)]
        finally:
            con.close()

    def test_duplicate_invocation_is_noop(self, tmp_path: Path) -> None:
        meta = metadata_db_path(tmp_path)
        ensure_schema(meta)
        dbt_dir = tmp_path / "dbt_project"
        self._write_manifest(dbt_dir, _manifest(invocation_id="inv-dup"))
        first = capture_dbt_manifest(meta, dbt_dir)
        second = capture_dbt_manifest(meta, dbt_dir)
        assert first == ("inv-dup", 0)
        assert second is None

    def test_missing_manifest_is_noop(self, tmp_path: Path) -> None:
        meta = metadata_db_path(tmp_path)
        ensure_schema(meta)
        dbt_dir = tmp_path / "dbt_project"
        dbt_dir.mkdir()
        assert capture_dbt_manifest(meta, dbt_dir) is None

    def test_safe_wrapper_swallows_exceptions(self, tmp_path: Path) -> None:
        meta = metadata_db_path(tmp_path)
        ensure_schema(meta)
        # Passing a path with a bogus manifest shouldn't raise.
        dbt_dir = tmp_path / "dbt_project"
        target = dbt_dir / "target"
        target.mkdir(parents=True)
        (target / "manifest.json").write_text("{not valid json")
        capture_dbt_manifest_safe(meta, dbt_dir)


class TestManifestParquetExport:
    def test_manifest_tables_included(self, tmp_path: Path) -> None:
        meta = metadata_db_path(tmp_path)
        ensure_schema(meta)

        parquet_dir = tmp_path / "parquet"
        exported = export_to_parquet(meta, parquet_dir)

        assert "dbt_manifest_snapshots" in exported
        assert "dbt_schema_changes" in exported
        assert exported["dbt_manifest_snapshots"].exists()
