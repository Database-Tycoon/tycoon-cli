"""Data functions: the only place catalog facts become visual-channel inputs.

Phase F widened the protocol: a function declares a `kind` — `"scalar"`
(float), `"timestamp"` (datetime), or `"status"` (a word from that function's
frozen vocabulary) — and `channels.CHANNEL_KIND` validates the binding at
apply time, so a timestamp can never silently feed a scalar channel.

Two rules hold for every function here:

- **Absence is a missing key, never None.** A catalog with no run history
  computes empty dicts, and the channel layer leaves the lot's field None —
  which the renderer treats as *unknown*, full colour, no marker. Unknown must
  never render as stale: dogfood's newest run may be weeks old and absent is
  the common case, so a default-to-stale would open the feature looking
  derelict.
- **No function reads a clock.** Timestamps are returned as-is;
  `apply_signals` converts them to ages against its injected `now`, in one
  place.
"""

from collections import deque
from datetime import datetime
from typing import Literal, Protocol

from ..catalog.models import PipelineContext

SignalKind = Literal["scalar", "timestamp", "status"]
SignalValue = float | datetime | str


class DataFunction(Protocol):
    name: str
    scope: Literal["object", "edge"]
    kind: SignalKind

    def compute(self, ctx: PipelineContext) -> dict[str, SignalValue]: ...


REGISTRY: dict[str, DataFunction] = {}


def register(fn: DataFunction) -> None:
    REGISTRY[fn.name] = fn


class RowCount:
    name = "row_count"
    scope: Literal["object", "edge"] = "object"
    kind: SignalKind = "scalar"

    def compute(self, ctx: PipelineContext) -> dict[str, SignalValue]:
        return {obj.key: float(obj.row_count) for obj in ctx.objects}


# Retained as a registered function and as history: it is NOT the POWERED
# default because it is always true on an acyclic graph. Every node traces back
# to some source, so only a dependency cycle could ever dim a building, and
# DuckDB does not produce one. See LineageParticipation below.
class LineageReachability:
    name = "lineage_reachability"
    scope: Literal["object", "edge"] = "object"
    kind: SignalKind = "scalar"

    def compute(self, ctx: PipelineContext) -> dict[str, SignalValue]:
        keys = {obj.key for obj in ctx.objects}
        outgoing: dict[str, list[str]] = {k: [] for k in keys}
        incoming: dict[str, list[str]] = {k: [] for k in keys}
        for edge in ctx.edges:
            if edge.src in keys and edge.dst in keys:
                outgoing[edge.src].append(edge.dst)
                incoming[edge.dst].append(edge.src)

        # Sources (no incoming edge) are fed directly by the database root.
        reachable: set[str] = set()
        queue = deque(k for k in keys if not incoming[k])
        reachable.update(queue)
        while queue:
            key = queue.popleft()
            for nxt in outgoing[key]:
                if nxt not in reachable:
                    reachable.add(nxt)
                    queue.append(nxt)

        return {k: (1.0 if k in reachable else 0.0) for k in keys}


class EdgeVolume:
    """Rows flowing along a lineage edge: the upstream object's row count,
    falling back to the downstream one when the upstream is unmeasured.

    An earlier version took min(src, dst), reading "flow is limited by the
    smaller end". That made the signal **structurally zero on every edge the
    loader can produce**: SQL-scan lineage always points *into* a view, and the
    loader records every view as 0 rows because DuckDB's estimated_size only
    exists for tables. A view's zero is "unmeasured", not "empty" -- min()
    treated it as empty, so no catalog ever spawned a vehicle and nobody
    noticed for weeks (the one test used a view with 40 rows, a shape the
    loader never emits).

    Preferring src is also the better meaning: traffic on the road from
    orders to stg_orders depicts orders' rows being consumed. A view -> view
    edge stays 0 -- both ends unmeasured, and inventing a number is exactly
    what this project does not do.
    """

    name = "edge_volume"
    scope: Literal["object", "edge"] = "edge"
    kind: SignalKind = "scalar"

    def compute(self, ctx: PipelineContext) -> dict[str, SignalValue]:
        row_counts = {obj.key: obj.row_count for obj in ctx.objects}
        result: dict[str, SignalValue] = {}
        for edge in ctx.edges:
            if edge.src in row_counts and edge.dst in row_counts:
                volume = row_counts[edge.src] or row_counts[edge.dst]
                result[f"{edge.src}->{edge.dst}"] = float(volume)
        return result


