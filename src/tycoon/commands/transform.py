"""tycoon transform — run dbt commands against the local DuckDB warehouse."""

from __future__ import annotations

import shutil
import subprocess
from typing import Optional

import typer

from tycoon.config import config
from tycoon.utils.console import ai_hint, console, error, header, next_steps, success

app = typer.Typer(
    help="Run dbt transformations against the local DuckDB warehouse.",
    no_args_is_help=True,
)

_TARGET_OPTION = typer.Option(
    None,
    "--target",
    "-t",
    help=(
        "dbt target name (dev / prod / ...). Defaults to tycoon.yml's "
        "`dbt_target` if set, then dbt's own resolution."
    ),
)
_SELECT_OPTION = typer.Option(None, "--select", "-s", help="dbt model selection syntax (e.g. 'staging+').")
_FULL_REFRESH_FLAG = typer.Option(False, "--full-refresh", help="Drop and recreate incremental models.")


def _dbt_executable() -> str:
    """Find the dbt binary, preferring the one co-located with this Python."""
    import sys
    from pathlib import Path

    # Prefer dbt in the same virtualenv bin dir as the running Python
    venv_dbt = Path(sys.executable).parent / "dbt"
    if venv_dbt.exists():
        return str(venv_dbt)
    dbt = shutil.which("dbt")
    if not dbt:
        error("`dbt` not found. Install it with: uv add dbt-duckdb")
        raise typer.Exit(1)
    return dbt


def _capture_dbt_and_refresh_safe(dbt_cmd: str) -> None:
    """Best-effort dbt observability capture + Rill dashboard refresh.

    Parses target/run_results.json, inserts into ``.tycoon/metadata.duckdb``,
    and (if Rill is present) re-exports the usage dashboard Parquets + YAMLs.
    Silently no-ops on any failure — the dbt invocation result is authoritative.
    """
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
        )
        capture_dbt_manifest_safe(meta, config.dbt_project_dir)
        refresh_usage_dashboards(project_root=config.root, rill_dir=config.rill_dir)
    except Exception:
        pass


def _resolved_dbt_target(cli_target: Optional[str]) -> str:
    """CLI flag wins; else tycoon.yml's `dbt_target`; else dbt's default."""
    if cli_target:
        return cli_target
    if config.project and config.project.dbt_target:
        return config.project.dbt_target
    return "dev"


def _resolved_dbt_profiles_dir(project_dir):
    """Find the profiles.yml directory for dbt, honoring tycoon.yml overrides.

    Order:
      1. ``tycoon.yml``'s ``dbt_profiles_dir`` (if set)
      2. ``<dbt_project_dir>/profiles.yml`` if co-located
      3. None — dbt falls back to ``~/.dbt/profiles.yml``
    """
    from pathlib import Path

    if config.project and config.project.dbt_profiles_dir:
        explicit = Path(config.project.dbt_profiles_dir)
        if not explicit.is_absolute():
            explicit = (config.root / explicit).resolve()
        if (explicit / "profiles.yml").exists():
            return explicit
    if (project_dir / "profiles.yml").exists():
        return project_dir
    return None


def _run_dbt(
    dbt_cmd: str,
    target: Optional[str],
    select: Optional[str],
    full_refresh: bool,
    extra: list[str] | None = None,
) -> int:
    """Invoke dbt as a subprocess from the configured dbt project directory.

    Honors ``tycoon.yml``'s ``dbt_profiles_dir`` / ``dbt_target`` /
    ``dbt_profile`` settings (introduced in v0.1.4 via ``tycoon register
    dbt``'s new flags). CLI flags still win.
    """
    dbt = _dbt_executable()
    project_dir = config.dbt_project_dir
    resolved_target = _resolved_dbt_target(target)

    cmd = [dbt, dbt_cmd, "--target", resolved_target]
    profiles_dir = _resolved_dbt_profiles_dir(project_dir)
    if profiles_dir is not None:
        cmd += ["--profiles-dir", str(profiles_dir)]
    if config.project and config.project.dbt_profile:
        cmd += ["--profile", config.project.dbt_profile]
    if select:
        cmd += ["--select", select]
    if full_refresh:
        cmd.append("--full-refresh")
    if extra:
        cmd.extend(extra)

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")

    result = subprocess.run(cmd, cwd=project_dir)
    _capture_dbt_and_refresh_safe(dbt_cmd)
    return result.returncode


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

@app.command()
def run(
    target: Optional[str] = _TARGET_OPTION,
    select: Optional[str] = _SELECT_OPTION,
    full_refresh: bool = _FULL_REFRESH_FLAG,
) -> None:
    """Execute dbt run — build all models (or a selection) in the warehouse."""
    header("dbt run")

    if not config.dbt_project_dir.exists():
        error(f"dbt project directory not found: {config.dbt_project_dir}")
        raise typer.Exit(1)

    rc = _run_dbt("run", target=target, select=select, full_refresh=full_refresh)

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
    target: Optional[str] = _TARGET_OPTION,
    select: Optional[str] = _SELECT_OPTION,
) -> None:
    """Execute dbt test — run data quality tests against built models."""
    header("dbt test")

    if not config.dbt_project_dir.exists():
        error(f"dbt project directory not found: {config.dbt_project_dir}")
        raise typer.Exit(1)

    rc = _run_dbt("test", target=target, select=select, full_refresh=False)

    if rc == 0:
        success("dbt test completed successfully.")
    else:
        error(f"dbt test exited with code {rc}.")
        ai_hint("why did my dbt tests fail?")
        raise typer.Exit(rc)


@app.command()
def build(
    target: Optional[str] = _TARGET_OPTION,
    select: Optional[str] = _SELECT_OPTION,
    full_refresh: bool = _FULL_REFRESH_FLAG,
) -> None:
    """Execute dbt build — run + test all models (or a selection)."""
    header("dbt build")

    if not config.dbt_project_dir.exists():
        error(f"dbt project directory not found: {config.dbt_project_dir}")
        raise typer.Exit(1)

    rc = _run_dbt("build", target=target, select=select, full_refresh=full_refresh)

    if rc == 0:
        success("dbt build completed successfully.")
    else:
        error(f"dbt build exited with code {rc}.")
        raise typer.Exit(rc)


@app.command()
def docs(
    target: Optional[str] = _TARGET_OPTION,
    port: int = typer.Option(8080, "--port", "-p", help="Port for dbt docs serve."),
) -> None:
    """Generate and serve dbt documentation in the browser."""
    header("dbt docs")

    if not config.dbt_project_dir.exists():
        error(f"dbt project directory not found: {config.dbt_project_dir}")
        raise typer.Exit(1)

    console.print("[bold]Generating dbt docs...[/bold]")
    gen_rc = _run_dbt("docs", target=target, select=None, full_refresh=False, extra=["generate"])
    if gen_rc != 0:
        error(f"dbt docs generate failed with code {gen_rc}.")
        raise typer.Exit(gen_rc)

    success("Docs generated. Starting server...")

    dbt = _dbt_executable()
    project_dir = config.dbt_project_dir
    cmd = [dbt, "docs", "serve", "--port", str(port)]
    profiles_dir = _resolved_dbt_profiles_dir(project_dir)
    if profiles_dir is not None:
        cmd += ["--profiles-dir", str(profiles_dir)]

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
    console.print(f"[bold green]dbt docs available at http://localhost:{port}[/bold green]")
    console.print("[dim]Press Ctrl+C to stop.[/dim]")

    try:
        subprocess.run(cmd, cwd=project_dir)
    except KeyboardInterrupt:
        console.print("\n[dim]dbt docs server stopped.[/dim]")
