---
title: city.json v1
description: The normative wire format between Database Tycoon's Python side and any renderer, and why each decision was taken
tags: [contract, format, export, renderer]
related: [handover, superpowers/specs/2026-08-03-city-foundation-design]
updated: '2026-08-06'
---

# `city.json` v1

The single seam between Python and any client. Upstream of it: reading the
catalog, planning the layout, deriving visual state from data. Downstream:
presentation only. A renderer that can read this file needs nothing else from
this repository.

Produced by `tycoon_city.export.city_json` — the only producer — and written by
`tycoon-city-export`. A committed golden lives at `contract/fixtures/demo.city.json`
and `tests/export/test_city_json.py` asserts a fresh emit matches it byte for
byte.

```bash
uv run tycoon-city-export path/to/db.duckdb out/    # writes out/city.json + out/spritesheet.png
uv run python scripts/update_contract_golden.py  # after a deliberate change
```

## Guarantees

**Byte-stable.** The same catalog and theme always produce identical bytes.
Every collection is sorted on a key that cannot tie, edge rates are rounded, and
nothing carries a timestamp, a path, or a random seed. This is what makes both a
committed golden and a cross-language contract test possible.

**No renderer, no engine.** The emitter imports no pygame — enforced by
`tests/export/test_export_no_pygame.py`, which makes pygame *unimportable* in a
subprocess rather than merely checking `sys.modules` afterwards — and it never
constructs an `Engine`, so no tick has to run before an export.

**Self-contained output.** `theme.spritesheet` is a bare filename resolved next
to `city.json`, so the output directory can be served by a static host as-is and
the document says nothing about the machine that produced it.

## Top-level shape

