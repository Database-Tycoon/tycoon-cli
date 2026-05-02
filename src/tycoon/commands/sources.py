"""tycoon sources — manage registered data sources."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import click
import typer
from rich.table import Table

from tycoon.config import config
from tycoon.ingestion.catalog import CATALOG, CatalogEntry
from tycoon.project import SourceConfig, load_project, save_project
from tycoon.utils.console import ai_hint, console, error, header, info, next_steps, success, warn

app = typer.Typer(help="Manage registered data sources.")

catalog_app = typer.Typer(
    help="Browse and install source integrations.",
    invoke_without_command=True,
    no_args_is_help=False,
)

list_app = typer.Typer(
    help="List registered sources and inspect their config.",
    invoke_without_command=True,
    no_args_is_help=False,
)

app.add_typer(catalog_app, name="catalog")
app.add_typer(list_app, name="list")


def _require_project() -> None:
    """Abort if no tycoon.yml exists."""
    if not config.has_project_file:
        error("No tycoon.yml found. Run [bold]tycoon init[/bold] first.")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# catalog sub-group
# ---------------------------------------------------------------------------


def _show_catalog() -> None:
    """Print the source catalog table."""
    table = Table(title="Source Catalog", show_lines=True)
    table.add_column("Type", style="cyan bold")
    table.add_column("Category", style="dim")
    table.add_column("Description", style="white")
    table.add_column("Tables", style="green")

    for entry in CATALOG.values():
        table.add_row(
            entry.id,
            entry.category,
            entry.description,
            ", ".join(entry.resources),
        )

    console.print(table)
    console.print()
    info("Add a source with: [bold]tycoon data sources add <type>[/bold]  (e.g. tycoon data sources add github)")


@catalog_app.callback()
def catalog_default(ctx: typer.Context) -> None:
    """Browse available source integrations."""
    if ctx.invoked_subcommand is None:
        _show_catalog()


# ---------------------------------------------------------------------------
# list sub-group
# ---------------------------------------------------------------------------


def _list_sources() -> None:
    """Print registered sources table."""
    _require_project()

    sources = config.sources
    if not sources:
        info("No sources registered yet.")
        info("Browse available sources with [bold]tycoon data sources catalog[/bold]")
        return

    table = Table(title="Registered Sources", show_lines=True)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="bold")
    table.add_column("Schema", style="green")

    for name, src in sources.items():
        table.add_row(name, src.type, src.schema_name)

    console.print(table)


@list_app.callback()
def list_default(ctx: typer.Context) -> None:
    """List all registered data sources."""
    if ctx.invoked_subcommand is None:
        _list_sources()


@list_app.command("show")
def show_source(
    name: str = typer.Argument(help="Name of the source to show"),
) -> None:
    """Show detailed configuration for a specific source."""
    _require_project()

    sources = config.sources
    if name not in sources:
        error(f"Source [bold]{name}[/bold] not found.")
        info(f"Available sources: {', '.join(sources.keys()) if sources else '(none)'}")
        raise typer.Exit(1)

    src = sources[name]
    header(f"Source: {name}")
    console.print(f"  [bold]Type:[/bold]   {src.type}")
    console.print(f"  [bold]Schema:[/bold] {src.schema_name}")

    if src.tables:
        console.print(f"  [bold]Tables:[/bold] {', '.join(src.tables)}")
    else:
        console.print("  [bold]Tables:[/bold] (all)")

    if src.dbt_package:
        console.print(f"  [bold]dbt package:[/bold] {src.dbt_package}")

    if src.config:
        console.print("  [bold]Config:[/bold]")
        for key, value in src.config.items():
            display = "***" if any(s in key.lower() for s in ("token", "key", "secret", "password")) else value
            console.print(f"    {key}: {display}")


# ---------------------------------------------------------------------------
# add / remove
# ---------------------------------------------------------------------------


def _prompt_catalog_config(entry: CatalogEntry) -> dict[str, Any]:
    """Prompt for credentials and config fields using catalog metadata."""
    cfg: dict[str, Any] = {}

    if entry.credentials:
        console.print("\n  [bold]Credentials[/bold]")
        for cred in entry.credentials:
            console.print(f"  [dim]{cred.hint}[/dim]")
            default = f"${{{cred.env_var}}}"
            value = typer.prompt(
                f"  {cred.label}",
                default=default,
                hide_input=cred.secret,
                show_default=True,
            )
            cfg[cred.key] = value

    if entry.config_fields:
        console.print("\n  [bold]Configuration[/bold]")
        for field in entry.config_fields:
            if field.hint:
                console.print(f"  [dim]{field.hint}[/dim]")
            if field.required:
                value = typer.prompt(f"  {field.label}")
            else:
                value = typer.prompt(
                    f"  {field.label}",
                    default=field.default or "",
                    show_default=bool(field.default),
                )
            if value:
                cfg[field.key] = value

    return cfg


def _prompt_rest_api_config() -> dict[str, Any]:
    """Prompt for rest_api source configuration."""
    base_url = typer.prompt("Base URL for the REST API")
    return {"base_url": base_url}


def _prompt_sql_database_config() -> dict[str, Any]:
    """Prompt for sql_database source configuration."""
    info("Hint: use ${ENV_VAR} syntax for secrets (e.g. ${DATABASE_URL})")
    connection_string = typer.prompt("Connection string")
    return {"connection_string": connection_string}


def _prompt_filesystem_config() -> dict[str, Any]:
    """Prompt for filesystem source configuration."""
    path = typer.prompt("Path or URL to the data files")
    return {"path": path}


def _prompt_generic_config() -> dict[str, Any]:
    """Prompt for generic key=value configuration pairs."""
    info("Enter config as key=value pairs. Empty line to finish.")
    cfg: dict[str, Any] = {}
    while True:
        pair = typer.prompt("  key=value (or empty to finish)", default="", show_default=False)
        if not pair:
            break
        if "=" not in pair:
            warn(f"Skipping invalid entry (no '=' found): {pair}")
            continue
        key, value = pair.split("=", 1)
        cfg[key.strip()] = value.strip()
    return cfg


_CONFIG_PROMPTERS = {
    "rest_api": _prompt_rest_api_config,
    "sql_database": _prompt_sql_database_config,
    "filesystem": _prompt_filesystem_config,
}


def _derive_source_identity(source_type: str, cfg: dict) -> tuple[str, str]:
    """Auto-derive (source_name, schema_name) from config for sources that support it."""
    from urllib.parse import urlparse

    if source_type == "rest_api":
        base_url = cfg.get("base_url", "")
        try:
            host = urlparse(base_url).hostname or ""
            parts = host.split(".")
            slug = parts[-2] if len(parts) >= 2 else parts[0]
        except Exception:
            slug = "api"
        slug = slug.replace("-", "_")
        return slug, f"raw_{slug}"

    if source_type == "filesystem":
        path = cfg.get("path", "")
        slug = Path(path).expanduser().stem or Path(path).expanduser().name or "files"
        slug = slug.replace("-", "_")
        return slug, f"raw_{slug}"

    raise ValueError(f"No auto-naming for {source_type}")


# Sources that get their name/schema derived from config rather than prompted.
_AUTO_NAMED_SOURCES: set[str] = {"rest_api", "filesystem"}


@app.command("add")
def add_source(
    source_type: Optional[str] = typer.Argument(None, help="Source type — run 'tycoon data sources catalog' to see all options"),
) -> None:
    """Interactively register a new data source."""
    _require_project()

    if not source_type:
        _show_catalog()
        source_type = typer.prompt("Enter a source type from the catalog")

    catalog_entry = CATALOG.get(source_type)

    if catalog_entry:
        header(f"Add source: {catalog_entry.display_name}")
        console.print(f"  [dim]{catalog_entry.description}[/dim]")
        console.print(f"  Tables: [green]{', '.join(catalog_entry.resources)}[/green]\n")
    else:
        header(f"Add source: {source_type}")

    if catalog_entry and source_type in _AUTO_NAMED_SOURCES:
        source_config = _prompt_catalog_config(catalog_entry)
        source_name, schema_name = _derive_source_identity(source_type, source_config)
        info(f"Source name: [bold]{source_name}[/bold]")
        info(f"Schema:      [bold]{schema_name}[/bold]")
    else:
        default_name = f"my-{source_type}" if catalog_entry else source_type
        source_name = typer.prompt("Source name", default=default_name)
        default_schema = catalog_entry.default_schema if catalog_entry else f"raw_{source_name.replace('-', '_')}"
        schema_name = typer.prompt("Schema name", default=default_schema)
        if catalog_entry:
            source_config = _prompt_catalog_config(catalog_entry)
        else:
            prompter = _CONFIG_PROMPTERS.get(source_type, _prompt_generic_config)
            source_config = prompter()

    new_source = SourceConfig(
        type=source_type,
        schema=schema_name,
        config=source_config,
    )

    project = load_project(config.root)
    assert project is not None  # guarded by _require_project

    if source_name in project.sources:
        overwrite = typer.confirm(
            f"Source '{source_name}' already exists. Overwrite?", default=False
        )
        if not overwrite:
            info("Cancelled.")
            raise typer.Exit(0)

    project.sources[source_name] = new_source
    save_project(project, config.root)
    config.reload()

    success(f"Source [bold]{source_name}[/bold] added to tycoon.yml")

    if catalog_entry:
        _maybe_install_catalog_source(source_type)
    else:
        _maybe_install_dlt_extra(source_type)

    next_steps(
        (f"tycoon data sources run {source_name}", "load data into DuckDB"),
        ("tycoon data sources list", "see all registered sources"),
    )


def _maybe_install_catalog_source(source_type: str) -> None:
    """Offer to download the dlt verified source if not already installed."""
    from tycoon.ingestion.source_manager import install_source, is_source_installed

    if is_source_installed(source_type):
        return

    install = typer.confirm(
        f"Source '{source_type}' hasn't been downloaded yet. Download it now via dlt init?",
        default=True,
    )
    if install:
        info(f"Running dlt init {source_type} ...")
        if install_source(source_type):
            success(f"Source '{source_type}' installed to ~/.tycoon/sources/")
        else:
            warn(
                f"Failed to install '{source_type}'. "
                f"You can retry with: tycoon data sources catalog install {source_type}"
            )
    else:
        info(f"Skipped. Install later with: tycoon data sources catalog install {source_type}")


def _maybe_install_dlt_extra(source_type: str) -> None:
    """Check if the dlt extra is available and offer to install if not."""
    from tycoon.ingestion.source_installer import (
        DLT_EXTRAS,
        install_dlt_extra,
        is_dlt_extra_available,
    )

    if source_type not in DLT_EXTRAS:
        return

    if is_dlt_extra_available(source_type):
        return

    install = typer.confirm(
        f"dlt[{source_type}] is not installed. Install it now?", default=True
    )
    if install:
        if install_dlt_extra(source_type):
            success(f"dlt[{source_type}] installed successfully.")
        else:
            warn(f"Failed to install dlt[{source_type}]. You can install it manually.")
    else:
        info(f"Skipped. Install later with: uv pip install 'dlt[{source_type}]'")


@app.command("remove")
def remove_source(
    name: str = typer.Argument(help="Name of the source to remove"),
) -> None:
    """Remove a registered data source."""
    _require_project()

    project = load_project(config.root)
    assert project is not None

    if name not in project.sources:
        error(f"Source [bold]{name}[/bold] not found.")
        info(f"Available sources: {', '.join(project.sources.keys()) if project.sources else '(none)'}")
        raise typer.Exit(1)

    typer.confirm(f"Remove source '{name}'?", abort=True)

    del project.sources[name]
    save_project(project, config.root)
    config.reload()

    success(f"Source [bold]{name}[/bold] removed from tycoon.yml")


# ---------------------------------------------------------------------------
# Ingestion commands
# ---------------------------------------------------------------------------

_MaxRecordsOption = typer.Option(
    None,
    "--max-records",
    "-n",
    help="Cap the total number of records fetched per resource (useful for testing).",
    show_default=False,
)


@app.command(name="run")
def run_source(
    source_name: Optional[str] = typer.Argument(None, help="Name of the registered source to ingest."),
    max_records: Optional[int] = _MaxRecordsOption,
) -> None:
    """Ingest data from a registered source by name."""
    from tycoon.ingestion.runner import run_source as _run_source

    _require_project()

    sources = config.sources
    if not source_name:
        if not sources:
            error("No sources registered. Run 'tycoon data sources add' first.")
            raise typer.Exit(1)
        source_name = typer.prompt(
            "Choose a source to ingest",
            type=click.Choice(list(sources.keys())),
            show_choices=True,
        )

    if source_name not in sources:
        error(f"Source '{source_name}' not found. Available: {', '.join(sources.keys()) or '(none)'}")
        raise typer.Exit(1)

    source_config = sources[source_name]
    header(f"Ingesting: {source_name}")
    info(f"Type: {source_config.type} | Schema: {source_config.schema_name}")
    if max_records is not None:
        info(f"Record cap: {max_records:,}")

    config.ensure_data_dir()

    try:
        _pipeline, load_info = _run_source(
            name=source_name,
            source_config=source_config,
            raw_db_path=config.raw_db,
            max_records=max_records,
        )
        success(f"{source_name} load complete. {load_info}")
        next_steps(
            ("tycoon data transform run", "run dbt models on the ingested data"),
            ("tycoon start --only rill", "open the Rill dashboard"),
        )
    except Exception as exc:
        from tycoon.ingestion.runner import IngestionError
        error(str(exc) if isinstance(exc, IngestionError) else f"{source_name} pipeline failed: {exc}")
        if not isinstance(exc, IngestionError):
            ai_hint(f"help me debug the {source_name} ingestion")
        raise typer.Exit(1) from exc


@app.command(name="run-all")
def run_all(
    max_records: Optional[int] = _MaxRecordsOption,
) -> None:
    """Run all registered source pipelines sequentially."""
    from tycoon.ingestion.runner import run_source as _run_source

    _require_project()

    sources = config.sources
    if not sources:
        error("No sources registered. Run 'tycoon data sources add' first.")
        raise typer.Exit(1)

    total = len(sources)
    header(f"Full Ingestion ({total} source{'s' if total != 1 else ''})")
    if max_records is not None:
        info(f"Record cap per resource: {max_records:,}")

    config.ensure_data_dir()

    for i, (name, source_config) in enumerate(sources.items(), 1):
        info(f"Step {i}/{total} — {name} ({source_config.type})...")
        try:
            _pipeline, load_info = _run_source(
                name=name,
                source_config=source_config,
                raw_db_path=config.raw_db,
                max_records=max_records,
            )
            success(f"{name} complete. {load_info}")
        except Exception as exc:
            error(f"{name} pipeline failed: {exc}")
            ai_hint(f"help me debug the {name} ingestion")
            raise typer.Exit(1) from exc

    success("All ingestion pipelines completed successfully.")
    next_steps(
        ("tycoon data transform run", "run dbt models on the ingested data"),
        ("tycoon start --only rill", "open the Rill dashboard"),
    )
