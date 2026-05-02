"""Tests for `tycoon ask context` (#7-related) and `tycoon ask doctor` (#7 §6).

Also covers the `tycoon ask init --llm <provider>` shortcut that records
the LLM provider in tycoon.yml — the headline UX win called out in #7 §5.
"""

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


# ---------------------------------------------------------------------------
# `tycoon ask doctor` — issue #7 §6
# ---------------------------------------------------------------------------


class TestAskDoctor:
    """Health check for the ask stack."""

    def test_fails_when_nao_config_missing(self, project, cli_runner):
        result = cli_runner.invoke(app, ["ask", "doctor"])
        assert result.exit_code == 1
        assert "nao_config.yaml" in result.stdout
        assert "FAIL" in result.stdout

    def test_passes_when_init_was_run(self, project, cli_runner):
        # Simulate `tycoon ask init`
        from tycoon.config import TycoonConfig
        from tycoon.nao import write_nao_project

        cfg = TycoonConfig(project_root=project)
        write_nao_project(cfg)
        result = cli_runner.invoke(app, ["ask", "doctor"])
        # No FAIL lines because nao_config + dirs are present and warehouse
        # is local DuckDB (no auth needed). Exit 0.
        assert result.exit_code == 0, result.stdout
        # Check that all four panels rendered
        assert "nao_config.yaml" in result.stdout
        assert "nao directories" in result.stdout

    def test_doctor_fails_loudly_on_lm_studio_unreachable(
        self, tmp_path: Path, monkeypatch, cli_runner
    ):
        """When LLM is lm-studio but the endpoint is unreachable, doctor exits 1."""
        (tmp_path / "tycoon.yml").write_text(
            "name: test\n"
            "version: 0.1.0\n"
            "database:\n"
            "  raw: data/raw.duckdb\n"
            "  warehouse: data/warehouse.duckdb\n"
            "sources: {}\n"
            "ask:\n"
            "  llm:\n"
            "    provider: lm-studio\n"
            "    base_url: http://127.0.0.1:1/v1\n"  # unreachable port
        )
        from tycoon.commands import ask as ask_mod
        from tycoon.config import TycoonConfig
        from tycoon.nao import write_nao_project

        cfg = TycoonConfig(project_root=tmp_path)
        monkeypatch.setattr(ask_mod, "config", cfg)
        monkeypatch.chdir(tmp_path)
        write_nao_project(cfg)

        result = cli_runner.invoke(app, ["ask", "doctor"])
        assert result.exit_code == 1
        assert "LM Studio" in result.stdout
        assert "FAIL" in result.stdout

    def test_warns_when_motherduck_token_missing(self, tmp_path: Path, monkeypatch, cli_runner):
        """When warehouse is md:* but MOTHERDUCK_TOKEN is unset, we WARN
        (could be on OAuth) rather than fail — matches `tycoon doctor`
        behavior from v0.1.2 #3."""
        (tmp_path / "tycoon.yml").write_text(
            "name: test\n"
            "version: 0.1.0\n"
            "database:\n"
            "  raw: data/raw.duckdb\n"
            "  warehouse: md:my_catalog\n"
            "sources: {}\n"
            "stack:\n"
            "  warehouse: motherduck\n"
        )
        from tycoon.commands import ask as ask_mod
        from tycoon.config import TycoonConfig
        from tycoon.nao import write_nao_project

        cfg = TycoonConfig(project_root=tmp_path)
        monkeypatch.setattr(ask_mod, "config", cfg)
        monkeypatch.chdir(tmp_path)
        write_nao_project(cfg)
        # Ensure no token
        monkeypatch.delenv("MOTHERDUCK_TOKEN", raising=False)

        result = cli_runner.invoke(app, ["ask", "doctor"])
        assert result.exit_code == 0, result.stdout  # WARN, not FAIL
        assert "MotherDuck auth" in result.stdout
        assert "WARN" in result.stdout


class TestAskInitLlmFlag:
    """`tycoon ask init --llm <provider>` records a provider shortcut in tycoon.yml.

    Issue #7 §5 — make LM Studio (and other providers) reachable without
    making users hand-edit YAML.
    """

    def test_unknown_provider_errors(self, project, cli_runner):
        # nao_core can't actually be missing for ask init to run, but
        # the validation happens before the nao import so this still works.
        result = cli_runner.invoke(app, ["ask", "init", "--llm", "made-up"])
        assert result.exit_code == 1
        combined = (result.stdout or "") + (result.stderr or "")
        assert "Unknown --llm" in combined

    def test_lm_studio_writes_provider_to_tycoon_yml(self, project, cli_runner):
        result = cli_runner.invoke(app, ["ask", "init", "--llm", "lm-studio"])
        # If nao_core isn't installed in the test env, ask_init exits 1 at
        # `_require_nao` before we get to the YAML write. Our test env
        # has nao-core (it's in the [ask] extra installed via uv sync
        # --all-extras), so this should succeed.
        assert result.exit_code == 0, result.stdout

        yml_text = (project / "tycoon.yml").read_text()
        assert "provider: lm-studio" in yml_text

        # And the generated nao_config.yaml expanded the shortcut to
        # OpenAI-compatible config pointed at LM Studio's default URL.
        nao_cfg = (project / ".tycoon" / "nao" / "nao_config.yaml").read_text()
        assert "base_url: http://localhost:1234/v1" in nao_cfg
        assert "api_key: lm-studio" in nao_cfg
