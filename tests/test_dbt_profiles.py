"""Tests for tycoon.dbt_profiles — central dbt profile resolver."""

from __future__ import annotations

from pathlib import Path

import yaml

from tycoon.dbt_profiles import (
    ProfileOverrides,
    discover_profiles,
    extract_dbt_warehouse_target,
    redact_secrets,
    resolve_profile,
)


def _write_dbt_project(dir_: Path, profile_name: str = "p") -> None:
    dir_.mkdir(parents=True, exist_ok=True)
    (dir_ / "dbt_project.yml").write_text(
        yaml.dump({"name": "p", "profile": profile_name, "version": "1"})
    )


def _write_profiles(
    dir_: Path,
    profile_name: str = "p",
    target: str = "dev",
    type_: str = "duckdb",
    path: str = "warehouse.duckdb",
) -> None:
    dir_.mkdir(parents=True, exist_ok=True)
    (dir_ / "profiles.yml").write_text(
        yaml.dump(
            {
                profile_name: {
                    "target": target,
                    "outputs": {target: {"type": type_, "path": path}},
                }
            }
        )
    )


class TestResolveProfile:
    def test_co_located_profiles_yml_wins_over_home(self, tmp_path):
        """Default search prefers <dbt_project>/profiles.yml over ~/.dbt."""
        dbt = tmp_path / "dbt"
        _write_dbt_project(dbt)
        _write_profiles(dbt)

        r = resolve_profile(project_root=tmp_path, dbt_project_dir=dbt)
        assert r is not None
        assert r.profiles_yml == dbt / "profiles.yml"
        assert r.profile == "p"
        assert r.target == "dev"
        assert r.warehouse is not None
        assert r.warehouse.adapter_type == "duckdb"
        assert r.source.startswith("<dbt_project_dir>")

    def test_cli_profiles_dir_override_wins(self, tmp_path):
        """``ProfileOverrides.profiles_dir`` short-circuits everything."""
        dbt = tmp_path / "dbt"
        _write_dbt_project(dbt)
        _write_profiles(dbt, type_="duckdb", path="local.duckdb")

        external = tmp_path / "external"
        _write_profiles(external, type_="snowflake")
        # External profile uses 'snowflake' type — give it the right shape.
        external_yml = yaml.safe_load((external / "profiles.yml").read_text())
        external_yml["p"]["outputs"]["dev"] = {
            "type": "snowflake",
            "account": "acct123",
            "database": "DB",
            "schema": "PUBLIC",
            "warehouse": "WH",
            "role": "R",
        }
        (external / "profiles.yml").write_text(yaml.dump(external_yml))

        r = resolve_profile(
            project_root=tmp_path,
            dbt_project_dir=dbt,
            overrides=ProfileOverrides(profiles_dir=external),
        )
        assert r is not None
        assert r.profiles_yml == external / "profiles.yml"
        assert r.warehouse is not None
        assert r.warehouse.adapter_type == "snowflake"
        assert r.warehouse.identifier == "acct123"
        assert r.source == "CLI --profiles-dir"

    def test_tycoon_yml_dbt_profiles_dir_beats_dbt_project(self, tmp_path):
        """``project_dbt_profiles_dir`` (i.e. tycoon.yml) wins over the
        co-located ``profiles.yml`` when no CLI override is supplied."""
        dbt = tmp_path / "dbt"
        _write_dbt_project(dbt)
        _write_profiles(dbt)  # co-located DuckDB profile

        elsewhere = tmp_path / "elsewhere"
        _write_profiles(elsewhere, type_="duckdb", path="other.duckdb")

        r = resolve_profile(
            project_root=tmp_path,
            dbt_project_dir=dbt,
            project_dbt_profiles_dir=str(elsewhere),
        )
        assert r is not None
        assert r.profiles_yml == elsewhere / "profiles.yml"
        assert r.source.startswith("tycoon.yml")

    def test_env_var_dbt_profiles_dir_used_when_no_other(
        self, tmp_path, monkeypatch
    ):
        """``$DBT_PROFILES_DIR`` is honored after the co-located file."""
        dbt = tmp_path / "dbt"
        _write_dbt_project(dbt)
        # No co-located profiles.yml — only an env-pointed one.
        env_dir = tmp_path / "env"
        _write_profiles(env_dir)

        monkeypatch.setenv("DBT_PROFILES_DIR", str(env_dir))
        # And make sure ~/.dbt isn't accidentally read.
        monkeypatch.setenv("HOME", str(tmp_path / "home"))

        r = resolve_profile(project_root=tmp_path, dbt_project_dir=dbt)
        assert r is not None
        assert r.profiles_yml == env_dir / "profiles.yml"
        assert r.source == "$DBT_PROFILES_DIR"

    def test_returns_none_when_no_profiles_yml_anywhere(
        self, tmp_path, monkeypatch
    ):
        dbt = tmp_path / "dbt"
        _write_dbt_project(dbt)  # dbt_project.yml only
        monkeypatch.delenv("DBT_PROFILES_DIR", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))

        r = resolve_profile(project_root=tmp_path, dbt_project_dir=dbt)
        assert r is None

    def test_profile_override_picks_named_profile(self, tmp_path):
        """``ProfileOverrides.profile`` ignores dbt_project.yml's `profile:`."""
        dbt = tmp_path / "dbt"
        _write_dbt_project(dbt, profile_name="primary")
        # profiles.yml carries two profiles; default would be 'primary'.
        (dbt / "profiles.yml").write_text(
            yaml.dump(
                {
                    "primary": {
                        "target": "dev",
                        "outputs": {"dev": {"type": "duckdb", "path": "p.duckdb"}},
                    },
                    "secondary": {
                        "target": "dev",
                        "outputs": {"dev": {"type": "duckdb", "path": "s.duckdb"}},
                    },
                }
            )
        )
        r = resolve_profile(
            project_root=tmp_path,
            dbt_project_dir=dbt,
            overrides=ProfileOverrides(profile="secondary"),
        )
        assert r is not None
        assert r.profile == "secondary"
        assert r.warehouse is not None
        assert r.warehouse.identifier.endswith("s.duckdb")

    def test_target_override_picks_named_target(self, tmp_path):
        dbt = tmp_path / "dbt"
        _write_dbt_project(dbt)
        (dbt / "profiles.yml").write_text(
            yaml.dump(
                {
                    "p": {
                        "target": "dev",
                        "outputs": {
                            "dev": {"type": "duckdb", "path": "dev.duckdb"},
                            "prod": {"type": "duckdb", "path": "prod.duckdb"},
                        },
                    }
                }
            )
        )
        r = resolve_profile(
            project_root=tmp_path,
            dbt_project_dir=dbt,
            overrides=ProfileOverrides(target="prod"),
        )
        assert r is not None
        assert r.target == "prod"
        assert r.warehouse is not None
        assert r.warehouse.identifier.endswith("prod.duckdb")


