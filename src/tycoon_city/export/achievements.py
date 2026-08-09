"""Achievements: named coverage milestones, counted from real artifacts.

Stephen's rule, in force everywhere in this repository: **achievements are
COUNTS OF REAL ARTIFACTS, never invented points.** `docs/semantic-roads.md`
names two of them by hand -- "every mart reachable by paved road", "old town
fully signed" -- as *counts of real declared artifacts*, and that is the whole
mechanic: absence renders as underdevelopment, and filling documentation in
feels like building.

They are also **STATELESS**. A milestone is "true right now", computed from
this document and nothing else: no minted-badge store, no first-earned
timestamp, nothing persisted. That is what keeps `city.json` byte-stable, and
it is also the honest shape -- an achievement that stays lit after the
documentation is deleted would be a trophy, not a measurement.

Every milestone carries its MEASURED terms: `have`, `need`, and `short` -- the
actual object keys that fall short, so the HUD can fly to them. Every number in
this city is a door.

## The three states, and why `unmet` is not the default

The law this block exists to obey is the one `docs/city-json-v1.md` already
states for `lots[].build_status` and for `weather`: **unknown never renders as
stale.** Here it reads:

* A catalog with **no dbt manifest at all** does not have 0% documentation
  coverage. It has *unknown* coverage -- the artifact that would answer the
  question was never read, and the models may be immaculately documented in a
  manifest we never got. Reporting `met: false, have: 0` would invent a
  failure out of an absence, and would put a red gauge in front of someone
  who has nothing to fix.
* The same holds one rung down: a milestone whose **universe is empty** (no
  marts on this map, no judged sources) has nothing to measure, and a
  vacuously "met" milestone is the same lie wearing the opposite colour.

So `state` is the discriminator -- `met` / `unmet` / `unknown` -- and in the
unknown state `met`, `have` and `need` are all **null**. Two independent
readings therefore both refuse to mislead: a client switching on `state` sees
the third case by name, and a client that only looks at `met` gets null rather
than a `false` it would render as a failed milestone.

Nothing here is persisted, timestamped, seeded or path-bearing, and the
milestone list is a fixed literal order, so the block is byte-stable by
construction.
"""

from typing import Any

from ..catalog.models import PipelineContext
from ..sim.signals import SourceFreshnessStatus, TestStatus

#: The three values `achievements.milestones[].state` can take. `unknown` is a
#: first-class state, not the absence of the other two.
STATE_MET = "met"
STATE_UNMET = "unmet"
STATE_UNKNOWN = "unknown"

# The sentences that name a missing artifact. Each one says what was not read
# AND that the milestone is unknown rather than zero, because the note is what
# a client puts next to the greyed-out gauge.
NO_MANIFEST_NOTE = "no dbt manifest joined onto this catalog — coverage is unknown, not zero"
NO_FRESHNESS_NOTE = "no `dbt source freshness` verdicts — SLA coverage is unknown, not zero"
NO_SEMANTIC_NOTE = "no semantic model (Apache Ossie / OSI) — the declared network is unknown, not empty"
NO_TEST_RESULTS_NOTE = "no test results in the run history — fires are unknown, not out"

# The top-level note when every single milestone came back unknown. A wall of
# zeroes would misrepresent absence as failure; this says the catalog has not
# handed us anything to measure yet, which is the actionable fact.
NOTHING_TO_MEASURE_NOTE = (
    "nothing measurable yet: this catalog supplied none of the artifacts these "
    "milestones count, so every one of them is unknown rather than unmet"
)


def _milestone(
    milestone_id: str,
    name: str,
    description: str,
    *,
    universe: set[str],
    covered: set[str],
    counts: str,
    missing_evidence: str | None,
) -> dict[str, Any]:
    """One milestone, in whichever of the three states its evidence supports.

    `missing_evidence` is the sentence to emit when the artifact that would
    supply the terms was never read -- passing it is what makes the caller
    state, per milestone, what "we cannot know" looks like for that milestone.
    `universe` is what has to be covered and `covered` is what already is;
    `short` is the difference, sorted, and it is the fly-to list.
    """
    if missing_evidence is not None:
        return _unknown(milestone_id, name, description, missing_evidence)
    if not universe:
        # Nothing to measure is not "all done": a vacuous `met` on an empty
        # universe is the same misrepresentation as a zero on a missing one.
        return _unknown(milestone_id, name, description, f"nothing to measure: this catalog has no {counts}")
    short = sorted(universe - covered)
    need = len(universe)
    have = need - len(short)
    return {
        "id": milestone_id,
        "name": name,
        "description": description,
        "state": STATE_MET if have == need else STATE_UNMET,
        "met": have == need,
        "have": have,
        "need": need,
        # The keys that fall short, so the HUD can fly to them. Bounded by the
        # loader's 500-object cap, sorted, so the block stays byte-stable.
        "short": short,
        "note": f"{have} of {need} {counts}",
    }


