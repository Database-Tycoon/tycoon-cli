"""Loader and Pydantic models for the verified_sources.json manifest.

``load_manifest()`` is the single entry point: it reads the bundled
``data/verified_sources.json`` and returns a validated dict of
:class:`SourceSpec` objects keyed by source id.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class CredentialField(BaseModel):
    key: str
    env_var: str
    label: str
    secret: bool = True
    hint: str = ""


class ConfigField(BaseModel):
    key: str
    label: str
    required: bool = True
    hint: str = ""
    default: str | None = None


class SourceSpec(BaseModel):
    id: str
    display_name: str
    category: str
    description: str
    resources: list[str] = []
    credentials: list[CredentialField] = []
    config_fields: list[ConfigField] = []
    dlt_source: str | None = None
    dlt_init_name: str | None = None
    requires_dlt_init: bool = False
    default_schema: str = ""
    docs_url: str = ""

    def credential_defaults(self) -> dict[str, str]:
        """Return {key: "${ENV_VAR}"} for every credential field."""
        return {c.key: f"${{{c.env_var}}}" for c in self.credentials}


_MANIFEST_PATH = Path(__file__).parent / "data" / "verified_sources.json"


def load_manifest() -> dict[str, SourceSpec]:
    """Load and validate verified_sources.json from the package data directory."""
    raw: dict[str, Any] = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    return {k: SourceSpec(id=k, **v) for k, v in raw.items()}