class TestDiscoverProfiles:
    def test_lists_all_profiles_with_targets_and_adapters(self, tmp_path):
        f = tmp_path / "profiles.yml"
        f.write_text(
            yaml.dump(
                {
                    "alpha": {
                        "target": "dev",
                        "outputs": {
                            "dev": {"type": "duckdb", "path": "a.duckdb"},
                            "prod": {"type": "duckdb", "path": "ap.duckdb"},
                        },
                    },
                    "beta": {
                        "target": "ci",
                        "outputs": {
                            "ci": {
                                "type": "snowflake",
                                "account": "x",
                                "database": "D",
                                "schema": "S",
                                "warehouse": "W",
                                "role": "R",
                            }
                        },
                    },
                    "config": {"send_anonymous_usage_stats": False},
                }
            )
        )
        out = discover_profiles(f)
        names = sorted(p.name for p in out)
        assert names == ["alpha", "beta"]  # 'config' is filtered

        alpha = next(p for p in out if p.name == "alpha")
        assert sorted(alpha.targets) == ["dev", "prod"]
        assert alpha.default_target == "dev"
        assert alpha.adapter_types == {"dev": "duckdb", "prod": "duckdb"}

        beta = next(p for p in out if p.name == "beta")
        assert beta.adapter_types == {"ci": "snowflake"}


class TestExtractDbtWarehouseTargetCompat:
    """Backwards-compat for callers in init.py / register.py."""

    def test_returns_duckdb_target(self, tmp_path):
        dbt = tmp_path / "dbt"
        _write_dbt_project(dbt)
        _write_profiles(dbt)

        target = extract_dbt_warehouse_target(dbt)
        assert target is not None
        assert target.adapter_type == "duckdb"
        assert target.identifier.endswith("warehouse.duckdb")

    def test_returns_none_when_unresolvable(self, tmp_path):
        dbt = tmp_path / "dbt"
        _write_dbt_project(dbt)
        # No profiles.yml anywhere.
        import os

        old = os.environ.pop("DBT_PROFILES_DIR", None)
        try:
            assert extract_dbt_warehouse_target(dbt) is None
        finally:
            if old is not None:
                os.environ["DBT_PROFILES_DIR"] = old


class TestRedactSecrets:
    def test_redacts_known_secret_keys(self):
        body = {
            "type": "snowflake",
            "account": "acct",
            "user": "u",
            "password": "p4ssw0rd",
            "private_key": "-----BEGIN----",
            "warehouse": "wh",
        }
        out = redact_secrets(body)
        assert out["password"] == "***redacted***"
        assert out["private_key"] == "***redacted***"
        assert out["account"] == "acct"
        assert out["user"] == "u"

    def test_recurses_into_nested_dicts(self):
        body = {"outputs": {"dev": {"token": "xyz", "type": "duckdb"}}}
        out = redact_secrets(body)
        assert out["outputs"]["dev"]["token"] == "***redacted***"
        assert out["outputs"]["dev"]["type"] == "duckdb"
