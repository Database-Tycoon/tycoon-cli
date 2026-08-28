"""Read `.tycoon/metadata.duckdb` — run history for the city's temporal signals.

Three rules, each verified against the real database (dogfood, 2026-08-04):

- **Read-only connect, never `ensure_schema`.** Two processes cannot both hold
  a DuckDB write handle, and a `tycoon` command may be running right now. A
  locked or unreadable database degrades to None, not an error.
- **Never read `dbt_runs.success`.** It is NULL on every real row (dbt 1.11's
  run_results.json has no such key); a run is ok when
  `models_error == 0 and tests_failed == 0`.
- **Tolerate NULL `rows_affected`** (NULL on all 244 real node rows — the
  duckdb adapter does not report it).

Every table is read behind its own try/except: a metadata database written by
an older CLI missing one table costs that table's signals, nothing else.

`dbt_nodes` was probed again on 2026-08-06 for the run-replay feature: its
columns are `invocation_id, node_name, resource_type, status, execution_time_s,
rows_affected, compile_time_s, message`. There are **no per-node timestamps**,
which is why `run_nodes` records durations and statuses and leaves ordering to
be reconstructed downstream (`sim.build_replay.topological_order`).
"""

import dataclasses
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import duckdb

logger = logging.getLogger(__name__)

# How many invocations keep their per-node detail. A year of hourly builds is
# ~9,000 runs and every one of them would otherwise be held in memory in full;
# replay is a thing you do to a recent run, so the window is small and the
# documents say out loud that it is a window (see `docs/run-json-v1.md`).
MAX_REPLAY_RUNS = 20


@dataclass(frozen=True)
class DbtRun:
    invocation_id: str
    command: str
    started_at: datetime
    target: str
    ok: bool  # derived; the stored `success` column is never read
    models_error: int
    tests_failed: int
    elapsed_s: float


@dataclass(frozen=True)
class NodeResult:
    """The most recent status per dbt node (model or test), across runs."""

    status: str
    execution_time_s: float
    invocation_id: str
    started_at: datetime


@dataclass(frozen=True)
class RunNode:
    """One node's result inside ONE invocation — the unit a replay steps through.

    `status` is dbt's own word, kept exactly as written (`success`, `error`,
    `skipped`, `pass`, `fail`, `warn`, ...). `node_results` above folds a node's
    runs down to the newest and `build_history` keeps only the successes; both
    throw away the failures and skips a single run is made of.
    """

    unique_id: str
    status: str
    execution_time_s: float


@dataclass(frozen=True)
class RunHistory:
    runs: tuple[DbtRun, ...]  # newest first
    node_results: dict[str, NodeResult]  # unique_id -> latest result
    # Both dlt maps are keyed LOWERCASE and their consumers lowercase the
    # catalog side to match. dlt records the schema it ingested under, the
    # warehouse spells it however the warehouse spells it, and on a DuckDB
    # copy of a Snowflake account that is `RAW` against dlt's `raw`: an
    # exact-match join drops the whole district's load time, which then
    # renders as "never loaded" — the one thing unknown must never look like.
    dlt_loaded_at: dict[str, datetime]  # source_schema (lowercase) -> newest inserted_at
    dlt_rows: dict[str, int]  # "schema.table" (lowercase) -> newest rows_loaded
    # unique_id -> newest captured_at in dbt_schema_changes: schema drift.
    schema_changed_at: dict[str, datetime]
    notes: tuple[str, ...]
    # unique_id -> every successful build as (started_at, execution_time_s),
    # oldest first. The road-load overlay derives cadence AND cost from this;
    # node_results keeps only the latest and cannot.
    build_history: dict[str, tuple[tuple[datetime, float], ...]] = dataclasses.field(default_factory=dict)
    # invocation_id -> that ONE run's node results, every status, sorted by
    # unique_id. Only the newest MAX_REPLAY_RUNS invocations are kept. This is
    # what makes a specific `dbt build` replayable step by step; the two fields
    # above answer "what is the state now" and cannot.
    run_nodes: dict[str, tuple[RunNode, ...]] = dataclasses.field(default_factory=dict)

    @property
    def latest(self) -> DbtRun | None:
        return self.runs[0] if self.runs else None


# The cadence denominator never goes below one hour. A backfill that rebuilt a
# model six times in ninety seconds is not evidence of 5,760 builds a day, and
# dividing by the real span would say exactly that.
SPAN_FLOOR_DAYS = 1 / 24


def observed_span_days(history: tuple[tuple[datetime, float], ...]) -> float:
    """The real window these builds were observed over, in days. A fact, so it
    is deliberately **not** floored — the floor belongs to the rate's
    denominator, and a reader comparing the two must see the window that
    actually happened."""
    if len(history) < 2:
        return 0.0
    times = [at for at, _ in history]
    return (max(times) - min(times)).total_seconds() / 86400


def daily_rate(history: tuple[tuple[datetime, float], ...]) -> float | None:
    """Builds per day for one node: (n-1) intervals over their real span, with
    the span floored at one hour.

    The **single** cadence calculator in this project. The road-load overlay
    (`daily_load_s`) and the per-object usage block both derive from it, so
    "how often" means one thing in both places and a change reaches both.

    None — never a guess — when there are fewer than two builds (one build
    offers no interval to measure) or the span is zero (a burst in a single
    instant says nothing about a daily rhythm).
    """
    if len(history) < 2:
        return None
    span_days = observed_span_days(history)
    if span_days <= 0:
        return None
    return (len(history) - 1) / max(span_days, SPAN_FLOOR_DAYS)


