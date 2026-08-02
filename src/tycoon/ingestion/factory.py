"""SourceFactory — spec-driven config collection for dlt sources."""

from __future__ import annotations

from typing import Any

import typer

from tycoon.ingestion.manifest import SourceSpec
from tycoon.utils.console import console, error, info


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

        if not self.spec.credentials and not self.spec.config_fields and not no_prompt:
            console.print("  [dim]No fields to configure — setup is handled by dlt init.[/dim]")

        if self.spec.credentials and not no_prompt:
            console.print("[bold]Credentials[/bold]")
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

        if self.spec.config_fields and self.spec.credentials and not no_prompt:
            console.print("[bold]Configuration[/bold]")

        if no_prompt:
            missing: list[str] = []
            for field in self.spec.config_fields:
                if field.key in flags:
                    cfg[field.key] = flags[field.key]
                elif field.required:
                    missing.append(field.key)
                elif field.default is not None and field.default != "":
                    cfg[field.key] = field.default
            if missing:
                for key in missing:
                    error(
                        f"--config {key}=<value> is required for "
                        f"[bold]{self.spec.id}[/bold] under --no-prompt."
                    )
                raise typer.Exit(1)
        else:
            for field in self.spec.config_fields:
                if field.hint:
                    console.print(f"  [dim]{field.hint}[/dim]")
                label = f"  {field.label}" + ("" if field.required else " (optional)")
                if field.required:
                    value = typer.prompt(label)
                    cfg[field.key] = value
                else:
                    value = typer.prompt(
                        label,
                        default=field.default if field.default is not None else "",
                        show_default=bool(field.default),
                    )
                    if value:
                        cfg[field.key] = value

        return cfg
