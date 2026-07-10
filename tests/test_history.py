"""Tests for `tycoon data history` command and the status 'Runs' column."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

from tycoon.cli import app
from tycoon.core.events import DbtRunCompleted, RunCompleted


# ---------------------------------------------------------------------------
# Fixtures and seeding helpers
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
    """Seed .tycoon/metadata.duckdb with rows in the OLD observability schema.

    Used only by TestStatusRunsColumn, which still reads ``dlt_runs`` via
    ``_query_run_counts()``. All history tests use ``_seed_events()`` instead.
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


def _seed_events(root: Path, events: list) -> Path:
    """Seed .tycoon/metadata.duckdb with events via the new backend."""
    from tycoon.metadata_backends.duckdb_file import DuckDBFileBackend

    meta = root / ".tycoon" / "metadata.duckdb"
    with DuckDBFileBackend(meta) as b:
        for e in events:
            b.append_event(e)
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
        _seed_events(
            history_project,
            [
                RunCompleted(
                    source_id="raw_src_a",
                    runtime_id="dlt-managed",
                    load_id="load-aaaaaaaa-001",
                    rows_loaded={"items": 100, "orders": 50},
                    timestamp=datetime(2026, 4, 19, 15, 30, tzinfo=timezone.utc),
                ),
            ],
        )
        result = cli_runner.invoke(app, ["data", "history"])
        assert result.exit_code == 0
        assert "dlt" in result.stdout
        assert "raw_src_a" in result.stdout
        assert "150" in result.stdout

    def test_lists_dbt_runs(self, history_project, cli_runner):
        _seed_events(
            history_project,
            [
                DbtRunCompleted(
                    event_id="inv-abcdefgh",
                    source_id="dbt",
                    runtime_id="dbt",
                    command="build",
                    target="dev",
                    models_run=12,
                    models_passed=12,
                    models_errored=0,
                    duration_seconds=38.1,
                    timestamp=datetime(2026, 4, 19, 16, 0, tzinfo=timezone.utc),
                ),
            ],
        )
        result = cli_runner.invoke(app, ["data", "history"])
        assert result.exit_code == 0
        assert "dbt" in result.stdout
        assert "build" in result.stdout
        assert "inv-abcd" in result.stdout

    def test_filters_by_tool_dlt(self, history_project, cli_runner):
        _seed_events(
            history_project,
            [
                RunCompleted(
                    source_id="s",
                    runtime_id="dlt-managed",
                    load_id="load-1",
                    timestamp=datetime(2026, 4, 19, 10, 0, tzinfo=timezone.utc),
                ),
                DbtRunCompleted(
                    event_id="inv-1",
                    source_id="dbt",
                    runtime_id="dbt",
                    command="run",
                    target="dev",
                    timestamp=datetime(2026, 4, 19, 11, 0, tzinfo=timezone.utc),
                ),
            ],
        )
        result = cli_runner.invoke(app, ["data", "history", "--tool", "dlt"])
        assert result.exit_code == 0
        # dbt invocation should be absent when filtering to dlt only
        assert "inv-1" not in result.stdout

    def test_invalid_tool_rejected(self, history_project, cli_runner):
        result = cli_runner.invoke(app, ["data", "history", "--tool", "bogus"])
        assert result.exit_code != 0

    def test_respects_limit(self, history_project, cli_runner):
        # Use prefixes that differ in the first 8 chars since the ref column
        # truncates load_ids to 8.
        prefixes = ["aardvark", "badger01", "cheetah0", "dolphin0", "eagle-01"]
        events = [
            RunCompleted(
                source_id="s",
                runtime_id="dlt-managed",
                load_id=f"{p}-{i:03d}",
                timestamp=datetime(2026, 4, 19, 10, i, tzinfo=timezone.utc),
            )
            for i, p in enumerate(prefixes)
        ]
        _seed_events(history_project, events)
        result = cli_runner.invoke(app, ["data", "history", "--limit", "2"])
        assert result.exit_code == 0
        # Only the two newest (eagle, dolphin) should appear
        assert "eagle" in result.stdout
        assert "dolphin" in result.stdout
        assert "aardvark" not in result.stdout


