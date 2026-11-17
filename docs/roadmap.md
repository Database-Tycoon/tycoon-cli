# Roadmap

_Last updated 2026-11-16, during the v0.2.5 cycle. This page is the north
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

## Now: v0.2.5

Sprint 2026-11-07 to 2026-11-20. The milestone's scope is the rewrite
foundation (config singleton, catalog manifest) and the layer-aware data CLI,
with MotherDuck Phase 1 alongside. The fixes still open at the end of v0.2.4
moved into this cycle, and most of what has merged so far comes from them.

- Rewrite foundation. No pull requests yet for the remaining config singleton
  uses ([#175], [#176], [#189]) or the source catalog's JSON manifest and
  loader ([#98], [#100], design in [#197]).
- Layer-aware data CLI ([#306]). PRs [#288] and [#289] are open, awaiting
  re-review.
- MotherDuck ([#429]). Merged: raw ingestion builds a MotherDuck dlt
  destination and skips the post-load steps that need a local raw file
  ([#447], [#448], PRs [#477], [#478], part of [#430]), with a `motherduck`
  extra for pyarrow ([#459], PR [#485]). The city renderer and `data sync`
  accept `motherduck:` ([#446], PR [#479]), OSI scaffolding reads a MotherDuck
  warehouse ([#298], PR [#450]), and an `md:` target with no token fails
  instead of opening a browser ([#460], PRs [#481], [#482]). Still open:
  [#430] itself, the token-gated e2e job ([#437], whose workflow merged in
  the v0.2.4 cycle in PR [#449]), `data sync` and `tycoon city` printing a
  token that is in the connection string ([#510]), and Phase 1, the
  Destination protocol and a MotherDuck destination ([#110], [#118]), which
  has no pull request yet.
- Data integrity. Merged: `duckdb` is pinned to 1.5.4, which fixes
  QUALIFY-over-cast models ([#339], PR [#484]); dlt trace capture follows the
  pipeline's working directory and projects get their own pipeline
  directories ([#394], PRs [#398], [#399]); an invalid `tycoon.yml` no longer
  crashes the CLI ([#378], PR [#467]). Still open: running each project's
  pipelines in its own working directory (PR [#400]), and a Google Sheets
  source that forces a browser sign-in, so headless runs fail ([#349]).
- dbt and time. Open, with no pull requests yet: `data transform freshness`
  ([#340]), a looser `dbt-core` pin ([#347]), and consistent local time in
  status, history and the city ([#322], [#327]).
- The city. Merged: the legend hides while the detail panel is open ([#382],
  PR [#401]), long names wrap ([#383], PR [#402]), HUD panels stay inside the
  window ([#384], PR [#403]), views say their rows are not counted ([#388],
  PR [#404]), and the two object counts are labelled ([#389], PR [#405]).
  Still open: the opening camera ([#386]), off-map dbt sources in the
  inspector's upstream list (PR [#409], a follow-up to [#387]), and a mental
  model of the map in the docs ([#323], PR [#331]).
- CLI. Merged: `tycoon init` creates a new dbt project inline ([#259], PR
  [#260]), and the Jira sync workflow and `PTC-` title scopes are gone
  ([#351], PR [#463]). Still open: output formats for `data query` and
  filters for `data schema` ([#391], [#393], PR [#395]), `doctor` telling a
  working `.venv` apart from a broken one ([#392], PR [#396]), local secret
  files kept out of commits ([#410], PR [#466]), and literal RST backticks in
  help text ([#443], PR [#512]).
- CI and release safety. Merged: the publish workflow refuses a tag that
  isn't on `main` ([#473], PR [#474]), CODEOWNERS covers CI, dependency and
  release files ([#497], PR [#501]), workflows stop persisting checkout
  credentials ([#498], PR [#502]), CI installs from lockfiles only ([#499],
  PR [#506]) and runs workflow and dependency security checks ([#500], PR
  [#503]), and uv's required version is pinned ([#493], PR [#505]).
- Docs and dependencies. Merged: the contributing guide says closing keywords
  don't fire on release-branch merges ([#487], PR [#488]). Still open: this
  page ([#219], PR [#218]), a section structure for release pages ([#469]),
  and a migration assessment for DuckDB 2.0 LTS ([#465]).

## Next: v0.3.0 and v0.3.1

Two-week cycles, each with a GitHub milestone.

- v0.3.0, to 2026-12-04: one run path for dlt users. The Runtime protocol
  and `DltManagedRuntime` replace `runner.py` ([#85]: [#109], [#111],
  [#112], [#113], [#115], [#116]). MotherDuck Phase 2 puts run history in
  MotherDuck, opt in ([#120], [#129]), with the legacy capture path routed
  through the metadata backend first ([#434]).
- v0.3.1, to 2026-12-18: bring your own dlt project ([#343], [#75], [#117],
  [#121]) and the catalog factory that drives `sources add` from the
  manifest ([#102] through [#108]). MotherDuck Phase 3 finishes the
  scaffolding and adds a recipe ([#128], [#431]).

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
  deleted in v0.2.5 ([#72]).
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
- [v0.2.2](releases/v0.2.2.md), 2026-10-09: every project gets its own
  uv-managed `.venv`, and source code and dependencies live inside the
  project ([#261], [#262], [#263], [#264]). `--no-prompt` installs what it
  registers ([#272]). A load that finds nothing leaves the table alone, and
  `--fail-on-empty` stops a zero-row run ([#240]). `data query`, `data
  schema` and `data clean` work against an `md:` warehouse ([#70]). Saving
  `tycoon.yml` keeps your comments ([#177]).

[#14]: https://github.com/Database-Tycoon/tycoon-cli/issues/14
[#43]: https://github.com/Database-Tycoon/tycoon-cli/issues/43
[#54]: https://github.com/Database-Tycoon/tycoon-cli/issues/54
[#58]: https://github.com/Database-Tycoon/tycoon-cli/issues/58
[#70]: https://github.com/Database-Tycoon/tycoon-cli/issues/70
[#72]: https://github.com/Database-Tycoon/tycoon-cli/issues/72
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
[#177]: https://github.com/Database-Tycoon/tycoon-cli/issues/177
[#189]: https://github.com/Database-Tycoon/tycoon-cli/issues/189
[#197]: https://github.com/Database-Tycoon/tycoon-cli/issues/197
[#202]: https://github.com/Database-Tycoon/tycoon-cli/issues/202
[#203]: https://github.com/Database-Tycoon/tycoon-cli/issues/203
[#218]: https://github.com/Database-Tycoon/tycoon-cli/pull/218
[#219]: https://github.com/Database-Tycoon/tycoon-cli/issues/219
[#221]: https://github.com/Database-Tycoon/tycoon-cli/issues/221
[#240]: https://github.com/Database-Tycoon/tycoon-cli/issues/240
[#248]: https://github.com/Database-Tycoon/tycoon-cli/pull/248
[#249]: https://github.com/Database-Tycoon/tycoon-cli/pull/249
[#250]: https://github.com/Database-Tycoon/tycoon-cli/pull/250
[#256]: https://github.com/Database-Tycoon/tycoon-cli/pull/256
[#259]: https://github.com/Database-Tycoon/tycoon-cli/issues/259
[#260]: https://github.com/Database-Tycoon/tycoon-cli/pull/260
[#261]: https://github.com/Database-Tycoon/tycoon-cli/issues/261
[#262]: https://github.com/Database-Tycoon/tycoon-cli/issues/262
[#263]: https://github.com/Database-Tycoon/tycoon-cli/issues/263
[#264]: https://github.com/Database-Tycoon/tycoon-cli/issues/264
[#272]: https://github.com/Database-Tycoon/tycoon-cli/issues/272
[#288]: https://github.com/Database-Tycoon/tycoon-cli/pull/288
[#289]: https://github.com/Database-Tycoon/tycoon-cli/pull/289
[#291]: https://github.com/Database-Tycoon/tycoon-cli/issues/291
[#298]: https://github.com/Database-Tycoon/tycoon-cli/issues/298
[#306]: https://github.com/Database-Tycoon/tycoon-cli/issues/306
[#307]: https://github.com/Database-Tycoon/tycoon-cli/issues/307
[#308]: https://github.com/Database-Tycoon/tycoon-cli/issues/308
[#309]: https://github.com/Database-Tycoon/tycoon-cli/issues/309
[#310]: https://github.com/Database-Tycoon/tycoon-cli/issues/310
[#322]: https://github.com/Database-Tycoon/tycoon-cli/issues/322
[#323]: https://github.com/Database-Tycoon/tycoon-cli/issues/323
[#325]: https://github.com/Database-Tycoon/tycoon-cli/issues/325
[#326]: https://github.com/Database-Tycoon/tycoon-cli/issues/326
[#327]: https://github.com/Database-Tycoon/tycoon-cli/issues/327
[#331]: https://github.com/Database-Tycoon/tycoon-cli/pull/331
[#339]: https://github.com/Database-Tycoon/tycoon-cli/issues/339
[#340]: https://github.com/Database-Tycoon/tycoon-cli/issues/340
[#341]: https://github.com/Database-Tycoon/tycoon-cli/issues/341
[#343]: https://github.com/Database-Tycoon/tycoon-cli/issues/343
[#344]: https://github.com/Database-Tycoon/tycoon-cli/issues/344
[#347]: https://github.com/Database-Tycoon/tycoon-cli/issues/347
[#348]: https://github.com/Database-Tycoon/tycoon-cli/issues/348
[#349]: https://github.com/Database-Tycoon/tycoon-cli/issues/349
[#350]: https://github.com/Database-Tycoon/tycoon-cli/issues/350
[#351]: https://github.com/Database-Tycoon/tycoon-cli/issues/351
[#377]: https://github.com/Database-Tycoon/tycoon-cli/issues/377
[#378]: https://github.com/Database-Tycoon/tycoon-cli/issues/378
[#382]: https://github.com/Database-Tycoon/tycoon-cli/issues/382
[#383]: https://github.com/Database-Tycoon/tycoon-cli/issues/383
[#384]: https://github.com/Database-Tycoon/tycoon-cli/issues/384
[#385]: https://github.com/Database-Tycoon/tycoon-cli/issues/385
[#386]: https://github.com/Database-Tycoon/tycoon-cli/issues/386
[#387]: https://github.com/Database-Tycoon/tycoon-cli/issues/387
[#388]: https://github.com/Database-Tycoon/tycoon-cli/issues/388
[#389]: https://github.com/Database-Tycoon/tycoon-cli/issues/389
[#390]: https://github.com/Database-Tycoon/tycoon-cli/issues/390
[#391]: https://github.com/Database-Tycoon/tycoon-cli/issues/391
[#392]: https://github.com/Database-Tycoon/tycoon-cli/issues/392
[#393]: https://github.com/Database-Tycoon/tycoon-cli/issues/393
[#394]: https://github.com/Database-Tycoon/tycoon-cli/issues/394
[#395]: https://github.com/Database-Tycoon/tycoon-cli/pull/395
[#396]: https://github.com/Database-Tycoon/tycoon-cli/pull/396
[#398]: https://github.com/Database-Tycoon/tycoon-cli/pull/398
[#399]: https://github.com/Database-Tycoon/tycoon-cli/pull/399
[#400]: https://github.com/Database-Tycoon/tycoon-cli/pull/400
[#401]: https://github.com/Database-Tycoon/tycoon-cli/pull/401
[#402]: https://github.com/Database-Tycoon/tycoon-cli/pull/402
[#403]: https://github.com/Database-Tycoon/tycoon-cli/pull/403
[#404]: https://github.com/Database-Tycoon/tycoon-cli/pull/404
[#405]: https://github.com/Database-Tycoon/tycoon-cli/pull/405
[#409]: https://github.com/Database-Tycoon/tycoon-cli/pull/409
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
[#430]: https://github.com/Database-Tycoon/tycoon-cli/issues/430
[#431]: https://github.com/Database-Tycoon/tycoon-cli/issues/431
[#434]: https://github.com/Database-Tycoon/tycoon-cli/issues/434
[#437]: https://github.com/Database-Tycoon/tycoon-cli/issues/437
[#443]: https://github.com/Database-Tycoon/tycoon-cli/issues/443
[#446]: https://github.com/Database-Tycoon/tycoon-cli/issues/446
[#447]: https://github.com/Database-Tycoon/tycoon-cli/issues/447
[#448]: https://github.com/Database-Tycoon/tycoon-cli/issues/448
[#449]: https://github.com/Database-Tycoon/tycoon-cli/pull/449
[#450]: https://github.com/Database-Tycoon/tycoon-cli/pull/450
[#459]: https://github.com/Database-Tycoon/tycoon-cli/issues/459
[#460]: https://github.com/Database-Tycoon/tycoon-cli/issues/460
[#463]: https://github.com/Database-Tycoon/tycoon-cli/pull/463
[#465]: https://github.com/Database-Tycoon/tycoon-cli/issues/465
[#466]: https://github.com/Database-Tycoon/tycoon-cli/pull/466
[#467]: https://github.com/Database-Tycoon/tycoon-cli/pull/467
[#469]: https://github.com/Database-Tycoon/tycoon-cli/issues/469
[#473]: https://github.com/Database-Tycoon/tycoon-cli/issues/473
[#474]: https://github.com/Database-Tycoon/tycoon-cli/pull/474
[#477]: https://github.com/Database-Tycoon/tycoon-cli/pull/477
[#478]: https://github.com/Database-Tycoon/tycoon-cli/pull/478
[#479]: https://github.com/Database-Tycoon/tycoon-cli/pull/479
[#481]: https://github.com/Database-Tycoon/tycoon-cli/pull/481
[#482]: https://github.com/Database-Tycoon/tycoon-cli/pull/482
[#484]: https://github.com/Database-Tycoon/tycoon-cli/pull/484
[#485]: https://github.com/Database-Tycoon/tycoon-cli/pull/485
[#487]: https://github.com/Database-Tycoon/tycoon-cli/issues/487
[#488]: https://github.com/Database-Tycoon/tycoon-cli/pull/488
[#493]: https://github.com/Database-Tycoon/tycoon-cli/issues/493
[#497]: https://github.com/Database-Tycoon/tycoon-cli/issues/497
[#498]: https://github.com/Database-Tycoon/tycoon-cli/issues/498
[#499]: https://github.com/Database-Tycoon/tycoon-cli/issues/499
[#500]: https://github.com/Database-Tycoon/tycoon-cli/issues/500
[#501]: https://github.com/Database-Tycoon/tycoon-cli/pull/501
[#502]: https://github.com/Database-Tycoon/tycoon-cli/pull/502
[#503]: https://github.com/Database-Tycoon/tycoon-cli/pull/503
[#505]: https://github.com/Database-Tycoon/tycoon-cli/pull/505
[#506]: https://github.com/Database-Tycoon/tycoon-cli/pull/506
[#510]: https://github.com/Database-Tycoon/tycoon-cli/issues/510
[#512]: https://github.com/Database-Tycoon/tycoon-cli/pull/512
