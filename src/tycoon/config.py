"""Path and configuration resolution.

Reads from tycoon.yml if present, otherwise falls back to v0.1 defaults
for backwards compatibility.
"""

from __future__ import annotations

from pathlib import Path

from tycoon.project import PROJECT_FILENAME, TycoonProject, load_project


# v0.1 defaults (used when no tycoon.yml exists)
_DEFAULT_RAW_DB = "data/raw.duckdb"
_DEFAULT_LOCAL_DB = "data/warehouse.duckdb"
_DEFAULT_DBT_DIR = "dbt_project"
_DEFAULT_RILL_DIR = "rill"


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
    def raw_db(self) -> Path:
        if self._project:
            return self.root / self._project.database.raw
        return self.root / _DEFAULT_RAW_DB

    @property
    def local_db(self) -> Path:
        if self._project:
            return self.root / self._project.database.warehouse
        return self.root / _DEFAULT_LOCAL_DB

    @property
    def dbt_project_dir(self) -> Path:
        if self._project:
            p = Path(self._project.dbt_project_dir)
            return p if p.is_absolute() else (self.root / p).resolve()
        return self.root / _DEFAULT_DBT_DIR

    @property
    def rill_dir(self) -> Path:
        if self._project:
            p = Path(self._project.rill_dir)
            return p if p.is_absolute() else (self.root / p).resolve()
        return self.root / _DEFAULT_RILL_DIR

    # -- Sources --

    @property
    def sources(self) -> dict:
        if self._project:
            return self._project.sources
        return {}

    def ensure_data_dir(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)


# Singleton
config = TycoonConfig()
