"""tycoon run — passthrough to any tool in the tycoon environment."""

from __future__ import annotations

import subprocess

import typer

from tycoon.utils.console import error


def run_cmd(
    ctx: typer.Context,
    tool: str = typer.Argument(help="Tool to invoke (e.g. dbt, dlt, rill)."),
) -> None:
    """Invoke any CLI tool in the tycoon environment and forward all arguments.

    All arguments after <tool> are passed through unchanged.

    Examples:

      tycoon run dbt run --select staging+

      tycoon run dlt pipeline nyc_dot_pipeline show

      tycoon run rill --help
    """
    cmd = [tool] + ctx.args
    try:
        result = subprocess.run(cmd)
        raise typer.Exit(result.returncode)
    except FileNotFoundError:
        error(f"'{tool}' not found on PATH — is it installed in this environment?")
        raise typer.Exit(1)
