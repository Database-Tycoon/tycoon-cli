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


# -- Layer-aware mart discovery (v0.1.7) ----------------------------------------


def _write_manifest(dbt_project_dir: Path, nodes: dict) -> None:
    """Drop a minimal target/manifest.json under ``dbt_project_dir``."""
    import json

    target = dbt_project_dir / "target"
    target.mkdir(parents=True, exist_ok=True)
    (target / "manifest.json").write_text(json.dumps({"nodes": nodes}))


class TestLayerAwareDiscovery:
    """As of v0.1.7, mart discovery prefers dbt manifest classification."""

    @pytest.fixture
    def warehouse_with_oddly_named_marts(self, tmp_path: Path) -> Path:
        """A warehouse where marts use unconventional names (no fct_/dim_/etc).

        These tables would be invisible to the v0.1.6 prefix matcher but
        visible to the v0.1.7 layer classifier because they live in
        ``models/marts/`` per the manifest.
        """
        db = tmp_path / "wh.duckdb"
        con = duckdb.connect(str(db))
        con.execute(
            "CREATE TABLE orders_summary ("
            "  id INTEGER, "
            "  total DECIMAL(18, 2), "
            "  order_date DATE"
            ")"
        )
        con.execute("CREATE TABLE customer_book (id INTEGER, name VARCHAR)")
        # Should still NOT appear — manifest classifies as staging.
        con.execute("CREATE TABLE stg_raw_orders (id INTEGER)")
        con.close()
        return db

    def test_manifest_picks_up_unconventionally_named_marts(
        self, warehouse_with_oddly_named_marts, tmp_path: Path
    ) -> None:
        dbt_dir = tmp_path / "dbt"
        _write_manifest(
            dbt_dir,
            {
                "model.p.orders_summary": {
                    "resource_type": "model",
                    "name": "orders_summary",
                    "schema": "main",
                    "original_file_path": "models/marts/orders_summary.sql",
                    "config": {"meta": {}},
                },
                "model.p.customer_book": {
                    "resource_type": "model",
                    "name": "customer_book",
                    "schema": "main",
                    "original_file_path": "models/marts/customer_book.sql",
                    "config": {"meta": {}},
                },
                "model.p.stg_raw_orders": {
                    "resource_type": "model",
                    "name": "stg_raw_orders",
                    "schema": "main",
                    "original_file_path": "models/staging/stg_raw_orders.sql",
                    "config": {"meta": {}},
                },
            },
        )
        out = tmp_path / "osi.yaml"
        result = scaffold_osi(
            warehouse_db=warehouse_with_oddly_named_marts,
            out_path=out,
            project_name="demo",
            dbt_project_dir=dbt_dir,
        )
        assert sorted(result.datasets_emitted) == ["customer_book", "orders_summary"]

    def test_meta_override_promotes_table_to_mart(
        self, tmp_path: Path
    ) -> None:
        """A table in models/scratch/ tagged ``meta.tycoon_layer: mart`` is included."""
        db = tmp_path / "wh.duckdb"
        con = duckdb.connect(str(db))
        con.execute("CREATE TABLE oddball (id INTEGER, value DECIMAL(18, 2))")
        con.close()

        dbt_dir = tmp_path / "dbt"
        _write_manifest(
            dbt_dir,
            {
                "model.p.oddball": {
                    "resource_type": "model",
                    "name": "oddball",
                    "schema": "main",
                    "original_file_path": "models/scratch/oddball.sql",
                    "config": {"meta": {"tycoon_layer": "mart"}},
                },
            },
        )
        out = tmp_path / "osi.yaml"
        result = scaffold_osi(
            warehouse_db=db,
            out_path=out,
            project_name="demo",
            dbt_project_dir=dbt_dir,
        )
        assert result.datasets_emitted == ["oddball"]

    def test_missing_manifest_falls_back_to_prefix(
        self, warehouse, tmp_path: Path
    ) -> None:
        """No manifest at the given path → warn + fall back to prefix matching."""
        dbt_dir = tmp_path / "dbt"  # no manifest written
        out = tmp_path / "osi.yaml"
        result = scaffold_osi(
            warehouse_db=warehouse,
            out_path=out,
            project_name="demo",
            dbt_project_dir=dbt_dir,
        )
        # Fixture's mart_orders + dim_customer get picked up via prefix.
        assert sorted(result.datasets_emitted) == ["dim_customer", "mart_orders"]
        assert any("No dbt manifest" in w for w in result.warnings)

    def test_no_dbt_project_dir_uses_prefix(
        self, warehouse, tmp_path: Path
    ) -> None:
        """Caller passes None → existing v0.1.6 behaviour exactly."""
        out = tmp_path / "osi.yaml"
        result = scaffold_osi(
            warehouse_db=warehouse,
            out_path=out,
            project_name="demo",
            dbt_project_dir=None,
        )
        assert sorted(result.datasets_emitted) == ["dim_customer", "mart_orders"]
        # No manifest-related warnings when None is passed explicitly.
        assert not any("manifest" in w.lower() for w in result.warnings)

    def test_manifest_excludes_staging_even_with_mart_prefix(
        self, tmp_path: Path
    ) -> None:
        """A table named ``fct_x`` living in ``models/staging/`` is NOT a mart."""
        db = tmp_path / "wh.duckdb"
        con = duckdb.connect(str(db))
        con.execute("CREATE TABLE fct_legacy (id INTEGER)")
        con.close()

        dbt_dir = tmp_path / "dbt"
        _write_manifest(
            dbt_dir,
            {
                "model.p.fct_legacy": {
                    "resource_type": "model",
                    "name": "fct_legacy",
                    "schema": "main",
                    "original_file_path": "models/staging/fct_legacy.sql",
                    "config": {"meta": {}},
                },
            },
        )
        out = tmp_path / "osi.yaml"
        result = scaffold_osi(
            warehouse_db=db,
            out_path=out,
            project_name="demo",
            dbt_project_dir=dbt_dir,
        )
        # Empty datasets — fct_legacy is staging per the manifest.
        assert result.datasets_emitted == []
