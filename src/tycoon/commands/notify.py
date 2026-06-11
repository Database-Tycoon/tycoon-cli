"""tycoon notify — send a pipeline notification to a webhook (#46)."""

from __future__ import annotations

import typer

from tycoon import notify as notify_mod
from tycoon.utils.console import error, success


def _parse_fields(pairs: list[str]) -> dict[str, str]:
    """Parse repeated ``--field key=value`` flags into a dict."""
    out: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            error(f"Invalid --field '{pair}' — expected key=value.")
            raise typer.Exit(2)
        key, value = pair.split("=", 1)
        key = key.strip()
        if not key:
            error(f"Invalid --field '{pair}' — key cannot be empty.")
            raise typer.Exit(2)
        out[key] = value.strip()
    return out


def notify_cmd(
    severity: str = typer.Argument(
        help="One of: success, error, info.",
    ),
    message: str = typer.Argument(help="Notification message body."),
    field: list[str] = typer.Option(
        [],
        "--field",
        "-f",
        help="Extra key=value pairs to include (repeatable), e.g. -f rows=1234.",
    ),
    label: str | None = typer.Option(
        None,
        "--label",
        help="Override the source label in the payload (defaults to notify.label in tycoon.yml).",
    ),
) -> None:
    """Send a one-off notification to the configured webhook.

    The webhook URL comes from ``$TYCOON_NOTIFY_WEBHOOK_URL``. Slack incoming
    webhooks get a coloured attachment; any other URL gets a generic JSON
    envelope. Useful standalone or as a recipe hook; ``tycoon data run-all
    --notify`` wires the same surface into pipeline runs.
    """
    if severity not in notify_mod.SEVERITIES:
        error(
            f"Unknown severity '{severity}'. Choose one of: "
            f"{', '.join(notify_mod.SEVERITIES)}."
        )
        raise typer.Exit(2)

    fields = _parse_fields(field)

    if notify_mod.webhook_url() is None:
        error(
            f"No webhook configured. Set ${notify_mod.WEBHOOK_ENV_VAR} to a "
            "Slack incoming webhook or any URL that accepts a JSON POST."
        )
        raise typer.Exit(1)

    # Fall back to the project's notify.label when --label isn't given.
    if label is None:
        from tycoon.config import config

        project = config.project
        if project is not None and project.notify is not None:
            label = project.notify.label

    if notify_mod.send(severity, message, fields, label=label):
        success("Notification sent.")
    else:
        error("Failed to send notification (check the webhook URL and connectivity).")
        raise typer.Exit(1)
