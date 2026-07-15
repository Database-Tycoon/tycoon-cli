"""tycoon register — attach an existing dbt or Rill project to tycoon.yml."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml

from tycoon.commands.init import (
    _clone_repo,
    _extract_dbt_warehouse_target,
    _normalize_warehouse_for_compare,
)
from tycoon.config import config
from tycoon.project import (
    BITool,
    PROJECT_FILENAME,
    TransformationTool,
    WarehouseType,
)
from tycoon.utils.console import console, error, header, info, success, warn


app = typer.Typer(
    help="Attach existing dbt, Rill, or warehouse components to the current tycoon.yml.",
    no_args_is_help=True,
)


def _resolve_path_or_url(source: str, default_clone_dest: Path) -> Path | None:
    """Accept a local path or a git URL. Clone if URL. Return resolved absolute path."""
    if source.startswith(("http://", "https://", "git@")):
        clone_here = typer.confirm(
            f"Clone into {default_clone_dest}?",
            default=True,
        )
        dest = default_clone_dest
        if not clone_here:
            dest = Path(
                typer.prompt("Where should the project be cloned?", default=str(default_clone_dest))
            ).expanduser().resolve()
        if not _clone_repo(source, dest):
            return None
        return dest

    path = Path(source).expanduser().resolve()
    if not path.exists():
        error(f"Path does not exist: {path}")
        return None
    return path


def _create_new_dbt_project(
    raw: dict,
    source: str | None,
    default_target: Path,
) -> Path | None:
    """Bootstrap a fresh dbt project wired to the active tycoon warehouse.

    Reuses :func:`tycoon.scaffolding.templates._scaffold_dbt_project` —
    same code path that ``tycoon init`` runs when the user picks "Create
    new dbt project" in the wizard. Returns the resolved target path on
    success, or ``None`` after printing a user-facing error.

    Limitation: the underlying scaffolder only knows DuckDB and MotherDuck
    profiles today. For Snowflake/BigQuery warehouses, this command bails
    early so users hand-author the profile and use plain
    ``tycoon register dbt <path>``.
    """
    from tycoon.scaffolding.templates import _scaffold_dbt_project

    target = (
        Path(source).expanduser().resolve() if source else default_target.resolve()
    )

    if (target / "dbt_project.yml").exists():
        error(
            f"{target} already contains a dbt_project.yml. "
            f"Use `tycoon register dbt {target}` to register it instead."
        )
        return None

    stack_raw = raw.get("stack") or {}
    warehouse_value = stack_raw.get("warehouse", WarehouseType.duckdb.value)
    try:
        warehouse_type = WarehouseType(warehouse_value)
    except ValueError:
        warehouse_type = WarehouseType.duckdb

    if warehouse_type not in (WarehouseType.duckdb, WarehouseType.motherduck):
        error(
            f"--create only supports DuckDB and MotherDuck warehouses today "
            f"(active warehouse: {warehouse_type.value}). For Snowflake / "
            "BigQuery, hand-author dbt_project.yml + profiles.yml and use "
            "`tycoon register dbt <path>`."
        )
        return None

    db = raw.get("database") or {}
    raw_db_path = db.get("raw", "data/raw.duckdb")
    warehouse_db_path = db.get("warehouse", "data/warehouse.duckdb")

    name = raw.get("name", config.root.name)
    _scaffold_dbt_project(
        dbt_dir=target,
        name=name,
        warehouse=warehouse_type,
        warehouse_db_path=warehouse_db_path,
        raw_db_path=raw_db_path,
        target=config.root,
    )
    return target


def _require_tycoon_yml() -> Path:
    """Resolve the tycoon.yml path, or bail if no project."""
    if not config.has_project_file:
        error(
            "No tycoon.yml found in the current project. "
            "Run `tycoon init` first, or cd into an existing tycoon project."
        )
        raise typer.Exit(1)
    return config.root / PROJECT_FILENAME


def _load_raw_tycoon_yml(path: Path) -> dict:
    """Load tycoon.yml as a raw dict (preserving unknown keys on write)."""
    raw = yaml.safe_load(path.read_text()) or {}
    if not isinstance(raw, dict):
        error(f"tycoon.yml is not a mapping: {path}")
        raise typer.Exit(1)
    return raw


def _write_raw_tycoon_yml(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


@app.command(name="dbt")
def register_dbt(
    source: Annotated[
        Optional[str],
        typer.Argument(
            help=(
                "Local path or GitHub URL of an existing dbt project. "
                "Required unless --create is set (in which case it overrides "
                "the default sibling path)."
            ),
        ),
    ] = None,
    create: Annotated[
        bool,
        typer.Option(
            "--create",
            help=(
                "Bootstrap a new dbt project (sibling repo at "
                "../<project>-dbt by default) wired to the active tycoon "
                "warehouse, then register it. Pass SOURCE to override the "
                "location. Refuses if a dbt_project.yml already exists at "
                "the target — use plain `register dbt <path>` for that case."
            ),
        ),
    ] = False,
    profiles_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--profiles-dir",
            help=(
                "Directory containing profiles.yml. Defaults to <SOURCE>/profiles.yml "
                "if present, then ~/.dbt/profiles.yml — same as dbt's own resolution."
            ),
        ),
    ] = None,
    profile: Annotated[
        Optional[str],
        typer.Option(
            "--profile",
            help="Profile name within profiles.yml. Default: the `profile:` field in dbt_project.yml.",
        ),
    ] = None,
    target: Annotated[
        Optional[str],
        typer.Option(
            "--target",
            help="Target within the profile (dev / prod / ...). Default: the profile's `target:` field, then 'dev'.",
        ),
    ] = None,
    no_attach_metadata: Annotated[
        bool,
        typer.Option(
            "--no-attach-metadata",
            help=(
                "Skip wiring tycoon's observability metadata DB into the "
                "registered profile. Default: attach `.tycoon/metadata.duckdb` "
                "as `tycoon_meta` so dbt models can SELECT from it directly."
            ),
        ),
    ] = False,
) -> None:
    """Attach an existing dbt project — or bootstrap a new one with ``--create``.

    The three profile-related flags mirror dbt's own CLI options. Any value
    you pass is also persisted in tycoon.yml under ``dbt_profiles_dir`` /
    ``dbt_profile`` / ``dbt_target`` so subsequent ``tycoon data transform``
    runs use them automatically.
    """
    header("Register dbt project")

    yml_path = _require_tycoon_yml()
    raw = _load_raw_tycoon_yml(yml_path)

    existing_dbt = raw.get("dbt_project_dir")
    if existing_dbt:
        warn(f"tycoon.yml already has dbt_project_dir = {existing_dbt!r}.")
        if not typer.confirm("Overwrite it?", default=False):
            info("Aborted; no changes made.")
            raise typer.Exit(0)

    if not create and source is None:
        error(
            "SOURCE is required unless --create is set. "
            "Pass a path/URL to register an existing dbt project, "
            "or use --create to bootstrap a new one."
        )
        raise typer.Exit(1)

    default_clone = config.root.parent / f"{raw.get('name', config.root.name)}-dbt"

    if create:
        resolved = _create_new_dbt_project(raw, source, default_clone)
        if resolved is None:
            raise typer.Exit(1)
    else:
        assert source is not None  # narrowed by the check above
        resolved = _resolve_path_or_url(source, default_clone)
        if resolved is None:
            raise typer.Exit(1)
        if not (resolved / "dbt_project.yml").exists():
            error(f"{resolved} does not contain a dbt_project.yml")
            raise typer.Exit(1)

    # Resolve profiles_dir to an absolute path so the warehouse-alignment
    # extractor and the persisted tycoon.yml entry agree.
    if profiles_dir is not None:
        profiles_dir = profiles_dir.expanduser().resolve()
        if not (profiles_dir / "profiles.yml").exists():
            error(f"{profiles_dir} does not contain a profiles.yml")
            raise typer.Exit(1)

    # Write path relative to tycoon.yml when possible, otherwise absolute
    import os

    def _rel_or_abs(p: Path) -> str:
        try:
            return os.path.relpath(p, config.root)
        except ValueError:
            return str(p)

    raw["dbt_project_dir"] = _rel_or_abs(resolved)
    if profiles_dir is not None:
        raw["dbt_profiles_dir"] = _rel_or_abs(profiles_dir)
    elif "dbt_profiles_dir" in raw:
        # Don't carry forward a stale value from a previous register call.
        del raw["dbt_profiles_dir"]
    if profile is not None:
        raw["dbt_profile"] = profile
    elif "dbt_profile" in raw:
        del raw["dbt_profile"]
    if target is not None:
        raw["dbt_target"] = target
    elif "dbt_target" in raw:
        del raw["dbt_target"]

    # Update stack — `--create` means tycoon owns the project (managed),
    # otherwise it's user-authored / external.
    stack = raw.setdefault("stack", {})
    stack["transformation"] = TransformationTool.dbt.value
    stack["transformation_managed"] = bool(create)

    # Warehouse alignment offer — pass the explicit profile/target through
    # so alignment reads the right adapter config.
    dbt_target = _extract_dbt_warehouse_target(
        resolved,
        profiles_dir=profiles_dir,
        profile_name=profile,
        target_name=target,
    )
    if dbt_target is not None:
        if dbt_target.adapter_type == "duckdb":
            _align_duckdb_warehouse(raw, stack, dbt_target.identifier)
        else:
            _align_cloud_warehouse(raw, stack, dbt_target)

    _write_raw_tycoon_yml(yml_path, raw)
    success(f"Registered dbt project at {resolved}")
    info(f"Updated {yml_path.name}.")

    # Wire tycoon's observability metadata into the registered profile so
    # dbt models can SELECT from `tycoon_meta.main.<table>` directly.
    # Idempotent — skipped if the ATTACH is already present, or if a
    # profiles.yml isn't co-located (caller's choice). Opt out via flag.
    if not no_attach_metadata:
        from tycoon.scaffolding.observability_dbt import (
            attach_metadata_to_profiles,
            scaffold_observability_models,
        )

        # profiles.yml lookup: explicit --profiles-dir wins, then co-located
        if profiles_dir is not None:
            profiles_yml = profiles_dir / "profiles.yml"
        else:
            profiles_yml = resolved / "profiles.yml"

        if profiles_yml.exists():
            metadata_db = config.root / ".tycoon" / "metadata.duckdb"
            try:
                changed = attach_metadata_to_profiles(profiles_yml, metadata_db)
                if changed:
                    info(f"Added [bold]tycoon_meta[/bold] ATTACH to {profiles_yml}")
                # Also generate the _tycoon staging models so users get the
                # full surface (dbt + Nao via downstream sync).
                scaffold_observability_models(resolved)
                info(
                    f"Generated [bold]models/_tycoon/[/bold] under {resolved}. "
                    "Run [bold]tycoon data transform run[/bold] to build them."
                )
            except Exception as exc:  # best-effort
                warn(f"Could not wire observability metadata: {exc}")
        else:
            info(
                "[dim]No co-located profiles.yml — skipping metadata ATTACH. "
                "Run [bold]tycoon data observability scaffold[/bold] to add it later.[/dim]"
            )


def _align_duckdb_warehouse(raw: dict, stack: dict, dbt_warehouse: str) -> None:
    """DuckDB / MotherDuck alignment (v0.1.1 + v0.1.2 behavior, unchanged)."""
    current_warehouse = raw.get("database", {}).get("warehouse", "")
    if current_warehouse.startswith("md:"):
        current_norm = current_warehouse
    else:
        abs_path = Path(current_warehouse).expanduser() if current_warehouse else Path()
        if not abs_path.is_absolute():
            abs_path = (config.root / current_warehouse).resolve() if current_warehouse else Path()
        else:
            abs_path = abs_path.resolve()
        current_norm = str(abs_path) if current_warehouse else ""

    if current_norm == _normalize_warehouse_for_compare(dbt_warehouse):
        return

    console.print()
    warn(
        f"Your dbt project targets {dbt_warehouse}, "
        f"but tycoon.yml has warehouse = {current_warehouse!r}."
    )
    if typer.confirm(f"Update warehouse to {dbt_warehouse}?", default=True):
        raw.setdefault("database", {})["warehouse"] = dbt_warehouse
        if raw["database"].get("raw", "") == current_warehouse:
            raw["database"]["raw"] = dbt_warehouse
        stack["warehouse"] = (
            WarehouseType.motherduck.value
            if dbt_warehouse.startswith("md:")
            else WarehouseType.duckdb.value
        )


def _align_cloud_warehouse(raw: dict, stack: dict, dbt_target) -> None:
    """Alignment for Snowflake / BigQuery / Redshift / other cloud adapters.

    These adapters don't map to a single ``path`` field, so we do **not**
    touch ``database.warehouse`` (it's meaningless for them). What we *do*
    check is whether ``stack.warehouse`` agrees with the dbt adapter type
    — and, for Snowflake, whether the account matches any previously-
    registered account in the raw yaml under ``warehouse_connection``.
    """
    current_stack_type = stack.get("warehouse", WarehouseType.duckdb.value)
    desired_type = dbt_target.tycoon_warehouse_type
    if not desired_type:
        # Unknown adapter — warn but don't force a change.
        console.print()
        warn(
            f"Your dbt project uses adapter type {dbt_target.adapter_type!r} "
            f"which tycoon doesn't model yet. Leaving stack.warehouse as "
            f"{current_stack_type!r}; make sure that matches your expectations."
        )
        return

    if current_stack_type != desired_type:
        console.print()
        warn(
            f"Your dbt project targets {dbt_target.display} "
            f"(adapter {dbt_target.adapter_type!r}), "
            f"but tycoon.yml has stack.warehouse = {current_stack_type!r}."
        )
        info(
            "tycoon.yml's database.warehouse path only applies to DuckDB / "
            "MotherDuck, so it won't be touched. Only stack.warehouse is "
            "adjusted for cloud adapters."
        )
        if typer.confirm(
            f"Update stack.warehouse to {desired_type!r}?", default=True
        ):
            stack["warehouse"] = desired_type

    # Snowflake: surface an account-mismatch hint when the user previously
    # recorded one in `warehouse_connection.account` (free-form yaml key).
    if dbt_target.adapter_type == "snowflake" and dbt_target.identifier:
        prior_account = (
            raw.get("warehouse_connection", {}).get("account")
            if isinstance(raw.get("warehouse_connection"), dict)
            else None
        )
        if prior_account and prior_account != dbt_target.identifier:
            warn(
                f"tycoon.yml's warehouse_connection.account = "
                f"{prior_account!r} differs from the dbt profile's "
                f"account = {dbt_target.identifier!r}. Double-check that "
                "ingestion and dbt are both pointing at the right account."
            )


_LOCAL_TYPE_ALIASES = {"local", "l", "duckdb"}
_CLOUD_TYPE_ALIASES = {"cloud", "c", "motherduck", "md"}


@app.command(name="warehouse")
def register_warehouse(
    warehouse_type: Annotated[
        Optional[str],
        typer.Option(
            "--type",
            help=(
                "Warehouse type — 'duckdb' (or 'local') for a local DuckDB file, "
                "'motherduck' (or 'cloud') for a MotherDuck catalog. Skips the "
                "interactive prompt when set."
            ),
        ),
    ] = None,
    path: Annotated[
        Optional[str],
        typer.Option(
            "--path",
            help="For --type duckdb: path to the local .duckdb file. Default: data/warehouse.duckdb.",
        ),
    ] = None,
    catalog: Annotated[
        Optional[str],
        typer.Option(
            "--catalog",
            help="For --type motherduck: catalog name. Becomes md:<catalog> in tycoon.yml.",
        ),
    ] = None,
    no_prompt: Annotated[
        bool,
        typer.Option(
            "--no-prompt",
            help="Fail rather than prompt — for CI / scripted setup.",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Overwrite an existing warehouse without prompting.",
        ),
    ] = False,
) -> None:
    """Attach or switch the warehouse (local DuckDB or MotherDuck) in tycoon.yml.

    Fully scriptable when ``--type`` plus the type-specific value (``--path``
    or ``--catalog``) is set; otherwise drops to interactive prompts.
    Combine with ``--no-prompt`` and ``--force`` for non-interactive CI use.
    """
    import os

    header("Register warehouse")

    yml_path = _require_tycoon_yml()
    raw = _load_raw_tycoon_yml(yml_path)

    existing = raw.get("database", {}).get("warehouse", "")
    if existing:
        if force:
            info(f"Overwriting existing warehouse: {existing!r}.")
        elif no_prompt:
            error(
                f"tycoon.yml already has warehouse = {existing!r}. "
                "Re-run with --force to overwrite, or remove --no-prompt to be asked."
            )
            raise typer.Exit(1)
        else:
            warn(f"tycoon.yml already has warehouse = {existing!r}.")
            if not typer.confirm("Overwrite it?", default=False):
                info("Aborted; no changes made.")
                raise typer.Exit(0)

    # ---- Resolve warehouse type ----
    if warehouse_type:
        normalized = warehouse_type.strip().lower()
        if normalized in _LOCAL_TYPE_ALIASES:
            choice = "local"
        elif normalized in _CLOUD_TYPE_ALIASES:
            choice = "cloud"
        else:
            error(
                f"Unknown --type {warehouse_type!r}. Expected one of: "
                f"{', '.join(sorted(_LOCAL_TYPE_ALIASES | _CLOUD_TYPE_ALIASES))}."
            )
            raise typer.Exit(1)
    elif no_prompt:
        error("--type is required when --no-prompt is set.")
        raise typer.Exit(1)
    else:
        choice = typer.prompt(
            "Cloud (MotherDuck) or local DuckDB? [cloud/local]",
            default="local",
        ).strip().lower()
        if choice in _CLOUD_TYPE_ALIASES:
            choice = "cloud"
        elif choice in _LOCAL_TYPE_ALIASES:
            choice = "local"
        else:
            error(f"Unknown choice: {choice!r}. Expected 'cloud' or 'local'.")
            raise typer.Exit(1)

    # ---- Resolve type-specific value ----
    if choice == "cloud":
        if catalog is not None:
            md_name = catalog.strip()
        elif no_prompt:
            error("--catalog is required when --no-prompt is set with --type motherduck.")
            raise typer.Exit(1)
        else:
            default_name = str(raw.get("name", config.root.name)).replace("-", "_")
            md_name = typer.prompt("MotherDuck database name", default=default_name).strip()
        if not md_name:
            error("MotherDuck catalog name is required.")
            raise typer.Exit(1)
        warehouse_value = f"md:{md_name}"

        if not os.environ.get("MOTHERDUCK_TOKEN"):
            console.print()
            warn("MOTHERDUCK_TOKEN is not set in your environment.")
            info("Get a token at https://app.motherduck.com/token")
            info("Then add to your shell profile: export MOTHERDUCK_TOKEN=<your_token>")
            info("`tycoon doctor` will flag this until you set it.")

        stack_warehouse_type = WarehouseType.motherduck.value
    else:  # local
        if path is not None:
            path_input = path.strip()
        elif no_prompt:
            path_input = "data/warehouse.duckdb"
        else:
            path_input = typer.prompt(
                "Path to your DuckDB file (will be created on first write if missing)",
                default="data/warehouse.duckdb",
            ).strip()
        if not path_input:
            error("Warehouse path is required.")
            raise typer.Exit(1)
        warehouse_value = path_input
        stack_warehouse_type = WarehouseType.duckdb.value

    db = raw.setdefault("database", {})
    old_warehouse = db.get("warehouse", "")
    db["warehouse"] = warehouse_value
    # If raw was pinned to the same old warehouse value, migrate it too.
    if db.get("raw", "") == old_warehouse and old_warehouse:
        db["raw"] = warehouse_value

    stack = raw.setdefault("stack", {})
    stack["warehouse"] = stack_warehouse_type

    _write_raw_tycoon_yml(yml_path, raw)
    success(f"Registered warehouse: {warehouse_value}")
    info(f"Updated {yml_path.name}.")


@app.command(name="rill")
def register_rill(
    source: Annotated[
        str,
        typer.Argument(help="Local path or GitHub URL of the Rill project to register."),
    ],
) -> None:
    """Attach an existing Rill project to the current tycoon.yml."""
    header("Register Rill project")

    yml_path = _require_tycoon_yml()
    raw = _load_raw_tycoon_yml(yml_path)

    existing_rill = raw.get("rill_dir")
    if existing_rill:
        warn(f"tycoon.yml already has rill_dir = {existing_rill!r}.")
        if not typer.confirm("Overwrite it?", default=False):
            info("Aborted; no changes made.")
            raise typer.Exit(0)

    default_clone = config.root.parent / f"{raw.get('name', config.root.name)}-rill"
    resolved = _resolve_path_or_url(source, default_clone)
    if resolved is None:
        raise typer.Exit(1)
    if not (resolved / "rill.yaml").exists():
        error(f"{resolved} does not contain a rill.yaml")
        raise typer.Exit(1)

    import os
    try:
        rel = os.path.relpath(resolved, config.root)
        raw["rill_dir"] = rel
    except ValueError:
        raw["rill_dir"] = str(resolved)

    stack = raw.setdefault("stack", {})
    stack["bi"] = BITool.rill.value
    stack["bi_managed"] = False

    _write_raw_tycoon_yml(yml_path, raw)
    success(f"Registered Rill project at {resolved}")
    info(f"Updated {yml_path.name}.")
