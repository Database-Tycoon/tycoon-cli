"""Tests for `tycoon register dbt` and `tycoon register rill`."""

from __future__ import annotations

from pathlib import Path

import yaml

from tycoon.cli import app


def _scaffold_tycoon_project(root: Path, name: str = "proj") -> Path:
    """Create a minimal tycoon.yml in `root` and return the yml path."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(exist_ok=True)
    (root / "pyproject.toml").write_text(f'[project]\nname = "{name}"\n')
    yml = root / "tycoon.yml"
    yml.write_text(
        yaml.dump(
            {
                "name": name,
                "version": "0.1.0",
                "database": {
                    "raw": "data/raw.duckdb",
                    "warehouse": "data/warehouse.duckdb",
                },
                "sources": {},
            }
        )
    )
    return yml


def _make_dbt_project(dbt_dir: Path, profile: str, duckdb_path: str) -> None:
    dbt_dir.mkdir(parents=True, exist_ok=True)
    (dbt_dir / "dbt_project.yml").write_text(
        yaml.dump({"name": profile, "profile": profile, "config-version": 2})
    )
    (dbt_dir / "profiles.yml").write_text(
        yaml.dump(
            {
                profile: {
                    "target": "dev",
                    "outputs": {"dev": {"type": "duckdb", "path": duckdb_path}},
                }
            }
        )
    )


def _make_snowflake_dbt_project(
    dbt_dir: Path,
    profile: str,
    account: str,
    database: str = "ANALYTICS",
    schema: str = "public",
) -> None:
    dbt_dir.mkdir(parents=True, exist_ok=True)
    (dbt_dir / "dbt_project.yml").write_text(
        yaml.dump({"name": profile, "profile": profile, "config-version": 2})
    )
    (dbt_dir / "profiles.yml").write_text(
        yaml.dump(
            {
                profile: {
                    "target": "dev",
                    "outputs": {
                        "dev": {
                            "type": "snowflake",
                            "account": account,
                            "user": "me",
                            "password": "***",
                            "database": database,
                            "schema": schema,
                            "warehouse": "COMPUTE_WH",
                            "role": "ANALYST",
                        }
                    },
                }
            }
        )
    )


def _make_bigquery_dbt_project(
    dbt_dir: Path,
    profile: str,
    gcp_project: str,
    dataset: str = "analytics",
) -> None:
    dbt_dir.mkdir(parents=True, exist_ok=True)
    (dbt_dir / "dbt_project.yml").write_text(
        yaml.dump({"name": profile, "profile": profile, "config-version": 2})
    )
    (dbt_dir / "profiles.yml").write_text(
        yaml.dump(
            {
                profile: {
                    "target": "dev",
                    "outputs": {
                        "dev": {
                            "type": "bigquery",
                            "method": "service-account",
                            "project": gcp_project,
                            "dataset": dataset,
                            "keyfile": "/tmp/keyfile.json",
                        }
                    },
                }
            }
        )
    )


def _reload_config(monkeypatch, project_root: Path) -> None:
    """Rebind the module-level `config` singletons so commands see the new project."""
    from tycoon.commands import register as register_mod
    from tycoon.config import TycoonConfig

    cfg = TycoonConfig(project_root=project_root)
    monkeypatch.setattr(register_mod, "config", cfg)


class TestRegisterDbt:

    def test_register_dbt_by_local_path(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        dbt_dir = tmp_path / "proj-dbt"
        _make_dbt_project(dbt_dir, "proj", str(project / "data" / "warehouse.duckdb"))

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "dbt", str(dbt_dir)], input="\n")
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load(yml.read_text())
        assert "dbt_project_dir" in data
        assert data["stack"]["transformation"] == "dbt"
        assert data["stack"]["transformation_managed"] is False

    def test_register_dbt_refuses_nonexistent_path(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "dbt", "/nowhere/does/not/exist"])
        assert result.exit_code != 0

    def test_register_dbt_refuses_dir_without_dbt_project_yml(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        empty = tmp_path / "not-a-dbt"
        empty.mkdir()
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "dbt", str(empty)])
        assert result.exit_code != 0

    def test_register_dbt_prompts_on_overwrite(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        data = yaml.safe_load(yml.read_text())
        data["dbt_project_dir"] = "old_dbt"
        yml.write_text(yaml.dump(data))

        dbt_dir = tmp_path / "proj-dbt"
        _make_dbt_project(dbt_dir, "proj", str(project / "data" / "warehouse.duckdb"))

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)

        # "n" = don't overwrite
        result = cli_runner.invoke(app, ["register", "dbt", str(dbt_dir)], input="n\n")
        assert result.exit_code == 0
        final = yaml.safe_load(yml.read_text())
        assert final["dbt_project_dir"] == "old_dbt"

    def test_register_dbt_offers_warehouse_alignment(self, cli_runner, tmp_path, monkeypatch):
        """If dbt project targets a different DuckDB, offer to adopt it."""
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")

        dbt_dir = tmp_path / "proj-dbt"
        divergent = tmp_path / "elsewhere" / "theirs.duckdb"
        _make_dbt_project(dbt_dir, "proj", str(divergent))

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)

        # First prompt: overwrite? (no existing → no prompt). Warehouse prompt: yes.
        result = cli_runner.invoke(app, ["register", "dbt", str(dbt_dir)], input="y\n")
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load((project / "tycoon.yml").read_text())
        assert data["database"]["warehouse"] == str(divergent)

    def test_register_dbt_persists_profile_flags(self, cli_runner, tmp_path, monkeypatch):
        """`--profiles-dir / --profile / --target` save into tycoon.yml (#18)."""
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        dbt_dir = tmp_path / "proj-dbt"
        _make_dbt_project(dbt_dir, "proj", str(project / "data" / "warehouse.duckdb"))

        # Stage profiles.yml in a non-default sibling dir
        external_profiles = tmp_path / "ci-profiles"
        external_profiles.mkdir()
        (external_profiles / "profiles.yml").write_text(
            yaml.dump(
                {
                    "ci_profile": {
                        "target": "prod",
                        "outputs": {
                            "prod": {
                                "type": "duckdb",
                                "path": str(project / "data" / "warehouse.duckdb"),
                            }
                        },
                    }
                }
            )
        )

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(
            app,
            [
                "register", "dbt", str(dbt_dir),
                "--profiles-dir", str(external_profiles),
                "--profile", "ci_profile",
                "--target", "prod",
            ],
            input="\n",
        )
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load(yml.read_text())
        # Persisted flags
        assert "dbt_profiles_dir" in data
        assert Path(data["dbt_profiles_dir"]).expanduser().resolve() == external_profiles
        assert data["dbt_profile"] == "ci_profile"
        assert data["dbt_target"] == "prod"

    def test_register_dbt_drops_stale_profile_keys_when_unspecified(
        self, cli_runner, tmp_path, monkeypatch
    ):
        """Re-registering without --profile should drop a previously-persisted value."""
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        # Pre-populate stale values
        data = yaml.safe_load(yml.read_text())
        data["dbt_profile"] = "old_profile"
        data["dbt_target"] = "old_target"
        yml.write_text(yaml.dump(data))

        dbt_dir = tmp_path / "proj-dbt"
        _make_dbt_project(dbt_dir, "proj", str(project / "data" / "warehouse.duckdb"))

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        # "y" overwrites the existing dbt_project_dir prompt (none here, so just newline)
        result = cli_runner.invoke(app, ["register", "dbt", str(dbt_dir)], input="\n")
        assert result.exit_code == 0, result.stdout

        final = yaml.safe_load(yml.read_text())
        assert "dbt_profile" not in final
        assert "dbt_target" not in final

    def test_register_dbt_refuses_missing_profiles_dir(
        self, cli_runner, tmp_path, monkeypatch
    ):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        dbt_dir = tmp_path / "proj-dbt"
        _make_dbt_project(dbt_dir, "proj", str(project / "data" / "warehouse.duckdb"))

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(
            app,
            [
                "register", "dbt", str(dbt_dir),
                "--profiles-dir", str(tmp_path / "does-not-exist"),
            ],
        )
        assert result.exit_code != 0

    def test_register_dbt_offers_motherduck_alignment(self, cli_runner, tmp_path, monkeypatch):
        """If dbt project targets md:foo and tycoon warehouse is a local DuckDB, offer to adopt."""
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")

        dbt_dir = tmp_path / "proj-dbt"
        _make_dbt_project(dbt_dir, "proj", "md:theirs")

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)

        result = cli_runner.invoke(app, ["register", "dbt", str(dbt_dir)], input="y\n")
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load((project / "tycoon.yml").read_text())
        assert data["database"]["warehouse"] == "md:theirs"
        assert data["stack"]["warehouse"] == "motherduck"


