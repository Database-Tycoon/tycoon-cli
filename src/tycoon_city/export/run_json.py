"""The run documents: `runs.json` (the index) and `runs/<id>.json` (one run).

`docs/run-json-v1.md` is normative; this module is its only producer, the same
one-producer discipline `city_json` states for the contract.

**Why these are not part of `city.json`.** A run record is an `invocation_id`
and a wall-clock timestamp. `city.json` v1 is byte-stable and carries no uuid,
timestamp, path or seed — that is what makes a committed golden and a
cross-language contract test possible — so records that carry them live in
their own documents. The precedent is CRLF's request/shipment records
(`docs/agent_tasks/specification_citizen_request_framework.md`). These
documents are therefore explicitly **not** byte-stable, and nothing here may
ever be folded back into the contract emitter.

The `replay` block inside `city.json` is a different thing and stays where it
is: an aggregate schedule of the newest status per node, reconstructed from
durations, naming no run. This module reconstructs a **specific invocation**,
failures and skips included.

Three facts, joined, never inflated:

- dbt's own `status` word per node, relayed rather than remapped. `sim.signals`
  folds unrecognised words down for the visual channels because a channel has
  to pick a colour; a record has no such excuse, so the client folds.
- the run's node set, intersected with this city's buildings. What ran but has
  no building here is listed in `unmapped[]`, never silently dropped.
- the city's measured lineage edges, which supply both `depends_on` and the
  reachability behind `failure_cascade`.
"""

import json
import re
from typing import Any

from ..catalog.models import Edge, PipelineContext
from ..catalog.run_history import MAX_REPLAY_RUNS, DbtRun, RunNode
from ..sim.build_replay import RECONSTRUCTED_NOTE, induced_subgraph, topological_order
from ..sim.channels import as_naive_utc

INDEX_FORMAT = "database-tycoon.runs"
RUN_FORMAT = "database-tycoon.run"
VERSION = 1

# Whether the step order was read from the data or rebuilt from the graph.
# `dbt_nodes` carries per-node durations and no per-node start times (probed
# against the real schema, 2026-08-06), so today every document says
# "reconstructed". The field exists so a client never has to guess which it is
# looking at, and so a metadata database that one day records start times can
# say "observed" without a version bump or a client change.
ORDER_OBSERVED = "observed"
ORDER_RECONSTRUCTED = "reconstructed"

# dbt's spellings for "this node failed" and "this node never ran because
# something upstream did". Used only to COUNT and to build the cascade; the
# document always relays the original word.
FAILED_STATUSES = frozenset({"error", "fail", "failure", "runtime error"})
SKIPPED_STATUSES = frozenset({"skipped", "skip"})

# Emitted when there is no run history at all to index — an ordinary plain
# DuckDB file, say, which has no `.tycoon/metadata.duckdb` behind it. The
# loader's own sentences (missing metadata db, locked db, no runs yet) are
# already in `ctx.notes` and are passed through verbatim rather than restated.
NO_HISTORY_NOTE = "no dbt run history for this catalog"

# An id has to become a filename in the static export. Real invocation_ids are
# uuids; anything that could steer a write outside the output directory is
# refused rather than sanitised into a different run's name.
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


def _listed(ctx: PipelineContext) -> tuple[DbtRun, ...]:
    """The runs that have a document: the newest `MAX_REPLAY_RUNS`.

    Exactly the window `read_run_history` kept node detail for, so the index
    never advertises a run whose document would come back empty.
    """
    if ctx.runs is None:
        return ()
    return tuple(ctx.runs.runs[:MAX_REPLAY_RUNS])


def known_run_ids(ctx: PipelineContext) -> set[str]:
    """Every id `run_document` will answer for. The server validates against
    this set *before* an id reaches any path or filename."""
    return {run.invocation_id for run in _listed(ctx)}


def run_file_name(run_id: str) -> str | None:
    """`<id>.json` when the id is safe to use as a filename, else None."""
    return f"{run_id}.json" if _SAFE_ID.fullmatch(run_id) else None


