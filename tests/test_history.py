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
