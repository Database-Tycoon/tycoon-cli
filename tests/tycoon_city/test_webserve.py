"""One happy and one error path per endpoint, per the verification budget for
HTTP plumbing. The server runs live on port 0 in a thread -- these test what a
client receives, not handler internals."""

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import duckdb
import pytest

from tycoon_city import webserve
from tycoon_city.export.city_json import FORMAT
from tycoon_city.webserve import DEFAULT_HOST, _Handler, _SourceCache


@pytest.fixture
def site(tmp_path):
    db = tmp_path / "fx.duckdb"
    con = duckdb.connect(str(db))
    con.execute("create schema raw")
    con.execute("create table raw.orders as select * from range(5) t(id)")
    con.execute("create view main.v_orders as select * from raw.orders")
    con.close()

    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>fx</title>")
    (dist / "assets").mkdir()
    (dist / "assets" / "app.js").write_text("// bundle")
    # A stale baked copy, as a real Vite build of public/ would leave behind:
    # the dynamic route must win over it.
    (dist / "city.json").write_text('{"stale": true}')

    handler = type(
        "Handler",
        (_Handler,),
        # Its own cache, as `serve` gives each server: no test may inherit
        # another test's build.
        {"db_path": str(db), "theme_name": "default", "dist": dist, "cache": _SourceCache()},
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}", db
    server.shutdown()


def _get(url: str) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def test_city_json_is_generated_fresh_not_served_from_dist(site):
    base, _ = site
    status, body = _get(f"{base}/city.json")

    assert status == 200
    document = json.loads(body)
    # The baked {"stale": true} in dist must lose to the dynamic export.
    assert document.get("format") == FORMAT
    assert document["database"]["name"] == "fx"


def test_meta_json_reports_no_export_time_and_says_why(site):
    """The served city.json was built FOR this request, so there is no earlier
    moment to report and `generated_at` is null. A client reads that as "measure
    my own fetch", which is the truth here and a lie for a static export.

    200-with-a-null rather than 404 on purpose: one question, one document, one
    named answer. And it must survive a database the server cannot read -- this
    route describes the DOCUMENT's provenance, not the catalog's health."""
    base, db = site
    status, body = _get(f"{base}/meta.json")

    assert status == 200
    document = json.loads(body)
    assert document["format"] == "database-tycoon.meta"
    assert document["generated_at"] is None
    assert "fetch" in document["note"], "a null must arrive with the reason for it"

    db.unlink()  # the bad-volume-mount failure mode; /healthz 503s, this must not
    assert _get(f"{base}/meta.json")[0] == 200


def test_healthz_reports_counts_and_503_on_a_bad_database(site, tmp_path):
    base, db = site
    status, body = _get(f"{base}/healthz")
    assert status == 200
    assert json.loads(body)["objects"] == 2

    db.unlink()  # the bad-volume-mount failure mode
    status, body = _get(f"{base}/healthz")
    assert status == 503
    assert json.loads(body)["status"] == "error"


def test_static_bundle_and_spritesheet_are_served(site):
    base, _ = site
    assert _get(f"{base}/")[0] == 200
    assert b"fx" in _get(f"{base}/index.html")[1]
    assert _get(f"{base}/assets/app.js")[0] == 200
    status, body = _get(f"{base}/spritesheet.png")
    assert status == 200
    assert body[:4] == b"\x89PNG"


def test_paths_outside_the_bundle_are_refused(site):
    base, _ = site
    assert _get(f"{base}/../pyproject.toml")[0] == 404
    assert _get(f"{base}/%2e%2e/%2e%2e/etc/hosts")[0] == 404
    assert _get(f"{base}/missing.js")[0] == 404


# --- The bind ----------------------------------------------------------------


def _bound_address(monkeypatch, argv, tmp_path):
    """The address `main` actually hands to the socket, without serving."""
    dist = tmp_path / "dist"
    dist.mkdir(exist_ok=True)
    (dist / "index.html").write_text("x")
    captured = {}

    class _FakeServer:
        def __init__(self, address, handler):
            captured["address"] = address

        def serve_forever(self):
            captured["served"] = True

    monkeypatch.setattr(webserve, "ThreadingHTTPServer", _FakeServer)
    monkeypatch.delenv("DATABASE_TYCOON_HOST", raising=False)
    assert webserve.main([str(tmp_path / "any.duckdb"), "--dist", str(dist), *argv]) == 0
    assert captured.get("served"), "main returned without ever serving"
    return captured["address"][0]


