"""Tests for tycoon.ingestion.factory — SourceFactory.collect_config()."""

from __future__ import annotations

import pytest
import typer

from tycoon.ingestion.factory import SourceFactory
from tycoon.ingestion.manifest import ConfigField, CredentialField, SourceSpec, load_manifest


def _spec_with(**overrides) -> SourceSpec:
    defaults = dict(id="test", display_name="Test", category="Test", description="desc")
    defaults.update(overrides)
    return SourceSpec(**defaults)


class TestCollectConfigNonInteractive:
    def test_credential_defaults_to_env_var_ref_when_flag_absent(self):
        spec = load_manifest()["github"]
        factory = SourceFactory(spec)
        config = factory.collect_config(no_prompt=True, flags={"owner": "dlt-hub", "repo": "dlt"})
        assert config["access_token"] == "${GITHUB_TOKEN}"

    def test_flags_override_credential_default(self):
        spec = load_manifest()["github"]
        config = SourceFactory(spec).collect_config(
            no_prompt=True,
            flags={"access_token": "ghp_abc123", "owner": "acme", "repo": "widgets"},
        )
        assert config["access_token"] == "ghp_abc123"

    def test_required_config_field_present_in_flags(self):
        spec = load_manifest()["github"]
        config = SourceFactory(spec).collect_config(
            no_prompt=True,
            flags={"owner": "dlt-hub", "repo": "dlt"},
        )
        assert config["owner"] == "dlt-hub"
        assert config["repo"] == "dlt"

    def test_missing_required_config_field_raises_exit(self):
        spec = load_manifest()["github"]
        with pytest.raises(typer.Exit) as exc_info:
            SourceFactory(spec).collect_config(no_prompt=True, flags={})
        assert exc_info.value.exit_code == 1

    def test_missing_one_required_field_raises_exit(self):
        spec = load_manifest()["github"]
        with pytest.raises(typer.Exit) as exc_info:
            SourceFactory(spec).collect_config(no_prompt=True, flags={"owner": "acme"})
        assert exc_info.value.exit_code == 1

    def test_all_missing_required_fields_reported_before_exit(self):
        spec = load_manifest()["github"]
        with pytest.raises(typer.Exit) as exc_info:
            SourceFactory(spec).collect_config(no_prompt=True, flags={})
        assert exc_info.value.exit_code == 1

    def test_optional_field_absent_keeps_default(self):
        spec = load_manifest()["slack"]
        config = SourceFactory(spec).collect_config(no_prompt=True, flags={})
        assert "channel_ids" not in config

    def test_optional_field_with_non_empty_default_included(self):
        spec = _spec_with(
            config_fields=[
                ConfigField(key="base_url", label="Base URL", required=False, default="https://example.com")
            ]
        )
        config = SourceFactory(spec).collect_config(no_prompt=True, flags={})
        assert config["base_url"] == "https://example.com"

    def test_optional_field_with_empty_default_excluded(self):
        spec = _spec_with(
            config_fields=[ConfigField(key="ids", label="IDs", required=False, default="")]
        )
        config = SourceFactory(spec).collect_config(no_prompt=True, flags={})
        assert "ids" not in config

    def test_source_with_no_fields_returns_empty_dict(self):
        spec = load_manifest()["airtable"]
        config = SourceFactory(spec).collect_config(no_prompt=True, flags={})
        assert config == {}

    def test_none_flags_treated_as_empty(self):
        spec = load_manifest()["airtable"]
        config = SourceFactory(spec).collect_config(no_prompt=True, flags=None)
        assert config == {}

    def test_rest_api_optional_defaults_included(self):
        spec = load_manifest()["rest_api"]
        config = SourceFactory(spec).collect_config(no_prompt=True, flags={})
        assert "access_token" not in config
        assert config["base_url"] == "https://pokeapi.co/api/v2/"
        assert config["resources"] == "pokemon,berry,type"

    def test_optional_field_with_none_default_excluded(self):
        spec = _spec_with(
            config_fields=[ConfigField(key="ids", label="IDs", required=False, default=None)]
        )
        config = SourceFactory(spec).collect_config(no_prompt=True, flags={})
        assert "ids" not in config

    def test_multiple_credentials_all_defaulted(self):
        spec = _spec_with(
            credentials=[
                CredentialField(key="key1", env_var="KEY_ONE", label="Key One"),
                CredentialField(key="key2", env_var="KEY_TWO", label="Key Two"),
            ]
        )
        config = SourceFactory(spec).collect_config(no_prompt=True, flags={})
        assert config["key1"] == "${KEY_ONE}"
        assert config["key2"] == "${KEY_TWO}"


class TestCollectConfigInteractive:
    """Interactive-mode tests use typer.testing.CliRunner to drive prompts."""

    def _run_factory(self, spec: SourceSpec, input_text: str) -> dict:
        import typer
        from typer.testing import CliRunner

        _app = typer.Typer()

        result_holder: dict = {}

        @_app.command()
        def _cmd() -> None:
            result_holder["config"] = SourceFactory(spec).collect_config(no_prompt=False)

        runner = CliRunner()
        result = runner.invoke(_app, [], input=input_text)
        assert result.exit_code == 0, f"CLI crashed: {result.exception}"
        return result_holder.get("config", {})

    def test_interactive_credential_uses_env_var_default(self):
        spec = load_manifest()["github"]
        config = self._run_factory(spec, "\ndlt-hub\ndlt\n")
        assert config.get("access_token") == "${GITHUB_TOKEN}"

    def test_interactive_credential_explicit_value(self):
        spec = load_manifest()["github"]
        config = self._run_factory(spec, "ghp_token\ndlt-hub\ndlt\n")
        assert config.get("access_token") == "ghp_token"

    def test_interactive_required_config_field(self):
        spec = load_manifest()["github"]
        config = self._run_factory(spec, "\ndlt-hub\ndlt\n")
        assert config.get("owner") == "dlt-hub"
        assert config.get("repo") == "dlt"

    def test_interactive_optional_field_blank_excluded(self):
        spec = load_manifest()["slack"]
        config = self._run_factory(spec, "\n\n")
        assert "channel_ids" not in config

    def test_interactive_optional_field_filled_included(self):
        spec = load_manifest()["slack"]
        config = self._run_factory(spec, "\nC01234567\n")
        assert config.get("channel_ids") == "C01234567"

    def test_interactive_source_with_no_fields_returns_empty(self):
        spec = load_manifest()["airtable"]
        config = self._run_factory(spec, "")
        assert config == {}