class TestRegisterDbtCreate:
    """Tests for `tycoon register dbt --create` — bootstrap + register
    in one shot, the recovery path for users who picked Skip on the dbt
    prompt during `tycoon init`."""

    def test_create_bootstraps_at_default_sibling_path(
        self, cli_runner, tmp_path, monkeypatch
    ):
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "dbt", "--create"])
        assert result.exit_code == 0, result.stdout

        # Default sibling path: ../<project_name>-dbt
        sibling = tmp_path / "proj-dbt"
        assert (sibling / "dbt_project.yml").exists()
        assert (sibling / "profiles.yml").exists()

        data = yaml.safe_load(yml.read_text())
        assert "dbt_project_dir" in data
        assert data["stack"]["transformation"] == "dbt"
        # --create marks the project as tycoon-managed (we own it)
        assert data["stack"]["transformation_managed"] is True

    def test_create_with_explicit_path_overrides_default(
        self, cli_runner, tmp_path, monkeypatch
    ):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        custom = tmp_path / "custom-dbt-location"

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(
            app, ["register", "dbt", "--create", str(custom)]
        )
        assert result.exit_code == 0, result.stdout
        assert (custom / "dbt_project.yml").exists()
        assert not (tmp_path / "proj-dbt").exists()

    def test_create_refuses_when_dbt_project_yml_already_exists(
        self, cli_runner, tmp_path, monkeypatch
    ):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        existing = tmp_path / "proj-dbt"
        _make_dbt_project(existing, "proj", str(project / "data" / "warehouse.duckdb"))

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "dbt", "--create"])

        assert result.exit_code != 0
        # Existing project survived — sentinel: dbt_project_dir not registered
        assert "dbt_project_dir" not in yaml.safe_load(
            (project / "tycoon.yml").read_text()
        )

    def test_create_motherduck_warehouse_writes_md_profile(
        self, cli_runner, tmp_path, monkeypatch
    ):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        # Flip the warehouse type to motherduck before registering.
        yml_data = yaml.safe_load((project / "tycoon.yml").read_text())
        yml_data["stack"] = {"warehouse": "motherduck"}
        yml_data["database"]["warehouse"] = "md:proj"
        yml_data["database"]["raw"] = "md:proj_raw"
        (project / "tycoon.yml").write_text(yaml.dump(yml_data))

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "dbt", "--create"])
        assert result.exit_code == 0, result.stdout

        sibling = tmp_path / "proj-dbt"
        profiles = yaml.safe_load((sibling / "profiles.yml").read_text())
        # First (and only) profile in the file
        profile_block = next(iter(profiles.values()))
        dev = profile_block["outputs"]["dev"]
        assert dev["path"] == "md:proj"

    def test_create_bails_on_unsupported_warehouse(
        self, cli_runner, tmp_path, monkeypatch
    ):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        yml_data = yaml.safe_load((project / "tycoon.yml").read_text())
        yml_data["stack"] = {"warehouse": "snowflake"}
        (project / "tycoon.yml").write_text(yaml.dump(yml_data))

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "dbt", "--create"])
        assert result.exit_code != 0
        # No sibling dbt project should have been written
        assert not (tmp_path / "proj-dbt").exists()

    def test_register_without_create_or_source_errors(
        self, cli_runner, tmp_path, monkeypatch
    ):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "dbt"])
        assert result.exit_code != 0


