"""The site plan: which column and which ROW every building takes.

Half of the DAG planner (`town_plan` is the other half plus the orchestration;
`town_streets` turns this into pavement). Split out on 2026-08-05 when
`town_plan.py` passed the 500-line rule — the seam is the one the streets v4
blueprint named: rows and clustering here, channels and routing there.
Nothing in this module knows a road exists.

What it decides, in order:

  columns   depth (`compute_depths`, cycle-safe) is the x band; long edges
            reserve ONE shared pass-through slot per (destination, column).
  order     barycenter sweeps, then schema BANDS, then AFFINITY clusters
            (shared-source buildings touch), with sibling BLOCKS (exact same
            source set) contiguous inside their cluster.
  footprints the top decile of this catalog's row counts gets a 2x2 lot.
  rows      the clustering rhythm (blocks touch, bands tight, boundaries wide),
            first-member FLOAT (a column starts on its predecessors' row), and
            the HIGHWAY pass (one constant crossing row per destination).

Imports no pygame and holds no rendering concepts.
"""

from dataclasses import dataclass

from ..catalog.models import PipelineContext

# The clustering RHYTHM (Stephen, 2026-08-05: "I don't see the clustering"):
# grouping only reads when spacing varies. Same-schema neighbours sit tight,
# schema-band boundaries leave a visible gap, blocks touch.
NEIGHBOUR_PITCH = 2  # same schema band: dense neighbourhood
BAND_GAP = 5  # a new schema band: unmistakable open ground between districts
MARGIN = 3

# The western utility strip, fixed columns: the plant, its feeder, the
# POWER_LINE trunk, the per-source stubs, then the first building column.
PLANT_X = 1
TRUNK_X = 3
FIRST_COL_X = 5


@dataclass(frozen=True)
class SitePlan:
    """Everything decided before the first street is drawn."""

    # Edge -> the chain of nodes its street threads (dummies for crossings).
    chains: dict[tuple[str, str], list[str]]
    node_layer: dict[str, int]  # depth per node, dummies included
    columns: dict[int, list[str]]  # column membership, dummy slots included
    forward_segments: list[tuple[str, str]]  # deduplicated, west -> east
    rows_of: dict[str, int]  # the y of every node, dummies included
    block_of: dict[str, str]  # sibling-block id per member (exact source set)
    big: frozenset[str]  # 2x2 lots


