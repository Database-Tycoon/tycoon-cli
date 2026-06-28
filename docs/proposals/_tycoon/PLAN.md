# PLAN — Tycoon CLI Rewrite

> Companion to [MANIFESTO.md](./MANIFESTO.md) (the *why*) and [ARCHITECTURE.md](./ARCHITECTURE.md) (the *how it's built*). This document is the *what we're doing about it* — the execution plan to evolve the current codebase toward the new vision.
>
> Intended audience: contributors and reviewers (Stephen, the team). Will be threaded as a GitHub issue once vetted internally.

---

## TL;DR

We are rewriting the ingestion layer of `tycoon-cli` against the abstractions in MANIFESTO.md and ARCHITECTURE.md. Two existing packages will coexist in this repo during the rewrite: `src/tycoon/` (current production code, entrypoint `tycoon`) and `src/_tycoon/` (the rewrite, entrypoint `tycli`). When the rewrite reaches feature parity for ingestion and passes the architectural acceptance test (Fivetran adapter slotted in with zero core changes), we cut over in a single PR: delete `src/tycoon/`, rename `src/_tycoon/` → `src/tycoon/`. The `tycli` entrypoint stays as either an alias or the primary command depending on what we've learned by then.

The decision to rewrite rather than refactor was made after a focused inventory pass (Appendix A). The current code is ~50% reshapeable, ~30% actively contradicts the new shape, and the load-bearing assumptions (source-type conflated with runtime, dispatch hardcoded to dlt, shims monolithic) are exactly the assumptions the new abstractions exist to remove. Refactoring in-place would force a months-long half-converted state. Rewriting in parallel keeps the production CLI working while the new shape is built deliberately.

---

## Decisions locked

These are settled. Each is recorded here so the rationale is durable.

### D1 — Rewrite path: extract a new package, port the good parts

Build a new package at `src/_tycoon/` from scratch against the manifesto and architecture. The old `src/tycoon/` remains untouched in the same repo as a working fallback. Four specific patterns from the old code will be ported deliberately (see §"Port list"). Everything else either gets rebuilt with the right shape or stays out.

**Why not refactor in place:** half-converted codebases die of contortion. Every PR becomes "rename this, gate that, add a flag." The load-bearing assumptions in the current code are exactly what the new abstractions remove — fighting them in-flight is slower than rebuilding cleanly.

**Why not pure greenfield in a separate repo:** we'd lose the four patterns worth porting, lose the git history, and create a coordination problem (two repos to track, two PyPI distributions to reconcile). Same-repo coexistence is cheaper.

**Why the install-base does not constrain:** ~17 PyPI downloads/day, no known production users. The team is the entire user base. No coexistence-for-users requirement.

### D2 — Package and entrypoint naming

| Surface | During rewrite window | At cutover |
|---|---|---|
| Import path | `_tycoon` | `tycoon` |
| Filesystem | `src/_tycoon/` | `src/tycoon/` (old deleted) |
| Entrypoint command | `tycli` | `tycli` (alias) and/or `tycoon` (decide at cutover) |
| PyPI distribution | unchanged (`database-tycoon`) | unchanged unless we rename deliberately |

The leading underscore is the explicit "in-progress, will-be-renamed" marker. It cannot be invoked by accident through `tycoon`. The entrypoint is decoupled from the import name from day one — that decoupling is permanent, not just a rewrite-window convenience. We never again confuse "what the package is called internally" with "what the user types."

### D3 — CLI as a thin shell over a programmatic API

Every command returns a typed result. The CLI renderer formats it for humans; the JSON surface emits the same model unchanged for agents; future surfaces (MCP, TUI) read the same model. The Python API is the real product; the CLI imports and calls it.

**What this means concretely:**
- No command function "prints a table." It returns a structured result object; a renderer prints the table.
- `--json` works on every command by default, emitting the same model the CLI rendered.
- `from _tycoon import sources; sources.add(...)` gives an experience equivalent to `tycli source add ...`.
- This is the manifesto §5 (agent-latchability) commitment made concrete from day one. Retrofitting later is much harder than building toward it.

### D4 — Quality scaffolding from day one, proportionate

| Concern | Decision |
|---|---|
| Test framework | pytest (same as current `tycoon`) |
| Test types | Unit tests for `core/`; integration tests for adapters; one end-to-end test for the Phase 1 vertical slice |
| Coverage target | None as a number. Behavioral floor: each `core/` module has tests; each adapter has at least one integration test; each command has a smoke test |
| Linting | ruff (strict-ish — fail on import order, unused, undocumented public APIs in `core/`) |
| Type checking | mypy or pyright in strict mode on `core/`; looser on adapters where third-party stubs are weak |
| CI | One GitHub Actions workflow: lint + type-check + test on PRs |
| Pre-commit hooks | ruff format + ruff check + mypy on changed files |
| `CLAUDE.md` | At `src/_tycoon/` root. Short (under 200 lines). Covers manifesto's load-bearing rules, layering constraints, "where new things go," test/lint expectations |

Done first, before any business logic. Empty package, working CI, working pre-commit, empty `CLAUDE.md`. Sets the tone.

### D5 — POC scope: ingestion only, two Runtimes, three modes

Per manifesto §8. The rewrite ships exactly two Runtime adapters in the POC:

- **dlt** — execution in-process (or in a controlled subprocess for `dlt-project`)
- **Fivetran** — execution delegated; dbty observes and triggers via API

From those, three Source modes:

1. **`dlt-native`** — dbty runs a dlt source or resource (own shim or user entrypoint)
2. **`dlt-project`** — dbty wraps a user's existing dlt project
3. **`fivetran`** — dbty observes and triggers a Fivetran connector via API

**Out of scope for this rewrite:** Transformation, Semantics, Presentation, additional Surfaces (MCP, TUI, web). The architecture has homes for these; they are built after Phase 2 lands.

---

## Sequencing

Four steps, in order. Each has a concrete acceptance criterion. No step starts until the previous one passes.

### Step 1 — Rails up

**Goal:** Empty package with all quality scaffolding working. No business logic.

**Concrete deliverables:**
- `src/_tycoon/` directory with the layout from ARCHITECTURE.md §"Level 4 — Code" (`core/`, `runtimes/`, `destinations/`, `metadata_backends/`, `scaffolds/`, `surfaces/cli/`, `surfaces/json/`).
- Every module is empty but has a docstring stating its purpose. The layering rules from ARCHITECTURE.md are enforceable by inspection.
- `pyproject.toml` updated: new `[project.scripts]` entry `tycli = "_tycoon.cli:app"`, keeping existing `tycoon` entry untouched.
- `ruff`, `mypy`/`pyright`, pytest configured. Pre-commit hooks installed.
- One GitHub Actions workflow that runs lint + type-check + test on PRs.
- `src/_tycoon/CLAUDE.md` written: load-bearing rules, layering constraints, where new things go.

**Acceptance:**
- `pip install -e .` succeeds.
- `tycli --help` works and shows an empty Typer app (or a placeholder).
- `pytest` runs, finds zero tests, exits 0.
- `ruff check src/_tycoon/` is clean.
- CI passes on PR.

**Estimated effort:** half a day.

### Step 2 — Protocols + one real dlt adapter, no CLI

**Goal:** Prove the core abstractions hold against one real adapter before the CLI shape is locked in.

**Concrete deliverables:**
- `core/source.py` — `Source` dataclass with identity, runtime binding, handle, capability declarations.
- `core/runtime.py` — **The `Runtime` Protocol — the single contract every Runtime implements.** Methods: `capabilities`, `catalog_offers`, `introspect`, `run`, `observe`, `read_state`. The dlt adapter built in this step is the *first* implementation, not a special case. Future runtimes (dlt-project, Fivetran, sling, Airbyte) implement the same Protocol without modifying `core/`.
- `core/capabilities.py` — `Capability` enum and capability-set helpers.
- `core/events.py` — Pydantic models for the metadata event schema (subset sufficient for ingestion runs).
- `core/identifiers.py` — qualified IDs (e.g. `source:<name>@<runtime>`), parsing, formatting.
- `core/metadata.py` — **The `MetadataBackend` Protocol and the Metadata API. Metadata is an abstract substrate with pluggable backing.** The DuckDB file backing built in this step is the cockpit default; the Protocol is designed against the second backing (writes into the user's Destination as a managed schema) from day one. Configuration surface includes which backing to use and any backing-specific options (file path for the file backing; connection + schema name for the Destination backing). User-overrideable via project manifest.
- `metadata_backends/duckdb_file.py` — local DuckDB file backing. **First implementation of `MetadataBackend`, not the only shape the Protocol supports.** Configurable file path (with a sensible default — see open questions).
- `metadata_backends/__init__.py` — backend registry. Selecting a backing is a configuration choice in the project manifest, not a hardcoded import.
- `runtimes/dlt_native.py` — first dlt adapter. Start with REST API or one verified source (whichever is simpler to wire). Implements the full Runtime Protocol.
- `runtimes/__init__.py` — runtime registry. Same pattern as `metadata_backends/`.
- Unit tests on every `core/` module.
- One integration test: invoke `dlt_native` runtime programmatically, ingest, write a metadata event to the file backing, read it back.
- One contract test for `MetadataBackend`: a shared test suite that any backing implementation must pass. The file backing passes it now; future backings (Destination, in-memory for tests) pass it too. This is what keeps the contract honest.
- One contract test for `Runtime`: same idea — a shared test suite every Runtime implementation passes.

**Acceptance:**
- `python -c "from _tycoon.runtimes.dlt_native import DltNativeRuntime; ..."` works.
- A test executes ingestion end-to-end without any CLI in the loop.
- Metadata events are written to `.tycoon/metadata.duckdb` (or the new path we settle on) and queryable.
- `mypy --strict src/_tycoon/core/` passes.

**Estimated effort:** ~1 week.

**Why no CLI yet:** the CLI is a rendering of the model. The model has to be right first. If the CLI surfaces design decisions backward into `core/`, the model is wrong and we fix it before adding the second renderer.

### Step 3 — CLI surface, designed top-down

**Goal:** Phase 1 vertical slice working end-to-end through `tycli`.

**Concrete deliverables (in this order):**
- A separate short document — a command-tree sketch — reviewed before implementation. ASCII tree, each verb has a one-line purpose and a typed result shape. This is the deliberate CLI modeling exercise (D3).
- `surfaces/cli/` implementations of: `attach`, `source add`, `source list`, `source show`, `source remove`, `run`, `status`.
- Every command is a thin wrapper that parses intent, calls the core, returns a typed result.
- `surfaces/json/` renderer that emits the typed result as JSON.
- A CLI human-renderer that formats the same typed result as a table/tree/whatever fits.
- `--json` flag on every command, emitting the JSON surface output unchanged.
- One end-to-end test: `tycli attach` in an empty directory → `tycli source add <something>` → `tycli run <something>` → `tycli status`, verified via both the CLI and `--json`.
- `scaffolds/manifest.py` and `scaffolds/dlt_native.py` implementing the strict scaffolder charter from MANIFESTO.md §9.

**Acceptance:**
- Phase 1 vertical slice from MANIFESTO.md §8 passes end-to-end.
- An agent (or a curl-and-jq script) can read `--json` output, parse the result, and act on it.
- Scaffolders create only what's needed, in the user's idiom, never mutate existing files, never re-run.

**Estimated effort:** ~1 week.

### Step 4 — Port the named patterns from `tycoon/`

**Goal:** Lift the four pleasantly-surprising patterns from the old code. Each port is a small focused PR.

**The port list (the entire list — nothing else gets ported):**

1. **Metadata hook pattern** — `capture_dlt_safe`, `capture_dbt_safe`, etc. The fail-silent capture hook shape, adapted to the new event-shaped Metadata API.
2. **Flat Pydantic source-config shape** — adapted into `core/source.py`, with `runtime` as a first-class field (the missing thing today).
3. **Command-surface separation** — the discipline of keeping `add` / `remove` / `run` cleanly separated from scaffolding side-effects, ported to the new CLI shape.
4. **Soft-fail capture pattern** — the silent-failure observability convention, used in the new `core/metadata.py` API as the default for non-critical writes.

**Explicit don't-port list** — these are not coming over, ever, from the old code:
- The FastAPI server (`commands/start.py`, `commands/stop.py`, `commands/services.py`)
- The Dagster orchestration scaffolding (`orchestration/`)
- The nao-core AI integration (`commands/ask.py`)
- The dbt auto-scaffolding side effects on `run`
- The existing flat command layout
- The existing `CATALOG` static dict (replaced by federated Catalog query layer per ARCHITECTURE.md)
- The shim-as-strings pattern from `source_manager.py` (replaced by adapter files)

**Acceptance:** the four patterns are present in the new code, with tests, and the old code's equivalents are not referenced.

**Estimated effort:** ~3-5 days.

---

## Phase 2 — The architectural acceptance test (after the four steps)

After Step 4, the next milestone is adding the **Fivetran Runtime adapter** in `runtimes/fivetran.py`.

**The acceptance test:** Fivetran is added with **zero changes to `src/_tycoon/core/`**. If a core change is needed, the Runtime Protocol is wrong and we fix the Protocol, not the Fivetran adapter. This is the architectural acceptance test from MANIFESTO.md §8 made concrete.

If we cannot add Fivetran without touching `core/`, the abstractions are wrong and we stop and fix them before any more adapters get written. This is the moment of truth for the design.

**Estimated effort:** ~1 week for the adapter itself; unknown if the Protocol needs revision.

---

## Cutover

Triggered when Phase 2 passes — Fivetran adapter works, zero core changes were needed (or the Protocol was revised and both adapters now sit on the revised Protocol).

**Cutover PR contents:**
- Delete `src/tycoon/` (and tests, and Dagster/FastAPI/nao extras from `pyproject.toml`).
- `git mv src/_tycoon src/tycoon`. Find-and-replace `_tycoon` → `tycoon` in imports.
- `[project.scripts]`: remove old `tycoon` entry. Keep `tycli`. Optionally add `tycoon` as alias.
- Update `README.md`, `CHANGELOG.md`, `MANIFESTO.md`, `ARCHITECTURE.md` to remove rewrite-window framing.
- Bump major version.

**Total estimated calendar effort, Step 1 through Cutover:** 4–6 weeks, depending on how clean Phase 2 lands.

---

## Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| The Runtime Protocol designed against dlt is wrong for Fivetran | Medium | Phase 2 is the deliberate test. We catch it before more adapters compound the mistake. |
| Scope creep on the port — "let's also bring over X" | High | The port list is in writing. PRs that exceed it get rejected. |
| Old `tycoon` package gets accidentally modified during rewrite | Low | Convention only — nobody assigns tickets against `src/tycoon/` during the rewrite window. Repo README will state this. |
| CLI design decisions leak backward into `core/` | Medium | Step 2 builds and tests `core/` with no CLI in the loop. Step 3 is downstream of a finished Step 2. |
| The four-pattern port list is incomplete — we discover a fifth pattern worth keeping | Medium | The port list can grow during Step 4 with a written justification, but each addition is reviewed against "does this actively shape the new code, or are we just sentimentally attached." |
| Fivetran adapter requires core changes that retroactively break the dlt adapter | Low-Medium | Both adapters are exercised by their integration tests on every PR. A change that breaks one is rejected. |

---

## Open questions (to resolve during execution)

These are intentionally unresolved here so they get decided in context rather than guessed in advance:

1. **Metadata backing configuration surface.** What's the default file path for the DuckDB file backing (`.tycoon/metadata.duckdb` collides with old code; `.tycli/metadata.duckdb` is separate; something else)? More importantly, what's the project-manifest shape for choosing a non-default backing and configuring it? The Protocol must support file backing, Destination backing (post-POC), and an in-memory backing for tests from day one — but only the file backing needs to be *implemented* in Step 2. Settle the configuration shape so adding the Destination backing later is "one file in `metadata_backends/`, zero changes to the manifest schema."
2. **Should `dlt-project` Runtime run in-process or in a subprocess?** Open question from ARCHITECTURE.md Level 3. Resolve when we wire the first user-supplied dlt project.
3. **`commands/` vs `surfaces/cli/` as the folder for command implementations.** Decide in Step 3.
4. **Static adapter registry vs. entry-point-based discovery.** Static is sufficient for the POC; defer entry-point discovery until a third party wants to ship an adapter.
5. **Whether to introduce a common `Adapter` base Protocol** that Runtime / Transformation / Semantics / Presentation extend. Defer until at least one adapter exists in each folder (architecture open thread).
6. **Cutover entrypoint:** keep `tycli` as primary, or rename to `tycoon` and demote `tycli` to alias. Decide at cutover based on what we've learned about usage.

---

## Appendix A — Inventory findings (summary)

A focused diagnostic pass on the current `src/tycoon/` ingestion code categorized everything against the new vision: **Aligns / Bends / Breaks / Missing**. Full report available; summarized here.

**Overall ratio:** ~15% aligns, ~50% bends, ~30% breaks, ~5% missing.

**The three load-bearing assumptions in current code that most constrain a redirect:**
1. `SourceConfig.type` conflates source-type with runtime — no runtime field exists.
2. `runner.run_source()` has no runtime decision point; dlt is baked all the way through.
3. Shims live inside `source_manager.py` as monolithic Python strings — new runtimes mean editing that file, not adding adapter files.

**The four pleasantly-surprising things worth porting (the port list in §Step 4):**
1. Metadata capture is already hook-shaped, soft-fail, runtime-agnostic in spirit.
2. Command surface is cleanly separated from scaffolding side-effects.
3. `SourceConfig` is flat Pydantic — straightforward to adapt.
4. Optional extras (Dagster, FastAPI, nao-core) are properly scoped — they're in `[extras]`, not threaded through ingestion core.

---

## Status

This plan reflects decisions taken between the manifesto/architecture conversations and the start of execution, as of 2026-06-28. Once vetted internally, it becomes the basis of a GitHub issue for Stephen's review and ongoing tracking.

**Next action after sign-off:** open the GitHub issue, then begin Step 1.
