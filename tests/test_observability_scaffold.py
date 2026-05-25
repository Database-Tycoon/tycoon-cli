"""Tests for `tycoon.scaffolding.observability_dbt` — the auto-generated
``stg_tycoon__*`` / ``dim_runs`` dbt models that surface tycoon's own
metadata DB."""

from __future__ import annotations

from pathlib import Path

from tycoon.scaffolding.observability_dbt import scaffold_observability_models


class TestScaffolderEmitsTycoonTag:
    """Every auto-generated dbt model should carry ``tags=['tycoon']``.

    Lets users skip tycoon's bookkeeping models with
    ``dbt run --exclude tag:tycoon`` when iterating on business logic.
    """

    def test_every_staging_model_has_tycoon_tag(self, tmp_path: Path) -> None:
        written = scaffold_observability_models(tmp_path)
        sql_files = [p for p in written if p.name.startswith("stg_tycoon__")]
        assert sql_files, "scaffolder should produce at least one staging model"
        for path in sql_files:
            body = path.read_text()
            assert "tags=['tycoon']" in body, f"{path.name} missing tycoon tag"

    def test_dim_runs_has_tycoon_tag(self, tmp_path: Path) -> None:
        written = scaffold_observability_models(tmp_path)
        dim_path = next(p for p in written if p.name == "dim_runs.sql")
        assert "tags=['tycoon']" in dim_path.read_text()
