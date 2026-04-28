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


def _require_nao() -> None:
    try:
        import nao_core  # noqa: F401
    except ImportError:
        error("Nao is not installed. Run: [bold]pip install tycoon\\[ask][/bold]")
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


def _refresh_agents_md() -> None:
    """Write or refresh AGENTS.md at the project root.

    Best-effort: never raises. Prints a hint when a user-authored
    AGENTS.md is preserved so the user knows tycoon's pointer file
    isn't getting refreshed.
    """
    from tycoon.nao import write_agents_md

    wrote, path = write_agents_md(config)
    if wrote:
        info(f"AGENTS.md refreshed at [bold]{path}[/bold]")
    else:
        warn(
            f"AGENTS.md at [bold]{path}[/bold] is user-authored "
            "(no tycoon sentinel) — left alone. Delete the file to let "
            "[bold]tycoon ask[/bold] manage it again."
        )


@app.command("init")
def ask_init() -> None:
    """Generate .tycoon/nao/nao_config.yaml from tycoon.yml."""
    _require_project()
    _require_nao()

    from tycoon.nao import write_nao_project

    write_nao_project(config)
    _refresh_agents_md()

    success(f"Nao config written to [bold]{config.nao_dir}[/bold]")
    next_steps(
        ("tycoon ask sync", "build DB and dbt context (~30s first run)"),
        ("tycoon ask chat", "launch the query UI"),
        ("tycoon ask context --help", "pipe synced context into any agent"),
    )


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
        error("No nao_config.yaml found. Run [bold]tycoon ask init[/bold] first.")
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
    """
    _require_project()
    _require_nao()

    # Auto-init if no config exists yet
    nao_config = config.nao_dir / "nao_config.yaml"
    if not nao_config.exists():
        info("No nao_config.yaml found — running [bold]tycoon ask init[/bold] automatically...")
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
            error(f"No RULES.md at [bold]{rules}[/bold]. Run [bold]tycoon ask init[/bold].")
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
