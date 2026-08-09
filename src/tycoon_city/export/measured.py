"""The three MEASURED blocks: the city's money, its traffic, and its weather.

Budget, usage and weather were cut into `city.json` as reserved keys on
2026-08-06 and are filled here. All three restate facts the catalog and its
run history already carry — no simulation, no defaults that look like data —
and all three have a specific way to lie, which is what most of the code below
is guarding against:

* **budget** — local DuckDB costs $0 as a *fact*, and its note says so. That
  must never be confusable with $0-because-nothing-was-measured, so a bill
  that could price nothing emits null totals rather than a zero, and a partial
  bill counts the objects it left out.
* **usage** — how often an object appears in recorded runs. This is BUILD/RUN
  usage, **not query usage**: vanilla DuckDB has no query log (see
  `docs/semantic-roads.md`, which names query history as the
  MotherDuck/Snowflake differentiator), and the `source` discriminator is what
  holds that seam open. null means *unknown*, never *unused*.
* **weather** — fog covers the districts a late source FEEDS, walked over the
  measured edges. When there are no freshness verdicts at all, all-clear would
  be clear-because-unknown rendered as clear-because-fine, so no cells are
  emitted and the note names the absence.

The multi-hop walk lives here rather than in the client for the reason
`docs/city-json-v1.md` already settled for `theme.style_rules`: a rule with a
precedence order is not a projection, and clients must not re-derive rules.
"""

from collections import deque
from typing import Any

from ..catalog.models import PipelineContext
from ..catalog.run_history import daily_load_s, daily_rate, observed_span_days
from ..pricing import COST_PRECISION, DEFAULT_PRICE_BOOK, LOAD_PRECISION, PriceBook
from ..sim.signals import SourceFreshnessStatus
from .blocks import RATE_PRECISION

# --- usage -----------------------------------------------------------------

#: The `usage.source` discriminator. `"runs"` is what vanilla DuckDB can
#: measure: appearances in recorded dbt builds. A MotherDuck or Snowflake
#: build reading a real query log would emit `"queries"` here, and a client
#: switching on this field never has to guess which one it is looking at.
USAGE_SOURCE_RUNS = "runs"


def _usage_by_key(ctx: PipelineContext) -> dict[str, dict[str, Any]]:
    """Per-object run appearances, keyed by catalog key.

    Objects the run history says nothing about are **absent from this map**,
    which becomes a null `usage` on the wire. Unknown-usage and zero-usage are
    different facts and a client must not render them alike.

    `rate_per_day` reuses `run_history.daily_rate` — the one cadence
    calculator — so a backfill burst gets the same one-hour span floor the
    road-load overlay applies, and "how often" means the same thing in both.
    `window_days` is the *unfloored* span: the window that actually happened.
    """
    if ctx.runs is None:
        return {}
    usage: dict[str, dict[str, Any]] = {}
    for key, unique_id in ctx.dbt_nodes_by_key.items():
        history = ctx.runs.build_history.get(unique_id, ())
        if not history:
            continue
        rate = daily_rate(history)
        usage[key] = {
            "source": USAGE_SOURCE_RUNS,
            "runs_seen": len(history),
            "window_days": round(observed_span_days(history), RATE_PRECISION),
            # None with one run or a zero span: a guess here would put a
            # building's whole traffic story on one data point.
            "rate_per_day": None if rate is None else round(rate, RATE_PRECISION),
        }
    return usage


# --- budget ----------------------------------------------------------------


def _budget(ctx: PipelineContext, pricing: PriceBook | None = None) -> dict[str, Any] | None:
    """The city's compute bill: measured `daily_load_s` times a declared rate.

    null when the run history knows nothing about anything on this map. That
    is the case `database.notes` already names ("no run history yet", "no run
    metadata"), and inventing a zero bill for it would be the exact confusion
    the local-DuckDB $0 has to stay distinguishable from.
    """
    book = pricing or DEFAULT_PRICE_BOOK
    if ctx.runs is None:
        return None
    histories = {key: ctx.runs.build_history.get(unique_id, ()) for key, unique_id in ctx.dbt_nodes_by_key.items()}
    if not any(histories.values()):
        return None

    # Priced = the cadence is measurable. Everything else on the map is
    # counted, never quietly folded in at zero. The test is `is not None` and
    # not truthiness on purpose: a model whose builds all took 0.0s has a
    # MEASURED load of zero, which belongs in the bill, not in the excluded
    # pile with the objects nothing is known about.
    priced: dict[str, float] = {}
    for key in sorted(histories):
        load = daily_load_s(histories[key])
        if load is not None:
            priced[key] = load
    total_load = sum(priced.values())
    total_objects = len(ctx.objects)
    unpriced = total_objects - len(priced)

    return {
        "engine": book.engine,
        "currency": book.currency,
        "unit_price_per_s": book.unit_price_per_s,
        # Where the rate came from: the built-in table, or the file that
        # overrode it. The one number here that is declared, not measured.
        "price_source": book.price_source,
        # Both null when nothing could be priced: unknown, not a zero bill.
        "daily_load_s": round(total_load, LOAD_PRECISION) if priced else None,
        "daily_cost": round(total_load * book.unit_price_per_s, COST_PRECISION) if priced else None,
        "priced_objects": len(priced),
        "unpriced_objects": unpriced,
        "by_object": [
            {
                "object_key": key,
                "daily_load_s": round(load, LOAD_PRECISION),
                "daily_cost": round(load * book.unit_price_per_s, COST_PRECISION),
            }
            for key, load in priced.items()
        ],
        "note": _budget_note(book, len(priced), total_objects, unpriced),
    }


