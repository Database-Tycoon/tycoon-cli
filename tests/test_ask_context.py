"""Tests for `tycoon ask context` (#7-related) and `tycoon ask doctor` (#7 §6).

Also covers `tycoon register llm <provider>` — the LLM provider config
flow lives in the `register` namespace (symmetric with register dbt /
register warehouse), not under `ask`. The `ask` namespace is reserved
for analytics endpoints (chat, sync, context, doctor).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tycoon.cli import app

# Captured at module-load time, BEFORE the autouse `_stub_local_llm_probe`
# fixture replaces `ask._probe_local_llm` with a stub. Tests that need
# to exercise the real probe (against a stubbed httpx) reach for this
# rather than re-importing inside the test body.
from tycoon.commands.ask import _probe_local_llm as _REAL_PROBE_LOCAL_LLM


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
    """tycoon.yml + monkey-patched config singletons for the ask
    namespace (analytics endpoints) and the register namespace (where
    register_llm lives)."""
    _write_tycoon_yml(tmp_path)

    from tycoon.commands import ask as ask_mod
    from tycoon.commands import register as register_mod
    from tycoon.config import TycoonConfig

    cfg = TycoonConfig(project_root=tmp_path)
    monkeypatch.setattr(ask_mod, "config", cfg)
    monkeypatch.setattr(register_mod, "config", cfg)
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
        # Simulate the post-register state by writing nao project files
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


class TestRegisterLlmCommand:
    """`tycoon register llm <provider>` records a provider shortcut in
    tycoon.yml and triggers setup_ask_stack (write nao config, refresh
    AGENTS.md, seed exclude_schemas, offer model install).

    Symmetric with `register dbt` / `register warehouse`. Issue #7 §5.
    """

    def test_unknown_provider_errors(self, project, cli_runner):
        result = cli_runner.invoke(app, ["register", "llm", "made-up"])
        assert result.exit_code == 1
        combined = (result.stdout or "") + (result.stderr or "")
        assert "Unknown provider" in combined

    def test_lm_studio_writes_provider_to_tycoon_yml(self, project, cli_runner):
        result = cli_runner.invoke(
            app, ["register", "llm", "lm-studio", "--skip-install"]
        )
        # nao-core must be installed for register llm; the [ask] extra
        # is in our test env via uv sync --all-extras.
        assert result.exit_code == 0, result.stdout

        yml_text = (project / "tycoon.yml").read_text()
        assert "provider: lm-studio" in yml_text

        # And the generated nao_config.yaml expanded the shortcut to
        # OpenAI-compatible config pointed at LM Studio's default URL.
        nao_cfg = (project / ".tycoon" / "nao" / "nao_config.yaml").read_text()
        assert "base_url: http://localhost:1234/v1" in nao_cfg
        assert "api_key: lm-studio" in nao_cfg

    def test_no_args_with_no_existing_provider_errors(self, project, cli_runner):
        """Re-run path requires an existing provider in tycoon.yml."""
        result = cli_runner.invoke(app, ["register", "llm"])
        assert result.exit_code == 1
        combined = (result.stdout or "") + (result.stderr or "")
        assert "No LLM provider in tycoon.yml" in combined

    def test_skip_install_bypasses_offer(self, project, cli_runner, monkeypatch):
        """--skip-install must not call _offer_model_install."""
        from tycoon.commands import ask as ask_mod

        called = []
        monkeypatch.setattr(
            ask_mod, "_offer_model_install", lambda p: called.append(p)
        )
        result = cli_runner.invoke(
            app, ["register", "llm", "ollama", "--skip-install"]
        )
        assert result.exit_code == 0, result.stdout
        assert called == []

    def test_register_offers_install_by_default(
        self, project, cli_runner, monkeypatch
    ):
        from tycoon.commands import ask as ask_mod

        called = []
        monkeypatch.setattr(
            ask_mod, "_offer_model_install", lambda p: called.append(p)
        )
        result = cli_runner.invoke(app, ["register", "llm", "ollama"])
        assert result.exit_code == 0, result.stdout
        assert called == ["ollama"]


class TestRegisterLlmSeedExcludeSchemas:
    """Issue #7 §3: registering an LLM provider should seed
    `ask.exclude_schemas` with conservative noise patterns when the
    user hasn't configured either include_schemas or exclude_schemas
    yet. Triggered via `register llm`'s call to setup_ask_stack."""

    def test_seeds_defaults_when_unset(self, project, cli_runner):
        result = cli_runner.invoke(
            app, ["register", "llm", "lm-studio", "--skip-install"]
        )
        assert result.exit_code == 0, result.stdout

        import yaml as _y
        data = _y.safe_load((project / "tycoon.yml").read_text())
        excludes = data["ask"]["exclude_schemas"]
        assert "information_schema" in excludes
        assert "_tycoon" in excludes
        assert "sqlmesh__main" in excludes

    def _rewrite_with_ask(self, project, ask_block: str, monkeypatch):
        """Rewrite tycoon.yml with a custom `ask` block, then refresh
        the cached config so the next register llm call sees it.

        Rebinds both ask_mod and register_mod since setup_ask_stack
        (called by register_llm) reads the ask_mod-scoped config."""
        existing = (project / "tycoon.yml").read_text()
        (project / "tycoon.yml").write_text(existing + ask_block)
        from tycoon.commands import ask as ask_mod
        from tycoon.commands import register as register_mod
        from tycoon.config import TycoonConfig

        cfg = TycoonConfig(project_root=project)
        monkeypatch.setattr(register_mod, "config", cfg)
        monkeypatch.setattr(ask_mod, "config", cfg)

    def test_preserves_user_set_include_schemas(self, project, cli_runner, monkeypatch):
        self._rewrite_with_ask(
            project,
            "ask:\n  include_schemas: [mart]\n  llm:\n    provider: lm-studio\n",
            monkeypatch,
        )
        result = cli_runner.invoke(app, ["register", "llm", "--skip-install"])
        assert result.exit_code == 0, result.stdout

        import yaml as _y
        data = _y.safe_load((project / "tycoon.yml").read_text())
        assert data["ask"]["include_schemas"] == ["mart"]
        # exclude_schemas left empty since include_schemas already constrained the surface
        assert not data["ask"].get("exclude_schemas", [])

    def test_preserves_user_set_exclude_schemas(self, project, cli_runner, monkeypatch):
        self._rewrite_with_ask(
            project,
            "ask:\n  exclude_schemas: [my_custom_noise]\n  llm:\n    provider: lm-studio\n",
            monkeypatch,
        )
        result = cli_runner.invoke(app, ["register", "llm", "--skip-install"])
        assert result.exit_code == 0, result.stdout

        import yaml as _y
        data = _y.safe_load((project / "tycoon.yml").read_text())
        # User's value preserved; defaults NOT merged in.
        assert data["ask"]["exclude_schemas"] == ["my_custom_noise"]


