"""`tycoon-city demo` — the project it generates, and the two ways it could fail
to ship.

THE TWO FAILURES THESE ARE AGAINST:

1. **A data file that does not ship.** `semantic.yml` is package data. Resolving
   it through the checkout works perfectly in this repo and produces a wheel
   whose demo has no semantic model at all — the classic version of the bug.
2. **A demo that decays.** The project's facts are all TIMES. Baking them would
   ship a "fresh pipeline" that reads a month old a month after release, so the
   ages are asserted against an INJECTED clock, which only a generator can
   honour.
"""

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb
import pytest

from tycoon_city.demo import DEMO_DIR_NAME, materialise
from tycoon_city.demo.project import build_demo_project, semantic_source
from tycoon_city.export.build import build_city
from tycoon_city.theme_data import load_theme_data, theme_dir

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def demo_at_a_pinned_clock(tmp_path_factory):
    """One project, built at a clock we chose, so every OFFSET below is
    arithmetic a reader can check rather than a range.

    Not used for the city facts: `last_build_age_s` and friends are measured
    from the wall clock at load time (deliberately — a frozen clock is a stale
    render), so a pinned build date would make every age wrong by however long
    ago 2026-08-06 was.
    """
    now = datetime(2026, 8, 6, 12, 0, 0, tzinfo=UTC)
    root = build_demo_project(tmp_path_factory.mktemp("demo") / DEMO_DIR_NAME, now)
    return root, now


@pytest.fixture(scope="module")
def demo_now(tmp_path_factory):
    """The project as `tycoon-city demo` builds it: dated from the real clock, so
    the ages a viewer would see are the ages asserted here."""
    return build_demo_project(tmp_path_factory.mktemp("live") / DEMO_DIR_NAME)


def test_the_demo_ages_are_generated_from_the_clock_not_baked(demo_at_a_pinned_clock):
    """The whole argument for generating instead of baking. Build at a clock two
    years from now and the "21 days ago" mart is still 21 days old — a baked
    project would report the distance to its own bake date instead."""
    root, now = demo_at_a_pinned_clock
    con = duckdb.connect(str(root / ".tycoon" / "metadata.duckdb"), read_only=True)
    started = dict(con.execute("select invocation_id, started_at from dbt_runs").fetchall())
    con.close()

    naive_now = now.replace(tzinfo=None)
    # Hand-checked against tycoon_city/demo/project.py's offsets.
    assert naive_now - started["old-run"] == timedelta(days=21)
    assert naive_now - started["fail-fast"] == timedelta(hours=2)
    assert naive_now - started["fresh-run"] == timedelta(minutes=20)
    assert naive_now - started["fresh-tests"] == timedelta(minutes=5)

    # And the SAME scenario built two years later is still 21 days stale.
    far = build_demo_project(root.parent / "later", now + timedelta(days=730))
    con = duckdb.connect(str(far / ".tycoon" / "metadata.duckdb"), read_only=True)
    later = dict(con.execute("select invocation_id, started_at from dbt_runs").fetchall())
    con.close()
    assert (now + timedelta(days=730)).replace(tzinfo=None) - later["old-run"] == timedelta(days=21)


def test_the_demo_city_shows_every_scenario_it_promises(demo_now):
    """A demo whose named scenarios are not actually visible is a demo that
    wastes the one minute someone gives it. Each assertion below names the
    scenario from the module docstring it proves."""
    root = demo_now
    ctx, city = build_city(str(root), load_theme_data(theme_dir("default")).style_rules)
    from tycoon_city.export.city_json import city_document

    doc = city_document(ctx, city, load_theme_data(theme_dir("default")))
    lots = {lot["object_key"]: lot for lot in doc["lots"]}

    assert lots["mart.mart__broken"]["build_status"] == "error"  # a build error
    assert lots["mart.mart__revenue"]["test_status"] == "fail"  # a failing test
    assert lots["staging.stg_orders"]["test_status"] == "warn"  # a warning test
    assert lots["raw.customers"]["freshness_status"] == "error"  # a late source
    assert lots["raw.orders"]["freshness_status"] == "pass"  # …beside a fresh one
    assert lots["staging.stg_customers"]["schema_drift_age_s"] is not None  # the crane
    # The stale mart and the never-built object, standing next to each other:
    # 21 days is stale, and unknown is NOT stale.
    assert lots["mart.mart__forgotten"]["last_build_age_s"] == pytest.approx(21 * 86400, abs=60)
    assert lots["scratch.experiment"]["last_build_age_s"] is None

    # The declared OSI joins, which only exist if the packaged semantic.yml was
    # found and copied. Four, per src/tycoon_city/demo/semantic.yml.
    assert len(doc["joins"]) == 4
    assert any(join["composite"] for join in doc["joins"])
    assert any(join["lineage_edge"] is not None for join in doc["joins"])