| Key | Type | Meaning |
|---|---|---|
| `format` | string | Always `"database-tycoon.city"` |
| `version` | integer | `1`. Bump on any breaking change |
| `database` | object | `name`, `object_count`, `total_rows`, `has_known_edges`, `notes` |
| `grid` | object | `width`, `height`, `tile_kinds`, `tiles_rle` |
| `plant` | object | `x`, `y` — the database itself, one tile |
| `library` / `firehouse` | object \| null | Civic buildings on the utility strip (context inventory / fire-response dispatch); null on hand-built maps |
| `focus` | object | `min_x`, `min_y`, `max_x`, `max_y` — inclusive tile bbox |
| `districts` | array | One per schema: `schema`, `x`, `y`, `w`, `h` — the bounding rect around its CONNECTED lots (suburb orphans excluded unless the schema is all-orphan; streets v2, 2026-08-05: replaced the ring-era `ring`/`size`; rects are ground tint, may overlap) |
| `street_features` | array | How each road is allowed to END (streets v4, 2026-08-05; additive): `kind` (`apron`/`dock`/`plaza`), `x`, `y`, `facing` (`n`/`s`/`e`/`w`, or null if a future kind faces nothing), `w`, `h` — see below |
| `lots` | array | One per placed object: `object_key`, `x`, `y`, `w`, `h` (ground plan in tiles, NW-anchored — big tables, the top decile of the catalog's row counts, are 2×2; added 2026-08-05), `zone_style`, `target_density`, `powered`, `last_build_age_s`, `build_status`, `test_status`, `freshness_status` (dbt's sources.json SLA verdict), `schema_drift_age_s` |
| `objects` | array | Catalog facts plus `dbt` (nullable: `description`, `materialized`, `tags`, `owner`, `tests[]` with per-test `status`, null = never run), plus `usage` (measured run appearances, nullable) and `semantic` (the declared OSI model, nullable) — see below |
| `edges` | array | Known lineage: `src`, `dst`, `rate`, `provenance`, `route` (the street's tile path), `columns` (column-level lineage pairs), `daily_load_s` (expected compute, nullable) |
| `joins` | array | DECLARED joins from an OSI semantic model (2026-08-06; additive): `name`, `many`, `one`, `cardinality`, `keys`, `composite`, `provenance`, `lineage_edge` — see below. Empty on any catalog with no semantic model |
| `replay` | object \| null | The last run as a playable schedule: `span_ticks`, `note`, `steps[]` (`object_key`, `start`, `duration`) |
| `budget` | object \| null | The compute bill: measured load at a declared rate; null when the run history knows nothing — see below |
| `weather` | object | Source freshness as weather over the districts a late source feeds; empty cells + a note when nothing is judged — see below |
| `achievements` | object | Named coverage milestones, STATELESS and counted from real artifacts: `milestones[]` + `note` — see below |
| `theme` | object | `name`, `logo_text`, `labels`, `colors`, `sprites`, `spritesheet` |

All coordinates are integer tile indices with the origin at the top-left of the
grid, `x` rightward and `y` downward — the same convention the tile grid uses.

## `grid.tiles_rle` — row-major run-length pairs

A flat array of integers read as `[kind_id, run, kind_id, run, …]`, where each
`kind_id` indexes `grid.tile_kinds`. Runs are laid out row-major and **cross row
boundaries**, which is why decoding needs `width` to re-split rows. Decoding is
about ten lines:

```js
const flat = new Uint8Array(grid.width * grid.height)
let at = 0
for (let i = 0; i < grid.tiles_rle.length; i += 2) {
  flat.fill(grid.tiles_rle[i], at, at += grid.tiles_rle[i + 1])
}
```

Kind ids are **positions in `tile_kinds`**, not the values of the Python enum
(`auto()` makes those 1-based). The legend ships inside every document, so a
client resolves a name and never a bare number, and inserting a kind renumbers
the wire ids without breaking anything that reads the legend.

`water` appears in the legend but the generator never emits it. The legend
describes the vocabulary, not the contents.

### Why one line, and why not nested pairs

Measured on three catalogs before the format was fixed:

| Catalog | Grid | Runs | RLE, one line | RLE, one int per line | Nested pairs, `indent=2` | Raw grid, one line |
|---|---|---|---|---|---|---|
| `demo.duckdb` | 42² | 49 | **206 B** | 501 B | 1,089 B | 3,613 B |
| 500 objects, 50-deep chain | 708² | 2,209 | **8.9 KB** | 22 KB | 49 KB | 1.00 MB |
| 500 one-object schemas | 905² | 278,161 | **1.11 MB** | 2.78 MB | 6.12 MB | 1.64 MB |

The last row is the ring-era pathological case: 500 one-object schemas on one
ring shredded every grass row. **The plan's expectation that grass dominance
would keep the run count low holds on realistic catalogs and fails badly on
pathological ones** — nested pairs at `indent=2` would have cost 6.1 MB, past
the point the plan defines as "the schema is wrong", and worse than shipping
the raw grid.

> ⚠️ **These measurements predate streets v2 (2026-08-05).** The layered
> layout produces different grids (wider with channel count, no rings, no
> radial arterials); realistic catalogs remain small (dogfood ≈ 76×54), but
> the 500-object worst case has NOT been re-measured under v2. Re-measure
> before relying on the absolute numbers above.

So `dumps` writes the whole document at `indent=2` *except* `tiles_rle`, which is
spliced in on one line. As shipped, the worst case is **1.31 MB of `city.json`,
27 KB gzipped, emitted in 0.13 s**. Every realistic catalog is orders of
magnitude smaller.

## `lots` — derived visual state, not presentation

`target_density` (1–8) is the level the building should reach. The tween from 0 is
**presentation**, so the client animates the grow-in itself; emitting the tweened
`density` would make the bytes depend on how many ticks had run before the export
and no golden would be possible. `tests/export/test_city_json.py` asserts
`density` is absent.

`zone_style` is one of `industrial`, `commercial`, `residential`, already
resolved. The theme's `[[style_rules]]` regexes never cross the wire and no
client re-implements pattern matching — which is also why `theme` carries no
`style_rules` key.

`powered` false means the object takes part in **no** lineage in either
direction. When the whole catalog has no known lineage, every lot is powered
instead (see `has_known_edges`); a client must not dim the entire map because
lineage could not be determined.

Sprite names follow `lot_<zone_style>_<level>` for levels 1–8, and `grass` /
`grass_alt` alternate on `(x + y) % 2` for ground.

The three temporal keys (added 2026-08-04, Phase F; additive) come from a
tycoon project's run history: `last_build_age_s` (whole seconds at export
time), `build_status` (`success`/`error`/`skipped`/`partial`) and
`test_status` (`pass`/`fail`/`warn`). **null means unknown, and unknown must
render as full colour, no tint, no marker — never as stale.** Documents for
catalogs with run history are time-dependent by nature; byte-stability holds
for runs-free catalogs (the committed golden) and for any fixed injected
`now`.

