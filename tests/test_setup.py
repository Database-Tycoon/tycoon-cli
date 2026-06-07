"""Tests for `tycoon setup` / managed project-local `.venv` (#57).

The whole point of this module is that it never creates a real environment:
every subprocess call goes through ``tycoon.venv.subprocess.run``, which we
patch, mirroring the source_installer test pattern.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tycoon.cli import app
from tycoon import venv as venv_mod


def _ok(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


# ---------------------------------------------------------------------------
# Version parsing / range
# ---------------------------------------------------------------------------


class TestVersionHelpers:
    def test_parse_major_minor(self):
        assert venv_mod.parse_python_version("3.13") == (3, 13)

    def test_parse_ignores_patch(self):
        assert venv_mod.parse_python_version("3.13.2") == (3, 13)

    def test_parse_rejects_garbage(self):
        with pytest.raises(ValueError):
            venv_mod.parse_python_version("python3")

    def test_parse_rejects_single_component(self):
        with pytest.raises(ValueError):
            venv_mod.parse_python_version("3")

    @pytest.mark.parametrize(
        "ver,supported",
        [((3, 12), True), ((3, 13), True), ((3, 11), False), ((3, 14), False)],
    )
    def test_is_supported_version(self, ver, supported):
        assert venv_mod.is_supported_version(ver) is supported


# ---------------------------------------------------------------------------
# create_venv — the subprocess-isolated core
# ---------------------------------------------------------------------------


class TestCreateVenv:
    def test_rejects_unsupported_version_without_shelling_out(self, tmp_path):
        with patch("tycoon.venv.subprocess.run") as run:
            result = venv_mod.create_venv(tmp_path, "3.14")
        assert result.ok is False
        assert "supported range" in result.message
        run.assert_not_called()

    def test_errors_when_uv_missing(self, tmp_path):
        with patch("tycoon.venv.find_uv", return_value=None), \
             patch("tycoon.venv.subprocess.run") as run:
            result = venv_mod.create_venv(tmp_path, "3.13")
        assert result.ok is False
        assert "uv is not installed" in result.message
        run.assert_not_called()

    def test_refuses_to_clobber_existing_venv(self, tmp_path):
        (tmp_path / ".venv").mkdir()
        with patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"), \
             patch("tycoon.venv.subprocess.run") as run:
            result = venv_mod.create_venv(tmp_path, "3.13")
        assert result.ok is False
        assert "--force" in result.message
        run.assert_not_called()

    def test_happy_path_creates_pins_and_installs(self, tmp_path):
        with patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"), \
             patch("tycoon.venv.subprocess.run", side_effect=[_ok(), _ok()]) as run:
            result = venv_mod.create_venv(tmp_path, "3.13")

        assert result.ok is True, result.message
        assert result.venv_path == tmp_path / ".venv"
        # .python-version pinned in the project dir.
        assert (tmp_path / ".python-version").read_text() == "3.13\n"
        # Two subprocess calls: `uv venv` then `uv pip install`.
        assert run.call_count == 2
        venv_cmd = run.call_args_list[0].args[0]
        assert venv_cmd[:3] == ["/usr/bin/uv", "venv", "--python"]
        assert "3.13" in venv_cmd
        install_cmd = run.call_args_list[1].args[0]
        assert install_cmd[:3] == ["/usr/bin/uv", "pip", "install"]
        assert "database-tycoon" in install_cmd

    def test_no_install_skips_pip(self, tmp_path):
        with patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"), \
             patch("tycoon.venv.subprocess.run", side_effect=[_ok()]) as run:
            result = venv_mod.create_venv(tmp_path, "3.13", install_spec=None)
        assert result.ok is True
        assert run.call_count == 1  # only `uv venv`

    def test_uv_venv_failure_surfaces_stderr(self, tmp_path):
        with patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"), \
             patch("tycoon.venv.subprocess.run", side_effect=[_ok(1, stderr="no such python")]):
            result = venv_mod.create_venv(tmp_path, "3.13")
        assert result.ok is False
        assert "no such python" in result.message
        # Never got as far as pinning the version.
        assert not (tmp_path / ".python-version").exists()

    def test_install_failure_keeps_venv_but_reports(self, tmp_path):
        with patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"), \
             patch("tycoon.venv.subprocess.run", side_effect=[_ok(), _ok(1, stderr="resolution impossible")]):
            result = venv_mod.create_venv(tmp_path, "3.13")
        assert result.ok is False
        assert "installing" in result.message
        assert "resolution impossible" in result.message
        # The env + pin were still created before the install step failed.
        assert (tmp_path / ".python-version").exists()

    def test_force_recreates_existing(self, tmp_path):
        (tmp_path / ".venv").mkdir()
        with patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"), \
             patch("tycoon.venv.subprocess.run", side_effect=[_ok(), _ok()]) as run:
            result = venv_mod.create_venv(tmp_path, "3.13", force=True)
        assert result.ok is True
        assert run.call_count == 2


# ---------------------------------------------------------------------------
# `tycoon setup` command
# ---------------------------------------------------------------------------


class TestSetupCommand:
    def _bind(self, tmp_path: Path, monkeypatch, *, with_project: bool = True):
        if with_project:
            (tmp_path / "tycoon.yml").write_text(
                "name: test\nversion: 0.1.0\n"
                "database:\n  raw: data/raw.duckdb\n  warehouse: data/warehouse.duckdb\n"
                "sources: {}\n"
            )
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        from tycoon.commands import setup as setup_mod
        from tycoon.config import TycoonConfig

        cfg = TycoonConfig(project_root=tmp_path)
        monkeypatch.setattr(setup_mod, "config", cfg)
        return cfg

    def test_errors_without_project(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch, with_project=False)
        result = cli_runner.invoke(app, ["setup", "--no-prompt"])
        assert result.exit_code == 1
        assert "tycoon init" in (result.stderr or result.output)

    def test_errors_when_uv_missing(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        with patch("tycoon.commands.setup.find_uv", return_value=None):
            result = cli_runner.invoke(app, ["setup", "--no-prompt"])
        assert result.exit_code == 1
        assert "uv is not installed" in (result.stderr or result.output)

    def test_happy_path_invokes_create_venv(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        fake = venv_mod.VenvResult(ok=True, message="Created .venv", venv_path=tmp_path / ".venv")
        with patch("tycoon.commands.setup.find_uv", return_value="/usr/bin/uv"), \
             patch("tycoon.commands.setup.create_venv", return_value=fake) as cv:
            result = cli_runner.invoke(app, ["setup", "--no-prompt", "--python", "3.12"])
        assert result.exit_code == 0, result.output
        cv.assert_called_once()
        # The chosen interpreter is threaded through.
        assert cv.call_args.args[1] == "3.12"
        assert "source .venv/bin/activate" in result.output

    def test_no_install_threads_through(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        fake = venv_mod.VenvResult(ok=True, message="ok", venv_path=tmp_path / ".venv")
        with patch("tycoon.commands.setup.find_uv", return_value="/usr/bin/uv"), \
             patch("tycoon.commands.setup.create_venv", return_value=fake) as cv:
            cli_runner.invoke(app, ["setup", "--no-prompt", "--no-install"])
        assert cv.call_args.kwargs["install_spec"] is None

    def test_failure_exits_nonzero(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        fake = venv_mod.VenvResult(ok=False, message="uv venv failed")
        with patch("tycoon.commands.setup.find_uv", return_value="/usr/bin/uv"), \
             patch("tycoon.commands.setup.create_venv", return_value=fake):
            result = cli_runner.invoke(app, ["setup", "--no-prompt"])
        assert result.exit_code == 1
        assert "uv venv failed" in (result.stderr or result.output)


# ---------------------------------------------------------------------------
# `tycoon doctor --fix`
# ---------------------------------------------------------------------------


class TestDoctorFix:
    def test_fix_warns_when_uv_missing(self, capsys):
        from tycoon.commands import doctor

        with patch("tycoon.venv.find_uv", return_value=None):
            doctor._fix_python_env()
        combined = capsys.readouterr()
        assert "uv isn't installed" in (combined.out + combined.err)

    def test_fix_builds_venv_when_uv_present(self, capsys):
        from tycoon.commands import doctor

        fake = venv_mod.VenvResult(ok=True, message="Created /x/.venv on Python 3.13.")
        with patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"), \
             patch("tycoon.venv.create_venv", return_value=fake) as cv:
            doctor._fix_python_env()
        cv.assert_called_once()
        out = capsys.readouterr().out
        assert "Created" in out
        assert "activate" in out.lower()

    def test_in_range_interpreter_makes_fix_a_noop(self, cli_runner, tmp_path, monkeypatch):
        """The test suite runs on a supported interpreter, so even with --fix
        the repair path must not fire (no uv lookups, no env build)."""
        from tycoon.commands import doctor as doctor_mod
        from tycoon.config import TycoonConfig

        monkeypatch.setattr(doctor_mod, "config", TycoonConfig(project_root=tmp_path))
        with patch("tycoon.commands.doctor._fix_python_env") as fix:
            result = cli_runner.invoke(app, ["doctor", "--fix"])
        assert result.exit_code == 0, result.output
        fix.assert_not_called()
