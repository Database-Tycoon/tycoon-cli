"""Tests for tycoon.ingestion.manifest — SourceSpec model and load_manifest()."""

from __future__ import annotations

from tycoon.ingestion.manifest import ConfigField, CredentialField, SourceSpec, load_manifest


class TestLoadManifest:
    def test_returns_dict_of_source_specs(self):
        m = load_manifest()
        assert isinstance(m, dict)
        assert len(m) >= 40

    def test_all_values_are_source_specs(self):
        m = load_manifest()
        for key, spec in m.items():
            assert isinstance(spec, SourceSpec), f"{key} is not a SourceSpec"

    def test_id_matches_key(self):
        m = load_manifest()
        for key, spec in m.items():
            assert spec.id == key, f"spec.id {spec.id!r} != key {key!r}"

    def test_github_full_entry(self):
        m = load_manifest()
        assert "github" in m
        gh = m["github"]
        assert gh.display_name == "GitHub"
        assert gh.category == "Developer Tools"
        assert gh.requires_dlt_init is True
        assert gh.dlt_init_name == "github"
        assert gh.dlt_source == "github.github_reactions"
        assert gh.default_schema == "raw_github"
        assert len(gh.credentials) == 1
        assert gh.credentials[0].env_var == "GITHUB_TOKEN"
        assert gh.credentials[0].secret is True
        assert len(gh.config_fields) == 2
        owner_field = gh.config_fields[0]
        assert owner_field.key == "owner"
        assert owner_field.required is True

    def test_rest_api_no_dlt_init(self):
        m = load_manifest()
        ra = m["rest_api"]
        assert ra.requires_dlt_init is False
        assert ra.dlt_source is None
        assert ra.dlt_init_name is None
        assert len(ra.credentials) == 0

    def test_filesystem_no_dlt_init(self):
        m = load_manifest()
        fs = m["filesystem"]
        assert fs.requires_dlt_init is False

    def test_sql_database_no_dlt_init(self):
        m = load_manifest()
        sql = m["sql_database"]
        assert sql.requires_dlt_init is False

    def test_slack_full_entry(self):
        m = load_manifest()
        sl = m["slack"]
        assert sl.credentials[0].env_var == "SLACK_ACCESS_TOKEN"
        assert sl.requires_dlt_init is True

    def test_stripe_maps_to_stripe_analytics_dlt(self):
        m = load_manifest()
        st = m["stripe"]
        assert st.dlt_init_name == "stripe_analytics"
        assert st.dlt_source == "stripe_analytics.stripe_source"

    def test_all_minimal_entries_have_required_fields(self):
        m = load_manifest()
        minimal = [k for k, v in m.items() if not v.credentials and not v.config_fields]
        assert len(minimal) >= 30
        for key in minimal:
            spec = m[key]
            assert spec.display_name, f"{key} missing display_name"
            assert spec.category, f"{key} missing category"
            assert spec.description, f"{key} missing description"
            assert spec.default_schema, f"{key} missing default_schema"


class TestSourceSpec:
    def test_credential_defaults_returns_env_var_refs(self):
        spec = load_manifest()["github"]
        defaults = spec.credential_defaults()
        assert defaults == {"access_token": "${GITHUB_TOKEN}"}

    def test_credential_defaults_empty_for_no_creds(self):
        spec = load_manifest()["rest_api"]
        assert spec.credential_defaults() == {}

    def test_multiple_credentials_all_appear_in_defaults(self):
        spec = SourceSpec(
            id="test",
            display_name="Test",
            category="Test",
            description="Test source",
            credentials=[
                CredentialField(key="api_key", env_var="TEST_KEY", label="API Key"),
                CredentialField(key="api_secret", env_var="TEST_SECRET", label="Secret"),
            ],
        )
        defaults = spec.credential_defaults()
        assert defaults == {"api_key": "${TEST_KEY}", "api_secret": "${TEST_SECRET}"}


class TestSourceSpecModel:
    def test_minimal_construction(self):
        spec = SourceSpec(id="x", display_name="X", category="Test", description="desc")
        assert spec.resources == []
        assert spec.credentials == []
        assert spec.config_fields == []
        assert spec.requires_dlt_init is False
        assert spec.dlt_source is None

    def test_credential_field_defaults(self):
        cred = CredentialField(key="token", env_var="MY_TOKEN", label="Token")
        assert cred.secret is True
        assert cred.hint == ""

    def test_config_field_defaults(self):
        field = ConfigField(key="owner", label="Owner")
        assert field.required is True
        assert field.hint == ""
        assert field.default is None

    def test_optional_default_accepted(self):
        field = ConfigField(key="ids", label="IDs", required=False, default="")
        assert field.default == ""