def _unknown(milestone_id: str, name: str, description: str, note: str) -> dict[str, Any]:
    """The unknown state, spelled out once so no caller can spell it two ways.

    `met` is **null**, not false: a client that only looks at `met` must not
    read a missing measurement as a failed one. `have`/`need` are null for the
    same reason -- `have: 0` is a measurement, and we did not take one.
    """
    return {
        "id": milestone_id,
        "name": name,
        "description": description,
        "state": STATE_UNKNOWN,
        "met": None,
        "have": None,
        "need": None,
        "short": [],
        "note": note,
    }


# --- what the catalog actually told us -------------------------------------


def _manifest_note(ctx: PipelineContext) -> str | None:
    """None when a dbt manifest joined onto this catalog, else the sentence.

    Structural, not a `notes` string match: the question is whether the
    manifest reached *this* catalog's objects, and a manifest that matched
    nothing tells us exactly as much about documentation as no manifest at all.
    """
    joined = ctx.dbt_context_by_key or ctx.dbt_nodes_by_key or ctx.tests_by_key
    return None if joined else NO_MANIFEST_NOTE


def _semantic_note(ctx: PipelineContext) -> str | None:
    joined = ctx.ai_context_by_key or ctx.semantic_relationships
    return None if joined else NO_SEMANTIC_NOTE


def _adjacency(ctx: PipelineContext) -> tuple[set[str], set[str]]:
    """(keys with an inbound edge, keys with an outbound edge), on-map only.

    Same rule as `blocks._edges`: an edge to something that is not in
    `objects` is not on the map and cannot make anything a mart or a source.
    """
    keys = {obj.key for obj in ctx.objects}
    inbound: set[str] = set()
    outbound: set[str] = set()
    for edge in ctx.edges:
        if edge.src in keys and edge.dst in keys and edge.src != edge.dst:
            outbound.add(edge.src)
            inbound.add(edge.dst)
    return inbound, outbound


def _marts(ctx: PipelineContext) -> set[str]:
    """**How "mart" is defined here: the lineage DAG's terminal objects.**

    A mart is an object with at least one inbound lineage edge and no outbound
    one -- the end of the line, the thing the pipeline exists to deliver and
    the thing people query. That is read off `edges[]`, which is measured,
    rather than off a schema called `mart`, which is a naming convention: a
    catalog whose reporting layer lives in `analytics` or `rpt` or `core` has
    marts too, and one with a `mart` schema full of intermediate models does
    not have five.

    The inbound requirement is what keeps an isolated table out. A standalone
    object nothing feeds and that feeds nothing is not the end of a pipeline;
    it is a building with no streets, and calling it an unpaved mart would put
    a permanent red mark on catalogs that simply have no lineage.

    District membership (`objects[].schema`, which is what `districts[]` is
    keyed on) is read alongside this only to *describe* the shortfall in the
    note -- how many districts the unpaved marts are scattered across. It is
    deliberately not part of the definition, for the naming-convention reason
    above.
    """
    inbound, outbound = _adjacency(ctx)
    return inbound - outbound


def _join_endpoints(ctx: PipelineContext) -> set[str]:
    """Every object a DECLARED join touches, on either side.

    "Reachable by paved road" in `docs/semantic-roads.md`'s incentive table:
    a join known only from SQL is a dirt track, a relationship declared in OSI
    is the paved and marked street. So a building is reachable by paved road
    when at least one declared join runs to it -- you can drive there.
    """
    keys = {obj.key for obj in ctx.objects}
    endpoints: set[str] = set()
    for rel in ctx.semantic_relationships:
        # Same on-map filter `blocks._joins` applies before emitting.
        if rel.many in keys and rel.one in keys:
            endpoints.add(rel.many)
            endpoints.add(rel.one)
    return endpoints


def _districts_of(ctx: PipelineContext, keys: set[str]) -> int:
    schema_of = {obj.key: obj.schema for obj in ctx.objects}
    return len({schema_of[key] for key in keys if key in schema_of})


def _documented(ctx: PipelineContext) -> set[str]:
    return {
        key for key, context in ctx.dbt_context_by_key.items() if context.description and context.description.strip()
    }


def _signed(ctx: PipelineContext) -> set[str]:
    """Objects whose declared OSI dataset carries `ai_context`.

    `AiContext.declared` is the same predicate `blocks._semantic_block` leans
    on to keep "nobody declared this" and "declared but unannotated" apart --
    a dataset someone named without annotating has no signage yet.
    """
    return {key for key, dataset in ctx.ai_context_by_key.items() if dataset.ai_context.declared}


