"""Centralized dbt profile resolution for tycoon.

Resolution order matches dbt's own CLI (so `tycoon ... --profiles-dir
foo` and `dbt ... --profiles-dir foo` find the same file):

    1. CLI flag (``--profiles-dir`` / ``--profile`` / ``--target``)
    2. ``tycoon.yml`` overrides (``dbt_profiles_dir`` / ``dbt_profile`` /
       ``dbt_target``)
    3. Co-located ``<dbt_project_dir>/profiles.yml`` (dbt 1.5+ default)
    4. ``$DBT_PROFILES_DIR`` env var
    5. ``~/.dbt/profiles.yml``

Public API:

* :func:`resolve_profile` — full resolution → :class:`ResolvedProfile`.
* :func:`discover_profiles` — list every profile in the resolved
  ``profiles.yml`` (used by ``tycoon profiles list``).
* :func:`extract_dbt_warehouse_target` — typed view of the active
  output target (adapter, identifier, display, details).
* :class:`DbtWarehouseTarget`, :class:`ProfileOverrides`,
  :class:`ResolvedProfile` — data containers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# --------------------------------------------------------------------------
# Data containers
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ProfileOverrides:
    """CLI-supplied overrides; ``None`` means "fall through to next layer"."""

    profiles_dir: Path | None = None
    profile: str | None = None
    target: str | None = None


@dataclass(frozen=True)
class DbtWarehouseTarget:
    """Structured view of a dbt profile's active output target.

    ``adapter_type`` is the raw dbt adapter type (``duckdb``, ``snowflake``,
    ``bigquery``, ``redshift``, ``postgres``, ...). ``identifier`` is the
    best single-field locator for the warehouse:

    * duckdb (local)  → absolute filesystem path
    * duckdb (md:*)   → the full ``md:<name>`` string
    * snowflake       → ``<account>`` (dbt's ``account`` field)
    * bigquery        → ``<project>``
    * redshift        → ``<host>``
    * anything else   → whatever looks distinctive (may be empty)

    ``display`` is a human-friendly string for prompts / warnings. For
    DuckDB and MotherDuck this equals ``identifier``; for Snowflake it's
    ``snowflake://<account>[/<database>]``.
    """

    adapter_type: str
    identifier: str
    display: str
    details: dict[str, str]

    @property
    def tycoon_warehouse_type(self) -> str | None:
        """Map adapter_type → tycoon's WarehouseType string, or None if unknown."""
        if self.adapter_type == "duckdb":
            return "motherduck" if self.identifier.startswith("md:") else "duckdb"
        if self.adapter_type in {"snowflake", "bigquery", "redshift"}:
            return self.adapter_type
        return None


@dataclass(frozen=True)
class ResolvedProfile:
    """Outcome of resolving a tycoon project's dbt profile.

    ``profiles_yml`` is the file we actually read. ``profile`` and
    ``target`` are the names of the active profile and its active
    output target. ``warehouse`` carries the parsed adapter view.

    ``source`` documents which resolution layer won, so doctor commands
    can explain *why* tycoon picked this profile.
    """

    profiles_yml: Path
    profile: str
    target: str
    warehouse: DbtWarehouseTarget | None
    source: str
    raw_target: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------
# Search-path resolution
# --------------------------------------------------------------------------


def _candidate_profile_dirs(
    project_root: Path,
    dbt_project_dir: Path,
    overrides: ProfileOverrides,
    project_dbt_profiles_dir: str | None,
) -> list[tuple[Path, str]]:
    """Return ``[(dir, source_label), ...]`` in resolution order.

    ``source_label`` is recorded on the returned :class:`ResolvedProfile`
    so doctor output can say *why* the chosen file was chosen.
    """
    out: list[tuple[Path, str]] = []

    if overrides.profiles_dir is not None:
        d = overrides.profiles_dir.expanduser()
        if not d.is_absolute():
            d = (project_root / d).resolve()
        out.append((d, "CLI --profiles-dir"))

    if project_dbt_profiles_dir:
        d = Path(project_dbt_profiles_dir).expanduser()
        if not d.is_absolute():
            d = (project_root / d).resolve()
        out.append((d, "tycoon.yml dbt_profiles_dir"))

    if dbt_project_dir.exists():
        out.append((dbt_project_dir, "<dbt_project_dir>/profiles.yml"))

    env = os.environ.get("DBT_PROFILES_DIR")
    if env:
        out.append((Path(env).expanduser().resolve(), "$DBT_PROFILES_DIR"))

    out.append((Path.home() / ".dbt", "~/.dbt/profiles.yml"))
    return out


def _first_existing_profiles_yml(
    candidates: list[tuple[Path, str]],
) -> tuple[Path, str] | None:
    """Walk candidates, return the first ``profiles.yml`` that exists."""
    for d, source in candidates:
        f = d / "profiles.yml"
        if f.exists():
            return f, source
    return None


# --------------------------------------------------------------------------
# Profile parsing
# --------------------------------------------------------------------------


def _load_profiles_yml(path: Path) -> dict[str, Any] | None:
    """Best-effort load. Returns ``None`` on missing / malformed files."""
    try:
        data = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError):
        return None
    return data if isinstance(data, dict) else None


