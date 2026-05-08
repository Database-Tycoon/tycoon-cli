"""tycoon profiles — discover, inspect, and validate dbt profiles.

Sits alongside ``tycoon doctor`` and ``tycoon register`` — profiles are
a configuration concern, not a pipeline one. Three subcommands:

* ``list``   — every profile in the active ``profiles.yml``, with targets
  + adapter types. Shows which one tycoon will use by default.
* ``show``   — pretty-print one profile, with secrets redacted.
* ``doctor`` — verify the active profile resolves and its adapter
  matches ``stack.warehouse``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.table import Table

from tycoon.config import config
from tycoon.dbt_profiles import (
    ProfileOverrides,
    discover_profiles,
    redact_secrets,
    resolve_profile,
)
from tycoon.utils.console import console, error, header, info, success, warn

app = typer.Typer(
    help="Discover, inspect, and validate dbt profiles.",
    no_args_is_help=True,
)


_PROFILE_OPTION = typer.Option(
    None,
    "--profile",
    help="Profile name override (default: tycoon.yml's `dbt_profile` or dbt_project.yml's `profile:`).",
)
_PROFILES_DIR_OPTION = typer.Option(
    None,
    "--profiles-dir",
    help="profiles.yml directory override (default: tycoon.yml → <dbt_project_dir> → $DBT_PROFILES_DIR → ~/.dbt).",
)
_TARGET_OPTION = typer.Option(
    None,
    "--target",
    "-t",
    help="Target name override (default: tycoon.yml's `dbt_target`, then the profile's own).",
)


def _require_project() -> None:
    """Bail when there's no tycoon.yml — every subcommand needs one."""
    if not config.has_project_file:
        error(
            "No tycoon.yml found. Run [bold]tycoon init[/bold] first, "
            "or cd into an existing tycoon project."
        )
        raise typer.Exit(1)


def _resolve_for_cli(
    profile: Optional[str],
    profiles_dir: Optional[Path],
    target: Optional[str],
):
    """Centralized resolve_profile call; returns ResolvedProfile | None."""
    project = config.project
    return resolve_profile(
        project_root=config.root,
        dbt_project_dir=config.dbt_project_dir,
        project_dbt_profiles_dir=project.dbt_profiles_dir if project else None,
        project_dbt_profile=project.dbt_profile if project else None,
        project_dbt_target=project.dbt_target if project else None,
        overrides=ProfileOverrides(
            profiles_dir=profiles_dir,
            profile=profile,
            target=target,
        ),
    )


@app.command(name="list")
def list_cmd(
    profiles_dir: Optional[Path] = _PROFILES_DIR_OPTION,
) -> None:
    """List every profile in the active profiles.yml + targets + adapters."""
    _require_project()
    header("Available dbt profiles")

    resolved = _resolve_for_cli(profile=None, profiles_dir=profiles_dir, target=None)
    if resolved is None:
        warn(
            "No profiles.yml found in any of: --profiles-dir, tycoon.yml's "
            "dbt_profiles_dir, <dbt_project_dir>, $DBT_PROFILES_DIR, or "
            "~/.dbt. Run `tycoon register dbt` or create one manually."
        )
        return

    info(f"Reading [bold]{resolved.profiles_yml}[/bold] (via {resolved.source})")

    profiles = discover_profiles(resolved.profiles_yml)
    if not profiles:
        warn("profiles.yml is empty or unparseable.")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Profile")
    table.add_column("Targets")
    table.add_column("Default")
    table.add_column("Adapter(s)")
    table.add_column("Active")

    for p in profiles:
        adapters = ", ".join(sorted(set(p.adapter_types.values()))) or "—"
        is_active = p.name == resolved.profile
        marker = "✓" if is_active else ""
        active_target = resolved.target if is_active else ""
        targets_display = ", ".join(p.targets) if p.targets else "—"
        if active_target:
            targets_display = ", ".join(
                f"[bold]{t}[/bold]" if t == active_target else t
                for t in p.targets
            )
        table.add_row(
            f"[bold]{p.name}[/bold]" if is_active else p.name,
            targets_display,
            p.default_target or "—",
            adapters,
            marker,
        )

    console.print(table)
    console.print(
        f"\n[dim]Tycoon will use:[/dim] [bold]{resolved.profile}[/bold] "
        f"(target: [bold]{resolved.target}[/bold])"
    )


