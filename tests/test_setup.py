"""Tests for `tycoon setup` / managed project-local `.venv` (#57).

Most of this module never creates a real environment: every subprocess call
goes through ``tycoon.venv.subprocess.run``, which we patch, mirroring the
source_installer test pattern. ``TestCreateVenvRealUv`` is the deliberate
exception, see its docstring.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tycoon import venv as venv_mod
from tycoon.cli import app


def _ok(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


def _subprocess_side_effect(tmp_path: Path, *results: MagicMock):
    """Simulate ``subprocess.run`` across create_venv's uv calls.

    Mocking ``subprocess.run`` means nothing ever actually creates
    ``.venv`` the way a real ``uv sync`` would, and ``create_venv`` now
    checks ``target.exists()`` after a successful sync (gh-270 review), so
    tests need that side effect simulated, not just a canned return value.
    """
    calls = iter(results)

    def _run(cmd, **kwargs):
        result = next(calls)
        if "sync" in cmd and result.returncode == 0:
            (tmp_path / ".venv").mkdir(exist_ok=True)
        return result

    return _run


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
        with patch("tycoon.venv.find_uv", return_value=None), patch("tycoon.venv.subprocess.run") as run:
            result = venv_mod.create_venv(tmp_path, "3.13")
        assert result.ok is False
        assert "uv is not installed" in result.message
        run.assert_not_called()

    def test_refuses_to_clobber_existing_venv(self, tmp_path):
        (tmp_path / ".venv").mkdir()
        with patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"), patch("tycoon.venv.subprocess.run") as run:
            result = venv_mod.create_venv(tmp_path, "3.13")
        assert result.ok is False
        assert "--force" in result.message
        run.assert_not_called()

    def test_happy_path_creates_pins_syncs_and_adds(self, tmp_path):
        with (
            patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"),
            patch("tycoon.venv.subprocess.run", side_effect=_subprocess_side_effect(tmp_path, _ok(), _ok())) as run,
        ):
            result = venv_mod.create_venv(tmp_path, "3.13")

        assert result.ok is True, result.message
        assert result.venv_path == tmp_path / ".venv"
        # .python-version pinned in the project dir.
        assert (tmp_path / ".python-version").read_text() == "3.13\n"
        # pyproject.toml seeded with no dependencies, install_spec is
        # always applied afterward via `uv add`, default included.
        pyproject = (tmp_path / "pyproject.toml").read_text()
        assert 'name = "' in pyproject
        assert "database-tycoon" not in pyproject
        assert run.call_count == 2
        sync_cmd = run.call_args_list[0].args[0]
        assert sync_cmd == ["/usr/bin/uv", "--project", str(tmp_path), "sync", "--python", "3.13"]
        add_cmd = run.call_args_list[1].args[0]
        assert add_cmd == ["/usr/bin/uv", "--project", str(tmp_path), "add", "--python", "3.13", "database-tycoon"]

    def test_existing_pyproject_is_left_alone_but_still_gets_the_dependency(self, tmp_path):
        """Regression: an existing pyproject.toml used to make the default
        install a silent no-op that still reported success (gh-270 review).
        The file's other content is untouched, but the dependency now lands
        via `uv add` regardless."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "hand-written"\ndependencies = []\n')
        with (
            patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"),
            patch("tycoon.venv.subprocess.run", side_effect=_subprocess_side_effect(tmp_path, _ok(), _ok())) as run,
        ):
            result = venv_mod.create_venv(tmp_path, "3.13")
        assert result.ok is True
        assert run.call_count == 2
        add_cmd = run.call_args_list[1].args[0]
        assert "database-tycoon" in add_cmd
        # name = "hand-written" is preserved, seeding never ran.
        assert 'name = "hand-written"' in (tmp_path / "pyproject.toml").read_text()

    def test_no_install_skips_add_entirely(self, tmp_path):
        with (
            patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"),
            patch("tycoon.venv.subprocess.run", side_effect=_subprocess_side_effect(tmp_path, _ok())) as run,
        ):
            result = venv_mod.create_venv(tmp_path, "3.13", install_spec=None)
        assert result.ok is True
        assert run.call_count == 1  # only `uv sync`, no `uv add` at all
        assert "database-tycoon" not in (tmp_path / "pyproject.toml").read_text()

    def test_custom_install_spec_via_uv_add_editable(self, tmp_path):
        with (
            patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"),
            patch("tycoon.venv.subprocess.run", side_effect=_subprocess_side_effect(tmp_path, _ok(), _ok())) as run,
        ):
            result = venv_mod.create_venv(tmp_path, "3.13", install_spec="-e /repo/tycoon-cli")
        assert result.ok is True
        assert run.call_count == 2
        add_cmd = run.call_args_list[1].args[0]
        assert add_cmd == [
            "/usr/bin/uv",
            "--project",
            str(tmp_path),
            "add",
            "--python",
            "3.13",
            "--editable",
            "/repo/tycoon-cli",
        ]

    def test_editable_spec_expands_user_home(self, tmp_path):
        with (
            patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"),
            patch("tycoon.venv.subprocess.run", side_effect=_subprocess_side_effect(tmp_path, _ok(), _ok())) as run,
            patch("tycoon.venv.Path.expanduser", return_value=Path("/Users/me/Projects/tycoon-cli")),
        ):
            venv_mod.create_venv(tmp_path, "3.13", install_spec="-e ~/Projects/tycoon-cli")
        add_cmd = run.call_args_list[1].args[0]
        assert add_cmd[-1] == "/Users/me/Projects/tycoon-cli"

    def test_bare_local_path_is_not_forced_editable(self, tmp_path):
        """Regression: a wheel/sdist path (or any bare local path without an
        explicit `-e`) used to be force-classified `--editable`, which uv
        rejects for a non-source-tree path. uv classifies it itself now."""
        with (
            patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"),
            patch("tycoon.venv.subprocess.run", side_effect=_subprocess_side_effect(tmp_path, _ok(), _ok())) as run,
        ):
            venv_mod.create_venv(tmp_path, "3.13", install_spec="./dist/x.whl")
        add_cmd = run.call_args_list[1].args[0]
        assert "--editable" not in add_cmd
        assert add_cmd[-1] == "./dist/x.whl"

    def test_pinned_version_spec_uses_plain_uv_add(self, tmp_path):
        with (
            patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"),
            patch("tycoon.venv.subprocess.run", side_effect=_subprocess_side_effect(tmp_path, _ok(), _ok())) as run,
        ):
            venv_mod.create_venv(tmp_path, "3.13", install_spec="database-tycoon==0.2.2")
        add_cmd = run.call_args_list[1].args[0]
        assert add_cmd == [
            "/usr/bin/uv",
            "--project",
            str(tmp_path),
            "add",
            "--python",
            "3.13",
            "database-tycoon==0.2.2",
        ]

    def test_uv_sync_failure_surfaces_stderr(self, tmp_path):
        with (
            patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"),
            patch("tycoon.venv.subprocess.run", side_effect=[_ok(1, stderr="no such python")]),
        ):
            result = venv_mod.create_venv(tmp_path, "3.13")
        assert result.ok is False
        assert "no such python" in result.message
        # The pin and pyproject.toml are prerequisites `uv sync` reads, so
        # they're written before the call, and left in place on failure.
        assert (tmp_path / ".python-version").exists()
        assert (tmp_path / "pyproject.toml").exists()

    def test_sync_success_but_venv_missing_is_not_claimed_as_success(self, tmp_path):
        """Regression: UV_PROJECT_ENVIRONMENT or a [tool.uv.workspace] root
        can redirect where uv actually builds the environment. A successful
        `uv sync` used to be trusted blindly (gh-270 review)."""
        with (
            patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"),
            patch("tycoon.venv.subprocess.run", side_effect=[_ok()]),
        ):
            result = venv_mod.create_venv(tmp_path, "3.13", install_spec=None)
        assert result.ok is False
        assert "doesn't exist" in result.message

    def test_install_failure_keeps_venv_but_reports(self, tmp_path):
        with (
            patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"),
            patch(
                "tycoon.venv.subprocess.run",
                side_effect=_subprocess_side_effect(tmp_path, _ok(), _ok(1, stderr="resolution impossible")),
            ),
        ):
            result = venv_mod.create_venv(tmp_path, "3.13", install_spec="-e /repo/tycoon-cli")
        assert result.ok is False
        assert "installing" in result.message
        assert "resolution impossible" in result.message
        # The env + pin were still created before the `uv add` step failed.
        assert (tmp_path / ".python-version").exists()

    def test_force_passes_upgrade_instead_of_deleting(self, tmp_path):
        """Regression: `--force` used to `shutil.rmtree` `.venv` and unlink
        `uv.lock` directly, which crashed on a symlinked or plain-file
        `.venv` and deleted the lockfile before confirming the rebuild would
        succeed (gh-270 review). `uv sync --upgrade` reconciles in place."""
        (tmp_path / ".venv").mkdir()
        (tmp_path / "uv.lock").write_text("existing lock")
        with (
            patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"),
            patch("tycoon.venv.subprocess.run", side_effect=[_ok(), _ok()]) as run,
        ):
            result = venv_mod.create_venv(tmp_path, "3.13", force=True)
        assert result.ok is True
        sync_cmd = run.call_args_list[0].args[0]
        assert "--upgrade" in sync_cmd
        # Nothing was deleted up front.
        assert (tmp_path / "uv.lock").read_text() == "existing lock"

    def test_force_on_non_directory_venv_fails_gracefully(self, tmp_path):
        """A symlink or plain file named `.venv` used to crash `shutil.rmtree`
        with an unhandled OSError. Now it's uv's own (handled) failure."""
        (tmp_path / ".venv").write_text("not a directory")
        with (
            patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"),
            patch(
                "tycoon.venv.subprocess.run",
                side_effect=[_ok(1, stderr="expected directory but found a file")],
            ),
        ):
            result = venv_mod.create_venv(tmp_path, "3.13", force=True)
        assert result.ok is False
        assert "expected directory but found a file" in result.message


