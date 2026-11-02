"""Render `tycoon data query` results as a terminal table, CSV, JSON, or Markdown."""

from __future__ import annotations

import csv
import io
import json
import math
from collections.abc import Sequence
from datetime import timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any

import typer
from rich.console import Console
from rich.measure import Measurement
from rich.table import Table


class OutputFormat(StrEnum):
    table = "table"
    csv = "csv"
    json = "json"
    markdown = "markdown"


def iso_duration(value: timedelta) -> str:
    """ISO 8601 duration text for a DuckDB INTERVAL, such as P1DT2H30M."""
    if value < timedelta(0):
        return "-" + iso_duration(-value)
    hours, remainder = divmod(value.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = [f"{value.days}D" if value.days else ""]
    time_parts = [
        f"{hours}H" if hours else "",
        f"{minutes}M" if minutes else "",
        f"{seconds + value.microseconds / 1_000_000:g}S" if seconds or value.microseconds else "",
    ]
    if any(time_parts):
        parts.append("T" + "".join(time_parts))
    return "P" + "".join(parts) if any(parts) else "PT0S"


def _machine_value(value: Any, nan_as_null: bool = False) -> Any:
    """A value the way csv, json and markdown output show it.

    Python's repr of bytes and timedelta means nothing to a reader outside
    Python, so BLOB becomes hex and INTERVAL an ISO 8601 duration. JSON has
    no spelling for NaN or infinity, so those become null there; CSV keeps
    them, since CSV readers accept nan and inf as doubles.
    """
    if nan_as_null and isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, timedelta):
        return iso_duration(value)
    if isinstance(value, list):
        return [_machine_value(item, nan_as_null) for item in value]
    if isinstance(value, dict):
        return {key: _machine_value(item, nan_as_null) for key, item in value.items()}
    return value


def _machine_rows(rows: Sequence[Sequence[Any]], nan_as_null: bool = False) -> list[list[Any]]:
    return [[_machine_value(value, nan_as_null) for value in row] for row in rows]


def _json_default(value: Any) -> Any:
    # DuckDB returns DECIMAL columns as Decimal, which json can't encode.
    # A number keeps the output usable by scripts, the same as DuckDB's own
    # JSON output mode.
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


def to_csv(columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    """Rows as CSV with a header line. NULL becomes an empty field."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(_machine_rows(rows))
    return buffer.getvalue()


def to_json(columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    """Rows as a JSON array with one object per row."""
    records = [dict(zip(columns, row, strict=True)) for row in _machine_rows(rows, nan_as_null=True)]
    return json.dumps(records, indent=2, default=_json_default, allow_nan=False)


def _markdown_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", r"\|").replace("\r\n", " ").replace("\n", " ")


def to_markdown(columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    """Rows as a GitHub-flavored Markdown table."""
    lines = [
        "| " + " | ".join(_markdown_cell(c) for c in columns) + " |",
        "|" + "|".join(" --- " for _ in columns) + "|",
    ]
    lines.extend("| " + " | ".join(_markdown_cell(v) for v in row) + " |" for row in _machine_rows(rows))
    return "\n".join(lines) + "\n"


def _wide_table(title: str, columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> Table:
    table = Table(title=title, show_lines=True)
    for col in columns:
        table.add_column(col, style="cyan")
    for row in rows:
        table.add_row(*(str(v) for v in row))
    return table


def _record_table(title: str, columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> Table:
    table = Table(title=title, show_header=False)
    table.add_column("column", style="cyan", no_wrap=True)
    table.add_column("value", overflow="fold")
    for index, row in enumerate(rows, start=1):
        table.add_row(f"[bold magenta]record {index}[/]", "")
        for col, value in zip(columns, row, strict=True):
            table.add_row(col, str(value))
        if index < len(rows):
            table.add_section()
    return table


def fits_terminal(console: Console, table: Table) -> bool:
    """True if every column can show its header and longest word unbroken."""
    # Measurement.get clamps to the options' max_width, so measure against an
    # unbounded width to learn what the table actually needs.
    unbounded = console.options.update(max_width=1_000_000)
    return Measurement.get(console, unbounded, table).minimum <= console.options.max_width


def _column_list(title: str, columns: Sequence[str]) -> Table:
    table = Table(title=title, show_header=False)
    table.add_column("column", style="cyan", overflow="fold")
    table.add_row("[bold magenta]0 rows; columns:[/]")
    for col in columns:
        table.add_row(col)
    return table


def print_table(console: Console, title: str, columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> bool:
    """Print rows as a Rich table, one block per record if the columns don't fit.

    An empty result that is too wide lists the column names instead, since a
    squashed header row would hide the one thing it has to show.

    Returns True when the per-record or column-list layout was used.
    """
    table = _wide_table(title, columns, rows)
    if fits_terminal(console, table):
        console.print(table)
        return False
    console.print(_column_list(title, columns) if not rows else _record_table(title, columns, rows))
    return True


def emit_rows(fmt: OutputFormat, columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> None:
    """Write rows to stdout in a machine-readable format, with nothing else around them."""
    renderers = {
        OutputFormat.csv: to_csv,
        OutputFormat.json: to_json,
        OutputFormat.markdown: to_markdown,
    }
    output = renderers[fmt](columns, rows)
    typer.echo(output, nl=not output.endswith("\n"))
