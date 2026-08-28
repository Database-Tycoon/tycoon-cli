"""`scripts/readiness.py` -- the diagnostic Stephen points at a client catalog.

The property that matters most here is not what the report says, it is what it
does NOT say: the default output must carry no identifier from the catalog, or
the whole point of the script (paste it into a chat window) is gone. So the
fixture is built with names that could not occur in the harness's own prose,
and the test asserts their absence -- and then asserts `--names` puts them
back, so "absent" cannot be passing because the report is empty.
"""

import importlib.util
import sys
from pathlib import Path

import duckdb
import pytest

REPO = Path(__file__).resolve().parents[1]

# A catalog full of words that appear nowhere in the report's own text, so a
# leak cannot hide behind ordinary English.
SCHEMA = "zqx_clientschema"
TABLE = "zqx_customertable"
VIEW = "zqx_revenueview"
COLUMN = "zqx_ssncolumn"


@pytest.fixture(scope="module")
def readiness():
    spec = importlib.util.spec_from_file_location("readiness", REPO / "scripts" / "readiness.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["readiness"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def catalog(tmp_path_factory):
    db = tmp_path_factory.mktemp("readiness") / "client.duckdb"
    con = duckdb.connect(str(db))
    con.execute(f'create schema "{SCHEMA}"')
    con.execute(f'create table "{SCHEMA}"."{TABLE}" as select 1 as "{COLUMN}"')
    con.execute(f'create view "{SCHEMA}"."{VIEW}" as select "{COLUMN}" from "{SCHEMA}"."{TABLE}"')
    con.close()
    return db


def test_the_default_report_is_clean_and_names_nothing(readiness, catalog, capsys):
    code = readiness.main([str(catalog)])
    out = capsys.readouterr().out

    # Precondition: the report really did run the whole stack, so "no names"
    # is not passing because nothing was produced.
    assert code == 0
    assert "LOAD TIME BY STAGE" in out and "RENDERING" in out
    assert "objects" in out and "city.json" in out

    for secret in (SCHEMA, TABLE, VIEW, COLUMN, str(catalog)):
        assert secret not in out, f"the default report leaked {secret!r}"


def test_names_puts_the_identifiers_back(readiness, catalog, capsys):
    assert readiness.main([str(catalog), "--names"]) == 0
    out = capsys.readouterr().out
    assert SCHEMA in out, "--names printed no identifiers; the redaction test proves nothing"
    assert str(catalog) in out


def test_notes_are_redacted_but_still_readable(readiness):
    """The one channel client text can ride in. `_Redactor` blanks the value
    and leaves the sentence, so a degradation stays legible."""
    redact = readiness._Redactor({"acme_prod", "raw", "no"})
    assert redact("run history from target 'acme_prod'") == "run history from target '<redacted>'"
    # Under three characters is left alone: blanking "no" would eat the prose.
    assert redact("no run history yet") == "no run history yet"


def test_a_catalog_that_cannot_be_opened_exits_non_zero(readiness, tmp_path, capsys):
    assert readiness.main([str(tmp_path / "does-not-exist.duckdb")]) == 1
    assert "BROKEN" in capsys.readouterr().out


def test_a_broken_city_is_reported_as_broken_not_merely_noted(readiness, catalog, capsys, monkeypatch):
    """The exit code is the smoke-test half of the contract, so it needs a
    mutant of its own: break the object-to-lot correspondence and the run must
    fail. Without this the exit code is only ever observed as 0."""
    real = readiness.generate_city

    def lossy(ctx, style_rules):
        city = real(ctx, style_rules)
        city.lots.popitem()
        return city

    monkeypatch.setattr(readiness, "generate_city", lossy)
    assert readiness.main([str(catalog)]) == 1
    assert "objects are being lost" in capsys.readouterr().out
