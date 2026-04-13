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
