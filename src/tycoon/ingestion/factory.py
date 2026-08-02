"""SourceFactory — spec-driven config collection for dlt sources.

All behaviour is driven by SourceSpec fields; there is no
``if source_type == "github"`` branching here.
"""

from __future__ import annotations

from typing import Any

import typer

from tycoon.ingestion.manifest import SourceSpec
from tycoon.utils.console import console, info


class SourceFactory:
    def __init__(self, spec: SourceSpec) -> None:
        self.spec = spec

    def collect_config(
        self,
        *,
        no_prompt: bool = False,
        flags: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Produce a flat config dict from spec-driven prompts or flags."""
        flags = flags or {}
        cfg: dict[str, Any] = {}

        for cred in self.spec.credentials:
            default = f"${{{cred.env_var}}}"
            if no_prompt:
                cfg[cred.key] = flags.get(cred.key, default)
            else:
                if cred.hint:
                    console.print(f"  [dim]{cred.hint}[/dim]")
                value = typer.prompt(
                    f"  {cred.label}",
                    default=default,
                    hide_input=cred.secret,
                    show_default=True,
                )
                cfg[cred.key] = value

        for field in self.spec.config_fields:
            if no_prompt:
                if field.key in flags:
                    cfg[field.key] = flags[field.key]
                elif field.required:
                    info(
                        f"--config {field.key}=<value> is required for "
                        f"[bold]{self.spec.id}[/bold] under --no-prompt."
                    )
                    raise SystemExit(1)
                elif field.default is not None and field.default != "":
                    cfg[field.key] = field.default
            else:
                if field.hint:
                    console.print(f"  [dim]{field.hint}[/dim]")
                if field.required:
                    value = typer.prompt(f"  {field.label}")
                    cfg[field.key] = value
                else:
                    value = typer.prompt(
                        f"  {field.label}",
                        default=field.default if field.default is not None else "",
                        show_default=bool(field.default),
                    )
                    if value:
                        cfg[field.key] = value

        return cfg
