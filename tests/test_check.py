"""Tests for the `tycoon doctor` command."""

from __future__ import annotations

from datetime import UTC

from tycoon.cli import app


class TestDoctorCommand:
    def test_doctor_runs_without_crash(self, cli_runner):
        """doctor should run and produce output (may exit 0 or 1 depending on env)."""
        result = cli_runner.invoke(app, ["doctor"])
        # It should produce output regardless of pass/fail
        assert len(result.stdout) > 0

    def test_doctor_help(self, cli_runner):
        """--help flag should be accepted."""
        result = cli_runner.invoke(app, ["doctor", "--help"])
        assert result.exit_code == 0


class TestMotherDuckAuthProbe:
    """Regression coverage for issue #3: doctor must recognize OAuth, not
    only the MOTHERDUCK_TOKEN env var."""

    def test_env_token_wins(self, monkeypatch, capsys):
        from tycoon.commands import doctor

        monkeypatch.setenv("MOTHERDUCK_TOKEN", "fake-token")
        doctor._check_motherduck_auth()
        out = capsys.readouterr().out
        assert "token (env" in out

    def test_oauth_cache_detected(self, monkeypatch, tmp_path, capsys):
        from tycoon.commands import doctor

        fake_cache = tmp_path / "stored_tokens"
        fake_cache.write_text("not-empty")
        monkeypatch.delenv("MOTHERDUCK_TOKEN", raising=False)
        monkeypatch.setattr(
            doctor,
            "_MOTHERDUCK_CACHE_CANDIDATES",
            (fake_cache,),
        )
        doctor._check_motherduck_auth()
        out = capsys.readouterr().out
        assert "OAuth" in out

    def test_no_auth_errors_out(self, monkeypatch, tmp_path, capsys):
        from tycoon.commands import doctor

        monkeypatch.delenv("MOTHERDUCK_TOKEN", raising=False)
        monkeypatch.setattr(
            doctor,
            "_MOTHERDUCK_CACHE_CANDIDATES",
            (tmp_path / "does_not_exist",),
        )
        doctor._check_motherduck_auth()
        captured = capsys.readouterr()
        assert "not configured" in (captured.out + captured.err)

    def test_empty_cache_file_not_counted(self, monkeypatch, tmp_path, capsys):
        from tycoon.commands import doctor

        empty = tmp_path / "stored_tokens"
        empty.touch()
        monkeypatch.delenv("MOTHERDUCK_TOKEN", raising=False)
        monkeypatch.setattr(
            doctor,
            "_MOTHERDUCK_CACHE_CANDIDATES",
            (empty,),
        )
        doctor._check_motherduck_auth()
        captured = capsys.readouterr()
        assert "not configured" in (captured.out + captured.err)


class TestPythonVersionCheck:
    """`_check_python_version` enforces the supported interpreter range
    (>=3.12,<3.14), the blind spot that hid #55 until `transform run` failed."""

    def test_supported_version_passes(self, capsys):
        from tycoon.commands import doctor

        doctor._check_python_version((3, 13))
        out = capsys.readouterr().out
        assert "Python 3.13 is in the supported range" in out

    def test_lower_bound_inclusive(self, capsys):
        from tycoon.commands import doctor

        doctor._check_python_version((3, 12))
        out = capsys.readouterr().out
        assert "supported range" in out

    def test_too_old_errors(self, capsys):
        from tycoon.commands import doctor

        doctor._check_python_version((3, 11))
        captured = capsys.readouterr()
        assert "too old" in (captured.out + captured.err)

    def test_too_new_errors_with_dbt_context(self, capsys):
        from tycoon.commands import doctor

        doctor._check_python_version((3, 14))
        captured = capsys.readouterr()
        combined = captured.out + captured.err
        assert "too new" in combined
        # The remediation points at the managed-venv direction (#57).
        assert "tycoon setup --python 3.13" in " ".join(combined.split())

    def test_defaults_to_running_interpreter(self, capsys):
        """With no argument it inspects the live interpreter — and since the
        test suite runs on a supported interpreter, it should pass."""
        from tycoon.commands import doctor

        doctor._check_python_version()
        out = capsys.readouterr().out
        assert "supported range" in out


