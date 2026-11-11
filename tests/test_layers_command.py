"""Tests for `tycoon data layers` and `tycoon data sources explore` (gh-306).

Each test builds a small real project: a tycoon.yml with a dlt source, a dbt
`target/manifest.json`, a raw DuckDB with the source's tables, and a metadata
DB where a command reads one. Assertions target names, counts and the order
panels appear in, not table layout.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb
import pytest

from tycoon.cli import app
from tycoon.observability import capture_dbt, ensure_schema, metadata_db_path

_YML_HEAD = "name: test\nversion: 0.1.0\nschema_version: 2\ndatabase:\n  raw: data/raw.duckdb\n  warehouse: data/warehouse.duckdb\n"
_YML_SOURCE = "sources:\n  shop:\n    type: rest_api\n    schema: raw_shop\n"


def _model(name: str, folder: str) -> dict:
    return {
        "resource_type": "model",
        "name": name,
        "schema": "main",
        "original_file_path": f"models/{folder}/{name}.sql",
        "config": {"meta": {}},
    }


_MANIFEST_NODES = {
    "model.p.stg_orders": _model("stg_orders", "staging"),
    "model.p.int_order_items": _model("int_order_items", "intermediate"),
    "model.p.fct_orders": _model("fct_orders", "marts"),
}


def _write_manifest(root: Path, nodes: dict) -> None:
    target = root / "dbt_project" / "target"
    target.mkdir(parents=True, exist_ok=True)
    (target / "manifest.json").write_text(json.dumps({"nodes": nodes}))


def _write_raw_db(root: Path, *, with_dlt_tables: bool = False) -> None:
    raw = root / "data" / "raw.duckdb"
    raw.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(raw)) as con:
        con.execute("CREATE SCHEMA raw_shop")
        con.execute("CREATE TABLE raw_shop.orders (order_id INTEGER, customer VARCHAR)")
        con.execute("INSERT INTO raw_shop.orders VALUES (101, 'ada'), (102, 'grace'), (103, 'linus')")
        if with_dlt_tables:
            con.execute("CREATE TABLE raw_shop._dlt_loads (load_id VARCHAR, status INTEGER)")
            con.execute("INSERT INTO raw_shop._dlt_loads VALUES ('1726000000.1', 0)")


def _run_results(unique_ids: list[str], started_at: datetime) -> dict:
    stamp = started_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return {
        "metadata": {"invocation_id": "inv-built", "generated_at": stamp},
        "args": {"which": "build"},
        "results": [
            {
                "unique_id": uid,
                "status": "success",
                "execution_time": 0.5,
                "timing": [{"name": "execute", "started_at": stamp, "completed_at": stamp}],
            }
            for uid in unique_ids
        ],
        "elapsed_time": 1.0,
    }


def _flat(output: str) -> str:
    """Collapse Rich's soft wraps so a sentence can be matched whole."""
    return " ".join(output.split())


def _make_project(root: Path, monkeypatch, *, yml_tail: str = _YML_SOURCE) -> Path:
    (root / "tycoon.yml").write_text(_YML_HEAD + yml_tail)
    # Both commands resolve the project from the working directory.
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def project(tmp_path: Path, monkeypatch) -> Path:
    return _make_project(tmp_path, monkeypatch)


