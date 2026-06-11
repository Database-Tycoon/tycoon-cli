"""Pipeline-completion notifications (#46) — Slack / generic webhook.

The simplest production-grade gap tycoon had: an unattended `tycoon data
run-all` printed Rich output and exited, so nobody knew a scheduled run
succeeded or failed without checking the terminal. This closes it with a small,
local-first notification surface — POST a JSON payload to a webhook on
completion. No daemon, no cloud dependency.

The webhook URL is read from ``$TYCOON_NOTIFY_WEBHOOK_URL`` so the secret never
lands in ``tycoon.yml``; the optional ``notify:`` block holds only non-secret
prefs (which severities to emit, a source label). When the URL points at a
Slack incoming webhook we send Slack's coloured-attachment shape; otherwise a
plain JSON envelope any webhook can consume.

This module is pure transport + payload construction so it's unit-testable with
the HTTP call mocked.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

WEBHOOK_ENV_VAR = "TYCOON_NOTIFY_WEBHOOK_URL"

# Three severities, matching the model in #46.
SEVERITIES: tuple[str, ...] = ("success", "error", "info")

# Slack attachment colours per severity (also surfaced in the generic payload).
_COLORS: dict[str, str] = {
    "success": "#36a64f",  # green
    "error": "#d00000",    # red
    "info": "#2196f3",     # blue
}


def webhook_url(url: str | None = None) -> str | None:
    """Resolve the webhook URL: explicit arg wins, else the env var, else None."""
    return url or os.environ.get(WEBHOOK_ENV_VAR) or None


def is_slack_url(url: str) -> bool:
    """True for Slack incoming-webhook URLs (drives the payload shape)."""
    return "hooks.slack.com" in url


def build_payload(
    severity: str,
    message: str,
    fields: dict[str, str] | None = None,
    *,
    label: str | None = None,
    slack: bool = False,
) -> dict[str, Any]:
    """Build the JSON body for ``severity``/``message``.

    Slack mode emits a single coloured attachment with the fields rendered as
    short key/value pairs; generic mode emits a flat envelope that any webhook
    consumer can parse.
    """
    fields = fields or {}
    if slack:
        attachment: dict[str, Any] = {
            "color": _COLORS.get(severity, _COLORS["info"]),
            "title": f"tycoon: {severity}",
            "text": message,
            "fields": [
                {"title": k, "value": v, "short": True} for k, v in fields.items()
            ],
        }
        if label:
            attachment["footer"] = label
        return {"attachments": [attachment]}

    payload: dict[str, Any] = {
        "source": "tycoon",
        "severity": severity,
        "message": message,
        "color": _COLORS.get(severity, _COLORS["info"]),
        "fields": fields,
    }
    if label:
        payload["label"] = label
    return payload


def send(
    severity: str,
    message: str,
    fields: dict[str, str] | None = None,
    *,
    label: str | None = None,
    url: str | None = None,
    timeout: float = 10.0,
) -> bool:
    """POST a notification. Returns True on a 2xx response.

    Best-effort by contract: returns False (never raises) when no webhook is
    configured or the request fails, so a notification problem can't take down
    the pipeline that triggered it. Callers that care about the difference
    should check :func:`webhook_url` first.
    """
    resolved = webhook_url(url)
    if not resolved:
        return False

    payload = build_payload(
        severity, message, fields, label=label, slack=is_slack_url(resolved)
    )
    try:
        response = httpx.post(resolved, json=payload, timeout=timeout)
    except Exception:
        # Best-effort by contract — swallow anything (httpx.HTTPError, plus
        # InvalidURL / ValueError from a malformed webhook) so a notification
        # problem can never crash the calling pipeline.
        return False
    return response.is_success
