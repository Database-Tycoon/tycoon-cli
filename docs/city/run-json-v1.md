---
title: run.json v1
description: The normative wire format for replaying one specific dbt run — the runs index, one run's steps, and why these documents live outside city.json
tags: [contract, format, export, replay, runs]
related: [city-json-v1, handover, agent_tasks/specification_citizen_request_framework]
updated: '2026-08-06'
---

# `runs.json` / `runs/<id>.json` v1

Two documents that let a client replay **one specific `dbt build`** step by
step: a model errors, its building ignites at that moment, and the downstream
models dbt reported as skipped dim as the cascade spreads.

Produced by `tycoon_city.export.run_json` — the only producer, the same
one-producer discipline `city.json` has — and served or written at the same
two paths either way:

```bash
uv run tycoon-city <tycoon-project>/            # GET /runs.json, GET /runs/<id>.json
uv run tycoon-city-export <src> out/            # out/runs.json, out/runs/<id>.json
```

## Why these are not in `city.json`

A run record is an `invocation_id` and a wall-clock timestamp. `city.json` v1
is **byte-stable** and carries no uuid, timestamp, path or seed — that is what
makes the committed golden and a cross-language contract test possible. So
records that carry them get their own documents. The precedent is CRLF's
request and shipment records (`docs/agent_tasks/specification_citizen_request_framework.md`),
decided for the same reason.

**These documents are therefore NOT byte-stable, and there is no golden.** The
same catalog produces the same content for a fixed metadata database — every
collection is sorted on a key that cannot tie, and the step order is
deterministic — but they carry ids and timestamps by design, so nothing here
may ever be folded back into the contract emitter.
`tests/export/test_run_json.py` pins the boundary from the other side: it
asserts that no `invocation_id` and no run timestamp appears anywhere in the
bytes of `city.json`.

The `replay` block **inside** `city.json` is a different thing and stays where
it is: an aggregate schedule of the newest status per node, reconstructed from
durations, naming no run. This format reconstructs a *named invocation*, with
its failures and skips.

## `runs.json` — the index

| Key | Type | Meaning |
|---|---|---|
| `format` | string | Always `"database-tycoon.runs"` |
| `version` | integer | `1`. Bump on any breaking change |
| `database` | string | The catalog's name, matching `city.json`'s `database.name` |
| `runs` | array | Run headers, **newest first** |
| `notes` | array | The loader's degradation ladder, verbatim, plus the two below |

Always answered, always `200` for a catalog that loads at all. No history is an
empty `runs` with the reason in `notes`, never a 404 — a client cannot tell
404 "no runs" from 404 "wrong host". The reasons are the loader's own
sentences, passed through rather than restated here: `no run history yet`, `no
run metadata (.tycoon/metadata.duckdb)`, `run metadata unreadable (locked by a
running tycoon command?)`. Two of this format's own may join them:
`no dbt run history for this catalog` (there is no history to index at all) and
`showing the newest N of M runs` (see the window, below).

### The run header

Carried in both documents, so a client renders the picker and the run's header
from either without a second fetch.

| Key | Type | Meaning |
|---|---|---|
| `id` | string | The `invocation_id`. The only handle a client needs |
| `command` | string | dbt's own command word (`run`, `build`, `test`, …) |
| `started_at` | string | Naive-UTC ISO 8601, normalised through `sim.channels.as_naive_utc` |
| `target` | string | The dbt target the run used |
| `ok` | boolean | **Derived**: no error models and no failed tests. The stored `success` column is NULL on every real row and is never read |
| `models_error` / `tests_failed` | integer | dbt's own counts, for the whole run |
| `elapsed_s` | number | Wall-clock seconds for the run |
| `step_count` | integer | Nodes that land on a building in THIS city |
| `unmapped_count` | integer | Nodes that ran without one (tests, seeds, models this catalog has not got) |
| `failed_count` | integer | Failing steps **with a building** — what the replay can set on fire. It differs from `models_error` whenever the run touched models that are not on this map, and that difference is information, not a bug |

### The window

Only the newest **20** invocations (`catalog.run_history.MAX_REPLAY_RUNS`) keep
per-node detail: a year of hourly builds is ~9,000 runs and replay is something
you do to a recent one. The index lists exactly those — so an id it lists
always has a document, and an id it does not is a 404 — and says
`showing the newest N of M runs` when it has hidden any. Absence stays named.

## `runs/<id>.json` — one run

