"""Tests for local scheduled runs (#48).

Backend tests patch `current_platform` so both launchd and systemd paths run on
any host, and patch `subprocess.run` so no real launchctl/systemctl is invoked
— while exercising the real unit-file rendering against a temp HOME.
"""

from __future__ import annotations

import plistlib
from unittest.mock import MagicMock, patch

import pytest

from tycoon import schedule as sched
from tycoon.cli import app


def _spec(tmp_path, **kw):
    base = dict(
        name="daily-refresh",
        args=["data", "run-all", "--notify"],
        hour=4,
        minute=30,
        cadence="daily",
        project_root=tmp_path / "proj",
    )
    base.update(kw)
    return sched.ScheduleSpec(**base)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    @pytest.mark.parametrize("name", ["daily", "daily-refresh", "x", "a1-b2"])
    def test_valid_names(self, name):
        sched.validate_name(name)  # no raise

    @pytest.mark.parametrize("name", ["Daily", "has space", "-leading", "with_underscore", ""])
    def test_invalid_names(self, name):
        with pytest.raises(sched.ScheduleError):
            sched.validate_name(name)

    def test_parse_time_ok(self):
        assert sched.parse_time("04:00") == (4, 0)
        assert sched.parse_time("23:59") == (23, 59)

    @pytest.mark.parametrize("bad", ["4pm", "24:00", "12:60", "9", "12:5"])
    def test_parse_time_bad(self, bad):
        with pytest.raises(sched.ScheduleError):
            sched.parse_time(bad)


# ---------------------------------------------------------------------------
# Unit-file rendering
# ---------------------------------------------------------------------------


class TestRendering:
    def test_launchd_daily_interval(self, tmp_path):
        pl = plistlib.loads(sched.render_launchd_plist(_spec(tmp_path), home=tmp_path))
        assert pl["Label"] == "com.databasetycoon.daily-refresh"
        assert pl["StartCalendarInterval"] == {"Hour": 4, "Minute": 30}
        assert pl["ProgramArguments"][-3:] == ["data", "run-all", "--notify"]
        assert pl["RunAtLoad"] is False

    def test_launchd_hourly_interval(self, tmp_path):
        pl = plistlib.loads(sched.render_launchd_plist(_spec(tmp_path, cadence="hourly"), home=tmp_path))
        assert pl["StartCalendarInterval"] == {"Minute": 30}

    def test_launchd_weekly_interval(self, tmp_path):
        pl = plistlib.loads(
            sched.render_launchd_plist(_spec(tmp_path, cadence="weekly", weekday=3), home=tmp_path)
        )
        assert pl["StartCalendarInterval"]["Weekday"] == 3

    def test_systemd_oncalendar_daily(self, tmp_path):
        timer = sched.render_systemd_timer(_spec(tmp_path))
        assert "OnCalendar=*-*-* 04:30:00" in timer
        assert "Persistent=true" in timer

    def test_systemd_oncalendar_weekly(self, tmp_path):
        timer = sched.render_systemd_timer(_spec(tmp_path, cadence="weekly", weekday=1))
        assert "OnCalendar=Mon *-*-* 04:30:00" in timer

    def test_systemd_service_has_workdir_and_exec(self, tmp_path):
        svc = sched.render_systemd_service(_spec(tmp_path), home=tmp_path)
        assert f"WorkingDirectory={tmp_path / 'proj'}" in svc
        assert "ExecStart=" in svc and "data run-all --notify" in svc


# ---------------------------------------------------------------------------
# add / list / remove — launchd backend
# ---------------------------------------------------------------------------