class LineageParticipation:
    """1.0 when an object takes part in lineage at all, 0.0 when orphaned.

    Only *known* edges count: an edge is known when both of its endpoints are
    objects in this catalog. An edge pointing at something outside the catalog
    therefore rescues nobody from orphanhood.

    When the catalog has **no known edges whatsoever**, every object scores 1.0.
    "We know of no lineage at all" is a different fact from "this object is an
    orphan" and must not render identically: a tables-only database without a
    manifest has zero edges and would otherwise dim every building on the map.
    The client flags that case in the status strip instead.

    Note: sim.layout.isolated_keys computes the same connectedness from the same
    definition of a known edge, deliberately duplicated so this module stays
    independent of the layout module. The two *differ in meaning* when there are
    no edges. Keep both in step if either changes.
    """

    name = "lineage_participation"
    scope: Literal["object", "edge"] = "object"
    kind: SignalKind = "scalar"

    def compute(self, ctx: PipelineContext) -> dict[str, SignalValue]:
        keys = {obj.key for obj in ctx.objects}
        connected: set[str] = set()
        for edge in ctx.edges:
            if edge.src in keys and edge.dst in keys:
                connected.add(edge.src)
                connected.add(edge.dst)
        if not connected:
            # No known edge anywhere: uninformative, not alarming. Stay lit.
            return dict.fromkeys(keys, 1.0)
        return {k: (1.0 if k in connected else 0.0) for k in keys}


# --- Phase F: temporal functions over run history ---------------------------
#
# All three return nothing at all for objects the history does not cover:
# absence is a missing key, and the channel layer turns a missing key into
# None on the lot, which renders as unknown -- never as stale or failed.


class LastBuildAt:
    """When each object was last built: dbt models from their newest node
    result, raw tables from their schema's newest dlt load."""

    name = "last_build_at"
    scope: Literal["object", "edge"] = "object"
    kind: SignalKind = "timestamp"

    def compute(self, ctx: PipelineContext) -> dict[str, SignalValue]:
        result: dict[str, SignalValue] = {}
        # dbt's own source-freshness snapshot is per-table truth and beats
        # everything else for the sources it covers.
        for key, verdict in ctx.source_freshness_by_key.items():
            loaded = _parse_iso(verdict.max_loaded_at)
            if loaded is not None:
                result[key] = loaded
        if ctx.runs is None:
            return result
        for key, node_id in ctx.dbt_nodes_by_key.items():
            node = ctx.runs.node_results.get(node_id)
            if node is not None and key not in result:
                result[key] = node.started_at
        for obj in ctx.objects:
            if obj.key in result:
                continue
            # Case-folded, like the sibling dlt_rows join in RowDelta: the
            # warehouse spells the schema, dlt records it, and they disagree
            # the moment a catalog is a copy of a Snowflake account.
            loaded = ctx.runs.dlt_loaded_at.get(obj.schema.lower())
            if loaded is not None:
                result[obj.key] = loaded
        return result


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


BUILD_STATUS_VOCABULARY = frozenset({"success", "error", "skipped", "partial"})


class BuildStatus:
    """The newest run's status for each dbt-managed object."""

    name = "build_status"
    scope: Literal["object", "edge"] = "object"
    kind: SignalKind = "status"

    def compute(self, ctx: PipelineContext) -> dict[str, SignalValue]:
        if ctx.runs is None:
            return {}
        result: dict[str, SignalValue] = {}
        for key, node_id in ctx.dbt_nodes_by_key.items():
            node = ctx.runs.node_results.get(node_id)
            if node is None:
                continue
            status = node.status.lower()
            if status in BUILD_STATUS_VOCABULARY:
                result[key] = status
            elif status:  # an unrecognised word maps to the nearest honest one
                result[key] = "partial"
        return result


