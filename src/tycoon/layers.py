"""Layer-aware data model.

Classifies every table tycoon governs into one of the canonical layers
of the medallion / Kimball / dbt-style analytics-warehouse architecture:

    sources -> staging -> intermediate -> marts

dbt-side classification flows from the manifest's ``original_file_path``
folder convention (``models/staging/`` -> staging, etc.) with per-model
``meta.tycoon_layer`` overrides taking priority. dbt merges per-folder
``+meta`` from ``dbt_project.yml`` into each node's ``config.meta`` for
us, so we don't have to read ``dbt_project.yml`` separately.

Source-side classification reads dlt vendor info from ``tycoon.yml``'s
``sources:`` block and Fivetran connectors from the latest snapshot
written by ``tycoon data fivetran sync``. No new ``tycoon.yml`` block
is introduced -- classification authority lives in the tools that own
the objects.

Tables that don't come from one of these tracked surfaces (hand-rolled
SQL, notebook outputs, ad-hoc CTAS) classify as ``Layer.UNCLASSIFIED``.
That's the right behaviour: tycoon governs dbt + ingestion, and that's
what it has an opinion about.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable


class Layer(str, Enum):
    """Canonical analytics-warehouse layer."""

    SOURCE = "source"
    STAGING = "staging"
    INTERMEDIATE = "intermediate"
    MART = "mart"
    SNAPSHOT = "snapshot"
    SEED = "seed"
    UNCLASSIFIED = "unclassified"


class Vendor(str, Enum):
    """Where a classified object came from."""

    DLT = "dlt"
    FIVETRAN = "fivetran"
    AIRBYTE = "airbyte"
    DBT = "dbt"
    UNKNOWN = "unknown"


# dbt folder-name -> Layer. Matches the convention dbt itself documents
# (`models/staging/`, `models/intermediate/`, `models/marts/`) plus the
# common aliases analytics teams use in practice.
_FOLDER_TO_LAYER: dict[str, Layer] = {
    "staging": Layer.STAGING,
    "stg": Layer.STAGING,
    "intermediate": Layer.INTERMEDIATE,
    "int": Layer.INTERMEDIATE,
    "marts": Layer.MART,
    "mart": Layer.MART,
    # Some teams use "core" or "published" for the final layer.
    "core": Layer.MART,
    "published": Layer.MART,
}

_META_KEY = "tycoon_layer"


@dataclass(frozen=True)
class LayerClassification:
    """One classified table tycoon knows about.

    Attributes
    ----------
    layer
        Which layer this table belongs to.
    vendor
        Who created the table (dlt, fivetran, dbt, ...).
    name
        Display name (model name or table name -- no schema prefix).
    schema
        Database schema. ``None`` only when the source hasn't been
        materialised yet (e.g. dlt source registered but never run).
    identifier
        Stable identifier: ``"<vendor>:<schema>.<name>"`` for sources,
        ``"dbt:<unique_id>"`` for dbt models. Use this for deduping
        across multiple classifier passes.
    source_name
        For sources only -- the dlt source name (`pokeapi`) or the
        Fivetran connector name. ``None`` for dbt models.
    file_path
        For dbt models only -- ``original_file_path`` from the
        manifest. ``None`` for sources.
    """

    layer: Layer
    vendor: Vendor
    name: str
    schema: str | None = None
    identifier: str = ""
    source_name: str | None = None
    file_path: str | None = None


# -- dbt manifest classification ------------------------------------------------


def _layer_from_folder(original_file_path: str) -> Layer:
    """Map ``models/staging/foo.sql`` to ``Layer.STAGING`` via folder name."""
    parts = Path(original_file_path).parts
    # Look for "models" then take the next path component as the folder.
    # Handles ``models/staging/stg_orders.sql`` and the rarer
    # ``models/staging/finance/stg_invoices.sql`` (nested) the same way.
    try:
        models_idx = parts.index("models")
    except ValueError:
        return Layer.UNCLASSIFIED
    if models_idx + 1 >= len(parts):
        return Layer.UNCLASSIFIED
    folder = parts[models_idx + 1]
    return _FOLDER_TO_LAYER.get(folder, Layer.UNCLASSIFIED)


def _classify_node(node: dict[str, Any]) -> Layer:
    """Resolve a single node's layer using the priority chain.

    1. ``config.meta.tycoon_layer`` -- per-model schema.yml or per-folder
       ``+meta`` (dbt merges both into ``config.meta`` for us).
    2. Folder convention from ``original_file_path``.
    3. ``Layer.UNCLASSIFIED``.
    """
    meta_layer = (node.get("config") or {}).get("meta", {}).get(_META_KEY)
    if isinstance(meta_layer, str):
        try:
            return Layer(meta_layer.lower())
        except ValueError:
            # User-typo'd a meta value -- fall through to folder convention
            # rather than crashing. doctor will surface it separately.
            pass

    file_path = node.get("original_file_path") or ""
    return _layer_from_folder(file_path)


def classify_dbt_models(manifest: dict[str, Any]) -> list[LayerClassification]:
    """Classify every model / snapshot / seed in a parsed dbt manifest.

    Parameters
    ----------
    manifest
        Already-parsed ``target/manifest.json`` dict. Use
        :func:`load_manifest` for the file-loading wrapper.
    """
    out: list[LayerClassification] = []
    nodes = manifest.get("nodes") or {}
    for unique_id, node in nodes.items():
        rtype = node.get("resource_type")
        if rtype not in ("model", "snapshot", "seed"):
            continue

        if rtype == "snapshot":
            layer = Layer.SNAPSHOT
        elif rtype == "seed":
            layer = Layer.SEED
        else:
            layer = _classify_node(node)

        out.append(
            LayerClassification(
                layer=layer,
                vendor=Vendor.DBT,
                name=node.get("name") or unique_id.rsplit(".", 1)[-1],
                schema=node.get("schema"),
                identifier=f"dbt:{unique_id}",
                file_path=node.get("original_file_path"),
            )
        )
    return out


def load_manifest(dbt_project_dir: Path) -> dict[str, Any] | None:
    """Read and parse ``<dbt_project_dir>/target/manifest.json``.

    Returns ``None`` when the manifest is missing or unreadable -- callers
    should treat that as "dbt hasn't compiled yet" and gracefully show an
    empty staging/intermediate/marts surface.
    """
    path = dbt_project_dir / "target" / "manifest.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


# -- Source-side classification -------------------------------------------------


def classify_dlt_sources(
    sources_block: dict[str, Any] | None,
) -> list[LayerClassification]:
    """Build source classifications from ``tycoon.yml``'s ``sources:`` block.

    Each entry materialises one ``LayerClassification`` representing the
    source as a whole; per-table fan-out happens later when the warehouse
    is actually inspected.
    """
    out: list[LayerClassification] = []
    for name, src in (sources_block or {}).items():
        schema_name = _resolve_schema_name(src)
        out.append(
            LayerClassification(
                layer=Layer.SOURCE,
                vendor=Vendor.DLT,
                name=name,
                schema=schema_name,
                identifier=f"dlt:{schema_name or '?'}.{name}",
                source_name=name,
            )
        )
    return out


def _resolve_schema_name(src: Any) -> str | None:
    """Pull the schema name off either a pydantic ``SourceConfig`` or a dict."""
    if src is None:
        return None
    if hasattr(src, "schema_name"):
        return src.schema_name
    if isinstance(src, dict):
        return src.get("schema_name") or src.get("schema")
    return None


def classify_fivetran_sources(
    snapshots: Iterable[dict[str, Any]],
) -> list[LayerClassification]:
    """Build source classifications from Fivetran connector snapshots.

    Parameters
    ----------
    snapshots
        Rows from :func:`tycoon.ingestion.fivetran_sync.latest_connector_snapshot`.
    """
    out: list[LayerClassification] = []
    for row in snapshots:
        schema_name = row.get("schema_name") or row.get("schema")
        name = row.get("name") or row.get("connector_id") or "?"
        out.append(
            LayerClassification(
                layer=Layer.SOURCE,
                vendor=Vendor.FIVETRAN,
                name=name,
                schema=schema_name,
                identifier=f"fivetran:{schema_name or '?'}.{name}",
                source_name=name,
            )
        )
    return out


# -- Convenience accessors -----------------------------------------------------


def filter_by_layer(
    classifications: Iterable[LayerClassification], layer: Layer
) -> list[LayerClassification]:
    """Return every classification matching ``layer``. Stable order."""
    return [c for c in classifications if c.layer == layer]