class TestRegisterDbtExternalE2E:
    """End-to-end: scaffold a standalone dbt project, register it with
    custom profile/target flags, then run a real `tycoon data transform
    run` and assert the model materialized with the registered profile.

    Distinct from the persistence tests above (which only check
    tycoon.yml keys) — this one proves the registered config is honored
    by the transform runner.
    """

    def test_external_dbt_project_runs_with_registered_profile(
        self, cli_runner, tmp_path, monkeypatch
    ):
        import duckdb

        # 1. Standalone dbt project at <tmp>/external_dbt with a custom
        #    profile name + non-default target name.
        external_dbt = tmp_path / "external_dbt"
        warehouse_path = tmp_path / "proj" / "data" / "warehouse.duckdb"
        external_dbt.mkdir()
        (external_dbt / "dbt_project.yml").write_text(
            yaml.dump(
                {
                    "name": "extproj",
                    "profile": "ci_profile",
                    "config-version": 2,
                    "model-paths": ["models"],
                }
            )
        )
        models_dir = external_dbt / "models"
        models_dir.mkdir()
        (models_dir / "hello.sql").write_text(
            "{{ config(materialized='table') }}\nselect 42 as the_answer\n"
        )

        # 2. Profiles.yml in a sibling 'ci-profiles/' dir (proves
        #    --profiles-dir is honored, not the default lookup).
        external_profiles = tmp_path / "ci-profiles"
        external_profiles.mkdir()
        (external_profiles / "profiles.yml").write_text(
            yaml.dump(
                {
                    "ci_profile": {
                        "target": "prod",
                        "outputs": {
                            "prod": {
                                "type": "duckdb",
                                "path": str(warehouse_path),
                            }
                        },
                    }
                }
            )
        )

        # 3. Tycoon project + register dbt with all three flags.
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)

        result = cli_runner.invoke(
            app,
            [
                "register", "dbt", str(external_dbt),
                "--profiles-dir", str(external_profiles),
                "--profile", "ci_profile",
                "--target", "prod",
            ],
            input="\n",
        )
        assert result.exit_code == 0, result.stdout

        # 4. Transform commands have their own config singleton — rebind.
        from tycoon.commands import transform as transform_mod
        from tycoon.config import TycoonConfig
        monkeypatch.setattr(
            transform_mod, "config", TycoonConfig(project_root=project)
        )

        # 5. Run transform — proves the persisted profile/target/profiles_dir
        #    are picked up by `_run_dbt`.
        result = cli_runner.invoke(app, ["data", "transform", "run"])
        assert result.exit_code == 0, (
            f"transform run failed:\n--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr if result.stderr_bytes else ''}"
        )

        # 6. Verify the model materialized in the registered warehouse path.
        assert warehouse_path.exists(), "warehouse DB was not created"
        con = duckdb.connect(str(warehouse_path), read_only=True)
        try:
            row = con.execute("SELECT the_answer FROM main.hello").fetchone()
            assert row == (42,), f"hello model not materialized: {row}"
        finally:
            con.close()


