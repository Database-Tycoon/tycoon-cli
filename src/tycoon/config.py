"""Path and configuration resolution.

Reads from tycoon.yml if present, otherwise falls back to v0.1 defaults
for backwards compatibility.
"""

from __future__ import annotations

from pathlib import Path

from tycoon.project import PROJECT_FILENAME, SCHEMA_VERSION, TycoonProject, load_project
from tycoon.utils.console import error as _error_console, warn as _warn_console

# v0.1 defaults (used when no tycoon.yml exists)
_DEFAULT_RAW_DB = "data/raw.duckdb"
_DEFAULT_LOCAL_DB = "data/warehouse.duckdb"
_DEFAULT_DBT_DIR = "dbt_project"
_DEFAULT_RILL_DIR = "rill"


def containment_boundary(root: Path) -> Path:
    """The directory `resolve_contained_path` enforces containment against.

    `root`'s parent, except for a project sitting in a top-level dir
    (`/app`, `/workspace`), where the parent is the filesystem root itself
    and would contain every path -- falls back to `root` there (PR #153
    review). Exposed so a caller computing a *default* path (not just
    validating one, e.g. the `tycoon init` wizard's clone destination) can
    use the same boundary the check itself will apply, instead of always
    assuming `root`'s parent and having the default rejected by its own
    check on a top-level root (gh-259 review).
    """
    boundary = root.resolve().parent
    if boundary == boundary.parent:
        boundary = root.resolve()
    return boundary


def resolve_contained_path(value: str, root: Path, field: str) -> Path:
    """Resolve a path field, rejecting escapes from the project area.

    Containment is enforced against `root`'s *parent*, not `root` itself: an
    existing dbt or Rill project can legitimately live beside the tycoon
    project rather than inside it, so a root-scoped check would reject a
    normal "point at my existing sibling project" setup. Parent scoping
    still rejects a malicious tycoon.yml pointing at system locations like
    `/etc/cron.d` or traversing out via `../../..` (#65).

    Used at runtime by `TycoonConfig` (reading an existing tycoon.yml) and
    at prompt time by the `tycoon init` wizard, before tycoon.yml exists, so
    a path outside the boundary is rejected the moment it's entered there
    rather than only the first time a command tries to use it. `tycoon
    register`'s own prompt flow doesn't call this yet (gh-259 review), so a
    path it accepts can still only fail later, the first time something
    reads tycoon.yml.

    The raised message states the fact (what's outside, and the boundary)
    without prescribing a fix: `field` identifies which caller raised this,
    not what the fix looks like, and "point tycoon.yml at ..." only makes
    sense once a tycoon.yml exists to point. Callers append their own
    remediation (see `TycoonConfig._resolve_contained_path` and the wizard's
    `_prompt_register_project`).
    """
    p = Path(value)
    resolved = p.resolve() if p.is_absolute() else (root / p).resolve()
    boundary = containment_boundary(root)
    if not resolved.is_relative_to(boundary):
        raise ValueError(
            f"{field} ({value!r}) resolves to {resolved}, outside the project's parent directory {boundary}. "
            "tycoon keeps dbt/Rill project paths inside the tycoon project or its parent directory as a "
            "security boundary, so a shared tycoon.yml can't be used to reach unrelated locations on your "
            "machine."
        )
    return resolved


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
            return self._resolve_contained_path(self._project.dbt_project_dir, "dbt_project_dir")
        return self.root / _DEFAULT_DBT_DIR

    @property
    def rill_dir(self) -> Path:
        if self._project:
            return self._resolve_contained_path(self._project.rill_dir, "rill_dir")
        return self.root / _DEFAULT_RILL_DIR

    def _resolve_contained_path(self, value: str, field: str) -> Path:
        """Resolve a tycoon.yml path field via `resolve_contained_path`.

        Appends the runtime-specific fix to the shared fact-only message: a
        tycoon.yml already exists here, so pointing it elsewhere is a real
        option, unlike at wizard prompt time before one is written.
        """
        try:
            return resolve_contained_path(value, self.root, f"tycoon.yml {field}")
        except ValueError as exc:
            raise ValueError(f"{exc} Move the project there, or point tycoon.yml at a path within it.") from exc

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
