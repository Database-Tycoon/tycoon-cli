"""tycoon data history — terminal view of dlt + dbt run history.

Reads ``.tycoon/metadata.duckdb`` and prints a unified feed of recent
runs or a drilldown into a single invocation / load.

Two invocation modes:

* ``tycoon data history``          — list recent runs across both tools
* ``tycoon data history show <id>`` — per-run detail (short id prefix OK)
"""

from __future__ import annotations

import datetime
from pathlib import Path

import duckdb
import typer
from rich.table import Table

from tycoon.config import config
from tycoon.observability import metadata_db_path
from tycoon.utils.console import console, error, header, info, warn


app = typer.Typer(
    help="Show dlt + dbt run history captured in .tycoon/metadata.duckdb.",
    invoke_without_command=True,
    no_args_is_help=False,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _metadata_or_exit() -> Path:
    """Return the metadata DB path, exiting with a hint if it doesn't exist."""
    meta = metadata_db_path(config.root)
    if not meta.exists():
        info(
            "No run history yet — metadata DB not found at "
            f"[dim]{meta.relative_to(config.root)}[/dim]. "
            "Run [bold]tycoon data sources run[/bold] or "
            "[bold]tycoon data transform run[/bold] to start capturing."
        )
        raise typer.Exit(0)
    return meta


def _fmt_ts(ts: datetime.datetime | None) -> str:
    if ts is None:
        return "—"
    if ts.tzinfo is not None:
        ts = ts.astimezone().replace(tzinfo=None)
    return ts.strftime("%Y-%m-%d %H:%M")


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(seconds, 60)
    return f"{int(minutes)}m{int(secs):02d}s"


def _short(id_value: str, n: int = 8) -> str:
    return id_value[:n] if id_value else "—"


# ---------------------------------------------------------------------------
# List view
# ---------------------------------------------------------------------------


def _load_dlt_rows(
    con: duckdb.DuckDBPyConnection,
    limit: int,
    source_schema: str | None = None,
) -> list[tuple]:
    """Return the most recent dlt runs with total rows loaded per load.

    If ``source_schema`` is given, only loads for that schema are returned.

    Tuple shape: (when_ts, tool, ref, full_id, ok, detail_str)
    """
    if source_schema:
        rows = con.execute(
            """
            SELECT
                r.inserted_at,
                r.source_schema,
                r.load_id,
                r.status,
                COALESCE(t.rows_total, 0) AS rows_total,
                COALESCE(t.table_count, 0) AS table_count
            FROM dlt_runs r
            LEFT JOIN (
                SELECT source_schema, load_id,
                       SUM(rows_loaded) AS rows_total,
                       COUNT(DISTINCT table_name) AS table_count
                FROM dlt_rows_by_table
                GROUP BY source_schema, load_id
            ) t USING (source_schema, load_id)
            WHERE r.source_schema = ?
            ORDER BY r.inserted_at DESC NULLS LAST
            LIMIT ?
            """,
            [source_schema, limit],
        ).fetchall()
    else:
        rows = con.execute(
            """
            SELECT
                r.inserted_at,
                r.source_schema,
                r.load_id,
                r.status,
                COALESCE(t.rows_total, 0) AS rows_total,
                COALESCE(t.table_count, 0) AS table_count
            FROM dlt_runs r
            LEFT JOIN (
                SELECT source_schema, load_id,
                       SUM(rows_loaded) AS rows_total,
                       COUNT(DISTINCT table_name) AS table_count
                FROM dlt_rows_by_table
                GROUP BY source_schema, load_id
            ) t USING (source_schema, load_id)
            ORDER BY r.inserted_at DESC NULLS LAST
            LIMIT ?
            """,
            [limit],
        ).fetchall()

    out: list[tuple] = []
    for inserted_at, schema, load_id, status, rows_total, table_count in rows:
        ok = status == 0
        detail = f"{schema} · {table_count} tables · {rows_total:,} rows"
        out.append((inserted_at, "dlt", f"{schema}/{_short(load_id)}", load_id, ok, detail))
    return out


def _load_dbt_rows(con: duckdb.DuckDBPyConnection, limit: int) -> list[tuple]:
    rows = con.execute(
        """
        SELECT
            started_at,
            command,
            invocation_id,
            success,
            elapsed_s,
            models_ok,
            models_error,
            tests_passed,
            tests_failed
        FROM dbt_runs
        ORDER BY started_at DESC NULLS LAST
        LIMIT ?
        """,
        [limit],
    ).fetchall()

    out: list[tuple] = []
    for (
        started_at,
        command,
        invocation_id,
        success,
        elapsed_s,
        models_ok,
        models_error,
        tests_passed,
        tests_failed,
    ) in rows:
        detail_parts: list[str] = [f"{_fmt_duration(elapsed_s)}"]
        if models_ok or models_error:
            detail_parts.append(f"{models_ok} ok / {models_error} err")
        if tests_passed or tests_failed:
            detail_parts.append(f"{tests_passed} pass / {tests_failed} fail")
        detail = " · ".join(detail_parts)
        ref = f"{command} ({_short(invocation_id)})" if command else _short(invocation_id)
        out.append((started_at, "dbt", ref, invocation_id, bool(success), detail))
    return out


def _render_history_table(combined: list[tuple]) -> Table:
    table = Table(show_lines=False)
    table.add_column("When", style="dim", no_wrap=True)
    table.add_column("Tool", style="bold")
    table.add_column("Ref", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    for when_ts, tool, ref, _full_id, ok, detail in combined:
        status_str = "[green]✓[/green]" if ok else "[red]✗[/red]"
        tool_style = "[bold cyan]dlt[/bold cyan]" if tool == "dlt" else "[bold magenta]dbt[/bold magenta]"
        table.add_row(_fmt_ts(when_ts), tool_style, ref, status_str, detail)

    return table


def _resolve_source_schema(source: str) -> str:
    """Translate a source name into its schema.

    If ``source`` matches a name in ``tycoon.yml``'s sources map, return its
    ``schema_name``. Otherwise treat it as a literal schema name. This lets
    users say ``--source pokeapi`` (config name) or ``--source raw_pokeapi``
    (schema literal) interchangeably.
    """
    try:
        src = config.sources.get(source)
        if src is not None:
            return src.schema_name
    except Exception:
        pass
    return source


def _list_history(tool: str, limit: int, source: str | None = None) -> None:
    meta = _metadata_or_exit()

    source_schema = _resolve_source_schema(source) if source else None

    con = duckdb.connect(str(meta), read_only=True)
    try:
        combined: list[tuple] = []
        if tool in ("all", "dlt"):
            combined.extend(_load_dlt_rows(con, limit, source_schema=source_schema))
        # dbt runs aren't source-scoped (a build touches all models), so when
        # the user asks for a specific source we hide dbt entirely rather
        # than polluting the view with unfiltered invocations.
        if tool in ("all", "dbt") and source_schema is None:
            combined.extend(_load_dbt_rows(con, limit))
    finally:
        con.close()

    if not combined:
        if source_schema:
            info(
                f"No dlt runs captured for source schema [bold]{source_schema}[/bold]."
            )
        else:
            info("No runs captured yet for the selected tool(s).")
        return

    combined.sort(
        key=lambda r: r[0] or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc),
        reverse=True,
    )
    combined = combined[:limit]

    title = "Run History"
    if source_schema:
        title += f" — {source_schema}"
    header(title)
    console.print(_render_history_table(combined))
    console.print()
    info("Drill in with [bold]tycoon data history show <id>[/bold] (short prefix OK).")


# ---------------------------------------------------------------------------
# Show (drilldown) view
# ---------------------------------------------------------------------------


def _resolve_id(
    con: duckdb.DuckDBPyConnection, id_prefix: str
) -> tuple[str, str] | None:
    """Resolve a short-prefix id to ('dlt', load_id) or ('dbt', invocation_id)."""
    dlt_matches = con.execute(
        "SELECT source_schema, load_id FROM dlt_runs WHERE load_id LIKE ? LIMIT 2",
        [f"{id_prefix}%"],
    ).fetchall()
    dbt_matches = con.execute(
        "SELECT invocation_id FROM dbt_runs WHERE invocation_id LIKE ? LIMIT 2",
        [f"{id_prefix}%"],
    ).fetchall()

    total = len(dlt_matches) + len(dbt_matches)
    if total == 0:
        return None
    if total > 1:
        samples: list[str] = [f"dlt/{m[1]}" for m in dlt_matches[:2]]
        samples.extend(f"dbt/{m[0]}" for m in dbt_matches[:2])
        warn(f"Prefix '{id_prefix}' is ambiguous — matches: {', '.join(samples)}")
        return None

    if dlt_matches:
        _, load_id = dlt_matches[0]
        return "dlt", load_id
    invocation_id = dbt_matches[0][0]
    return "dbt", invocation_id


def _fmt_bytes(n: int | None) -> str:
    if n is None:
        return "—"
    units = ("B", "KB", "MB", "GB", "TB")
    size = float(n)
    idx = 0
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024
        idx += 1
    if idx == 0:
        return f"{int(size)} {units[idx]}"
    return f"{size:,.1f} {units[idx]}"


def _show_dlt_run(con: duckdb.DuckDBPyConnection, load_id: str) -> None:
    run = con.execute(
        """
        SELECT source_schema, status, inserted_at, schema_version_hash
        FROM dlt_runs WHERE load_id = ?
        """,
        [load_id],
    ).fetchone()
    if run is None:
        error(f"No dlt load found with id '{load_id}'.")
        raise typer.Exit(1)
    schema, status, inserted_at, svh = run

    header(f"dlt load: {load_id}")
    console.print(f"  [bold]Source schema:[/bold] {schema}")
    console.print(f"  [bold]Status:[/bold] {'[green]success[/green]' if status == 0 else f'[red]error ({status})[/red]'}")
    console.print(f"  [bold]Loaded at:[/bold] {_fmt_ts(inserted_at)}")
    if svh:
        console.print(f"  [bold]Schema version:[/bold] {svh}")

    # Trace enrichment (v0.1.3): the load_id maps back to a transaction_id
    # via dlt_trace_jobs. When present, surface run duration + bytes.
    trace_row = con.execute(
        """
        SELECT r.transaction_id, r.pipeline_name, r.duration_s, r.success,
               (SELECT SUM(file_size_bytes) FROM dlt_trace_jobs j
                WHERE j.transaction_id = r.transaction_id) AS total_bytes
        FROM dlt_trace_runs r
        WHERE r.transaction_id IN (
            SELECT DISTINCT transaction_id FROM dlt_trace_jobs WHERE load_id = ?
        )
        LIMIT 1
        """,
        [load_id],
    ).fetchone()
    if trace_row is not None:
        txn_id, pipeline_name, duration_s, tr_success, total_bytes = trace_row
        console.print(f"  [bold]Pipeline:[/bold] {pipeline_name or '—'}")
        console.print(f"  [bold]Duration:[/bold] {_fmt_duration(duration_s)}")
        console.print(f"  [bold]Bytes written:[/bold] {_fmt_bytes(total_bytes)}")
        if not tr_success:
            console.print("  [bold]Trace:[/bold] [red]contained step exceptions[/red]")

        steps = con.execute(
            """
            SELECT step, duration_s, step_exception
            FROM dlt_trace_steps
            WHERE transaction_id = ?
            ORDER BY started_at
            """,
            [txn_id],
        ).fetchall()
        if steps:
            steps_table = Table(title="Steps", show_lines=False)
            steps_table.add_column("Step", style="cyan")
            steps_table.add_column("Duration", justify="right")
            steps_table.add_column("Status")
            for step_name, dur_s, exc in steps:
                status_str = "[green]ok[/green]" if not exc else "[red]error[/red]"
                steps_table.add_row(step_name, _fmt_duration(dur_s), status_str)
            console.print(steps_table)

    tables = con.execute(
        """
        SELECT table_name, rows_loaded
        FROM dlt_rows_by_table
        WHERE source_schema = ? AND load_id = ?
        ORDER BY table_name
        """,
        [schema, load_id],
    ).fetchall()

    if not tables:
        console.print("\n[dim]No per-table row counts captured for this load.[/dim]")
        return

    # Join per-table row counts with trace job bytes (if available).
    job_bytes = {
        row[0]: row[1]
        for row in con.execute(
            """
            SELECT table_name, SUM(file_size_bytes)
            FROM dlt_trace_jobs
            WHERE load_id = ?
            GROUP BY table_name
            """,
            [load_id],
        ).fetchall()
    }

    table = Table(title="Tables", show_lines=False)
    table.add_column("Table", style="cyan")
    table.add_column("Rows", justify="right")
    if job_bytes:
        table.add_column("Bytes", justify="right")

    total_rows = 0
    total_bytes = 0
    for name, rows_loaded in tables:
        row_values = [name, f"{rows_loaded:,}"]
        if job_bytes:
            b = job_bytes.get(name)
            row_values.append(_fmt_bytes(b))
            total_bytes += b or 0
        table.add_row(*row_values)
        total_rows += rows_loaded

    totals = ["[bold]Total[/bold]", f"[bold]{total_rows:,}[/bold]"]
    if job_bytes:
        totals.append(f"[bold]{_fmt_bytes(total_bytes)}[/bold]")
    table.add_row(*totals)
    console.print(table)


def _show_dbt_run(con: duckdb.DuckDBPyConnection, invocation_id: str) -> None:
    run = con.execute(
        """
        SELECT command, started_at, elapsed_s, success,
               models_ok, models_error, tests_passed, tests_failed,
               dbt_version, target_name
        FROM dbt_runs WHERE invocation_id = ?
        """,
        [invocation_id],
    ).fetchone()
    if run is None:
        error(f"No dbt invocation found with id '{invocation_id}'.")
        raise typer.Exit(1)
    (
        command,
        started_at,
        elapsed_s,
        success,
        models_ok,
        models_error,
        tests_passed,
        tests_failed,
        dbt_version,
        target_name,
    ) = run

    header(f"dbt {command or 'invocation'}: {invocation_id}")
    status_str = "[green]success[/green]" if success else "[red]failed[/red]"
    console.print(f"  [bold]Status:[/bold] {status_str}")
    console.print(f"  [bold]Started:[/bold] {_fmt_ts(started_at)}")
    console.print(f"  [bold]Elapsed:[/bold] {_fmt_duration(elapsed_s)}")
    if target_name:
        console.print(f"  [bold]Target:[/bold] {target_name}")
    if dbt_version:
        console.print(f"  [bold]dbt version:[/bold] {dbt_version}")
    console.print(
        f"  [bold]Models:[/bold] {models_ok} ok / {models_error} err   "
        f"[bold]Tests:[/bold] {tests_passed} pass / {tests_failed} fail"
    )

    nodes = con.execute(
        """
        SELECT node_name, resource_type, status,
               execution_time_s, rows_affected, message
        FROM dbt_nodes
        WHERE invocation_id = ?
        ORDER BY execution_time_s DESC NULLS LAST, node_name
        """,
        [invocation_id],
    ).fetchall()

    if nodes:
        table = Table(title="Nodes", show_lines=False)
        table.add_column("Node", style="cyan", overflow="fold")
        table.add_column("Type", style="dim")
        table.add_column("Status")
        table.add_column("Duration", justify="right")
        table.add_column("Rows", justify="right")
        for name, rtype, status, exec_s, rows, _msg in nodes:
            ok = status in ("success", "pass")
            status_str = f"[green]{status}[/green]" if ok else f"[red]{status}[/red]"
            rows_str = f"{rows:,}" if rows is not None else "—"
            table.add_row(name, rtype or "—", status_str, _fmt_duration(exec_s), rows_str)
        console.print(table)
    else:
        console.print("\n[dim]No node-level detail captured.[/dim]")

    # Schema-diff enrichment (v0.1.3): when a manifest snapshot recorded
    # changes vs. the previous run, surface them below the nodes table.
    changes = con.execute(
        """
        SELECT change_type, unique_id, column_name, old_value, new_value
        FROM dbt_schema_changes
        WHERE invocation_id = ?
        ORDER BY change_type, unique_id, column_name
        """,
        [invocation_id],
    ).fetchall()
    if changes:
        diff_table = Table(title="Schema changes vs. previous run", show_lines=False)
        diff_table.add_column("Change", style="yellow")
        diff_table.add_column("Node", style="cyan", overflow="fold")
        diff_table.add_column("Column", style="dim")
        diff_table.add_column("Old → New")
        for change_type, unique_id, column_name, old_value, new_value in changes:
            old_disp = old_value if old_value is not None else "—"
            new_disp = new_value if new_value is not None else "—"
            diff_table.add_row(
                change_type,
                unique_id,
                column_name or "—",
                f"{old_disp} → {new_disp}",
            )
        console.print(diff_table)


def _show_run(id_prefix: str) -> None:
    meta = _metadata_or_exit()
    con = duckdb.connect(str(meta), read_only=True)
    try:
        resolved = _resolve_id(con, id_prefix)
        if resolved is None:
            error(f"No run matches prefix '{id_prefix}'. Try [bold]tycoon data history[/bold] to list.")
            raise typer.Exit(1)
        tool, full_id = resolved
        if tool == "dlt":
            _show_dlt_run(con, full_id)
        else:
            _show_dbt_run(con, full_id)
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Typer wiring
# ---------------------------------------------------------------------------


@app.callback()
def history_default(
    ctx: typer.Context,
    tool: str = typer.Option(
        "all", "--tool", "-t", help="Filter by tool: all, dlt, or dbt."
    ),
    limit: int = typer.Option(
        20, "--limit", "-n", help="Max rows to display (default 20)."
    ),
    source: str = typer.Option(
        None,
        "--source",
        "-s",
        help=(
            "Filter dlt runs to a specific source. Accepts either the "
            "config name from tycoon.yml (e.g. 'pokeapi') or the raw "
            "schema literal (e.g. 'raw_pokeapi'). dbt runs are hidden "
            "when this flag is set since they aren't source-scoped."
        ),
    ),
) -> None:
    """List the most recent dlt + dbt runs captured in the metadata DB."""
    if ctx.invoked_subcommand is not None:
        return
    if tool not in ("all", "dlt", "dbt"):
        error(f"Invalid --tool '{tool}'. Use: all, dlt, dbt.")
        raise typer.Exit(1)
    _list_history(tool, limit, source=source)


@app.command("show")
def history_show(
    run_id: str = typer.Argument(
        ..., help="Invocation id (dbt) or load id (dlt). Short prefix OK."
    ),
) -> None:
    """Show per-node / per-table detail for a specific run."""
    _show_run(run_id)