## `edges` — known lineage with traffic folded on

Only edges whose **both** endpoints appear in `objects` are emitted: a client
cannot draw a road to something that is not on the map. `rate` is the normalised
0–1 traffic rate, rounded to six decimals, which is what retires the Python-side
`dict[tuple[str, str], float]` — unrepresentable in JSON — and keeps the
`"src->dst"` string convention private to `sim.channels`.

`provenance` (added 2026-08-04, Phase E; additive, version unchanged) says
where the edge's knowledge comes from: `"manifest"` (declared in a dbt
manifest — a tycoon project source), `"duckdb"` (the engine's dependency
catalog), or `"view_sql"` (the regex scan over view definitions). Existence is
a union across sources; when several agree, the most authoritative tag wins
(manifest > duckdb > view_sql). Clients label these declared vs inferred.

`route` (added 2026-08-05, streets-are-lineage; additive) is the exact tile
path the edge's street takes, lot to lot, as `[[x, y], ...]` — contiguous
orthogonal steps, endpoints on the two lots. The client's traffic drives these
instead of approximating with manhattan walks. Routes exist for every emitted
edge; older documents without them fall back client-side.

`columns` (added 2026-08-05, skybridges; additive) is the edge's column-level
lineage as sorted `[src_col, dst_col]` pairs, traced by sqlglot from view SQL
and from dbt model code (`compiled_code` when the manifest carries it, else
`raw_code` with the `config`/`ref()`/`source()` jinja subset resolved —
models with residual jinja are counted into a note, never guessed at). Output
columns are the *measured* ones from `duckdb_columns()`, so a pair's `dst_col`
always exists on the destination object. Always present, often empty. A traced
pair guarantees its table edge exists: the loader unions one in even when
`depends_on` never declared it.

`database.notes` (same change) carries the degradation ladder's messages —
"no dbt manifest — lineage from SQL scan only", "run metadata unreadable",
"N upstream sources outside this catalog", "catalog has N objects; showing the
500 most relevant" (the loader's cap, which keeps views first and then the
largest tables, so lineage survives truncation), low-join-rate warnings. Always
present, often empty. The list is free text, so a new message is not a shape
change and needs no version bump. Clients must show them: a named absence must
never render as a silently broken feature.

`database.has_known_edges` is false when no edge has both ends in this catalog.
That is a different fact from "nothing depends on anything": lineage in v1 comes
from view SQL only, so a tables-only warehouse yields zero edges. A client should
say so rather than render a city where nothing is connected.

An edge may run *inward*, from a higher ring to a lower one. A district's ring is
the **modal** lineage depth of its objects, so a schema mixing depths sits on one
ring not all of its objects agree with. This is expected, not corrupt data.

## `street_features` — where a road is allowed to end (streets v4)

Stephen, 2026-08-05: *"there needs to be a clear definition for when and where
a road is allowed to end, and what that looks like."* `docs/road-grammar.md`
holds the full legal-ending taxonomy; this array is the subset a lineage street
actually produces, one record per dressed ending:

| `kind` | Emitted where | Read |
|---|---|---|
| `dock` | the street leaves a **depth-0 source** | industrial loading yard / truck court |
| `plaza` | the street meets a **2×2 lot** or a **civic building** (firehouse) | paved forecourt, the terminated-vista move |
| `apron` | every other building the street touches | the ordinary driveway pad |

Precedence is `plaza` > `dock` > `apron`, which is what makes **a pad wider
than one tile always a plaza** — key your forecourt geometry off that. `w`/`h`
are the pad's ground plan, NW-anchored at (`x`, `y`): only a plaza against a
2×2 lot exceeds 1×1, spanning that building's whole frontage (`h: 2`, since
every street arrives at a building's east or west face — measured, not
assumed). `facing` is the compass direction from the pad **toward** the
building it serves.

Every feature tile is a ROAD tile in `grid.tiles_rle`: a plaza's extra
forecourt tile is *pavement*, painted by the generator like a lane tile. So a
client that ignores this array still renders a coherent city — it just renders
undressed endings.

Sorted by (`kind`, `x`, `y`); ties (one tile serving two buildings, which
happens when a single road tile separates two lots) break on the remaining
fields, so the array is byte-stable. Derived facts only: features come from
route endpoints and lot metadata, never invented. A catalog with no lineage has
no streets and therefore an empty array.

