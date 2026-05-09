"""Read-only client for the Fivetran Metadata API.

Tycoon doesn't *run* Fivetran — that's Fivetran's own scheduler. This
client just pulls connector + sync metadata from
``api.fivetran.com/v1`` so tycoon's observability surfaces (``data
status``, ``data history``) light up for projects with
``stack.ingestion = fivetran``.

Auth is HTTP Basic with ``api_key:api_secret``. Both come from
``stack.ingestion_metadata`` in ``tycoon.yml``; tycoon does not
re-implement Fivetran's secret handling.

Public surface:

* :class:`FivetranClient` — HTTP wrapper, dependency-injectable for tests.
* :class:`Connector` — typed snapshot of one connector's current state.
* :func:`build_client_from_config` — convenience constructor that reads
  the active ``tycoon.yml``.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any

import httpx

from tycoon.project import FivetranIngestionMetadata

DEFAULT_BASE_URL = "https://api.fivetran.com/v1"
DEFAULT_TIMEOUT_S = 15.0


@dataclass(frozen=True)
class Connector:
    """A point-in-time snapshot of one Fivetran connector.

    Field names track the Fivetran API response — see
    https://fivetran.com/docs/rest-api/connectors. ``succeeded_at`` and
    ``failed_at`` are ISO-8601 timestamps from the API; tycoon parses
    them at write-to-DuckDB time so the wire shape stays raw.
    """

    connector_id: str
    name: str
    service: str
    schema_name: str
    paused: bool
    sync_state: str
    setup_state: str
    update_state: str
    succeeded_at: datetime.datetime | None
    failed_at: datetime.datetime | None


class FivetranAPIError(RuntimeError):
    """Raised on non-2xx Fivetran API responses."""


class FivetranClient:
    """Thin HTTP client for the Fivetran Metadata API.

    All methods are sync. We pass the underlying ``httpx.Client`` in via
    the constructor so tests can swap it for a mock transport without
    monkey-patching network calls globally.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        group_id: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._group_id = group_id
        self._base_url = base_url.rstrip("/")
        self._http = http_client or httpx.Client(
            auth=httpx.BasicAuth(api_key, api_secret),
            timeout=DEFAULT_TIMEOUT_S,
        )
        # Even when the caller passes their own client, ensure auth is set.
        # (The mock-transport tests construct an Auth-less client and rely
        # on this call to install the credentials.)
        if http_client is not None and http_client.auth is None:
            self._http.auth = httpx.BasicAuth(api_key, api_secret)

    # ----- low-level HTTP -----------------------------------------------

    def _get(self, path: str, **params: Any) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            response = self._http.get(url, params=params or None)
        except httpx.HTTPError as exc:
            raise FivetranAPIError(f"Fivetran request failed: {exc}") from exc

        if response.status_code >= 400:
            raise FivetranAPIError(
                f"Fivetran API {response.status_code} on {path}: "
                f"{response.text[:200]}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise FivetranAPIError("Fivetran response was not JSON.") from exc

        if not isinstance(payload, dict) or "data" not in payload:
            raise FivetranAPIError(
                f"Unexpected Fivetran payload shape: {payload!r}"
            )
        return payload

    # ----- public API ---------------------------------------------------

    def list_connectors(self) -> list[Connector]:
        """Return every connector under the configured group."""
        ids = self._list_connector_ids_in_group()
        return [self._get_connector(cid) for cid in ids]

    def verify_credentials(self) -> bool:
        """Lightweight probe — fetch the group's name. Returns False on auth fail.

        Used by ``tycoon doctor`` to confirm the credentials in
        ``tycoon.yml`` actually work without pulling every connector.
        """
        try:
            self._get(f"/groups/{self._group_id}")
            return True
        except FivetranAPIError:
            return False

    # ----- internals ----------------------------------------------------

    def _list_connector_ids_in_group(self) -> list[str]:
        out: list[str] = []
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {"limit": 100}
            if cursor:
                params["cursor"] = cursor
            payload = self._get(f"/groups/{self._group_id}/connectors", **params)
            data = payload.get("data") or {}
            for item in data.get("items") or []:
                cid = item.get("id")
                if cid:
                    out.append(str(cid))
            cursor = data.get("next_cursor")
            if not cursor:
                break
        return out

    def _get_connector(self, connector_id: str) -> Connector:
        payload = self._get(f"/connectors/{connector_id}")
        body = payload.get("data") or {}
        status = body.get("status") or {}
        return Connector(
            connector_id=str(body.get("id") or connector_id),
            name=str(body.get("schema") or body.get("name") or ""),
            service=str(body.get("service") or ""),
            schema_name=str(body.get("schema") or ""),
            paused=bool(body.get("paused", False)),
            sync_state=str(status.get("sync_state") or ""),
            setup_state=str(status.get("setup_state") or ""),
            update_state=str(status.get("update_state") or ""),
            succeeded_at=_parse_iso(body.get("succeeded_at")),
            failed_at=_parse_iso(body.get("failed_at")),
        )


def _parse_iso(raw: Any) -> datetime.datetime | None:
    """Tolerant ISO-8601 → ``datetime`` (UTC). Returns None on missing/invalid."""
    if not raw:
        return None
    s = str(raw).replace("Z", "+00:00")
    try:
        dt = datetime.datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def build_client_from_config(
    cfg: FivetranIngestionMetadata,
    *,
    http_client: httpx.Client | None = None,
) -> FivetranClient:
    """Construct a client from a ``tycoon.yml`` ingestion-metadata block."""
    return FivetranClient(
        api_key=cfg.api_key,
        api_secret=cfg.api_secret,
        group_id=cfg.group_id,
        http_client=http_client,
    )