def daily_load_s(history: tuple[tuple[datetime, float], ...]) -> float | None:
    """Expected warehouse-seconds per day for one model, measured two ways:
    build cadence times mean build cost.

    Stephen's analogy (2026-08-05): the warehouse carries load, so roads show
    load. None whenever the cadence is unknown — absence propagates rather
    than collapsing into a zero that would read as "this road is quiet".
    """
    cadence = daily_rate(history)
    if cadence is None:
        return None
    mean_cost = sum(cost for _, cost in history) / len(history)
    return cadence * mean_cost


def _rows(con: duckdb.DuckDBPyConnection, sql: str) -> list[tuple]:
    """One table's rows, or none: a missing table costs its signals only."""
    try:
        return con.execute(sql).fetchall()
    except duckdb.Error as exc:
        logger.info("metadata table unavailable (%s)", exc)
        return []


def read_run_history(path: Path | str, prefer_target: str | None = None) -> RunHistory | None:
    """The history, or None when the database cannot be opened at all
    (missing, locked by a running `tycoon` command, or corrupt)."""
    try:
        con = duckdb.connect(str(path), read_only=True)
    except duckdb.Error as exc:
        logger.warning("could not open run metadata %s: %s", path, exc)
        return None

    try:
        run_rows = _rows(
            con,
            "select invocation_id, command, started_at, target_name, "
            "models_error, tests_failed, elapsed_s from dbt_runs",
        )
        node_rows = _rows(
            con,
            "select node_name, status, execution_time_s, invocation_id from dbt_nodes",
        )
        dlt_run_rows = _rows(con, "select source_schema, max(inserted_at) from dlt_runs group by 1")
        dlt_table_rows = _rows(
            con,
            "select source_schema, table_name, rows_loaded from dlt_rows_by_table "
            "qualify row_number() over (partition by source_schema, table_name "
            "order by captured_at desc) = 1",
        )
        drift_rows = _rows(con, "select unique_id, max(captured_at) from dbt_schema_changes group by 1")
    finally:
        con.close()

    notes: list[str] = []
    runs = [
        DbtRun(
            invocation_id=r[0],
            command=r[1],
            started_at=r[2],
            target=r[3] or "",
            # The rule: derived, never the stored NULL `success` column.
            ok=(r[4] or 0) == 0 and (r[5] or 0) == 0,
            models_error=r[4] or 0,
            tests_failed=r[5] or 0,
            elapsed_s=r[6] or 0.0,
        )
        for r in run_rows
    ]

    # A note may only describe what actually happened. The earlier shape said
    # "run history from target '<first>'" whenever a `prefer_target` was given,
    # including when it matched nothing and the runs were therefore left
    # UNFILTERED — claiming a filter that never ran, and naming the wrong
    # target while doing it.
    targets = sorted({run.target for run in runs if run.target})
    matched = prefer_target is not None and any(run.target == prefer_target for run in runs)
    if matched:
        runs = [run for run in runs if run.target == prefer_target]
        hidden = [t for t in targets if t != prefer_target]
        if hidden:  # nothing was excluded when it was the only target present
            notes.append(f"run history filtered to target '{prefer_target}' (hiding {', '.join(hidden)})")
    elif prefer_target is not None and targets:
        shown = targets[0] if len(targets) == 1 else ", ".join(targets)
        notes.append(f"no run history for target '{prefer_target}'; showing all runs ({shown})")
    elif len(targets) == 1:
        notes.append(f"run history from target '{targets[0]}'")
    elif len(targets) > 1:
        notes.append(f"run history spans targets: {', '.join(targets)}")

    runs.sort(key=lambda run: run.started_at, reverse=True)
    kept = {run.invocation_id: run for run in runs}

    # The replay window, decided here and not per row: `runs` is already sorted
    # newest first, so this is the set of invocations whose per-node detail is
    # worth carrying.
    replayable = {run.invocation_id for run in runs[:MAX_REPLAY_RUNS]}

    node_results: dict[str, NodeResult] = {}
    build_history: dict[str, list[tuple]] = {}
    run_nodes: dict[str, list[RunNode]] = {}
    for name, status, seconds, invocation_id in node_rows:
        run = kept.get(invocation_id)
        if run is None:  # filtered out with its run (other target), or orphaned
            continue
        if invocation_id in replayable:
            # Every status, unfolded: an `error` and the `skipped` nodes behind
            # it ARE the replay. One pass over the rows already fetched — this
            # module connects once, reads once, and closes.
            run_nodes.setdefault(invocation_id, []).append(
                RunNode(unique_id=name, status=status or "", execution_time_s=seconds or 0.0)
            )
        current = node_results.get(name)
        if current is None or run.started_at > current.started_at:
            node_results[name] = NodeResult(
                status=status or "",
                execution_time_s=seconds or 0.0,
                invocation_id=invocation_id,
                started_at=run.started_at,
            )
        if (status or "") == "success":
            build_history.setdefault(name, []).append((run.started_at, seconds or 0.0))

    return RunHistory(
        runs=tuple(runs),
        node_results=node_results,
        dlt_loaded_at={schema.lower(): at for schema, at in dlt_run_rows if at is not None},
        dlt_rows={f"{schema}.{table}".lower(): rows or 0 for schema, table, rows in dlt_table_rows},
        schema_changed_at={uid: at for uid, at in drift_rows if at is not None},
        notes=tuple(notes),
        build_history={name: tuple(sorted(builds)) for name, builds in build_history.items()},
        run_nodes={
            invocation_id: tuple(sorted(nodes, key=lambda node: node.unique_id))
            for invocation_id, nodes in run_nodes.items()
        },
    )