# ---------------------------------------------------------------------------
# create_venv, real, unmocked uv (CONTRIBUTING.md: "Testing for upgrade
# safety", at least one real integration test per subprocess entry point,
# not just mocked command-shape assertions)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(venv_mod.find_uv() is None, reason="uv not on PATH")
class TestCreateVenvRealUv:
    def test_plain_file_venv_is_a_graceful_failure(self, tmp_path):
        (tmp_path / ".venv").write_text("not a directory")
        result = venv_mod.create_venv(tmp_path, "3.13", force=True, install_spec=None)
        assert result.ok is False
        assert "directory" in result.message.lower()

    def test_existing_pyproject_with_unrelated_dep_still_gets_the_spec(self, tmp_path):
        """The gh-270 regression this whole layer of tests exists for: an
        existing pyproject.toml used to make the default install silently
        no-op. Uses a light install_spec, not the real database-tycoon, to
        keep this fast."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "existing"\nversion = "0.1.0"\n'
            'requires-python = ">=3.12,<3.14"\ndependencies = ["iniconfig"]\n'
        )
        result = venv_mod.create_venv(tmp_path, "3.13", install_spec="packaging")
        assert result.ok is True, result.message
        pyproject = (tmp_path / "pyproject.toml").read_text()
        assert "packaging" in pyproject
        assert "iniconfig" in pyproject  # pre-existing dependency untouched
        venv_python = tmp_path / ".venv" / "bin" / "python"
        assert subprocess.run([str(venv_python), "-c", "import packaging"], check=False).returncode == 0

    def test_explicit_python_flag_outranks_uv_python_env_var(self, tmp_path, monkeypatch):
        monkeypatch.setenv("UV_PYTHON", "3.12")
        result = venv_mod.create_venv(tmp_path, "3.13", install_spec=None)
        assert result.ok is True, result.message
        venv_python = tmp_path / ".venv" / "bin" / "python"
        version_out = subprocess.run(
            [str(venv_python), "-c", "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        assert version_out == "3.13"


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
        with (
            patch("tycoon.commands.setup.find_uv", return_value="/usr/bin/uv"),
            patch("tycoon.commands.setup.create_venv", return_value=fake) as cv,
        ):
            result = cli_runner.invoke(app, ["setup", "--no-prompt", "--python", "3.12"])
        assert result.exit_code == 0, result.output
        cv.assert_called_once()
        # The chosen interpreter is threaded through.
        assert cv.call_args.args[1] == "3.12"
        assert "source .venv/bin/activate" in result.output

    def test_no_install_threads_through(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        fake = venv_mod.VenvResult(ok=True, message="ok", venv_path=tmp_path / ".venv")
        with (
            patch("tycoon.commands.setup.find_uv", return_value="/usr/bin/uv"),
            patch("tycoon.commands.setup.create_venv", return_value=fake) as cv,
        ):
            cli_runner.invoke(app, ["setup", "--no-prompt", "--no-install"])
        assert cv.call_args.kwargs["install_spec"] is None

    def test_failure_exits_nonzero(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        fake = venv_mod.VenvResult(ok=False, message="uv venv failed")
        with (
            patch("tycoon.commands.setup.find_uv", return_value="/usr/bin/uv"),
            patch("tycoon.commands.setup.create_venv", return_value=fake),
        ):
            result = cli_runner.invoke(app, ["setup", "--no-prompt"])
        assert result.exit_code == 1
        assert "uv venv failed" in (result.stderr or result.output)


# ---------------------------------------------------------------------------
# `tycoon doctor --fix`
# ---------------------------------------------------------------------------


class TestDoctorFix:
    def _bind_project(self, tmp_path, monkeypatch):
        from tycoon.commands import doctor as doctor_mod
        from tycoon.config import TycoonConfig

        (tmp_path / "tycoon.yml").write_text("name: test\nversion: 0.1.0\nsources: {}\n")
        monkeypatch.setattr(doctor_mod, "config", TycoonConfig(project_root=tmp_path))

    def test_fix_warns_without_a_project(self, capsys):
        """Regression: `doctor --fix` used to call create_venv with whatever
        `_find_project_root` returned with no guard, unlike `setup`, which
        refuses outside a project. Outside one, it should refuse too, not
        seed a pyproject.toml/.venv into some unrelated directory (gh-270
        review)."""
        from tycoon.commands import doctor

        with patch("tycoon.venv.create_venv") as cv:
            doctor._fix_python_env()
        cv.assert_not_called()
        combined = capsys.readouterr()
        assert "no tycoon.yml" in (combined.out + combined.err).lower()

    def test_fix_warns_when_uv_missing(self, tmp_path, monkeypatch, capsys):
        from tycoon.commands import doctor

        self._bind_project(tmp_path, monkeypatch)
        with patch("tycoon.venv.find_uv", return_value=None):
            doctor._fix_python_env()
        combined = capsys.readouterr()
        assert "uv isn't installed" in (combined.out + combined.err)

    def test_fix_builds_venv_when_uv_present(self, tmp_path, monkeypatch, capsys):
        from tycoon.commands import doctor

        self._bind_project(tmp_path, monkeypatch)
        fake = venv_mod.VenvResult(ok=True, message="Created /x/.venv on Python 3.13.")
        with (
            patch("tycoon.venv.find_uv", return_value="/usr/bin/uv"),
            patch("tycoon.venv.create_venv", return_value=fake) as cv,
        ):
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
