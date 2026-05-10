"""End-to-end tests for built-in templates.

Unlike ``test_templates_smoke.py`` (which only validates init + doctor), these
tests execute actual ingestion pipelines. Two classes of tests live here,
distinguished by pytest markers:

* ``@pytest.mark.offline_e2e`` — fully local (no network, no credentials).
  Included in the default ``pytest`` run so CI gates on real integration,
  not just unit-level mocks.
* ``@pytest.mark.e2e`` — requires network or external services (live public
  APIs). Excluded from the default run; runs only via the manual
  ``e2e.yml`` workflow or explicit ``pytest -m e2e``.
"""

from __future__ import annotations

import csv
from pathlib import Path

import duckdb
import pytest

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

    Also rebinds the module-level singleton in ``tycoon.config`` —
    deep-call sites (e.g. ``ingestion/runner.py:_capture_and_refresh_safe``
    that imports ``config`` at call time) read from there, and without
    this patch they pick up the parent-tmpdir root pytest started in.
    """
    import tycoon.config as cfg_mod
    from tycoon.commands import sources as sources_mod
    from tycoon.commands import transform as transform_mod
    from tycoon.config import TycoonConfig

    cfg = TycoonConfig(project_root=project)
    monkeypatch.setattr(sources_mod, "config", cfg)
    monkeypatch.setattr(transform_mod, "config", cfg)
    monkeypatch.setattr(cfg_mod, "config", cfg)


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

        # widget_id has not_null + unique tests in schema.yml — assert the
        # invariant holds in the data, not just at the test layer.
        nulls = con.execute(
            "SELECT count(*) FROM main.stg_widgets WHERE widget_id IS NULL"
        ).fetchone()
        assert nulls is not None and nulls[0] == 0, "widget_id has nulls"
        distinct_ids = con.execute(
            "SELECT count(distinct widget_id) FROM main.stg_widgets"
        ).fetchone()
        assert distinct_ids is not None and distinct_ids[0] == 5, (
            f"widget_id should be unique (expected 5 distinct, got {distinct_ids})"
        )

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

        # Mart layer: fct_widget_summary should be a single-row aggregate
        # built from stg_widgets. Sum of quantity in the seeded data is
        # 10 + 20 + 30 + 40 + 50 = 150.
        mart = con.execute(
            "SELECT widget_count, distinct_names, total_quantity, "
            "min_quantity, max_quantity FROM main.fct_widget_summary"
        ).fetchall()
        assert len(mart) == 1, f"fct_widget_summary should have 1 row, got {len(mart)}"
        widget_count, distinct_names, total_qty, min_qty, max_qty = mart[0]
        assert widget_count == 5
        assert distinct_names == 5
        assert total_qty == 150
        assert min_qty == 10
        assert max_qty == 50
    finally:
        con.close()

    # Run `dbt test` and assert all schema-declared tests pass. Catches
    # any regression where stg_widgets no longer satisfies its declared
    # not_null / unique invariants — or where a future schema change
    # breaks an existing test.
    result = cli_runner.invoke(app, ["data", "transform", "test"])
    stderr = result.stderr if result.stderr_bytes else ""
    assert result.exit_code == 0, (
        f"dbt test failed (exit {result.exit_code}):\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{stderr}"
    )

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


def _seed_widgets_csv(input_dir: Path, count: int = 5) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    with (input_dir / "widgets.csv").open("w") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "qty"])
        for i in range(1, count + 1):
            writer.writerow([i, f"widget-{i}", i * 10])


@pytest.mark.offline_e2e
def test_csv_import_rerun_idempotent(cli_runner, tmp_path, monkeypatch):
    """Running the full pipeline twice must leave row counts and mart
    aggregates unchanged. Catches state leaks across repeated ingests.

    dlt's default write_disposition is `replace`, so re-ingesting the
    same CSV should rewrite the raw table rather than appending. If
    that contract drifts, this test will fail with row counts of 10.
    """
    project = tmp_path / "csv-import-rerun"
    project.mkdir()
    monkeypatch.chdir(project)
    _init_template(cli_runner, "csv-import")
    _seed_widgets_csv(project / "data" / "input", count=5)
    _rebind_config(monkeypatch, project)

    # Run the full pipeline twice.
    for pass_num in (1, 2):
        result = cli_runner.invoke(app, ["data", "sources", "run", "files"])
        assert result.exit_code == 0, (
            f"sources run pass {pass_num} failed:\n{result.stdout}"
        )
        result = cli_runner.invoke(app, ["data", "transform", "run"])
        assert result.exit_code == 0, (
            f"transform run pass {pass_num} failed:\n{result.stdout}"
        )

    # Raw table: same 5 rows after two ingests (replace semantics).
    raw_db = project / "data" / "files_raw.duckdb"
    con = duckdb.connect(str(raw_db), read_only=True)
    try:
        rows = con.execute(
            'SELECT count(*) FROM raw_files."_read_csv"'
        ).fetchone()
        assert rows is not None and rows[0] == 5, (
            f"raw row count drifted across reruns; got {rows[0]} "
            "(default write_disposition should be `replace`)"
        )
    finally:
        con.close()

    # Warehouse: stg_widgets row count + mart aggregates unchanged.
    warehouse_db = project / "data" / "files_warehouse.duckdb"
    con = duckdb.connect(str(warehouse_db), read_only=True)
    try:
        stg = con.execute("SELECT count(*) FROM main.stg_widgets").fetchone()
        assert stg is not None and stg[0] == 5
        mart = con.execute(
            "SELECT widget_count, total_quantity FROM main.fct_widget_summary"
        ).fetchone()
        assert mart == (5, 150), (
            f"mart aggregates drifted across reruns; got {mart}, expected (5, 150)"
        )
    finally:
        con.close()

    # Observability: both passes captured. Two dlt loads, two dbt runs.
    metadata_db = project / ".tycoon" / "metadata.duckdb"
    con = duckdb.connect(str(metadata_db), read_only=True)
    try:
        dlt_runs = con.execute("SELECT count(*) FROM dlt_runs").fetchone()
        dbt_runs = con.execute(
            "SELECT count(*) FROM dbt_runs WHERE command = 'run'"
        ).fetchone()
        assert dlt_runs is not None and dlt_runs[0] == 2, (
            f"expected 2 dlt loads captured, got {dlt_runs}"
        )
        assert dbt_runs is not None and dbt_runs[0] == 2, (
            f"expected 2 dbt 'run' invocations captured, got {dbt_runs}"
        )
    finally:
        con.close()


@pytest.mark.offline_e2e
def test_csv_import_transform_ingest_transform(cli_runner, tmp_path, monkeypatch):
    """Sequence: transform → ingest → transform must produce the same
    final state as ingest → transform alone. Catches stale-warehouse
    bugs where dbt sees the old raw table on a second pass.

    First transform runs against an empty raw table (0 rows). Second
    transform runs after the ingest and should produce the seeded
    aggregates. The first pass is allowed to non-zero exit because
    `_read_csv` may not yet exist; we only assert the *final* state.
    """
    project = tmp_path / "csv-import-tit"
    project.mkdir()
    monkeypatch.chdir(project)
    _init_template(cli_runner, "csv-import")
    _seed_widgets_csv(project / "data" / "input", count=5)
    _rebind_config(monkeypatch, project)

    # Pass 1: transform with no ingest (best-effort; may fail on missing source).
    cli_runner.invoke(app, ["data", "transform", "run"])

    # Pass 2: ingest + transform. This is the assertion target.
    result = cli_runner.invoke(app, ["data", "sources", "run", "files"])
    assert result.exit_code == 0, f"sources run failed:\n{result.stdout}"
    result = cli_runner.invoke(app, ["data", "transform", "run"])
    assert result.exit_code == 0, f"second transform run failed:\n{result.stdout}"

    warehouse_db = project / "data" / "files_warehouse.duckdb"
    con = duckdb.connect(str(warehouse_db), read_only=True)
    try:
        mart = con.execute(
            "SELECT widget_count, total_quantity FROM main.fct_widget_summary"
        ).fetchone()
        assert mart == (5, 150), (
            f"final mart state wrong after transform-then-ingest-then-transform: "
            f"got {mart}"
        )
    finally:
        con.close()


@pytest.mark.offline_e2e
def test_csv_import_then_data_sync(cli_runner, tmp_path, monkeypatch):
    """Full user workflow: ingest → transform → sync warehouse to a
    portable snapshot. Asserts the snapshot DB has the expected mart
    data after the round trip.

    This is the closest test we have to the "I built my warehouse and
    want a shareable file" user journey.
    """
    project = tmp_path / "csv-import-sync"
    project.mkdir()
    monkeypatch.chdir(project)
    _init_template(cli_runner, "csv-import")
    _seed_widgets_csv(project / "data" / "input", count=5)
    _rebind_config(monkeypatch, project)

    # Bind sync_cmd's config too, since it imports separately.
    from tycoon.commands import sync_cmd as sync_mod
    from tycoon.config import TycoonConfig
    monkeypatch.setattr(sync_mod, "config", TycoonConfig(project_root=project))

    # ingest + transform
    assert cli_runner.invoke(app, ["data", "sources", "run", "files"]).exit_code == 0
    assert cli_runner.invoke(app, ["data", "transform", "run"]).exit_code == 0

    # Sync the full warehouse. Views that depend on the dbt-attached
    # `tycoon_meta` catalog (the _tycoon observability staging models)
    # are skipped per-row rather than failing the whole sync (issue #23).
    snapshot = project / "data" / "snapshot.duckdb"
    warehouse_db = project / "data" / "files_warehouse.duckdb"
    result = cli_runner.invoke(
        app,
        ["data", "sync", "--from", str(warehouse_db), "--to", str(snapshot)],
    )
    assert result.exit_code == 0, f"sync failed:\n{result.stdout}"
    assert snapshot.exists(), "snapshot DB was not created"
    # The user-owned tables landed; the tycoon_meta-dependent views were
    # skipped with a warning (asserted via stdout contents).
    assert "stg_widgets" in result.stdout
    assert "fct_widget_summary" in result.stdout
    assert "Skipped" in result.stdout, (
        f"expected sync to surface skipped views; stdout:\n{result.stdout}"
    )

    # The snapshot should carry the mart and stg tables built by dbt.
    con = duckdb.connect(str(snapshot), read_only=True)
    try:
        mart = con.execute(
            "SELECT widget_count, total_quantity FROM main.fct_widget_summary"
        ).fetchone()
        assert mart == (5, 150), f"snapshot mart mismatched: {mart}"
        stg = con.execute("SELECT count(*) FROM main.stg_widgets").fetchone()
        assert stg is not None and stg[0] == 5
    finally:
        con.close()


@pytest.mark.e2e
def test_nyc_transit_e2e(cli_runner, tmp_path, monkeypatch):
    """Public NYC Open Data / MTA feeds — no auth needed, but slow.

    v0.1.5: extended past raw-DB-exists. With `transform.auto_scaffold`
    on by default, `data sources run` triggers analyze, then
    `data transform run` materializes staging in the warehouse DB.
    """
    project = tmp_path / "nyc-transit"
    project.mkdir()
    monkeypatch.chdir(project)
    _init_template(cli_runner, "nyc-transit")

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

    # Auto-scaffold should have written staging models for nyc-dot.
    staging_dir = project / "dbt_project" / "models" / "staging" / "nyc-dot"
    assert staging_dir.exists(), (
        f"auto-scaffold did not create staging dir; sources run output:\n{result.stdout}"
    )
    sql_files = list(staging_dir.glob("stg_nyc-dot__*.sql"))
    assert sql_files, f"no staging .sql files generated under {staging_dir}"

    # Run dbt against the auto-scaffolded models.
    result = cli_runner.invoke(app, ["data", "transform", "run"])
    if result.exit_code != 0:
        pytest.xfail(
            f"dbt run returned {result.exit_code}; could be a downstream "
            f"compatibility issue against live data:\n{result.stdout}"
        )

    # Assert at least one staging table is materialized in the warehouse.
    warehouse_db = project / "data" / "nyc_open_data_local.duckdb"
    assert warehouse_db.exists(), "warehouse db was not created by dbt run"
    con = duckdb.connect(str(warehouse_db), read_only=True)
    try:
        rows = con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_name LIKE 'stg_nyc-dot__%'"
        ).fetchone()
        assert rows is not None and rows[0] >= 1, (
            f"expected at least one stg_nyc-dot__* table in warehouse DB; got {rows}"
        )
    finally:
        con.close()


@pytest.mark.offline_e2e
def test_register_dbt_create_e2e(cli_runner, tmp_path, monkeypatch):
    """End-to-end coverage for `tycoon register dbt --create` (#34).

    The unit tests in `test_register.py::TestRegisterDbtCreate` prove
    register --create writes the right files. This test proves the
    *result* — a freshly bootstrapped dbt project can actually run
    ``tycoon data transform run`` to completion. That's the gate the
    unit tests can't give us: unit-level write-correctness != end-to-end
    runnability.

    Mirrors the user journey that motivated #34: a tycoon project
    where dbt was Skipped during init, recovered via a single CLI
    command.
    """
    import yaml

    project = tmp_path / "no-dbt-recovery"
    project.mkdir()
    (project / "data").mkdir()
    monkeypatch.chdir(project)

    # Hand-write the tycoon.yml that the wizard would produce when the
    # user picks "Skip" on the dbt prompt — no dbt_project_dir, stack
    # marks transformation as none.
    (project / "tycoon.yml").write_text(
        yaml.dump(
            {
                "name": "no-dbt-recovery",
                "version": "0.1.0",
                "database": {
                    "raw": "data/raw.duckdb",
                    "warehouse": "data/warehouse.duckdb",
                },
                "sources": {},
                "stack": {
                    "warehouse": "duckdb",
                    "transformation": "none",
                    "transformation_managed": False,
                },
            }
        )
    )

    _rebind_config(monkeypatch, project)
    # register.py also imports config at module scope — rebind that too.
    from tycoon.commands import register as register_mod
    from tycoon.config import TycoonConfig
    monkeypatch.setattr(register_mod, "config", TycoonConfig(project_root=project))

    # The marquee v0.1.6 command — bootstrap dbt from scratch.
    result = cli_runner.invoke(app, ["register", "dbt", "--create"])
    assert result.exit_code == 0, (
        f"register dbt --create failed:\n--- stdout ---\n{result.stdout}\n"
        f"--- exception ---\n{result.exception!r}"
    )

    # Sibling dbt project landed at the default path.
    sibling = tmp_path / "no-dbt-recovery-dbt"
    assert (sibling / "dbt_project.yml").exists(), "dbt_project.yml missing"
    assert (sibling / "profiles.yml").exists(), "profiles.yml missing"

    # tycoon.yml got the wiring.
    yml = yaml.safe_load((project / "tycoon.yml").read_text())
    assert yml["dbt_project_dir"], "dbt_project_dir not written to tycoon.yml"
    assert yml["stack"]["transformation"] == "dbt"
    assert yml["stack"]["transformation_managed"] is True, (
        "--create should mark project as tycoon-managed"
    )

    # In real CLI use each command is a fresh process and re-reads
    # tycoon.yml. In-process tests share the singleton, so we rebind
    # after register wrote the new dbt_project_dir.
    _rebind_config(monkeypatch, project)

    # The actual gate: the freshly bootstrapped project must be runnable
    # by `tycoon data transform run`. This is what the unit tests can't
    # cover. If the profile is malformed, the metadata DB ATTACH is
    # broken, or the scaffolded `_tycoon/` models are stale, transform
    # run blows up here.
    result = cli_runner.invoke(app, ["data", "transform", "run"])
    stderr = result.stderr if result.stderr_bytes else ""
    traceback = repr(result.exception) if result.exception else ""
    assert result.exit_code == 0, (
        f"transform run against freshly created dbt project failed "
        f"(exit {result.exit_code}):\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{stderr}\n"
        f"--- exception ---\n{traceback}"
    )

    # Warehouse DB should exist now.
    warehouse_db = project / "data" / "warehouse.duckdb"
    assert warehouse_db.exists(), "warehouse db was not created"
