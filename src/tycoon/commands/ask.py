"""tycoon ask — AI analytics agent powered by Nao."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tycoon.config import config
from tycoon.utils.console import error, info, next_steps, success, warn

app = typer.Typer(help="AI analytics agent — query your data in natural language.")
skills_app = typer.Typer(help="Manage Nao skills.")
mcp_app = typer.Typer(help="Manage MCP server configuration.")

app.add_typer(skills_app, name="skills")
app.add_typer(mcp_app, name="mcp")

console = Console()

_SKILL_TEMPLATE = """\
---
name: {name}
description: "Describe when this skill should trigger"
---

## Requirements
- Table: analytics.your_table

## SQL
```sql
SELECT ...
FROM analytics.your_table
LIMIT 10
```

## Output Format
| column | description |
|--------|-------------|
"""


def _default_exclude_schemas() -> list[str]:
    """Conservative noise list for the `ask.exclude_schemas` seed.

    These are schemas a user almost never wants their AI agent
    iterating: DuckDB system schemas, the auto-generated _tycoon
    observability staging layer, and stale schemas from prior
    transformation-tool migrations (sqlmesh, dlt internals).

    Glob patterns aren't supported in include/exclude_schemas as of
    v0.1.5 — these are exact-match names. Add more patterns as users
    surface new noise sources.
    """
    return [
        "information_schema",
        "pg_catalog",
        "main_pg_catalog",
        "system",
        "_tycoon",
        "sqlmesh__main",
        "sqlmesh",
    ]


def _local_llm_base_url(llm) -> str | None:
    """Default OpenAI-compat base_url for our two local-LLM shortcuts.

    Returns None for cloud providers (no probe is meaningful — the
    endpoint is always reachable, the question is whether the API key
    works, which doctor doesn't validate to avoid burning round-trips).
    """
    if llm is None:
        return None
    if llm.base_url:
        return llm.base_url
    from tycoon.nao import _LM_STUDIO_PRESET, _OLLAMA_PRESET

    if llm.provider == "lm-studio":
        return _LM_STUDIO_PRESET["base_url"]
    if llm.provider == "ollama":
        return _OLLAMA_PRESET["base_url"]
    return None


def _probe_local_llm(base_url: str) -> tuple[bool, int, str | None]:
    """Hit ``GET <base_url>/models`` to count loaded models.

    Returns ``(reachable, model_count, error_message)``. Both LM Studio
    and Ollama (since 0.1.27) expose the OpenAI-compatible endpoint at
    ``/models`` — same probe works for both.

    Used by `tycoon ask doctor` and the pre-launch check in
    `tycoon ask chat`. Bounded at 2s so doctor stays snappy.
    """
    try:
        import httpx

        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"{base_url}/models")
        if resp.status_code != 200:
            return False, 0, f"HTTP {resp.status_code}"
        data = (resp.json() or {}).get("data") or []
        return True, len(data), None
    except Exception as exc:
        return False, 0, str(exc)


_RECOMMENDED_MODEL = {
    # Qwen 2.5 Coder 7B Instruct — Q4_K_M quant, ~4.7 GB. Tuned
    # specifically for code (SQL inclusive); outperforms Llama 3.1 8B on
    # coding benchmarks (HumanEval 88.4%). Comfortably under our 8 GB
    # ceiling. Same weights work for both Ollama and LM Studio. See
    # `docs/recipes/lm-studio-local-llm.md` for the rationale.
    "display_name": "Qwen 2.5 Coder 7B Instruct (Q4_K_M, ~4.7 GB)",
    "ollama_tag": "qwen2.5-coder:7b",
    "lm_studio_search": "Qwen2.5-Coder-7B-Instruct-GGUF",
    "lm_studio_quant": "Q4_K_M",
}


def _offer_model_install(provider: str) -> None:
    """Probe the local LLM provider and, if no model is loaded, offer
    to install the recommended one. Best-effort — bails quietly if the
    runtime isn't reachable, the binary isn't on PATH, or the user
    declines. The rest of tycoon works without an LLM, so we never
    fail the calling command on this path.

    For Ollama: auto-pulls via ``ollama pull <tag>`` (CLI-friendly,
    streams progress to the user). For LM Studio: prints the GUI
    instructions because there's no clean CLI install flow.
    """
    if provider not in ("lm-studio", "ollama"):
        return  # Cloud providers — nothing to install locally.

    label = "LM Studio" if provider == "lm-studio" else "Ollama"

    # Probe takes a config-like shape — synthesize one from the preset.
    from tycoon.nao import _LM_STUDIO_PRESET, _OLLAMA_PRESET

    base_url = (
        _LM_STUDIO_PRESET["base_url"]
        if provider == "lm-studio"
        else _OLLAMA_PRESET["base_url"]
    )
    reachable, model_count, err = _probe_local_llm(base_url)

    if not reachable:
        warn(
            f"{label} not reachable at {base_url} ({err}). "
            f"Start the {label} app/server, then run "
            f"[bold]tycoon ask doctor[/bold] to verify."
        )
        info(_model_install_hint(provider))
        return

    if model_count >= 1:
        success(
            f"{label} ready: {model_count} model(s) already loaded at "
            f"{base_url}."
        )
        return

    # Reachable, 0 models — offer the install.
    rec = _RECOMMENDED_MODEL
    warn(f"{label} reachable at {base_url} but 0 models are loaded.")

    if provider == "lm-studio":
        # No clean LM Studio CLI flow — just surface the GUI steps.
        info(_model_install_hint("lm-studio"))
        return

    # Ollama path: try the auto-pull if the binary is on PATH.
    import shutil

    if shutil.which("ollama") is None:
        warn("`ollama` binary not found on PATH — can't auto-pull.")
        info(_model_install_hint("ollama"))
        return

    if not typer.confirm(
        f"Pull the recommended model [bold]{rec['ollama_tag']}[/bold] "
        f"([dim]{rec['display_name']}[/dim]) now?",
        default=True,
    ):
        info(_model_install_hint("ollama"))
        return

    info(
        f"Running [bold]ollama pull {rec['ollama_tag']}[/bold]. "
        "This may take several minutes on first run..."
    )
    pull = subprocess.run(["ollama", "pull", rec["ollama_tag"]])
    if pull.returncode == 0:
        success(f"Pulled {rec['ollama_tag']} — chat is ready.")
    else:
        warn(
            f"`ollama pull` exited {pull.returncode}. Try manually: "
            f"[bold]ollama pull {rec['ollama_tag']}[/bold]"
        )


def _model_install_hint(provider: str) -> str:
    """User-facing instructions for getting a model loaded for the local
    LLM provider. LM Studio is GUI-driven; Ollama has a clean CLI flow.

    Recommends the same model on both providers (Qwen 2.5 Coder 7B) so
    users get consistent SQL/analytics behavior regardless of runtime.
    """
    rec = _RECOMMENDED_MODEL
    if provider == "lm-studio":
        return (
            f"Recommended: [bold]{rec['display_name']}[/bold].\n"
            f"Open LM Studio → click [bold]Discover[/bold] → search "
            f"[bold]{rec['lm_studio_search']}[/bold] → pick the "
            f"[bold]{rec['lm_studio_quant']}[/bold] quant → Download → Load.\n"
            "After loading, re-run the command."
        )
    if provider == "ollama":
        return (
            f"Recommended: [bold]{rec['display_name']}[/bold].\n"
            f"Run [bold]ollama pull {rec['ollama_tag']}[/bold] "
            "(Ollama auto-loads on first request — no separate Load step)."
        )
    return ""


def _require_nao() -> None:
    try:
        import nao_core  # noqa: F401
    except ImportError:
        error("Nao is not installed. Run: [bold]pip install 'database-tycoon[ask]'[/bold]")
        raise typer.Exit(1)


def _require_project() -> None:
    if not config.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)


def _nao_executable() -> str:
    """Find the `nao` binary, preferring the one co-located with this Python.

    ``nao-core`` ships a ``nao`` console script but no ``__main__.py``, so
    ``python -m nao_core`` fails with ``No module named nao_core.__main__``.
    Mirror the dbt helper: resolve the venv bin first, then ``$PATH``.
    """
    venv_nao = Path(sys.executable).parent / "nao"
    if venv_nao.exists():
        return str(venv_nao)
    nao = shutil.which("nao")
    if not nao:
        error("`nao` not found. Reinstall: [bold]pip install 'database-tycoon[ask]'[/bold]")
        raise typer.Exit(1)
    return nao


def _nao_env() -> dict[str, str]:
    """Environment for nao subprocess.

    - ``NAO_DEFAULT_PROJECT_PATH`` — tells nao where its project root is.
    - ``DB_URI`` — keeps Nao's SQLite chat DB in ``.tycoon/nao/db.sqlite``
      instead of inside the venv (``nao_core/bin/db.sqlite``), so chat
      history survives ``uv sync``, venv rebuilds, and tycoon upgrades.
    """
    db_path = config.nao_dir / "db.sqlite"
    return {
        **os.environ,
        "NAO_DEFAULT_PROJECT_PATH": str(config.nao_dir),
        "DB_URI": f"sqlite:{db_path}",
    }


def _skills_dir() -> Path:
    """Resolve the skills directory from config or default."""
    ask = config.project.ask if config.project else None
    if ask and ask.skills_dir:
        return Path(ask.skills_dir)
    return config.nao_dir / "agent" / "skills"


def _mcp_path() -> Path:
    """Resolve the mcp.json path."""
    return config.nao_dir / "agent" / "mcps" / "mcp.json"


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Parse YAML frontmatter from a markdown file (key: value lines only)."""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    result: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"')
    return result


# ---------------------------------------------------------------------------
# Core ask commands
# ---------------------------------------------------------------------------


def _refresh_agents_md(cfg=None) -> None:
    """Write or refresh AGENTS.md at the project root.

    Best-effort: never raises. Prints a hint when a user-authored
    AGENTS.md is preserved so the user knows tycoon's pointer file
    isn't getting refreshed.
    """
    from tycoon.nao import write_agents_md

    wrote, path = write_agents_md(cfg if cfg is not None else config)
    if wrote:
        info(f"AGENTS.md refreshed at [bold]{path}[/bold]")
    else:
        warn(
            f"AGENTS.md at [bold]{path}[/bold] is user-authored "
            "(no tycoon sentinel) — left alone. Delete the file to let "
            "[bold]tycoon ask[/bold] manage it again."
        )


def setup_ask_stack(cfg=None) -> None:
    """Run the post-LLM-config setup: seed exclude_schemas, write
    nao_config.yaml, refresh AGENTS.md, and offer a model install if a
    local provider is configured.

    Idempotent — preserves user-set values, skips writes when nothing
    needs to change. Both `tycoon register llm` and the chained call
    from `tycoon init` go through this so the UX is identical.

    ``cfg`` defaults to the module-level ``config`` singleton; pass an
    explicit ``TycoonConfig`` from callers (e.g. ``tycoon init``) that
    just wrote a new tycoon.yml and need a fresh view without mutating
    module-level state.

    Caller must ensure ``nao_core`` is importable (run ``_require_nao()``
    or do an ImportError-safe import) — this function uses
    ``write_nao_project`` which depends on it.
    """
    from tycoon.nao import write_nao_project
    from tycoon.project import AskConfig, save_project

    if cfg is None:
        cfg = config
    project = cfg.project

    # Seed exclude_schemas defaults (issue #7 §3). Skip if the user
    # already populated either include_schemas or exclude_schemas.
    if project is not None:
        ask = project.ask
        already_configured = ask is not None and (
            ask.include_schemas or ask.exclude_schemas
        )
        if not already_configured:
            defaults = _default_exclude_schemas()
            if ask is None:
                project.ask = AskConfig(exclude_schemas=defaults)
            else:
                ask.exclude_schemas = defaults
            info(
                f"Seeded [bold]ask.exclude_schemas[/bold] with "
                f"{len(defaults)} noise patterns "
                "(DuckDB internals, _tycoon staging, sqlmesh leftovers)."
            )
            save_project(project, cfg.root)
            cfg.reload()

    write_nao_project(cfg)
    _refresh_agents_md(cfg)
    success(f"Nao config written to [bold]{cfg.nao_dir}[/bold]")

    # Local-runtime probe + install offer. Best-effort.
    project = cfg.project  # re-read after the seed branch may have saved
    final_provider = (
        project.ask.llm.provider
        if project is not None and project.ask is not None and project.ask.llm is not None
        else None
    )
    if final_provider in ("lm-studio", "ollama"):
        _offer_model_install(final_provider)


@app.command("sync")
def ask_sync(
    reinit: bool = typer.Option(False, "--reinit", help="Regenerate nao_config.yaml before syncing"),
) -> None:
    """Sync DB schema and dbt context into Nao."""
    _require_project()
    _require_nao()

    if reinit:
        from tycoon.nao import write_nao_project
        write_nao_project(config)
        info("Config regenerated.")

    if not (config.nao_dir / "nao_config.yaml").exists():
        error("No nao_config.yaml found. Run [bold]tycoon register llm[/bold] first.")
        raise typer.Exit(1)

    info("Syncing Nao context...")
    result = subprocess.run(
        [_nao_executable(), "sync"],
        cwd=str(config.nao_dir),
        env=_nao_env(),
    )
    if result.returncode != 0:
        error("nao sync failed.")
        raise typer.Exit(result.returncode)

    _refresh_agents_md()

    success("Context synced.")
    next_steps(
        ("tycoon ask chat", "start querying your data in natural language"),
        ("tycoon ask context --table <table>", "pipe table context into any agent"),
    )


@app.command("chat")
def ask_chat(
    port: int = typer.Option(0, help="Port override (default: from tycoon.yml or 5005)"),
) -> None:
    """Launch the Nao chat UI in your browser.

    Automatically runs init and sync on first use if not already done.

    Requires an LLM provider to be configured in tycoon.yml's
    ``ask.llm.provider`` field. The chat UI is unusable without one
    (Nao has nothing to ask), so we fail fast with a directing error
    rather than launching a dead UI.
    """
    _require_project()
    _require_nao()

    # No LLM configured → chat is unusable. Direct the user to
    # `tycoon register llm <provider>` (or re-run `tycoon init` to
    # pick one in the wizard).
    project = config.project
    has_llm = project is not None and project.ask is not None and project.ask.llm is not None
    if not has_llm:
        error(
            "No LLM configured. `tycoon ask chat` needs a provider in "
            "[bold]ask.llm.provider[/bold] to do anything useful."
        )
        info(
            "Run one of:\n"
            "  [bold]tycoon register llm lm-studio[/bold]   "
            "(local, recommended — install LM Studio first)\n"
            "  [bold]tycoon register llm ollama[/bold]      "
            "(local — install Ollama first)\n"
            "  [bold]tycoon register llm openai[/bold]      "
            "(needs OPENAI_API_KEY)\n"
            "  [bold]tycoon register llm anthropic[/bold]   "
            "(needs ANTHROPIC_API_KEY)"
        )
        raise typer.Exit(1)

    # Local-LLM model check: server up + at least one model loaded.
    # Catches the "installed LM Studio but didn't download a model"
    # case which would otherwise show a working-looking chat UI that
    # errors on first message.
    llm = project.ask.llm
    if llm.provider in ("lm-studio", "ollama"):
        base_url = _local_llm_base_url(llm)
        if base_url:
            reachable, model_count, probe_err = _probe_local_llm(base_url)
            label = "LM Studio" if llm.provider == "lm-studio" else "Ollama"
            if not reachable:
                error(
                    f"{label} not reachable at [bold]{base_url}[/bold] "
                    f"({probe_err}). Start the {label} app/server, then re-run."
                )
                raise typer.Exit(1)
            if model_count == 0:
                error(
                    f"{label} is reachable at [bold]{base_url}[/bold] but "
                    f"has 0 models loaded — chat would have nothing to ask."
                )
                info(_model_install_hint(llm.provider))
                raise typer.Exit(1)

    # Auto-init if no config exists yet
    nao_config = config.nao_dir / "nao_config.yaml"
    if not nao_config.exists():
        info("No nao_config.yaml found — running [bold]tycoon register llm[/bold] automatically...")
        from tycoon.nao import write_nao_project
        write_nao_project(config)
        success(f"Nao config written to [bold]{config.nao_dir}[/bold]")

    # Auto-sync if context DB hasn't been built yet
    context_ready = (config.nao_dir / "databases").exists()
    if not context_ready:
        info("Context not yet synced — running [bold]tycoon ask sync[/bold] automatically...")
        result = subprocess.run(
            [_nao_executable(), "sync"],
            cwd=str(config.nao_dir),
            env=_nao_env(),
        )
        if result.returncode != 0:
            error("nao sync failed. Run [bold]tycoon ask sync[/bold] to debug.")
            raise typer.Exit(result.returncode)

    # Resolve port: CLI flag > tycoon.yml > default
    resolved_port = port
    if not resolved_port and config.project and config.project.ask:
        resolved_port = config.project.ask.port
    if not resolved_port:
        resolved_port = 5005

    info(f"Starting Nao chat at [bold]http://localhost:{resolved_port}[/bold]")
    subprocess.run(
        [_nao_executable(), "chat", "--port", str(resolved_port)],
        cwd=str(config.nao_dir),
        env=_nao_env(),
    )


@app.command("context")
def ask_context(
    table: str | None = typer.Option(None, "--table", "-t", help="Filter to a single table name."),
    schema: str | None = typer.Option(None, "--schema", "-s", help="Filter to a single schema name."),
    include_dbt: bool = typer.Option(False, "--include-dbt", help="Also dump synced dbt model SQL."),
    rules_only: bool = typer.Option(False, "--rules-only", help="Only print RULES.md."),
) -> None:
    """Print Nao-synced context for a table/schema. Pipe into any agent.

    Output goes to stdout as plain markdown so it composes with
    ``tycoon ask context --table foo | claude -p "explain this table"``.
    """
    _require_project()

    nao_dir = config.nao_dir
    if not nao_dir.exists():
        error("No Nao context found. Run [bold]tycoon ask sync[/bold] first.")
        raise typer.Exit(1)

    if rules_only:
        rules = nao_dir / "RULES.md"
        if not rules.exists():
            error(f"No RULES.md at [bold]{rules}[/bold]. Run [bold]tycoon register llm[/bold].")
            raise typer.Exit(1)
        typer.echo(rules.read_text(), nl=False)
        return

    db_root = nao_dir / "databases"
    if not db_root.exists():
        error("No Nao database context. Run [bold]tycoon ask sync[/bold] first.")
        raise typer.Exit(1)

    # Collect every synced table dir, optionally filtered.
    candidates: list[Path] = []
    for table_dir in db_root.glob("type=*/database=*/schema=*/table=*"):
        t = table_dir.name.removeprefix("table=")
        s = table_dir.parent.name.removeprefix("schema=")
        if table is not None and t != table:
            continue
        if schema is not None and s != schema:
            continue
        candidates.append(table_dir)

    candidates.sort()

    # No filters and no candidates → nothing synced. Filter present and no
    # candidates → user typo. Distinguish so the message is useful.
    if not candidates:
        if table is None and schema is None:
            error("No tables in Nao context. Run [bold]tycoon ask sync[/bold] first.")
        else:
            filt = ", ".join(f"{k}={v}" for k, v in (("table", table), ("schema", schema)) if v)
            error(f"No Nao context matched {filt}. Run [bold]tycoon ask context[/bold] (no flags) to list.")
        raise typer.Exit(1)

    # Listing mode: no filters, just print available tables.
    if table is None and schema is None and not include_dbt:
        typer.echo("# Available Nao context\n")
        for table_dir in candidates:
            t = table_dir.name.removeprefix("table=")
            s = table_dir.parent.name.removeprefix("schema=")
            typer.echo(f"- {s}.{t}")
        typer.echo(
            "\nRun `tycoon ask context --table <name>` "
            "or `--schema <name>` to print a table's columns + preview."
        )
        return

    # Selected mode: cat columns.md + preview.md per matching table.
    for table_dir in candidates:
        for filename in ("columns.md", "preview.md"):
            f = table_dir / filename
            if f.exists():
                typer.echo(f.read_text(), nl=False)
                typer.echo("")  # blank line between sections

    if include_dbt:
        dbt_root = nao_dir / "repos" / "dbt" / "models"
        if dbt_root.exists():
            for sql in sorted(dbt_root.rglob("*.sql")):
                typer.echo(f"\n# {sql.relative_to(dbt_root)}\n")
                typer.echo("```sql")
                typer.echo(sql.read_text(), nl=False)
                typer.echo("```")


# ---------------------------------------------------------------------------
# Doctor — health check for the ask stack
# ---------------------------------------------------------------------------


@app.command("doctor")
def ask_doctor() -> None:
    """Check the health of the ``tycoon ask`` setup.

    Validates the four most common breakage modes called out in issue
    #7: missing nao_config.yaml, missing required directories, missing
    MotherDuck auth (token or OAuth), and an unreachable LM Studio
    endpoint when configured. Reports a pass/warn/fail per check using
    the same status_table layout as ``tycoon doctor``.
    """
    from tycoon.utils.console import status_table
    from tycoon.nao import _NAO_REQUIRED_DIRS

    _require_project()

    nao_dir = config.nao_dir
    rows: list[tuple[str, str, str]] = []

    # 1. nao_config.yaml present?
    cfg_path = nao_dir / "nao_config.yaml"
    if cfg_path.exists():
        rows.append(("nao_config.yaml", "OK", str(cfg_path)))
    else:
        rows.append(
            ("nao_config.yaml", "FAIL", "missing — run `tycoon register llm`")
        )

    # 2. Required directories present?
    missing = [d for d in _NAO_REQUIRED_DIRS if not (nao_dir / d).exists()]
    if not missing:
        rows.append(("nao directories", "OK", f"all {len(_NAO_REQUIRED_DIRS)} present"))
    else:
        rows.append(
            (
                "nao directories",
                "FAIL",
                f"missing: {', '.join(missing)} — run `tycoon register llm`",
            )
        )

    # 3. Warehouse auth — only check MotherDuck. Local DuckDB has no auth.
    project = config.project
    warehouse_path = project.database.warehouse if project else ""
    if warehouse_path.startswith("md:"):
        token = os.environ.get("MOTHERDUCK_TOKEN")
        if token:
            rows.append(
                (
                    "MotherDuck auth",
                    "OK",
                    f"MOTHERDUCK_TOKEN set ({len(token)} chars)",
                )
            )
        else:
            # Possible OAuth — we can't verify without trying a connection.
            # Fall through to a soft warning.
            rows.append(
                (
                    "MotherDuck auth",
                    "WARN",
                    "MOTHERDUCK_TOKEN not set — relying on OAuth (run `tycoon doctor` for full check)",
                )
            )
    else:
        rows.append(("Warehouse", "OK", "local DuckDB (no auth)"))

    # 4. LLM endpoint — probe local providers (LM Studio / Ollama) for
    #    reachability AND for a non-zero loaded-model count. Cloud
    #    providers aren't probed because key validation is a network
    #    round-trip every doctor run; we just confirm the provider is
    #    set.
    llm = project.ask.llm if project and project.ask else None
    label_for = {"lm-studio": "LM Studio", "ollama": "Ollama"}
    if llm and llm.provider in ("lm-studio", "ollama"):
        label = label_for[llm.provider]
        base_url = _local_llm_base_url(llm)
        reachable, model_count, err = _probe_local_llm(base_url) if base_url else (False, 0, "no base_url")
        if not reachable:
            rows.append((label, "FAIL", f"{base_url} unreachable: {err}"))
        elif model_count == 0:
            rows.append(
                (
                    label,
                    "FAIL",
                    f"{base_url} reachable but 0 models loaded — "
                    f"`tycoon ask chat` will be unusable. "
                    f"{_model_install_hint(llm.provider)}",
                )
            )
        else:
            rows.append(
                (label, "OK", f"{base_url} responded ({model_count} model(s) loaded)")
            )
    elif llm:
        rows.append(("LLM", "OK", f"provider={llm.provider} (no probe)"))
    else:
        rows.append(
            (
                "LLM",
                "WARN",
                "no provider configured — `tycoon ask chat` unavailable. "
                "Run `tycoon register llm<provider>` to enable.",
            )
        )

    console.print(status_table(rows, title="tycoon ask doctor"))

    # Exit non-zero on any FAIL so this command is CI-friendly.
    if any(status == "FAIL" for _, status, _ in rows):
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Skills sub-commands
# ---------------------------------------------------------------------------


@skills_app.command("list")
def skills_list() -> None:
    """List all skills in the skills directory."""
    skills_dir = _skills_dir()
    if not skills_dir.exists():
        info("No skills found.")
        return

    skill_files = sorted(skills_dir.glob("*.md"))
    if not skill_files:
        info("No skills found.")
        return

    table = Table(title="Nao Skills", show_header=True, header_style="bold")
    table.add_column("Name", style="bold cyan")
    table.add_column("Description")
    table.add_column("File", style="dim")

    for skill_file in skill_files:
        fm = _parse_frontmatter(skill_file.read_text())
        name = fm.get("name", skill_file.stem)
        description = fm.get("description", "")
        table.add_row(name, description, skill_file.name)

    console.print(table)


@skills_app.command("new")
def skills_new(
    name: str = typer.Argument(..., help="Skill name (used as filename and frontmatter name)."),
) -> None:
    """Scaffold a new skill file."""
    skills_dir = _skills_dir()
    skills_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{name}.md"
    skill_path = skills_dir / filename

    if skill_path.exists():
        warn(f"Skill file already exists: [bold]{skill_path}[/bold]")
        raise typer.Exit(1)

    skill_path.write_text(_SKILL_TEMPLATE.format(name=name))
    success(f"Skill created: [bold]{skill_path}[/bold]")
    next_steps(
        ("tycoon ask skills list", "see all available skills"),
        ("tycoon ask chat", "start a chat session to use the skill"),
    )


# ---------------------------------------------------------------------------
# MCP sub-commands
# ---------------------------------------------------------------------------

_MCP_SERVERS: dict[str, dict] = {
    "metabase": {
        "command": "npx",
        "args": ["-y", "@getnao/metabase-mcp-server@latest"],
        "env": {
            "METABASE_URL": "${METABASE_URL}",
            "METABASE_API_KEY": "${METABASE_API_KEY}",
        },
    }
}


@mcp_app.command("list")
def mcp_list() -> None:
    """List configured MCP servers."""
    mcp_path = _mcp_path()
    if not mcp_path.exists():
        info("No MCP servers configured.")
        return

    data = json.loads(mcp_path.read_text())
    servers = data.get("mcpServers", {})
    if not servers:
        info("No MCP servers configured.")
        return

    table = Table(title="MCP Servers", show_header=True, header_style="bold")
    table.add_column("Name", style="bold cyan")
    table.add_column("Command")

    for server_name, server_cfg in servers.items():
        command = server_cfg.get("command", "")
        args = server_cfg.get("args", [])
        full_command = " ".join([command, *args]) if args else command
        table.add_row(server_name, full_command)

    console.print(table)


@mcp_app.command("add")
def mcp_add(
    server: str = typer.Argument(..., help="MCP server name to add (e.g. metabase)."),
) -> None:
    """Add an MCP server to mcp.json."""
    if server not in _MCP_SERVERS:
        error(f"Only {', '.join(repr(s) for s in _MCP_SERVERS)} is supported right now.")
        raise typer.Exit(1)

    mcp_path = _mcp_path()
    mcp_path.parent.mkdir(parents=True, exist_ok=True)

    if mcp_path.exists():
        data = json.loads(mcp_path.read_text())
    else:
        data = {"mcpServers": {}}

    data.setdefault("mcpServers", {})[server] = _MCP_SERVERS[server]
    mcp_path.write_text(json.dumps(data, indent=2))

    success(f"Added MCP server [bold]{server}[/bold] to [bold]{mcp_path}[/bold]")
    if server == "metabase":
        info("Set METABASE_URL and METABASE_API_KEY environment variables before starting the agent.")
    next_steps(
        ("tycoon ask chat", "restart the agent to load the new MCP server"),
    )
