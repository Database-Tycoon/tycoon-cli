"""Render `tycoon data query` results as a terminal table, CSV, JSON, or Markdown."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Sequence
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
    writer.writerows(rows)
    return buffer.getvalue()


def to_json(columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    """Rows as a JSON array with one object per row."""
    records = [dict(zip(columns, row, strict=True)) for row in rows]
    return json.dumps(records, indent=2, default=_json_default)


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
    lines.extend("| " + " | ".join(_markdown_cell(v) for v in row) + " |" for row in rows)
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


def print_table(console: Console, title: str, columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> bool:
    """Print rows as a Rich table, one block per record if the columns don't fit.

    Returns True when the per-record layout was used.
    """
    table = _wide_table(title, columns, rows)
    if not rows or fits_terminal(console, table):
        console.print(table)
        return False
    console.print(_record_table(title, columns, rows))
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
