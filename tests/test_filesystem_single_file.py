"""Regression tests for issue #238: a filesystem source whose ``path`` names
a single file must load that file's rows, not run an empty resource to a
zero-row success."""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path

import duckdb
import pytest

from tycoon.ingestion.runner import IngestionError, _build_filesystem_source, run_source
from tycoon.project import ResourceConfig, SourceConfig


def _row_count(raw_db_path: Path, schema: str, table: str) -> int:
    con = duckdb.connect(str(raw_db_path), read_only=True)
    try:
        row = con.execute(f'SELECT count(*) FROM {schema}."{table}"').fetchone()
    finally:
        con.close()
    assert row is not None
    return row[0]


@pytest.fixture
def sales_csv(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    csv = data_dir / "sales.csv"
    csv.write_text("id,amount\n1,10\n2,20\n3,30\n")
    return csv


@pytest.fixture
def pipeline_cleanup() -> Iterator[list[str]]:
    names: list[str] = []
    yield names
    for name in names:
        shutil.rmtree(Path.home() / ".dlt" / "pipelines" / name, ignore_errors=True)


class TestSingleFilePath:
    def test_flat_path_to_a_file_loads_its_rows(self, tmp_path, sales_csv, pipeline_cleanup):
        """The exact shape `tycoon data sources add filesystem` writes."""
        name = "test_gh238_flat"
        pipeline_cleanup.append(name)
        raw_db_path = tmp_path / "raw.duckdb"
        source_config = SourceConfig(type="filesystem", schema="raw_files", config={"path": str(sales_csv)})

        run_source(name, source_config, raw_db_path=raw_db_path)

        assert _row_count(raw_db_path, "raw_files", name) == 3

    def test_resource_path_to_a_file_loads_its_rows(self, tmp_path, sales_csv, pipeline_cleanup):
        name = "test_gh238_resources"
        pipeline_cleanup.append(name)
        raw_db_path = tmp_path / "raw.duckdb"
        source_config = SourceConfig(
            type="filesystem",
            schema="raw_files",
            resources=[ResourceConfig(table_name="test_gh238_sales", path=str(sales_csv))],
        )

        run_source(name, source_config, raw_db_path=raw_db_path)

        assert _row_count(raw_db_path, "raw_files", "test_gh238_sales") == 3

    def test_flat_file_path_with_glob_fails_clearly(self, sales_csv):
        source_config = SourceConfig(
            type="filesystem",
            schema="raw_files",
            config={"path": str(sales_csv), "file_glob": "*.csv"},
        )
        with pytest.raises(IngestionError, match="path must be a directory when file_glob is set"):
            _build_filesystem_source(source_config)

    def test_resource_file_path_with_glob_fails_clearly(self, sales_csv):
        source_config = SourceConfig(
            type="filesystem",
            schema="raw_files",
            resources=[ResourceConfig(table_name="sales", path=str(sales_csv), file_glob="*.csv")],
        )
        with pytest.raises(IngestionError, match="path must be a directory when file_glob is set"):
            _build_filesystem_source(source_config)

    def test_resource_directory_without_glob_still_fails(self, sales_csv):
        """Only a file path may omit the glob; a directory still needs one."""
        source_config = SourceConfig(
            type="filesystem",
            schema="raw_files",
            resources=[ResourceConfig(table_name="sales", path=str(sales_csv.parent))],
        )
        with pytest.raises(IngestionError, match="missing a path or file_glob"):
            _build_filesystem_source(source_config)

    @pytest.mark.parametrize(
        "url",
        ["s3://bucket/data/sales.csv", "gs://bucket/sales.csv", "az://container/sales.csv", "https://x.io/sales.csv"],
    )
    def test_remote_url_is_left_alone(self, url):
        from tycoon.ingestion.runner import _split_single_file_path

        assert _split_single_file_path(url, "*.csv") == (url, "*.csv")
        assert _split_single_file_path(url, "") == (url, "")