def _budget_note(book: PriceBook, priced: int, total: int, unpriced: int) -> str:
    """The engine's billing sentence, then this bill's own partiality.

    Engine-neutral by construction: the first clause is whatever the price
    book says (Snowflake bills warehouses, MotherDuck ducklings, local DuckDB
    is free), and nothing here knows which engine it is describing.
    """
    if priced == 0:
        return (
            f"{book.note}; no object has the two recorded builds a cadence needs, "
            "so nothing could be priced — unknown, not a zero bill"
        )
    if unpriced == 0:
        return f"{book.note}; priced all {total} objects"
    return (
        f"{book.note}; priced {priced} of {total} objects — {unpriced} have too little run history to measure a cadence"
    )


# --- weather ---------------------------------------------------------------

#: What a district's sky looks like. `fog` is the alarming one, so it takes
#: precedence over `overcast`, which takes precedence over `clear`.
CONDITIONS = ("clear", "overcast", "fog")
_CONDITION_OF_VERDICT = {"error": "fog", "warn": "overcast"}
_SEVERITY = {condition: rank for rank, condition in enumerate(CONDITIONS)}

NO_VERDICTS_NOTE = "no source freshness verdicts — weather unknown"


def _weather(ctx: PipelineContext) -> dict[str, Any]:
    """Source freshness as weather over the districts a late source FEEDS.

    The derivation that makes this worth doing upstream of the seam: a late
    source does not fog its own district, it fogs everything downstream of it,
    which is a multi-hop walk over the measured edges plus a precedence rule.
    `docs/city-json-v1.md` already settled that clients must not re-run rules.

    Two honesty rules do most of the work here:

    * **No verdicts, no cells.** `loader` emits "no source freshness snapshot
      (run `dbt source freshness`)" whenever sources exist but verdicts do
      not. In that state a full set of `clear` cells is a lie —
      clear-because-unknown rendered as clear-because-fine — so the cells stay
      empty and the note says weather is unknown.
    * **Partial coverage is named.** A district with no judged source upstream
      of it gets no cell at all and is counted in the note. A cell is a
      positive assertion about a district, which is why `clear` is emitted
      rather than left as an absence.
    """
    verdicts = {key: str(status) for key, status in SourceFreshnessStatus().compute(ctx).items()}
    keys = {obj.key for obj in ctx.objects}
    verdicts = {key: status for key, status in verdicts.items() if key in keys}
    if not verdicts:
        return {"cells": [], "note": NO_VERDICTS_NOTE}

    schema_of = {obj.key: obj.schema for obj in ctx.objects}
    downstream: dict[str, list[str]] = {key: [] for key in keys}
    for edge in ctx.edges:
        if edge.src in keys and edge.dst in keys:
            downstream[edge.src].append(edge.dst)

    covered: set[str] = set()
    # schema -> (severity, hops, source_key) of the worst source reaching it.
    worst: dict[str, tuple[int, int, str]] = {}
    late = 0
    for source_key in sorted(verdicts):
        condition = _CONDITION_OF_VERDICT.get(verdicts[source_key], "clear")
        if condition != "clear":
            late += 1
        for reached, hops in _reach(source_key, downstream):
            covered.add(schema_of[reached])
            # hops == 0 is the source's own building: a late source does not
            # rain on itself, it rains on what it feeds.
            if hops == 0 or condition == "clear":
                continue
            schema = schema_of[reached]
            candidate = (_SEVERITY[condition], hops, source_key)
            current = worst.get(schema)
            # Worse wins; ties break on the nearer source, then on its key so
            # the choice cannot depend on dict order.
            if current is None or (-candidate[0], candidate[1], candidate[2]) < (
                -current[0],
                current[1],
                current[2],
            ):
                worst[schema] = candidate

    cells = []
    for schema in sorted(covered):
        entry = worst.get(schema)
        if entry is None:
            # A positive assertion: judged sources reach this district and
            # none of them is late.
            cells.append(
                {
                    "schema": schema,
                    "condition": "clear",
                    "worst_source": None,
                    "verdict": None,
                    "hops": None,
                }
            )
            continue
        severity, hops, source_key = entry
        cells.append(
            {
                "schema": schema,
                "condition": CONDITIONS[severity],
                "worst_source": source_key,
                "verdict": verdicts[source_key],
                "hops": hops,
            }
        )

    uncovered = len({schema_of[key] for key in keys} - covered)
    return {"cells": cells, "note": _weather_note(len(verdicts), late, uncovered)}


def _reach(start: str, downstream: dict[str, list[str]]) -> list[tuple[str, int]]:
    """Breadth-first downstream walk from `start`, as (key, fewest hops).

    Includes `start` itself at hop 0 — that is what makes a source's own
    district *covered* (we do know its weather) while still exempt from its
    own lateness.
    """
    seen = {start: 0}
    queue = deque([start])
    while queue:
        key = queue.popleft()
        for nxt in downstream.get(key, ()):
            if nxt not in seen:
                seen[nxt] = seen[key] + 1
                queue.append(nxt)
    return sorted(seen.items())


def _weather_note(judged: int, late: int, uncovered: int) -> str:
    head = (
        f"weather from dbt source freshness: {judged} judged "
        f"{'source' if judged == 1 else 'sources'}, {late} late; "
        "fog covers the districts a late source feeds, not its own"
    )
    if uncovered:
        return (
            f"{head}; {uncovered} "
            f"{'district has' if uncovered == 1 else 'districts have'} "
            "no judged source upstream — no weather shown there"
        )
    return head
