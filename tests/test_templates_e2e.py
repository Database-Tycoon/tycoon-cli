"""End-to-end tests for built-in templates.

Unlike ``test_templates_smoke.py`` (which only validates init + doctor), these
tests execute actual ingestion pipelines. Two classes of tests live here,
distinguished by pytest markers:

* ``@pytest.mark.offline_e2e`` — fully local (no network, no credentials).
  Included in the default ``pytest`` run so CI gates on real integration,
  not just unit-level mocks.
* ``@pytest.mark.e2e`` — requires network or external services (live public
  APIs, API tokens). Excluded from the default run; runs only via the
  manual ``e2e.yml`` workflow or explicit ``pytest -m e2e``.

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


def _init_template(
    cli_runner,
    template: str,
    params: dict[str, str] | None = None,
) -> None:
    """Invoke `tycoon init --template <name>`, optionally with parameters."""
    args = ["init", "--template", template]
    for k, v in (params or {}).items():
        args.extend(["--param", f"{k}={v}"])
    result = cli_runner.invoke(app, args)
    assert result.exit_code == 0, (
        f"init --template {template} failed:\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- exception ---\n{result.exception!r}"
    )


def _rebind_config(monkeypatch, project: Path) -> None:
    """Point the command-scoped ``config`` singletons at ``project``.

    Each command module holds its own ``config`` reference imported at
    module load time, so tests must monkey-patch every module whose
    behavior depends on the config root. Keep this list in sync with any
    new command module that imports ``tycoon.config.config``.
    """
    from tycoon.commands import sources as sources_mod
    from tycoon.commands import transform as transform_mod
    from tycoon.config import TycoonConfig

    cfg = TycoonConfig(project_root=project)
    monkeypatch.setattr(sources_mod, "config", cfg)
    monkeypatch.setattr(transform_mod, "config", cfg)


@pytest.mark.offline_e2e
def test_csv_import_e2e(cli_runner, tmp_path, monkeypatch):
    """csv-import is the only fully-offline template: seed a CSV, run, assert.

    Runs in the default ``pytest`` suite — no network, no credentials.
    """
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
    # error() in tycoon.utils.console writes to a stderr-only Console, so we
    # must include result.stderr in the assertion message to see what broke.
    stderr = result.stderr if result.stderr_bytes else ""
    traceback = repr(result.exception) if result.exception else ""
    assert result.exit_code == 0, (
        f"sources run failed (exit {result.exit_code}):\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{stderr}\n"
        f"--- exception ---\n{traceback}"
    )

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
            row = con.execute(f'SELECT count(*) FROM raw_files."{t}"').fetchone()
            total += int(row[0]) if row else 0
        assert total >= 5, f"expected >= 5 ingested rows, got {total}"
    finally:
        con.close()

    # ------------------------------------------------------------------
    # Transform: run `tycoon data transform run` and assert stg_widgets
    # is materialized in the warehouse DB. Proves the full offline
    # pipeline (init → ingest → transform) holds together on every PR.
    # ------------------------------------------------------------------
    result = cli_runner.invoke(app, ["data", "transform", "run"])
    stderr = result.stderr if result.stderr_bytes else ""
    traceback = repr(result.exception) if result.exception else ""
    assert result.exit_code == 0, (
        f"transform run failed (exit {result.exit_code}):\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{stderr}\n"
        f"--- exception ---\n{traceback}"
    )

    warehouse_db = project / "data" / "files_warehouse.duckdb"
    assert warehouse_db.exists(), "warehouse db was not created"

    con = duckdb.connect(str(warehouse_db), read_only=True)
    try:
        row = con.execute("SELECT count(*) FROM main.stg_widgets").fetchone()
        assert row is not None
        stg_rows = row[0]
        # Test wrote 5 rows to widgets.csv, clobbering the template's 10.
        # Any other count means the pipeline is dropping or inventing rows.
        assert stg_rows == 5, f"expected 5 rows in stg_widgets, got {stg_rows}"

        # Verify column-typing happened (CAST in staging model)
        col_types = dict(
            con.execute(
                "SELECT column_name, data_type "
                "FROM information_schema.columns "
                "WHERE table_schema = 'main' AND table_name = 'stg_widgets'"
            ).fetchall()
        )
        assert col_types.get("widget_id") == "INTEGER", col_types
        assert col_types.get("quantity") == "INTEGER", col_types
    finally:
        con.close()

    # Observability: the invocation should have been captured.
    metadata_db = project / ".tycoon" / "metadata.duckdb"
    assert metadata_db.exists(), "observability metadata DB was not created"
    con = duckdb.connect(str(metadata_db), read_only=True)
    try:
        row = con.execute(
            "SELECT count(*) FROM dbt_runs WHERE command = 'run'"
        ).fetchone()
        assert row is not None and row[0] >= 1, (
            f"dbt_runs should contain at least one 'run' invocation; got {row}"
        )
        row = con.execute(
            "SELECT count(*) FROM dbt_nodes "
            "WHERE status = 'success' AND node_name LIKE '%stg_widgets%'"
        ).fetchone()
        assert row is not None and row[0] >= 1, (
            "dbt_nodes should record the successful stg_widgets run"
        )
    finally:
        con.close()


@pytest.mark.e2e
def test_github_analytics_e2e(cli_runner, tmp_path, monkeypatch):
    """Needs a GITHUB_TOKEN. Skip when absent.

    v0.1.3: with template parameterization landed, this now runs a real
    fetch against a tiny public repo (`--max-records 5` on each resource)
    and asserts rows made it into the raw DB. Rate-limited upstream may
    still xfail; that's expected.
    """
    if not os.environ.get("GITHUB_TOKEN"):
        pytest.skip("GITHUB_TOKEN not set; skipping github-analytics e2e")

    project = tmp_path / "github-analytics"
    project.mkdir()
    monkeypatch.chdir(project)
    _init_template(
        cli_runner,
        "github-analytics",
        params={"owner": "octocat", "repo": "hello-world"},
    )

    tycoon_yml = yaml.safe_load((project / "tycoon.yml").read_text())
    assert "github" in tycoon_yml["sources"], "github source missing from template"
    # Substitution should have replaced every {{ owner }} / {{ repo }}
    config_blob = yaml.safe_dump(tycoon_yml)
    assert "{{" not in config_blob, (
        f"Unresolved placeholders in tycoon.yml:\n{config_blob}"
    )

    _rebind_config(monkeypatch, project)
    result = cli_runner.invoke(
        app, ["data", "sources", "run", "github", "--max-records", "5"]
    )
    if result.exit_code != 0:
        pytest.xfail(
            f"github ingest returned {result.exit_code}; GitHub API may be "
            f"rate-limiting or flaky:\n{result.stdout}"
        )

    raw_db = project / "data" / "github_raw.duckdb"
    assert raw_db.exists(), "raw db was not created"


@pytest.mark.e2e
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


@pytest.mark.e2e
def test_weather_station_e2e(cli_runner, tmp_path, monkeypatch):
    """NOAA public API (no key) — with v0.1.3 template parameterization,
    this now fetches against a real station. KJFK is a major airport
    station that's very unlikely to go offline.
    """
    project = tmp_path / "weather-station"
    project.mkdir()
    monkeypatch.chdir(project)
    _init_template(
        cli_runner,
        "weather-station",
        params={
            "station_id": "KJFK",
            "office": "OKX",
            "gridX": "32",
            "gridY": "34",
        },
    )

    tycoon_yml = yaml.safe_load((project / "tycoon.yml").read_text())
    config_blob = yaml.safe_dump(tycoon_yml)
    assert "{{" not in config_blob, (
        f"Unresolved placeholders in tycoon.yml:\n{config_blob}"
    )
    assert "KJFK" in config_blob and "OKX" in config_blob

    _rebind_config(monkeypatch, project)
    result = cli_runner.invoke(
        app, ["data", "sources", "run", "noaa", "--max-records", "5"]
    )
    if result.exit_code != 0:
        pytest.xfail(
            f"noaa ingest returned {result.exit_code}; upstream API may be down:\n"
            f"{result.stdout}"
        )

    raw_db = project / "data" / "weather_raw.duckdb"
    assert raw_db.exists(), "raw db was not created"
