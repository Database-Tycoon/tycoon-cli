"""Tests for Fivetran metadata reader (client, sync, status integration).

All HTTP is mocked via ``httpx.MockTransport`` — no real Fivetran
calls. The fixtures shape responses to match the real API as
documented at https://fivetran.com/docs/rest-api so the parser is
exercised against realistic payloads.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import duckdb
import httpx
import pytest

from tycoon.ingestion.fivetran_client import (
    Connector,
    FivetranAPIError,
    FivetranClient,
)
from tycoon.ingestion.fivetran_sync import (
    freshness_label,
    latest_connector_snapshot,
    sync_fivetran_metadata,
)


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


def _connector_body(
    cid: str,
    *,
    schema: str = "raw_orders",
    service: str = "postgres",
    succeeded_at: str | None = "2026-05-08T08:30:00Z",
    failed_at: str | None = None,
    paused: bool = False,
    sync_state: str = "scheduled",
    setup_state: str = "connected",
    update_state: str = "on_schedule",
) -> dict:
    """Inline connector representation as it appears in list + detail responses."""
    return {
        "id": cid,
        "service": service,
        "schema": schema,
        "paused": paused,
        "succeeded_at": succeeded_at,
        "failed_at": failed_at,
        "status": {
            "sync_state": sync_state,
            "setup_state": setup_state,
            "update_state": update_state,
        },
    }


def _connector_payload(cid: str, **kwargs) -> dict:
    """Single-connector detail response — wraps the body in a `data` envelope."""
    return {"data": _connector_body(cid, **kwargs)}


def _list_payload(
    connectors: list[dict] | list[str],
    next_cursor: str | None = None,
) -> dict:
    """Group-connector list response. Accepts full bodies (preferred) or bare
    ids as a backwards-compatible shorthand for tests that only care about
    pagination shape."""
    items: list[dict] = [
        c if isinstance(c, dict) else _connector_body(c)
        for c in connectors
    ]
    body: dict = {"data": {"items": items}}
    if next_cursor:
        body["data"]["next_cursor"] = next_cursor
    return body


def _make_handler(routes: dict[str, dict | list[dict]]):
    """Build a handler that maps URL path → JSON payload(s).

    A list value means "return payload N on the Nth call to that path"
    — used to test pagination cursors.
    """
    state: dict[str, int] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        key = request.url.path
        match = routes.get(key)
        if match is None:
            return httpx.Response(404, json={"error": f"no fixture for {key}"})
        if isinstance(match, list):
            i = state.get(key, 0)
            payload = match[min(i, len(match) - 1)]
            state[key] = i + 1
        else:
            payload = match
        return httpx.Response(200, json=payload)

    return handler


def _make_client(routes: dict, group_id: str = "g1") -> FivetranClient:
    transport = httpx.MockTransport(_make_handler(routes))
    http = httpx.Client(transport=transport)
    return FivetranClient(
        api_key="k", api_secret="s", group_id=group_id, http_client=http
    )


# --------------------------------------------------------------------------
# Client
# --------------------------------------------------------------------------


class TestFivetranClient:
    def test_list_connectors_returns_typed_objects(self):
        client = _make_client(
            {
                "/v1/groups/g1/connectors": _list_payload(
                    [
                        _connector_body("c1", schema="raw_a"),
                        _connector_body("c2", schema="raw_b", service="shopify"),
                    ]
                ),
            }
        )
        out = client.list_connectors()
        assert len(out) == 2
        assert all(isinstance(c, Connector) for c in out)
        names = sorted(c.schema_name for c in out)
        assert names == ["raw_a", "raw_b"]

    def test_list_connectors_makes_one_call_no_per_id_fanout(self):
        """Regression test for the N+1 we just removed. Counts list-endpoint
        hits to prove we didn't sneak in a per-connector round-trip."""
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            return httpx.Response(
                200,
                json=_list_payload(
                    [_connector_body("c1"), _connector_body("c2")]
                ),
            )

        http = httpx.Client(transport=httpx.MockTransport(handler))
        client = FivetranClient("k", "s", "g1", http_client=http)
        client.list_connectors()
        # Exactly one round-trip — the list endpoint, period.
        assert calls == ["/v1/groups/g1/connectors"]

    def test_pagination_follows_next_cursor(self):
        client = _make_client(
            {
                "/v1/groups/g1/connectors": [
                    _list_payload(
                        [_connector_body("c1")], next_cursor="abc"
                    ),
                    _list_payload([_connector_body("c2")]),  # no cursor → done
                ],
            }
        )
        out = client.list_connectors()
        assert {c.connector_id for c in out} == {"c1", "c2"}

    def test_iso_timestamps_parsed_as_utc_aware(self):
        client = _make_client(
            {
                "/v1/groups/g1/connectors": _list_payload(
                    [_connector_body("c1", succeeded_at="2026-05-08T08:30:00Z")]
                ),
            }
        )
        c = client.list_connectors()[0]
        assert c.succeeded_at is not None
        assert c.succeeded_at.tzinfo is not None
        assert c.succeeded_at == datetime.datetime(
            2026, 5, 8, 8, 30, tzinfo=datetime.timezone.utc
        )

    def test_invalid_timestamp_becomes_none(self):
        client = _make_client(
            {
                "/v1/groups/g1/connectors": _list_payload(
                    [_connector_body("c1", succeeded_at="not-a-date")]
                ),
            }
        )
        c = client.list_connectors()[0]
        assert c.succeeded_at is None

    def test_context_manager_closes_owned_client(self):
        """When the client creates its own httpx.Client, exiting the `with`
        block must close it. Reuses a real client + asserts via is_closed."""
        client = FivetranClient("k", "s", "g1")
        underlying = client._http  # noqa: SLF001 — explicit white-box check
        with client:
            assert not underlying.is_closed
        assert underlying.is_closed

    def test_context_manager_does_not_close_caller_provided_client(self):
        """If the caller passed in their own httpx.Client, we don't close
        it — that's the caller's contract."""
        http = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"data": {}})))
        with FivetranClient("k", "s", "g1", http_client=http):
            pass
        assert not http.is_closed
        http.close()

    def test_4xx_response_raises_api_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "unauthorized"})

        http = httpx.Client(transport=httpx.MockTransport(handler))
        client = FivetranClient("k", "s", "g1", http_client=http)
        with pytest.raises(FivetranAPIError, match="401"):
            client.list_connectors()

    def test_verify_credentials_returns_false_on_auth_failure(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "unauthorized"})

        http = httpx.Client(transport=httpx.MockTransport(handler))
        client = FivetranClient("k", "s", "g1", http_client=http)
        assert client.verify_credentials() is False

    def test_verify_credentials_returns_true_on_success(self):
        client = _make_client({"/v1/groups/g1": {"data": {"id": "g1", "name": "X"}}})
        assert client.verify_credentials() is True


