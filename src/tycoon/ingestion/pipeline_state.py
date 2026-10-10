"""Per-project dlt working directories, and carrying state into them (gh-394).

dlt keeps each pipeline's working directory, including its incremental
state, under ``~/.dlt/pipelines/<pipeline_name>`` unless told otherwise.
Tycoon names pipelines after the source, so two projects on one machine
with a ``github`` source shared one incremental cursor and loaded duplicate
rows. Tycoon now points dlt at ``<project>/.tycoon/dlt/pipelines`` for the
length of a run, next to the project's ``.tycoon/sources/``.

Moving to an empty directory must not cause a reload. ``plan_carry_over``
decides, per pipeline, whether the shared working directory is this
project's own and safe to copy, or whether dlt should restore the project's
state from its own raw database instead. The shared directory is only ever
read, never moved or deleted: other projects may still be using it.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

DLT_DATA_DIR_ENV = "DLT_DATA_DIR"

LEGACY_PIPELINE_IDENTITIES: dict[str, tuple[str, str]] = {
    "nyc-dot": ("nyc_dot", "raw_nyc_dot"),
    "mta-gtfs": ("mta_gtfs", "raw_mta"),
    "mta-bus-speeds": ("mta_bus_speeds", "raw_mta_bus_speeds"),
}


def project_dlt_data_dir(project_root: Path) -> Path:
    """The ``DLT_DATA_DIR`` tycoon sets for a project's pipeline runs."""
    return project_root / ".tycoon" / "dlt"


def project_pipelines_dir(project_root: Path) -> Path:
    """Where a project's dlt working directories live."""
    return project_dlt_data_dir(project_root) / "pipelines"


def shared_pipelines_dir() -> Path:
    """dlt's machine-wide default pipelines directory, normally ``~/.dlt/pipelines``.

    Resolved through dlt so ``XDG_DATA_HOME`` and dlt's root and no-home
    fallbacks match what dlt itself used before tycoon set a project dir.
    """
    from dlt.common.runtime.run_context import global_dir

    return Path(global_dir()) / "pipelines"


def user_dlt_data_dir() -> str | None:
    """The user's own ``DLT_DATA_DIR``, if set. Tycoon leaves that choice alone."""
    return os.environ.get(DLT_DATA_DIR_ENV) or None


def pipeline_identity(source_name: str, schema_name: str) -> tuple[str, str]:
    """The ``(pipeline_name, dataset_name)`` a tycoon source runs under.

    Generic and catalog sources use the tycoon source name and its schema.
    The bundled legacy pipelines hard-code their own names.
    """
    return LEGACY_PIPELINE_IDENTITIES.get(source_name, (source_name, schema_name))


class CarryOver(StrEnum):
    NOT_NEEDED = "not_needed"
    COPY = "copy"
    COPY_UNVERIFIED = "copy_unverified"
    RESTORE_FROM_DESTINATION = "restore_from_destination"
    FRESH = "fresh"


@dataclass(frozen=True)
class StatePlan:
    pipeline_name: str
    action: CarryOver
    reason: str
    shared_dir: Path
    project_dir: Path


class StateCarryOverError(RuntimeError):
    """The shared state couldn't be checked, so nothing was changed."""


def _shared_version_hash(working_dir: Path) -> str | None:
    import json

    try:
        state = json.loads((working_dir / "state.json").read_text())
    except (OSError, ValueError):
        return None
    value = state.get("_version_hash") if isinstance(state, dict) else None
    return value if isinstance(value, str) else None


@dataclass(frozen=True)
class _DestinationState:
    dataset_exists: bool
    version_hash: str | None


def _destination_state(raw_db_path: Path, dataset_name: str, pipeline_name: str) -> _DestinationState:
    """The state dlt last stored for ``pipeline_name`` in this project's raw database.

    Mirrors dlt's own lookup (``get_stored_state``): the newest state row
    whose load completed.
    """
    import duckdb

    if not raw_db_path.exists():
        return _DestinationState(dataset_exists=False, version_hash=None)
    con = duckdb.connect(str(raw_db_path), read_only=True)
    try:
        tables = {
            row[0]
            for row in con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = ?",
                [dataset_name],
            ).fetchall()
        }
        if not tables:
            return _DestinationState(dataset_exists=False, version_hash=None)
        if not {"_dlt_pipeline_state", "_dlt_loads"} <= tables:
            return _DestinationState(dataset_exists=True, version_hash=None)
        schema = '"' + dataset_name.replace('"', '""') + '"'
        row = con.execute(
            f"SELECT s.version_hash FROM {schema}._dlt_pipeline_state AS s "
            f"JOIN {schema}._dlt_loads AS l ON l.load_id = s._dlt_load_id "
            "WHERE s.pipeline_name = ? AND l.status = 0 "
            "ORDER BY l.load_id DESC LIMIT 1",
            [pipeline_name],
        ).fetchone()
        return _DestinationState(dataset_exists=True, version_hash=row[0] if row else None)
    finally:
        con.close()


