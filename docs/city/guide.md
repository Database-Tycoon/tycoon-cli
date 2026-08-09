# Database Tycoon

A read-only view of a DuckDB catalog, rendered as a SimCity-style living city.
Schemas become districts, tables and views become buildings, **lineage becomes
the street network**, the database is the power plant, and row counts drive
building height. Failing tests set buildings on fire. It never writes to your
database.

The point is not the picture. An observation platform has to answer "is
anything wrong?" in zero clicks, and a city does that with peripheral vision:
you notice a fire, a fog bank or a street that goes nowhere before you have
read a single number. Every visual here restates a fact that was measured —
from your catalog, your dbt artifacts, and your run history — and anything that
could not be measured is drawn as **unknown**, never as fine and never as
stale.

MIT licensed. Local DuckDB catalogs, and a
[tycoon project](#pointing-it-at-your-own-catalog) if you have one.

## Trademarks

dbt is a trademark of dbt Labs, Inc. This project is independent and is not
affiliated with, sponsored by, or endorsed by dbt Labs. It reads the artifacts
dbt produces; the name is used only to say so.

---

## Look at it first

```bash
docker build -t tycoon-city .
docker run --rm -p 8000:8000 tycoon-city tycoon-city demo
```

Open <http://localhost:8000/?tour=1>. No Python, no install, nothing to
configure. (A bare `docker run --rm -p 8000:8000 tycoon-city` also works, but it
serves a plain baked `.duckdb` file — schemas, tables and lineage, and none of
the dbt artifacts the demo project carries.)

From a checkout, once the web bundle is built (`cd web && npm install && npm run
build`):

```bash
uv run tycoon-city demo          # → http://127.0.0.1:8000/?tour=1
```

`tycoon-city demo` generates a whole synthetic **tycoon project** into a temp
directory and serves it: a week of scheduled runs, a mart nobody has rebuilt in
21 days, a failing test, a build error, a source past its freshness SLA, a
schema that drifted on Tuesday, a `dbt build --fail-fast` cascade to replay, and
a declared semantic model. It is generated rather than shipped pre-built
because every one of those facts is a *time*: a baked demo would show you a
"fresh pipeline" that last ran whenever the release was cut. It takes about a
second, writes nothing outside `$TMPDIR`, and deletes itself on exit.

The wheel carries the compiled JavaScript, so there is nothing to build:

```bash
pip install database-tycoon-city
tycoon-city demo                 # → http://127.0.0.1:8000/?tour=1
```

A checkout still needs `cd web && npm install && npm run build` once, because
from a checkout the server prefers `web/dist` over the packaged copy — that is
what lets you edit the front end and reload. `--dist` (or
`$DATABASE_TYCOON_WEB_DIST`) overrides both.

If you already use the Tycoon CLI, the city installs as an optional extra
instead:

```bash
pip install "database-tycoon[city]"
cd my-tycoon-project && tycoon city
```

## Pointing it at your own catalog

```bash
uv sync
cd web && npm install && npm run build && cd ..
uv run tycoon-city path/to/db.duckdb        # → http://127.0.0.1:8000
```

`path/to/db.duckdb` can be a plain DuckDB file or a **tycoon project
directory** — one holding a `tycoon.yml`, a dbt `target/manifest.json`, and a
`.tycoon/metadata.duckdb` of run history. A plain file gives you the catalog,
lineage traced out of view SQL, and row counts. A project adds everything that
needs artifacts: dbt descriptions, tests, source-freshness verdicts, run
replay, the compute budget, usage, and achievements. Anything missing is
**named** in the footer's notes popover rather than silently dropped.

To mount your own catalog into the container:

```bash
docker run --rm -p 8000:8000 \
  -v /path/to/my.duckdb:/data/catalog.duckdb:ro \
  -e DATABASE_TYCOON_DB=/data/catalog.duckdb \
  tycoon-city
```

| Route | Returns |
|---|---|
| `/` | the interactive 3D city (the built web app) |
| `/city.json` | the contract document, exported fresh per request |
| `/meta.json` | when that document was produced — `null` here, deliberately (see [freshness](#freshness-and-metajson)) |
| `/runs.json`, `/runs/<id>.json` | the replayable runs, and one run step by step |
| `/spritesheet.png` | the active theme's sprite atlas |
| `/healthz` | JSON catalog counts — 503 if the database cannot be read |

The catalog is re-read whenever a file behind it moves, so editing the database
and pressing `R` in the app shows the change; an unchanged database is served
from the parsed copy rather than rebuilt per request.

Outside Docker the server binds `127.0.0.1`. A city names real schemas, tables
and columns, so publishing one on every interface is a decision you make:
`--host 0.0.0.0`, or `DATABASE_TYCOON_HOST`. The container image sets that itself,
because a published port cannot reach a loopback socket.

`/healthz` deliberately reads the catalog rather than just answering the socket,
because a bad volume mount produces a server that is up but cannot see any data,
and that should not report healthy.

## Reading the map

The map uses the database's own vocabulary, not game terms:

- **Roads are lineage and streets.** Streets run inside each schema's area so
  every table and view is reachable. Between areas, a road exists because a
  dependency exists — the road grid is not decoration.
- **Placement is graph-driven, in columns.** An object's **column** is its
  lineage depth, west to east, so sources sit on the left and the things built
  from them sit downstream of them. Within a column, buildings are ordered to
  keep their edges short, then grouped into **schema bands** — same-schema
  neighbours sit tight, a new band leaves an unmistakable gap — and inside a
  band, objects cut from the same sources cluster together, with exact
  siblings (identical source sets) touching as one block. A long edge that
  skips columns is threaded through a reserved pass-through slot rather than
  cutting across the map.
- **Districts are labelled schemas.** A district is the bounding rect around
  one schema's connected buildings, tinted on the ground with a chip carrying
  the schema name. Districts stay 1:1 with schemas — that is load-bearing for
  every district-keyed feature (weather cells, labels, achievements), which is
  why a schema spread across depths gets a wide district rather than being
  split into two.
- **Buildings grow with row count, on an absolute log scale.** Each density
  level is one decade of rows (level 5 ≈ 10k, level 7 ≈ 1M), so a building's
  height means the same thing in every catalog — and a warehouse of tiny
  tables is honestly short. The top decile of *this* catalog's row counts gets
  a 2×2 ground plan; a one-tile skyscraper beside a one-tile road read wrong.
- **The database powers the map.** The database is the plant, and yellow
  arterials radiate from it to every schema area. A dimmed building takes no
  part in lineage at all: nothing feeds it and it feeds nothing.
- **Schema areas sit at their lineage depth.** Source schemas cluster near the
  plant; each downstream layer sits further out, so data flows outward.
- **Roads end in something, never in a stub.** A street that stops at a
  building ends in an apron or a loading dock; one that stops in the open ends
  in a plaza. The rule is deliberate ([`docs/road-grammar.md`](road-grammar.md)):
  raw stubs are the single strongest tell that a network is a diagram rather
  than a place.
- **Open grass surrounds the city.** The map fills the viewport whatever size
  the catalog is; ground past the edge of the city is unbuilt land, not a
  boundary.

Then the things that are *wrong*, which is what you are actually looking for:

- **A building on fire has a failing test.** Amber markers are warnings, green
  is tested-and-passing, and no marker at all means never tested — which is not
  the same as passing and is not drawn as if it were. The **firehouse** on the
  civic strip lists the active fires.
- **A worn, boarded-up building missed its freshness SLA** — dbt's own
  `sources.json` verdict, not our judgement. The amber contractor van answering
  it is a dispatch, never a repair anyone has made.
- **A crane over a roof means the object's shape moved recently**: columns came
  or went since the last schema snapshot.
- **Fog over a district means a late source feeds it.** The fog sits on the
  districts *downstream* of the late source, walked over measured edges, not on
  the source's own district — the problem is upstream, the consequence is
  where you are looking.
- **The public library is your documentation inventory** — shelves are counts
  of real described columns and tested objects, so an under-documented city is
  visibly under-built.

Hover a building for a tooltip (`object — N rows`); the legend in the
bottom-right names every one of these, and names the ones your catalog could
not report as absences rather than omitting the row.

## What the city knows

Everything below is measured, and everything below has a named absence.

**Run replay.** "Replay a run" steps through one specific dbt invocation:
buildings grow as they build, failures ignite in the order they failed, and the
downstream models dbt reported as *skipped* dim behind them. The cascade is a
join of three measured facts — dbt said `skipped`, the node is reachable from
the failure over measured lineage, and it came later — computed once in Python
and replayed, never re-derived in the client. A model dbt built successfully
downstream of a failure stays lit, because the record relays dbt's verdict and
never infers a blast radius. Step order is reconstructed from durations
(`dbt_nodes` records no per-node start time) and the panel says so.

**Weather, from source freshness.** One cell per district a *judged* source
reaches. `clear` is a positive assertion — judged sources reach this district
and none is late. A district with no cell has no judged source upstream, and a
catalog where nothing was judged emits no cells at all plus a note saying why:
all-clear would be clear-because-unknown wearing clear-because-fine. `W`.

**The compute budget.** Measured build load (cadence × mean build cost per
object) at a **declared** rate, so the price carries its provenance. Local
DuckDB is free, and `$0` there is a fact — but `$0` because nothing could be
priced is a different fact and comes through as null, with a count of the
objects the bill left out. A `pricing.toml` beside the catalog, or `--pricing`,
declares a rate for engines that charge.

**The usage overlay** (`U`). How hard each building is worked, from measured
run appearances: a beacon whose height is cadence relative to this city's
busiest object, a lid on the ones that are measured but barely used, and a ring
on the ones seen too few times to have a cadence at all. **Unmeasured is not
unused** — an object the run history says nothing about gets no marker and is
counted out loud in the legend, because "nobody uses this" is a deprecation
signal somebody would act on.

**Declared semantics and joins (OSI).** Point the loader at an [Apache
Ossie](semantic-roads.md)-style `semantic.yml` and objects gain their
business names, keys, synonyms and instructions, and the model's declared joins
arrive in their own `joins[]` array. They are kept separate from `edges[]` on
purpose: an edge asserts *data moved here at build time*, a join asserts *these
two are formally joinable* — true whether or not a build ever ran between them,
which is the ordinary case for a dimension every query joins and no build
reads. The inspector marks them solid (declared) and dashed (inferred) so one
can never wear the other's provenance. Rendering joins as streets is Phase 3;
today they are inspector-level.

**Achievements are coverage milestones**, counted from real artifacts — six of
them, including "every building has a plaque", "every mart reachable by paved
road" and "old town fully signed" — and they are
**stateless**: true right now, computed from this document, never minted and
never persisted. An achievement that stayed lit after you deleted the
documentation would be a trophy, not a measurement. A catalog with no manifest
reports `unknown` coverage with its terms null, not 0%.

**The road-load overlay** (`T`) paints expected warehouse-seconds/day on each
street, accumulated per tile, so a shared trunk glows with everything it
carries.

## Role lenses and the tour

The same city, re-weighted for the job you do: **data engineer**, **analytics
engineer**, **on-call responder**, **data lead**. A browser that has never
chosen gets a one-time picker; after that the footer has a switcher, and
`?lens=on-call` shares a view without rewriting the recipient's preference.

**A lens re-weights presentation and never changes arithmetic.** It reorders
health chips, reorders the triage list, decides which coverage gauges lead,
which overlays start on and which panel opens — and nothing else. Every count
is identical under every lens, and an end-to-end test asserts exactly that,
byte for byte, because "lens" drifting into "invented score" is the failure
this project forbids everywhere else. A chip a lens does not name still
renders, after the ones it does.

`?tour=1` walks the city stop by stop, in the order that lens would want, and
only through stops your catalog can actually support — no fires here means the
tour says what a quiet city looks like rather than inventing one.

## The HUD

The health strip under the header answers "is anything wrong?" before any
interaction: `● 2 tests failing · ▲ 1 source late · ✕ 1 build error`. Every
number is a door — click it and the camera flies to the offender and selects it.

| Key | |
|---|---|
| `/` | search objects, tags, owners, districts |
| `P` | problems panel — triage list, worst first, with the coverage gauges |
| `T` `W` `U` | road-load / weather / usage overlays |
| `space` `←` `0` `esc` | run replay: step, back, restart, exit |
| `R` | re-read the catalog in place (camera and selection survive) |
| `F` `H` | fly camera / home framing |
| click, drag, wheel | inspect, orbit, zoom |

`?` in the footer holds the full keymap; `ⓘ notes` holds the degradation notes,
because a named absence deserves better than an ellipsis in a status line.

## Export for a static host

The city can be written out as data, with no renderer attached:

```bash
uv run tycoon-city-export path/to/db.duckdb out/
```

That writes `out/city.json`, `out/meta.json`, `out/runs.json`, `out/runs/*.json`
and the spritesheet the document names — a self-contained directory a static
host can serve as-is, at the same paths the server routes, so a client written
against the live server works unchanged against the copy. The format is
documented in [`docs/city-json-v1.md`](city-json-v1.md); it is byte-stable,
so the same catalog always produces the same bytes, and needs no display to
produce.

### Freshness and `meta.json`

The footer's age used to be measured from the moment your browser fetched
`city.json`. That is exactly right for the live server, which builds the
document for the request that asked for it — and exactly wrong for a static
export, where a week-old file on a CDN read "as of 3s ago".

`city.json` cannot carry the fix: it is byte-stable by law, no timestamp, no
uuid, no path, which is what makes a committed golden and a cross-language
contract test possible. So the export time rides in a **sibling** document, the
way `runs.json` does. `tycoon-city-export` writes `meta.json` with a
`generated_at`, and the footer reads **"exported 6 days ago"**. The live server
answers the same route with `generated_at: null` — it has no export time to
give — and the footer falls back to **"as of 12s ago"**, which is the age of
your own fetch and says so on hover. An older export with no `meta.json` at all
lands on the same honest fallback. The verb is the load-bearing part: you can
always tell whose claim you are being shown.

## Theming

A theme is one folder (`themes/<name>/` with `spritesheet.png` + `theme.toml`),
selected with `--theme`. Regenerate the default spritesheet with:

```bash
uv run --group art python scripts/make_default_theme.py
```

`pygame-ce` is in the `art` group and nowhere else on purpose: the shipped
package has to import and serve with no SDL anywhere, and a test makes pygame
genuinely unimportable to prove it.

## What this does not do

- **It never writes to your database.** Every connection is read-only, and
  there are no player verbs: you observe a catalog, you do not edit one.
- **Local DuckDB only, for now.** The wording is engine-neutral and the
  `usage.source` discriminator already exists for engines with a real query
  log, but MotherDuck (`md:`) is untested and Snowflake is not implemented.
- **Lineage is as good as your artifacts.** With a dbt manifest it is declared;
  without one it is parsed out of view SQL with sqlglot, which cannot see
  through a table built by an external process. Column-level lineage covers
  what it can parse and the notes count what it could not.
- **Streets are mid-rewrite.** What ships by default is the v4 planner:
  lineage-driven layout in depth columns, schema bands, and POWER_LINE
  arterials. The v5 planner — schema-clustered neighbourhoods on a lattice
  that satisfies the junction-spacing rule by construction — is available
  behind `DATABASE_TYCOON_PLANNER=v5` and is not yet the default. The next
  geometry phase is planned behind a spike gauntlet: every geometry change
  gets rendered and looked at before a test is written for it, because four
  spec-first attempts at this were wrong.
- **District labels can stack** when two bands sit adjacent, and far-view
  contrast on residential zones is low.
- **Simulated content stays flagged.** Anything not restating a measured fact
  is off by default and labelled when on (`?ambient=1`, `?guests=1`).

## Develop

```bash
uv run pytest
uv run ruff format . && uv run ruff check .
```

Web checks (types, the production build, then the Playwright suite):

```bash
cd web && npx tsc --noEmit && npm run build
cd web && npm run demo-data && npm run e2e
```

`npm run demo-data` exports the committed `demo.duckdb` into `web/public/`,
which is what the dev server (`npm run dev`, port 5173) and the e2e suite read.
Playwright needs Google Chrome installed and downloads no browser. Set
`DATABASE_TYCOON_WEB_PORT` when running two checkouts at once — a screenshot of the wrong
checkout looks fine and lies.

## Licence

MIT — see [`LICENSE`](LICENSE). Copyright (c) 2026 Stephen Sciortino.

Bundled third-party runtime dependencies (three.js, zod, duckdb, sqlglot,
PyYAML) are all MIT; their notices and the recipe for re-verifying them are in
[`THIRD-PARTY.md`](https://github.com/Database-Tycoon/tycoon-cli/blob/main/THIRD-PARTY.md).