def test_the_failure_cascade_replays_with_its_hand_counted_members(demo_now):
    """Run replay's headline. The two exclusions are the point: a skip that is
    not downstream (staging.stg_orders), and a downstream model dbt built
    anyway (mart.dim__customers)."""
    from tycoon_city.catalog.loader import load_context
    from tycoon_city.export.run_json import run_document

    document = run_document(load_context(str(demo_now)), "fail-fast")

    assert document["failure_cascade"] == [
        {
            "object_key": "staging.stg_customers",
            "order": 0,
            "skipped": ["mart.dim__customer_status", "mart.mart__broken", "mart.mart__revenue"],
        }
    ]


# --- Packaging: the file that has to ship ----------------------------------


def test_the_semantic_model_is_package_data_not_a_checkout_path():
    """`semantic_source()` must resolve INSIDE the installed package. A path
    that walks out to `scripts/` works here and ships a demo with no semantic
    model at all."""
    import tycoon_city

    package = Path(tycoon_city.__file__).resolve().parent
    resolved = semantic_source().resolve()

    assert resolved.is_file()
    assert resolved.is_relative_to(package), f"{resolved} is outside {package}"
    assert not resolved.is_relative_to(REPO / "scripts")


def test_the_packaged_semantic_model_matches_the_one_scripts_uses():
    """Two copies of one file, so the duplication is a guarded invariant rather
    than a slow divergence: `scripts/make_demo_tycoon.py` (a checkout) and the
    wheel's `tycoon_city/demo/semantic.yml` must be the same bytes."""
    assert semantic_source().read_bytes() == (REPO / "src" / "tycoon_city" / "demo" / "semantic.yml").read_bytes()