def big_lots(ctx: PipelineContext) -> frozenset[str]:
    """The 2x2 ground plans (Stephen, 2026-08-05, approved with the roads
    pass; scale was half the problem — a 1-tile road beside a 1-tile
    skyscraper reads wrong). "Big" is a relative, MEASURED fact: the top decile
    of THIS catalog's row counts (at least one, once four objects have rows at
    all), so every warehouse gets its downtown mass. Views and empty tables
    stay 1x1. NW anchor; growth east and south."""
    positive = sorted((o for o in ctx.objects if o.row_count > 0), key=lambda o: (-o.row_count, o.key))
    if len(positive) < 4:
        return frozenset()
    return frozenset(o.key for o in positive[: max(1, len(positive) // 10)])


def _forward_chains(
    edges: list[tuple[str, str]],
    depth: dict[str, int],
) -> tuple[dict[tuple[str, str], list[str]], dict[str, int], dict[int, list[str]]]:
    """Edge -> node chain, with ONE shared dummy per (destination, column).

    Every edge bound for the same destination that crosses a column rides the
    same reserved pass-through row — the tributary system stays merged once it
    merges. Same-depth edges (inside a dependency cycle) get a two-node chain
    handled as a loop segment by the router. Returns the chains, a layer map
    covering dummies, and the column membership including dummy slots.
    """
    node_layer = dict(depth)
    columns: dict[int, list[str]] = {}
    for key in sorted(depth):
        columns.setdefault(depth[key], []).append(key)
    chains: dict[tuple[str, str], list[str]] = {}
    for src, dst in edges:
        chain = [src]
        for mid in range(depth[src] + 1, depth[dst]):
            dummy = f"\x00{dst}\x00{mid}"  # NUL prefix: unspellable as a key
            if dummy not in node_layer:
                columns.setdefault(mid, []).append(dummy)
                node_layer[dummy] = mid
            chain.append(dummy)
        chain.append(dst)
        chains[(src, dst)] = chain
    return chains, node_layer, columns


def _barycenter_order(
    columns: dict[int, list[str]],
    segments: list[tuple[str, str]],
    node_layer: dict[str, int],
    sweeps: int = 4,
) -> dict[int, dict[str, int]]:
    """Row order per column, crossing-reduced by averaging neighbour rows."""
    order = {ly: {n: i for i, n in enumerate(sorted(columns[ly]))} for ly in columns}
    by_dst: dict[str, list[str]] = {}
    by_src: dict[str, list[str]] = {}
    for a, b in segments:
        by_dst.setdefault(b, []).append(a)
        by_src.setdefault(a, []).append(b)
    layers = sorted(columns)

    def rank(ly: int, neighbours: dict[str, list[str]]) -> None:
        ranked = sorted(
            columns[ly],
            key=lambda n: (
                sum(order[node_layer[m]][m] for m in neighbours[n]) / len(neighbours[n])
                if neighbours.get(n)
                else float(order[ly][n]),
                n,
            ),
        )
        order[ly] = {n: i for i, n in enumerate(ranked)}

    for _ in range(sweeps):
        for ly in layers[1:]:
            rank(ly, by_dst)
        for ly in reversed(layers[:-1]):
            rank(ly, by_src)
    return order


def _sibling_blocks(
    connected: list[str],
    preds: dict[str, set[str]],
    schema_of: dict[str, str],
    depth: dict[str, int],
) -> dict[str, str]:
    """Sibling BLOCKS (Stephen, 2026-08-05: "if two models have the exact same
    sources, they should be clustered together to form a block"). The key is
    exact — same schema, same depth, same full source set — never fuzzy;
    members pack at pitch 1 (touching, a real city block) and share one
    delivery trunk, because one street serves buildings fed by the same
    suppliers. Chain-heavy DAGs (dogfood) may have none; star schemas many."""
    groups: dict[tuple, list[str]] = {}
    for k in connected:
        if k in preds:
            groups.setdefault((schema_of[k], depth[k], frozenset(preds[k])), []).append(k)
    block_of: dict[str, str] = {}
    for members in groups.values():
        if len(members) >= 2:
            block_id = min(members)
            for m in members:
                block_of[m] = block_id
    return block_of


def _cluster_columns(
    columns: dict[int, list[str]],
    order: dict[int, dict[str, int]],
    preds: dict[str, set[str]],
    block_of: dict[str, str],
    schema_of: dict[str, str],
    row_count_of: dict[str, int],
) -> dict[str, tuple[int, str]]:
    """Rewrite `order` in place into bands -> clusters -> blocks, and report
    which cluster each building joined (the row cursor needs it).

    Cluster by schema (Stephen, 2026-08-05: "cluster buildings by schema...
    otherwise this is going to look like a circuit board"): within each column
    a schema's buildings become one contiguous band, bands ordered by mean
    barycenter rank so lineage still pulls related neighbourhoods together,
    and dummies (pass-through streets) take no cursor row at all.

    Inside a band, AFFINITY CLUSTERS (Stephen, 2026-08-05: "Think like a true
    urban planner. Try to cluster together the bigger buildings / tables
    visually especially if they share common sources"): buildings sharing at
    least one source join one cluster (transitively); clusters order by lineage
    pull, the biggest tables lead inside each, and members TOUCH — the city
    block, now visible on warehouses whose source sets overlap without being
    identical. Exact-source sibling BLOCKS stay contiguous inside their cluster
    and keep their extra privilege — ONE delivery trunk — untouched.
    """
    cluster_of: dict[str, tuple[int, str]] = {}
    for ly, members in columns.items():
        ranks = order[ly]
        groups: dict[str, list[str]] = {}
        for n in members:
            if n.startswith("\x00"):
                continue  # pass-through slots take no cursor row (highway pass)
            groups.setdefault(schema_of[n], []).append(n)
        banded = sorted(
            groups.values(),
            key=lambda g, r=ranks: (sum(r[n] for n in g) / len(g), min(g)),
        )

        sequence: list[str] = []
        for band in banded:
            parent = {n: n for n in band}

            def find(a: str, parent=parent) -> str:
                while parent[a] != a:
                    parent[a] = parent[parent[a]]
                    a = parent[a]
                return a

            for i, a in enumerate(band):
                for b in band[i + 1 :]:
                    if preds.get(a, set()) & preds.get(b, set()):
                        ra, rb = find(a), find(b)
                        if ra != rb:
                            parent[max(ra, rb)] = min(ra, rb)
            clusters: dict[str, list[str]] = {}
            for n in sorted(band):
                clusters.setdefault(find(n), []).append(n)
            for root, cluster in sorted(
                clusters.items(),
                key=lambda kv, r=ranks: (sum(r[n] for n in kv[1]) / len(kv[1]), kv[0]),
            ):
                # Blocks stay contiguous: members sort by their block group
                # (sized by its largest table), biggest groups first.
                group_size: dict[str, int] = {}
                for n in cluster:
                    g = block_of.get(n, n)
                    group_size[g] = max(group_size.get(g, 0), row_count_of.get(n, 0))
                cluster.sort(
                    key=lambda n, gs=group_size, r=ranks: (
                        -gs[block_of.get(n, n)],
                        block_of.get(n, n),
                        -row_count_of.get(n, 0),
                        r[n],
                        n,
                    )
                )
                for n in cluster:
                    cluster_of[n] = (ly, root)
                sequence.extend(cluster)
        order[ly] = {n: i for i, n in enumerate(sequence)}
    return cluster_of


def _assign_rows(
    columns: dict[int, list[str]],
    order: dict[int, dict[str, int]],
    cluster_of: dict[str, tuple[int, str]],
    adjacent_preds: dict[str, list[str]],
    schema_of: dict[str, str],
    big: frozenset[str],
) -> dict[str, int]:
    """The cursor + FLOAT pass (streets v3, 2026-08-05, Stephen: the roads are
    "strange and unrealistic and ugly"). Rows are decided BEFORE column x
    positions, because whether a unit needs a vertical trunk at all depends on
    rows — and a channel only reserves width for units that do.

      cursor  the clustering rhythm (blocks touch, bands tight, gaps wide);
      float   a column's FIRST building starts on its predecessors' row
              instead of the margin, so matched columns align and a 1:1 chain
              becomes one straight street. MEASURED on dogfood before
              choosing: float-only gave 8 straight routes / 7 kinks vs 5/6
              with no alignment — and per-building slack stretching LOST (5
              straight, 11 kinks: an ideal it could only half-reach
              manufactured 1-tile staircases).
    """
    rows_of: dict[str, int] = {}
    for ly in sorted(columns):
        previous: str | None = None
        y = MARGIN
        real = sorted((m for m in columns[ly] if not m.startswith("\x00")), key=lambda n: order[ly][n])
        for i, n in enumerate(real):
            if i == 0:
                pred_rows = sorted(rows_of[p] for p in adjacent_preds.get(n, ()) if p in rows_of)
                ideal = pred_rows[len(pred_rows) // 2] if pred_rows else None
                y = MARGIN if ideal is None else max(MARGIN, ideal)
            else:
                same_cluster = cluster_of.get(n) is not None and cluster_of.get(n) == cluster_of.get(previous)
                y += 1 if same_cluster else NEIGHBOUR_PITCH if schema_of[n] == schema_of[previous] else BAND_GAP
            rows_of[n] = y
            if n in big:
                y += 1  # a 2x2 lot owns its south row too
            previous = n
    return rows_of


def _highway_pass(
    columns: dict[int, list[str]],
    rows_of: dict[str, int],
    big: frozenset[str],
) -> None:
    """One constant crossing row per destination, written into `rows_of`.

    A pass-through slot takes no cursor row — a crossing only needs a row no
    building in that column occupies (both rows of a 2x2 lot count). So a
    destination's pass-throughs all take ONE row, the nearest free-everywhere
    row to the destination itself, and a long street rides a single straight
    arterial instead of jogging at every column.
    """
    used_rows: dict[int, set[int]] = {}
    for ly, members in columns.items():
        taken: set[int] = set()
        for n in members:
            if n.startswith("\x00"):
                continue
            taken.add(rows_of[n])
            if n in big:
                taken.add(rows_of[n] + 1)
        used_rows[ly] = taken
    dummy_cols: dict[str, list[int]] = {}
    for ly, members in columns.items():
        for n in members:
            if n.startswith("\x00"):
                dummy_cols.setdefault(n.split("\x00")[1], []).append(ly)
    row_ceiling = max((y for ys in used_rows.values() for y in ys), default=MARGIN) + len(dummy_cols) + MARGIN
    for dst in sorted(dummy_cols):
        cols = dummy_cols[dst]
        target = rows_of[dst]
        h = target
        for delta in range(row_ceiling):
            near = (target,) if delta == 0 else (target - delta, target + delta)
            found = next(
                (c for c in near if c >= MARGIN and all(c not in used_rows[m] for m in cols)),
                None,
            )
            if found is not None:
                h = found
                break
        for m in cols:
            used_rows[m].add(h)
            rows_of[f"\x00{dst}\x00{m}"] = h


def plan_site(
    ctx: PipelineContext,
    edges: list[tuple[str, str]],
    depth: dict[str, int],
) -> SitePlan:
    """Columns, order, footprints and rows — the site before any pavement."""
    connected = sorted(depth)
    schema_of = {obj.key: obj.schema for obj in ctx.objects}
    row_count_of = {obj.key: obj.row_count for obj in ctx.objects}
    big = big_lots(ctx)

    preds: dict[str, set[str]] = {}
    for s, d in edges:
        preds.setdefault(d, set()).add(s)
    block_of = _sibling_blocks(connected, preds, schema_of, depth)

    chains, node_layer, columns = _forward_chains(edges, depth)
    # Deduplicated: same-destination chains share dummies, so they share the
    # trailing segments of their chains too.
    forward_segments = sorted(
        {
            (a, b)
            for chain in chains.values()
            for a, b in zip(chain, chain[1:], strict=False)
            if node_layer[b] > node_layer[a]
        }
    )
    order = _barycenter_order(columns, forward_segments, node_layer)
    cluster_of = _cluster_columns(columns, order, preds, block_of, schema_of, row_count_of)

    adjacent_preds: dict[str, list[str]] = {}
    for s, d in edges:
        if depth[d] - depth[s] == 1:
            adjacent_preds.setdefault(d, []).append(s)
    rows_of = _assign_rows(columns, order, cluster_of, adjacent_preds, schema_of, big)
    _highway_pass(columns, rows_of, big)

    return SitePlan(
        chains=chains,
        node_layer=node_layer,
        columns=columns,
        forward_segments=forward_segments,
        rows_of=rows_of,
        block_of=block_of,
        big=big,
    )