class TestProjectVenvCheck:
    """`_check_project_venv` (gh-265) reports plainly whether this project
    has picked up its own `.venv` (gh-262+) and whether tycoon is actually
    running from it, a runtime filesystem fact, not a schema field."""

    def _patch_config(self, monkeypatch, tmp_path):
        from tycoon.commands import doctor
        from tycoon.config import TycoonConfig

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        cfg = TycoonConfig(project_root=tmp_path)
        monkeypatch.setattr(doctor, "config", cfg)
        return cfg

    def test_reports_success_when_running_from_project_venv(self, monkeypatch, tmp_path, capsys):
        import sys

        from tycoon.commands import doctor

        self._patch_config(monkeypatch, tmp_path)
        venv = tmp_path / ".venv"
        venv.mkdir()
        monkeypatch.setattr(sys, "prefix", str(venv.resolve()))

        doctor._check_project_venv()
        out = capsys.readouterr().out
        assert "using its own .venv" in out

    def test_warns_when_venv_exists_but_tycoon_not_running_from_it(self, monkeypatch, tmp_path, capsys):
        """Review must-fix: the old check was "`.venv` exists", not "tycoon
        is executing from this project's `.venv`" (the actual gh-265
        premise). An empty `.venv` (a failed/partial setup, or `tycoon
        setup` leaving one beside an existing pyproject.toml, gh-262 review)
        used to report OK while tycoon kept running from the ambient
        interpreter, with no warning before the next catalog-source run
        failed "not installed" (gh-263)."""
        import sys

        from tycoon.commands import doctor

        self._patch_config(monkeypatch, tmp_path)
        venv = tmp_path / ".venv"
        venv.mkdir()
        # The running interpreter is NOT this project's `.venv` — a
        # different path entirely, same as the real ambient-interpreter case.
        monkeypatch.setattr(sys, "prefix", str((tmp_path / "somewhere-else").resolve()))

        doctor._check_project_venv()
        captured = capsys.readouterr()
        # Rich hard-wraps a long temp-dir path with no word boundary, so
        # normalizing via split()/join() (used elsewhere for wrapped output)
        # would corrupt the path itself here — check un-normalized instead.
        combined = captured.out + captured.err
        assert ".venv" in combined
        assert "running from" in combined
        assert "activate" in combined.lower()

    def test_warns_when_venv_missing(self, monkeypatch, tmp_path, capsys):
        from tycoon.commands import doctor

        self._patch_config(monkeypatch, tmp_path)

        doctor._check_project_venv()
        captured = capsys.readouterr()
        combined = " ".join((captured.out + captured.err).split())
        assert "doesn't have its own .venv yet" in combined
        assert "tycoon setup" in combined

    def test_doctor_cmd_skips_venv_check_outside_project(self, cli_runner, tmp_path, monkeypatch):
        """Should-fix: outside any project this used to warn 'run tycoon
        setup' right above a 'tycoon.yml not found, run tycoon init' panel —
        `setup` itself refuses without a tycoon.yml, so the first piece of
        advice was a dead end. Gated behind `config.has_project_file`, same
        as the stack checks below it."""
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(app, ["doctor"])

        assert "doesn't have its own .venv yet" not in (result.stdout + (result.stderr or ""))


class TestDoctorObservabilityCheck:
    """`_check_observability` reports capture-hook health."""

    def _patch_config(self, monkeypatch, tmp_path):
        from tycoon.commands import doctor
        from tycoon.config import TycoonConfig

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "tycoon.yml").write_text("name: test\nsources: {}\n")
        cfg = TycoonConfig(project_root=tmp_path)
        monkeypatch.setattr(doctor, "config", cfg)
        return cfg

    def test_no_metadata_db_reports_hint(self, monkeypatch, tmp_path, capsys):
        from tycoon.commands import doctor

        self._patch_config(monkeypatch, tmp_path)
        doctor._check_observability()
        out = capsys.readouterr().out
        assert "metadata DB not yet created" in out

    def test_empty_metadata_db_reports_hint(self, monkeypatch, tmp_path, capsys):
        import duckdb

        from tycoon.commands import doctor
        from tycoon.observability import ensure_schema, metadata_db_path

        cfg = self._patch_config(monkeypatch, tmp_path)
        meta = metadata_db_path(cfg.root)
        ensure_schema(meta)
        duckdb.connect(str(meta)).close()  # ensure file exists after schema call

        doctor._check_observability()
        out = capsys.readouterr().out
        assert "no runs captured yet" in out

    def test_populated_metadata_db_reports_counts(self, monkeypatch, tmp_path, capsys):
        from datetime import datetime

        import duckdb

        from tycoon.commands import doctor
        from tycoon.observability import ensure_schema, metadata_db_path

        cfg = self._patch_config(monkeypatch, tmp_path)
        meta = metadata_db_path(cfg.root)
        ensure_schema(meta)

        now = datetime.now(tz=UTC)
        con = duckdb.connect(str(meta))
        try:
            con.execute(
                "INSERT INTO dlt_runs VALUES (?, ?, ?, ?, ?, ?)",
                ["s", "load-1", 0, now, "h", now],
            )
            con.execute(
                "INSERT INTO dbt_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ["inv-1", "build", now, 1.0, True, 1, 0, 0, 0, "1.9.0", "dev", now],
            )
        finally:
            con.close()

        doctor._check_observability()
        out = capsys.readouterr().out
        assert "1 dlt load(s)" in out
        assert "1 dbt run(s)" in out
        # Terminal wrapping may split the command hint across lines
        normalized = " ".join(out.split())
        assert "tycoon data history" in normalized


