"""Pydantic models for tycoon.yml project configuration."""

from __future__ import annotations

import os
import re
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, SecretStr, field_validator


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


class TransformationTool(str, Enum):
    dbt = "dbt"
    none = "none"


class FivetranIngestionMetadata(BaseModel):
    """Credentials + group_id for the Fivetran Metadata API.

    Fivetran auth is HTTP Basic with ``api_key:api_secret``. The
    ``group_id`` scopes which connector group tycoon reads from — get
    yours from ``GET /v1/groups`` on the Fivetran API or from the
    Fivetran web UI under Settings → Account.

    ``api_key``/``api_secret`` are :class:`~pydantic.SecretStr` so they
    never leak into a ``repr``/traceback. Prefer env-var indirection —
    write ``api_secret: ${FIVETRAN_API_SECRET}`` in ``tycoon.yml`` (the
    loader expands ``${VAR}`` before validation) so the literal secret
    stays out of the committed config file.
    """

    api_key: SecretStr = Field(
        description=(
            "Fivetran API key (Basic Auth username). Recommended: "
            "${FIVETRAN_API_KEY} rather than a literal value."
        )
    )
    api_secret: SecretStr = Field(
        description=(
            "Fivetran API secret (Basic Auth password). Recommended: "
            "${FIVETRAN_API_SECRET} rather than a literal value."
        )
    )
    group_id: str = Field(description="Fivetran group identifier.")


class StackConfig(BaseModel):
    ingestion: IngestionTool = IngestionTool.dlt
    ingestion_managed: bool = True
    ingestion_metadata: FivetranIngestionMetadata | None = Field(
        default=None,
        description=(
            "Vendor-specific metadata-API credentials. Used when "
            "``ingestion=fivetran`` to pull connector + sync state into "
            "tycoon's observability surfaces. Other ingestion vendors "
            "(Airbyte Cloud / Stitch) get their own typed sub-config when "
            "support is added."
        ),
    )
    warehouse: WarehouseType = WarehouseType.duckdb
    transformation: TransformationTool = TransformationTool.dbt
    transformation_managed: bool = True
    bi: BITool = BITool.rill
    bi_managed: bool = True


def _interpolate_env(value: str) -> str:
    """Replace ${ENV_VAR} and ${ENV_VAR:-default} patterns with env values."""
    def _replace(match: re.Match) -> str:
        var = match.group(1)
        if ":-" in var:
            name, default = var.split(":-", 1)
            return os.environ.get(name, default)
        return os.environ.get(var, match.group(0))

    return re.sub(r"\$\{([^}]+)}", _replace, value)


# ${VAR} expansion runs against the victim's full os.environ, so expanding the
# whole config would let a malicious shared tycoon.yml exfiltrate arbitrary
# secrets (${MOTHERDUCK_TOKEN}, ${AWS_SECRET_ACCESS_KEY}, ...) by planting
# references in fields that flow into generated artifacts or the notify
# webhook payload (#62). Expansion is therefore limited to the fields
# documented to carry credentials, connection strings, or machine-specific
# paths; everywhere else ``${...}`` stays literal.
#
# Patterns are tuples of on-disk yml key segments; "*" matches any single map
# key or list index. Leaves expand one string field; subtrees expand every
# string beneath the prefix.
_INTERPOLATED_LEAVES: tuple[tuple[str, ...], ...] = (
    ("database", "raw"),
    ("database", "warehouse"),
    ("stack", "ingestion_metadata", "api_key"),
    ("stack", "ingestion_metadata", "api_secret"),
    ("sync", "to"),
    ("sync", "sources", "*", "from"),
)
_INTERPOLATED_SUBTREES: tuple[tuple[str, ...], ...] = (
    # dlt source credentials: tokens, connection strings, bucket URLs.
    ("sources", "*", "config"),
)


def _path_matches(path: tuple[str, ...], pattern: tuple[str, ...]) -> bool:
    return len(path) == len(pattern) and all(
        p in ("*", segment) for segment, p in zip(path, pattern)
    )


def _is_interpolated_field(path: tuple[str, ...]) -> bool:
    if any(_path_matches(path, leaf) for leaf in _INTERPOLATED_LEAVES):
        return True
    return any(
        len(path) > len(prefix) and _path_matches(path[: len(prefix)], prefix)
        for prefix in _INTERPOLATED_SUBTREES
    )


