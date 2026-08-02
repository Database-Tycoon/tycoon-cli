"""Loader and Pydantic models for the verified_sources.json manifest."""

from __future__ import annotations

import functools
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


class DltBackend(BaseModel):
    dlt_source: str | None = None
    dlt_init_name: str | None = None
    requires_dlt_init: bool = False


class SourceSpec(BaseModel):
    id: str
    provider: str
    backend: dict[str, Any]
    display_name: str
    category: str
    description: str
    resources: list[str] = []
    credentials: list[CredentialField] = []
    config_fields: list[ConfigField] = []
    default_schema: str = ""
    docs_url: str = ""

    def credential_defaults(self) -> dict[str, str]:
        """Return {key: "${ENV_VAR}"} for every credential field."""
        return {c.key: f"${{{c.env_var}}}" for c in self.credentials}

    def as_dlt(self) -> DltBackend:
        """Parse backend as DltBackend; raises if provider is not 'dlt'."""
        if self.provider != "dlt":
            raise ValueError(f"{self.id!r} is not a dlt source (provider={self.provider!r})")
        return DltBackend(**self.backend)


_MANIFEST_PATH = Path(__file__).parent / "data" / "verified_sources.json"


@functools.lru_cache()
def load_manifest() -> dict[str, SourceSpec]:
    """Load and validate verified_sources.json from the package data directory."""
    raw: dict[str, Any] = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    return {k: SourceSpec(id=k, **v) for k, v in raw.items()}
