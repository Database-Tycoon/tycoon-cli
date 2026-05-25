"""Tests for `tycoon data history` command and the status 'Runs' column."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

from tycoon.cli import app


# ---------------------------------------------------------------------------
# Fixture: a tmp project with a seeded metadata.duckdb
# ---------------------------------------------------------------------------


def _write_tycoon_yml(root: Path, with_sources: bool = False) -> None:
    body = (
        "name: test\n"
        "version: 0.1.0\n"
        "database:\n"
        "  raw: data/raw.duckdb\n"
        "  warehouse: data/warehouse.duckdb\n"
    )
    if with_sources:
        body += (
            "sources:\n"
            "  src_a:\n"
            "    type: rest_api\n"
            "    schema: raw_src_a\n"
        )
    else:
        body += "sources: {}\n"
    (root / "tycoon.yml").write_text(body)


def _seed_metadata(
    root: Path,
    *,
    dlt_runs: list[tuple] | None = None,
    dlt_rows: list[tuple] | None = None,
    dbt_runs: list[tuple] | None = None,
    dbt_nodes: list[tuple] | None = None,
) -> Path:
    """Seed .tycoon/metadata.duckdb with explicit rows.

    Tuple shapes (all trailing captured_at is auto-filled with now()):
      dlt_runs: (source_schema, load_id, status, inserted_at, svh)
      dlt_rows: (source_schema, table_name, load_id, rows_loaded)
      dbt_runs: (invocation_id, command, started_at, elapsed_s, success,
                 models_ok, models_error, tests_passed, tests_failed,
                 dbt_version, target_name)
      dbt_nodes: (invocation_id, node_name, resource_type, status,
                  execution_time_s, rows_affected, compile_time_s, message)
    """
    from tycoon.observability import ensure_schema, metadata_db_path

    meta = metadata_db_path(root)
    ensure_schema(meta)

    now = datetime.now(tz=timezone.utc)
    con = duckdb.connect(str(meta))
    try:
        for row in dlt_runs or []:
            con.execute(
                "INSERT INTO dlt_runs VALUES (?, ?, ?, ?, ?, ?)",
                [*row, now],
            )
        for row in dlt_rows or []:
            con.execute(
                "INSERT INTO dlt_rows_by_table VALUES (?, ?, ?, ?, ?)",
                [*row, now],
            )
        for row in dbt_runs or []:
            con.execute(
                "INSERT INTO dbt_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [*row, now],
            )
        for row in dbt_nodes or []:
            con.execute(
                "INSERT INTO dbt_nodes VALUES (?, ?, ?, ?, ?, ?, ?, ?)", list(row)
            )
    finally:
        con.close()
    return meta


@pytest.fixture
def history_project(tmp_path: Path, monkeypatch):
    """Write tycoon.yml + seed metadata, then monkeypatch the history module's config."""
    _write_tycoon_yml(tmp_path)

    # Patch config references on both modules that read it
    from tycoon.commands import history as history_mod
    from tycoon.commands import status as status_mod
    from tycoon.config import TycoonConfig

    cfg = TycoonConfig(project_root=tmp_path)
    monkeypatch.setattr(history_mod, "config", cfg)
    monkeypatch.setattr(status_mod, "config", cfg)
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# history list view
# ---------------------------------------------------------------------------


