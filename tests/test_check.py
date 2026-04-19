"""Tests for the `tycoon doctor` command."""

from __future__ import annotations


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
        from datetime import datetime, timezone

        import duckdb

        from tycoon.commands import doctor
        from tycoon.observability import ensure_schema, metadata_db_path

        cfg = self._patch_config(monkeypatch, tmp_path)
        meta = metadata_db_path(cfg.root)
        ensure_schema(meta)

        now = datetime.now(tz=timezone.utc)
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
