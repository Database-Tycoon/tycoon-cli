"""Tests for `tycoon data query`, `tycoon data schema`, and `tycoon data clean`."""

from __future__ import annotations

from pathlib import Path

import duckdb

from tycoon.cli import app


class TestSchema:
    def test_schema_runs(self, cli_runner):
        """data schema should run even with no databases (shows WARN status)."""
        result = cli_runner.invoke(app, ["data", "schema"])
        assert result.exit_code == 0
        assert len(result.stdout) > 0

    def test_schema_output_contains_database_labels(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "schema"])
        output = result.stdout
        assert "Raw" in output or "raw" in output or "Warehouse" in output or "warehouse" in output


class TestQuery:
    def test_query_no_database_gives_error(self, cli_runner, tmp_config, monkeypatch):
        """query should fail gracefully when the database file does not exist."""
        monkeypatch.setattr("tycoon.commands.db.config", tmp_config)
        if tmp_config.local_db.exists():
            tmp_config.local_db.unlink()

        result = cli_runner.invoke(app, ["data", "query", "SELECT 1"])
        assert result.exit_code != 0

    def test_query_with_db_flag(self, cli_runner, tmp_path):
        """--db flag should query a specific DuckDB file."""
        db_path = tmp_path / "test.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute("CREATE TABLE t (id INTEGER, name VARCHAR)")
        con.execute("INSERT INTO t VALUES (1, 'alice'), (2, 'bob')")
        con.close()

        result = cli_runner.invoke(app, ["data", "query", "SELECT * FROM t", "--db", str(db_path)])
        assert result.exit_code == 0
        assert "alice" in result.stdout
        assert "bob" in result.stdout

    def test_query_with_source_flag(self, cli_runner, tmp_path, monkeypatch):
        """--source flag should find the right raw DB by schema introspection."""
        from tycoon.config import TycoonConfig

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "tycoon.yml").write_text("name: test\nsources: {}\n")
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        db_path = data_dir / "my_raw.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute("CREATE SCHEMA raw_myapi")
        con.execute("CREATE TABLE raw_myapi.items (id INTEGER, val VARCHAR)")
        con.execute("INSERT INTO raw_myapi.items VALUES (1, 'hello')")
        con.close()

        cfg = TycoonConfig(project_root=tmp_path)
        monkeypatch.setattr("tycoon.commands.db.config", cfg)

        result = cli_runner.invoke(app, ["data", "query", "SELECT * FROM raw_myapi.items", "--source", "myapi"])
        assert result.exit_code == 0
        assert "hello" in result.stdout


class TestDataHelp:
    def test_data_help_shows_query_schema_clean(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "--help"])
        assert result.exit_code == 0
        assert "query" in result.stdout
        assert "schema" in result.stdout
        assert "clean" in result.stdout

    def test_query_help_shows_source_and_db_flags(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "query", "--help"])
        assert result.exit_code == 0
        assert "--source" in result.stdout
        assert "--db" in result.stdout