def _interpolate_allowed_fields(obj: Any, path: tuple[str, ...] = ()) -> Any:
    """Interpolate env vars only in the allowlisted fields of a parsed tycoon.yml."""
    if isinstance(obj, str):
        return _interpolate_env(obj) if _is_interpolated_field(path) else obj
    if isinstance(obj, dict):
        return {k: _interpolate_allowed_fields(v, (*path, str(k))) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_interpolate_allowed_fields(v, (*path, str(i))) for i, v in enumerate(obj)]
    return obj


# Source names flow into filesystem paths (models/staging/<source_name>/) and
# generated dbt SQL ({{ source('<name>', '<table>') }}); schema names become
# DuckDB schemas / dlt dataset names. Constraining them to identifier-safe
# characters blocks path traversal (../..) and SQL/jinja quote breakout from a
# shared tycoon.yml (#65). Source names additionally allow "-" because the CLI
# and shipped templates use hyphenated names (e.g. nyc-dot) and derive schemas
# via replace("-", "_").
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SOURCE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


class SourceConfig(BaseModel):
    """Configuration for a registered data source."""

    type: str = Field(description="dlt source type (e.g. rest_api, sql_database, filesystem)")
    config: dict[str, Any] = Field(default_factory=dict, description="Config passed to dlt source")
    schema_name: str = Field(alias="schema", description="Target schema in raw database")
    tables: list[str] | None = Field(default=None, description="Optional table filter")
    dbt_package: str | None = Field(default=None, description="Optional dbt hub package name")

    model_config = {"populate_by_name": True}

    @field_validator("type")
    @classmethod
    def _check_type(cls, v: str) -> str:
        # `type` names a dlt source module: it reaches `dlt init` argv and
        # filesystem paths, so it gets the strict identifier charset.
        if not _IDENTIFIER_RE.match(v):
            raise ValueError(
                f"source type {v!r} is not a valid identifier "
                "(letters, digits, and underscores only; must not start with a digit)"
            )
        return v

    @field_validator("schema_name")
    @classmethod
    def _check_schema_name(cls, v: str) -> str:
        if not _IDENTIFIER_RE.match(v):
            raise ValueError(
                f"schema {v!r} is not a valid identifier "
                "(letters, digits, and underscores only; must not start with a digit)"
            )
        return v

    @field_validator("tables")
    @classmethod
    def _check_tables(cls, v: list[str] | None) -> list[str] | None:
        for table in v or []:
            if not _IDENTIFIER_RE.match(table):
                raise ValueError(
                    f"table {table!r} is not a valid identifier "
                    "(letters, digits, and underscores only; must not start with a digit)"
                )
        return v


class DatabaseConfig(BaseModel):
    """Database file paths (relative to project root)."""

    raw: str = Field(default="data/raw.duckdb", description="Raw ingestion database")
    warehouse: str = Field(default="data/warehouse.duckdb", description="Transformed warehouse database")


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


class TransformConfig(BaseModel):
    """Top-level ``transform:`` block — defaults for transform-side commands."""

    auto_scaffold: bool = Field(
        default=True,
        description=(
            "When True (default), `tycoon data sources run <name>` "
            "auto-runs the `tycoon data analyze` flow after a successful "
            "ingest if no staging models exist yet for that source. Set "
            "to False to opt out project-wide; pass --no-scaffold for a "
            "one-shot opt-out."
        ),
    )
    auto_osi_scaffold: bool = Field(
        default=False,
        description=(
            "When True, `tycoon data transform run` and `tycoon data analyze` "
            "auto-invoke `tycoon semantics scaffold` after a successful build. "
            "Default False in v0.1.6 — opt in once you've validated the "
            "Conservative scaffold matches your project conventions. "
            "Best-effort: never breaks the underlying transform on OSI failure."
        ),
    )