def _node_kind(unique_id: str) -> str:
    """dbt unique_ids are `<resource_type>.<package>.<name>`, so the kind is
    the first segment: model, test, source, seed, snapshot.

    Taken from the id rather than by widening the `dbt_nodes` query: a metadata
    database written by an older CLI without a `resource_type` column would
    fail the whole node read and cost every temporal signal in the city, which
    is a steep price for a label that the id already carries.
    """
    return unique_id.split(".", 1)[0] if "." in unique_id else ""


def _split(ctx: PipelineContext, run_id: str) -> tuple[dict[str, RunNode], list[RunNode]]:
    """This run's nodes as (object_key -> node) for what has a building here,
    plus everything else in id order — tests, seeds, models from another
    target's catalog. Absence stays named: the second list is emitted."""
    nodes = ctx.runs.run_nodes.get(run_id, ()) if ctx.runs is not None else ()
    key_of = {unique_id: key for key, unique_id in ctx.dbt_nodes_by_key.items()}
    mapped: dict[str, RunNode] = {}
    unmapped: list[RunNode] = []
    for node in nodes:
        key = key_of.get(node.unique_id)
        if key is None:
            unmapped.append(node)
        else:
            mapped[key] = node
    return mapped, unmapped


def _step_order(mapped: dict[str, RunNode], edges: tuple[Edge, ...]) -> list[str]:
    """This run's building keys in reconstructed execution order.

    Topological over the edges among *this run's* steps, ties broken on
    object_key, so a fixed input always produces the same document. Any key the
    walk could not release (a cycle — impossible in dbt, cheap to survive) is
    appended in key order: a step may never vanish from the record.
    """
    upstream, downstream = induced_subgraph(mapped, edges)
    order = topological_order(upstream, downstream)
    return order + sorted(set(mapped) - set(order))


def _reachable(downstream: dict[str, list[str]], start: str) -> set[str]:
    """Everything downstream of `start` over the city's edges, `start` excluded.

    Walked over the whole city graph, not just this run's steps: a skip cascade
    in dbt propagates through the DAG whether or not every link in the chain
    was itself selected.
    """
    seen: set[str] = set()
    queue = list(downstream.get(start, ()))
    while queue:
        key = queue.pop()
        if key in seen or key == start:
            continue
        seen.add(key)
        queue.extend(downstream.get(key, ()))
    return seen


def _header(ctx: PipelineContext, run: DbtRun) -> dict[str, Any]:
    """One run's summary line, in both documents so a client can render the
    picker and the header from either without a second fetch."""
    mapped, unmapped = _split(ctx, run.invocation_id)
    return {
        "id": run.invocation_id,
        "command": run.command,
        # The one place a run's wall clock enters a document, normalised
        # through `sim.channels.as_naive_utc` like every other timestamp here.
        "started_at": as_naive_utc(run.started_at).isoformat(),
        "target": run.target,
        # Derived, never the stored `success` column: NULL on every real row.
        "ok": run.ok,
        "models_error": run.models_error,
        "tests_failed": run.tests_failed,
        "elapsed_s": round(run.elapsed_s, 3),
        # Steps that land on a building in THIS city, and what ran without one.
        "step_count": len(mapped),
        "unmapped_count": len(unmapped),
        # Failing steps with a building — what the replay can set on fire.
        # dbt's own `models_error` and `tests_failed` counts sit beside it and
        # will differ whenever the run touched models this catalog has not got.
        "failed_count": sum(1 for node in mapped.values() if _is_failure(node)),
    }


def _is_failure(node: RunNode) -> bool:
    return node.status.strip().lower() in FAILED_STATUSES


def _is_skip(node: RunNode) -> bool:
    return node.status.strip().lower() in SKIPPED_STATUSES