TEST_STATUS_VOCABULARY = frozenset({"pass", "fail", "warn"})

# dbt writes several spellings; anything unrecognised is treated as fail --
# for a *test result*, an unknown word is not reassurance.
_TEST_FAILING = {"fail", "error"}
_TEST_WARNING = {"warn"}
_TEST_PASSING = {"pass", "success", "skipped"}


class TestStatus:
    """Worst test result attached to each object: any fail -> fail."""

    name = "test_status"
    scope: Literal["object", "edge"] = "object"
    kind: SignalKind = "status"

    def compute(self, ctx: PipelineContext) -> dict[str, SignalValue]:
        if ctx.runs is None:
            return {}
        result: dict[str, SignalValue] = {}
        for key, refs in ctx.tests_by_key.items():
            statuses = [
                ctx.runs.node_results[ref.unique_id].status.lower()
                for ref in refs
                if ref.unique_id in ctx.runs.node_results
            ]
            if not statuses:
                continue  # tests declared but never run: unknown, not pass
            if any(s in _TEST_FAILING or s not in (_TEST_WARNING | _TEST_PASSING) for s in statuses):
                result[key] = "fail"
            elif any(s in _TEST_WARNING for s in statuses):
                result[key] = "warn"
            else:
                result[key] = "pass"
        return result


class RowDelta:
    """Rows loaded by the newest dlt load per raw table. No dbt-model coverage
    in v1 and says so: `rows_affected` is NULL on the duckdb adapter, and this
    project does not fake it from estimated_size."""

    name = "row_delta"
    scope: Literal["object", "edge"] = "object"
    kind: SignalKind = "scalar"

    def compute(self, ctx: PipelineContext) -> dict[str, SignalValue]:
        if ctx.runs is None:
            return {}
        result: dict[str, SignalValue] = {}
        for obj in ctx.objects:
            rows = ctx.runs.dlt_rows.get(obj.key.lower())
            if rows is not None:
                result[obj.key] = float(rows)
        return result


FRESHNESS_VOCABULARY = frozenset({"pass", "warn", "error"})


class SourceFreshnessStatus:
    """dbt's own SLA verdict per source, from `dbt source freshness`.

    The verdict is dbt's, not ours: the project configured warn_after and
    error_after, dbt judged the loaded-at against them, and this signal only
    relays the word. `runtime error` folds to `error` -- a check that could
    not run is not reassurance.
    """

    name = "source_freshness_status"
    scope: Literal["object", "edge"] = "object"
    kind: SignalKind = "status"

    def compute(self, ctx: PipelineContext) -> dict[str, SignalValue]:
        result: dict[str, SignalValue] = {}
        for key, verdict in ctx.source_freshness_by_key.items():
            status = verdict.status.lower()
            result[key] = status if status in FRESHNESS_VOCABULARY else "error"
        return result


register(RowCount())
register(LineageReachability())
register(EdgeVolume())
register(LineageParticipation())
register(LastBuildAt())
register(BuildStatus())
register(TestStatus())
register(RowDelta())


class SchemaDriftAt:
    """When each dbt-managed object's schema last changed, from the CLI's
    dbt_schema_changes capture. Absence means no recorded drift -- most
    objects, most of the time."""

    name = "schema_drift_at"
    scope: Literal["object", "edge"] = "object"
    kind: SignalKind = "timestamp"

    def compute(self, ctx: PipelineContext) -> dict[str, SignalValue]:
        if ctx.runs is None:
            return {}
        result: dict[str, SignalValue] = {}
        for key, node_id in ctx.dbt_nodes_by_key.items():
            changed = ctx.runs.schema_changed_at.get(node_id)
            if changed is not None:
                result[key] = changed
        return result


register(SourceFreshnessStatus())
register(SchemaDriftAt())