# --- the block --------------------------------------------------------------


def _achievements(ctx: PipelineContext) -> dict[str, Any]:
    """The `achievements` block: six milestones, each a count of real artifacts.

    A pure function of the context -- no city, no theme, no clock -- which is
    what makes it stateless and byte-stable. The milestone order is a fixed
    literal, which is stronger than sorting on a key that cannot tie.
    """
    keys = {obj.key for obj in ctx.objects}
    manifest = _manifest_note(ctx)
    semantic = _semantic_note(ctx)

    freshness = {key: str(word) for key, word in SourceFreshnessStatus().compute(ctx).items()}
    freshness = {key: word for key, word in freshness.items() if key in keys}
    tests = {key: str(word) for key, word in TestStatus().compute(ctx).items()}
    tests = {key: word for key, word in tests.items() if key in keys}

    inbound, outbound = _adjacency(ctx)
    marts = _marts(ctx)
    mart_districts = _districts_of(ctx, marts)
    # A source is where the lineage starts: nothing feeds it and it feeds
    # something. Anything dbt judged is a source too, even one nothing on this
    # map reads yet -- otherwise a judged-but-unused source would be counted as
    # covered without ever being counted as needing cover.
    sources = ((keys - inbound) & outbound) | set(freshness)

    milestones = [
        _milestone(
            "documented_buildings",
            "Every building has a plaque",
            "Objects carrying a dbt description — the nameplate over the door.",
            universe=keys,
            covered=_documented(ctx),
            counts="buildings carry a dbt description",
            missing_evidence=manifest,
        ),
        _milestone(
            "tested_buildings",
            "Every building inspected",
            "Objects carrying at least one declared dbt test.",
            universe=keys,
            covered={key for key, refs in ctx.tests_by_key.items() if refs and key in keys},
            counts="buildings carry a dbt test",
            missing_evidence=manifest,
        ),
        _milestone(
            "sources_under_sla",
            "Every source under SLA",
            "Sources carrying a `dbt source freshness` verdict — a declared, judged SLA.",
            universe=sources,
            covered=set(freshness),
            counts="sources carry a dbt freshness verdict",
            missing_evidence=NO_FRESHNESS_NOTE if not freshness else None,
        ),
        _milestone(
            "old_town_signed",
            "Old town fully signed",
            "Objects carrying declared OSI `ai_context` — the street signs and lobby directories.",
            universe=keys,
            covered=_signed(ctx),
            counts="buildings carry declared OSI ai_context",
            missing_evidence=semantic,
        ),
        _milestone(
            "marts_paved",
            "Every mart reachable by paved road",
            "Marts — the lineage DAG's terminal objects — touched by a DECLARED join, "
            "which is what paves a road that SQL scanning leaves as dirt track.",
            universe=marts,
            covered=_join_endpoints(ctx),
            counts=(
                f"marts (terminal in lineage, across {mart_districts} "
                f"{'district' if mart_districts == 1 else 'districts'}) "
                "are touched by a declared join"
            ),
            missing_evidence=semantic,
        ),
        _milestone(
            "fires_out",
            "No building on fire",
            "Objects whose declared tests have actually run, and none of them failing.",
            universe=set(tests),
            covered={key for key, word in tests.items() if word != "fail"},
            counts="buildings with a run test result are not failing",
            missing_evidence=NO_TEST_RESULTS_NOTE if not tests else None,
        ),
    ]
    return {"milestones": milestones, "note": _note(milestones)}


def _note(milestones: list[dict[str, Any]]) -> str:
    """The block's own summary, which has to survive the all-unknown case.

    A catalog that supplied nothing gets this sentence instead of six zeroes:
    absence is not failure, and a HUD that renders it as failure teaches people
    to ignore the gauge.
    """
    total = len(milestones)
    met = sum(1 for m in milestones if m["state"] == STATE_MET)
    unknown = sum(1 for m in milestones if m["state"] == STATE_UNKNOWN)
    if unknown == total:
        return NOTHING_TO_MEASURE_NOTE
    head = f"{met} of {total} milestones met"
    if not unknown:
        return f"{head}; every milestone's terms are measurable here"
    return (
        f"{head}; {unknown} unknown — the artifact that would supply their terms "
        "was never read, which is not the same as unmet"
    )


__all__ = [
    "NOTHING_TO_MEASURE_NOTE",
    "NO_FRESHNESS_NOTE",
    "NO_MANIFEST_NOTE",
    "NO_SEMANTIC_NOTE",
    "NO_TEST_RESULTS_NOTE",
    "STATE_MET",
    "STATE_UNKNOWN",
    "STATE_UNMET",
    "_achievements",
]