class TestCleanMetadataPreservation:
    """tycoon data clean must preserve .tycoon/metadata.duckdb unless --metadata."""

    def _setup(self, tmp_path: Path, monkeypatch):
        from tycoon.config import TycoonConfig

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "tycoon.yml").write_text("name: test\nsources: {}\n")
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        meta_dir = tmp_path / ".tycoon"
        meta_dir.mkdir()

        # Seed raw + warehouse + metadata DBs
        raw = data_dir / "raw.duckdb"
        local = data_dir / "warehouse.duckdb"
        meta = meta_dir / "metadata.duckdb"
        for p in (raw, local, meta):
            duckdb.connect(str(p)).close()

        cfg = TycoonConfig(project_root=tmp_path)
        monkeypatch.setattr("tycoon.commands.db.config", cfg)
        return raw, local, meta

    def test_clean_all_preserves_metadata_by_default(self, tmp_path, monkeypatch, cli_runner):
        raw, local, meta = self._setup(tmp_path, monkeypatch)
        # Answer "y" to the confirm prompt
        result = cli_runner.invoke(app, ["data", "clean", "--all"], input="y\n")
        assert result.exit_code == 0
        assert not raw.exists()
        assert not local.exists()
        assert meta.exists(), "metadata.duckdb must survive --all by default"

    def test_clean_all_with_metadata_flag_wipes_metadata(self, tmp_path, monkeypatch, cli_runner):
        raw, local, meta = self._setup(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["data", "clean", "--all", "--metadata"], input="y\n")
        assert result.exit_code == 0
        assert not raw.exists()
        assert not local.exists()
        assert not meta.exists()

    def test_clean_metadata_alone_removes_only_metadata(self, tmp_path, monkeypatch, cli_runner):
        raw, local, meta = self._setup(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["data", "clean", "--metadata"], input="y\n")
        assert result.exit_code == 0
        assert raw.exists()
        assert local.exists()
        assert not meta.exists()

    def test_clean_help_mentions_metadata(self, cli_runner):
        result = cli_runner.invoke(app, ["data", "clean", "--help"])
        assert result.exit_code == 0
        assert "--metadata" in result.stdout