class TestProbeLocalLlm:
    """Provider-specific probe behavior. Issue: LM Studio's
    ``GET /v1/models`` returns DOWNLOADED models regardless of load
    state, so counting it gives a misleading "N model(s) loaded"
    when 0 are actually held in memory. Fix: hit the richer
    ``/api/v0/models`` endpoint for LM Studio and count only
    ``state == "loaded"`` rows.
    """

    def test_lm_studio_uses_v0_endpoint_and_filters_loaded(self, monkeypatch):
        """LM Studio probe must distinguish downloaded from loaded."""
        from tycoon.commands import ask as ask_mod

        # Restore the real probe (autouse stub replaced it).
        monkeypatch.setattr(ask_mod, "_probe_local_llm", _REAL_PROBE_LOCAL_LLM)

        # Stub httpx so we can simulate LM Studio's /api/v0/models response.
        recorded_urls: list[str] = []

        class _StubResp:
            def __init__(self, status: int, body: dict):
                self.status_code = status
                self._body = body

            def json(self):
                return self._body

        class _StubClient:
            def __init__(self, *_a, **_kw):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_a):
                return False

            def get(self, url):
                recorded_urls.append(url)
                # Mimic LM Studio: 2 models DOWNLOADED, 0 LOADED.
                return _StubResp(
                    200,
                    {
                        "data": [
                            {
                                "id": "google/gemma-4-26b-a4b",
                                "state": "not-loaded",
                            },
                            {
                                "id": "text-embedding-nomic-embed-text-v1.5",
                                "state": "not-loaded",
                            },
                        ]
                    },
                )

        import httpx
        monkeypatch.setattr(httpx, "Client", _StubClient)

        reachable, count, err = _REAL_PROBE_LOCAL_LLM(
            "http://localhost:1234/v1", provider="lm-studio"
        )
        # Critical assertion: 0 loaded even though 2 are downloaded.
        # Without the v0-endpoint fix, this would say 2.
        assert reachable is True
        assert count == 0, (
            f"expected 0 loaded models, got {count} — probe is "
            f"counting downloaded models instead of loaded"
        )
        assert err is None
        # Verify the v0 endpoint was actually called.
        assert any("/api/v0/models" in u for u in recorded_urls)

    def test_lm_studio_v0_counts_loaded_models(self, monkeypatch):
        """When some models ARE loaded, count them correctly."""
        from tycoon.commands import ask as ask_mod
        from tycoon.commands.ask import _probe_local_llm

        monkeypatch.setattr(ask_mod, "_probe_local_llm", _probe_local_llm)

        class _StubResp:
            def __init__(self, body):
                self.status_code = 200
                self._body = body

            def json(self):
                return self._body

        class _StubClient:
            def __init__(self, *_a, **_kw):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_a):
                return False

            def get(self, url):
                return _StubResp(
                    {
                        "data": [
                            {"id": "qwen2.5-coder", "state": "loaded"},
                            {"id": "embedding", "state": "loaded"},
                            {"id": "llama-3", "state": "not-loaded"},
                        ]
                    }
                )

        import httpx
        monkeypatch.setattr(httpx, "Client", _StubClient)

        reachable, count, _ = _REAL_PROBE_LOCAL_LLM(
            "http://localhost:1234/v1", provider="lm-studio"
        )
        assert reachable is True
        assert count == 2  # qwen + embedding loaded; llama not

    def test_ollama_uses_v1_models(self, monkeypatch):
        """Ollama doesn't expose a v0 endpoint; v1/models is fine since
        Ollama auto-loads on first request."""
        from tycoon.commands import ask as ask_mod
        from tycoon.commands.ask import _probe_local_llm

        monkeypatch.setattr(ask_mod, "_probe_local_llm", _probe_local_llm)

        recorded_urls: list[str] = []

        class _StubResp:
            def __init__(self, body):
                self.status_code = 200
                self._body = body

            def json(self):
                return self._body

        class _StubClient:
            def __init__(self, *_a, **_kw):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_a):
                return False

            def get(self, url):
                recorded_urls.append(url)
                return _StubResp({"data": [{"id": "llama3.2"}]})

        import httpx
        monkeypatch.setattr(httpx, "Client", _StubClient)

        reachable, count, _ = _REAL_PROBE_LOCAL_LLM(
            "http://localhost:11434/v1", provider="ollama"
        )
        assert reachable is True
        assert count == 1
        # Ollama should NOT be hit at /api/v0/models (LM-Studio-only).
        assert all("/api/v0/models" not in u for u in recorded_urls)


