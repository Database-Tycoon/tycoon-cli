"""Visual channels: the only place derived visual state is written from data.

Phase F added the temporal channels and two guarantees:

- **The clock is injected.** `apply_signals(city, ctx, bindings, now)` — no
  data function ever calls `datetime.now()`, and timestamps become ages in
  exactly one place here. Idempotence keeps its meaning: same `ctx`,
  `bindings` and `now` → same state.
- **Kinds are validated at bind time.** `CHANNEL_KIND` says what each channel
  consumes; binding a timestamp function to a scalar channel fails fast with a
  named error instead of silently rendering nonsense.

The rule that must survive every review: **unknown never renders as stale.**
A lot the history does not cover keeps `None` in its temporal fields, and the
client renders None as full colour, no marker.
"""

import math
from datetime import UTC, datetime
from enum import Enum, auto

from ..catalog.models import PipelineContext
from .city import CityMap
from .signals import REGISTRY, SignalKind


class VisualChannel(Enum):
    DENSITY = auto()
    POWERED = auto()
    TRAFFIC_RATE = auto()
    DECAY = auto()  # freshness: age since last build desaturates a building
    TINT = auto()  # build status: error tints toward red
    CONDITION = auto()  # test status: fail/warn hangs a marker on the building
    FRESHNESS = auto()  # dbt's source-freshness SLA verdict: late sources get a cone
    DRIFT = auto()  # schema changed recently: the building is under construction


CHANNEL_KIND: dict[VisualChannel, SignalKind] = {
    VisualChannel.DENSITY: "scalar",
    VisualChannel.POWERED: "scalar",
    VisualChannel.TRAFFIC_RATE: "scalar",
    VisualChannel.DECAY: "timestamp",
    VisualChannel.TINT: "status",
    VisualChannel.CONDITION: "status",
    VisualChannel.FRESHNESS: "status",
    VisualChannel.DRIFT: "timestamp",
}

DEFAULT_BINDINGS: dict[VisualChannel, str] = {
    VisualChannel.DENSITY: "row_count",
    VisualChannel.POWERED: "lineage_participation",
    VisualChannel.TRAFFIC_RATE: "edge_volume",
    VisualChannel.DECAY: "last_build_at",
    VisualChannel.TINT: "build_status",
    VisualChannel.CONDITION: "test_status",
    VisualChannel.FRESHNESS: "source_freshness_status",
    VisualChannel.DRIFT: "schema_drift_at",
}


def as_naive_utc(value: datetime) -> datetime:
    """Every timestamp normalised the same way: aware → UTC, then naive.

    The metadata database stores naive timestamps that are UTC in practice
    (Tower runs on UTC); treating naive as already-UTC is the documented
    assumption, applied here and nowhere else.
    """
    if value.tzinfo is not None:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


def _rows_to_density(value: float) -> int:
    """Density level = decade of rows: an absolute log scale.

    1-9 rows -> 1, 10-99 -> 2, ..., 100k -> 6, 10M+ -> 8. Replaced the earlier
    percentile rank at Stephen's direction (2026-08-04): rank made 1,200 rows
    and 250,000 rows near-neighbours in height, destroying exactly the
    magnitude information a skyline is good at showing. Absolute decades make
    height mean the same thing in every catalog -- a level-6 building holds
    ~100k rows wherever you see it -- at the price that a catalog of uniformly
    tiny tables is uniformly short, which is honest.

    0 rows (views: unmeasured, and genuinely empty tables) stays level 1.
    """
    if value < 1:
        return 1
    return max(1, min(8, int(math.log10(value)) + 1))


def _validate(bindings: dict[VisualChannel, str]) -> None:
    for channel, name in bindings.items():
        fn = REGISTRY.get(name)
        if fn is None:
            raise ValueError(f"{channel.name} is bound to unknown function '{name}'")
        expected = CHANNEL_KIND[channel]
        if fn.kind != expected:
            raise ValueError(f"{channel.name} consumes {expected} but '{name}' produces {fn.kind}")


def apply_signals(
    city: CityMap,
    ctx: PipelineContext,
    bindings: dict[VisualChannel, str],
    now: datetime | None = None,
) -> None:
    """Compute bound data functions and write derived visual state onto city.

    This is the only place visual state is written from data. Idempotent for a
    fixed (ctx, bindings, now); `now` defaults to the wall clock for callers
    that want the present, and is injected everywhere determinism matters.
    """
    _validate(bindings)
    now = as_naive_utc(now if now is not None else datetime.now(UTC))

    density_values = REGISTRY[bindings[VisualChannel.DENSITY]].compute(ctx)
    for key, lot in city.lots.items():
        lot.target_density = _rows_to_density(float(density_values.get(key, 0.0)))

    powered_values = REGISTRY[bindings[VisualChannel.POWERED]].compute(ctx)
    for key, lot in city.lots.items():
        lot.powered = float(powered_values.get(key, 0.0)) >= 0.5

    edge_values = REGISTRY[bindings[VisualChannel.TRAFFIC_RATE]].compute(ctx)
    max_value = max((float(v) for v in edge_values.values()), default=0.0)
    edge_rates: dict[tuple[str, str], float] = {}
    for edge_key, value in edge_values.items():
        src, dst = edge_key.split("->", 1)
        edge_rates[(src, dst)] = (float(value) / max_value) if max_value > 0 else 0.0
    city.edge_rates = edge_rates

    # Temporal channels. Absence is a missing key; the fields stay None and
    # None renders as unknown -- full colour, no tint, no marker.
    built_at = REGISTRY[bindings[VisualChannel.DECAY]].compute(ctx)
    for key, lot in city.lots.items():
        value = built_at.get(key)
        lot.last_build_age_s = (
            max(0.0, (now - as_naive_utc(value)).total_seconds()) if isinstance(value, datetime) else None
        )

    build_status = REGISTRY[bindings[VisualChannel.TINT]].compute(ctx)
    for key, lot in city.lots.items():
        value = build_status.get(key)
        lot.build_status = str(value) if value is not None else None

    test_status = REGISTRY[bindings[VisualChannel.CONDITION]].compute(ctx)
    for key, lot in city.lots.items():
        value = test_status.get(key)
        lot.test_status = str(value) if value is not None else None

    freshness = REGISTRY[bindings[VisualChannel.FRESHNESS]].compute(ctx)
    for key, lot in city.lots.items():
        value = freshness.get(key)
        lot.freshness_status = str(value) if value is not None else None

    drift = REGISTRY[bindings[VisualChannel.DRIFT]].compute(ctx)
    for key, lot in city.lots.items():
        value = drift.get(key)
        lot.schema_drift_age_s = (
            max(0.0, (now - as_naive_utc(value)).total_seconds()) if isinstance(value, datetime) else None
        )
