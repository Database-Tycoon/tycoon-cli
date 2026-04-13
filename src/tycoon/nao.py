"""Generate nao_config.yaml and RULES.md for the Nao analytics agent.

Nao (https://getnao.io) is a local AI analytics agent that connects to a
DuckDB warehouse and a dbt project, letting users query data in natural
language. This module generates its config from tycoon.yml so the user
never has to write nao_config.yaml by hand.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from tycoon.config import TycoonConfig

_DEFAULT_RULES_TEMPLATE = """\
You are an analytics assistant for the {name} project.

- Always explain your SQL and the business logic behind it clearly.
- Prefer mart tables over staging tables when answering business questions.
- When results are empty, suggest why that might be and what to check.
"""


def _rel(from_dir: Path, to_path: Path) -> str:
    """Return a relative path string from from_dir to to_path."""
    return str(os.path.relpath(to_path, from_dir))


def build_nao_config(cfg: TycoonConfig) -> dict:
    """Build the nao_config.yaml dict from tycoon config."""
    project = cfg.project
    nao_dir = cfg.nao_dir
    ask = project.ask if project else None

    # Database entry pointing at the warehouse DuckDB
    db_entry: dict = {
        "name": project.name if project else "tycoon-warehouse",
        "type": "duckdb",
        "path": _rel(nao_dir, cfg.local_db),
        "accessors": ["columns", "preview"],
        "profiling": {
            "refresh_policy": "interval",
            "interval_days": 1,
        },
    }
    if ask and ask.include_schemas:
        db_entry["include"] = ask.include_schemas
    if ask and ask.exclude_schemas:
        db_entry["exclude"] = ask.exclude_schemas

    # Repo entry pointing at the dbt project
    repo_entry = {
        "name": "dbt",
        "local_path": _rel(nao_dir, cfg.dbt_project_dir),
        "include": ["models/**/*.sql", "models/**/*.yml"],
    }

    config: dict = {
        "project_name": project.name if project else "tycoon",
        "databases": [db_entry],
        "repos": [repo_entry],
    }

    # LLM config
    if ask and ask.llm:
        llm = ask.llm
        llm_entry: dict = {"provider": llm.provider}
        if llm.model:
            llm_entry["model"] = llm.model
        if llm.api_key_env:
            # Use nao's {{ env('VAR') }} interpolation — NOT tycoon's ${VAR}
            llm_entry["api_key"] = f"{{{{ env('{llm.api_key_env}') }}}}"
        config["llm"] = llm_entry

    # Skills config
    skills_dir = Path(ask.skills_dir) if (ask and ask.skills_dir) else nao_dir / "agent" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    config["skills"] = {
        "folder_path": str(skills_dir)
    }

    # MCP config
    mcp_path = nao_dir / "agent" / "mcps" / "mcp.json"
    mcp_path.parent.mkdir(parents=True, exist_ok=True)
    if not mcp_path.exists():
        mcp_path.write_text('{"mcpServers": {}}')
    config["mcp"] = {"json_file_path": str(mcp_path)}

    return config


def build_rules(cfg: TycoonConfig) -> str:
    """Return the RULES.md content."""
    project = cfg.project
    ask = project.ask if project else None
    if ask and ask.rules:
        return ask.rules
    name = project.name if project else "tycoon"
    return _DEFAULT_RULES_TEMPLATE.format(name=name)


def write_nao_project(cfg: TycoonConfig) -> None:
    """Write nao_config.yaml and RULES.md to .tycoon/nao/."""
    nao_dir = cfg.nao_dir
    nao_dir.mkdir(parents=True, exist_ok=True)

    config = build_nao_config(cfg)
    config_path = nao_dir / "nao_config.yaml"
    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))

    rules_path = nao_dir / "RULES.md"
    rules_path.write_text(build_rules(cfg))
