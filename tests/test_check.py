"""Tests for the `tycoon doctor` command."""

from __future__ import annotations

from pathlib import Path

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