class TestMotherDuckWarehouse:
    """An ``md:`` warehouse is a DuckDB connection string, never a local file (#70)."""

    def _setup(
        self, tmp_path: Path, monkeypatch, warehouse: str = "md:x", raw: str = "data/raw.duckdb"
    ) -> list[tuple[str, dict]]:
        from tycoon.config import TycoonConfig

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "tycoon.yml").write_text(
            f"name: test\nsources: {{}}\ndatabase:\n  warehouse: '{warehouse}'\n  raw: '{raw}'\n"
        )
        cfg = TycoonConfig(project_root=tmp_path)
        monkeypatch.setattr("tycoon.commands.db.config", cfg)

        calls: list[tuple[str, dict]] = []
        real_connect = duckdb.connect

        def fake_connect(database: str = ":memory:", **kwargs):
            calls.append((database, kwargs))
            if str(database).startswith("md:"):
                return real_connect(":memory:")
            return real_connect(database, **kwargs)

        monkeypatch.setattr(duckdb, "connect", fake_connect)
        return calls

    def test_query_connects_to_motherduck_url(self, tmp_path, monkeypatch, cli_runner):
        calls = self._setup(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["data", "query", "SELECT 1"])
        assert result.exit_code == 0, result.stdout
        assert [c[0] for c in calls] == ["md:x"]
        assert "read_only" not in calls[0][1]

    def test_schema_connects_to_motherduck_url(self, tmp_path, monkeypatch, cli_runner):
        calls = self._setup(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["data", "schema"])
        assert result.exit_code == 0, result.stdout
        assert "md:x" in [c[0] for c in calls]
        assert not any("md:" in str(c[0]) and c[0] != "md:x" for c in calls)

    def test_clean_all_skips_motherduck_warehouse(self, tmp_path, monkeypatch, cli_runner):
        self._setup(tmp_path, monkeypatch)
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        raw = data_dir / "raw.duckdb"
        raw.write_bytes(b"")
        bogus = tmp_path / "md:x"
        bogus.write_bytes(b"")

        unlinked: list[Path] = []
        real_unlink = Path.unlink

        def tracking_unlink(self: Path, missing_ok: bool = False) -> None:
            unlinked.append(self)
            real_unlink(self, missing_ok=missing_ok)

        monkeypatch.setattr(Path, "unlink", tracking_unlink)

        result = cli_runner.invoke(app, ["data", "clean", "--all"], input="y\n")
        assert result.exit_code == 0, result.stdout
        assert not raw.exists()
        assert bogus.exists()
        assert not any("md:" in str(p) for p in unlinked)
        assert "MotherDuck" in result.stdout

    def test_clean_local_only_deletes_nothing(self, tmp_path, monkeypatch, cli_runner):
        self._setup(tmp_path, monkeypatch)
        bogus = tmp_path / "md:x"
        bogus.write_bytes(b"")
        result = cli_runner.invoke(app, ["data", "clean", "--local"], input="y\n")
        assert result.exit_code == 0, result.stdout
        assert bogus.exists()
        assert "MotherDuck" in result.stdout

    def test_schema_hides_motherduck_token(self, tmp_path, monkeypatch, cli_runner):
        calls = self._setup(tmp_path, monkeypatch, warehouse="md:x?motherduck_token=SECRET123")
        result = cli_runner.invoke(app, ["data", "schema"])
        assert result.exit_code == 0, result.stdout
        assert "md:x?motherduck_token=SECRET123" in [c[0] for c in calls]
        assert "SECRET123" not in result.stdout
        assert "motherduck_token" not in result.stdout

    def test_schema_error_hides_motherduck_token(self, tmp_path, monkeypatch, cli_runner):
        self._setup(tmp_path, monkeypatch, warehouse="md:x?motherduck_token=SECRET123")

        def failing_connect(database: str = ":memory:", **kwargs):
            raise duckdb.IOException(f"can't open '{database}'")

        monkeypatch.setattr(duckdb, "connect", failing_connect)
        result = cli_runner.invoke(app, ["data", "schema"])
        assert result.exit_code == 0, result.stdout
        assert "WARN" in result.stdout
        assert "SECRET123" not in result.stdout

    def test_clean_warning_hides_motherduck_token(self, tmp_path, monkeypatch, cli_runner):
        self._setup(tmp_path, monkeypatch, warehouse="md:x?motherduck_token=SECRET123")
        result = cli_runner.invoke(app, ["data", "clean", "--local"], input="y\n")
        assert result.exit_code == 0, result.stdout
        assert "MotherDuck (md:x)" in result.stdout
        assert "SECRET123" not in result.stdout

    def test_clean_all_never_deletes_motherduck_raw(self, tmp_path, monkeypatch, cli_runner):
        self._setup(tmp_path, monkeypatch, raw="md:x_raw")
        bogus = tmp_path / "md:x_raw"
        bogus.write_bytes(b"")
        result = cli_runner.invoke(app, ["data", "clean", "--all"], input="y\n")
        assert result.exit_code == 0, result.stdout
        assert bogus.exists()
        assert "Raw database is MotherDuck (md:x_raw)" in result.stdout

    def test_schema_labels_motherduck_raw(self, tmp_path, monkeypatch, cli_runner):
        calls = self._setup(tmp_path, monkeypatch, raw="md:x_raw?motherduck_token=SECRET123")
        (tmp_path / "md:x_raw").write_bytes(b"")
        result = cli_runner.invoke(app, ["data", "schema"])
        assert result.exit_code == 0, result.stdout
        assert "md:x_raw?motherduck_token=SECRET123" in [c[0] for c in calls]
        assert "MotherDuck md:x_raw" in result.stdout
        assert "SECRET123" not in result.stdout

    def test_query_raw_connects_to_motherduck_url(self, tmp_path, monkeypatch, cli_runner):
        calls = self._setup(tmp_path, monkeypatch, raw="md:x_raw")
        result = cli_runner.invoke(app, ["data", "query", "--raw", "SELECT 1"])
        assert result.exit_code == 0, result.stdout
        assert [c[0] for c in calls] == ["md:x_raw"]
        assert "read_only" not in calls[0][1]


WIDE_COLUMNS = [f"metric_column_number_{i}" for i in range(12)]


def _wide_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "wide.duckdb"
    con = duckdb.connect(str(db_path))
    select = ", ".join(f"'value {i}' AS {name}" for i, name in enumerate(WIDE_COLUMNS))
    con.execute(f"CREATE TABLE wide AS SELECT 'M15' AS route_id, 1.50::DECIMAL(4,2) AS fare, NULL AS notes, {select}")
    con.close()
    return db_path