def runs_index(ctx: PipelineContext) -> dict[str, Any]:
    """`runs.json`: every replayable run, newest first, with its notes."""
    listed = _listed(ctx)
    notes = list(ctx.notes)
    if ctx.runs is None:
        # The loader has already said WHY (no metadata database, or unreadable
        # because a tycoon command holds the write lock) in `ctx.notes`, in its
        # own words. This says what follows from it.
        notes.append(NO_HISTORY_NOTE)
    elif len(ctx.runs.runs) > len(listed):
        notes.append(f"showing the newest {len(listed)} of {len(ctx.runs.runs)} runs")
    return {
        "format": INDEX_FORMAT,
        "version": VERSION,
        "database": ctx.database_name,
        "runs": [_header(ctx, run) for run in listed],
        "notes": notes,
    }


def run_document(ctx: PipelineContext, run_id: str) -> dict[str, Any] | None:
    """`runs/<id>.json`: one invocation, step by step. None for an unknown id."""
    run = next((r for r in _listed(ctx) if r.invocation_id == run_id), None)
    if run is None:
        return None

    mapped, unmapped = _split(ctx, run_id)
    order = _step_order(mapped, ctx.edges)
    index_of = {key: position for position, key in enumerate(order)}

    # depends_on and the cascade both read the whole city's graph: a step's
    # upstream is a fact about the map, not about this run. `induced_subgraph`
    # is the ONE place "edges among these keys" is defined -- an edge to
    # something that is not on the map is dropped there, which is why there is
    # no second filter here to go stale.
    city_upstream, city_downstream = induced_subgraph({obj.key for obj in ctx.objects}, ctx.edges)

    steps = [
        {
            "order": position,
            "object_key": key,
            "unique_id": mapped[key].unique_id,
            "node_kind": _node_kind(mapped[key].unique_id),
            # dbt's own word, relayed. The client folds it for colour.
            "status": mapped[key].status,
            "execution_time_s": round(mapped[key].execution_time_s, 3),
            # Intersected with this city's objects: a client cannot draw a road
            # to something that is not on the map (`blocks._edges` sets that
            # precedent), so it is never handed a key it cannot resolve.
            "depends_on": sorted(city_upstream.get(key, ())),
        }
        for position, key in enumerate(order)
    ]

    return {
        "format": RUN_FORMAT,
        "version": VERSION,
        "run": _header(ctx, run),
        "order_source": ORDER_RECONSTRUCTED,
        "note": RECONSTRUCTED_NOTE,
        "steps": steps,
        "unmapped": [
            {
                "unique_id": node.unique_id,
                "node_kind": _node_kind(node.unique_id),
                "status": node.status,
                "execution_time_s": round(node.execution_time_s, 3),
            }
            for node in unmapped
        ],
        "failure_cascade": _cascade(mapped, order, index_of, city_downstream),
    }


def _cascade(
    mapped: dict[str, RunNode],
    order: list[str],
    index_of: dict[str, int],
    city_downstream: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """What each failure took down with it — three measured facts joined.

    A step is in a failure's cascade when dbt itself reported it `skipped`, it
    is reachable from the failure over the city's edges, and it comes later in
    this run's order. Never an inferred blast radius: a descendant dbt did not
    report skipped is not dimmed, and neither is a skip the reconstruction
    cannot place after the failure. An entry is emitted for every failure, with
    an empty list when nothing measurable followed — "nothing cascaded" is a
    fact worth stating.
    """
    skipped = {key for key, node in mapped.items() if _is_skip(node)}
    cascade: list[dict[str, Any]] = []
    for key in order:
        if not _is_failure(mapped[key]):
            continue
        reached = _reachable(city_downstream, key)
        cascade.append(
            {
                "object_key": key,
                "order": index_of[key],
                "skipped": sorted(other for other in skipped & reached if index_of[other] > index_of[key]),
            }
        )
    return cascade


def dumps(doc: dict[str, Any]) -> str:
    """Plain `json.dumps(indent=2)`.

    No token substitution and no byte-stability claim: these documents carry an
    invocation_id and a wall-clock timestamp by design, so there is nothing here
    for a golden to pin. `city_json.dumps` is the one that has to be careful.
    """
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
