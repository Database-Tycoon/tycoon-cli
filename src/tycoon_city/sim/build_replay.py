"""Reconstruct the last dbt run as a schedule the client can play.

`dbt_nodes` has per-node durations but **no per-node start times**, so the
schedule is built topologically over the catalog's edges with an
infinite-parallelism assumption: a model starts when its slowest upstream
finishes. That is honest as far as it goes and no further — durations are
measured, ordering is reconstructed — and the note carried on the plan says
exactly that, verbatim, for the client to display.

Refuse rather than mislead: no run history means no replay, and a history
whose models mostly do not map onto this catalog (wrong target, foreign
manifest) is named, not animated.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from ..catalog.models import Edge, PipelineContext

TARGET_SPAN_TICKS = 300  # ~30 s at the client's 10 Hz tick
RECONSTRUCTED_NOTE = "durations measured, ordering reconstructed"

# Below this, the history describes some other catalog and a replay would be
# a lie told with animation.
MIN_JOINED = 0.5


def induced_subgraph(keys: Iterable[str], edges: Iterable[Edge]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """`(upstream, downstream)` adjacency over the subgraph `edges` induces on
    `keys` — every key present, edges with an endpoint outside `keys` dropped.

    Shared with `export.run_json` on purpose (2026-08-06): the run documents
    order a specific run's steps over the same measured edges this schedule
    uses, and two copies of "which edges count" would drift apart silently.
    """
    keyset = set(keys)
    upstream: dict[str, list[str]] = {key: [] for key in keyset}
    downstream: dict[str, list[str]] = {key: [] for key in keyset}
    for edge in edges:
        if edge.src in keyset and edge.dst in keyset:
            upstream[edge.dst].append(edge.src)
            downstream[edge.src].append(edge.dst)
    return upstream, downstream


def topological_order(upstream: dict[str, list[str]], downstream: dict[str, list[str]]) -> list[str]:
    """Kahn over the adjacency from `induced_subgraph`, ties broken on the key
    so a fixed input always yields the same order.

    A member of a cycle (possible in principle, not in dbt) is never released
    and is therefore **absent from the result** rather than hanging the walk —
    callers that must account for every key add the difference back themselves.
    """
    queue = sorted(key for key, ups in upstream.items() if not ups)
    order: list[str] = []
    done: set[str] = set()
    while queue:
        key = queue.pop(0)
        order.append(key)
        done.add(key)
        ready = sorted(down for down in downstream[key] if all(up in done for up in upstream[down]))
        for down in ready:
            if down not in done and down not in queue:
                queue.append(down)
    return order


@dataclass(frozen=True)
class ReplayStep:
    object_key: str
    start: int  # tick
    duration: int  # ticks, >= 1


@dataclass(frozen=True)
class ReplayPlan:
    span_ticks: int
    note: str
    steps: tuple[ReplayStep, ...]


@dataclass(frozen=True)
class ReplayRefusal:
    reason: str


def plan_replay(ctx: PipelineContext, target_span_ticks: int = TARGET_SPAN_TICKS) -> ReplayPlan | ReplayRefusal:
    """The last run as (start, duration) ticks per object, or a named refusal."""
    if ctx.runs is None or not ctx.runs.node_results:
        return ReplayRefusal("no run history to replay")

    # Model results that map onto this catalog's objects.
    key_of_node = {node_id: key for key, node_id in ctx.dbt_nodes_by_key.items()}
    model_results = {
        node_id: result for node_id, result in ctx.runs.node_results.items() if node_id.startswith("model.")
    }
    if not model_results:
        return ReplayRefusal("no run history to replay")

    joined = {key_of_node[nid]: r for nid, r in model_results.items() if nid in key_of_node}
    if len(joined) / len(model_results) < MIN_JOINED:
        return ReplayRefusal("run history does not match this catalog")

    # Topological schedule over the catalog's edges, infinite parallelism:
    # start = max(finish of joined upstreams). The walk itself lives in
    # `topological_order` so the run documents share it; a cycle drops its
    # members there rather than hanging, and they stay out of the schedule.
    upstream, downstream = induced_subgraph(joined, ctx.edges)
    order = topological_order(upstream, downstream)

    finish: dict[str, float] = {}
    for key in order:
        start = max((finish[up] for up in upstream[key]), default=0.0)
        finish[key] = start + max(0.01, joined[key].execution_time_s)

    span = max(finish.values(), default=0.0)
    if span <= 0:
        return ReplayRefusal("no run history to replay")

    scale = target_span_ticks / span
    steps = []
    for key in order:
        duration = max(0.01, joined[key].execution_time_s)
        start = finish[key] - duration
        steps.append(
            ReplayStep(
                object_key=key,
                start=int(round(start * scale)),
                duration=max(1, int(round(duration * scale))),
            )
        )
    steps.sort(key=lambda s: (s.start, s.object_key))
    return ReplayPlan(span_ticks=target_span_ticks, note=RECONSTRUCTED_NOTE, steps=tuple(steps))