def test_the_default_bind_is_loopback_and_wider_exposure_is_explicit(monkeypatch, tmp_path):
    """A catalog names a client's schemas, tables and columns. Binding every
    interface by default published that to the whole network; it is now an
    argument the operator has to type."""
    assert DEFAULT_HOST == "127.0.0.1"
    assert _bound_address(monkeypatch, [], tmp_path) == "127.0.0.1"
    assert _bound_address(monkeypatch, ["--host", "0.0.0.0"], tmp_path) == "0.0.0.0"


# --- The mtime cache ---------------------------------------------------------


def _object_keys(document) -> set[str]:
    return {o["key"] for o in document["objects"]}


def test_the_catalog_is_rebuilt_when_a_source_file_moves_and_not_before(site, monkeypatch):
    """The core loop is "edit the database, press R". Rebuilding the whole
    catalog per request was that loop's cost; serving a cached copy of a file
    that has already changed would be worse than the cost. Both directions are
    asserted here, with the loader's real invocation count as the witness."""
    base, db = site
    builds = []
    real_build = webserve.build_city

    def counting(db_path, style_rules, *args, **kwargs):
        builds.append(db_path)
        return real_build(db_path, style_rules, *args, **kwargs)

    monkeypatch.setattr(webserve, "build_city", counting)

    first = json.loads(_get(f"{base}/city.json")[1])
    assert len(builds) == 1, "the first request must build"

    stamp = db.stat().st_mtime_ns
    second = json.loads(_get(f"{base}/city.json")[1])
    assert len(builds) == 1, "nothing moved, so nothing may be rebuilt"
    assert _object_keys(second) == _object_keys(first)

    con = duckdb.connect(str(db))
    con.execute("create table raw.shipments as select * from range(3) t(id)")
    con.close()
    # Precondition: the file really moved. Without this the rebuild below
    # could be passing for any reason at all.
    assert db.stat().st_mtime_ns != stamp, "the fixture did not change the file"

    third = json.loads(_get(f"{base}/city.json")[1])
    assert len(builds) == 2, "a changed file must rebuild"
    # And the change reaches the client -- a rebuild that served the old
    # document would satisfy the counter and still be the bug.
    assert _object_keys(third) - _object_keys(first) == {"raw.shipments"}


def test_healthz_and_city_json_share_one_build(site, monkeypatch):
    base, _ = site
    builds = []
    real_build = webserve.build_city

    def counting(db_path, style_rules, *args, **kwargs):
        builds.append(db_path)
        return real_build(db_path, style_rules, *args, **kwargs)

    monkeypatch.setattr(webserve, "build_city", counting)

    assert _get(f"{base}/healthz")[0] == 200
    assert _get(f"{base}/city.json")[0] == 200
    assert len(builds) == 1


def test_an_unfingerprintable_source_is_never_cached(tmp_path):
    """`md:` catalogs have no files behind them, so there is nothing that could
    say they are unchanged; they must rebuild every time rather than be served
    from a key that cannot move."""
    assert webserve._fingerprint("md:some_catalog") is None
    assert webserve._fingerprint(str(tmp_path / "not_a_project_dir")) is not None


def test_the_fingerprint_covers_every_file_of_a_tycoon_project(tmp_path):
    """The manifest, sources.json and metadata db each change the loaded
    context on their own, so each has to be in the key. A manifest that did
    not exist last request and does now counts as a change too."""
    from tests.fixtures.tycoon_factory import make_tycoon_project

    root = make_tycoon_project(tmp_path / "fx")
    files = {p.name for p in webserve._source_files(str(root))}
    assert {"tycoon.yml", "manifest.json", "metadata.duckdb"} <= files

    before = webserve._fingerprint(str(root))
    (root / "dbt" / "target" / "sources.json").write_text('{"results": []}')
    assert webserve._fingerprint(str(root)) != before, "a new artifact must move the key"


