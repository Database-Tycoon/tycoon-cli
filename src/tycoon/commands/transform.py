"""tycoon transform — run dbt commands against the local DuckDB warehouse."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import time
from collections import deque
from collections.abc import Iterable
from pathlib import Path

import typer

from tycoon.config import config
from tycoon.dbt_profiles import ProfileOverrides, resolve_profile
from tycoon.utils.console import console, error, header, next_steps, success

app = typer.Typer(
    help="Run dbt transformations against the local DuckDB warehouse.",
    no_args_is_help=True,
)

_TARGET_OPTION = typer.Option(
    None,
    "--target",
    "-t",
    help="dbt target name (dev / prod / ...). Default: tycoon.yml's `dbt_target`, then the profile's own `target`, then 'dev'.",
)
_PROFILE_OPTION = typer.Option(
    None,
    "--profile",
    help="Profile name within profiles.yml. Default: tycoon.yml's `dbt_profile`, then dbt_project.yml's `profile:` field.",
)
_PROFILES_DIR_OPTION = typer.Option(
    None,
    "--profiles-dir",
    help="Directory containing profiles.yml. Default: tycoon.yml's `dbt_profiles_dir`, then <dbt_project_dir>, then $DBT_PROFILES_DIR, then ~/.dbt.",
)
_SELECT_OPTION = typer.Option(None, "--select", "-s", help="dbt model selection syntax (e.g. 'staging+').")
_FULL_REFRESH_FLAG = typer.Option(False, "--full-refresh", help="Drop and recreate incremental models.")


def _dbt_executable() -> str:
    """Find the dbt binary, preferring the one co-located with this Python."""
    venv_dbt = Path(sys.executable).parent / "dbt"
    if venv_dbt.exists():
        return str(venv_dbt)
    dbt = shutil.which("dbt")
    if not dbt:
        error("`dbt` not found. Install it with: uv add dbt-duckdb")
        raise typer.Exit(1)
    return dbt


_OUTPUT_TAIL_LINES = 20
_ERROR_SUMMARY_CHARS = 300
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_DBT_LOG_TIMESTAMP = re.compile(r"^\d{2}:\d{2}:\d{2}\s+")


def _stream_dbt(cmd: list[str], cwd: Path) -> tuple[int, list[str]]:
    """Run dbt, echoing its stdout as it arrives, and keep the last lines.

    The kept lines are the only record of an error dbt hits before it writes
    run_results.json, such as an unknown target or a locked DuckDB file.
    """
    tail: deque[str] = deque(maxlen=_OUTPUT_TAIL_LINES)
    with subprocess.Popen(
        cmd, cwd=cwd, stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", bufsize=1
    ) as proc:
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            tail.append(line)
    return proc.returncode, list(tail)


def _clip(text: str) -> str:
    text = " ".join(text.split())
    if len(text) <= _ERROR_SUMMARY_CHARS:
        return text
    return text[: _ERROR_SUMMARY_CHARS - 3] + "..."


def _dbt_error_summary(results: list[dict], output_tail: Iterable[str]) -> str | None:
    """One line on why a dbt run failed: the first failed node, else dbt's own error text."""
    from tycoon.core.events import DBT_ERROR_STATUSES

    failed = [r for r in results if (r.get("status") or "").lower() in DBT_ERROR_STATUSES]
    if failed:
        first = failed[0]
        text = f"{first.get('unique_id')}: {first.get('message') or first.get('status')}"
        if len(failed) > 1:
            text += f" (and {len(failed) - 1} more)"
        return _clip(text)

    lines = [_DBT_LOG_TIMESTAMP.sub("", _ANSI_ESCAPE.sub("", line)).strip() for line in output_tail]
    lines = [line for line in lines if line]
    if not lines:
        return None
    marker = max((i for i, line in enumerate(lines) if "Encountered an error" in line), default=None)
    if marker is not None and marker + 1 < len(lines):
        kind, *detail = lines[marker + 1 :]
        return _clip(f"{kind}: {' '.join(detail)}" if detail else kind)
    return _clip(lines[-1])