class TestHistorySourceFilter:
    """`--source` filters dlt runs by source_id; hides dbt runs entirely."""

    def test_source_filters_dlt_by_schema_literal(self, history_project, cli_runner):
        _seed_events(
            history_project,
            [
                RunCompleted(
                    source_id="raw_apples",
                    runtime_id="dlt-managed",
                    load_id="apple-load-1",
                    timestamp=datetime(2026, 4, 19, 10, 0, tzinfo=timezone.utc),
                ),
                RunCompleted(
                    source_id="raw_bananas",
                    runtime_id="dlt-managed",
                    load_id="banana-load-1",
                    timestamp=datetime(2026, 4, 19, 11, 0, tzinfo=timezone.utc),
                ),
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
        # Set up tycoon.yml with a named source
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

        from tycoon.commands import history as history_mod
        from tycoon.config import TycoonConfig

        monkeypatch.setattr(history_mod, "config", TycoonConfig(project_root=history_project))

        _seed_events(
            history_project,
            [
                RunCompleted(
                    source_id="pokeapi",
                    runtime_id="dlt-managed",
                    load_id="poke-load-1",
                    timestamp=datetime(2026, 4, 19, 10, 0, tzinfo=timezone.utc),
                ),
                RunCompleted(
                    source_id="other",
                    runtime_id="dlt-managed",
                    load_id="other-load-1",
                    timestamp=datetime(2026, 4, 19, 11, 0, tzinfo=timezone.utc),
                ),
            ],
        )
        # Events are keyed by source_id = config name (not schema)
        result = cli_runner.invoke(app, ["data", "history", "--source", "pokeapi"])
        assert result.exit_code == 0
        assert "pokeapi" in result.stdout
        assert "raw_other" not in result.stdout

    def test_source_hides_dbt_runs(self, history_project, cli_runner):
        _seed_events(
            history_project,
            [
                RunCompleted(
                    source_id="raw_apples",
                    runtime_id="dlt-managed",
                    load_id="apple-load-1",
                    timestamp=datetime(2026, 4, 19, 10, 0, tzinfo=timezone.utc),
                ),
                DbtRunCompleted(
                    event_id="inv-xyz",
                    source_id="dbt",
                    runtime_id="dbt",
                    command="build",
                    target="dev",
                    timestamp=datetime(2026, 4, 19, 11, 0, tzinfo=timezone.utc),
                ),
            ],
        )
        result = cli_runner.invoke(
            app, ["data", "history", "--source", "raw_apples"]
        )
        assert result.exit_code == 0
        assert "apple-lo" in result.stdout
        assert "inv-xyz" not in result.stdout

    def test_source_with_no_matches_informs(self, history_project, cli_runner):
        _seed_events(
            history_project,
            [
                RunCompleted(
                    source_id="raw_apples",
                    runtime_id="dlt-managed",
                    load_id="apple-load-1",
                    timestamp=datetime(2026, 4, 19, 10, 0, tzinfo=timezone.utc),
                ),
            ],
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
        _seed_events(
            history_project,
            [
                RunCompleted(
                    source_id="raw_src",
                    runtime_id="dlt-managed",
                    load_id="load-xyz-123456",
                    rows_loaded={"items": 42},
                    tables_created=["items"],
                    timestamp=datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc),
                ),
            ],
        )
        result = cli_runner.invoke(app, ["data", "history", "show", "load-xyz"])
        assert result.exit_code == 0
        assert "raw_src" in result.stdout
        assert "items" in result.stdout
        assert "42" in result.stdout

    def test_show_resolves_dbt_invocation_by_prefix(self, history_project, cli_runner):
        _seed_events(
            history_project,
            [
                DbtRunCompleted(
                    event_id="deadbeef-cafe",
                    source_id="dbt",
                    runtime_id="dbt",
                    command="build",
                    target="dev",
                    models_run=1,
                    models_passed=1,
                    models_errored=0,
                    duration_seconds=5.0,
                    timestamp=datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc),
                ),
            ],
        )
        result = cli_runner.invoke(app, ["data", "history", "show", "deadbeef"])
        assert result.exit_code == 0
        assert "build" in result.stdout

    def test_show_dlt_surfaces_duration(self, history_project, cli_runner):
        """Show view renders duration from the RunCompleted event."""
        _seed_events(
            history_project,
            [
                RunCompleted(
                    source_id="raw_src",
                    runtime_id="dlt-managed",
                    load_id="load-dur-001",
                    rows_loaded={"widgets": 42},
                    duration_seconds=3.0,
                    timestamp=datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc),
                ),
            ],
        )
        result = cli_runner.invoke(app, ["data", "history", "show", "load-dur"])
        assert result.exit_code == 0
        assert "Duration" in result.stdout

    def test_show_dbt_invocation_exits_zero(self, history_project, cli_runner):
        """dbt show renders successfully even without per-node detail in M1."""
        _seed_events(
            history_project,
            [
                DbtRunCompleted(
                    event_id="inv-schema-change",
                    source_id="dbt",
                    runtime_id="dbt",
                    command="build",
                    target="dev",
                    models_run=2,
                    models_errored=0,
                    duration_seconds=3.0,
                    timestamp=datetime(2026, 4, 19, 12, 0, tzinfo=timezone.utc),
                ),
            ],
        )
        result = cli_runner.invoke(
            app, ["data", "history", "show", "inv-schema-change"]
        )
        assert result.exit_code == 0
        assert "build" in result.stdout

    def test_show_unknown_id_errors(self, history_project, cli_runner):
        _seed_events(
            history_project,
            [
                RunCompleted(
                    source_id="s",
                    runtime_id="dlt-managed",
                    load_id="load-1",
                    timestamp=datetime(2026, 4, 19, 10, 0, tzinfo=timezone.utc),
                ),
            ],
        )
        result = cli_runner.invoke(app, ["data", "history", "show", "nonexistent"])
        assert result.exit_code != 0

    def test_show_ambiguous_prefix_errors(self, history_project, cli_runner):
        _seed_events(
            history_project,
            [
                RunCompleted(
                    source_id="s1",
                    runtime_id="dlt-managed",
                    load_id="shared-prefix-aaa",
                    timestamp=datetime(2026, 4, 19, 10, 0, tzinfo=timezone.utc),
                ),
                RunCompleted(
                    source_id="s2",
                    runtime_id="dlt-managed",
                    load_id="shared-prefix-bbb",
                    timestamp=datetime(2026, 4, 19, 11, 0, tzinfo=timezone.utc),
                ),
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

    def test_layer_filter_shows_all_dbt_runs_m1_limitation(
        self, history_project, cli_runner, monkeypatch
    ):
        self._setup(history_project, monkeypatch)
        _seed_events(
            history_project,
            [
                DbtRunCompleted(
                    event_id="inv-staging",
                    source_id="dbt",
                    runtime_id="dbt",
                    command="run",
                    target="dev",
                    models_run=1,
                    timestamp=datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc),
                ),
                DbtRunCompleted(
                    event_id="inv-marts00",
                    source_id="dbt",
                    runtime_id="dbt",
                    command="build",
                    target="dev",
                    models_run=1,
                    timestamp=datetime(2026, 5, 1, 11, 0, tzinfo=timezone.utc),
                ),
            ],
        )
        result = cli_runner.invoke(app, ["data", "history", "--layer", "mart"])
        assert result.exit_code == 0
        # M1: --layer shows all dbt runs; per-model filtering added in a later milestone.
        assert "build" in result.stdout

    def test_layer_filter_with_no_manifest_errors_out(
        self, history_project, cli_runner, monkeypatch
    ):
        # No manifest written — _resolve_layer_models errors before reaching DB
        _write_tycoon_yml(history_project, with_sources=False)
        from tycoon.commands import history as history_mod
        from tycoon.config import TycoonConfig

        cfg = TycoonConfig(project_root=history_project)
        monkeypatch.setattr(history_mod, "config", cfg)

        result = cli_runner.invoke(app, ["data", "history", "--layer", "mart"])
        assert result.exit_code == 1
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
