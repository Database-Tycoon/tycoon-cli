"""One happy path and one error path, per the plan's verification budget for
CLI plumbing. The contract itself is tested in test_city_json.py."""

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from tycoon_city.export.cli import main, meta_document


def _make_db(path: Path) -> None:
    con = duckdb.connect(str(path))
    con.execute("create schema raw")
    con.execute("create table raw.orders as select * from range(5) t(id)")
    con.execute("create view main.v_orders as select * from raw.orders")
    con.close()


def test_export_writes_a_self_contained_directory(tmp_path, capsys):
    db = tmp_path / "fx.duckdb"
    out = tmp_path / "site"
    _make_db(db)

    assert main([str(db), str(out)]) == 0

    document = json.loads((out / "city.json").read_text(encoding="utf-8"))
    # The spritesheet the document names must actually be next to it, or a
    # static host serves a city with no textures.
    assert (out / document["theme"]["spritesheet"]).exists()
    assert document["database"]["name"] == "fx"

    printed = capsys.readouterr().out
    assert "city.json" in printed


def test_missing_database_reports_and_exits_nonzero(tmp_path, capsys):
    assert main([str(tmp_path / "nope.duckdb"), str(tmp_path / "site")]) == 1

    assert "not found" in capsys.readouterr().err


def test_export_writes_the_run_documents_at_the_routes_own_paths(tmp_path):
    """The contract doc promises an output directory a static host can serve
    as-is. Without these, a static export silently loses replay -- and the
    paths must be the ones the server routes at, or a client written against
    the routes breaks on the static copy."""
    from tests.fixtures.tycoon_factory import make_cascade_project

    root = make_cascade_project(tmp_path / "fx")
    out = tmp_path / "site"

    assert main([str(root), str(out)]) == 0

    index = json.loads((out / "runs.json").read_text(encoding="utf-8"))
    assert [run["id"] for run in index["runs"]] == ["odd-1", "partial-1", "build-1"]
    # Every listed run has its document, at /runs/<id>.json.
    for run in index["runs"]:
        assert (out / "runs" / f"{run['id']}.json").is_file()

    document = json.loads((out / "runs" / "build-1.json").read_text(encoding="utf-8"))
    assert document["failure_cascade"] == [
        {
            "object_key": "mart.zz_fail",
            "order": 1,
            "skipped": ["mart.aa_skip", "mart.bb_skip_deep"],
        }
    ]


def test_export_writes_an_index_even_with_no_run_history(tmp_path):
    """A missing runs.json is indistinguishable from a broken host; an empty
    one carries the reason."""
    db = tmp_path / "fx.duckdb"
    out = tmp_path / "site"
    _make_db(db)

    assert main([str(db), str(out)]) == 0

    index = json.loads((out / "runs.json").read_text(encoding="utf-8"))
    assert index["runs"] == []
    assert index["notes"], "an empty index must say why it is empty"
    assert not (out / "runs").exists(), "no documents, so no directory"


# --- meta.json: the export's own freshness --------------------------------
#
# THE BUG THESE GUARD: the footer's age was measured from the CLIENT's fetch,
# which is right for the live server and wrong for a static export -- a
# week-old city.json on a CDN read "as of 3s ago". The fix is a sibling
# document, because city.json may never carry a timestamp.


def test_export_writes_a_meta_sibling_carrying_the_export_time(tmp_path):
    db = tmp_path / "fx.duckdb"
    out = tmp_path / "site"
    _make_db(db)

    before = datetime.now(UTC).replace(microsecond=0)
    assert main([str(db), str(out)]) == 0
    after = datetime.now(UTC)

    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    assert meta["format"] == "database-tycoon.meta"
    assert meta["version"] == 1
    # A REAL time, bracketed by the export -- not merely "a string is present",
    # which a hardcoded epoch would also satisfy.
    stamp = datetime.fromisoformat(meta["generated_at"].replace("Z", "+00:00"))
    assert stamp.tzinfo is not None, "an export time with no zone is not a time"
    assert before <= stamp <= after
    assert meta["note"]


def test_meta_carries_the_timestamp_that_city_json_may_never_carry(tmp_path):
    """The contract's byte-stability is the reason this document exists at all;
    a `generated_at` that leaked into city.json would break the golden AND make
    the sibling pointless."""
    db = tmp_path / "fx.duckdb"
    _make_db(db)
    first, second = tmp_path / "a", tmp_path / "b"

    assert main([str(db), str(first)]) == 0
    assert main([str(db), str(second)]) == 0

    city = (first / "city.json").read_bytes()
    assert city == (second / "city.json").read_bytes(), "city.json must stay byte-stable"
    assert b"generated_at" not in city
    # …while the sibling right next to it does carry one.
    assert json.loads((first / "meta.json").read_text())["generated_at"] is not None


def test_a_producer_with_no_export_time_says_so_rather_than_inventing_one():
    """`generated_at: null` is the live server's honest answer, and it must be
    a NAMED absence: the note has to explain it, because a client that sees a
    null has to tell "no export time" from "broken producer"."""
    served = meta_document(None)

    assert served["generated_at"] is None
    assert "fetch" in served["note"], "a null must arrive with the reason for it"
    assert served["note"] != meta_document(datetime.now(UTC))["note"]


def test_the_export_stamp_is_utc_whatever_the_local_clock_says():
    """A naive or offset-bearing datetime must still serialise as UTC `Z`: the
    client parses one spelling, and a local-time stamp would read as hours of
    drift on a machine in another zone."""
    from datetime import timedelta, timezone

    noon_utc = datetime(2026, 8, 6, 12, 0, 0, 500_000, tzinfo=UTC)
    assert meta_document(noon_utc)["generated_at"] == "2026-08-06T12:00:00Z"

    # The same instant, expressed in UTC+02:00 -- the SAME output.
    same_instant = noon_utc.astimezone(timezone(timedelta(hours=2)))
    assert meta_document(same_instant)["generated_at"] == "2026-08-06T12:00:00Z"