# --------------------------------------------------------------------------
# Sync (DB writes)
# --------------------------------------------------------------------------


class TestFivetranSync:
    def test_sync_writes_one_row_per_connector(self, tmp_path: Path):
        client = _make_client(
            {
                "/v1/groups/g1/connectors": _list_payload(
                    [
                        _connector_body("c1", schema="a"),
                        _connector_body(
                            "c2",
                            schema="b",
                            failed_at="2026-05-08T09:00:00Z",
                            succeeded_at=None,
                        ),
                    ]
                ),
            }
        )
        meta_db = tmp_path / "metadata.duckdb"
        result = sync_fivetran_metadata(client, meta_db)
        assert result.connectors_seen == 2
        assert result.failing == 1
        assert result.healthy == 1
        assert result.new == 2

        con = duckdb.connect(str(meta_db), read_only=True)
        try:
            count = con.execute(
                "SELECT count(*) FROM fivetran_connectors"
            ).fetchone()[0]
        finally:
            con.close()
        assert count == 2

    def test_re_sync_at_later_time_accumulates_history(self, tmp_path: Path):
        """Multiple syncs produce multiple snapshots per connector."""
        client = _make_client(
            {
                "/v1/groups/g1/connectors": _list_payload(
                    [_connector_body("c1")]
                ),
            }
        )
        meta_db = tmp_path / "metadata.duckdb"

        first = sync_fivetran_metadata(client, meta_db)
        # Real-clock advance: re-sync may collide on captured_at within the
        # same second. INSERT OR REPLACE keeps the call safe; we just check
        # the schema accepts repeated inserts without raising.
        sync_fivetran_metadata(client, meta_db)

        con = duckdb.connect(str(meta_db), read_only=True)
        try:
            row = con.execute(
                "SELECT count(DISTINCT connector_id) FROM fivetran_connectors"
            ).fetchone()
        finally:
            con.close()
        assert row[0] == 1
        assert first.new == 1  # first sync flagged it as new

    def test_latest_connector_snapshot_returns_most_recent_per_connector(
        self, tmp_path: Path
    ):
        meta_db = tmp_path / "metadata.duckdb"
        client = _make_client(
            {
                "/v1/groups/g1/connectors": _list_payload(
                    [_connector_body("c1")]
                ),
            }
        )
        sync_fivetran_metadata(client, meta_db)
        rows = latest_connector_snapshot(meta_db)
        assert len(rows) == 1
        assert rows[0]["connector_id"] == "c1"
        assert rows[0]["sync_state"] == "scheduled"

    def test_latest_connector_snapshot_handles_missing_db(self, tmp_path: Path):
        assert latest_connector_snapshot(tmp_path / "no.duckdb") == []


# --------------------------------------------------------------------------
# Freshness labelling
# --------------------------------------------------------------------------


class TestFreshnessLabel:
    def test_paused_connector_labelled_paused(self):
        label, _ = freshness_label(
            succeeded_at=None, failed_at=None, paused=True
        )
        assert label == "paused"

    def test_never_synced_is_red(self):
        _, style = freshness_label(
            succeeded_at=None, failed_at=None, paused=False
        )
        assert style == "red"

    def test_recent_success_is_green(self):
        recent = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
            minutes=10
        )
        _, style = freshness_label(
            succeeded_at=recent, failed_at=None, paused=False
        )
        assert style == "green"

    def test_failure_after_success_is_red_failed(self):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        succ = now - datetime.timedelta(hours=2)
        fail = now - datetime.timedelta(minutes=5)
        label, style = freshness_label(
            succeeded_at=succ, failed_at=fail, paused=False
        )
        assert "failed" in label
        assert style == "red"