def _read_dbt_project_profile_name(dbt_project_dir: Path) -> str | None:
    """Read the ``profile:`` field from ``dbt_project.yml``."""
    f = dbt_project_dir / "dbt_project.yml"
    if not f.exists():
        return None
    try:
        data = yaml.safe_load(f.read_text())
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(data, dict):
        return None
    val = data.get("profile")
    return str(val) if val else None


def _adapter_view(target: dict[str, Any], dbt_project_dir: Path) -> DbtWarehouseTarget:
    """Build a :class:`DbtWarehouseTarget` from a raw dbt target dict."""
    adapter_type = str(target.get("type") or "")

    if adapter_type == "duckdb":
        path = target.get("path")
        if not path:
            return DbtWarehouseTarget("duckdb", "", "duckdb", {})
        if str(path).startswith("md:"):
            return DbtWarehouseTarget("duckdb", str(path), str(path), {})
        abs_path = Path(path)
        if not abs_path.is_absolute():
            abs_path = (dbt_project_dir / abs_path).resolve()
        return DbtWarehouseTarget("duckdb", str(abs_path), str(abs_path), {})

    if adapter_type == "snowflake":
        account = str(target.get("account") or "")
        database = str(target.get("database") or "")
        display = f"snowflake://{account}" + (f"/{database}" if database else "")
        return DbtWarehouseTarget(
            "snowflake",
            account,
            display,
            {
                "database": database,
                "schema": str(target.get("schema") or ""),
                "warehouse": str(target.get("warehouse") or ""),
                "role": str(target.get("role") or ""),
            },
        )

    if adapter_type == "bigquery":
        project = str(target.get("project") or "")
        dataset = str(target.get("dataset") or target.get("schema") or "")
        display = f"bigquery://{project}" + (f"/{dataset}" if dataset else "")
        return DbtWarehouseTarget(
            "bigquery",
            project,
            display,
            {
                "dataset": dataset,
                "method": str(target.get("method") or ""),
                "location": str(target.get("location") or ""),
            },
        )

    if adapter_type == "redshift":
        host = str(target.get("host") or "")
        database = str(target.get("dbname") or target.get("database") or "")
        display = f"redshift://{host}" + (f"/{database}" if database else "")
        return DbtWarehouseTarget(
            "redshift",
            host,
            display,
            {"database": database, "schema": str(target.get("schema") or "")},
        )

    return DbtWarehouseTarget(adapter_type, "", adapter_type or "unknown", {})


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------