class NotifyConfig(BaseModel):
    """Optional ``notify:`` block — non-secret notification prefs (#46).

    The webhook URL itself comes from ``$TYCOON_NOTIFY_WEBHOOK_URL`` and never
    lives here. This block only holds preferences safe to commit.
    """

    severities: list[str] = Field(
        default_factory=lambda: ["success", "error"],
        description=(
            "Which severities `--notify` emits on a pipeline run. Defaults to "
            "success + error (info is for manual `tycoon notify` calls)."
        ),
    )
    label: str | None = Field(
        default=None,
        description="Optional source label included in the payload (e.g. project or channel name).",
    )


class TycoonProject(BaseModel):
    """Top-level tycoon.yml schema."""

    name: str = Field(default="my-project", description="Project name")
    version: str = Field(default="0.1.0", description="Project version")
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    sources: dict[str, SourceConfig] = Field(default_factory=dict, description="Registered data sources")
    dbt_project_dir: str = Field(default="dbt_project", description="Path to dbt project")
    dbt_profiles_dir: str | None = Field(
        default=None,
        description=(
            "Path to the directory containing profiles.yml. Defaults to "
            "<dbt_project_dir>/profiles.yml if present, otherwise dbt's "
            "default of ~/.dbt/profiles.yml."
        ),
    )
    dbt_profile: str | None = Field(
        default=None,
        description=(
            "Profile name within profiles.yml. Defaults to the `profile:` "
            "field in dbt_project.yml."
        ),
    )
    dbt_target: str | None = Field(
        default=None,
        description=(
            "Target within the profile (dev / prod / ...). Defaults to the "
            "profile's `target:` field, then 'dev'."
        ),
    )
    rill_dir: str = Field(default="rill", description="Path to Rill dashboards")
    sync: SyncConfig | None = Field(default=None, description="`tycoon data sync` defaults")
    transform: TransformConfig = Field(
        default_factory=lambda: TransformConfig(),
        description="Defaults for transform-side commands (`data analyze`, `data sources run`).",
    )
    stack: StackConfig = Field(default_factory=StackConfig)
    notify: NotifyConfig = Field(
        default_factory=lambda: NotifyConfig(),
        description="Notification preferences for `--notify` runs and `tycoon notify`.",
    )

    @field_validator("sources")
    @classmethod
    def _check_source_names(cls, v: dict[str, SourceConfig]) -> dict[str, SourceConfig]:
        for name in v:
            if not _SOURCE_NAME_RE.match(name):
                raise ValueError(
                    f"source name {name!r} is not a valid identifier "
                    "(letters, digits, underscores, and hyphens only; "
                    "must not start with a digit or hyphen)"
                )
        return v

    @field_validator("dbt_project_dir", "dbt_profiles_dir", "rill_dir")
    @classmethod
    def _check_path_field(cls, v: str | None) -> str | None:
        if v is not None and any(ch in v for ch in "\x00\n\r"):
            raise ValueError("path must not contain NUL, newline, or carriage-return characters")
        return v


PROJECT_FILENAME = "tycoon.yml"


def load_project(project_root: Path) -> TycoonProject | None:
    """Load and validate tycoon.yml from the given root. Returns None if not found."""
    path = project_root / PROJECT_FILENAME
    if not path.exists():
        return None
    raw = yaml.safe_load(path.read_text())
    if raw is None:
        return TycoonProject()
    raw = _interpolate_allowed_fields(raw)
    return TycoonProject.model_validate(raw)


def save_project(project: TycoonProject, project_root: Path) -> None:
    """Write tycoon.yml to disk.

    Preserves the hand-authored ``stack.ingestion_metadata`` block from
    the existing file verbatim. Those credentials are ``SecretStr`` (a
    plain dump would mask them to ``**********``) and may be written as
    ``${ENV}`` references that ``load_project`` has already expanded —
    re-dumping the in-memory value would either corrupt the config or
    flatten an env-ref into its literal secret. tycoon never edits that
    block, so round-tripping the on-disk form is always correct.
    """
    path = project_root / PROJECT_FILENAME
    data = project.model_dump(by_alias=True, exclude_none=True, mode="json")
    if path.exists():
        existing = yaml.safe_load(path.read_text())
        if isinstance(existing, dict):
            existing_meta = (existing.get("stack") or {}).get("ingestion_metadata")
            if existing_meta is not None and isinstance(data.get("stack"), dict):
                data["stack"]["ingestion_metadata"] = existing_meta
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
