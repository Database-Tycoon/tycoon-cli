# Roadmap

_Last updated 2026-11-18, at the end of the v0.2.5 cycle. This page is the north
star for tycoon: the direction we are building toward, reviewed at each sprint
retro. The [wish list](#wish-list) at the end collects ideas we like but have
not committed to. Items move from the wish list onto the roadmap, never
silently the other way. Every item links to its GitHub issue or pull request;
the milestones on GitHub are the schedule of record._

## Who tycoon is for

The dlt user. You already think in dlt pipelines, or you are one
`tycoon init` away from starting to. tycoon gives that person a complete local
analytics stack (ingestion, DuckDB, dbt, dashboards, and a catalog you can walk
through) with one `pip install` and no accounts, no Docker, no cloud bill.

Two supported ways in:

1. Catalog sources. `tycoon data sources add` installs and configures a
   source from the built-in catalog, which today holds eight entries: GitHub,
   Slack, Stripe, HubSpot, Notion, Google Sheets, REST API and local files
   (`src/tycoon/ingestion/catalog.py`). Opening the catalog up to the rest of
   dlt's verified sources is the JSON manifest work in [#84].
2. Bring your own dlt project. `tycoon.yml` has accepted a `runtimes:` block
   since 0.1.11, but nothing runs it yet ([#343]). Running, observing and
   registering an existing dlt project ([#75]) is scheduled for v0.3.1.

## What we are not building

- Other query engines, for now. DuckDB is the engine. A Snowflake backend is
  possible future scope, not something we are building.
- Vendor ingestion runtimes. No Airbyte or Fivetran execution inside tycoon.
  Read-only observability of those vendors is on the roadmap under
  [Later](#later); running them is not.
- A hosted product. tycoon is local-first. The one cloud target we are
  building is MotherDuck, because it is DuckDB.

## Now: v0.2.6

The cycle after v0.2.5. This section names the themes; the
[v0.2.6 milestone](https://github.com/Database-Tycoon/tycoon-cli/milestone/19)
is the current list of issues.

- Rewrite foundation. Move the remaining commands off the config singleton
  ([#175]) and enforce `schema_version` in every command module ([#189]).
  These moved from v0.2.5, where no work had started on them.
- MotherDuck Phase 1 ([#429]). A Destination protocol and a MotherDuck
  destination ([#110], [#118]), so the commands that read a warehouse stop
  assuming a local file. Also moved from v0.2.5.
- MotherDuck fixes. `tycoon city` can't yet render a project whose warehouse
  is on MotherDuck ([#511]). Five token checks disagree ([#491]), which lets
  `data transform` open a browser sign-in ([#492]) and `doctor` report a
  working sign-in when only a cached file exists ([#490]).
- Follow-ups from the v0.2.5 reviews ([#494], [#523], [#524]) and the city's
  opening camera ([#386]).

## Next: v0.3.0 and v0.3.1

Both are due in the first quarter of 2027; the GitHub milestones carry the
exact dates. Until v0.3.0, releases continue on the two-week v0.2.x cycle,
and each one carries one step of the MotherDuck work, in this order:

1. The Destination protocol and a MotherDuck destination ([#110], [#118]),
   in v0.2.6.
2. The legacy run-history capture goes through the metadata backend
   ([#434]), in v0.2.7.
3. Run history in MotherDuck, opt in ([#120], [#129]), in v0.2.8.
4. Scaffolding for new MotherDuck projects ([#128]) and a recipe for the
   local-to-MotherDuck path ([#431]), in v0.2.9.

A step ships in its release even if bug fixes have to wait for the next
one. v0.2.10 leaves room for a step that slips. There is no release over
the last two weeks of 2026.

- v0.3.0: full support for running tycoon on MotherDuck. This is where the
  MotherDuck work in the v0.2.x releases comes together: raw loads and
  `motherduck:` targets in v0.2.4 and v0.2.5, then the four steps above.
  It is done when this path passes against a real MotherDuck database in
  the token-gated e2e job ([#437]): `tycoon init` choosing MotherDuck,
  `tycoon data sources add rest_api`, `tycoon data sources run`, the rows
  landing in the `md:` catalog, and `tycoon data status` and
  `tycoon data history` reading from that same catalog.
- v0.3.1: one run path, and bring your own dlt project. The Runtime
  protocol and `DltManagedRuntime` replace `runner.py` ([#85], with [#109],
  [#111], [#112], [#113], [#115], [#116]), which is what lets tycoon run an
  existing dlt project ([#343], [#75], [#117], [#121]), with a check that a
  dlt-project runtime names its path ([#176]). The source catalog gets a
  JSON manifest and loader ([#98], [#100]), and the catalog factory drives
  `sources add` from it ([#102] through [#108]).

The MotherDuck phases are laid out in
[`docs/proposals/motherduck-support.md`](https://github.com/Database-Tycoon/tycoon-cli/blob/main/docs/proposals/motherduck-support.md),
a contributor page that is not published on this site.

## AI and agents

tycoon's bet is to be the stack agents stand on, not another agent.

- Legible by design. The agent skills ship as three Claude Code plugins, one
  per audience ([#307], in 0.2.3), a root `CLAUDE.md` points coding agents at
  the contributor rules (in 0.2.2), run history and pipeline metadata are
  ordinary queryable tables ([observability reference](reference/observability.md)),
  and every operation has a plain CLI contract an agent can drive and verify.
- No required model. tycoon never needs an API key to do its job. The `ask`
  layer was removed in 0.1.10 rather than half-maintained. If natural-language
  conveniences return, they will run against an optional, user-configured
  OpenAI-compatible endpoint, and everything must keep working without one.
  Open ideas: a lighter LLM backend ([#202]), AI-driven fix offers on command
  failure ([#203]), and typed decisions via Jev in scaffolding ([#291]) and
  run triage ([#325]). These are proposals, not commitments.
- MCP. The open scope is helping users install the dbt and dlt MCP servers
  into their project ([#142], [#143]). Query-level MCP already exists in
  DuckDB and MotherDuck; tycoon only builds what those do not cover. No
  tycoon MCP server of its own is on the roadmap today.

## Later

Tracked, not scheduled to a milestone.

- DuckLake. A DuckLake destination ([#122]), native layered storage with a
  SQLite catalog ([#73], proposal in PR [#74]), DuckLake health checks in
  `doctor` ([#144]), and dlt load history for DuckLake targets ([#344]).
  `ducklake_config.py`, which only wrote Parquet and had no callers, is
  deleted in v0.2.5 ([#448]).
- Object storage as a destination ([#124]) and a local-to-cloud push, since
  `data sync` is one-way today ([#77]).
- Alternative ingestion modes ([#88]): a Fivetran runtime and sources panel,
  observability only ([#130], [#131], [#132], [#135]), and Airbyte and
  Estuary skeletons ([#133], [#134], [#80]).
- The city renderer as the default way you look at your warehouse, with the
  CLI and the city as two views of the same catalog. The layer-aware commands
  in [#306] read the same data the city draws, and the city guide moves into
  the published docs ([#425]).
- Docs and site. A product site separate from the consultancy site ([#412]),
  a changelog feed ([#413]), a writing reference for changelog entries
  ([#414]), links to the docs site from the places that should carry them
  ([#419]), and link previews ([#420]).
- Dependencies. A minor release for DuckDB 2.0 when it ships ([#43]); dbt
  Core v2 when `dbt-duckdb` and the pin allow it ([#58], [#347]).
- Community. GitHub Discussions and good-first-issue triage ([#54]).

## Wish list

Reviewed at retros; not scheduled, not promised.

- DuckLake as the opinionated scaffold default: hand tycoon an empty bucket
  and it structures everything ([#350]).
- Nudge dbt projects toward the semantic layer in the same environment
  ([#427]).
- Filesystem sources that expose what dlt supports: per-resource naming,
  more formats, more options ([#221]).
- Redesign `tycoon init` around a required dbt or dlt project ([#14]).
- Rendering the city as a MotherDuck flight or dive (no issue yet).
- Dashboards over tycoon's own run metadata (no issue yet).
- pandas as an optional extra ([#148]).
- Align the PyPI, docs and CLI naming ([#140]).

## Shipped

The last three releases, with their release notes.

- [v0.2.5](releases/v0.2.5.md), 2026-11-20: MotherDuck as a load target and
  the layer-aware data CLI. `data sources run`, `run-all` and `data run-all`
  load into a MotherDuck raw database, with a `motherduck` extra ([#447],
  [#459]), and `data query`, `data schema`, `data sync` and `tycoon city`
  stop with an error on an `md:` or `motherduck:` target with no token,
  instead of opening a browser ([#460]). `tycoon fire`, `data layers` and
  `data sources explore` arrive ([#306]), `data query` gets output formats
  ([#391]) and `data schema` can show one schema ([#393]). Projects stop
  sharing dlt state, so same-named sources no longer load duplicates
  ([#394]). Secret files can't be committed by accident ([#410]), and the
  publish workflow refuses a tag that isn't on `main` ([#473]).
- [v0.2.4](releases/v0.2.4.md), 2026-11-07: safer MotherDuck queries and
  reliable dbt run history. `data query` refuses writes on MotherDuck unless
  you pass `--allow-writes` ([#309]), `data schema` estimates MotherDuck row
  counts ([#310]), and tycoon recognises both `md:` and `motherduck:` ([#308]).
  Run history stops marking no-op builds failed, records failed runs and
  `run-all` builds, and `data status` finds each layer's last build ([#341],
  [#377], [#326], [#390]). City labels stop overlapping ([#385]), and staging
  models name the dbt sources that live outside the warehouse ([#387]).
- [v0.2.3](releases/v0.2.3.md), 2026-10-24: the documentation site publishes
  to GitHub Pages, with internal pages withheld by a check that fails the
  build ([#348], PR [#415]). The city renderer is tested and gated in CI
  (PRs [#248], [#249], [#256]) and its vehicles and guests drive (PR
  [#250]). Agent skills install as Claude Code plugins ([#307]). The
  MotherDuck roadmap is agreed ([#429]).

[#14]: https://github.com/Database-Tycoon/tycoon-cli/issues/14
[#43]: https://github.com/Database-Tycoon/tycoon-cli/issues/43
[#54]: https://github.com/Database-Tycoon/tycoon-cli/issues/54
[#58]: https://github.com/Database-Tycoon/tycoon-cli/issues/58
[#73]: https://github.com/Database-Tycoon/tycoon-cli/issues/73
[#74]: https://github.com/Database-Tycoon/tycoon-cli/pull/74
[#75]: https://github.com/Database-Tycoon/tycoon-cli/issues/75
[#77]: https://github.com/Database-Tycoon/tycoon-cli/issues/77
[#80]: https://github.com/Database-Tycoon/tycoon-cli/issues/80
[#84]: https://github.com/Database-Tycoon/tycoon-cli/issues/84
[#85]: https://github.com/Database-Tycoon/tycoon-cli/issues/85
[#88]: https://github.com/Database-Tycoon/tycoon-cli/issues/88
[#98]: https://github.com/Database-Tycoon/tycoon-cli/issues/98
[#100]: https://github.com/Database-Tycoon/tycoon-cli/issues/100
[#102]: https://github.com/Database-Tycoon/tycoon-cli/issues/102
[#108]: https://github.com/Database-Tycoon/tycoon-cli/issues/108
[#109]: https://github.com/Database-Tycoon/tycoon-cli/issues/109
[#110]: https://github.com/Database-Tycoon/tycoon-cli/issues/110
[#111]: https://github.com/Database-Tycoon/tycoon-cli/issues/111
[#112]: https://github.com/Database-Tycoon/tycoon-cli/issues/112
[#113]: https://github.com/Database-Tycoon/tycoon-cli/issues/113
[#115]: https://github.com/Database-Tycoon/tycoon-cli/issues/115
[#116]: https://github.com/Database-Tycoon/tycoon-cli/issues/116
[#117]: https://github.com/Database-Tycoon/tycoon-cli/issues/117
[#118]: https://github.com/Database-Tycoon/tycoon-cli/issues/118
[#120]: https://github.com/Database-Tycoon/tycoon-cli/issues/120
[#121]: https://github.com/Database-Tycoon/tycoon-cli/issues/121
[#122]: https://github.com/Database-Tycoon/tycoon-cli/issues/122
[#124]: https://github.com/Database-Tycoon/tycoon-cli/issues/124
[#128]: https://github.com/Database-Tycoon/tycoon-cli/issues/128
[#129]: https://github.com/Database-Tycoon/tycoon-cli/issues/129
[#130]: https://github.com/Database-Tycoon/tycoon-cli/issues/130
[#131]: https://github.com/Database-Tycoon/tycoon-cli/issues/131
[#132]: https://github.com/Database-Tycoon/tycoon-cli/issues/132
[#133]: https://github.com/Database-Tycoon/tycoon-cli/issues/133
[#134]: https://github.com/Database-Tycoon/tycoon-cli/issues/134
[#135]: https://github.com/Database-Tycoon/tycoon-cli/issues/135
[#140]: https://github.com/Database-Tycoon/tycoon-cli/issues/140
[#142]: https://github.com/Database-Tycoon/tycoon-cli/issues/142
[#143]: https://github.com/Database-Tycoon/tycoon-cli/issues/143
[#144]: https://github.com/Database-Tycoon/tycoon-cli/issues/144
[#148]: https://github.com/Database-Tycoon/tycoon-cli/issues/148
[#175]: https://github.com/Database-Tycoon/tycoon-cli/issues/175
[#176]: https://github.com/Database-Tycoon/tycoon-cli/issues/176
[#189]: https://github.com/Database-Tycoon/tycoon-cli/issues/189
[#202]: https://github.com/Database-Tycoon/tycoon-cli/issues/202
[#203]: https://github.com/Database-Tycoon/tycoon-cli/issues/203
[#221]: https://github.com/Database-Tycoon/tycoon-cli/issues/221
[#248]: https://github.com/Database-Tycoon/tycoon-cli/pull/248
[#249]: https://github.com/Database-Tycoon/tycoon-cli/pull/249
[#250]: https://github.com/Database-Tycoon/tycoon-cli/pull/250
[#256]: https://github.com/Database-Tycoon/tycoon-cli/pull/256
[#291]: https://github.com/Database-Tycoon/tycoon-cli/issues/291
[#306]: https://github.com/Database-Tycoon/tycoon-cli/issues/306
[#307]: https://github.com/Database-Tycoon/tycoon-cli/issues/307
[#308]: https://github.com/Database-Tycoon/tycoon-cli/issues/308
[#309]: https://github.com/Database-Tycoon/tycoon-cli/issues/309
[#310]: https://github.com/Database-Tycoon/tycoon-cli/issues/310
[#325]: https://github.com/Database-Tycoon/tycoon-cli/issues/325
[#326]: https://github.com/Database-Tycoon/tycoon-cli/issues/326
[#341]: https://github.com/Database-Tycoon/tycoon-cli/issues/341
[#343]: https://github.com/Database-Tycoon/tycoon-cli/issues/343
[#344]: https://github.com/Database-Tycoon/tycoon-cli/issues/344
[#347]: https://github.com/Database-Tycoon/tycoon-cli/issues/347
[#348]: https://github.com/Database-Tycoon/tycoon-cli/issues/348
[#350]: https://github.com/Database-Tycoon/tycoon-cli/issues/350
[#377]: https://github.com/Database-Tycoon/tycoon-cli/issues/377
[#385]: https://github.com/Database-Tycoon/tycoon-cli/issues/385
[#386]: https://github.com/Database-Tycoon/tycoon-cli/issues/386
[#387]: https://github.com/Database-Tycoon/tycoon-cli/issues/387
[#390]: https://github.com/Database-Tycoon/tycoon-cli/issues/390
[#391]: https://github.com/Database-Tycoon/tycoon-cli/issues/391
[#393]: https://github.com/Database-Tycoon/tycoon-cli/issues/393
[#394]: https://github.com/Database-Tycoon/tycoon-cli/issues/394
[#410]: https://github.com/Database-Tycoon/tycoon-cli/issues/410
[#412]: https://github.com/Database-Tycoon/tycoon-cli/issues/412
[#413]: https://github.com/Database-Tycoon/tycoon-cli/issues/413
[#414]: https://github.com/Database-Tycoon/tycoon-cli/issues/414
[#415]: https://github.com/Database-Tycoon/tycoon-cli/pull/415
[#419]: https://github.com/Database-Tycoon/tycoon-cli/issues/419
[#420]: https://github.com/Database-Tycoon/tycoon-cli/issues/420
[#425]: https://github.com/Database-Tycoon/tycoon-cli/issues/425
[#427]: https://github.com/Database-Tycoon/tycoon-cli/issues/427
[#429]: https://github.com/Database-Tycoon/tycoon-cli/issues/429
[#431]: https://github.com/Database-Tycoon/tycoon-cli/issues/431
[#434]: https://github.com/Database-Tycoon/tycoon-cli/issues/434
[#437]: https://github.com/Database-Tycoon/tycoon-cli/issues/437
[#447]: https://github.com/Database-Tycoon/tycoon-cli/issues/447
[#448]: https://github.com/Database-Tycoon/tycoon-cli/issues/448
[#459]: https://github.com/Database-Tycoon/tycoon-cli/issues/459
[#460]: https://github.com/Database-Tycoon/tycoon-cli/issues/460
[#473]: https://github.com/Database-Tycoon/tycoon-cli/issues/473
[#490]: https://github.com/Database-Tycoon/tycoon-cli/issues/490
[#491]: https://github.com/Database-Tycoon/tycoon-cli/issues/491
[#492]: https://github.com/Database-Tycoon/tycoon-cli/issues/492
[#494]: https://github.com/Database-Tycoon/tycoon-cli/issues/494
[#511]: https://github.com/Database-Tycoon/tycoon-cli/issues/511
[#523]: https://github.com/Database-Tycoon/tycoon-cli/issues/523
[#524]: https://github.com/Database-Tycoon/tycoon-cli/issues/524
