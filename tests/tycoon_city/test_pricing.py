"""The price book: the one declared number in `city.json`, and its provenance.

Everything else in the document is measured. That makes the rate the one place
a wrong default silently becomes a wrong bill, so the rules under test are:
a rate always names where it came from, an engine this build has never heard
of is refused rather than billed at DuckDB's free rate, and discovery is
anchored to the catalog so `city.json`'s bytes never depend on the cwd.
"""

import pytest

from tycoon_city.pricing import (
    DEFAULT_ENGINE,
    DEFAULT_PRICE_BOOK,
    DEFAULT_PRICES,
    PRICING_FILE,
    PricingError,
    read_price_book,
    resolve_price_book,
)


def test_the_default_is_local_duckdb_and_it_is_free_on_purpose():
    assert DEFAULT_ENGINE == "duckdb"
    assert DEFAULT_PRICE_BOOK.unit_price_per_s == 0.0
    # The zero has a reason attached; that is what keeps it from reading as a
    # missing measurement.
    assert "free" in DEFAULT_PRICE_BOOK.note
    assert "price table" in DEFAULT_PRICE_BOOK.price_source


def test_every_built_in_engine_names_its_billing_unit():
    """Engine-neutral wording is a standing direction, not a nicety: the note
    is what a reader sees under the bill."""
    assert "warehouses" in DEFAULT_PRICES["snowflake"].note
    assert "ducklings" in DEFAULT_PRICES["motherduck"].note
    assert "DuckDB is free" in DEFAULT_PRICES["duckdb"].note
    # A paid engine's default is a list price and says so — nobody should
    # mistake it for their invoice.
    for engine in ("snowflake", "motherduck"):
        assert DEFAULT_PRICES[engine].unit_price_per_s > 0
        assert "list price" in DEFAULT_PRICES[engine].price_source


def test_a_declared_rate_replaces_the_default_and_names_the_file(tmp_path):
    path = tmp_path / PRICING_FILE
    path.write_text('engine = "snowflake"\nunit_price_per_s = 0.0004\n')

    book = read_price_book(path)
    assert book.engine == "snowflake"
    assert book.unit_price_per_s == 0.0004
    # Provenance: the file, not the built-in table it overrode.
    assert book.price_source == str(path)
    assert "list price" not in book.price_source
    # Fields the file left out fall back to that engine's row.
    assert book.currency == "USD"
    assert "warehouses" in book.note


def test_naming_a_known_engine_without_a_rate_takes_that_engines_default(tmp_path):
    path = tmp_path / PRICING_FILE
    path.write_text('engine = "motherduck"\n')

    book = read_price_book(path)
    assert book.unit_price_per_s == DEFAULT_PRICES["motherduck"].unit_price_per_s
    assert "list price" in book.price_source


def test_an_unknown_engine_without_a_rate_is_refused(tmp_path):
    """Falling back to the free local rate here would bill a paid warehouse at
    zero — the exact confusion this whole block is built to prevent."""
    path = tmp_path / PRICING_FILE
    path.write_text('engine = "bigquery"\n')

    with pytest.raises(PricingError) as excinfo:
        read_price_book(path)
    assert "bigquery" in str(excinfo.value)


def test_an_unknown_engine_with_a_rate_is_accepted(tmp_path):
    path = tmp_path / PRICING_FILE
    path.write_text('engine = "bigquery"\nunit_price_per_s = 0.002\n')

    book = read_price_book(path)
    assert book.engine == "bigquery"
    assert book.unit_price_per_s == 0.002


@pytest.mark.parametrize(
    "body",
    [
        'unit_price_per_s = "free"',
        "unit_price_per_s = -1",
        "engine = 3",
        "this is not toml",
    ],
)
def test_a_malformed_price_file_raises_rather_than_degrading(tmp_path, body):
    path = tmp_path / PRICING_FILE
    path.write_text(body)
    with pytest.raises(PricingError):
        read_price_book(path)


def test_discovery_looks_beside_the_catalog(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    (project / PRICING_FILE).write_text('engine = "snowflake"\nunit_price_per_s = 0.5\n')

    # A project directory finds its own file...
    assert resolve_price_book(project).unit_price_per_s == 0.5
    # ...and so does a database file sitting inside it.
    assert resolve_price_book(project / "fx.duckdb").unit_price_per_s == 0.5


def test_discovery_ignores_the_working_directory(tmp_path, monkeypatch):
    """`city.json` is byte-stable. A `pricing.toml` picked up from wherever the
    exporter happened to be invoked would make the bytes depend on the cwd."""
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    (cwd / PRICING_FILE).write_text('engine = "snowflake"\nunit_price_per_s = 9.0\n')
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(cwd)

    assert resolve_price_book(elsewhere / "fx.duckdb") == DEFAULT_PRICE_BOOK


def test_an_explicit_file_wins_over_discovery(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    (project / PRICING_FILE).write_text("unit_price_per_s = 1.0\n")
    override = tmp_path / "other.toml"
    override.write_text("unit_price_per_s = 2.0\n")

    assert resolve_price_book(project, override).unit_price_per_s == 2.0


def test_an_md_catalog_has_no_directory_to_discover_in():
    assert resolve_price_book("md:some_db") == DEFAULT_PRICE_BOOK


def test_a_missing_explicit_file_is_an_error_not_a_silent_default(tmp_path):
    with pytest.raises(PricingError):
        resolve_price_book(tmp_path, tmp_path / "nope.toml")