class TestExtractDbtWarehouseTarget:
    """v0.1.3 theme #2: structured target extraction across adapters."""

    def test_duckdb_local_path_is_resolved_absolute(self, tmp_path):
        from tycoon.commands.init import _extract_dbt_warehouse_target

        dbt_dir = tmp_path / "dbt"
        _make_dbt_project(dbt_dir, "p", "data/warehouse.duckdb")
        target = _extract_dbt_warehouse_target(dbt_dir)

        assert target is not None
        assert target.adapter_type == "duckdb"
        assert target.identifier.endswith("data/warehouse.duckdb")
        assert Path(target.identifier).is_absolute()
        assert target.tycoon_warehouse_type == "duckdb"

    def test_motherduck_path_is_preserved(self, tmp_path):
        from tycoon.commands.init import _extract_dbt_warehouse_target

        dbt_dir = tmp_path / "dbt"
        _make_dbt_project(dbt_dir, "p", "md:mine")
        target = _extract_dbt_warehouse_target(dbt_dir)

        assert target is not None
        assert target.adapter_type == "duckdb"
        assert target.identifier == "md:mine"
        assert target.tycoon_warehouse_type == "motherduck"

    def test_snowflake_exposes_account_and_details(self, tmp_path):
        from tycoon.commands.init import _extract_dbt_warehouse_target

        dbt_dir = tmp_path / "dbt"
        _make_snowflake_dbt_project(dbt_dir, "p", account="acme-us-east-1")
        target = _extract_dbt_warehouse_target(dbt_dir)

        assert target is not None
        assert target.adapter_type == "snowflake"
        assert target.identifier == "acme-us-east-1"
        assert target.display.startswith("snowflake://acme-us-east-1")
        assert target.details["database"] == "ANALYTICS"
        assert target.details["warehouse"] == "COMPUTE_WH"
        assert target.tycoon_warehouse_type == "snowflake"

    def test_bigquery_exposes_project_and_dataset(self, tmp_path):
        from tycoon.commands.init import _extract_dbt_warehouse_target

        dbt_dir = tmp_path / "dbt"
        _make_bigquery_dbt_project(dbt_dir, "p", gcp_project="my-gcp-proj")
        target = _extract_dbt_warehouse_target(dbt_dir)

        assert target is not None
        assert target.adapter_type == "bigquery"
        assert target.identifier == "my-gcp-proj"
        assert target.details["dataset"] == "analytics"
        assert target.tycoon_warehouse_type == "bigquery"

    def test_unknown_adapter_surfaces_raw_type(self, tmp_path):
        from tycoon.commands.init import _extract_dbt_warehouse_target

        dbt_dir = tmp_path / "dbt"
        dbt_dir.mkdir()
        (dbt_dir / "dbt_project.yml").write_text(
            yaml.dump({"name": "p", "profile": "p", "config-version": 2})
        )
        (dbt_dir / "profiles.yml").write_text(
            yaml.dump(
                {
                    "p": {
                        "target": "dev",
                        "outputs": {
                            "dev": {"type": "databricks", "host": "x.databricks.com"}
                        },
                    }
                }
            )
        )
        target = _extract_dbt_warehouse_target(dbt_dir)
        assert target is not None
        assert target.adapter_type == "databricks"
        assert target.tycoon_warehouse_type is None  # unknown to tycoon

    def test_explicit_profiles_dir_override(self, tmp_path):
        """`profiles_dir` arg should win over the co-located profiles.yml."""
        from tycoon.commands.init import _extract_dbt_warehouse_target

        dbt_dir = tmp_path / "dbt"
        # Co-located profile points at "wrong.duckdb"
        _make_dbt_project(dbt_dir, "p", str(tmp_path / "wrong.duckdb"))

        # External profile points at "right.duckdb"
        external = tmp_path / "external_profiles"
        external.mkdir()
        (external / "profiles.yml").write_text(
            yaml.dump(
                {
                    "p": {
                        "target": "dev",
                        "outputs": {"dev": {"type": "duckdb", "path": str(tmp_path / "right.duckdb")}},
                    }
                }
            )
        )

        target = _extract_dbt_warehouse_target(dbt_dir, profiles_dir=external)
        assert target is not None
        assert "right.duckdb" in target.identifier
        assert "wrong.duckdb" not in target.identifier

    def test_explicit_profile_name_override(self, tmp_path):
        """`profile_name` arg should win over dbt_project.yml's `profile:` field."""
        from tycoon.commands.init import _extract_dbt_warehouse_target

        dbt_dir = tmp_path / "dbt"
        dbt_dir.mkdir()
        # dbt_project.yml says profile=primary
        (dbt_dir / "dbt_project.yml").write_text(
            yaml.dump({"name": "p", "profile": "primary", "config-version": 2})
        )
        # profiles.yml has BOTH primary and secondary
        (dbt_dir / "profiles.yml").write_text(
            yaml.dump(
                {
                    "primary": {
                        "target": "dev",
                        "outputs": {"dev": {"type": "duckdb", "path": str(tmp_path / "primary.duckdb")}},
                    },
                    "secondary": {
                        "target": "dev",
                        "outputs": {"dev": {"type": "duckdb", "path": str(tmp_path / "secondary.duckdb")}},
                    },
                }
            )
        )

        target = _extract_dbt_warehouse_target(dbt_dir, profile_name="secondary")
        assert target is not None
        assert "secondary.duckdb" in target.identifier

    def test_explicit_target_name_override(self, tmp_path):
        """`target_name` arg should win over the profile's `target:` field."""
        from tycoon.commands.init import _extract_dbt_warehouse_target

        dbt_dir = tmp_path / "dbt"
        dbt_dir.mkdir()
        (dbt_dir / "dbt_project.yml").write_text(
            yaml.dump({"name": "p", "profile": "p", "config-version": 2})
        )
        (dbt_dir / "profiles.yml").write_text(
            yaml.dump(
                {
                    "p": {
                        "target": "dev",
                        "outputs": {
                            "dev": {"type": "duckdb", "path": str(tmp_path / "dev.duckdb")},
                            "prod": {"type": "duckdb", "path": str(tmp_path / "prod.duckdb")},
                        },
                    }
                }
            )
        )

        target = _extract_dbt_warehouse_target(dbt_dir, target_name="prod")
        assert target is not None
        assert "prod.duckdb" in target.identifier

    def test_missing_profile_returns_none(self, tmp_path):
        from tycoon.commands.init import _extract_dbt_warehouse_target

        dbt_dir = tmp_path / "dbt"
        dbt_dir.mkdir()
        # No dbt_project.yml at all
        assert _extract_dbt_warehouse_target(dbt_dir) is None