class TestQueryFormats:
    """gh-391: machine-readable output, and no squashed headers on wide results."""

    def _query(self, cli_runner, db_path: Path, *args: str):
        return cli_runner.invoke(app, ["data", "query", "SELECT * FROM wide", "--db", str(db_path), *args])

    def test_csv_prints_only_rows(self, cli_runner, tmp_path):
        result = self._query(cli_runner, _wide_db(tmp_path), "--format", "csv")
        assert result.exit_code == 0
        lines = result.stdout.splitlines()
        assert lines[0] == ",".join(["route_id", "fare", "notes", *WIDE_COLUMNS])
        assert lines[1].startswith("M15,1.50,,value 0,")
        assert len(lines) == 2

    def test_json_prints_only_parseable_rows(self, cli_runner, tmp_path):
        import json

        result = self._query(cli_runner, _wide_db(tmp_path), "--format", "json")
        assert result.exit_code == 0
        records = json.loads(result.stdout)
        assert records[0]["route_id"] == "M15"
        assert records[0]["fare"] == 1.5
        assert records[0]["notes"] is None
        assert records[0]["metric_column_number_11"] == "value 11"

    def test_markdown_escapes_pipes(self, cli_runner, tmp_path):
        db_path = tmp_path / "pipes.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute("CREATE TABLE wide AS SELECT 'a|b' AS label, NULL AS notes")
        con.close()

        result = self._query(cli_runner, db_path, "-f", "markdown")
        assert result.exit_code == 0
        assert result.stdout.splitlines() == [
            "| label | notes |",
            "| --- | --- |",
            r"| a\|b |  |",
        ]

    def test_unknown_format_is_a_usage_error(self, cli_runner, tmp_path):
        result = self._query(cli_runner, _wide_db(tmp_path), "--format", "xml")
        assert result.exit_code == 2

    def test_wide_table_prints_one_block_per_record(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.setenv("COLUMNS", "100")
        result = self._query(cli_runner, _wide_db(tmp_path))
        assert result.exit_code == 0
        assert "metric_column_number_11" in result.stdout
        assert "record 1" in result.stdout
        assert "…" not in result.stdout
        assert "1 row(s) returned" in result.stdout

    def test_narrow_table_keeps_the_column_layout(self, cli_runner, tmp_path, monkeypatch):
        monkeypatch.setenv("COLUMNS", "100")
        result = cli_runner.invoke(
            app, ["data", "query", "SELECT route_id, fare FROM wide", "--db", str(_wide_db(tmp_path))]
        )
        assert result.exit_code == 0
        assert "record 1" not in result.stdout
        header = next(line for line in result.stdout.splitlines() if "route_id" in line)
        assert "fare" in header


class TestSchemaFilters:
    """gh-393: narrow `data schema` to one database, one schema, and no dlt bookkeeping."""

    def _setup(self, tmp_path: Path, monkeypatch) -> None:
        from tycoon.config import TycoonConfig

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "tycoon.yml").write_text("name: test\nsources: {}\n")
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        raw = duckdb.connect(str(data_dir / "raw.duckdb"))
        for schema_name in ("raw_bus", "raw_traffic"):
            raw.execute(f"CREATE SCHEMA {schema_name}")
            raw.execute(f"CREATE TABLE {schema_name}.events AS SELECT 1 AS id")
            raw.execute(f"CREATE TABLE {schema_name}._dlt_loads AS SELECT 1 AS load_id")
        raw.close()

        warehouse = duckdb.connect(str(data_dir / "warehouse.duckdb"))
        for schema_name in ("main_staging", "main_marts"):
            warehouse.execute(f"CREATE SCHEMA {schema_name}")
            warehouse.execute(f"CREATE TABLE {schema_name}.model_in_{schema_name} AS SELECT 1 AS id")
        warehouse.close()

        extra = duckdb.connect(str(data_dir / "snapshot.duckdb"))
        extra.execute("CREATE TABLE snapshot_table AS SELECT 1 AS id")
        extra.close()

        monkeypatch.setattr("tycoon.commands.db.config", TycoonConfig(project_root=tmp_path))
        monkeypatch.setenv("COLUMNS", "200")

    def test_hides_dlt_tables_by_default(self, tmp_path, monkeypatch, cli_runner):
        self._setup(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["data", "schema"])
        assert result.exit_code == 0, result.stdout
        assert "raw_bus.events" in result.stdout
        assert "_dlt_loads" not in result.stdout
        assert "2 _dlt_* hidden" in result.stdout
        assert "snapshot_table" in result.stdout

    def test_include_dlt_shows_them(self, tmp_path, monkeypatch, cli_runner):
        self._setup(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["data", "schema", "--include-dlt"])
        assert result.exit_code == 0, result.stdout
        assert "raw_bus._dlt_loads" in result.stdout
        assert "hidden" not in result.stdout

    def test_schema_name_matches_exactly(self, tmp_path, monkeypatch, cli_runner):
        self._setup(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["data", "schema", "--schema", "main_marts"])
        assert result.exit_code == 0, result.stdout
        assert "main_marts.model_in_main_marts" in result.stdout
        assert "main_staging" not in result.stdout
        assert "raw_bus" not in result.stdout

    def test_schema_glob(self, tmp_path, monkeypatch, cli_runner):
        self._setup(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["data", "schema", "--schema", "RAW_*"])
        assert result.exit_code == 0, result.stdout
        assert "raw_bus.events" in result.stdout
        assert "raw_traffic.events" in result.stdout
        assert "main_marts" not in result.stdout

    def test_schema_with_no_match_warns(self, tmp_path, monkeypatch, cli_runner):
        self._setup(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["data", "schema", "--schema", "nope"])
        assert result.exit_code == 0, result.stdout
        assert "No tables in a schema matching 'nope'" in result.stdout

    def test_raw_shows_only_the_raw_database(self, tmp_path, monkeypatch, cli_runner):
        self._setup(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["data", "schema", "--raw"])
        assert result.exit_code == 0, result.stdout
        assert "Raw database" in result.stdout
        assert "Warehouse database" not in result.stdout
        assert "snapshot" not in result.stdout

    def test_warehouse_shows_only_the_warehouse(self, tmp_path, monkeypatch, cli_runner):
        self._setup(tmp_path, monkeypatch)
        result = cli_runner.invoke(app, ["data", "schema", "--warehouse"])
        assert result.exit_code == 0, result.stdout
        assert "Warehouse database" in result.stdout
        assert "Raw database" not in result.stdout
        assert "snapshot" not in result.stdout

    def test_motherduck_counts_only_the_tables_it_shows(self, monkeypatch):
        """#310: every count(*) on MotherDuck costs a query, so filtered-out tables aren't counted."""
        from tycoon.commands import db

        con = duckdb.connect(":memory:")
        con.execute("CREATE SCHEMA main_marts")
        con.execute("CREATE TABLE main_marts.kept AS SELECT 1 AS id")
        con.execute("CREATE TABLE main_marts._dlt_loads AS SELECT 1 AS id")
        con.execute("CREATE TABLE main.skipped AS SELECT 1 AS id")
        executed: list[str] = []

        class RecordingConnection:
            def execute(self, sql: str):
                executed.append(sql)
                return con.execute(sql)

            def close(self) -> None:
                pass

        monkeypatch.setattr(duckdb, "connect", lambda *args, **kwargs: RecordingConnection())

        rows, shown = db._motherduck_schema_rows("md:x", "Warehouse", "main_marts", include_dlt=False)

        assert shown == 1
        assert ("  main_marts.kept", "", "1 rows") in rows
        counts = [sql for sql in executed if sql.startswith("SELECT count(*)")]
        assert counts == ['SELECT count(*) FROM "main_marts"."kept"']