def test_fingerprint_includes_duckdb_wal_sidecar(tmp_path):
    """The mtime/WAL staleness trap (handover, 2026-08-07): DuckDB can leave
    committed writes in a `.wal` sidecar, so the main file's mtime stays old
    while the content has changed. The fingerprint must include the `-wal`
    sidecar so a WAL update invalidates the cache.

    This is exactly what the bug was: the server served an old catalog because
    the main `.duckdb` file's mtime was stale, while the `.wal` sidecar had
    the actual content.
    """
    db = tmp_path / "wal_test.duckdb"
    # Create a minimal DuckDB file
    con = duckdb.connect(str(db))
    con.execute("create schema raw")
    con.execute("create table raw.test as select * from range(3) t(id)")
    con.close()

    # Fingerprint without WAL
    fp_no_wal = webserve._fingerprint(str(db))
    assert fp_no_wal is not None

    # Now create a WAL sidecar with a future mtime
    wal = tmp_path / "wal_test.duckdb-wal"
    wal.write_bytes(b"fake wal content")
    # Set the WAL's mtime to the far future (10 years ahead) in nanoseconds
    import os as _os
    import time

    future_time_ns = int((time.time() + 10 * 365 * 24 * 3600) * 1e9)
    _os.utime(wal, (future_time_ns / 1e9, future_time_ns / 1e9))

    # Fingerprint WITH WAL
    fp_with_wal = webserve._fingerprint(str(db))
    assert fp_with_wal is not None

    # The fingerprints must differ — the WAL sidecar changes the fingerprint
    assert fp_no_wal != fp_with_wal, "WAL sidecar must change the fingerprint to detect uncheckpointed writes"

    # The WAL path must appear in the fingerprint
    wal_str = str(wal)
    wal_entries = [e for e in fp_with_wal if wal_str in e[0]]
    assert len(wal_entries) == 1, "WAL sidecar must appear exactly once in fingerprint"
    # The WAL's mtime must be a large future value (within float precision of
    # the nanosecond conversion). The key assertion is that the WAL appears in
    # the fingerprint, proving the fix works.
    wal_mtime = wal_entries[0][1]
    assert wal_mtime > future_time_ns - 1_000_000_000, (
        f"WAL mtime {wal_mtime} should be ~{future_time_ns} (within 1s float precision)"
    )


def test_fingerprint_returns_none_for_md_catalogs(tmp_path):
    """`md:` catalogs have no files behind them, so there is nothing that could
    say they are unchanged; they must rebuild every time rather than be served
    from a key that cannot move."""
    assert webserve._fingerprint("md:some_catalog") is None
    assert webserve._fingerprint(str(tmp_path / "not_a_project_dir")) is not None


# --- The run-replay routes ---------------------------------------------------


@pytest.fixture
def replay_site(tmp_path):
    """A server over the failure-cascade project, so /runs routes have a real
    run with a failure and the skips behind it."""
    from tests.fixtures.tycoon_factory import make_cascade_project

    root = make_cascade_project(tmp_path / "fx")
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html>")

    handler = type(
        "Handler",
        (_Handler,),
        {"db_path": str(root), "theme_name": "default", "dist": dist, "cache": _SourceCache()},
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_the_runs_routes_serve_the_index_and_one_replayable_run(replay_site):
    status, body = _get(f"{replay_site}/runs.json")
    assert status == 200
    index = json.loads(body)
    assert [run["id"] for run in index["runs"]] == ["odd-1", "partial-1", "build-1"]

    status, body = _get(f"{replay_site}/runs/build-1.json")
    assert status == 200
    document = json.loads(body)
    assert document["run"]["id"] == "build-1"
    # The whole point of the feature, over the wire: hand-counted off the
    # fixture DAG in tycoon_factory.
    assert document["failure_cascade"] == [
        {
            "object_key": "mart.zz_fail",
            "order": 1,
            "skipped": ["mart.aa_skip", "mart.bb_skip_deep"],
        }
    ]


def test_an_unknown_run_id_is_a_404_with_a_body_and_never_touches_a_path(replay_site):
    """The id is matched against the known invocation set before it is used for
    anything at all -- which is why a traversal attempt is just another unknown
    id rather than a file read."""
    status, body = _get(f"{replay_site}/runs/never-happened.json")
    assert status == 404
    assert json.loads(body)["error"] == "unknown run"

    assert _get(f"{replay_site}/runs/../../pyproject.toml.json")[0] == 404
    assert _get(f"{replay_site}/runs/%2e%2e%2f%2e%2e%2fetc%2fhosts.json")[0] == 404


def test_runs_json_is_200_with_the_reason_when_there_is_no_history(site):
    """`site` is a plain DuckDB file: no tycoon project, no run metadata. An
    empty list plus a note beats a 404 -- a client cannot tell 404 "no runs"
    from 404 "wrong host"."""
    from tycoon_city.export.run_json import NO_HISTORY_NOTE

    base, _ = site
    status, body = _get(f"{base}/runs.json")

    assert status == 200
    index = json.loads(body)
    assert index["runs"] == []
    assert NO_HISTORY_NOTE in index["notes"]


def test_the_runs_routes_share_the_one_cached_build(replay_site, monkeypatch):
    builds = []
    real_build = webserve.build_city

    def counting(db_path, style_rules, *args, **kwargs):
        builds.append(db_path)
        return real_build(db_path, style_rules, *args, **kwargs)

    monkeypatch.setattr(webserve, "build_city", counting)

    assert _get(f"{replay_site}/city.json")[0] == 200
    assert _get(f"{replay_site}/runs.json")[0] == 200
    assert _get(f"{replay_site}/runs/build-1.json")[0] == 200
    assert len(builds) == 1, "the run routes must reuse the mtime cache"