class TestHistoryList:
    def test_informs_when_metadata_db_missing(self, history_project, cli_runner):
        result = cli_runner.invoke(app, ["data", "history"])
        assert result.exit_code == 0
        assert "No run history yet" in result.stdout

    def test_lists_dlt_runs(self, history_project, cli_runner):
        _seed_metadata(
            history_project,
            dlt_runs=[
                ("raw_src_a", "load-aaaaaaaa-001", 0, datetime(2026, 4, 19, 15, 30), "hash-v1"),
            ],
            dlt_rows=[
                ("raw_src_a", "items", "load-aaaaaaaa-001", 100),
                ("raw_src_a", "orders", "load-aaaaaaaa-001", 50),
            ],
        )
        result = cli_runner.invoke(app, ["data", "history"])
        assert result.exit_code == 0
        assert "dlt" in result.stdout
        assert "raw_src_a" in result.stdout
        # total rows summary: 150
        assert "150" in result.stdout

    def test_lists_dbt_runs(self, history_project, cli_runner):
        _seed_metadata(
            history_project,
            dbt_runs=[
                (
                    "inv-abcdefgh",
                    "build",
                    datetime(2026, 4, 19, 16, 0),
                    38.1,
                    True,
                    12,
                    0,
                    45,
                    0,
                    "1.9.0",
                    "dev",
                ),
            ],
        )
        result = cli_runner.invoke(app, ["data", "history"])
        assert result.exit_code == 0
        assert "dbt" in result.stdout
        assert "build" in result.stdout
        # short id prefix appears in the ref column
        assert "inv-abcd" in result.stdout

    def test_filters_by_tool_dlt(self, history_project, cli_runner):
        _seed_metadata(
            history_project,
            dlt_runs=[
                ("s", "load-1", 0, datetime(2026, 4, 19, 10, 0), "h"),
            ],
            dbt_runs=[
                (
                    "inv-1",
                    "run",
                    datetime(2026, 4, 19, 11, 0),
                    1.0,
                    True,
                    0,
                    0,
                    0,
                    0,
                    "1.9.0",
                    "dev",
                ),
            ],
        )
        result = cli_runner.invoke(app, ["data", "history", "--tool", "dlt"])
        assert result.exit_code == 0
        # Only dlt should appear as a tool cell — "dbt" will still appear in the
        # command hint text. Check for the invocation id instead.
        assert "inv-1" not in result.stdout

    def test_invalid_tool_rejected(self, history_project, cli_runner):
        result = cli_runner.invoke(app, ["data", "history", "--tool", "bogus"])
        assert result.exit_code != 0

    def test_respects_limit(self, history_project, cli_runner):
        # Use prefixes that differ in the first 8 chars since the ref column
        # truncates load_ids to 8.
        prefixes = ["aardvark", "badger01", "cheetah0", "dolphin0", "eagle-01"]
        rows = [
            ("s", f"{p}-{i:03d}", 0, datetime(2026, 4, 19, 10, i), "h")
            for i, p in enumerate(prefixes)
        ]
        _seed_metadata(history_project, dlt_runs=rows)
        result = cli_runner.invoke(app, ["data", "history", "--limit", "2"])
        assert result.exit_code == 0
        # Only the two newest (eagle, dolphin) should appear
        assert "eagle" in result.stdout
        assert "dolphin" in result.stdout
        assert "aardvark" not in result.stdout


class TestHistorySourceFilter:
    """`--source` filters dlt runs by schema; hides dbt runs entirely."""

    def test_source_filters_dlt_by_schema_literal(self, history_project, cli_runner):
        _seed_metadata(
            history_project,
            dlt_runs=[
                ("raw_apples", "apple-load-1", 0, datetime(2026, 4, 19, 10, 0), "h"),
                ("raw_bananas", "banana-load-1", 0, datetime(2026, 4, 19, 11, 0), "h"),
            ],
        )
        result = cli_runner.invoke(
            app, ["data", "history", "--source", "raw_apples"]
        )
        assert result.exit_code == 0
        # _short() truncates load_id to 8 chars → "apple-lo"
        assert "apple-lo" in result.stdout
        assert "banana-l" not in result.stdout

    def test_source_resolves_config_name_to_schema(self, history_project, cli_runner, monkeypatch):
        # Set up tycoon.yml with a named source whose schema differs from its name
        yml = (
            "name: test\n"
            "version: 0.1.0\n"
            "database:\n"
            "  raw: data/raw.duckdb\n"
            "  warehouse: data/warehouse.duckdb\n"
            "sources:\n"
            "  pokeapi:\n"
            "    type: rest_api\n"
            "    schema: raw_pokeapi\n"
        )
        (history_project / "tycoon.yml").write_text(yml)

        # Rebind the history command's config to pick up the updated yml
        from tycoon.commands import history as history_mod
        from tycoon.config import TycoonConfig

        monkeypatch.setattr(history_mod, "config", TycoonConfig(project_root=history_project))

        _seed_metadata(
            history_project,
            dlt_runs=[
                ("raw_pokeapi", "poke-load-1", 0, datetime(2026, 4, 19, 10, 0), "h"),
                ("raw_other", "other-load-1", 0, datetime(2026, 4, 19, 11, 0), "h"),
            ],
        )
        # Pass the config name 'pokeapi' — should be resolved to schema 'raw_pokeapi'
        result = cli_runner.invoke(app, ["data", "history", "--source", "pokeapi"])
        assert result.exit_code == 0
        # The resolved schema should appear in the title; the other schema should not
        assert "raw_pokeapi" in result.stdout
        assert "raw_other" not in result.stdout

    def test_source_hides_dbt_runs(self, history_project, cli_runner):
        _seed_metadata(
            history_project,
            dlt_runs=[
                ("raw_apples", "apple-load-1", 0, datetime(2026, 4, 19, 10, 0), "h"),
            ],
            dbt_runs=[
                (
                    "inv-xyz",
                    "build",
                    datetime(2026, 4, 19, 11, 0),
                    1.0,
                    True,
                    1, 0, 0, 0, "1.9.0", "dev",
                ),
            ],
        )
        result = cli_runner.invoke(
            app, ["data", "history", "--source", "raw_apples"]
        )
        assert result.exit_code == 0
        assert "apple-lo" in result.stdout
        # The dbt invocation id should NOT appear when --source is active
        assert "inv-xyz" not in result.stdout

    def test_source_with_no_matches_informs(self, history_project, cli_runner):
        _seed_metadata(
            history_project,
            dlt_runs=[("raw_apples", "apple-load-1", 0, datetime(2026, 4, 19, 10, 0), "h")],
        )
        result = cli_runner.invoke(
            app, ["data", "history", "--source", "raw_nonexistent"]
        )
        assert result.exit_code == 0
        assert "No dlt runs captured" in result.stdout