The planner guarantees there is nothing left over: **property S7** fails the
build if any road tile where the network ends (at most one orthogonal ROAD
neighbour) is not carried or touched by a feature. A naked stub is a bug, not a
style opinion.

## `joins` — declared joins, and why they are not `edges`

Added 2026-08-06 (the OSI loader), additive, `version` unchanged. Populated from
an **Apache Ossie / OSI** semantic model found at the project root (or named by
`tycoon.yml`'s `semantic_model:` key); `[]` for every catalog without one, which
is most of them.

| Field | Type | Meaning |
|---|---|---|
| `name` | string | The relationship's declared name |
| `many` | string | Object key on the **many** side |
| `one` | string | Object key on the **one** side — the dimension the join points at |
| `cardinality` | string | Always `"many_to_one"`; the spec has no other kind |
| `keys` | array | `[many-side column, one-side column]` pairs, in declaration order |
| `composite` | bool | More than one pair. Not derived client-side, so a renderer keys its double-marked crossing off one field |
| `provenance` | string | Always `"declared"` |
| `lineage_edge` | array \| null | `[src, dst]` of the `edges` entry on the same pair, or null |

**A separate array, deliberately not folded onto `edges`.** The two are
different claims: an edge asserts *data moved here at build time*, a join
asserts *these two are formally joinable* — true whether or not a build ever
ran between them. The common case settles it: a dimension joined by every query
and never a build input of the fact has no edge to hang off, so folding would
either invent an edge that implies data movement or leave that join with
nowhere to live. A client that reads `edges` and ignores `joins` renders exactly
what it rendered before this key carried anything.

`lineage_edge` is what keeps the two reconciled. When the same pair also has
lineage it names that edge **in the edge's own direction**, which is usually the
reverse of the join's (the dimension flows *into* the fact while the join points
*at* the dimension), so a renderer marks the existing street rather than laying
a parallel road. Null means the pair has no lineage — the join street that has
to be paved out of the dirt.

Both endpoints always appear in `objects`, same rule as `edges`. Declarations
that match no catalog object are dropped and **counted into `database.notes`**
("3 of 12 declared joins did not match a catalog object"): one typo in a
hand-written YAML costs a road, and a road missing for a reason must not look
like a road nobody declared. Sorted by (`many`, `one`, `keys`), which cannot
tie — two relationships on the same pair with the same key columns are one join.

Everything here is **declared**. Nothing in this array is inferred from SQL; a
join guessed from a query is a weaker fact and it already exists, as lineage.

## `objects[].semantic` — the declared dataset, or null