class TestAskChatRequiresLLM:
    """`tycoon ask chat` must fail-fast with a directing error when no
    LLM provider is configured. Launching Nao with no brain is a worse
    UX than refusing — the chat UI sits there doing nothing.
    """

    def test_chat_errors_when_no_llm_configured(self, project, cli_runner):
        # The base project fixture writes a tycoon.yml with no `ask:` block.
        result = cli_runner.invoke(app, ["ask", "chat"])
        assert result.exit_code == 1
        combined = (result.stdout or "") + (result.stderr or "")
        assert "No LLM configured" in combined
        # Surfaces the specific commands the user can run to fix it.
        assert "tycoon register llm" in combined

    def test_chat_errors_when_lm_studio_unreachable(
        self, project, cli_runner, monkeypatch
    ):
        # Configure LM Studio at an unreachable URL so the probe fails.
        existing = (project / "tycoon.yml").read_text()
        (project / "tycoon.yml").write_text(
            existing
            + "ask:\n  llm:\n    provider: lm-studio\n    base_url: http://127.0.0.1:1/v1\n"
        )
        from tycoon.commands import ask as ask_mod
        from tycoon.config import TycoonConfig
        monkeypatch.setattr(ask_mod, "config", TycoonConfig(project_root=project))

        result = cli_runner.invoke(app, ["ask", "chat"])
        assert result.exit_code == 1
        combined = (result.stdout or "") + (result.stderr or "")
        assert "not reachable" in combined
        assert "LM Studio" in combined

    def test_chat_errors_when_no_models_loaded(
        self, project, cli_runner, monkeypatch
    ):
        # Configure LM Studio at a URL that responds 200 but with 0 models.
        existing = (project / "tycoon.yml").read_text()
        (project / "tycoon.yml").write_text(
            existing
            + "ask:\n  llm:\n    provider: lm-studio\n    base_url: http://stub/v1\n"
        )
        from tycoon.commands import ask as ask_mod
        from tycoon.config import TycoonConfig
        monkeypatch.setattr(ask_mod, "config", TycoonConfig(project_root=project))
        # Stub the probe to simulate "reachable, 0 models".
        monkeypatch.setattr(
            ask_mod, "_probe_local_llm", lambda *_a, **_kw: (True, 0, None)
        )

        result = cli_runner.invoke(app, ["ask", "chat"])
        assert result.exit_code == 1
        combined = (result.stdout or "") + (result.stderr or "")
        assert "0 models loaded" in combined
        # Provider-specific install hint surfaced.
        assert "LM Studio" in combined or "Discover" in combined


