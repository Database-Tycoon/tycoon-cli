"""Shared dbt project definition for use by Dagster and CLI commands.

This module used to hardcode `profiles_dir` to a path relative to the
tycoon source tree, which only worked inside the tycoon repo itself
(installed users got a path that didn't exist). v0.1.6 reads the
active tycoon project's config and resolves the dbt profile via
:mod:`tycoon.dbt_profiles`.

If no ``tycoon.yml`` is available (e.g. importing this module outside a
project root), ``dbt_project`` is ``None`` and callers must guard.
"""

from __future__ import annotations

from pathlib import Path

from dagster_dbt import DbtProject

from tycoon.config import config
from tycoon.dbt_profiles import resolve_profile


def _build_dbt_project() -> DbtProject | None:
    """Build a Dagster DbtProject pointed at the active tycoon project.

    Returns ``None`` when no tycoon.yml is available — callers (notably
    ``orchestration/assets/transforms.py``) already guard against a
    missing manifest, so we propagate the absence cleanly.
    """
    project = config.project
    project_root = config.root
    if project is None:
        return None

    dbt_dir = Path(project.dbt_project_dir)
    if not dbt_dir.is_absolute():
        dbt_dir = (project_root / dbt_dir).resolve()
    if not dbt_dir.exists():
        return None

    resolved = resolve_profile(
        project_root=project_root,
        dbt_project_dir=dbt_dir,
        project_dbt_profiles_dir=project.dbt_profiles_dir,
        project_dbt_profile=project.dbt_profile,
        project_dbt_target=project.dbt_target,
    )

    profiles_dir = resolved.profiles_yml.parent if resolved is not None else dbt_dir
    target = resolved.target if resolved is not None else (project.dbt_target or "dev")

    return DbtProject(
        project_dir=str(dbt_dir),
        profiles_dir=str(profiles_dir),
        target=target,
    )


dbt_project: DbtProject | None = _build_dbt_project()
if dbt_project is not None:
    try:
        dbt_project.prepare_if_dev()
    except Exception:
        pass
