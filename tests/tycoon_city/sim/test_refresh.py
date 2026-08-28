from datetime import datetime

from tycoon_city.catalog.models import CatalogObject, PipelineContext
from tycoon_city.sim.channels import DEFAULT_BINDINGS, apply_signals
from tycoon_city.sim.generator import generate_city, refresh
from tycoon_city.sim.tiles import ZoneStyle

RULES = [("raw", ZoneStyle.INDUSTRIAL), ("mart", ZoneStyle.RESIDENTIAL)]


def _ctx(objects):
    return PipelineContext("demo", tuple(objects), ())


def _snapshot(city):
    lots = {k: (lot.target_density, lot.powered, lot.density) for k, lot in city.lots.items()}
    return lots, dict(city.edge_rates)


def test_refresh_adds_new_lots_and_carries_density():
    ctx = _ctx([CatalogObject("raw", "orders", "table", 100)])
    city = generate_city(ctx, RULES)
    city.lots["raw.orders"].density = 3

    new_ctx = _ctx(
        [
            CatalogObject("raw", "orders", "table", 100),
            CatalogObject("raw", "customers", "table", 5),
        ]
    )
    new_city = refresh(city, new_ctx, RULES)

    assert new_city.lots["raw.orders"].density == 3  # carried over
    assert "raw.customers" in new_city.lots
    assert new_city.lots["raw.customers"].density == 0  # brand new lot


def test_refresh_unchanged_data_changes_no_state():
    ctx = _ctx(
        [
            CatalogObject("raw", "orders", "table", 100),
            CatalogObject("mart", "revenue", "view", 40),
        ]
    )
    now = datetime(2026, 8, 5, 12, 0, 0)
    city = generate_city(ctx, RULES)
    apply_signals(city, ctx, DEFAULT_BINDINGS, now)
    # The tween is the CLIENT's job now (the Python engine died with pygame);
    # a settled city is simply density == target.
    for lot in city.lots.values():
        lot.density = lot.target_density
    before = _snapshot(city)

    # replay the app's R-refresh flow with identical data
    new_city = refresh(city, ctx, RULES)
    apply_signals(new_city, ctx, DEFAULT_BINDINGS, now)
    after = _snapshot(new_city)

    assert after == before  # unchanged data -> no state change