def _capture_dbt_and_refresh_safe(
    dbt_cmd: str,
    *,
    started_at: float,
    exit_code: int | None = None,
    target: str | None = None,
    output_tail: Iterable[str] = (),
) -> None:
    """Best-effort dbt observability capture + Rill dashboard refresh.

    ``exit_code`` is dbt's own; ``None`` means the caller doesn't know it, and
    the run's outcome is then read from the node statuses alone. A failed run
    is recorded even when dbt stopped before writing run_results.json, with
    ``output_tail`` (dbt's last lines of output) as its error summary.
    """
    run_results_path = config.dbt_project_dir / "target" / "run_results.json"
    try:
        fresh = run_results_path.stat().st_mtime >= started_at
    except Exception:
        fresh = False

    try:
        from tycoon.observability import (
            capture_dbt_manifest_safe,
            capture_dbt_safe,
            metadata_db_path,
        )
        from tycoon.scaffolding.rill_generator import refresh_usage_dashboards

        meta = metadata_db_path(config.root)
        capture_dbt_safe(
            meta,
            config.dbt_project_dir,
            command=dbt_cmd,
            # A stale run_results.json belongs to an earlier invocation, so
            # this run's exit code says nothing about it.
            exit_code=exit_code if fresh else None,
        )
        capture_dbt_manifest_safe(meta, config.dbt_project_dir)
        refresh_usage_dashboards(project_root=config.root, rill_dir=config.rill_dir)
    except Exception:
        pass

    try:
        import json

        from tycoon.core.events import DBT_ERROR_STATUSES, DbtRunCompleted
        from tycoon.metadata_backends.duckdb_file import DuckDBFileBackend
        from tycoon.observability import metadata_db_path

        if fresh:
            with open(run_results_path, encoding="utf-8") as f:
                run_results = json.load(f)
            elapsed = float(run_results.get("elapsed_time") or 0.0)
            args = run_results.get("args") or {}
            target = args.get("target") or target
            results = run_results.get("results") or []
        elif exit_code not in (None, 0):
            elapsed = time.time() - started_at
            results = []
        else:
            return

        models_run = len(results)
        models_errored = sum(1 for r in results if (r.get("status") or "").lower() in DBT_ERROR_STATUSES)
        failed = models_errored > 0 or exit_code not in (None, 0)

        event = DbtRunCompleted(
            source_id="dbt",
            runtime_id="dbt",
            command=dbt_cmd,
            target=target or "dev",
            models_run=models_run,
            models_passed=models_run - models_errored,
            models_errored=models_errored,
            duration_seconds=elapsed,
            exit_code=exit_code,
            error=_dbt_error_summary(results, output_tail) if failed else None,
        )
        with DuckDBFileBackend(metadata_db_path(config.root)) as b:
            b.append_event(event)
    except Exception:
        pass


def _auto_osi_scaffold_safe() -> None:
    """Re-emit dbt_project/semantic/osi.yaml after a successful dbt run.

    Opt-in via ``transform.auto_osi_scaffold: true`` in tycoon.yml. Never
    raises into the dbt command's own success path — OSI failures are
    informational only.
    """
    project = config.project
    warehouse_db = config.local_db
    if project is None or not project.transform.auto_osi_scaffold or warehouse_db is None:
        return
    try:
        from tycoon.scaffolding.osi_generator import scaffold_osi

        out_path = config.dbt_project_dir / "semantic" / "osi.yaml"
        scaffold_osi(
            warehouse_db=warehouse_db,
            out_path=out_path,
            project_name=project.name,
            dbt_project_dir=config.dbt_project_dir,
        )
    except Exception:
        pass


def _resolve_for_run(
    profile: str | None,
    profiles_dir: Path | None,
    target: str | None,
) -> tuple[Path | None, str | None, str]:
    """Resolve profile/profiles_dir/target via the central resolver.

    Returns ``(profiles_dir, profile_name, target)`` ready to splice into
    a dbt CLI invocation. Any of the first two may be ``None`` if the
    user is happy with dbt's own discovery; ``target`` is always set.
    """
    project = config.project
    project_root = config.root
    dbt_dir = config.dbt_project_dir

    overrides = ProfileOverrides(
        profiles_dir=profiles_dir,
        profile=profile,
        target=target,
    )

    resolved = resolve_profile(
        project_root=project_root,
        dbt_project_dir=dbt_dir,
        project_dbt_profiles_dir=project.dbt_profiles_dir if project else None,
        project_dbt_profile=project.dbt_profile if project else None,
        project_dbt_target=project.dbt_target if project else None,
        overrides=overrides,
    )

    if resolved is not None:
        return resolved.profiles_yml.parent, resolved.profile, resolved.target

    # Resolver couldn't find a profile; fall back to whatever the user
    # passed on the CLI / had in tycoon.yml so dbt's own discovery still
    # has a chance.
    fallback_target = target or (project.dbt_target if project else None) or "dev"
    return profiles_dir, profile, fallback_target


def _run_dbt(
    dbt_cmd: str,
    profile: str | None,
    profiles_dir: Path | None,
    target: str | None,
    select: str | None,
    full_refresh: bool,
    extra: list[str] | None = None,
) -> int:
    """Invoke dbt as a subprocess from the configured dbt project directory."""
    dbt = _dbt_executable()
    project_dir = config.dbt_project_dir

    resolved_dir, resolved_profile, resolved_target = _resolve_for_run(
        profile=profile, profiles_dir=profiles_dir, target=target
    )

    cmd = [dbt, dbt_cmd, "--target", resolved_target]
    if resolved_dir is not None:
        cmd += ["--profiles-dir", str(resolved_dir)]
    if resolved_profile:
        cmd += ["--profile", resolved_profile]
    if select:
        cmd += ["--select", select]
    if full_refresh:
        cmd.append("--full-refresh")
    if extra:
        cmd.extend(extra)

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")

    started_at = time.time()
    returncode, output_tail = _stream_dbt(cmd, project_dir)
    _capture_dbt_and_refresh_safe(
        dbt_cmd,
        started_at=started_at,
        exit_code=returncode,
        target=resolved_target,
        output_tail=output_tail,
    )
    if returncode == 0 and dbt_cmd in {"run", "build"}:
        _auto_osi_scaffold_safe()
    return returncode


