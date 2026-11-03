# Roadmap

_Last updated 2026-11-02, during the v0.2.4 cycle. This page is the north
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

## Now: v0.2.4

Sprint 2026-10-24 to 2026-11-06. The theme on the milestone is "trust what
tycoon tells you": run history, status and the city should report what
actually happened. Nothing has merged to the release branch yet; the open pull
requests are listed with their issues.

- Data integrity and unblockers. The `duckdb==1.5.2` pin breaks
  QUALIFY-over-cast models ([#339]). `data run-all` runs whichever dbt is
  first on `PATH` rather than tycoon's own ([#439], PR [#461]). Projects
  share `~/.dlt/pipelines`, so same-named sources share incremental state
  and load duplicates ([#394], PRs [#398], [#399], [#400]). An invalid
  `tycoon.yml` crashes `--help` and `--version` ([#378]).
- MotherDuck Phase 0 ([#429]). One helper accepts both `md:` and
  `motherduck:` ([#308], PR [#454]), `data query` refuses DDL and DML on
  MotherDuck unless asked ([#309], PR [#452]), and `data schema` estimates
  row counts instead of counting every table ([#310], PR [#451]). The rest
  of Phase 0 moved to v0.2.5, below.
- Run history. Successful dbt builds are marked failed ([#341], PR [#462]),
  failed runs are never recorded ([#377]), `data status` says "last build
  never" when history has the builds ([#390], PR [#397]), and `data run-all`
  records no dbt rows at all ([#326]).
- The city. Eight fixes from the 0.2.3 review: the legend and detail panel
  overlap ([#382]), long names clip ([#383]), HUD panels run off narrow
  windows ([#384]), labels overlap ([#385]), the opening camera misses the
  city ([#386]), dbt sources are missing so staging models show no upstream
  ([#387]), views show zero rows ([#388]), and two object counts disagree
  ([#389]). PRs [#401] through [#409]. A mental model of the map joins the
  docs ([#323], PR [#331]).
- CLI. Output formats and no squashed columns for `data query`, plus filters
  for `data schema` ([#391], [#393], PR [#395]); `doctor` stops calling a
  working `.venv` broken ([#392], PR [#396]); `tycoon init` creates a new dbt
  project inline rather than as a sibling repo ([#259], PR [#260]); local
  secret files stay out of commits ([#410], PR [#411]); the Jira sync
  workflow and `PTC-` title scopes go away ([#351], PR [#463]).
- Docs. This page ([#219], PR [#218]) and maintainer process pages for CI/CD,
  QA and metrics ([#220], PR [#217]).

Also open against the v0.2.4 branch, but not part of this cycle: the
layer-aware data CLI ([#306], PRs [#288], [#289]), scheduled for v0.2.5
below, and the DuckLake storage proposal (PR [#74]), which has no milestone.

## Next: v0.2.5 to v0.3.1

Two-week cycles, each with a GitHub milestone.

- v0.2.5, to 2026-11-20: the rewrite foundation. The remaining config
  singleton uses move to the project model ([#175], [#176], [#189]); the
  source catalog gets its JSON manifest and loader ([#98], [#100], design in
  [#197]); the layer-aware data CLI lands ([#306], PRs [#288], [#289]).
  MotherDuck Phase 0 finishes: raw ingestion lands in a MotherDuck raw
  database ([#430], [#447], [#448], PRs [#455], [#456]) with a `motherduck`
  extra for pyarrow ([#459]), the city accepts `motherduck:` ([#446], PR
  [#457]), OSI scaffolding reads a MotherDuck warehouse ([#298], PR [#450]),
  and a token-gated e2e job runs on demand ([#437], PR [#449]). Phase 1 adds
  the Destination protocol and a MotherDuck destination ([#110], [#118]). Alongside: `data transform freshness`
  ([#340]), a looser `dbt-core` pin ([#347]), consistent local time in
  status and history ([#322], [#327]), and an `md:` target with no token
  failing instead of opening a browser ([#460]).
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
  `ducklake_config.py` still only writes Parquet ([#72]).
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
- [v0.2.1](releases/v0.2.1.md), 2026-09-16: a filesystem source can declare
  several named resources and load them in one run ([#224], [#225]), JSONL
  joins CSV and Parquet ([#228]), and config that used to be quietly
  defaulted is validated instead, the one breaking change ([#223]). `tycoon
  city` lays the city out by pipeline depth (PR [#247]). Pull requests get
  size and title checks ([#211], [#213]) and a writing-style skill ([#215]).

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
[#211]: https://github.com/Database-Tycoon/tycoon-cli/issues/211
[#213]: https://github.com/Database-Tycoon/tycoon-cli/issues/213
[#215]: https://github.com/Database-Tycoon/tycoon-cli/issues/215
[#217]: https://github.com/Database-Tycoon/tycoon-cli/pull/217
[#218]: https://github.com/Database-Tycoon/tycoon-cli/pull/218
[#219]: https://github.com/Database-Tycoon/tycoon-cli/issues/219
[#220]: https://github.com/Database-Tycoon/tycoon-cli/issues/220
[#221]: https://github.com/Database-Tycoon/tycoon-cli/issues/221
[#223]: https://github.com/Database-Tycoon/tycoon-cli/issues/223
[#224]: https://github.com/Database-Tycoon/tycoon-cli/issues/224
[#225]: https://github.com/Database-Tycoon/tycoon-cli/issues/225
[#228]: https://github.com/Database-Tycoon/tycoon-cli/issues/228
[#240]: https://github.com/Database-Tycoon/tycoon-cli/issues/240
[#247]: https://github.com/Database-Tycoon/tycoon-cli/pull/247
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
[#397]: https://github.com/Database-Tycoon/tycoon-cli/pull/397
[#398]: https://github.com/Database-Tycoon/tycoon-cli/pull/398
[#399]: https://github.com/Database-Tycoon/tycoon-cli/pull/399
[#400]: https://github.com/Database-Tycoon/tycoon-cli/pull/400
[#401]: https://github.com/Database-Tycoon/tycoon-cli/pull/401
[#409]: https://github.com/Database-Tycoon/tycoon-cli/pull/409
[#410]: https://github.com/Database-Tycoon/tycoon-cli/issues/410
[#411]: https://github.com/Database-Tycoon/tycoon-cli/pull/411
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
[#439]: https://github.com/Database-Tycoon/tycoon-cli/issues/439
[#446]: https://github.com/Database-Tycoon/tycoon-cli/issues/446
[#447]: https://github.com/Database-Tycoon/tycoon-cli/issues/447
[#448]: https://github.com/Database-Tycoon/tycoon-cli/issues/448
[#449]: https://github.com/Database-Tycoon/tycoon-cli/pull/449
[#450]: https://github.com/Database-Tycoon/tycoon-cli/pull/450
[#451]: https://github.com/Database-Tycoon/tycoon-cli/pull/451
[#452]: https://github.com/Database-Tycoon/tycoon-cli/pull/452
[#454]: https://github.com/Database-Tycoon/tycoon-cli/pull/454
[#455]: https://github.com/Database-Tycoon/tycoon-cli/pull/455
[#456]: https://github.com/Database-Tycoon/tycoon-cli/pull/456
[#457]: https://github.com/Database-Tycoon/tycoon-cli/pull/457
[#459]: https://github.com/Database-Tycoon/tycoon-cli/issues/459
[#460]: https://github.com/Database-Tycoon/tycoon-cli/issues/460
[#461]: https://github.com/Database-Tycoon/tycoon-cli/pull/461
[#462]: https://github.com/Database-Tycoon/tycoon-cli/pull/462
[#463]: https://github.com/Database-Tycoon/tycoon-cli/pull/463