class TestRegisterDbtCloudAlignment:
    """v0.1.3 theme #2: Snowflake / BigQuery alignment offers to update
    ``stack.warehouse`` but leaves ``database.warehouse`` alone."""

    def test_snowflake_alignment_updates_stack_warehouse(
        self, cli_runner, tmp_path, monkeypatch
    ):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")

        dbt_dir = tmp_path / "proj-dbt"
        _make_snowflake_dbt_project(dbt_dir, "proj", account="acme-us-east-1")

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)

        result = cli_runner.invoke(app, ["register", "dbt", str(dbt_dir)], input="y\n")
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load((project / "tycoon.yml").read_text())
        assert data["stack"]["warehouse"] == "snowflake"
        # database.warehouse untouched — still the local DuckDB default
        assert data["database"]["warehouse"] == "data/warehouse.duckdb"

    def test_bigquery_alignment_updates_stack_warehouse(
        self, cli_runner, tmp_path, monkeypatch
    ):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")

        dbt_dir = tmp_path / "proj-dbt"
        _make_bigquery_dbt_project(dbt_dir, "proj", gcp_project="my-gcp-proj")

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)

        result = cli_runner.invoke(app, ["register", "dbt", str(dbt_dir)], input="y\n")
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load((project / "tycoon.yml").read_text())
        assert data["stack"]["warehouse"] == "bigquery"
        assert data["database"]["warehouse"] == "data/warehouse.duckdb"

    def test_snowflake_no_change_if_types_already_aligned(
        self, cli_runner, tmp_path, monkeypatch
    ):
        """When stack.warehouse is already snowflake, no prompt — the value stays."""
        project = tmp_path / "proj"
        yml_path = _scaffold_tycoon_project(project, "proj")
        # Pre-set the stack to snowflake so alignment is already true.
        data = yaml.safe_load(yml_path.read_text())
        data.setdefault("stack", {})["warehouse"] = "snowflake"
        yml_path.write_text(yaml.dump(data))

        dbt_dir = tmp_path / "proj-dbt"
        _make_snowflake_dbt_project(dbt_dir, "proj", account="acme-us-east-1")

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)

        result = cli_runner.invoke(app, ["register", "dbt", str(dbt_dir)])
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load((project / "tycoon.yml").read_text())
        assert data["stack"]["warehouse"] == "snowflake"

    def test_snowflake_account_mismatch_warns(
        self, cli_runner, tmp_path, monkeypatch
    ):
        """When tycoon.yml records a warehouse_connection.account that
        differs from the dbt profile's account, we warn (non-fatal)."""
        project = tmp_path / "proj"
        yml_path = _scaffold_tycoon_project(project, "proj")
        data = yaml.safe_load(yml_path.read_text())
        data["warehouse_connection"] = {"account": "other-account"}
        yml_path.write_text(yaml.dump(data))

        dbt_dir = tmp_path / "proj-dbt"
        _make_snowflake_dbt_project(dbt_dir, "proj", account="acme-us-east-1")

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)

        result = cli_runner.invoke(app, ["register", "dbt", str(dbt_dir)], input="y\n")
        assert result.exit_code == 0, result.stdout
        assert "other-account" in result.stdout
        assert "acme-us-east-1" in result.stdout