@pytest.fixture
def no_project(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.parametrize("argv", [["data", "layers"], ["data", "sources", "explore"]])
def test_requires_tycoon_yml(no_project, cli_runner, argv):
    result = cli_runner.invoke(app, argv)
    assert result.exit_code == 1
    assert "No tycoon.yml found" in result.output


# ---------------------------------------------------------------------------
# tycoon data layers
# ---------------------------------------------------------------------------


class TestLayers:
    def test_rings_run_from_sources_outermost_to_marts_downtown(self, project, cli_runner):
        _write_manifest(project, _MANIFEST_NODES)
        result = cli_runner.invoke(app, ["data", "layers"])
        assert result.exit_code == 0
        out = result.output
        positions = [out.index(title) for title in ("Sources", "Staging", "Intermediate", "Marts")]
        assert positions == sorted(positions)
        # Each object sits inside its own ring's panel.
        assert positions[0] < out.index("shop") < positions[1]
        assert positions[1] < out.index("stg_orders") < positions[2]
        assert positions[2] < out.index("int_order_items") < positions[3]
        assert positions[3] < out.index("fct_orders")

    def test_every_object_shows_its_vendor(self, project, cli_runner):
        _write_manifest(project, _MANIFEST_NODES)
        result = cli_runner.invoke(app, ["data", "layers"])
        assert result.exit_code == 0
        rows = {line.split("│")[1].strip(): line for line in result.output.splitlines() if line.count("│") >= 3}
        assert " dlt " in rows["shop"]
        for model in ("stg_orders", "int_order_items", "fct_orders"):
            assert " dbt " in rows[model]

    def test_one_model_count_per_ring(self, project, cli_runner):
        _write_manifest(
            project,
            {**_MANIFEST_NODES, "model.p.dim_customers": _model("dim_customers", "marts")},
        )
        result = cli_runner.invoke(app, ["data", "layers"])
        counts = re.findall(r"(\d+) model\(s\)", result.output)
        assert counts == ["1", "1", "2"]

    def test_no_dbt_manifest(self, project, cli_runner):
        result = cli_runner.invoke(app, ["data", "layers"])
        assert result.exit_code == 0
        assert "No dbt manifest yet" in _flat(result.output)
        assert "shop" in result.output

    def test_no_dbt_project(self, tmp_path, monkeypatch, cli_runner):
        _make_project(tmp_path, monkeypatch, yml_tail=_YML_SOURCE + "stack:\n  transformation: none\n")
        result = cli_runner.invoke(app, ["data", "layers"])
        assert result.exit_code == 0
        assert "No dbt project" in _flat(result.output)

    def test_no_sources_registered(self, tmp_path, monkeypatch, cli_runner):
        _make_project(tmp_path, monkeypatch, yml_tail="sources: {}\n")
        _write_manifest(tmp_path, _MANIFEST_NODES)
        result = cli_runner.invoke(app, ["data", "layers"])
        assert result.exit_code == 0
        assert "No sources registered" in _flat(result.output)
        assert "fct_orders" in result.output

    def test_health_is_not_a_command(self, project, cli_runner):
        result = cli_runner.invoke(app, ["data", "health"])
        assert result.exit_code != 0

    def test_a_captured_build_shows_as_the_layer_last_build(self, project, cli_runner):
        # Regression for the gh-390 shape: the ledger keys nodes by dbt unique_id,
        # so looking them up by bare model name always said "never".
        _write_manifest(project, _MANIFEST_NODES)
        dbt_dir = project / "dbt_project"
        started = datetime.now(tz=UTC) - timedelta(hours=2)
        payload = _run_results(["model.p.stg_orders", "model.p.fct_orders"], started)
        (dbt_dir / "target" / "run_results.json").write_text(json.dumps(payload))
        assert capture_dbt(metadata_db_path(project), dbt_dir) == "inv-built"

        result = cli_runner.invoke(app, ["data", "layers"])
        assert result.exit_code == 0
        summaries = [line.strip() for line in result.output.splitlines() if "last build" in line]
        assert summaries == [
            "1 model(s), last build 2h ago",
            "1 model(s), last build never",
            "1 model(s), last build 2h ago",
        ]


# ---------------------------------------------------------------------------
# tycoon data sources explore
# ---------------------------------------------------------------------------


class TestSourcesExplore:
    def test_lists_registered_sources(self, project, cli_runner):
        result = cli_runner.invoke(app, ["data", "sources", "explore"])
        assert result.exit_code == 0
        assert "shop" in result.output
        assert "raw_shop" in result.output

    def test_no_sources_registered(self, tmp_path, monkeypatch, cli_runner):
        _make_project(tmp_path, monkeypatch, yml_tail="sources: {}\n")
        result = cli_runner.invoke(app, ["data", "sources", "explore"])
        assert result.exit_code == 1
        assert "No sources registered" in result.output

    def test_unknown_source(self, project, cli_runner):
        result = cli_runner.invoke(app, ["data", "sources", "explore", "nope"])
        assert result.exit_code == 1
        assert "Source 'nope' not found" in result.output
        assert "shop" in result.output

    def test_before_the_source_has_run(self, project, cli_runner):
        result = cli_runner.invoke(app, ["data", "sources", "explore", "shop"])
        assert result.exit_code == 0
        assert "Raw database not found" in _flat(result.output)

    def test_shows_the_schema(self, project, cli_runner):
        _write_raw_db(project)
        result = cli_runner.invoke(app, ["data", "sources", "explore", "shop"])
        assert result.exit_code == 0
        out = _flat(result.output)
        assert "orders" in out
        assert "order_id: INTEGER" in out
        assert "customer: VARCHAR" in out

    def test_shows_sample_rows(self, project, cli_runner):
        _write_raw_db(project)
        result = cli_runner.invoke(app, ["data", "sources", "explore", "shop", "--sample", "2"])
        assert result.exit_code == 0
        out = _flat(result.output)
        assert "first 2 rows" in out
        assert "ada" in out and "grace" in out
        assert "linus" not in out

    def test_samples_the_users_table_not_dlt_bookkeeping(self, project, cli_runner):
        # `_dlt_loads` sorts before `orders`; the sample must still come from orders.
        _write_raw_db(project, with_dlt_tables=True)
        result = cli_runner.invoke(app, ["data", "sources", "explore", "shop"])
        assert result.exit_code == 0
        out = _flat(result.output)
        assert "orders (first 3 rows)" in out
        assert "_dlt_loads (first" not in out

    def test_health_without_runs(self, project, cli_runner):
        _write_raw_db(project)
        result = cli_runner.invoke(app, ["data", "sources", "explore", "shop"])
        assert result.exit_code == 0
        assert "No runs recorded yet" in result.output

    def test_health_reports_captured_runs(self, project, cli_runner):
        _write_raw_db(project)
        meta = metadata_db_path(project)
        ensure_schema(meta)
        with duckdb.connect(str(meta)) as con:
            con.execute(
                "INSERT INTO dlt_runs VALUES (?, ?, ?, ?, ?, ?)",
                ["raw_shop", "1726000000.1", 0, datetime(2026, 9, 1, 10), "h", datetime(2026, 9, 1, 10)],
            )
            con.execute(
                "INSERT INTO dlt_rows_by_table VALUES (?, ?, ?, ?, ?)",
                ["raw_shop", "orders", "1726000000.1", 3, datetime(2026, 9, 1, 10)],
            )
        result = cli_runner.invoke(app, ["data", "sources", "explore", "shop"])
        assert result.exit_code == 0
        assert "Total runs: 1" in result.output
        assert "Last status: completed" in result.output
        assert "Total rows loaded: 3" in result.output
