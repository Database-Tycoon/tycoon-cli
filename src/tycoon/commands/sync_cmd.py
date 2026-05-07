"""``tycoon data sync`` — snapshot cloud DuckDB into a local file.

Implements issue #12. CLI is opinionated about what's sensible for
local-first development:

- Default mode is ``replace`` (the snapshot is a baseline, not a replica).
- Destination defaults to the project's ``sync.to`` config when no
  ``--to`` is passed; otherwise the user must supply one.
- Sources can come from CLI (``--from`` repeatable) OR from
  ``tycoon.yml``'s ``sync.sources`` block. CLI fully overrides config.
- ``--schema`` and ``--tables`` apply uniformly across all CLI-provided
  sources; for per-source filters, use ``tycoon.yml``'s ``sync.sources``
  block (each spec carries its own ``schemas`` / ``tables`` globs).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from tycoon.config import config
from tycoon.project import SyncSourceSpec
from tycoon.sync import sync_to_local
from tycoon.utils.console import console, error, info, next_steps, success, warn


def sync_cmd(
    from_: Optional[list[str]] = typer.Option(
        None,
        "--from",
        help="Source URL — repeatable. md:<catalog>, /path/to/other.duckdb, etc.",
    ),
    to: Optional[Path] = typer.Option(
        None,
        "--to",
        help="Destination DuckDB file. Defaults to tycoon.yml's sync.to.",
    ),
    schema: Optional[str] = typer.Option(
        None,
        "--schema",
        help="Filter to one schema (applied to every --from source).",
    ),
    tables: Optional[str] = typer.Option(
        None,
        "--tables",
        help="Glob filter for table names within selected schemas (e.g. 'mart.*,dim_*').",
    ),
    mode: str = typer.Option(
        "replace",
        "--mode",
        help="replace (default) | append | skip-existing.",
    ),
) -> None:
    """Snapshot one or more cloud DuckDB sources into a local file.

    Designed for offline-dev loops where running every query against
    prod is slow / fragile / risky. Sync is one-way (cloud → local) and
    the local snapshot is intentionally allowed to go stale until you
    re-run it.
    """
    sync_cfg = config.project.sync if config.project else None

    # Resolve source specs.
    if from_:
        # CLI-supplied: build SyncSourceSpec per URL using the shared
        # --schema / --tables filters.
        schemas_glob = [schema] if schema else ["*"]
        # Allow comma-separated list for --tables, matching how users
        # typically write fnmatch sets in shell ("mart.*,dim_*").
        tables_glob = [t.strip() for t in tables.split(",")] if tables else ["*"]
        sources = [
            SyncSourceSpec(
                **{"from": url},
                schemas=schemas_glob,
                tables=tables_glob,
            )
            for url in from_
        ]
    elif sync_cfg and sync_cfg.sources:
        # Config-supplied: use as-is. CLI --schema / --tables flags are
        # ignored when running from config, since the config block already
        # carries per-source filters. Warn so this isn't surprising.
        if schema or tables:
            warn(
                "Ignoring --schema / --tables — running with sync.sources from "
                "tycoon.yml. Pass --from to override per-source filters."
            )
        sources = list(sync_cfg.sources)
    else:
        error(
            "Nothing to sync. Pass [bold]--from <url>[/bold] (repeatable) "
            "or add a [bold]sync:[/bold] block to tycoon.yml."
        )
        raise typer.Exit(1)

    # Resolve destination.
    if to is None:
        if sync_cfg and sync_cfg.to:
            to = config.root / sync_cfg.to
        else:
            error(
                "No destination. Pass [bold]--to <path>[/bold] or add "
                "[bold]sync.to[/bold] to tycoon.yml."
            )
            raise typer.Exit(1)

    # Mode validation up front so we don't half-attach before failing.
    valid_modes = {"replace", "append", "skip-existing"}
    if mode not in valid_modes:
        error(f"Unknown --mode {mode!r}. Expected one of: {', '.join(sorted(valid_modes))}.")
        raise typer.Exit(1)

    info(
        f"Syncing {len(sources)} source(s) → [bold]{to}[/bold] "
        f"([dim]mode: {mode}[/dim])"
    )

    try:
        result = sync_to_local(sources, to, mode=mode)
    except Exception as exc:
        error(f"Sync failed: {exc}")
        raise typer.Exit(1) from exc

    if not result.tables and not result.skipped:
        warn("No tables matched the filters. Check --schema / --tables / sync.sources.")
        return

    # Summary table — keep it terse but show enough to spot misalignment.
    for t in result.tables:
        console.print(
            f"  [cyan]{t.schema}.{t.table}[/cyan]  "
            f"[dim]{t.rows:,} rows from {t.source}[/dim]"
        )

    if result.skipped:
        warn(
            f"Skipped {len(result.skipped)} table(s) that couldn't be copied "
            f"(usually views referencing unattached catalogs):"
        )
        for s in result.skipped:
            console.print(
                f"  [yellow]{s.schema}.{s.table}[/yellow]  [dim]{s.reason}[/dim]"
            )

    success(
        f"Synced {result.total_rows:,} rows across {len(result.tables)} "
        f"table(s) to [bold]{to}[/bold]"
    )
    next_steps(
        ("tycoon data query \"SELECT ...\"", f"query the local snapshot ({to.name})"),
        ("tycoon data sync --mode skip-existing", "re-run later, only fill in new tables"),
    )