class TestDoctorLayerCoverage:
    """`_check_layer_coverage` reports source -> staging-model coverage."""

    def _patch_config(self, monkeypatch, tmp_path, *, sources_yaml: str, transformation: str = "dbt"):
        import yaml

        from tycoon.commands import doctor
        from tycoon.config import TycoonConfig

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        body = {
            "name": "test",
            "stack": {"transformation": transformation},
            "sources": yaml.safe_load(sources_yaml) or {},
        }
        (tmp_path / "tycoon.yml").write_text(yaml.dump(body))
        cfg = TycoonConfig(project_root=tmp_path)
        monkeypatch.setattr(doctor, "config", cfg)
        return cfg

    def _write_manifest(self, dbt_dir, nodes):
        import json

        target = dbt_dir / "target"
        target.mkdir(parents=True, exist_ok=True)
        (target / "manifest.json").write_text(json.dumps({"nodes": nodes}))

    def test_silent_when_transformation_none(self, monkeypatch, tmp_path, capsys):
        from tycoon.commands import doctor

        self._patch_config(
            monkeypatch,
            tmp_path,
            sources_yaml="pokeapi:\n  type: rest_api\n  schema: raw_pokeapi\n  config: {}\n",
            transformation="none",
        )
        doctor._check_layer_coverage()
        out = capsys.readouterr().out
        assert out == ""  # nothing should be emitted

    def test_silent_when_no_sources(self, monkeypatch, tmp_path, capsys):
        from tycoon.commands import doctor

        self._patch_config(monkeypatch, tmp_path, sources_yaml="{}")
        doctor._check_layer_coverage()
        assert capsys.readouterr().out == ""

    def test_silent_when_no_manifest(self, monkeypatch, tmp_path, capsys):
        """Don't double-report — other rows already nudge toward dbt compile."""
        from tycoon.commands import doctor

        self._patch_config(
            monkeypatch,
            tmp_path,
            sources_yaml="pokeapi:\n  type: rest_api\n  schema: raw_pokeapi\n  config: {}\n",
        )
        doctor._check_layer_coverage()
        assert capsys.readouterr().out == ""

    def test_reports_success_when_every_source_has_staging(self, monkeypatch, tmp_path, capsys):
        from tycoon.commands import doctor

        cfg = self._patch_config(
            monkeypatch,
            tmp_path,
            sources_yaml="pokeapi:\n  type: rest_api\n  schema: raw_pokeapi\n  config: {}\n",
        )
        self._write_manifest(
            cfg.dbt_project_dir,
            {
                "model.p.stg_pokeapi__pokemon": {
                    "resource_type": "model",
                    "name": "stg_pokeapi__pokemon",
                    "schema": "main",
                    "original_file_path": "models/staging/stg_pokeapi__pokemon.sql",
                    "config": {"meta": {}},
                }
            },
        )
        doctor._check_layer_coverage()
        out = capsys.readouterr().out
        assert "every source" in out
        assert "1" in out

    def test_warns_when_source_has_no_staging(self, monkeypatch, tmp_path, capsys):
        from tycoon.commands import doctor

        cfg = self._patch_config(
            monkeypatch,
            tmp_path,
            sources_yaml=(
                "pokeapi:\n  type: rest_api\n  schema: raw_pokeapi\n  config: {}\n"
                "orphan:\n  type: rest_api\n  schema: raw_orphan\n  config: {}\n"
            ),
        )
        self._write_manifest(
            cfg.dbt_project_dir,
            {
                "model.p.stg_pokeapi__pokemon": {
                    "resource_type": "model",
                    "name": "stg_pokeapi__pokemon",
                    "schema": "main",
                    "original_file_path": "models/staging/stg_pokeapi__pokemon.sql",
                    "config": {"meta": {}},
                }
            },
        )
        doctor._check_layer_coverage()
        out = capsys.readouterr().out
        assert "orphan" in out
        assert "pokeapi" not in out.replace("stg_pokeapi", "")  # only the unsourced one
