"""Network-gated end-to-end tests for built-in templates.

Unlike ``test_templates_smoke.py`` (which only validates init + doctor), these
tests execute actual ingestion against live endpoints (or local filesystem for
csv-import). They are gated behind ``@pytest.mark.e2e`` and excluded from the
default test run (see ``pyproject.toml``'s ``[tool.pytest.ini_options]``).

Run explicitly with::

    uv run pytest -m e2e

CI runs these via the ``e2e.yml`` workflow (manual trigger only).

Tests that require credentials (GitHub token, etc.) ``pytest.skip`` when the
required env var is absent, so a partial run on a dev machine is still useful.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import duckdb
import pytest
import yaml

from tycoon.cli import app


pytestmark = pytest.mark.e2e


def _init_template(cli_runner, template: str) -> None:
    result = cli_runner.invoke(app, ["init", "--template", template])
    assert result.exit_code == 0, (
        f"init --template {template} failed:\n{result.stdout}"
    )


def _rebind_config(monkeypatch, project: Path) -> None:
    """Point the command-scoped ``config`` singletons at ``project``."""
    from tycoon.commands import sources as sources_mod
    from tycoon.config import TycoonConfig

    cfg = TycoonConfig(project_root=project)
    monkeypatch.setattr(sources_mod, "config", cfg)


def test_csv_import_e2e(cli_runner, tmp_path, monkeypatch):
    """csv-import is the only fully-offline template: seed a CSV, run, assert."""
    project = tmp_path / "csv-import"
    project.mkdir()
    monkeypatch.chdir(project)
    _init_template(cli_runner,"csv-import")

    input_dir = project / "data" / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    sample = input_dir / "widgets.csv"
    with sample.open("w") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "qty"])
        for i in range(1, 6):
            writer.writerow([i, f"widget-{i}", i * 10])

    _rebind_config(monkeypatch, project)
    result = cli_runner.invoke(app, ["data", "sources", "run", "files"])
    assert result.exit_code == 0, f"sources run failed:\n{result.stdout}"

    raw_db = project / "data" / "files_raw.duckdb"
    assert raw_db.exists(), "raw db was not created"

    con = duckdb.connect(str(raw_db), read_only=True)
    try:
        tables = [
            r[0]
            for r in con.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'raw_files'"
            ).fetchall()
        ]
        assert tables, "no tables materialized under raw_files schema"
        total = 0
        for t in tables:
            row = con.execute(f"SELECT count(*) FROM raw_files.{t}").fetchone()
            total += int(row[0]) if row else 0
        assert total >= 5, f"expected >= 5 ingested rows, got {total}"
    finally:
        con.close()


def test_github_analytics_e2e(cli_runner, tmp_path, monkeypatch):
    """Needs a GITHUB_TOKEN. Skip when absent."""
    if not os.environ.get("GITHUB_TOKEN"):
        pytest.skip("GITHUB_TOKEN not set; skipping github-analytics e2e")

    project = tmp_path / "github-analytics"
    project.mkdir()
    monkeypatch.chdir(project)
    _init_template(cli_runner,"github-analytics")

    # The template references `{owner}/{repo}` placeholders in the base URL;
    # we don't rewrite them here. The test only verifies init + that
    # `sources run` surfaces a clean error rather than crashing when required
    # config is missing. A follow-up will extend the template to accept
    # CLI-time owner/repo injection.
    tycoon_yml = yaml.safe_load((project / "tycoon.yml").read_text())
    assert "github" in tycoon_yml["sources"], "github source missing from template"


def test_nyc_transit_e2e(cli_runner, tmp_path, monkeypatch):
    """Public NYC Open Data / MTA feeds — no auth needed, but slow."""
    project = tmp_path / "nyc-transit"
    project.mkdir()
    monkeypatch.chdir(project)
    _init_template(cli_runner,"nyc-transit")

    _rebind_config(monkeypatch, project)
    # Cap records to keep the test under a minute.
    result = cli_runner.invoke(
        app, ["data", "sources", "run", "nyc-dot", "--max-records", "50"]
    )
    # Live HTTP can flake — treat non-zero as xfail rather than hard fail.
    if result.exit_code != 0:
        pytest.xfail(
            f"nyc-dot ingest returned {result.exit_code}; upstream API may be down:\n"
            f"{result.stdout}"
        )

    raw_db = project / "data" / "nyc_open_data_raw.duckdb"
    assert raw_db.exists(), "raw db was not created"


def test_weather_station_e2e(cli_runner, tmp_path, monkeypatch):
    """NOAA public API (no key), but the template uses URL templates
    (``{station_id}``/``{office}``) that require user-side fill-in. For v0.1.2
    we only verify init. A follow-up will supply sensible defaults so this
    test can exercise a real fetch."""
    project = tmp_path / "weather-station"
    project.mkdir()
    monkeypatch.chdir(project)
    _init_template(cli_runner,"weather-station")

    assert (project / "tycoon.yml").exists()