The OSI Dataset that claims this object: `name` (the business name, often not
the table's), `primary_key`, `unique_keys` (arrays of column arrays), and its
`ai_context` as `instructions` (nullable), `synonyms` and `example_queries`.

Null means **no dataset declares this object at all**. A block whose
`instructions` is null and whose lists are empty is a different fact — a dataset
someone named without annotating — and clients render the two differently: the
first is an undocumented building, the second a documented one with no signage
yet.

## `focus` — the opening frame

The inclusive bbox of every lot plus the plant: exactly the coordinate set the 2D
camera frames on (`app._built_tiles`), asserted equal in
`tests/export/test_build.py`. A 3D client should solve its camera distance from
this box's diagonal so the opening frame contains it, rather than inventing a
framing policy. Roads are deliberately outside it — they add at most one tile and
would make the frame describe pavement.

## `replay` — the last run as a schedule (Phase F, additive)

Built topologically over the edges from **measured per-node durations** with an
infinite-parallelism assumption — dbt records durations but not per-node start
times, so ordering is reconstructed, and `note` says exactly that for the
client to display during playback. `null` when there is no history or when the
history's models mostly do not map onto this catalog: the server refuses
rather than misleads. Objects absent from `steps` keep their height during
playback — an unknown building vanishing would read as a build failure.

## Reserved fields (1.0 workstreams)

Four 1.0 workstreams each add a block to this document. Their keys were cut
into the format **once**, on 2026-08-06, ahead of any of them — emitted
unconditionally, always empty — so that four independent branches land content
into a key that already exists instead of four contract changes racing the
golden and the client's schema. Strictly additive: `version` stays `1`.

| Key | Emitted as | Carries | Workstream |
|---|---|---|---|
| `budget` | object \| `null` | **FILLED 2026-08-06** — the compute bill: measured load at a declared rate | measure |
| `weather` | object | **FILLED 2026-08-06** — source freshness as weather over the districts a late source feeds | measure |
| `objects[].usage` | object \| `null` | **FILLED 2026-08-06** — how often the object appears in observed runs | measure |
| `joins` | array | **FILLED 2026-08-06** — declared OSI relationships, many-to-one, separate from `edges` because a join is not a claim that data moved | OSI |
| `objects[].semantic` | object \| `null` | **FILLED 2026-08-06** — the object's declared OSI context and keys | OSI |

All five seams were cut in empty on 2026-08-06 and filled the same day; the
section is kept because the property that made them worth cutting in at once
still holds and is still pinned: **every one of these keys is emitted
unconditionally**, so a client never meets a document that simply lacks one.
What varies is only whether the catalog had anything to say — `budget` is null
without run history, `weather` carries no cells without freshness verdicts
(all-clear there would be clear-because-unknown wearing clear-because-fine),
and `joins` / `semantic` stay `[]` / null without a declared semantic model,
which is most catalogs. Documents written before 2026-08-06 omit all five, so
`web/src/contract.ts` treats each as optional with the empty value as its
default — the same `.optional()` / `.default()` pattern `street_features`
uses — and no client needs a version check to read a document from either
side of the change.

**Filled in so far:** `joins` and `objects[].semantic` (OSI, 2026-08-06 — the
loader half; see the two sections above for their normative shapes). They still
emit `[]` and null on every catalog without a semantic model, so the seam's
promise holds for clients that have not caught up. The remaining three keep the
values in the table above.

Populating one of these is a contract change like any other: it goes through
this page, the golden, and the client's schema in one commit.

## `budget` — the compute bill (measure, 2026-08-06)

The city's money: the **measured** `daily_load_s` that already feeds
`edges[].daily_load_s`, aggregated per object and multiplied by a **declared**
rate. The rate is the only number in this document that is not measured, which
is why it never travels anonymously.

| Field | Meaning |
|---|---|
| `engine` | `duckdb` / `motherduck` / `snowflake`, or whatever a `pricing.toml` declares |
| `currency` | ISO-ish currency word; `USD` unless declared otherwise |
| `unit_price_per_s` | The declared rate per compute-second |
| `price_source` | **Where that rate came from** — the built-in table, or the path of the file that overrode it |
| `daily_load_s` | Total measured compute-seconds/day across priced objects; `null` when nothing could be priced |
| `daily_cost` | `daily_load_s × unit_price_per_s`; `null` when nothing could be priced |
| `priced_objects` / `unpriced_objects` | How much of the map this bill covers, and how much it does not |
| `by_object[]` | `object_key`, `daily_load_s`, `daily_cost` per priced object, sorted by `object_key` |
| `note` | How this engine bills, then this bill's own partiality |

Rounding follows the existing discipline: load to two decimals (the grain
`edges[].daily_load_s` already uses), money to six (`RATE_PRECISION`).

**The two zeros.** Local DuckDB costs `0.0` *as a fact* — the load was
measured, the rate really is zero, and the note says
"local DuckDB is free — the load is measured, the bill is zero". That must
never be confusable with $0-because-nothing-was-measured, so:

* No run history at all → `budget` is **`null`**, and `database.notes` already
  names the reason ("no run history yet", "no run metadata"). There is no
  invented zero.
* History exists but no object has the two builds a cadence needs → the block
  is emitted with `daily_load_s` and `daily_cost` **`null`** and a note ending
  "unknown, not a zero bill".
* Objects with too little history are **excluded from `by_object` and counted**
  in `unpriced_objects`. A partial bill announces its own partiality.

Wording is engine-neutral by construction: Snowflake bills warehouses,
MotherDuck bills ducklings, local DuckDB is free, and nothing in the emitter
knows which one it is describing. Engine *versions* are a later product line.
A project supplies its real rate in a `pricing.toml` beside its catalog, or
via `--pricing`; discovery is anchored to the catalog and never to the working
directory, so the document's bytes cannot depend on where the exporter ran.

## `objects[].usage` — run appearances (measure, 2026-08-06)

`{ "source": "runs", "runs_seen": int, "window_days": float, "rate_per_day":
float | null }`, or `null`.

**This is BUILD/RUN usage, not query usage.** Vanilla DuckDB has no query log,
so there is no query history to read; `docs/semantic-roads.md` already named
query history as the MotherDuck/Snowflake differentiator. The `source`
discriminator is what holds that seam open — a later engine version emits
`"queries"` here and a client switching on the field never has to guess which
one it is looking at.

`runs_seen` counts appearances in recorded successful builds. `window_days` is
the **measured, unfloored** span those appearances happened over.
`rate_per_day` comes from `run_history.daily_rate`, the single cadence
calculator this project has (the road-load overlay uses the same one), whose
denominator is floored at one hour so a backfill burst does not read as
thousands a day. It is **`null`** with fewer than two appearances or a zero
span — never a guess from one data point.

`usage` itself is `null` when the run history says nothing about the object.
**null is unknown, never "unused."** Zero-usage and unknown-usage are
different facts and must not render alike.

## `weather` — source freshness over the districts it feeds (measure, 2026-08-06)

`{ "cells": [ { "schema", "condition", "worst_source", "verdict", "hops" } ],
"note": string }`. Always an object; `cells` may be empty.

`condition` is `clear` / `overcast` / `fog`. The derivation is the interesting
part: **fog covers the districts a late source FEEDS, not the source's own
district.** From every source carrying a `dbt source freshness` verdict, the
emitter walks downstream reachability over the measured `edges` and aggregates
to schema; precedence is *any reachable source with `error` → `fog`, `warn`
only → `overcast`, else `clear`*. `worst_source` names the source that decided
the cell, `verdict` is dbt's own word for it, and `hops` is how far downstream
that district sits. Ties break on the nearer source, then on its key. Sorted by
`schema`.

This is computed in Python and not in the client for the reason this page
already settled for `theme.style_rules`: a multi-hop walk with a precedence
order is a **rule**, not a projection, and clients must not re-derive rules.

A `clear` cell is a **positive assertion** — judged sources reach this district
and none of them is late — which is why every covered district gets one.

**The honesty rule.** `loader` emits "no source freshness snapshot (run `dbt
source freshness`)" whenever sources exist but verdicts do not. In that state a
full set of `clear` cells would render clear-because-unknown as
clear-because-fine, so:

* No verdicts at all → `{"cells": [], "note": "no source freshness verdicts —
  weather unknown"}`. The client renders **no weather** plus a named-absence
  affordance.
* Partial coverage → cells only for districts a **judged** source reaches; the
  uncovered count goes in the note. A district nothing judged can reach gets no
  cell rather than a comforting `clear`.

## `achievements` — named coverage milestones (2026-08-06, additive)

`{ "milestones": [ … ], "note": string }`. Always an object, always six
milestones, `version` unchanged. Documents written before 2026-08-06 omit the
key, so a client's schema treats it as optional with the empty block as its
default — the same `.optional()` / `.default()` pattern `street_features` and
the five reserved seams use, and no version check is needed to read a document
from either side of the change.

Stephen's rule: **achievements are COUNTS OF REAL ARTIFACTS, never invented
points.** `docs/semantic-roads.md`'s incentive table is the design source —
"every mart reachable by paved road", "old town fully signed", each *a count of
real declared artifacts*. Nothing here scores anything; every milestone is a
coverage fraction over things that exist in the catalog.

They are also **STATELESS**, per the 1.0 decision: a milestone is "true right
now", derived from this document and nothing else. There is no minted-badge
store, no first-earned timestamp, nothing persisted. That is what keeps the
document byte-stable, and it is the honest shape — an achievement still lit
after the documentation was deleted would be a trophy, not a measurement.

### One milestone

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Stable handle. The client keys its gauges off this, never off `name` |
| `name` | string | The human milestone |
| `description` | string | One line: what is being counted |
| `state` | string | `met` / `unmet` / **`unknown`** — the discriminator |
| `met` | bool \| null | `null` in the unknown state. Never `false` there |
| `have` / `need` | int \| null | The measured terms; both `null` in the unknown state |
| `short` | array | The **object keys that fall short**, sorted — the HUD's fly-to list. `[]` when met or unknown |
| `note` | string | What `have`/`need` count, or why the milestone is unknown |

`short` is bounded by the loader's 500-object cap and sorted, so the array
cannot tie and the block stays byte-stable. Milestone order is a fixed literal,
which is stronger than sorting on a key that cannot tie.

### The six, and what each one counts

| `id` | Universe (`need`) | Counted (`have`) | Evidence it needs |
|---|---|---|---|
| `documented_buildings` | every catalog object | objects with a non-empty dbt description | a dbt manifest |
| `tested_buildings` | every catalog object | objects a declared dbt test attaches to | a dbt manifest |
| `sources_under_sla` | lineage **origins** (no inbound edge, at least one outbound) plus anything dbt judged | objects with a `dbt source freshness` verdict | a `sources.json` |
| `old_town_signed` | every catalog object | objects whose declared OSI dataset carries `ai_context` | an OSI semantic model |
| `marts_paved` | **marts** — see below | marts an entry in `joins[]` touches on either side | an OSI semantic model |
| `fires_out` | objects whose declared tests have actually RUN | those with no failing test among them | test results in the run history |

**"Mart" is defined from the graph, not from a schema name.** A mart is an
object with at least one inbound lineage edge and no outbound one: the end of
the line, the thing the pipeline exists to deliver. A catalog whose reporting
layer lives in `analytics` or `rpt` or `core` has marts too, and one with a
`mart` schema full of intermediate models does not have five. The inbound
requirement keeps an isolated object out — nothing feeds it and it feeds
nothing, so it is not the end of a pipeline, and calling it an unpaved mart
would put a permanent red mark on every catalog with no lineage. District
membership (`objects[].schema`, what `districts[]` is keyed on) is read
alongside, but only to say in the note how many districts the marts are
scattered across.

**"Paved" is `joins[]`, not `edges[]`,** for the reason `semantic-roads.md`
gives: a join known only from SQL scanning is a dirt track, a relationship
DECLARED in OSI is the paved and marked street. So a mart is reachable by paved
road when at least one declared join runs to it.

### The honesty rule: unknown is its own state

The same law this page already states for `lots[]`'s temporal keys and for
`weather`: **unknown never renders as stale.** Here it reads —

*A catalog with no dbt manifest at all does not have 0% documentation
coverage. It has UNKNOWN coverage.* The artifact that would answer the question
was never read, and the models may be immaculately documented in a manifest
this export never got. `met: false, have: 0` would invent a failure out of an
absence and put a red gauge in front of someone with nothing to fix.

So the unknown state is emitted as `state: "unknown"` with `met`, `have` and
`need` all **`null`** and `short` empty. Two independent readings therefore
both refuse to mislead: a client switching on `state` meets the third case by
name, and a client that only looks at `met` gets `null` rather than a `false`
it would paint red. The `note` names the missing artifact.

A milestone is unknown in exactly two situations:

* **the evidence was never read** — no manifest joined onto this catalog, no
  freshness verdicts, no semantic model, no test results;
* **the universe is empty** — no marts on this map, no judged sources. A
  vacuously `met` milestone is the same lie in the opposite colour, so nothing
  to measure is unknown, not done.

**A catalog with nothing to measure gets all six unknown plus a note** —
`nothing measurable yet: this catalog supplied none of the artifacts these
milestones count, so every one of them is unknown rather than unmet`. That is
what the committed golden shows: `demo.duckdb` is a plain warehouse with no
dbt project behind it, so its whole block is unknown. A discouraging wall of
zeroes would misrepresent absence as failure and teach people to ignore the
gauge.

The block's own `note` otherwise reads `N of 6 milestones met`, plus how many
are unknown and why that is not the same as unmet.

## Deliberately omitted

| Not emitted | Why |
|---|---|
| `roads` | Derivable from the tile grid; a second copy of the same information |
| `district_of` | Derivable client-side from the district rects |
| `theme.style_rules` | Resolved into `lots[].zone_style`; clients must not re-match regexes |
| `lots[].density` | Presentation state — see above |
| Vehicles, tick state | Presentation; the client runs its own tick |
| Achievement badges, earned-at timestamps, a minted set | Achievements are stateless by decision: "true right now", recomputed every export. A persisted badge would put a clock in a byte-stable document and would stay lit after the artifact it counted was deleted |

## Changing the format

Any change to emitted keys, types, or ordering is a contract change. Bump
`version`, update this page, regenerate the golden with
`scripts/update_contract_golden.py`, and **review the diff** — that diff is the
contract change, and it is the only place an accidental one becomes visible
before a client breaks on it.
