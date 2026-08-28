"""What a catalog keeps when it does not fit, and what it says about the rest.

Two decisions live here, both of which change what the city *is* and both of
which therefore owe the document a note rather than a log line:

* **Retention at MAX_OBJECTS** -- which 500 objects of a 2,000-object
  warehouse become buildings.
* **Key collisions** -- what happens when two objects claim the same
  `schema.name`, which DuckDB allows and which every key-addressed map
  downstream cannot survive.

Split out of `loader.py` on 2026-08-06 when that file passed the 500-line
rule. The loader still owns the *order* these run in; this module owns the
rules themselves.
"""

import logging
from collections import Counter

from .models import CatalogObject
from .sql_lineage import mentioned_keys

logger = logging.getLogger(__name__)

# How many objects become buildings. Not a rendering budget picked from
# nowhere: an uncapped 2,060-object catalog took 21 s to load and then was
# killed laying out its grid, so this is the line between a city and a
# swapfile. `_cap_objects` decides WHICH ones.
MAX_OBJECTS = 500


def cap_catalog(objects: list[CatalogObject], view_sql: dict[str, str]) -> tuple[list[CatalogObject], str | None]:
    """The catalog as it will be rendered, and a note when that is not all of it.

    The whole cap decision is one call so `MAX_OBJECTS` is read in exactly one
    module. A second binding of it in the loader is the shape of bug this
    project keeps finding: two names for one rule that stop agreeing.
    """
    if len(objects) <= MAX_OBJECTS:
        return objects, None
    logger.warning(
        "Catalog has %d objects; capping to %d (lineage neighbourhoods first).",
        len(objects),
        MAX_OBJECTS,
    )
    kept = _cap_objects(objects, view_sql)
    # The logger is not the UI. Truncation changes what the city *is*, so it
    # has to reach the document: absence stays named.
    return kept, _cap_note(objects, kept)


def _cap_objects(objects: list[CatalogObject], view_sql: dict[str, str]) -> list[CatalogObject]:
    """The retention rule at MAX_OBJECTS: **whole neighbourhoods, then size.**

    Two failures, one after the other, shaped this.

    A plain "largest by row count" sort is wrong, not merely crude: views are
    constructed with `row_count=0` (a view has no measured size), so it ranks
    every view below every non-empty table and a 600-object catalog loses
    *all* of them. Views are the only carriers of SQL, and SQL is where
    lineage comes from — a city with no views is a city with no streets.

    Keeping views wholesale, which is what fixed that, has the mirror-image
    failure and it is just as bad. A warehouse with more than MAX_OBJECTS
    views spends the whole budget on them and retains **no tables at all**:
    measured on a 2,060-object catalog (1,060 views over 1,000 tables) that
    left 500 buildings with 59 streets between them, because every table the
    retained views read had been dropped, and ten of its twenty-one schemas
    vanished without a word.

    So retention keeps *neighbourhoods*: each view is admitted together with
    the objects its SQL mentions (`sql_lineage.mentioned_keys`, an
    over-approximation on purpose), and a view whose whole neighbourhood does
    not fit is skipped so smaller ones can still get in. What the earlier rule
    wanted — "participates in an edge" — is finally the criterion; it was only
    ever unavailable because edges are derived *from* the retained set, and a
    textual mention is the part of that answer computable up front. Leftover
    budget then fills the old way, views before tables and largest first, so a
    catalog with no view SQL retains exactly what it always did.

    Neighbourhoods are admitted one schema at a time, round-robin, for the
    reason districts are 1:1 with schemas everywhere else in this project: a
    schema with no lot left is a district that silently does not exist, and
    alphabetical order alone hands the whole budget to whichever schemas sort
    first. On the same 2,060-object catalog that is six surviving schemas
    against twenty-one.

    Ties break on key so the retained set is deterministic.
    """
    by_key = {o.key: o for o in objects}
    mentions = mentioned_keys(objects, view_sql)
    views = _round_robin_by_schema(
        sorted((o for o in objects if o.kind == "view"), key=lambda o: (-o.row_count, o.key))
    )

    kept: dict[str, CatalogObject] = {}
    for view in views:
        neighbourhood = [view] + [by_key[key] for key in sorted(mentions.get(view.key, ())) if key in by_key]
        wanted = [o for o in neighbourhood if o.key not in kept]
        if len(kept) + len(wanted) > MAX_OBJECTS:
            continue  # a fan-in too wide for the budget must not starve the rest
        kept.update((o.key, o) for o in wanted)

    fill = views + sorted((o for o in objects if o.kind != "view"), key=lambda o: (-o.row_count, o.key))
    for obj in fill:
        if len(kept) >= MAX_OBJECTS:
            break
        kept.setdefault(obj.key, obj)
    return sorted(kept.values(), key=lambda o: o.key)


def _round_robin_by_schema(ordered: list[CatalogObject]) -> list[CatalogObject]:
    """The same objects, dealt out one per schema in turn.

    Order within a schema is preserved, so the caller's ranking still decides
    which of a schema's objects goes first; only the competition *between*
    schemas changes.
    """
    per_schema: dict[str, list[CatalogObject]] = {}
    for obj in ordered:
        per_schema.setdefault(obj.schema, []).append(obj)
    rank = {obj.key: i for group in per_schema.values() for i, obj in enumerate(group)}
    return sorted(ordered, key=lambda o: (rank[o.key], o.schema, o.key))


def _cap_note(before: list[CatalogObject], after: list[CatalogObject]) -> str:
    """What the cap did, in the document rather than in the logger.

    Naming the total is not enough. Truncation changes what the city *is*, and
    the two facts a reader needs beyond the count are which kind of object
    went and whether any district disappeared entirely — a schema with no lot
    left is a hole in the map that nothing else in the document mentions.
    """
    kinds_before = Counter(o.kind for o in before)
    kinds_after = Counter(o.kind for o in after)
    lost_schemas = len({o.schema for o in before} - {o.schema for o in after})
    note = (
        f"catalog has {len(before)} objects; showing the {MAX_OBJECTS} most relevant "
        f"(kept {kinds_after['view']} of {kinds_before['view']} views and "
        f"{kinds_after['table']} of {kinds_before['table']} tables"
    )
    if lost_schemas:
        note += f"; {lost_schemas} schemas dropped entirely"
    return note + ")"


def drop_duplicate_keys(objects: list[CatalogObject]) -> tuple[list[CatalogObject], str | None]:
    """One object per `schema.name` key, and a note when that costs anything.

    `key` is the identity every map downstream is keyed by — lots, positions,
    columns, districts — so two objects sharing one is not cosmetic: the
    second silently replaces the first everywhere, and the layout crashes
    outright (`min() iterable argument is empty`) when the loser's schema is
    left holding no placed lot. DuckDB allows a `.` *inside* an identifier, so
    schema `a.b` table `c` and schema `a` table `b.c` are two real objects
    with one key.

    The first in catalog order wins (the caller sorts on (key, schema, name),
    so "first" cannot depend on how DuckDB listed them) and the rest are
    counted, rather than inventing an escaped key format: `schema.name` is
    what the wire, the manifest join and every column map already agree on.
    Absence stays named.
    """
    kept: dict[str, CatalogObject] = {}
    dropped = 0
    for obj in objects:
        if obj.key in kept:
            dropped += 1
            continue
        kept[obj.key] = obj
    if not dropped:
        return list(kept.values()), None
    subject = "1 object" if dropped == 1 else f"{dropped} objects"
    return list(kept.values()), (
        f"{subject} collide with another object on the same 'schema.name' key "
        "(a '.' inside a schema or table name) and are not shown"
    )
