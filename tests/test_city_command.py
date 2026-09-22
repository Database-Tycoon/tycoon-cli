"""`tycoon city` — registration, the unimportable-renderer path, and argv construction.

The renderer ships inside this distribution, so it cannot be missing in a
healthy install. What still matters is that importing it stays lazy — no other
command should pay duckdb and sqlglot at startup — and that if the import does
fail, a damaged install reports one diagnosable line rather than a traceback.
"""

from __future__ import annotations

import builtins
import subprocess
import sys
from pathlib import Path

import pytest

from tycoon.cli import app
from tycoon.commands import city


class TestCityRegistration:
    """The command exists and costs nothing to register."""

    def test_city_listed_in_root_help(self, cli_runner):
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "city" in result.stdout

    def test_city_help_exits_zero(self, cli_runner):
        result = cli_runner.invoke(app, ["city", "--help"])
        assert result.exit_code == 0

    def test_city_help_does_not_advertise_an_install_step(self, cli_runner):
        """There is no `city` extra; help must not send the user to install one."""
        result = cli_runner.invoke(app, ["city", "--help"])
        assert "[city]" not in result.stdout

    def test_cli_imports_without_the_addon(self):
        """The CLI's startup must not depend on tycoon_city being importable.

        Checked in a SUBPROCESS: the renderer's own suite imports
        tycoon_city into this pytest process (rewired 2026-08-10), so
        in-process sys.modules can no longer witness the CLI's startup
        behaviour."""
        code = "import sys, tycoon.cli; sys.exit(1 if 'tycoon_city' in sys.modules else 0)"
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        assert proc.returncode == 0, f"tycoon.cli imported tycoon_city at startup\n{proc.stderr}"

    def test_city_module_does_not_import_tycoon_city_at_module_scope(self):
        source = Path(city.__file__).read_text()
        module_scope = [ln for ln in source.splitlines() if ln.startswith(("import ", "from "))]
        assert not any("tycoon_city" in ln for ln in module_scope), module_scope


class TestRendererUnimportable:
    """A renderer that will not import is one diagnosable line and a non-zero exit."""

    @pytest.fixture
    def broken_renderer(self, monkeypatch):
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "tycoon_city" or name.startswith("tycoon_city."):
                raise ImportError(f"No module named {name!r}")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        monkeypatch.delitem(sys.modules, "tycoon_city", raising=False)
        monkeypatch.delitem(sys.modules, "tycoon_city.webserve", raising=False)

    def test_exit_code_is_non_zero(self, cli_runner, broken_renderer):
        result = cli_runner.invoke(app, ["city"])
        assert result.exit_code != 0

    def test_message_reports_the_underlying_error(self, cli_runner, broken_renderer):
        result = cli_runner.invoke(app, ["city"])
        # Rich wraps at the console width, so compare without whitespace.
        combined = "".join(((result.stdout or "") + (result.stderr or "")).split())
        assert "cityrendererunavailable" in combined
        assert "tycoon_city" in combined, "the real import error must survive to the user"

    def test_message_does_not_advertise_an_extra(self, cli_runner, broken_renderer):
        """Reinstalling helps here; installing a `[city]` extra that does not exist does not."""
        result = cli_runner.invoke(app, ["city"])
        combined = "".join(((result.stdout or "") + (result.stderr or "")).split())
        assert "[city]" not in combined

    def test_no_traceback(self, cli_runner, broken_renderer):
        result = cli_runner.invoke(app, ["city"])
        combined = (result.stdout or "") + (result.stderr or "")
        assert "Traceback" not in combined
        assert "ModuleNotFoundError" not in combined
        assert "ImportError" not in combined


