"""Tests for the OSI v0.1.1 scaffold generator + validator."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
import yaml

from tycoon.scaffolding.osi_generator import (
    OSI_VERSION,
    SENTINEL_PREFIX,
    osi_schema_path,
    scaffold_osi,
    validate_osi_yaml,
)


@pytest.fixture
def warehouse(tmp_path: Path) -> Path:
    """A DuckDB file with one mart, one dim, and a non-mart staging table."""
    db = tmp_path / "wh.duckdb"
    con = duckdb.connect(str(db))
    con.execute(
        "CREATE TABLE mart_orders ("
        "  id INTEGER, "
        "  customer_id INTEGER, "
        "  order_date DATE, "
        "  total_amount DECIMAL(18, 2), "
        "  is_paid BOOLEAN"
        ")"
    )
    con.execute(
        "CREATE TABLE dim_customer ("
        "  id INTEGER, "
        "  name VARCHAR, "
        "  signup_date DATE, "
        "  lifetime_value DECIMAL(18, 2)"
        ")"
    )
    # Should be skipped — not a mart prefix.
    con.execute("CREATE TABLE staging_orders (id INTEGER)")
    con.close()
    return db


class TestScaffoldFromMart:
    def test_emits_dataset_per_mart_and_skips_non_marts(self, warehouse, tmp_path):
        out = tmp_path / "osi.yaml"
        result = scaffold_osi(
            warehouse_db=warehouse,
            out_path=out,
            project_name="demo",
        )
        assert sorted(result.datasets_emitted) == ["dim_customer", "mart_orders"]
        assert result.warnings == []
        assert out.exists()

    def test_first_line_is_sentinel(self, warehouse, tmp_path):
        out = tmp_path / "osi.yaml"
        scaffold_osi(warehouse_db=warehouse, out_path=out, project_name="demo")
        first_line = out.read_text().splitlines()[0]
        assert first_line.startswith(SENTINEL_PREFIX)

    def test_numeric_measure_columns_have_no_dimension_attribute(
        self, warehouse, tmp_path
    ):
        """Conservative dial: DECIMAL → measure-eligible (no dimension key)."""
        out = tmp_path / "osi.yaml"
        scaffold_osi(warehouse_db=warehouse, out_path=out, project_name="demo")
        body = yaml.safe_load(out.read_text())
        mart = next(
            d for d in body["semantic_model"][0]["datasets"]
            if d["name"] == "mart_orders"
        )
        total = next(f for f in mart["fields"] if f["name"] == "total_amount")
        assert "dimension" not in total

    def test_fk_named_columns_become_dimensions_even_when_numeric(
        self, warehouse, tmp_path
    ):
        out = tmp_path / "osi.yaml"
        scaffold_osi(warehouse_db=warehouse, out_path=out, project_name="demo")
        body = yaml.safe_load(out.read_text())
        mart = next(
            d for d in body["semantic_model"][0]["datasets"]
            if d["name"] == "mart_orders"
        )
        cust_id = next(f for f in mart["fields"] if f["name"] == "customer_id")
        # FK shape (column ends in `_id`) → dimension, despite INTEGER type.
        assert cust_id["dimension"] == {}
        # Bare `id` PK column → also dimension.
        id_field = next(f for f in mart["fields"] if f["name"] == "id")
        assert id_field["dimension"] == {}

    def test_date_columns_become_time_dimensions(self, warehouse, tmp_path):
        out = tmp_path / "osi.yaml"
        scaffold_osi(warehouse_db=warehouse, out_path=out, project_name="demo")
        body = yaml.safe_load(out.read_text())
        mart = next(
            d for d in body["semantic_model"][0]["datasets"]
            if d["name"] == "mart_orders"
        )
        order_date = next(f for f in mart["fields"] if f["name"] == "order_date")
        assert order_date["dimension"] == {"is_time": True}

    def test_no_metrics_or_relationships_scaffolded(self, warehouse, tmp_path):
        """Conservative dial: empty lists, user fills them in."""
        out = tmp_path / "osi.yaml"
        scaffold_osi(warehouse_db=warehouse, out_path=out, project_name="demo")
        body = yaml.safe_load(out.read_text())
        sm = body["semantic_model"][0]
        assert sm["metrics"] == []
        assert sm["relationships"] == []

    def test_primary_key_inferred_from_id_column(self, warehouse, tmp_path):
        out = tmp_path / "osi.yaml"
        scaffold_osi(warehouse_db=warehouse, out_path=out, project_name="demo")
        body = yaml.safe_load(out.read_text())
        for ds in body["semantic_model"][0]["datasets"]:
            assert ds["primary_key"] == ["id"]

    def test_source_uses_database_schema_table(self, warehouse, tmp_path):
        out = tmp_path / "osi.yaml"
        scaffold_osi(warehouse_db=warehouse, out_path=out, project_name="demo")
        body = yaml.safe_load(out.read_text())
        sources = sorted(d["source"] for d in body["semantic_model"][0]["datasets"])
        # DuckDB names the file's catalog after the file stem (`wh.duckdb` → `wh`).
        assert sources == ["wh.main.dim_customer", "wh.main.mart_orders"]


class TestSentinelGuard:
    def test_re_run_with_sentinel_overwrites(self, warehouse, tmp_path):
        out = tmp_path / "osi.yaml"
        scaffold_osi(warehouse_db=warehouse, out_path=out, project_name="demo")
        # Mutate the file (still sentineled) and re-run.
        body = out.read_text()
        out.write_text(body + "\n# user note\n")
        result = scaffold_osi(warehouse_db=warehouse, out_path=out, project_name="demo")
        assert result.skipped_due_to_sentinel is False
        # User comment is gone — file was regenerated.
        assert "# user note" not in out.read_text()

    def test_re_run_without_sentinel_skips(self, warehouse, tmp_path):
        out = tmp_path / "osi.yaml"
        scaffold_osi(warehouse_db=warehouse, out_path=out, project_name="demo")
        # Strip the sentinel.
        body_without_sentinel = "\n".join(out.read_text().splitlines()[1:])
        out.write_text(body_without_sentinel)
        result = scaffold_osi(warehouse_db=warehouse, out_path=out, project_name="demo")
        assert result.skipped_due_to_sentinel is True
        # Hand-edited content survives.
        assert SENTINEL_PREFIX not in out.read_text()

    def test_force_overwrites_unsentineled(self, warehouse, tmp_path):
        out = tmp_path / "osi.yaml"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("hand-written content\n")
        result = scaffold_osi(
            warehouse_db=warehouse,
            out_path=out,
            project_name="demo",
            force=True,
        )
        assert result.skipped_due_to_sentinel is False
        assert "hand-written content" not in out.read_text()
        assert out.read_text().startswith(SENTINEL_PREFIX)


class TestValidation:
    def test_generated_yaml_is_schema_valid(self, warehouse, tmp_path):
        out = tmp_path / "osi.yaml"
        scaffold_osi(warehouse_db=warehouse, out_path=out, project_name="demo")
        errors = validate_osi_yaml(out)
        assert errors == [], errors

    def test_validator_rejects_missing_version(self, tmp_path):
        out = tmp_path / "broken.yaml"
        out.write_text(yaml.dump({"semantic_model": [{"name": "x", "datasets": [{"name": "d", "source": "a.b.c"}]}]}))
        errors = validate_osi_yaml(out)
        assert any("version" in e for e in errors)

    def test_validator_rejects_wrong_version_string(self, tmp_path):
        out = tmp_path / "broken.yaml"
        out.write_text(
            yaml.dump(
                {
                    "version": "9.9.9",
                    "semantic_model": [
                        {
                            "name": "x",
                            "datasets": [{"name": "d", "source": "a.b.c"}],
                        }
                    ],
                }
            )
        )
        errors = validate_osi_yaml(out)
        # The schema's `const: "0.1.1"` rejects any other string.
        assert any("0.1.1" in e for e in errors)

    def test_vendored_schema_is_present(self):
        assert osi_schema_path().exists()


class TestEdgeCases:
    def test_empty_warehouse_emits_placeholder(self, tmp_path):
        empty_db = tmp_path / "empty.duckdb"
        con = duckdb.connect(str(empty_db))
        con.close()
        out = tmp_path / "osi.yaml"
        result = scaffold_osi(warehouse_db=empty_db, out_path=out, project_name="demo")
        assert any("No marts found" in w for w in result.warnings)
        # File still emitted, schema-valid (uses placeholder dataset).
        assert validate_osi_yaml(out) == []
        body = yaml.safe_load(out.read_text())
        assert body["semantic_model"][0]["datasets"][0]["name"] == "_placeholder"

    def test_nonexistent_warehouse_warns_no_file_written(self, tmp_path):
        out = tmp_path / "osi.yaml"
        result = scaffold_osi(
            warehouse_db=tmp_path / "nope.duckdb",
            out_path=out,
            project_name="demo",
        )
        assert any("Warehouse not found" in w for w in result.warnings)
        assert not out.exists()

    def test_version_constant_matches_schema(self):
        """Tycoon's vendored OSI version + schema must agree."""
        import json

        schema = json.loads(osi_schema_path().read_text())
        assert schema["properties"]["version"]["const"] == OSI_VERSION