def resolve_profile(
    project_root: Path,
    dbt_project_dir: Path,
    project_dbt_profiles_dir: str | None = None,
    project_dbt_profile: str | None = None,
    project_dbt_target: str | None = None,
    overrides: ProfileOverrides | None = None,
) -> ResolvedProfile | None:
    """Resolve the active dbt profile for a tycoon project.

    Returns ``None`` if no ``profiles.yml`` can be found in any of the
    standard locations, or if the named profile is missing.

    The function never raises on malformed YAML — it walks past broken
    files and tries the next candidate, matching dbt's behavior.
    """
    overrides = overrides or ProfileOverrides()
    dbt_project_dir = dbt_project_dir.expanduser().resolve()

    candidates = _candidate_profile_dirs(
        project_root=project_root,
        dbt_project_dir=dbt_project_dir,
        overrides=overrides,
        project_dbt_profiles_dir=project_dbt_profiles_dir,
    )
    found = _first_existing_profiles_yml(candidates)
    if found is None:
        return None
    profiles_yml, source = found

    data = _load_profiles_yml(profiles_yml)
    if data is None:
        return None

    profile_name = (
        overrides.profile
        or project_dbt_profile
        or _read_dbt_project_profile_name(dbt_project_dir)
    )
    if not profile_name:
        return None

    profile = data.get(profile_name)
    if not isinstance(profile, dict):
        return None

    target_name = overrides.target or project_dbt_target or profile.get("target") or "dev"
    outputs = profile.get("outputs") or {}
    raw_target = outputs.get(target_name) if isinstance(outputs, dict) else None
    if not isinstance(raw_target, dict):
        # Profile exists but the target doesn't — return a partial result so
        # doctor commands can flag the mismatch.
        return ResolvedProfile(
            profiles_yml=profiles_yml,
            profile=profile_name,
            target=str(target_name),
            warehouse=None,
            source=source,
            raw_target={},
        )

    return ResolvedProfile(
        profiles_yml=profiles_yml,
        profile=profile_name,
        target=str(target_name),
        warehouse=_adapter_view(raw_target, dbt_project_dir),
        source=source,
        raw_target=raw_target,
    )


@dataclass(frozen=True)
class DiscoveredProfile:
    """One row in `tycoon profiles list`."""

    name: str
    targets: list[str]
    default_target: str
    adapter_types: dict[str, str]  # target_name -> adapter type


def discover_profiles(profiles_yml: Path) -> list[DiscoveredProfile]:
    """List every profile in a ``profiles.yml`` with its targets + adapters.

    Used by ``tycoon profiles list``. Returns an empty list on missing /
    malformed files (the caller already knows the file existed because
    it came from :func:`resolve_profile`).
    """
    data = _load_profiles_yml(profiles_yml)
    if data is None:
        return []
    out: list[DiscoveredProfile] = []
    for name, body in data.items():
        if not isinstance(body, dict) or name == "config":
            continue
        outputs = body.get("outputs") or {}
        if not isinstance(outputs, dict):
            continue
        targets = list(outputs.keys())
        adapters = {
            t: str((outputs[t] or {}).get("type") or "")
            for t in targets
            if isinstance(outputs[t], dict)
        }
        default_target = body.get("target") or (targets[0] if targets else "")
        out.append(
            DiscoveredProfile(
                name=str(name),
                targets=targets,
                default_target=str(default_target),
                adapter_types=adapters,
            )
        )
    return out


def extract_dbt_warehouse_target(
    dbt_project_dir: Path,
    profiles_dir: Path | None = None,
    profile_name: str | None = None,
    target_name: str | None = None,
) -> DbtWarehouseTarget | None:
    """Backwards-compat shim used by ``tycoon init`` and ``tycoon register``.

    Mirrors the function previously defined inline in ``commands/init.py``.
    Returns ``None`` if the active profile/target can't be resolved.
    """
    overrides = ProfileOverrides(
        profiles_dir=profiles_dir,
        profile=profile_name,
        target=target_name,
    )
    resolved = resolve_profile(
        project_root=dbt_project_dir,
        dbt_project_dir=dbt_project_dir,
        overrides=overrides,
    )
    if resolved is None:
        return None
    return resolved.warehouse


_SECRET_KEYS = {
    "password",
    "private_key",
    "private_key_passphrase",
    "client_secret",
    "secret",
    "api_key",
    "token",
    "access_token",
    "refresh_token",
}


def redact_secrets(value: Any) -> Any:
    """Recursively redact common secret-bearing fields. Used by ``profiles show``."""
    if isinstance(value, dict):
        return {
            k: ("***redacted***" if k.lower() in _SECRET_KEYS else redact_secrets(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(v) for v in value]
    return value