class TestProjectRootWalkUp:
    """Root resolution is local to this module — see the docstring in city.py."""

    def test_finds_tycoon_yml(self, tmp_path, monkeypatch):
        (tmp_path / "tycoon.yml").write_text("")
        nested = tmp_path / "a" / "b"
        nested.mkdir(parents=True)
        monkeypatch.chdir(nested)
        assert city._project_root() == tmp_path.resolve()

    def test_falls_back_to_pyproject(self, tmp_path, monkeypatch):
        (tmp_path / "pyproject.toml").write_text("")
        nested = tmp_path / "a"
        nested.mkdir()
        monkeypatch.chdir(nested)
        assert city._project_root() == tmp_path.resolve()

    def test_tycoon_yml_wins_over_a_nearer_pyproject_ancestor(self, tmp_path, monkeypatch):
        (tmp_path / "tycoon.yml").write_text("")
        nested = tmp_path / "sub"
        nested.mkdir()
        (nested / "pyproject.toml").write_text("")
        monkeypatch.chdir(nested)
        # The nearest marker wins; the point is the walk stops at the first hit.
        assert city._project_root() == nested.resolve()

    def test_does_not_import_tycoon_config(self):
        source = Path(city.__file__).read_text()
        assert "tycoon.config" not in [ln.strip() for ln in source.splitlines() if ln.startswith("from ")]
        module_scope = [ln for ln in source.splitlines() if ln.startswith(("import ", "from "))]
        assert not any("tycoon.config" in ln for ln in module_scope), module_scope


class TestServeInvocation:
    """When the add-on is present, we call its real entry point correctly."""

    @pytest.fixture
    def fake_serve(self, monkeypatch):
        calls: list[list[str]] = []

        def _serve(argv):
            calls.append(argv)
            return 0

        fake_webserve = type(sys)("tycoon_city.webserve")
        fake_webserve.main = _serve
        fake_pkg = type(sys)("tycoon_city")
        fake_pkg.webserve = fake_webserve
        monkeypatch.setitem(sys.modules, "tycoon_city", fake_pkg)
        monkeypatch.setitem(sys.modules, "tycoon_city.webserve", fake_webserve)
        return calls

    def test_defaults_to_the_project_root(self, cli_runner, fake_serve, tmp_path, monkeypatch):
        (tmp_path / "tycoon.yml").write_text("")
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(app, ["city"])
        assert result.exit_code == 0
        assert fake_serve[0][0] == str(tmp_path.resolve())

    def test_passes_port_and_host(self, cli_runner, fake_serve, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(app, ["city", "--port", "9111", "--host", "0.0.0.0"])
        assert result.exit_code == 0
        argv = fake_serve[0]
        assert argv[argv.index("--port") + 1] == "9111"
        assert argv[argv.index("--host") + 1] == "0.0.0.0"

    def test_explicit_path_overrides_the_walk_up(self, cli_runner, fake_serve, tmp_path, monkeypatch):
        db = tmp_path / "warehouse.duckdb"
        db.write_text("")
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(app, ["city", "--path", str(db)])
        assert result.exit_code == 0
        assert fake_serve[0][0] == str(db)

    def test_relative_path_named_demo_is_not_the_demo_command(self, cli_runner, fake_serve, tmp_path, monkeypatch):
        """`webserve.main` dispatches argv[0] == "demo" before argparse runs.

        A user whose project directory is called `demo` must get their own data,
        not the built-in demo catalog. An absolute path can never collide.
        """
        demo_dir = tmp_path / "demo"
        demo_dir.mkdir()
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(app, ["city", "--path", "demo"])
        assert result.exit_code == 0
        assert fake_serve[0][0] != "demo"
        assert fake_serve[0][0] == str(demo_dir.resolve())

    def test_md_catalog_is_passed_through_unresolved(self, cli_runner, fake_serve, tmp_path, monkeypatch):
        """An md: catalog is a URI — resolving it would corrupt it into a path."""
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(app, ["city", "--path", "md:my_db"])
        assert result.exit_code == 0
        assert fake_serve[0][0] == "md:my_db"

    def test_md_share_url_is_passed_through_unresolved(self, cli_runner, fake_serve, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cli_runner.invoke(app, ["city", "--path", "md:_share/sales/abc-123"])
        assert fake_serve[0][0] == "md:_share/sales/abc-123"

    def test_optional_flags_are_omitted_when_unset(self, cli_runner, fake_serve, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cli_runner.invoke(app, ["city"])
        argv = fake_serve[0]
        assert "--dist" not in argv
        assert "--pricing" not in argv

    def test_serve_exit_code_is_propagated(self, cli_runner, monkeypatch, tmp_path):
        fake_webserve = type(sys)("tycoon_city.webserve")
        fake_webserve.main = lambda argv: 1
        fake_pkg = type(sys)("tycoon_city")
        fake_pkg.webserve = fake_webserve
        monkeypatch.setitem(sys.modules, "tycoon_city", fake_pkg)
        monkeypatch.setitem(sys.modules, "tycoon_city.webserve", fake_webserve)
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(app, ["city"])
        assert result.exit_code == 1
