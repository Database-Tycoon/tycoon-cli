"""Tests for `tycoon ask context` — the cat-the-Nao-context command."""

from __future__ import annotations

from pathlib import Path

import pytest

from tycoon.cli import app


def _write_tycoon_yml(root: Path) -> None:
    (root / "tycoon.yml").write_text(
        "name: test\n"
        "version: 0.1.0\n"
        "database:\n"
        "  raw: data/raw.duckdb\n"
        "  warehouse: data/warehouse.duckdb\n"
        "sources: {}\n"
    )


def _seed_nao_context(
    root: Path,
    *,
    tables: list[tuple[str, str]] | None = None,
    rules: str | None = None,
) -> None:
    """Mirror what `nao sync` writes under .tycoon/nao/."""
    nao = root / ".tycoon" / "nao"
    nao.mkdir(parents=True, exist_ok=True)
    if rules is not None:
        (nao / "RULES.md").write_text(rules)

    db_root = nao / "databases" / "type=duckdb" / "database=warehouse"
    for schema, table in tables or []:
        tdir = db_root / f"schema={schema}" / f"table={table}"
        tdir.mkdir(parents=True, exist_ok=True)
        (tdir / "columns.md").write_text(
            f"# {table}\n**Dataset:** `{schema}`\n## Columns\n- id (int)\n- name (string)\n"
        )
        (tdir / "preview.md").write_text(
            f"# {table} - Preview\n**Dataset:** `{schema}`\n## Rows\n- {{\"id\": 1}}\n"
        )


@pytest.fixture
def project(tmp_path: Path, monkeypatch):
    """tycoon.yml + monkey-patched config pointing the ask command at tmp_path."""
    _write_tycoon_yml(tmp_path)

    from tycoon.commands import ask as ask_mod
    from tycoon.config import TycoonConfig

    cfg = TycoonConfig(project_root=tmp_path)
    monkeypatch.setattr(ask_mod, "config", cfg)
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


class TestErrors:

    def test_no_nao_dir_errors(self, project, cli_runner):
        result = cli_runner.invoke(app, ["ask", "context"])
        assert result.exit_code == 1
        # Errors go to stderr but typer's runner mixes them in stderr; check both
        combined = (result.stdout or "") + (result.stderr or "")
        assert "tycoon ask sync" in combined

    def test_no_databases_dir_errors(self, project, cli_runner):
        # nao dir exists (e.g. after init) but no `databases/` yet
        (project / ".tycoon" / "nao").mkdir(parents=True)
        result = cli_runner.invoke(app, ["ask", "context"])
        assert result.exit_code == 1

    def test_filter_no_match_errors(self, project, cli_runner):
        _seed_nao_context(project, tables=[("mart", "dim_users")])
        result = cli_runner.invoke(app, ["ask", "context", "--table", "ghost"])
        assert result.exit_code == 1
        combined = (result.stdout or "") + (result.stderr or "")
        assert "table=ghost" in combined


# ---------------------------------------------------------------------------
# Listing mode
# ---------------------------------------------------------------------------


class TestListing:

    def test_lists_available_tables(self, project, cli_runner):
        _seed_nao_context(
            project,
            tables=[("mart", "dim_users"), ("mart", "fct_orders"), ("staging", "stg_widgets")],
        )
        result = cli_runner.invoke(app, ["ask", "context"])
        assert result.exit_code == 0
        assert "mart.dim_users" in result.stdout
        assert "mart.fct_orders" in result.stdout
        assert "staging.stg_widgets" in result.stdout
        assert "Available Nao context" in result.stdout


# ---------------------------------------------------------------------------
# Selected mode (--table / --schema)
# ---------------------------------------------------------------------------


class TestSelected:

    def test_table_filter_prints_columns_and_preview(self, project, cli_runner):
        _seed_nao_context(project, tables=[("mart", "dim_users"), ("mart", "fct_orders")])
        result = cli_runner.invoke(app, ["ask", "context", "--table", "dim_users"])
        assert result.exit_code == 0
        # dim_users content present, fct_orders absent
        assert "# dim_users" in result.stdout
        assert "# dim_users - Preview" in result.stdout
        assert "fct_orders" not in result.stdout

    def test_schema_filter_prints_all_tables_in_schema(self, project, cli_runner):
        _seed_nao_context(
            project,
            tables=[("mart", "dim_users"), ("mart", "fct_orders"), ("staging", "stg_widgets")],
        )
        result = cli_runner.invoke(app, ["ask", "context", "--schema", "mart"])
        assert result.exit_code == 0
        assert "# dim_users" in result.stdout
        assert "# fct_orders" in result.stdout
        assert "stg_widgets" not in result.stdout


# ---------------------------------------------------------------------------
# RULES.md surface
# ---------------------------------------------------------------------------


class TestRulesOnly:

    def test_rules_only_prints_rules_file(self, project, cli_runner):
        _seed_nao_context(
            project,
            tables=[("mart", "dim_users")],
            rules="# Project rules\nPrefer mart over staging.\n",
        )
        result = cli_runner.invoke(app, ["ask", "context", "--rules-only"])
        assert result.exit_code == 0
        assert "Prefer mart over staging" in result.stdout
        # Should NOT include database context
        assert "dim_users" not in result.stdout

    def test_rules_only_errors_when_missing(self, project, cli_runner):
        # nao dir exists but no RULES.md
        (project / ".tycoon" / "nao").mkdir(parents=True)
        result = cli_runner.invoke(app, ["ask", "context", "--rules-only"])
        assert result.exit_code == 1