def restores_from_destination(pipeline_name: str) -> bool:
    """Whether dlt will restore this pipeline's state from its destination on run.

    Resolved the way ``dlt.pipeline`` resolves it, so a
    ``RESTORE_FROM_DESTINATION=false`` env var or config.toml entry counts.
    """
    from dlt.common.configuration import resolve_configuration
    from dlt.common.configuration.specs import known_sections
    from dlt.pipeline.configuration import PipelineConfiguration

    resolved = resolve_configuration(
        PipelineConfiguration(pipeline_name=pipeline_name),
        sections=(known_sections.PIPELINES, pipeline_name),
    )
    return bool(resolved.restore_from_destination)


def plan_carry_over(
    pipeline_name: str,
    dataset_name: str,
    raw_db_path: Path,
    project_pipelines: Path,
    shared_pipelines: Path,
) -> StatePlan:
    """Decide what the project's first run in its own directory starts from.

    Read-only, so ``tycoon doctor`` can report the plan without acting on it.
    Raises ``StateCarryOverError`` when the raw database can't be read,
    since guessing could reload or skip rows.
    """
    shared = shared_pipelines / pipeline_name
    project = project_pipelines / pipeline_name

    def plan(action: CarryOver, reason: str) -> StatePlan:
        return StatePlan(pipeline_name, action, reason, shared, project)

    if project.exists():
        return plan(CarryOver.NOT_NEEDED, "the project already has its own dlt state")
    if not (shared / "state.json").is_file():
        return plan(CarryOver.NOT_NEEDED, "there is no shared dlt state to carry over")

    try:
        destination = _destination_state(raw_db_path, dataset_name, pipeline_name)
    except Exception as exc:
        raise StateCarryOverError(
            f"Couldn't read {raw_db_path} to check which dlt state belongs to '{pipeline_name}' ({exc}). "
            f"Nothing was changed. Close anything holding the raw database and rerun."
        ) from exc

    if not destination.dataset_exists:
        return plan(
            CarryOver.FRESH,
            f"dataset '{dataset_name}' doesn't exist in this project's raw database yet, "
            "so the shared state belongs to another project and is left out",
        )
    if destination.version_hash is None:
        return plan(
            CarryOver.COPY_UNVERIFIED,
            "the raw database holds no stored dlt state to check against, so the shared state is "
            "copied as is, which is what the run would have used before",
        )
    if destination.version_hash == _shared_version_hash(shared):
        return plan(CarryOver.COPY, "the shared state matches what this project last loaded")
    try:
        restores = restores_from_destination(pipeline_name)
    except Exception:
        restores = False
    if restores:
        return plan(
            CarryOver.RESTORE_FROM_DESTINATION,
            "the shared state doesn't match what this project last loaded, so dlt restores "
            "this project's own state from its raw database instead",
        )
    return plan(
        CarryOver.COPY_UNVERIFIED,
        "the shared state doesn't match what this project last loaded, and restore_from_destination "
        "is off or unreadable, so the shared state is copied as is, which is what the run would have used before",
    )


def carry_over(plan: StatePlan) -> None:
    """Copy the shared working directory into the project when the plan says so.

    Copies into a temporary sibling first and renames it into place, so an
    interrupted copy never looks like finished project state.
    """
    if plan.action not in (CarryOver.COPY, CarryOver.COPY_UNVERIFIED):
        return
    plan.project_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{plan.pipeline_name}.", dir=plan.project_dir.parent))
    try:
        target = staging / plan.pipeline_name
        shutil.copytree(plan.shared_dir, target, symlinks=True)
        target.rename(plan.project_dir)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _write_self_ignoring_gitignore(directory: Path) -> None:
    """Keep the directory out of git even in a project scaffolded before it existed.

    Load packages hold raw extracted rows, so they must not be committed.
    """
    gitignore = directory / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("# Created by tycoon: per-project dlt state, never commit it.\n*\n")


@contextmanager
def project_pipelines_env(project_root: Path) -> Iterator[Path | None]:
    """Point dlt at the project's own pipelines directory for the duration.

    Yields that directory, or ``None`` when the user has set ``DLT_DATA_DIR``
    themselves, in which case tycoon doesn't override it. Setting the env var
    rather than passing ``pipelines_dir=`` also covers catalog-source shims
    already installed in a project, which build their own ``dlt.pipeline``.
    """
    if user_dlt_data_dir() is not None:
        yield None
        return
    previous = os.environ.get(DLT_DATA_DIR_ENV)
    data_dir = project_dlt_data_dir(project_root)
    pipelines = project_pipelines_dir(project_root)
    pipelines.mkdir(parents=True, exist_ok=True)
    _write_self_ignoring_gitignore(data_dir)
    os.environ[DLT_DATA_DIR_ENV] = str(data_dir)
    try:
        yield pipelines
    finally:
        if previous is None:
            os.environ.pop(DLT_DATA_DIR_ENV, None)
        else:
            os.environ[DLT_DATA_DIR_ENV] = previous
