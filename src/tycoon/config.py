"""Path and configuration resolution.

Reads from tycoon.yml if present, otherwise falls back to v0.1 defaults
for backwards compatibility.
"""

from __future__ import annotations

import re
from pathlib import Path

from tycoon.project import PROJECT_FILENAME, SCHEMA_VERSION, TycoonProject, load_project
from tycoon.utils.console import error as _error_console, warn as _warn_console

# v0.1 defaults (used when no tycoon.yml exists)
_DEFAULT_RAW_DB = "data/raw.duckdb"
_DEFAULT_LOCAL_DB = "data/warehouse.duckdb"
_DEFAULT_DBT_DIR = "dbt_project"
_DEFAULT_RILL_DIR = "rill"

MOTHERDUCK_PREFIX = "md:"

# The query part of an md: string can carry motherduck_token=<secret>.
_MD_QUERY_RE = re.compile(r"(md:[^\s'\"?]*)\?[^\s'\"]*")
# The key, any spaces around "=", and an opening quote stay; the value is masked
# and stops at a quote, so a closing quote survives too (SET motherduck_token = '...').
_MD_TOKEN_RE = re.compile(r"(motherduck_token\s*=\s*['\"]?)[^\s&'\"]+", re.IGNORECASE)


def display_target(target: str) -> str:
    """A connection target that is safe to print.

    An ``md:`` string loses everything from ``?`` onwards, where a
    ``motherduck_token`` can sit; a local path is returned unchanged.
    """
    if target.startswith(MOTHERDUCK_PREFIX):
        return target.split("?", 1)[0]
    return target


def redact_secrets(text: str) -> str:
    """Strip md: query strings and motherduck_token values from free text, such as a DuckDB error."""
    return _MD_TOKEN_RE.sub(r"\1***", _MD_QUERY_RE.sub(r"\1", text))


def _find_project_root() -> Path:
    """Walk up from CWD to find the directory containing tycoon.yml or pyproject.toml."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / PROJECT_FILENAME).exists():
            return parent
        if (parent / "pyproject.toml").exists():
            return parent
    return current


class TycoonConfig:
    """Centralised path / config resolution.

    If tycoon.yml exists, all paths and source definitions come from it.
    Otherwise, falls back to hardcoded v0.1 defaults.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        self.root = project_root or _find_project_root()
        self._project: TycoonProject | None = load_project(self.root)

    # -- Project access --

    @property
    def project(self) -> TycoonProject | None:
        return self._project

    @property
    def has_project_file(self) -> bool:
        return self._project is not None

    def reload(self) -> None:
        """Re-read tycoon.yml from disk."""
        self._project = load_project(self.root)

    # -- Paths --

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def _raw_setting(self) -> str:
        if self._project:
            return self._project.database.raw
        return _DEFAULT_RAW_DB

    @property
    def raw_is_motherduck(self) -> bool:
        return self._raw_setting.startswith(MOTHERDUCK_PREFIX)

    @property
    def raw_target(self) -> str:
        """What ``duckdb.connect`` opens for the raw database, resolved like ``warehouse_target``."""
        if self.raw_is_motherduck:
            return self._raw_setting
        return str(self.root / self._raw_setting)

    @property
    def raw_db(self) -> Path:
        """The raw database's local DuckDB file.

        Ingestion and scaffolding only write local files so far, so an ``md:``
        raw database exits with a clear error instead of becoming a local
        file named after the connection string. Check ``raw_is_motherduck``
        first to handle MotherDuck without exiting.
        """
        if self.raw_is_motherduck:
            _error_console(
                f"database.raw is MotherDuck ({display_target(self._raw_setting)}), and this command only "
                "works with a local raw DuckDB file so far. Set database.raw to a local path such as "
                f"{_DEFAULT_RAW_DB} in tycoon.yml."
            )
            raise SystemExit(1)
        return self.root / self._raw_setting

    @property
    def _warehouse_setting(self) -> str:
        if self._project:
            return self._project.database.warehouse
        return _DEFAULT_LOCAL_DB

    @property
    def warehouse_is_motherduck(self) -> bool:
        return self._warehouse_setting.startswith(MOTHERDUCK_PREFIX)

    @property
    def warehouse_target(self) -> str:
        """What ``duckdb.connect`` opens for the warehouse.

        A MotherDuck ``md:`` connection string passes through verbatim; a
        local path resolves under the project root.
        """
        if self.warehouse_is_motherduck:
            return self._warehouse_setting
        return str(self.root / self._warehouse_setting)

    @property
    def local_db(self) -> Path | None:
        """The warehouse's local DuckDB file, or None when it lives in MotherDuck."""
        if self.warehouse_is_motherduck:
            return None
        return self.root / self._warehouse_setting

    @property
    def dbt_project_dir(self) -> Path:
        if self._project:
            return self._resolve_contained_path(self._project.dbt_project_dir, "dbt_project_dir")
        return self.root / _DEFAULT_DBT_DIR

    @property
    def rill_dir(self) -> Path:
        if self._project:
            return self._resolve_contained_path(self._project.rill_dir, "rill_dir")
        return self.root / _DEFAULT_RILL_DIR

    def _resolve_contained_path(self, value: str, field: str) -> Path:
        """Resolve a tycoon.yml path field, rejecting escapes from the project area.

        Containment is enforced against the project root's *parent*, not the
        root itself: the init wizard's default layout puts the dbt project in
        a sibling directory of the root (e.g. ``../myproj-dbt``), so a
        root-scoped check would break every standard project. Parent scoping
        still rejects a malicious tycoon.yml pointing at system locations
        like ``/etc/cron.d`` or traversing out via ``../../..`` (#65).
        """
        p = Path(value)
        resolved = p.resolve() if p.is_absolute() else (self.root / p).resolve()
        boundary = self.root.resolve().parent
        # A project sitting in a top-level dir (/app, /workspace) would make
        # the boundary the filesystem root, which contains every path — fall
        # back to root-scoped containment there (PR #153 review).
        if boundary == boundary.parent:
            boundary = self.root.resolve()
        if not resolved.is_relative_to(boundary):
            raise ValueError(
                f"tycoon.yml {field} ({value!r}) resolves to {resolved}, "
                f"outside the project's parent directory {boundary}"
            )
        return resolved

    # -- Sources --

    @property
    def sources(self) -> dict:
        if self._project:
            return self._project.sources
        return {}

    def ensure_data_dir(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)


def load_config() -> TycoonConfig:
    """Return a TycoonConfig rooted at the nearest project directory.

    Prefer this over importing _find_project_root across module boundaries.
    Emits a console warning when tycoon.yml is at an older schema version.
    """
    cfg = TycoonConfig(project_root=_find_project_root())
    if cfg.project is not None:
        sv = cfg.project.schema_version
        if sv is not None and sv > SCHEMA_VERSION:
            _error_console(
                f"tycoon.yml schema_version {sv} is newer than this tycoon supports "
                f"({SCHEMA_VERSION}). Upgrade tycoon-cli to use this project."
            )
            raise SystemExit(1)
        if sv is None or sv < SCHEMA_VERSION:
            current = sv if sv is not None else "none"
            _warn_console(
                f"tycoon.yml is at schema version {current}, current is {SCHEMA_VERSION}. "
                "Run 'tycoon init --upgrade' to migrate."
            )
    return cfg


# Singleton (used by modules not yet migrated to load_config)
config = TycoonConfig()