@app.command()
def show(
    name: Optional[str] = typer.Argument(
        None,
        help="Profile name. Defaults to the active profile (per tycoon.yml + dbt_project.yml).",
    ),
    profiles_dir: Optional[Path] = _PROFILES_DIR_OPTION,
) -> None:
    """Pretty-print one profile, with secrets redacted."""
    _require_project()

    resolved = _resolve_for_cli(profile=name, profiles_dir=profiles_dir, target=None)
    if resolved is None:
        error(
            "No profiles.yml found, or the requested profile doesn't exist. "
            "Run `tycoon profiles list` to see what's available."
        )
        raise typer.Exit(1)

    header(f"Profile: {resolved.profile}")
    info(f"From [bold]{resolved.profiles_yml}[/bold] (via {resolved.source})")

    raw = yaml.safe_load(resolved.profiles_yml.read_text()) or {}
    body = raw.get(resolved.profile, {})
    if not isinstance(body, dict):
        error("Profile is not a YAML mapping.")
        raise typer.Exit(1)

    redacted = redact_secrets(body)
    console.print()
    console.print(yaml.dump({resolved.profile: redacted}, default_flow_style=False, sort_keys=False))


@app.command()
def doctor(
    profile: Optional[str] = _PROFILE_OPTION,
    profiles_dir: Optional[Path] = _PROFILES_DIR_OPTION,
    target: Optional[str] = _TARGET_OPTION,
) -> None:
    """Validate the active profile + cross-check against tycoon.yml."""
    _require_project()
    header("Profile doctor")

    rc = run_profile_checks(profile=profile, profiles_dir=profiles_dir, target=target)
    raise typer.Exit(rc)


def run_profile_checks(
    profile: Optional[str] = None,
    profiles_dir: Optional[Path] = None,
    target: Optional[str] = None,
) -> int:
    """Shared check logic — also called by ``tycoon doctor``.

    Returns 0 if every check passes (or only emits informational rows),
    1 if at least one error was emitted. Warnings count as soft.
    """
    project = config.project
    resolved = _resolve_for_cli(profile=profile, profiles_dir=profiles_dir, target=target)

    if resolved is None:
        error(
            "No profiles.yml resolved. Tried CLI flags, tycoon.yml's "
            "dbt_profiles_dir, <dbt_project_dir>, $DBT_PROFILES_DIR, ~/.dbt."
        )
        return 1

    success(f"Found profiles.yml: {resolved.profiles_yml} (via {resolved.source})")
    success(f"Active profile: {resolved.profile} (target: {resolved.target})")

    if resolved.warehouse is None:
        warn(
            f"Target [bold]{resolved.target}[/bold] is not defined under "
            f"profile [bold]{resolved.profile}[/bold]'s outputs. "
            "Available targets: "
            + ", ".join(
                discover_profiles(resolved.profiles_yml)[0].targets
                if discover_profiles(resolved.profiles_yml)
                else []
            )
        )
        return 1

    success(f"Adapter: {resolved.warehouse.adapter_type}")
    if resolved.warehouse.display:
        info(f"  → {resolved.warehouse.display}")

    # Cross-check against tycoon.yml's stack.warehouse, if both are known.
    if project is None:
        return 0

    declared = project.stack.warehouse.value if project.stack.warehouse else None
    actual = resolved.warehouse.tycoon_warehouse_type
    if declared and actual and declared != actual:
        error(
            f"Adapter mismatch: tycoon.yml stack.warehouse = "
            f"[bold]{declared}[/bold] but profile is [bold]{actual}[/bold]. "
            "Either edit tycoon.yml or pick a different profile/target."
        )
        return 1
    if declared and actual:
        success(f"Adapter matches stack.warehouse ({declared}).")
    elif not declared:
        info("stack.warehouse not declared in tycoon.yml — skipping mismatch check.")
    return 0
