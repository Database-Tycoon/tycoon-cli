"""Pydantic models for tycoon.yml project configuration."""

from __future__ import annotations

import os
import re
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class IngestionTool(str, Enum):
    dlt = "dlt"
    airbyte = "airbyte"
    fivetran = "fivetran"
    meltano = "meltano"
    none = "none"


class WarehouseType(str, Enum):
    duckdb = "duckdb"
    motherduck = "motherduck"
    snowflake = "snowflake"
    bigquery = "bigquery"
    redshift = "redshift"
    other = "other"


class BITool(str, Enum):
    rill = "rill"
    metabase = "metabase"
    looker = "looker"
    tableau = "tableau"
    other = "other"
    none = "none"


class OrchestratorTool(str, Enum):
    dagster = "dagster"
    airflow = "airflow"
    prefect = "prefect"
    other = "other"
    none = "none"


class TransformationTool(str, Enum):
    dbt = "dbt"
    none = "none"


class StackConfig(BaseModel):
    ingestion: IngestionTool = IngestionTool.dlt
    ingestion_managed: bool = True
    warehouse: WarehouseType = WarehouseType.duckdb
    transformation: TransformationTool = TransformationTool.dbt
    transformation_managed: bool = True
    bi: BITool = BITool.rill
    bi_managed: bool = True
    orchestrator: OrchestratorTool = OrchestratorTool.dagster
    orchestrator_managed: bool = True


def _interpolate_env(value: str) -> str:
    """Replace ${ENV_VAR} and ${ENV_VAR:-default} patterns with env values."""
    def _replace(match: re.Match) -> str:
        var = match.group(1)
        if ":-" in var:
            name, default = var.split(":-", 1)
            return os.environ.get(name, default)
        return os.environ.get(var, match.group(0))

    return re.sub(r"\$\{([^}]+)}", _replace, value)


def _interpolate_recursive(obj: Any) -> Any:
    """Recursively interpolate env vars in strings throughout a data structure."""
    if isinstance(obj, str):
        return _interpolate_env(obj)
    if isinstance(obj, dict):
        return {k: _interpolate_recursive(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_interpolate_recursive(v) for v in obj]
    return obj


class SourceConfig(BaseModel):
    """Configuration for a registered data source."""

    type: str = Field(description="dlt source type (e.g. rest_api, sql_database, filesystem)")
    config: dict[str, Any] = Field(default_factory=dict, description="Config passed to dlt source")
    schema_name: str = Field(alias="schema", description="Target schema in raw database")
    tables: list[str] | None = Field(default=None, description="Optional table filter")
    dbt_package: str | None = Field(default=None, description="Optional dbt hub package name")

    model_config = {"populate_by_name": True}


class DatabaseConfig(BaseModel):
    """Database file paths (relative to project root)."""

    raw: str = Field(default="data/raw.duckdb", description="Raw ingestion database")
    warehouse: str = Field(default="data/warehouse.duckdb", description="Transformed warehouse database")


class LLMConfig(BaseModel):
    """LLM provider config for the ask (Nao) feature."""

    provider: str = Field(default="openai", description="LLM provider (openai, anthropic, ollama, mistral, gemini)")
    model: str | None = Field(default=None, description="Model name override")
    api_key_env: str | None = Field(default=None, description="Env var name holding the API key")


class AskConfig(BaseModel):
    """Configuration for `tycoon ask` (Nao analytics agent)."""

    llm: LLMConfig | None = Field(default=None)
    port: int = Field(default=5005, description="Port for nao chat UI")
    rules: str | None = Field(default=None, description="Custom instructions written to RULES.md")
    include_schemas: list[str] = Field(default_factory=list, description="Only expose these schemas to nao")
    exclude_schemas: list[str] = Field(default_factory=list, description="Hide these schemas from nao")
    skills_dir: str | None = Field(
        default=None,
        description="Path to skills folder. Defaults to .tycoon/nao/agent/skills/"
    )


class SyncSourceSpec(BaseModel):
    """One source-of-data for `tycoon data sync`.

    The ``from`` field accepts any DuckDB-attachable URL: ``md:<catalog>`` for
    MotherDuck, ``./other.duckdb`` for a local DuckDB file. v0.1.4 ships
    MotherDuck + local-DuckDB only; Postgres / etc. land later.
    """

    from_: str = Field(
        alias="from",
        description="Source URL — md:<catalog>, /path/to/other.duckdb, etc.",
    )
    schemas: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Schema-name globs (fnmatch) to include. Default: all.",
    )
    tables: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Table-name globs (fnmatch) to include within the selected schemas. Default: all.",
    )

    model_config = {"populate_by_name": True}


class SyncConfig(BaseModel):
    """Top-level ``sync:`` block — defaults for ``tycoon data sync``."""

    to: str = Field(
        default="data/local_snapshot.duckdb",
        description="Default destination DuckDB file (relative to project root).",
    )
    sources: list[SyncSourceSpec] = Field(default_factory=list)
    mode: str = Field(
        default="replace",
        description="Default sync mode: replace | append | skip-existing.",
    )


class TycoonProject(BaseModel):
    """Top-level tycoon.yml schema."""

    name: str = Field(default="my-project", description="Project name")
    version: str = Field(default="0.1.0", description="Project version")
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    sources: dict[str, SourceConfig] = Field(default_factory=dict, description="Registered data sources")
    dbt_project_dir: str = Field(default="dbt_project", description="Path to dbt project")
    rill_dir: str = Field(default="rill", description="Path to Rill dashboards")
    ask: AskConfig | None = Field(default=None, description="Nao analytics agent configuration")
    sync: SyncConfig | None = Field(default=None, description="`tycoon data sync` defaults")
    stack: StackConfig = Field(default_factory=StackConfig)


PROJECT_FILENAME = "tycoon.yml"


def load_project(project_root: Path) -> TycoonProject | None:
    """Load and validate tycoon.yml from the given root. Returns None if not found."""
    path = project_root / PROJECT_FILENAME
    if not path.exists():
        return None
    raw = yaml.safe_load(path.read_text())
    if raw is None:
        return TycoonProject()
    raw = _interpolate_recursive(raw)
    return TycoonProject.model_validate(raw)


def save_project(project: TycoonProject, project_root: Path) -> None:
    """Write tycoon.yml to disk."""
    path = project_root / PROJECT_FILENAME
    data = project.model_dump(by_alias=True, exclude_none=True, mode="json")
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