class TestOfferModelInstall:
    """The probe-and-offer flow that runs at the tail of `tycoon init`
    (when wizard picks a local LLM) and `tycoon register llm <p>`.

    Calls `_offer_model_install` directly rather than via the CLI so we
    can exhaustively cover the four states (cloud / unreachable / ready /
    needs-install) without rebuilding init scaffolding each time.
    """

    def _call(self, monkeypatch, provider, *, reachable, model_count, has_ollama=True):
        from tycoon.commands import ask as ask_mod

        monkeypatch.setattr(
            ask_mod, "_probe_local_llm",
            lambda *_a, **_kw: (reachable, model_count, None if reachable else "stub error"),
        )
        # Pretend `ollama` binary is / isn't on PATH.
        import shutil
        monkeypatch.setattr(
            shutil, "which", lambda name: "/usr/bin/ollama" if (has_ollama and name == "ollama") else None
        )
        # Don't actually shell out.
        import subprocess as _sp
        run_calls = []
        def fake_run(cmd, *a, **kw):
            run_calls.append(cmd)
            class R:
                returncode = 0
            return R()
        monkeypatch.setattr(_sp, "run", fake_run)
        # Auto-confirm the prompt.
        import typer as _t
        monkeypatch.setattr(_t, "confirm", lambda *a, **kw: True)
        ask_mod._offer_model_install(provider)
        return run_calls

    def test_cloud_provider_is_noop(self, monkeypatch):
        calls = self._call(monkeypatch, "anthropic", reachable=False, model_count=0)
        assert calls == []

    def test_unreachable_warns_no_pull(self, monkeypatch):
        calls = self._call(monkeypatch, "ollama", reachable=False, model_count=0)
        assert calls == []  # Did not attempt `ollama pull`.

    def test_ready_state_no_pull(self, monkeypatch):
        calls = self._call(monkeypatch, "ollama", reachable=True, model_count=2)
        assert calls == []

    def test_ollama_zero_models_pulls(self, monkeypatch):
        calls = self._call(monkeypatch, "ollama", reachable=True, model_count=0)
        assert len(calls) == 1
        assert calls[0][0] == "ollama"
        assert calls[0][1] == "pull"
        assert calls[0][2] == "qwen2.5-coder:7b"  # the recommended tag

    def test_ollama_zero_models_no_binary(self, monkeypatch):
        # Ollama binary not on PATH — falls back to printed instructions.
        calls = self._call(
            monkeypatch, "ollama", reachable=True, model_count=0, has_ollama=False
        )
        assert calls == []

    def test_lm_studio_zero_models_no_pull(self, monkeypatch):
        # LM Studio has no auto-pull path; we just print instructions.
        calls = self._call(monkeypatch, "lm-studio", reachable=True, model_count=0)
        assert calls == []