class TestRegisterWarehouse:

    def test_register_warehouse_local(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)

        # Inputs: overwrite=y, choice=local, path=data/elsewhere.duckdb
        result = cli_runner.invoke(
            app,
            ["register", "warehouse"],
            input="y\nlocal\ndata/elsewhere.duckdb\n",
        )
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load(yml.read_text())
        assert data["database"]["warehouse"] == "data/elsewhere.duckdb"
        assert data["stack"]["warehouse"] == "duckdb"

    def test_register_warehouse_motherduck(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        monkeypatch.delenv("MOTHERDUCK_TOKEN", raising=False)

        # Inputs: overwrite=y, choice=cloud, md name=myproj
        result = cli_runner.invoke(
            app,
            ["register", "warehouse"],
            input="y\ncloud\nmyproj\n",
        )
        assert result.exit_code == 0, result.stdout
        assert "MOTHERDUCK_TOKEN" in result.stdout  # warning surfaced

        data = yaml.safe_load(yml.read_text())
        assert data["database"]["warehouse"] == "md:myproj"
        assert data["stack"]["warehouse"] == "motherduck"

    def test_register_warehouse_non_interactive_local(self, cli_runner, tmp_path, monkeypatch):
        """`--type duckdb --path ./foo.duckdb --no-prompt` runs without prompts (#19)."""
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        # Wipe pre-existing warehouse so we don't hit the overwrite prompt
        data = yaml.safe_load(yml.read_text())
        data["database"] = {"raw": "data/raw.duckdb", "warehouse": ""}
        yml.write_text(yaml.dump(data))

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(
            app,
            [
                "register", "warehouse",
                "--type", "duckdb",
                "--path", "data/custom.duckdb",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0, result.stdout
        final = yaml.safe_load(yml.read_text())
        assert final["database"]["warehouse"] == "data/custom.duckdb"
        assert final["stack"]["warehouse"] == "duckdb"

    def test_register_warehouse_non_interactive_motherduck(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        data = yaml.safe_load(yml.read_text())
        data["database"] = {"raw": "data/raw.duckdb", "warehouse": ""}
        yml.write_text(yaml.dump(data))

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(
            app,
            [
                "register", "warehouse",
                "--type", "motherduck",
                "--catalog", "my_demo",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0, result.stdout
        final = yaml.safe_load(yml.read_text())
        assert final["database"]["warehouse"] == "md:my_demo"
        assert final["stack"]["warehouse"] == "motherduck"

    def test_register_warehouse_no_prompt_requires_type(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "warehouse", "--no-prompt"])
        assert result.exit_code != 0

    def test_register_warehouse_no_prompt_motherduck_requires_catalog(
        self, cli_runner, tmp_path, monkeypatch
    ):
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        data = yaml.safe_load(yml.read_text())
        data["database"]["warehouse"] = ""
        yml.write_text(yaml.dump(data))
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(
            app,
            ["register", "warehouse", "--type", "motherduck", "--no-prompt"],
        )
        assert result.exit_code != 0

    def test_register_warehouse_force_overrides_existing(self, cli_runner, tmp_path, monkeypatch):
        """`--force` skips the overwrite prompt for an existing warehouse."""
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        # Pre-populate a warehouse value that would normally trigger the prompt.
        data = yaml.safe_load(yml.read_text())
        data["database"]["warehouse"] = "data/old.duckdb"
        yml.write_text(yaml.dump(data))
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(
            app,
            [
                "register", "warehouse",
                "--type", "duckdb",
                "--path", "data/new.duckdb",
                "--force",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0, result.stdout
        final = yaml.safe_load(yml.read_text())
        assert final["database"]["warehouse"] == "data/new.duckdb"

    def test_register_warehouse_unknown_type_errors(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(
            app,
            ["register", "warehouse", "--type", "snowflake", "--no-prompt"],
        )
        assert result.exit_code != 0

    def test_register_warehouse_prompts_on_overwrite(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        data = yaml.safe_load(yml.read_text())
        data["database"]["warehouse"] = "data/old.duckdb"
        yml.write_text(yaml.dump(data))
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)

        # Answer 'n' to overwrite — no change.
        result = cli_runner.invoke(app, ["register", "warehouse"], input="n\n")
        assert result.exit_code == 0
        final = yaml.safe_load(yml.read_text())
        assert final["database"]["warehouse"] == "data/old.duckdb"


class TestRegisterRill:

    def test_register_rill_by_local_path(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        yml = _scaffold_tycoon_project(project, "proj")
        rill_dir = tmp_path / "proj-rill"
        rill_dir.mkdir()
        (rill_dir / "rill.yaml").write_text("compiler: rillv1\n")

        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "rill", str(rill_dir)])
        assert result.exit_code == 0, result.stdout

        data = yaml.safe_load(yml.read_text())
        assert "rill_dir" in data
        assert data["stack"]["bi"] == "rill"
        assert data["stack"]["bi_managed"] is False

    def test_register_rill_refuses_dir_without_rill_yaml(self, cli_runner, tmp_path, monkeypatch):
        project = tmp_path / "proj"
        _scaffold_tycoon_project(project, "proj")
        empty = tmp_path / "not-a-rill"
        empty.mkdir()
        monkeypatch.chdir(project)
        _reload_config(monkeypatch, project)
        result = cli_runner.invoke(app, ["register", "rill", str(empty)])
        assert result.exit_code != 0