class TestLaunchdBackend:
    def test_add_writes_plist_and_loads(self, tmp_path):
        with patch("tycoon.schedule.current_platform", return_value="darwin"), \
             patch("tycoon.schedule.subprocess.run", return_value=MagicMock(returncode=0)) as run:
            msg = sched.add(_spec(tmp_path), home=tmp_path)

        plist = sched.launchd_plist_path("daily-refresh", tmp_path)
        assert plist.exists()
        assert sched.log_dir("daily-refresh", tmp_path).exists()
        assert "launchd" in msg
        # launchctl load was invoked.
        loaded = [c.args[0] for c in run.call_args_list if "load" in c.args[0]]
        assert loaded

    def test_list_globs_managed_plists(self, tmp_path):
        with patch("tycoon.schedule.current_platform", return_value="darwin"), \
             patch("tycoon.schedule.subprocess.run", return_value=MagicMock(returncode=0)):
            sched.add(_spec(tmp_path, name="a"), home=tmp_path)
            sched.add(_spec(tmp_path, name="b"), home=tmp_path)
            # An unrelated plist must not show up.
            (sched.launch_agents_dir(tmp_path) / "com.other.thing.plist").write_text("x")
            names = sched.list_schedules(home=tmp_path)
        assert names == ["a", "b"]

    def test_remove_unloads_and_deletes(self, tmp_path):
        with patch("tycoon.schedule.current_platform", return_value="darwin"), \
             patch("tycoon.schedule.subprocess.run", return_value=MagicMock(returncode=0)):
            sched.add(_spec(tmp_path), home=tmp_path)
            plist = sched.launchd_plist_path("daily-refresh", tmp_path)
            assert plist.exists()
            sched.remove("daily-refresh", home=tmp_path)
            assert not plist.exists()

    def test_remove_missing_raises(self, tmp_path):
        with patch("tycoon.schedule.current_platform", return_value="darwin"):
            with pytest.raises(sched.ScheduleError):
                sched.remove("ghost", home=tmp_path)

    def test_add_scheduler_failure_raises(self, tmp_path):
        with patch("tycoon.schedule.current_platform", return_value="darwin"), \
             patch("tycoon.schedule.subprocess.run", return_value=MagicMock(returncode=1, stderr="boom", stdout="")):
            with pytest.raises(sched.ScheduleError):
                sched.add(_spec(tmp_path), home=tmp_path)


# ---------------------------------------------------------------------------
# add / list / remove — systemd backend
# ---------------------------------------------------------------------------


class TestSystemdBackend:
    def test_add_writes_timer_and_service(self, tmp_path):
        with patch("tycoon.schedule.current_platform", return_value="linux"), \
             patch("tycoon.schedule.subprocess.run", return_value=MagicMock(returncode=0)) as run:
            sched.add(_spec(tmp_path), home=tmp_path)
        unit_dir = sched.systemd_user_dir(tmp_path)
        assert (unit_dir / "tycoon-daily-refresh.timer").exists()
        assert (unit_dir / "tycoon-daily-refresh.service").exists()
        enabled = [c.args[0] for c in run.call_args_list if "enable" in c.args[0]]
        assert enabled

    def test_list_and_remove_round_trip(self, tmp_path):
        with patch("tycoon.schedule.current_platform", return_value="linux"), \
             patch("tycoon.schedule.subprocess.run", return_value=MagicMock(returncode=0)):
            sched.add(_spec(tmp_path), home=tmp_path)
            assert sched.list_schedules(home=tmp_path) == ["daily-refresh"]
            sched.remove("daily-refresh", home=tmp_path)
            assert sched.list_schedules(home=tmp_path) == []


# ---------------------------------------------------------------------------
# Unsupported platform
# ---------------------------------------------------------------------------


def test_unsupported_platform_errors(tmp_path):
    with patch("tycoon.schedule.current_platform", return_value="win32"):
        with pytest.raises(sched.ScheduleError, match="Windows"):
            sched.add(_spec(tmp_path), home=tmp_path)


# ---------------------------------------------------------------------------
# `tycoon schedule` command
# ---------------------------------------------------------------------------