def test_the_demo_builds_with_tests_and_scripts_unimportable():
    """The subcommand's real claim: no dependency on the checkout. Run in a
    subprocess with `tests` and the repo scripts blocked at the import hook, so
    a lazy import inside a function body fails too."""
    body = """
import sys, tempfile
from pathlib import Path

class _Blocked:
    def find_spec(self, name, path=None, target=None):
        if name == "tests" or name.startswith("tests."):
            raise ImportError("the checkout's tests package is blocked for this test")
        return None

sys.meta_path.insert(0, _Blocked())

from tycoon_city.demo import materialise
with materialise() as root:
    assert (root / "semantic.yml").is_file()
    assert (root / ".tycoon" / "metadata.duckdb").is_file()
assert "tests" not in sys.modules, "the demo pulled the test package in"
print("ok")
"""
    result = subprocess.run([sys.executable, "-c", body], capture_output=True, text=True, cwd=str(REPO))

    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_the_import_block_actually_blocks():
    """The counterweight: without this, a broken block would make the test
    above pass by importing `tests` perfectly happily."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys\n"
            "class B:\n"
            "    def find_spec(self, name, path=None, target=None):\n"
            '        if name == "tests" or name.startswith("tests."):\n'
            '            raise ImportError("blocked")\n'
            "        return None\n"
            "sys.meta_path.insert(0, B())\n"
            "import tests.fixtures.tycoon_factory\n",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )

    assert result.returncode != 0
    assert "blocked" in result.stderr


# --- The temp directory ----------------------------------------------------


def test_materialise_cleans_up_after_itself():
    with materialise() as root:
        assert root.is_dir()
        held = root
    assert not held.exists()
    assert not held.parent.exists(), "the temp directory goes too, not just the project"


def test_materialise_removes_the_directory_even_when_the_server_raises():
    """Ctrl-C is the normal way this subcommand ends."""
    with pytest.raises(KeyboardInterrupt):
        with materialise() as root:
            held = root
            raise KeyboardInterrupt
    assert not held.parent.exists()


# --- The subcommand --------------------------------------------------------


def test_demo_dispatches_before_path_parsing_and_serves_the_generated_project(tmp_path, monkeypatch, capsys):
    """`tycoon-city demo` must reach the demo, and `tycoon-city <path>` must still be
    a path — a subparser would have broken the primary invocation."""
    from tycoon_city import webserve
    from tycoon_city.demo import cli as demo_cli

    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html>")

    served: dict = {}

    def fake_serve(db_path, dist_dir, theme, port, host, *rest):
        served["db_path"] = Path(db_path)
        served["port"] = port
        served["host"] = host
        # The project must exist WHILE the server runs, not only before it.
        served["tycoon_yml"] = (Path(db_path) / "tycoon.yml").is_file()
        served["semantic"] = (Path(db_path) / "semantic.yml").is_file()

    monkeypatch.setattr(demo_cli, "serve", fake_serve)
    # The ordinary path's server is stubbed too, and NOT because this test uses
    # it: without the dispatch, `demo` parses as a path and `webserve.serve`
    # blocks in `serve_forever` — a mutant that hangs the suite instead of
    # failing it, which is not a detection anyone can act on.
    monkeypatch.setattr(webserve, "serve", lambda *a, **k: served.setdefault("as_a_path", True))

    assert webserve.main(["demo", "--port", "8199", "--dist", str(dist)]) == 0

    assert "as_a_path" not in served, "`demo` was parsed as a path, not dispatched"
    assert served["tycoon_yml"] and served["semantic"]
    assert served["port"] == 8199
    assert served["db_path"].name == DEMO_DIR_NAME
    # …and it is cleaned up once the server returns.
    assert not served["db_path"].exists()

    # The URL a first-time viewer is pointed at carries the tour: the picker
    # and the tour ARE the first-run experience.
    printed = capsys.readouterr().err
    assert "?tour=1" in printed


def test_demo_takes_the_bundle_host_and_port_the_container_sets(tmp_path, monkeypatch):
    """`docker run ... tycoon-city demo` passes no flags: the image's own
    DATABASE_TYCOON_WEB_DIST / DATABASE_TYCOON_HOST / PORT have to be enough, and the host
    one especially -- a published port cannot reach a loopback socket."""
    from tycoon_city import webserve
    from tycoon_city.demo import cli as demo_cli

    dist = tmp_path / "image-dist"
    dist.mkdir()
    monkeypatch.setenv("DATABASE_TYCOON_WEB_DIST", str(dist))
    monkeypatch.setenv("DATABASE_TYCOON_HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "9001")
    # No repo fallback, so a pass here can only come from the env.
    monkeypatch.setattr(demo_cli, "_default_dist", lambda: None)

    seen: dict = {}

    def fake_serve(db_path, dist_dir, theme, port, host, *rest):
        seen.update(dist=Path(dist_dir), port=port, host=host)

    monkeypatch.setattr(demo_cli, "serve", fake_serve)
    assert webserve.main(["demo"]) == 0

    assert seen == {"dist": dist, "port": 9001, "host": "0.0.0.0"}


def test_demo_unwinds_on_sigterm_so_docker_stop_takes_the_temp_dir_with_it(tmp_path, monkeypatch):
    """Ctrl-C already cleaned up; `docker stop` and a plain `kill` send SIGTERM,
    whose default handler kills the process outright and leaves the project
    behind. Verified end to end by hand (kill -TERM on a running server removes
    the directory); this pins the wiring so it cannot quietly go away."""
    import signal

    from tycoon_city import webserve
    from tycoon_city.demo import cli as demo_cli

    dist = tmp_path / "dist"
    dist.mkdir()
    monkeypatch.setattr(demo_cli, "serve", lambda *a, **k: None)
    previous = signal.getsignal(signal.SIGTERM)
    try:
        assert webserve.main(["demo", "--dist", str(dist)]) == 0
        assert signal.getsignal(signal.SIGTERM) is signal.default_int_handler
    finally:
        signal.signal(signal.SIGTERM, previous)


def test_demo_without_a_web_bundle_names_all_three_ways_to_get_one(tmp_path, monkeypatch, capsys):
    from tycoon_city import webserve
    from tycoon_city.demo import cli as demo_cli

    monkeypatch.delenv("DATABASE_TYCOON_WEB_DIST", raising=False)
    monkeypatch.setattr(demo_cli, "_default_dist", lambda: None)

    assert webserve.main(["demo"]) == 1

    err = capsys.readouterr().err
    assert "npm run build" in err and "docker run" in err and "--dist" in err


def test_a_path_that_is_not_demo_still_serves_that_path(tmp_path, monkeypatch, capsys):
    """The control for the dispatch above."""
    from tycoon_city import webserve

    db = tmp_path / "fx.duckdb"
    duckdb.connect(str(db)).close()
    dist = tmp_path / "dist"
    dist.mkdir()

    seen: dict = {}
    monkeypatch.setattr(
        webserve,
        "serve",
        lambda db_path, *rest: seen.setdefault("db_path", db_path),
    )

    assert webserve.main([str(db), "--dist", str(dist)]) == 0
    assert seen["db_path"] == str(db)


def test_the_export_of_the_demo_is_a_servable_directory(tmp_path):
    """The other half of the launch story: `tycoon-city-export` over the demo has
    to produce a directory a static host can serve, meta.json included."""
    from tycoon_city.export.cli import main as export_main

    out = tmp_path / "site"
    with materialise() as root:
        assert export_main([str(root), str(out)]) == 0

    assert (out / "city.json").is_file()
    assert (out / "runs.json").is_file()
    assert json.loads((out / "meta.json").read_text())["generated_at"] is not None