@app.command()
def run(
    target: str | None = _TARGET_OPTION,
    profile: str | None = _PROFILE_OPTION,
    profiles_dir: Path | None = _PROFILES_DIR_OPTION,
    select: str | None = _SELECT_OPTION,
    full_refresh: bool = _FULL_REFRESH_FLAG,
) -> None:
    """Execute dbt run — build all models (or a selection) in the warehouse."""
    header("dbt run")

    if not config.dbt_project_dir.exists():
        error(f"dbt project directory not found: {config.dbt_project_dir}")
        raise typer.Exit(1)

    rc = _run_dbt(
        "run",
        profile=profile,
        profiles_dir=profiles_dir,
        target=target,
        select=select,
        full_refresh=full_refresh,
    )

    if rc == 0:
        success("dbt run completed successfully.")
        next_steps(
            ("tycoon start --only rill", "explore data in the Rill dashboard"),
            ("tycoon data status", "check source freshness and row counts"),
        )
    else:
        error(f"dbt run exited with code {rc}.")
        raise typer.Exit(rc)


@app.command()
def test(
    target: str | None = _TARGET_OPTION,
    profile: str | None = _PROFILE_OPTION,
    profiles_dir: Path | None = _PROFILES_DIR_OPTION,
    select: str | None = _SELECT_OPTION,
) -> None:
    """Execute dbt test — run data quality tests against built models."""
    header("dbt test")

    if not config.dbt_project_dir.exists():
        error(f"dbt project directory not found: {config.dbt_project_dir}")
        raise typer.Exit(1)

    rc = _run_dbt(
        "test",
        profile=profile,
        profiles_dir=profiles_dir,
        target=target,
        select=select,
        full_refresh=False,
    )

    if rc == 0:
        success("dbt test completed successfully.")
    else:
        error(f"dbt test exited with code {rc}.")
        raise typer.Exit(rc)


@app.command()
def build(
    target: str | None = _TARGET_OPTION,
    profile: str | None = _PROFILE_OPTION,
    profiles_dir: Path | None = _PROFILES_DIR_OPTION,
    select: str | None = _SELECT_OPTION,
    full_refresh: bool = _FULL_REFRESH_FLAG,
) -> None:
    """Execute dbt build — run + test all models (or a selection)."""
    header("dbt build")

    if not config.dbt_project_dir.exists():
        error(f"dbt project directory not found: {config.dbt_project_dir}")
        raise typer.Exit(1)

    rc = _run_dbt(
        "build",
        profile=profile,
        profiles_dir=profiles_dir,
        target=target,
        select=select,
        full_refresh=full_refresh,
    )

    if rc == 0:
        success("dbt build completed successfully.")
    else:
        error(f"dbt build exited with code {rc}.")
        raise typer.Exit(rc)


@app.command()
def docs(
    target: str | None = _TARGET_OPTION,
    profile: str | None = _PROFILE_OPTION,
    profiles_dir: Path | None = _PROFILES_DIR_OPTION,
    port: int = typer.Option(8080, "--port", "-p", help="Port for dbt docs serve."),
) -> None:
    """Generate and serve dbt documentation in the browser."""
    header("dbt docs")

    if not config.dbt_project_dir.exists():
        error(f"dbt project directory not found: {config.dbt_project_dir}")
        raise typer.Exit(1)

    console.print("[bold]Generating dbt docs...[/bold]")
    gen_rc = _run_dbt(
        "docs",
        profile=profile,
        profiles_dir=profiles_dir,
        target=target,
        select=None,
        full_refresh=False,
        extra=["generate"],
    )
    if gen_rc != 0:
        error(f"dbt docs generate failed with code {gen_rc}.")
        raise typer.Exit(gen_rc)

    success("Docs generated. Starting server...")

    dbt = _dbt_executable()
    project_dir = config.dbt_project_dir
    cmd = [dbt, "docs", "serve", "--port", str(port)]
    resolved_dir, resolved_profile, _ = _resolve_for_run(profile=profile, profiles_dir=profiles_dir, target=target)
    if resolved_dir is not None:
        cmd += ["--profiles-dir", str(resolved_dir)]
    if resolved_profile:
        cmd += ["--profile", resolved_profile]

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
    console.print(f"[bold green]dbt docs available at http://localhost:{port}[/bold green]")
    console.print("[dim]Press Ctrl+C to stop.[/dim]")

    try:
        subprocess.run(cmd, cwd=project_dir)
    except KeyboardInterrupt:
        console.print("\n[dim]dbt docs server stopped.[/dim]")