class TestScheduleCommand:
    def _bind(self, tmp_path, monkeypatch):
        (tmp_path / "tycoon.yml").write_text(
            "name: t\nversion: 0.1.0\n"
            "database:\n  raw: data/raw.duckdb\n  warehouse: data/warehouse.duckdb\n"
            "sources: {}\n"
        )
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\n')
        from tycoon.commands import schedule as sched_cmd
        from tycoon.config import TycoonConfig

        monkeypatch.setattr(sched_cmd, "config", TycoonConfig(project_root=tmp_path))

    def test_add_requires_project(self, cli_runner, tmp_path, monkeypatch):
        # Bind config to an empty dir with no tycoon.yml.
        from tycoon.commands import schedule as sched_cmd
        from tycoon.config import TycoonConfig

        empty = tmp_path / "empty"
        empty.mkdir()
        monkeypatch.setattr(sched_cmd, "config", TycoonConfig(project_root=empty))
        result = cli_runner.invoke(app, ["schedule", "add", "daily-refresh"])
        assert result.exit_code == 1
        assert "tycoon init" in (result.stderr or result.output)

    def test_add_bad_cadence_exits_2(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["schedule", "add", "x", "--cadence", "monthly"])
        assert result.exit_code == 2

    def test_add_bad_time_exits_2(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["schedule", "add", "x", "--at", "9pm"])
        assert result.exit_code == 2

    def test_add_happy_path(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        with patch("tycoon.schedule.list_schedules", return_value=[]), \
             patch("tycoon.schedule.add", return_value="Scheduled 'nightly' via launchd.") as add:
            result = cli_runner.invoke(
                app,
                ["schedule", "add", "nightly", "--command", "data run-all", "--at", "02:15", "--notify"],
            )
        assert result.exit_code == 0, result.output
        spec = add.call_args.args[0]
        assert spec.name == "nightly"
        assert spec.hour == 2 and spec.minute == 15
        assert "--notify" in spec.args

    def test_add_duplicate_without_force_exits_1(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        with patch("tycoon.schedule.list_schedules", return_value=["nightly"]):
            result = cli_runner.invoke(app, ["schedule", "add", "nightly"])
        assert result.exit_code == 1
        assert "--force" in (result.stderr or result.output)

    def test_list_empty(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        with patch("tycoon.schedule.list_schedules", return_value=[]):
            result = cli_runner.invoke(app, ["schedule", "list"])
        assert result.exit_code == 0
        assert "No tycoon schedules" in result.output

    def test_status_missing_exits_1(self, cli_runner, tmp_path, monkeypatch):
        self._bind(tmp_path, monkeypatch)
        with patch("tycoon.schedule.list_schedules", return_value=[]):
            result = cli_runner.invoke(app, ["schedule", "status", "ghost"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# doctor schedules row
# ---------------------------------------------------------------------------


class TestDoctorSchedulesRow:
    def test_reports_count(self, capsys):
        from tycoon.commands import doctor

        with patch("tycoon.schedule.list_schedules", return_value=["a", "b"]):
            doctor._check_schedules()
        out = capsys.readouterr().out
        assert "2 installed" in out

    def test_reports_none(self, capsys):
        from tycoon.commands import doctor

        with patch("tycoon.schedule.list_schedules", return_value=[]):
            doctor._check_schedules()
        out = capsys.readouterr().out
        assert "none installed" in out


class TestAddCommandPrefixStrip:
    """The `add` CLI command should tolerate a redundant leading `tycoon`."""

    def test_strips_leading_tycoon_from_command(self, cli_runner, tmp_path):
        captured = {}

        def fake_add(spec, **_kwargs):
            captured["args"] = spec.args
            return "installed"

        with patch("tycoon.commands.schedule.config") as cfg, \
             patch("tycoon.commands.schedule.sched.list_schedules", return_value=[]), \
             patch("tycoon.commands.schedule.sched.add", side_effect=fake_add):
            cfg.has_project_file = True
            cfg.root = tmp_path
            result = cli_runner.invoke(
                app, ["schedule", "add", "daily-refresh", "--command", "tycoon data run-all"]
            )

        assert result.exit_code == 0, result.output
        assert captured["args"] == ["data", "run-all"]

    def test_keeps_command_without_tycoon_prefix(self, cli_runner, tmp_path):
        captured = {}

        def fake_add(spec, **_kwargs):
            captured["args"] = spec.args
            return "installed"

        with patch("tycoon.commands.schedule.config") as cfg, \
             patch("tycoon.commands.schedule.sched.list_schedules", return_value=[]), \
             patch("tycoon.commands.schedule.sched.add", side_effect=fake_add):
            cfg.has_project_file = True
            cfg.root = tmp_path
            result = cli_runner.invoke(
                app, ["schedule", "add", "daily-refresh", "--command", "data run-all"]
            )

        assert result.exit_code == 0, result.output
        assert captured["args"] == ["data", "run-all"]