# ---------------------------------------------------------------------------
# history show (drilldown)
# ---------------------------------------------------------------------------


class TestHistoryShow:
    def test_show_resolves_dlt_load_by_prefix(self, history_project, cli_runner):
        _seed_metadata(
            history_project,
            dlt_runs=[
                ("raw_src", "load-xyz-123456", 0, datetime(2026, 4, 19, 12, 0), "h"),
            ],
            dlt_rows=[
                ("raw_src", "items", "load-xyz-123456", 42),
            ],
        )
        result = cli_runner.invoke(app, ["data", "history", "show", "load-xyz"])
        assert result.exit_code == 0
        assert "raw_src" in result.stdout
        assert "items" in result.stdout
        assert "42" in result.stdout

    def test_show_resolves_dbt_invocation_by_prefix(self, history_project, cli_runner):
        _seed_metadata(
            history_project,
            dbt_runs=[
                (
                    "deadbeef-cafe",
                    "build",
                    datetime(2026, 4, 19, 12, 0),
                    5.0,
                    True,
                    1,
                    0,
                    2,
                    0,
                    "1.9.0",
                    "dev",
                ),
            ],
            dbt_nodes=[
                (
                    "deadbeef-cafe",
                    "model.demo.stg_orders",
                    "model",
                    "success",
                    0.8,
                    100,
                    0.1,
                    None,
                ),
            ],
        )
        result = cli_runner.invoke(app, ["data", "history", "show", "deadbeef"])
        assert result.exit_code == 0
        assert "stg_orders" in result.stdout
        assert "build" in result.stdout

    def test_show_dlt_surfaces_trace_details_when_present(
        self, history_project, cli_runner
    ):
        """v0.1.3: trace-enriched show view should display duration + bytes."""
        _seed_metadata(
            history_project,
            dlt_runs=[
                ("raw_src", "load-traceable-001", 0, datetime(2026, 4, 19, 12, 0), "h"),
            ],
            dlt_rows=[
                ("raw_src", "widgets", "load-traceable-001", 42),
            ],
        )

        from tycoon.observability import capture_dlt_trace_from_dict, metadata_db_path

        trace = {
            "transaction_id": "txn-history-001",
            "pipeline_name": "demo",
            "started_at": datetime(2026, 4, 19, 12, 0, 0),
            "finished_at": datetime(2026, 4, 19, 12, 0, 3),
            "engine_version": 1,
            "steps": [
                {
                    "step": "load",
                    "started_at": datetime(2026, 4, 19, 12, 0, 0),
                    "finished_at": datetime(2026, 4, 19, 12, 0, 3),
                    "step_exception": None,
                    "step_info": {
                        "load_packages": [
                            {
                                "load_id": "load-traceable-001",
                                "jobs": [
                                    {
                                        "job_id": "widgets.aaa.insert_values",
                                        "table_name": "widgets",
                                        "file_format": "insert_values",
                                        "file_size": 8192,
                                        "elapsed": 0.5,
                                        "state": "completed_jobs",
                                    }
                                ],
                            }
                        ]
                    },
                }
            ],
        }
        capture_dlt_trace_from_dict(metadata_db_path(history_project), trace)

        result = cli_runner.invoke(app, ["data", "history", "show", "load-traceable"])
        assert result.exit_code == 0
        assert "Duration" in result.stdout
        assert "Bytes written" in result.stdout
        # 8192 bytes = 8.0 KB
        assert "KB" in result.stdout

    def test_show_dbt_surfaces_schema_changes_when_present(
        self, history_project, cli_runner
    ):
        """v0.1.3: schema-diff drilldown should render below the Nodes table."""
        _seed_metadata(
            history_project,
            dbt_runs=[
                (
                    "inv-schema-change",
                    "build",
                    datetime(2026, 4, 19, 12, 0),
                    3.0,
                    True,
                    2, 0, 0, 0, "1.9.0", "dev",
                ),
            ],
        )

        from tycoon.observability import ensure_schema, metadata_db_path

        meta = metadata_db_path(history_project)
        ensure_schema(meta)
        con = duckdb.connect(str(meta))
        try:
            con.execute(
                """
                INSERT INTO dbt_schema_changes
                  (invocation_id, prev_invocation_id, change_type, unique_id,
                   column_name, old_value, new_value, captured_at)
                VALUES
                  ('inv-schema-change', 'inv-prev', 'column_added',
                   'model.demo.stg_widgets', 'name', NULL, 'VARCHAR', now()),
                  ('inv-schema-change', 'inv-prev', 'sql_changed',
                   'model.demo.stg_widgets', '', 'aaaa', 'bbbb', now())
                """
            )
        finally:
            con.close()

        result = cli_runner.invoke(
            app, ["data", "history", "show", "inv-schema-change"]
        )
        assert result.exit_code == 0
        assert "Schema changes" in result.stdout
        assert "column_added" in result.stdout
        assert "sql_changed" in result.stdout
        assert "stg_widgets" in result.stdout

    def test_show_unknown_id_errors(self, history_project, cli_runner):
        _seed_metadata(
            history_project,
            dlt_runs=[("s", "load-1", 0, datetime(2026, 4, 19, 10, 0), "h")],
        )
        result = cli_runner.invoke(app, ["data", "history", "show", "nonexistent"])
        assert result.exit_code != 0

    def test_show_ambiguous_prefix_errors(self, history_project, cli_runner):
        _seed_metadata(
            history_project,
            dlt_runs=[
                ("s1", "shared-prefix-aaa", 0, datetime(2026, 4, 19, 10, 0), "h"),
                ("s2", "shared-prefix-bbb", 0, datetime(2026, 4, 19, 11, 0), "h"),
            ],
        )
        result = cli_runner.invoke(app, ["data", "history", "show", "shared-prefix"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# status 'Runs' column
# ---------------------------------------------------------------------------


class TestStatusRunsColumn:
    def test_runs_column_header_present(self, history_project, cli_runner):
        # Seed sources in tycoon.yml + data dir + raw DB
        _write_tycoon_yml(history_project, with_sources=True)
        # Reload config after rewriting tycoon.yml
        from tycoon.commands import status as status_mod
        from tycoon.config import TycoonConfig

        cfg = TycoonConfig(project_root=history_project)
        cfg.ensure_data_dir()
        # Monkeypatch again since we rewrote the yaml after fixture setup
        status_mod.config = cfg  # type: ignore[misc]

        # Create raw DB with the source's schema
        raw = history_project / "data" / "raw.duckdb"
        con = duckdb.connect(str(raw))
        con.execute("CREATE SCHEMA raw_src_a")
        con.execute(
            "CREATE TABLE raw_src_a._dlt_loads "
            "(load_id VARCHAR, status INTEGER, inserted_at TIMESTAMP, "
            "schema_version_hash VARCHAR)"
        )
        con.close()

        result = cli_runner.invoke(app, ["data", "status"])
        assert result.exit_code == 0
        assert "Runs" in result.stdout

    def test_runs_column_reflects_captured_loads(self, history_project, cli_runner):
        _write_tycoon_yml(history_project, with_sources=True)
        from tycoon.commands import status as status_mod
        from tycoon.config import TycoonConfig

        cfg = TycoonConfig(project_root=history_project)
        cfg.ensure_data_dir()
        status_mod.config = cfg  # type: ignore[misc]

        raw = history_project / "data" / "raw.duckdb"
        con = duckdb.connect(str(raw))
        con.execute("CREATE SCHEMA raw_src_a")
        con.execute(
            "CREATE TABLE raw_src_a._dlt_loads "
            "(load_id VARCHAR, status INTEGER, inserted_at TIMESTAMP, "
            "schema_version_hash VARCHAR)"
        )
        con.close()

        _seed_metadata(
            history_project,
            dlt_runs=[
                ("raw_src_a", "load-1", 0, datetime(2026, 4, 19, 10, 0), "h"),
                ("raw_src_a", "load-2", 0, datetime(2026, 4, 19, 11, 0), "h"),
                ("raw_src_a", "load-3", 0, datetime(2026, 4, 19, 12, 0), "h"),
            ],
        )

        result = cli_runner.invoke(app, ["data", "status"])
        assert result.exit_code == 0
        # The count 3 should appear in the Runs column
        assert "3" in result.stdout
        # Drill-in hint should be shown when runs > 0
        assert "tycoon data history" in result.stdout


# ---------------------------------------------------------------------------
# history --layer (v0.1.7)
# ---------------------------------------------------------------------------


def _write_manifest(dbt_dir: Path, nodes: dict) -> None:
    """Drop a minimal target/manifest.json under ``dbt_dir``."""
    import json

    target = dbt_dir / "target"
    target.mkdir(parents=True, exist_ok=True)
    (target / "manifest.json").write_text(json.dumps({"nodes": nodes}))


class TestHistoryLayerFilter:
    """`--layer` restricts dbt invocations to those touching that layer."""

    def _setup(self, history_project: Path, monkeypatch):
        """Wire tycoon.yml + a project-level manifest with three layers."""
        _write_tycoon_yml(history_project, with_sources=False)
        from tycoon.commands import history as history_mod
        from tycoon.commands import status as status_mod
        from tycoon.config import TycoonConfig

        cfg = TycoonConfig(project_root=history_project)
        monkeypatch.setattr(history_mod, "config", cfg)
        monkeypatch.setattr(status_mod, "config", cfg)

        _write_manifest(
            cfg.dbt_project_dir,
            {
                "model.p.stg_orders": {
                    "resource_type": "model",
                    "name": "stg_orders",
                    "schema": "main",
                    "original_file_path": "models/staging/stg_orders.sql",
                    "config": {"meta": {}},
                },
                "model.p.fct_orders": {
                    "resource_type": "model",
                    "name": "fct_orders",
                    "schema": "main",
                    "original_file_path": "models/marts/fct_orders.sql",
                    "config": {"meta": {}},
                },
            },
        )
        return cfg

    def test_layer_filter_restricts_to_invocations_touching_layer(
        self, history_project, cli_runner, monkeypatch
    ):
        self._setup(history_project, monkeypatch)
        # Two invocations: one only built staging, one built marts.
        _seed_metadata(
            history_project,
            dbt_runs=[
                (
                    "inv-staging",
                    "run",
                    datetime(2026, 5, 1, 10, 0),
                    1.0,
                    True,
                    1,
                    0,
                    0,
                    0,
                    "1.9.0",
                    "dev",
                ),
                (
                    "inv-marts",
                    "build",
                    datetime(2026, 5, 1, 11, 0),
                    2.0,
                    True,
                    1,
                    0,
                    0,
                    0,
                    "1.9.0",
                    "dev",
                ),
            ],
            dbt_nodes=[
                ("inv-staging", "stg_orders", "model", "success", 0.5, 100, 0.1, ""),
                ("inv-marts", "fct_orders", "model", "success", 0.7, 50, 0.1, ""),
            ],
        )

        # --layer mart should only surface the marts invocation
        result = cli_runner.invoke(app, ["data", "history", "--layer", "mart"])
        assert result.exit_code == 0
        assert "build" in result.stdout  # the marts invocation's command
        assert "inv-staging"[:8] not in result.stdout

    def test_layer_filter_with_no_manifest_errors_out(
        self, history_project, cli_runner, monkeypatch
    ):
        # No manifest written
        _write_tycoon_yml(history_project, with_sources=False)
        from tycoon.commands import history as history_mod
        from tycoon.config import TycoonConfig

        cfg = TycoonConfig(project_root=history_project)
        monkeypatch.setattr(history_mod, "config", cfg)
        _seed_metadata(
            history_project,
            dbt_runs=[
                (
                    "inv-1",
                    "run",
                    datetime.now(tz=timezone.utc),
                    1.0,
                    True,
                    1,
                    0,
                    0,
                    0,
                    "1.9.0",
                    "dev",
                ),
            ],
        )

        result = cli_runner.invoke(app, ["data", "history", "--layer", "mart"])
        assert result.exit_code == 1
        # error() writes to stderr
        assert "No dbt manifest" in (result.stderr or result.output)

    def test_invalid_layer_errors_out(
        self, history_project, cli_runner, monkeypatch
    ):
        self._setup(history_project, monkeypatch)
        result = cli_runner.invoke(app, ["data", "history", "--layer", "nonsense"])
        assert result.exit_code == 1
        assert "Invalid --layer" in (result.stderr or result.output)

    def test_layer_and_source_are_mutually_exclusive(
        self, history_project, cli_runner, monkeypatch
    ):
        self._setup(history_project, monkeypatch)
        result = cli_runner.invoke(
            app,
            [
                "data",
                "history",
                "--layer",
                "mart",
                "--source",
                "pokeapi",
            ],
        )
        assert result.exit_code == 1
        assert "either --source or --layer" in (result.stderr or result.output)
