"""Regression tests for gh-239: ``--max-records`` on native dlt builders.

``run_source`` used to forward ``max_records`` to the legacy and catalog
paths only, so a ``filesystem``, ``rest_api``, or ``sql_database`` source
printed "Record cap: 3" and then loaded every row. Each test here runs a
real pipeline into a real DuckDB file and counts what landed.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import duckdb
import pytest

from tycoon.ingestion.runner import run_source
from tycoon.project import ResourceConfig, SourceConfig

_TEN_ROW_CSV = "id,value\n" + "".join(f"{i},row{i}\n" for i in range(10))


@pytest.fixture
def pipeline_name(request: pytest.FixtureRequest) -> Iterator[str]:
    name = f"test_gh239_{request.node.name}".replace("[", "_").replace("]", "")
    yield name
    shutil.rmtree(Path.home() / ".dlt" / "pipelines" / name, ignore_errors=True)


def _count(raw_db_path: Path, schema: str, table: str) -> int:
    con = duckdb.connect(str(raw_db_path), read_only=True)
    try:
        row = con.execute(f'SELECT count(*) FROM {schema}."{table}"').fetchone()
    finally:
        con.close()
    assert row is not None
    return row[0]


class TestFilesystemMaxRecords:
    def test_flat_config_caps_rows(self, tmp_path: Path, pipeline_name: str) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "sales.csv").write_text(_TEN_ROW_CSV)
        raw_db_path = tmp_path / "raw.duckdb"

        source_config = SourceConfig(
            type="filesystem",
            schema="raw_test",
            config={"path": str(input_dir), "file_glob": "*.csv"},
        )
        run_source(pipeline_name, source_config, raw_db_path=raw_db_path, max_records=3)

        assert _count(raw_db_path, "raw_test", pipeline_name) == 3

    def test_cap_applies_per_resource(self, tmp_path: Path, pipeline_name: str) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "games.csv").write_text(_TEN_ROW_CSV)
        (input_dir / "players.csv").write_text(_TEN_ROW_CSV)
        raw_db_path = tmp_path / "raw.duckdb"

        source_config = SourceConfig(
            type="filesystem",
            schema="raw_test",
            resources=[
                ResourceConfig(table_name="games", path=str(input_dir), file_glob="games.csv"),
                ResourceConfig(table_name="players", path=str(input_dir), file_glob="players.csv"),
            ],
        )
        run_source(pipeline_name, source_config, raw_db_path=raw_db_path, max_records=3)

        assert _count(raw_db_path, "raw_test", "games") == 3
        assert _count(raw_db_path, "raw_test", "players") == 3

    def test_cap_spans_multiple_files(self, tmp_path: Path, pipeline_name: str) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "a.csv").write_text("id,value\n1,a\n2,b\n")
        (input_dir / "b.csv").write_text("id,value\n3,c\n4,d\n")
        raw_db_path = tmp_path / "raw.duckdb"

        source_config = SourceConfig(
            type="filesystem",
            schema="raw_test",
            config={"path": str(input_dir), "file_glob": "*.csv"},
        )
        run_source(pipeline_name, source_config, raw_db_path=raw_db_path, max_records=3)

        assert _count(raw_db_path, "raw_test", pipeline_name) == 3

    def test_no_cap_loads_every_row(self, tmp_path: Path, pipeline_name: str) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "sales.csv").write_text(_TEN_ROW_CSV)
        raw_db_path = tmp_path / "raw.duckdb"

        source_config = SourceConfig(
            type="filesystem",
            schema="raw_test",
            config={"path": str(input_dir), "file_glob": "*.csv"},
        )
        run_source(pipeline_name, source_config, raw_db_path=raw_db_path)

        assert _count(raw_db_path, "raw_test", pipeline_name) == 10


class TestSqlDatabaseMaxRecords:
    def test_caps_rows_from_sqlite(self, tmp_path: Path, pipeline_name: str) -> None:
        # sqlalchemy is an optional dlt extra that tycoon does not install.
        pytest.importorskip("sqlalchemy")

        sqlite_path = tmp_path / "shop.db"
        con = sqlite3.connect(sqlite_path)
        con.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, value TEXT)")
        con.executemany("INSERT INTO orders VALUES (?, ?)", [(i, f"row{i}") for i in range(10)])
        con.commit()
        con.close()
        raw_db_path = tmp_path / "raw.duckdb"

        source_config = SourceConfig(
            type="sql_database",
            schema="raw_test",
            config={"connection_string": f"sqlite:///{sqlite_path}"},
        )
        run_source(pipeline_name, source_config, raw_db_path=raw_db_path, max_records=3)

        assert _count(raw_db_path, "raw_test", "orders") == 3


class _PagedItemsHandler(BaseHTTPRequestHandler):
    """Serves 10 items as five pages of two, linked by a ``next`` URL."""

    requested_pages: list[int] = []

    def do_GET(self) -> None:
        page = int(self.path.rsplit("page=", 1)[-1]) if "page=" in self.path else 0
        type(self).requested_pages.append(page)
        items = [{"id": i} for i in range(page * 2, page * 2 + 2)]
        host, port = self.server.server_address[:2]
        next_url = f"http://{host!s}:{port}/items?page={page + 1}" if page < 4 else None
        body = json.dumps({"data": items, "next": next_url}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


@pytest.fixture
def items_api() -> Iterator[tuple[str, list[int]]]:
    _PagedItemsHandler.requested_pages = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _PagedItemsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", _PagedItemsHandler.requested_pages
    finally:
        server.shutdown()
        server.server_close()


class TestRestApiMaxRecords:
    def test_caps_rows_and_stops_paging(
        self, tmp_path: Path, pipeline_name: str, items_api: tuple[str, list[int]]
    ) -> None:
        base_url, requested_pages = items_api
        raw_db_path = tmp_path / "raw.duckdb"

        source_config = SourceConfig(
            type="rest_api",
            schema="raw_test",
            config={
                "base_url": base_url,
                "resources": [
                    {
                        "name": "items",
                        "endpoint": {
                            "path": "items",
                            "data_selector": "data",
                            "paginator": {"type": "json_link", "next_url_path": "next"},
                        },
                    }
                ],
            },
        )
        run_source(pipeline_name, source_config, raw_db_path=raw_db_path, max_records=3)

        assert _count(raw_db_path, "raw_test", "items") == 3
        assert requested_pages == [0, 1]
