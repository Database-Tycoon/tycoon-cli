"""Tests for webhook notifications (#46) — transport, command, run-all wiring."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tycoon import notify
from tycoon.cli import app


# ---------------------------------------------------------------------------
# Payload + URL helpers
# ---------------------------------------------------------------------------


class TestPayload:
    def test_slack_shape_has_coloured_attachment(self):
        p = notify.build_payload("error", "boom", {"rows": "5"}, label="proj", slack=True)
        att = p["attachments"][0]
        assert att["color"] == "#d00000"
        assert att["text"] == "boom"
        assert att["fields"] == [{"title": "rows", "value": "5", "short": True}]
        assert att["footer"] == "proj"

    def test_generic_shape_is_flat_envelope(self):
        p = notify.build_payload("success", "ok", {"n": "1"}, label="proj")
        assert p["source"] == "tycoon"
        assert p["severity"] == "success"
        assert p["color"] == "#36a64f"
        assert p["fields"] == {"n": "1"}
        assert p["label"] == "proj"
        assert "attachments" not in p

    def test_is_slack_url(self):
        assert notify.is_slack_url("https://hooks.slack.com/services/T/B/x")
        assert not notify.is_slack_url("https://example.com/webhook")


class TestWebhookUrl:
    def test_explicit_arg_wins(self, monkeypatch):
        monkeypatch.setenv(notify.WEBHOOK_ENV_VAR, "https://env.example/h")
        assert notify.webhook_url("https://arg.example/h") == "https://arg.example/h"

    def test_falls_back_to_env(self, monkeypatch):
        monkeypatch.setenv(notify.WEBHOOK_ENV_VAR, "https://env.example/h")
        assert notify.webhook_url() == "https://env.example/h"

    def test_none_when_unset(self, monkeypatch):
        monkeypatch.delenv(notify.WEBHOOK_ENV_VAR, raising=False)
        assert notify.webhook_url() is None


class TestSend:
    def test_returns_false_when_not_configured(self, monkeypatch):
        monkeypatch.delenv(notify.WEBHOOK_ENV_VAR, raising=False)
        assert notify.send("info", "hi") is False

    def test_posts_and_returns_true_on_2xx(self):
        resp = MagicMock(is_success=True)
        with patch("tycoon.notify.httpx.post", return_value=resp) as post:
            ok = notify.send("success", "done", {"rows": "9"}, url="https://example.com/h")
        assert ok is True
        # Generic payload posted as JSON to the given URL.
        _, kwargs = post.call_args
        assert kwargs["json"]["severity"] == "success"

    def test_slack_url_gets_attachment_payload(self):
        resp = MagicMock(is_success=True)
        url = "https://hooks.slack.com/services/T/B/x"
        with patch("tycoon.notify.httpx.post", return_value=resp) as post:
            notify.send("error", "boom", url=url)
        assert "attachments" in post.call_args.kwargs["json"]

    def test_returns_false_on_http_error(self):
        import httpx

        with patch("tycoon.notify.httpx.post", side_effect=httpx.ConnectError("nope")):
            assert notify.send("info", "x", url="https://example.com/h") is False

    def test_returns_false_on_non_2xx(self):
        resp = MagicMock(is_success=False)
        with patch("tycoon.notify.httpx.post", return_value=resp):
            assert notify.send("info", "x", url="https://example.com/h") is False


# ---------------------------------------------------------------------------
# `tycoon notify` command
# ---------------------------------------------------------------------------


class TestNotifyCommand:
    def test_bad_severity_exits_2(self, cli_runner, monkeypatch):
        monkeypatch.setenv(notify.WEBHOOK_ENV_VAR, "https://example.com/h")
        result = cli_runner.invoke(app, ["notify", "bogus", "msg"])
        assert result.exit_code == 2
        assert "Unknown severity" in (result.stderr or result.output)

    def test_missing_webhook_exits_1(self, cli_runner, monkeypatch):
        monkeypatch.delenv(notify.WEBHOOK_ENV_VAR, raising=False)
        result = cli_runner.invoke(app, ["notify", "info", "hello"])
        assert result.exit_code == 1
        assert notify.WEBHOOK_ENV_VAR in (result.stderr or result.output)

    def test_invalid_field_exits_2(self, cli_runner, monkeypatch):
        monkeypatch.setenv(notify.WEBHOOK_ENV_VAR, "https://example.com/h")
        result = cli_runner.invoke(app, ["notify", "info", "hello", "--field", "noequals"])
        assert result.exit_code == 2
        assert "Invalid --field" in (result.stderr or result.output)

    def test_success_path_sends(self, cli_runner, monkeypatch):
        monkeypatch.setenv(notify.WEBHOOK_ENV_VAR, "https://example.com/h")
        with patch("tycoon.notify.send", return_value=True) as send:
            result = cli_runner.invoke(
                app, ["notify", "success", "done", "-f", "rows=10"]
            )
        assert result.exit_code == 0, result.output
        send.assert_called_once()
        # Fields parsed into a dict.
        assert send.call_args.args[2] == {"rows": "10"}

    def test_send_failure_exits_1(self, cli_runner, monkeypatch):
        monkeypatch.setenv(notify.WEBHOOK_ENV_VAR, "https://example.com/h")
        with patch("tycoon.notify.send", return_value=False):
            result = cli_runner.invoke(app, ["notify", "error", "broke"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# `tycoon data run-all --notify`
# ---------------------------------------------------------------------------


class TestRunAllNotify:
    def _bind(self, tmp_path, monkeypatch):
        (tmp_path / "tycoon.yml").write_text(
            "name: t\nversion: 0.1.0\n"
            "database:\n  raw: data/raw.duckdb\n  warehouse: data/warehouse.duckdb\n"
            "sources: {}\n"
        )
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\n')
        from tycoon.commands import run_all as ra_mod
        from tycoon.config import TycoonConfig

        monkeypatch.setattr(ra_mod, "config", TycoonConfig(project_root=tmp_path))

    def test_success_emits_notification(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        monkeypatch.setenv(notify.WEBHOOK_ENV_VAR, "https://example.com/h")
        with patch("tycoon.notify.send", return_value=True) as send:
            result = cli_runner.invoke(
                app,
                ["data", "run-all", "--skip-ingest", "--skip-transform", "--notify"],
            )
        assert result.exit_code == 0, result.output
        send.assert_called_once()
        assert send.call_args.args[0] == "success"

    def test_no_notify_flag_sends_nothing(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        monkeypatch.setenv(notify.WEBHOOK_ENV_VAR, "https://example.com/h")
        with patch("tycoon.notify.send", return_value=True) as send:
            cli_runner.invoke(
                app, ["data", "run-all", "--skip-ingest", "--skip-transform"]
            )
        send.assert_not_called()

    def test_notify_without_webhook_warns_not_crashes(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        monkeypatch.delenv(notify.WEBHOOK_ENV_VAR, raising=False)
        result = cli_runner.invoke(
            app, ["data", "run-all", "--skip-ingest", "--skip-transform", "--notify"]
        )
        # Pipeline still succeeds; just warns about the missing webhook.
        assert result.exit_code == 0, result.output
        assert notify.WEBHOOK_ENV_VAR in result.output