| Key | Type | Meaning |
|---|---|---|
| `format` | string | Always `"database-tycoon.run"` |
| `version` | integer | `1` |
| `run` | object | The header above |
| `order_source` | string | `"reconstructed"` or `"observed"` — see below |
| `note` | string | The same sentence `city.json`'s `replay` carries: `durations measured, ordering reconstructed` |
| `steps` | array | Nodes with a building here, in execution order |
| `unmapped` | array | Nodes without one. Always emitted |
| `failure_cascade` | array | What each failure took down with it |

`404` with a JSON body (`{"error": "unknown run", "id": …}`) for an id outside
the window. The server matches the id against the known invocation set
**before** it is used for anything else; nothing in this path opens a file.

### `order_source` — reconstructed, and saying so

`dbt_nodes` carries per-node **durations** and no per-node start times (probed
against the real schema on 2026-08-06: `invocation_id, node_name,
resource_type, status, execution_time_s, rows_affected, compile_time_s,
message`). So the order is rebuilt topologically over the city's measured
edges, ties broken on `object_key`, sharing
`sim.build_replay.topological_order` with the aggregate schedule so the two can
never drift.

`order_source` is emitted so a client never has to guess which it is looking
at, and so a metadata database that one day records start times can say
`"observed"` without a version bump or a client change. Today every document
says `"reconstructed"`.

### `steps[]`

| Key | Type | Meaning |
|---|---|---|
| `order` | integer | Dense `0..n-1`, the reconstructed execution order |
| `object_key` | string | The building, matching `city.json`'s `lots[].object_key` |
| `unique_id` | string | dbt's node id |
| `node_kind` | string | The id's first segment: `model`, `test`, `seed`, `snapshot`, `source` |
| `status` | string | **dbt's own word**, relayed — see below |
| `execution_time_s` | number | Measured, from `dbt_nodes` |
| `depends_on` | array | Upstream `object_key`s, **intersected with this city's objects** |

`status` is relayed, never remapped. `sim.signals` folds unrecognised words
down (`BUILD_STATUS_VOCABULARY`) because a visual channel has to pick a colour;
a record has no such excuse, so an unknown word such as `partial success`
arrives at the client intact and **the client folds it**.

`depends_on` is intersected with the city's object set for the same reason
`edges` is in `city.json`: a client cannot draw a road to something that is not
on the map, so it is never handed a key it cannot resolve.

### `unmapped[]` — always emitted

`unique_id`, `node_kind`, `status`, `execution_time_s` for everything that ran
without a building here — every test node, seeds, and models belonging to a
catalog this city is not. Never silently dropped: a six-step document out of a
seven-node run is a lie by omission, and `step_count + unmapped_count` is the
run's real size.

### `failure_cascade[]` — three measured facts joined

One entry per failing step, in order:

| Key | Type | Meaning |
|---|---|---|
| `object_key` | string | The building that failed |
| `order` | integer | Its position in `steps` |
| `skipped` | array | `object_key`s dimmed by this failure, sorted |

A step is in a failure's cascade when **all three** hold:

1. **dbt itself reported it `skipped`** — never a descendant dbt did not, and
   never an inferred blast radius. If dbt built a downstream model anyway, that
   model stays lit;
2. it is **reachable from the failure over the city's measured edges** —
   transitively, and through models this run did not select, because a dbt skip
   propagates down the DAG that way;
3. it comes **later in this run's order**. Where the chain between the two runs
   through a model this run never touched, the reconstruction has no order to
   place them by, and it does not claim a relationship it cannot see.

An entry is emitted for every failure even when `skipped` is empty: "nothing
measurable cascaded" is a fact worth stating, and a client that only ever sees
non-empty entries cannot tell it from "we did not look".

A statuses caveat, since dbt's words are relayed and not normalised: failure is
recognised as `error`, `fail`, `failure` or `runtime error`, and a skip as
`skipped` or `skip`, case-insensitively. That vocabulary decides counting and
cascade membership only — the `status` field always shows the original.

## Deliberately omitted

| Not emitted | Why |
|---|---|
| Node messages / error text | Not yet read from `dbt_nodes.message`; it may name client data, so it is a decision, not an oversight |
| `rows_affected` | NULL on every real row (the duckdb adapter does not report it) |
| Per-step tick timings | Presentation: the client paces its own playback from `execution_time_s` |
| Anything from `city.json` | One producer per fact. Lots, edges and routes are read from the contract document |

## Changing the format

Any change to emitted keys, types or ordering is a change to this page and a
`version` bump if it breaks a reader. There is no golden to regenerate — that
is the cost of carrying ids and timestamps, and it is why `city.json` does not.
