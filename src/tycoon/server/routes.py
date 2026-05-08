"""REST API routes for the Tycoon dashboard server."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException

from tycoon.config import config
from tycoon.constants import PORTS
from tycoon.server.subprocess_manager import subprocess_manager
from tycoon.utils.duckdb_utils import db_file_size_mb, get_tables
from tycoon.utils.process import is_port_in_use

router = APIRouter(prefix="/api")


def _dbt_run_results() -> dict:
    """Parse dbt run_results.json if it exists."""
    results_path = config.dbt_project_dir / "target" / "run_results.json"
    if not results_path.exists():
        return {}
    try:
        data = json.loads(results_path.read_text())
        statuses: dict[str, int] = {}
        for r in data.get("results", []):
            s = r.get("status", "unknown")
            statuses[s] = statuses.get(s, 0) + 1
        return {
            "elapsed_time": data.get("elapsed_time"),
            "generated_at": data.get("metadata", {}).get("generated_at"),
            **statuses,
        }
    except (json.JSONDecodeError, KeyError):
        return {}


def _db_info(db_path: Path) -> dict:
    """Return size and table count for a database file."""
    size = db_file_size_mb(db_path)
    tables = get_tables(db_path)
    return {
        "size_mb": round(size, 2) if size is not None else None,
        "table_count": len(tables) if tables else None,
        "tables": [f"{s}.{t}" for s, t in tables],
    }


def _sources_info() -> dict:
    """Return registered source metadata."""
    return {
        name: {
            "type": src.type,
            "schema": src.schema_name,
        }
        for name, src in config.sources.items()
    }


@router.get("/status")
async def status() -> dict:
    """Live status of services, databases, sources, and dbt results."""
    services = {}
    for name, port in PORTS.items():
        services[name] = {
            "port": port,
            "healthy": is_port_in_use(port),
        }

    databases = {
        "raw_db": _db_info(config.raw_db),
        "local_db": _db_info(config.local_db),
    }

    return {
        "project": config.project.name if config.has_project_file else None,
        "sources": _sources_info(),
        "services": services,
        "databases": databases,
        "dbt": _dbt_run_results(),
        "busy": subprocess_manager.is_busy(),
        "active_run_id": subprocess_manager.active_run_id,
    }


@router.post("/run/pipeline/{source_name}")
async def run_pipeline(source_name: str) -> dict:
    """Spawn an ingestion pipeline for a registered source."""
    if subprocess_manager.is_busy():
        raise HTTPException(
            status_code=409,
            detail=f"Another run is active: {subprocess_manager.active_run_id}",
        )

    # Validate source exists
    if source_name not in config.sources:
        raise HTTPException(
            status_code=404,
            detail=f"Source '{source_name}' not found. Registered: {list(config.sources.keys())}",
        )

    run_id = f"pipeline-{source_name}-{uuid.uuid4().hex[:8]}"
    cmd = [sys.executable, "-m", "tycoon", "data", "sources", "run", source_name]

    try:
        await subprocess_manager.start_run(run_id, cmd)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"run_id": run_id, "source": source_name, "cmd": cmd}


@router.post("/run/dbt")
async def run_dbt() -> dict:
    """Spawn a dbt build subprocess."""
    if subprocess_manager.is_busy():
        raise HTTPException(
            status_code=409,
            detail=f"Another run is active: {subprocess_manager.active_run_id}",
        )

    run_id = f"dbt-{uuid.uuid4().hex[:8]}"
    cmd = [
        "dbt",
        "build",
        "--project-dir",
        str(config.dbt_project_dir),
    ]
    # Resolve profiles_dir / profile / target via the same path the CLI
    # uses, so a server-triggered build matches `tycoon data transform build`.
    from tycoon.dbt_profiles import resolve_profile

    project = config.project
    resolved = resolve_profile(
        project_root=config.root,
        dbt_project_dir=config.dbt_project_dir,
        project_dbt_profiles_dir=project.dbt_profiles_dir if project else None,
        project_dbt_profile=project.dbt_profile if project else None,
        project_dbt_target=project.dbt_target if project else None,
    )
    if resolved is not None:
        cmd += ["--profiles-dir", str(resolved.profiles_yml.parent)]
        cmd += ["--profile", resolved.profile, "--target", resolved.target]
    else:
        cmd += ["--profiles-dir", str(config.dbt_project_dir)]

    try:
        await subprocess_manager.start_run(run_id, cmd)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"run_id": run_id, "cmd": cmd}
