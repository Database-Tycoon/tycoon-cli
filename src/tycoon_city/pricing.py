"""What a second of compute costs — the one place a price enters this project.

The city's money is derived from measured load (`run_history.daily_load_s`)
times a *declared* rate. The rate is the only number here that is not measured,
so it is never anonymous: every `PriceBook` carries a `price_source` naming
where the number came from, and the emitted budget block repeats it.

Two rules the rest of the codebase depends on:

- **Engine-neutral.** Snowflake bills warehouses, MotherDuck bills ducklings,
  local DuckDB is free. The table below names the billing unit per engine and
  nothing else; engine *versions* are a later product line and no code here
  may assume which one it is running against.
- **Zero is a fact, not an absence.** `duckdb`'s `unit_price_per_s` is `0.0`
  because local DuckDB genuinely costs nothing, and its note says so. A
  $0 bill that came from a *missing* measurement is a different thing
  entirely, and the budget block refuses to emit one (see
  `export.measured._budget`): unknown stays null.

A project supplies its real rate in a `pricing.toml` beside its catalog, or
via `--pricing`:

```toml
engine = "snowflake"
currency = "USD"
unit_price_per_s = 0.000583   # $2.10/credit ÷ 3600 s, one XS warehouse
```
"""

import logging
import tomllib
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

PRICING_FILE = "pricing.toml"

# Money is rounded like every other float that crosses the wire (see
# `export.blocks.RATE_PRECISION`): six decimals, which is past anything a
# reader can act on and is what keeps the golden diffable rather than carrying
# 17 significant digits of division noise. Load keeps the two decimals
# `_edges` already rounds `daily_load_s` to, so the budget's totals and the
# streets' per-edge numbers are stated at the same grain.
COST_PRECISION = 6
LOAD_PRECISION = 2


class PricingError(ValueError):
    """A `pricing.toml` that cannot be read as a price. Loud on purpose: the
    alternative is billing a Snowflake warehouse at DuckDB's free rate."""


@dataclass(frozen=True)
class PriceBook:
    """One engine's rate, with the provenance of the number attached."""

    engine: str
    currency: str
    unit_price_per_s: float
    #: Where `unit_price_per_s` came from — a built-in default or a file path.
    price_source: str
    #: How this engine bills, in its own vocabulary. Shown to the reader.
    note: str


# The built-in table. List prices, deliberately marked as such: a real bill
# depends on warehouse size, edition, region and contract, none of which this
# project can observe. `price_source` says "list price" so nobody mistakes the
# default for their invoice, and `pricing.toml` replaces it.
_LIST = "built-in list price — set your own rate in pricing.toml"

DEFAULT_PRICES: dict[str, PriceBook] = {
    "duckdb": PriceBook(
        engine="duckdb",
        currency="USD",
        unit_price_per_s=0.0,
        price_source="built-in price table (local DuckDB is free)",
        note="local DuckDB is free — the load is measured, the bill is zero",
    ),
    "motherduck": PriceBook(
        engine="motherduck",
        currency="USD",
        # Standard duckling, $0.25/hour list.
        unit_price_per_s=0.25 / 3600,
        price_source=_LIST,
        note="MotherDuck bills ducklings by the second",
    ),
    "snowflake": PriceBook(
        engine="snowflake",
        currency="USD",
        # One XS warehouse: 1 credit/hour at $2.00/credit list.
        unit_price_per_s=2.00 / 3600,
        price_source=_LIST,
        note="Snowflake bills warehouses by the second",
    ),
}

#: This build is the vanilla, local-only version (see the handover's engine
#: versions note), so an undeclared engine is the free one.
DEFAULT_ENGINE = "duckdb"

DEFAULT_PRICE_BOOK = DEFAULT_PRICES[DEFAULT_ENGINE]


def _price_book_from(data: dict, origin: str) -> PriceBook:
    """Build a book from parsed TOML, defaulting each field to the engine's
    row in the built-in table."""
    engine_raw = data.get("engine", DEFAULT_ENGINE)
    if not isinstance(engine_raw, str):
        raise PricingError(f"{origin}: 'engine' must be a string")
    engine = engine_raw.strip().lower()
    base = DEFAULT_PRICES.get(engine)

    price = data.get("unit_price_per_s")
    if price is None:
        if base is None:
            # Refusing beats guessing: there is no honest rate for an engine
            # this build has never heard of, and falling back to the free
            # local rate would silently bill a paid warehouse at zero.
            known = ", ".join(sorted(DEFAULT_PRICES))
            raise PricingError(f"{origin}: unknown engine '{engine}' and no unit_price_per_s (known engines: {known})")
        price = base.unit_price_per_s
        source = base.price_source
    else:
        if not isinstance(price, (int, float)) or isinstance(price, bool) or price < 0:
            raise PricingError(f"{origin}: 'unit_price_per_s' must be a number >= 0")
        price = float(price)
        source = origin

    currency = data.get("currency", base.currency if base else "USD")
    if not isinstance(currency, str):
        raise PricingError(f"{origin}: 'currency' must be a string")

    note = data.get("note", base.note if base else f"{engine} bills compute by the second")
    if not isinstance(note, str):
        raise PricingError(f"{origin}: 'note' must be a string")

    return PriceBook(
        engine=engine,
        currency=currency,
        unit_price_per_s=price,
        price_source=source,
        note=note,
    )


def read_price_book(path: Path | str) -> PriceBook:
    """Read one `pricing.toml`. Raises `PricingError` if it cannot be read as
    a price — a mistyped rate file must not degrade to the free default."""
    target = Path(path)
    try:
        data = tomllib.loads(target.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PricingError(f"could not read pricing file {target}: {exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise PricingError(f"{target}: not valid TOML ({exc})") from exc
    return _price_book_from(data, str(target))


def resolve_price_book(source: Path | str | None, explicit: Path | str | None = None) -> PriceBook:
    """The price for a catalog: `--pricing` if given, else a `pricing.toml`
    beside the catalog, else the built-in default.

    Discovery is deliberately anchored to the **catalog**, not to the working
    directory: a `pricing.toml` that happens to sit in whatever directory the
    exporter was invoked from would make `city.json`'s bytes depend on the cwd,
    and byte-stability is the property the golden rests on.
    """
    if explicit is not None:
        return read_price_book(explicit)
    for candidate in _candidate_files(source):
        if candidate.is_file():
            logger.info("pricing from %s", candidate)
            return read_price_book(candidate)
    return DEFAULT_PRICE_BOOK


def _candidate_files(source: Path | str | None) -> list[Path]:
    """`pricing.toml` in the tycoon project root, or beside a `.duckdb` file.
    An `md:` catalog has no directory and therefore no discoverable file."""
    if source is None:
        return []
    text = str(source)
    if text.startswith("md:"):
        return []
    path = Path(text)
    root = path if path.is_dir() else path.parent
    return [root / PRICING_FILE]
