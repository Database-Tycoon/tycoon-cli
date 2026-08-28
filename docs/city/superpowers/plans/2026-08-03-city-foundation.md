---
title: City foundation implementation plan
description: TDD plan for catalog-scaled districts placed by lineage depth, lineage-driven roads, POWER_LINE arterials, and honest powered state
tags: [plan, generator, layout, lineage, tdd]
related: [2026-08-03-city-foundation-design]
updated: '2026-08-03'
---

# City Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the unconditional road grid with districts sized to the catalog and placed in rings by lineage depth, roads that follow lineage, arterials that place the legended `POWER_LINE` tile, and a `powered` binding that can return false.

**Architecture:** A new pure-geometry module `sim/layout.py` turns a `PipelineContext` into a `LayoutPlan` (grid size, plant position, one square footprint per schema). `sim/generator.py` consumes that plan and paints tiles. `sim/signals.py` gains a data function that distinguishes objects participating in lineage from orphans. Nothing in this plan touches the renderer's geometry, the spritesheet, or the camera — the work is upstream of rendering by design, so it survives the planned move to a 3D renderer.

**Tech Stack:** Python 3.12+, `uv`, pytest, ruff. No new dependencies.

## Global Constraints

- Python `>=3.12` (`pyproject.toml`). Use modern type syntax (`X | None`, builtin generics).
- ruff: `line-length = 100`, `target-version = "py312"`, `select = ["E", "F", "I", "UP", "B"]`. Run `uv run ruff format . && uv run ruff check .` before every commit.
- **`sim/` must never import pygame.** Guarded by `tests/sim/test_no_pygame.py`. `sim/layout.py` is subject to this.
- **No sprite work.** `themes/default/spritesheet.png` and `scripts/make_default_theme.py` are not edited. Every sprite needed already exists in the committed sheet, `power_line` included.
- **Determinism:** identical catalog yields an identical map. No `random` in `sim/layout.py` or `sim/generator.py` after this plan. `Engine` keeps its own `random.Random` for presentation traffic.
- **Read-only:** nothing writes to the user's database.
- Run the full suite with `uv run pytest -q` before each commit. It is 73 tests green at the start of this plan.
- **Cut from this phase, do not implement:** drag-to-pan and camera clamping. A 3D orbit controller replaces both. Leave `render/camera.py` and `MapScreen.handle_event` alone.

---

### Task 1: Lineage depth and isolation

**Files:**
- Create: `src/pipeline_city/sim/layout.py`
- Test: `tests/sim/test_layout_depth.py`

**Interfaces:**
- Consumes: `PipelineContext`, `CatalogObject`, `Edge` from `pipeline_city.catalog.models`. `CatalogObject.key` is the `"schema.name"` string; edges reference those keys.
- Produces:
  - `compute_depths(ctx: PipelineContext) -> dict[str, int]` — every object key mapped to its lineage depth. Sources (no incoming edge) are `0`.
  - `isolated_keys(ctx: PipelineContext) -> set[str]` — keys with no edge in either direction.

Both are used by Task 2 and Task 4.

- [ ] **Step 1: Write the failing tests**

Create `tests/sim/test_layout_depth.py`:

```python
from pipeline_city.catalog.models import CatalogObject, Edge, PipelineContext
from pipeline_city.sim.layout import compute_depths, isolated_keys


def _ctx(objects, edges=()):
    return PipelineContext("demo", tuple(objects), tuple(edges))


def _obj(schema, name):
    return CatalogObject(schema, name, "table", 0)


def test_linear_chain_increments_depth():
    ctx = _ctx(
        [_obj("raw", "a"), _obj("stg", "b"), _obj("mart", "c")],
        [Edge("raw.a", "stg.b"), Edge("stg.b", "mart.c")],
    )
    assert compute_depths(ctx) == {"raw.a": 0, "stg.b": 1, "mart.c": 2}


def test_diamond_takes_longest_path():
    # a -> b -> d and a -> c -> d; d must be 2, not 1.
    ctx = _ctx(
        [_obj("s", "a"), _obj("s", "b"), _obj("s", "c"), _obj("s", "d")],
        [
            Edge("s.a", "s.b"),
            Edge("s.a", "s.c"),
            Edge("s.b", "s.d"),
            Edge("s.c", "s.d"),
        ],
    )
    assert compute_depths(ctx) == {"s.a": 0, "s.b": 1, "s.c": 1, "s.d": 2}


def test_isolated_object_is_depth_zero():
    ctx = _ctx([_obj("raw", "lonely")])
    assert compute_depths(ctx) == {"raw.lonely": 0}


def test_cycle_members_land_past_the_acyclic_max():
    # a -> b is a clean chain; c <-> d is a cycle. Cycle members take max + 1.
    ctx = _ctx(
        [_obj("s", "a"), _obj("s", "b"), _obj("s", "c"), _obj("s", "d")],
        [Edge("s.a", "s.b"), Edge("s.c", "s.d"), Edge("s.d", "s.c")],
    )
    depths = compute_depths(ctx)
    assert depths["s.a"] == 0
    assert depths["s.b"] == 1
    assert depths["s.c"] == 2
    assert depths["s.d"] == 2


def test_edges_referencing_unknown_keys_are_ignored():
    ctx = _ctx([_obj("raw", "a")], [Edge("raw.a", "gone.b")])
    assert compute_depths(ctx) == {"raw.a": 0}


def test_isolated_keys_finds_only_edgeless_objects():
    ctx = _ctx(
        [_obj("raw", "a"), _obj("stg", "b"), _obj("raw", "orphan")],
        [Edge("raw.a", "stg.b")],
    )
    assert isolated_keys(ctx) == {"raw.orphan"}


def test_isolated_keys_ignores_edges_to_unknown_keys():
    # An edge pointing at an object that is not in the catalog does not rescue
    # raw.a from isolation -- it has no edge to anything that exists.
    ctx = _ctx([_obj("raw", "a")], [Edge("raw.a", "gone.b")])
    assert isolated_keys(ctx) == {"raw.a"}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/sim/test_layout_depth.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline_city.sim.layout'`

- [ ] **Step 3: Write the minimal implementation**

Create `src/pipeline_city/sim/layout.py`:

```python
"""Pure geometry for placing a catalog on a grid.

Imports no pygame and holds no rendering concepts: it turns a PipelineContext
into coordinates. Guarded by tests/sim/test_no_pygame.py.
"""

from collections import deque

from ..catalog.models import PipelineContext


def _known_edges(ctx: PipelineContext) -> list[tuple[str, str]]:
    """Edges whose both endpoints exist in the catalog, in context order."""
    keys = {obj.key for obj in ctx.objects}
    return [(e.src, e.dst) for e in ctx.edges if e.src in keys and e.dst in keys]


def compute_depths(ctx: PipelineContext) -> dict[str, int]:
    """Lineage depth per object key: 0 for sources, else longest path from one.

    Uses Kahn's algorithm so a cyclic catalog degrades rather than hanging:
    whatever remains unresolved when the queue drains belongs to a cycle and
    takes the acyclic maximum plus one.
    """
    keys = sorted(obj.key for obj in ctx.objects)
    edges = _known_edges(ctx)

    successors: dict[str, list[str]] = {k: [] for k in keys}
    in_degree: dict[str, int] = dict.fromkeys(keys, 0)
    for src, dst in edges:
        successors[src].append(dst)
        in_degree[dst] += 1

    depths: dict[str, int] = {k: 0 for k in keys if in_degree[k] == 0}
    queue = deque(sorted(depths))
    remaining = dict(in_degree)

    while queue:
        key = queue.popleft()
        for nxt in successors[key]:
            depths[nxt] = max(depths.get(nxt, 0), depths[key] + 1)
            remaining[nxt] -= 1
            if remaining[nxt] == 0:
                queue.append(nxt)

    unresolved = [k for k in keys if k not in depths]
    if unresolved:
        cycle_depth = max(depths.values(), default=-1) + 1
        for key in unresolved:
            depths[key] = cycle_depth

    return depths


def isolated_keys(ctx: PipelineContext) -> set[str]:
    """Object keys with no lineage edge in either direction."""
    connected: set[str] = set()
    for src, dst in _known_edges(ctx):
        connected.add(src)
        connected.add(dst)
    return {obj.key for obj in ctx.objects} - connected
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/sim/test_layout_depth.py -v`
Expected: PASS, 7 tests.

Then confirm nothing else broke and the guard still holds:
Run: `uv run pytest -q`
Expected: PASS, 80 tests.

- [ ] **Step 5: Lint and commit**

```bash
cd ~/Projects/pipeline-city
uv run ruff format . && uv run ruff check .
git add src/pipeline_city/sim/layout.py tests/sim/test_layout_depth.py
git commit -m "feat: add lineage depth and isolation to a new layout module"
```

---

### Task 2: District planning

**Files:**
- Modify: `src/pipeline_city/sim/layout.py` (append to the module from Task 1)
- Test: `tests/sim/test_layout_plan.py`

**Interfaces:**
- Consumes: `compute_depths` from Task 1.
- Produces:
  - `DistrictPlan` — frozen dataclass with fields `schema: str`, `ring: int`, `x: int`, `y: int`, `size: int`. `(x, y)` is the top-left corner in grid coordinates; the footprint is a `size * size` square; `size` is always odd.
  - `LayoutPlan` — frozen dataclass with fields `grid: int`, `plant_xy: tuple[int, int]`, `districts: tuple[DistrictPlan, ...]`.
  - `plan_layout(ctx: PipelineContext) -> LayoutPlan`.
  - Module constants `GRID_MIN = 32`, `GRID_SOFT_MAX = 256`.

Task 3 consumes `plan_layout` and reads every field above.

**Geometry contract, so Task 3 can rely on it:**
- A district holding `n` objects gets `size = 2 * ceil(sqrt(n)) + 1`. Within the footprint, local cells at odd `(i, j)` are lot slots — there are exactly `ceil(sqrt(n)) ** 2 >= n` of them — and every other cell is street. A lot at an odd/odd cell therefore always has a street neighbour.
- A schema's `ring` is the modal depth of its objects, ties broken to the lowest depth.
- Districts never overlap and sit fully inside `[0, grid)`.

- [ ] **Step 1: Write the failing tests**

Create `tests/sim/test_layout_plan.py`:

```python
import math

from pipeline_city.catalog.models import CatalogObject, Edge, PipelineContext
from pipeline_city.sim.layout import GRID_MIN, GRID_SOFT_MAX, plan_layout


def _ctx(objects, edges=()):
    return PipelineContext("demo", tuple(objects), tuple(edges))


def _obj(schema, name):
    return CatalogObject(schema, name, "table", 0)


def _rects(plan):
    return [(d.x, d.y, d.size) for d in plan.districts]


def _overlaps(a, b):
    ax, ay, asize = a
    bx, by, bsize = b
    return ax < bx + bsize and bx < ax + asize and ay < by + bsize and by < ay + asize


def test_one_district_per_schema():
    ctx = _ctx([_obj("raw", "a"), _obj("raw", "b"), _obj("mart", "c")])
    plan = plan_layout(ctx)
    assert sorted(d.schema for d in plan.districts) == ["mart", "raw"]


def test_footprint_is_odd_and_scales_with_object_count():
    ctx = _ctx([_obj("big", f"t{i}") for i in range(9)] + [_obj("small", "only")])
    plan = plan_layout(ctx)
    by_schema = {d.schema: d for d in plan.districts}
    # 9 objects -> ceil(sqrt(9)) == 3 -> size 7; 1 object -> size 3.
    assert by_schema["big"].size == 7
    assert by_schema["small"].size == 3
    for d in plan.districts:
        assert d.size % 2 == 1
        assert ((d.size - 1) // 2) ** 2 >= sum(1 for o in ctx.objects if o.schema == d.schema)


def test_ring_equals_modal_depth():
    # raw is all depth 0; mart is all depth 1.
    ctx = _ctx(
        [_obj("raw", "a"), _obj("raw", "b"), _obj("mart", "c")],
        [Edge("raw.a", "mart.c")],
    )
    plan = plan_layout(ctx)
    by_schema = {d.schema: d for d in plan.districts}
    assert by_schema["raw"].ring == 0
    assert by_schema["mart"].ring == 1


def test_ring_tie_breaks_to_the_lowest_depth():
    # mixed schema holds one depth-0 and one depth-1 object: a 1-1 tie.
    ctx = _ctx(
        [_obj("mixed", "src"), _obj("mixed", "dst"), _obj("other", "x")],
        [Edge("other.x", "mixed.dst")],
    )
    plan = plan_layout(ctx)
    by_schema = {d.schema: d for d in plan.districts}
    assert by_schema["mixed"].ring == 0


def test_districts_never_overlap():
    ctx = _ctx([_obj(f"s{i}", f"t{j}") for i in range(6) for j in range(4)])
    rects = _rects(plan_layout(ctx))
    for i, a in enumerate(rects):
        for b in rects[i + 1 :]:
            assert not _overlaps(a, b)


def test_districts_stay_inside_the_grid():
    ctx = _ctx([_obj(f"s{i}", f"t{j}") for i in range(5) for j in range(3)])
    plan = plan_layout(ctx)
    for d in plan.districts:
        assert 0 <= d.x and d.x + d.size <= plan.grid
        assert 0 <= d.y and d.y + d.size <= plan.grid


def test_plant_sits_inside_the_grid_and_on_no_district():
    ctx = _ctx([_obj("raw", "a"), _obj("mart", "b")], [Edge("raw.a", "mart.b")])
    plan = plan_layout(ctx)
    px, py = plan.plant_xy
    assert 0 <= px < plan.grid and 0 <= py < plan.grid
    for d in plan.districts:
        assert not (d.x <= px < d.x + d.size and d.y <= py < d.y + d.size)


def test_small_catalog_gets_a_small_grid():
    ctx = _ctx([_obj("raw", "a")])
    plan = plan_layout(ctx)
    assert plan.grid == GRID_MIN


def test_grid_grows_with_the_catalog():
    small = plan_layout(_ctx([_obj("raw", f"t{i}") for i in range(3)]))
    large = plan_layout(_ctx([_obj(f"s{i}", f"t{j}") for i in range(8) for j in range(9)]))
    assert large.grid > small.grid


def test_large_catalog_compacts_toward_the_soft_target():
    # 500 objects is the catalog loader's cap.
    ctx = _ctx([_obj(f"s{i}", f"t{j}") for i in range(25) for j in range(20)])
    plan = plan_layout(ctx)
    assert plan.grid <= GRID_SOFT_MAX
    # containment must survive compaction
    for d in plan.districts:
        assert 0 <= d.x and d.x + d.size <= plan.grid
        assert 0 <= d.y and d.y + d.size <= plan.grid


def test_empty_catalog_yields_a_bare_grid():
    plan = plan_layout(_ctx([]))
    assert plan.districts == ()
    assert plan.grid == GRID_MIN
    px, py = plan.plant_xy
    assert 0 <= px < plan.grid and 0 <= py < plan.grid


def test_plan_is_deterministic():
    ctx = _ctx(
        [_obj("raw", "a"), _obj("stg", "b"), _obj("mart", "c")],
        [Edge("raw.a", "stg.b"), Edge("stg.b", "mart.c")],
    )
    assert plan_layout(ctx) == plan_layout(ctx)


def test_footprint_side_matches_the_documented_formula():
    for count, expected in [(1, 3), (2, 5), (4, 5), (5, 7), (9, 7), (10, 9)]:
        ctx = _ctx([_obj("s", f"t{i}") for i in range(count)])
        plan = plan_layout(ctx)
        assert plan.districts[0].size == 2 * math.ceil(math.sqrt(count)) + 1
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/sim/test_layout_plan.py -v`
Expected: FAIL — `ImportError: cannot import name 'GRID_MIN'`

- [ ] **Step 3: Write the minimal implementation**

Append to `src/pipeline_city/sim/layout.py`. Add `import math` and `from dataclasses import dataclass` to the existing imports at the top of the file:

```python
GRID_MIN = 32
GRID_SOFT_MAX = 256

# Spacing candidates tried in order when the natural grid overshoots
# GRID_SOFT_MAX: (ring gap, outer margin). Compaction shrinks the gap between
# rings before it shrinks the border, because the border is what keeps
# districts inside the grid.
_SPACING_CANDIDATES = ((2, 4), (1, 3), (1, 2), (0, 2), (0, 1))


@dataclass(frozen=True)
class DistrictPlan:
    schema: str
    ring: int
    x: int
    y: int
    size: int


@dataclass(frozen=True)
class LayoutPlan:
    grid: int
    plant_xy: tuple[int, int]
    districts: tuple[DistrictPlan, ...]


def _footprint_size(count: int) -> int:
    """Odd side length holding `count` lot slots on odd/odd local cells."""
    return 2 * math.ceil(math.sqrt(max(1, count))) + 1


def _modal_ring(depths: list[int]) -> int:
    """Most common depth; ties break to the lowest, keeping this deterministic."""
    counts: dict[int, int] = {}
    for depth in depths:
        counts[depth] = counts.get(depth, 0) + 1
    best = max(counts.values())
    return min(depth for depth, n in counts.items() if n == best)


def _placements(
    rings: dict[int, list[tuple[str, int]]],
    ring_gap: int,
) -> list[tuple[str, int, int, int, int]]:
    """(schema, ring, cx, cy, size) with centres on concentric rings at origin.

    Each ring's radius clears three constraints: enough circumference for its
    own districts, enough distance from the ring inside it, and enough room to
    miss the plant at the origin.
    """
    placed: list[tuple[str, int, int, int, int]] = []
    previous_radius = 0.0
    previous_max = 0
    for ring in sorted(rings):
        members = sorted(rings[ring])
        count = len(members)
        max_size = max(size for _, size in members)
        radius = max(
            count * (max_size + ring_gap) / (2 * math.pi),
            previous_radius + previous_max / 2 + max_size / 2 + ring_gap,
            max_size / 2 + ring_gap + 1,
        )
        for index, (schema, size) in enumerate(members):
            angle = 2 * math.pi * index / count
            cx = round(radius * math.cos(angle))
            cy = round(radius * math.sin(angle))
            placed.append((schema, ring, cx, cy, size))
        previous_radius = radius
        previous_max = max_size
    return placed


def plan_layout(ctx: PipelineContext) -> LayoutPlan:
    """Place every schema as a square district on a ring set by lineage depth."""
    schemas = sorted({obj.schema for obj in ctx.objects})
    if not schemas:
        centre = GRID_MIN // 2
        return LayoutPlan(grid=GRID_MIN, plant_xy=(centre, centre), districts=())

    depths = compute_depths(ctx)
    rings: dict[int, list[tuple[str, int]]] = {}
    for schema in schemas:
        members = [obj for obj in ctx.objects if obj.schema == schema]
        ring = _modal_ring([depths[obj.key] for obj in members])
        rings.setdefault(ring, []).append((schema, _footprint_size(len(members))))

    for ring_gap, margin in _SPACING_CANDIDATES:
        placed = _placements(rings, ring_gap)
        min_x = min(cx - size // 2 for _, _, cx, _, size in placed)
        max_x = max(cx + size // 2 for _, _, cx, _, size in placed)
        min_y = min(cy - size // 2 for _, _, _, cy, size in placed)
        max_y = max(cy + size // 2 for _, _, _, cy, size in placed)
        # The plant sits at the origin and must also fit inside the border.
        min_x, min_y = min(min_x, 0), min(min_y, 0)
        max_x, max_y = max(max_x, 0), max(max_y, 0)
        span = max(max_x - min_x, max_y - min_y) + 1 + 2 * margin
        grid = max(GRID_MIN, span)
        if grid <= GRID_SOFT_MAX:
            break

    shift_x = margin - min_x
    shift_y = margin - min_y
    districts = tuple(
        DistrictPlan(
            schema=schema,
            ring=ring,
            x=cx - size // 2 + shift_x,
            y=cy - size // 2 + shift_y,
            size=size,
        )
        for schema, ring, cx, cy, size in sorted(placed)
    )
    return LayoutPlan(grid=grid, plant_xy=(shift_x, shift_y), districts=districts)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/sim/test_layout_plan.py -v`
Expected: PASS, 13 tests.

If `test_districts_never_overlap` fails, the ring radius is too small: raise the circumference term in `_placements` by using `max_size + ring_gap + 1`. Do not "fix" it by silently dropping districts.

Run: `uv run pytest -q`
Expected: PASS, 93 tests.

- [ ] **Step 5: Lint and commit**

```bash
cd ~/Projects/pipeline-city
uv run ruff format . && uv run ruff check .
git add src/pipeline_city/sim/layout.py tests/sim/test_layout_plan.py
git commit -m "feat: plan schema districts on lineage-depth rings"
```

---

### Task 3: Rewrite the generator

**Files:**
- Modify: `src/pipeline_city/sim/generator.py` (full rewrite of `generate_city`; `refresh` loses its `seed` parameter)
- Modify: `tests/sim/test_generator.py` (rewrite — it asserts the old 128 grid)
- Modify: `tests/sim/test_refresh.py:32,54` (drop the `"demo"` seed argument)
- Modify: `tests/sim/test_channels.py` — `test_apply_signals_dims_an_orphaned_object` calls `generate_city(ctx, rules, "demo")`. Task 4 wrote it against the current three-arg signature because this task was skipped at the time; drop the seed here too. It carries an inline comment saying so.
- Test: `tests/sim/test_generator.py`

**Interfaces:**
- Consumes: `plan_layout`, `LayoutPlan`, `DistrictPlan` from Task 2. `manhattan_path` from `sim/paths.py` — returns an inclusive list of orthogonally adjacent coordinates from `a` to `b`.
- Produces:
  - `generate_city(ctx: PipelineContext, style_rules: list[tuple[str, ZoneStyle]]) -> CityMap` — **the `seed` parameter is removed.**
  - `refresh(city: CityMap, new_ctx: PipelineContext, style_rules: list[tuple[str, ZoneStyle]]) -> CityMap` — **the `seed` parameter is removed.**

Task 5 updates the two call sites in `app.py`.

**Painting order matters** — later steps must not overwrite earlier ones:
1. Everything starts `GRASS`.
2. District streets: every non-odd/odd local cell in a footprint becomes `ROAD`.
3. Lots: used odd/odd local cells become `LOT`. Unused odd/odd cells stay `GRASS`.
4. Plant at `plan.plant_xy` becomes `PLANT`.
5. Arterials: `manhattan_path` from the plant to each district entry, written `POWER_LINE` **only over `GRASS`**.
6. Lineage roads: `manhattan_path` between lots in different districts, written `ROAD` **only over `GRASS`**.

- [ ] **Step 1: Write the failing tests**

Replace the entire contents of `tests/sim/test_generator.py`:

```python
from pipeline_city.catalog.models import CatalogObject, Edge, PipelineContext
from pipeline_city.sim.generator import generate_city
from pipeline_city.sim.layout import GRID_MIN
from pipeline_city.sim.tiles import TileKind, ZoneStyle

RULES = [
    ("raw|source", ZoneStyle.INDUSTRIAL),
    ("stag|int", ZoneStyle.COMMERCIAL),
    ("mart|main", ZoneStyle.RESIDENTIAL),
]


def _ctx():
    objects = (
        CatalogObject("raw", "orders", "table", 100),
        CatalogObject("raw", "customers", "table", 10),
        CatalogObject("mart", "revenue", "view", 0),
    )
    edges = (Edge(src="raw.orders", dst="mart.revenue"),)
    return PipelineContext("demo", objects, edges)


def _neighbours(city, x, y):
    out = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < city.width and 0 <= ny < city.height:
            out.append(city.tiles[ny][nx])
    return out


def test_generate_city_is_deterministic():
    ctx = _ctx()
    a = generate_city(ctx, RULES)
    b = generate_city(ctx, RULES)
    assert a.tiles == b.tiles
    assert {k: (lot.x, lot.y) for k, lot in a.lots.items()} == {
        k: (lot.x, lot.y) for k, lot in b.lots.items()
    }


def test_every_object_gets_a_lot():
    ctx = _ctx()
    city = generate_city(ctx, RULES)
    assert set(city.lots) == {o.key for o in ctx.objects}


def test_grid_is_sized_from_the_catalog_not_a_constant():
    city = generate_city(_ctx(), RULES)
    assert city.width == city.height
    assert city.width == GRID_MIN  # three objects is a village, not 128 tiles


def test_zone_style_from_rules():
    city = generate_city(_ctx(), RULES)
    assert city.lots["raw.orders"].zone_style is ZoneStyle.INDUSTRIAL
    assert city.lots["mart.revenue"].zone_style is ZoneStyle.RESIDENTIAL


def test_generator_does_not_signal_density_or_power():
    # Layout only. Density target is a placeholder and powered is False until
    # apply_signals runs.
    city = generate_city(_ctx(), RULES)
    for lot in city.lots.values():
        assert lot.target_density == 1
        assert lot.powered is False
    assert city.edge_rates == {}


def test_plant_tile_present():
    city = generate_city(_ctx(), RULES)
    px, py = city.plant_xy
    assert city.tiles[py][px] is TileKind.PLANT


def test_every_lot_borders_a_street_or_arterial():
    # The invariant the deleted full-map grid used to guarantee by brute force.
    city = generate_city(_ctx(), RULES)
    for lot in city.lots.values():
        kinds = _neighbours(city, lot.x, lot.y)
        assert TileKind.ROAD in kinds or TileKind.POWER_LINE in kinds


def test_arterials_place_the_power_line_tile():
    # The legend advertises power_line; the map must actually contain it.
    city = generate_city(_ctx(), RULES)
    flat = [kind for row in city.tiles for kind in row]
    assert TileKind.POWER_LINE in flat


def test_no_water_is_generated():
    city = generate_city(_ctx(), RULES)
    flat = [kind for row in city.tiles for kind in row]
    assert TileKind.WATER not in flat


def test_no_full_height_road_columns():
    # Regression guard on the deleted grid: no column may be road end to end.
    city = generate_city(_ctx(), RULES)
    for x in range(city.width):
        column = [city.tiles[y][x] for y in range(city.height)]
        assert not all(kind is TileKind.ROAD for kind in column)


def test_district_of_maps_every_lot_to_its_schema():
    ctx = _ctx()
    city = generate_city(ctx, RULES)
    assert city.district_of == {o.key: o.schema for o in ctx.objects}


def test_lots_of_a_schema_cluster_inside_one_footprint():
    ctx = _ctx()
    city = generate_city(ctx, RULES)
    raw = [city.lots[k] for k in ("raw.orders", "raw.customers")]
    # Both raw lots sit within a few tiles of each other, not scattered.
    assert max(abs(raw[0].x - raw[1].x), abs(raw[0].y - raw[1].y)) <= 4


def test_empty_catalog_generates_a_bare_map():
    ctx = PipelineContext("empty", (), ())
    city = generate_city(ctx, RULES)
    assert city.lots == {}
    px, py = city.plant_xy
    assert city.tiles[py][px] is TileKind.PLANT


def test_roads_list_matches_road_tiles():
    city = generate_city(_ctx(), RULES)
    from_tiles = {
        (x, y)
        for y in range(city.height)
        for x in range(city.width)
        if city.tiles[y][x] is TileKind.ROAD
    }
    assert set(city.roads) == from_tiles
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/sim/test_generator.py -v`
Expected: FAIL — `generate_city()` still requires the `seed` argument, so every test errors with `TypeError: generate_city() missing 1 required positional argument: 'seed'`.

- [ ] **Step 3: Write the minimal implementation**

Replace the entire contents of `src/pipeline_city/sim/generator.py`:

```python
import re

from ..catalog.models import PipelineContext
from .city import CityMap, Lot
from .layout import DistrictPlan, LayoutPlan, plan_layout
from .paths import manhattan_path
from .tiles import TileKind, ZoneStyle

_PLACEHOLDER_DENSITY = 1  # real target density is set later by apply_signals


def _match_style(schema: str, style_rules: list[tuple[str, ZoneStyle]]) -> ZoneStyle:
    for pattern, style in style_rules:
        if re.search(pattern, schema):
            return style
    return ZoneStyle.RESIDENTIAL


def _lot_slots(district: DistrictPlan) -> list[tuple[int, int]]:
    """Odd/odd cells of a footprint, row-major: the buildable cells."""
    return [
        (district.x + i, district.y + j)
        for j in range(1, district.size, 2)
        for i in range(1, district.size, 2)
    ]


def _street_cells(district: DistrictPlan) -> list[tuple[int, int]]:
    """Every footprint cell that is not a lot slot, i.e. the street grid."""
    return [
        (district.x + i, district.y + j)
        for j in range(district.size)
        for i in range(district.size)
        if not (i % 2 == 1 and j % 2 == 1)
    ]


def _entry_point(district: DistrictPlan, plant_xy: tuple[int, int]) -> tuple[int, int]:
    """Street cell on the footprint border nearest the plant.

    Snapped to an even local index so it lands on the street grid rather than a
    lot slot, which keeps the arterial connected to the district's roads.
    """
    px, py = plant_xy
    left, top = district.x, district.y
    right, bottom = district.x + district.size - 1, district.y + district.size - 1

    x = min(max(px, left), right)
    y = min(max(py, top), bottom)
    # Push onto the nearest border edge.
    if min(abs(px - left), abs(px - right)) <= min(abs(py - top), abs(py - bottom)):
        x = left if abs(px - left) <= abs(px - right) else right
    else:
        y = top if abs(py - top) <= abs(py - bottom) else bottom
    # Snap to an even local index (street), staying inside the footprint.
    if (x - district.x) % 2 == 1:
        x = x - 1 if x > left else x + 1
    if (y - district.y) % 2 == 1:
        y = y - 1 if y > top else y + 1
    return (x, y)


def _paint(
    tiles: list[list[TileKind]],
    path: list[tuple[int, int]],
    kind: TileKind,
) -> None:
    """Write `kind` along `path`, but only over GRASS, so nothing is clobbered."""
    for x, y in path:
        if tiles[y][x] is TileKind.GRASS:
            tiles[y][x] = kind


def _build(
    ctx: PipelineContext,
    plan: LayoutPlan,
    style_rules: list[tuple[str, ZoneStyle]],
) -> CityMap:
    tiles = [[TileKind.GRASS for _ in range(plan.grid)] for _ in range(plan.grid)]
    lots: dict[str, Lot] = {}
    district_of: dict[str, str] = {}

    for district in plan.districts:
        for x, y in _street_cells(district):
            tiles[y][x] = TileKind.ROAD

        style = _match_style(district.schema, style_rules)
        members = sorted(
            (o for o in ctx.objects if o.schema == district.schema), key=lambda o: o.key
        )
        for obj, (x, y) in zip(members, _lot_slots(district), strict=False):
            tiles[y][x] = TileKind.LOT
            lots[obj.key] = Lot(
                object_key=obj.key,
                x=x,
                y=y,
                zone_style=style,
                target_density=_PLACEHOLDER_DENSITY,
            )
            district_of[obj.key] = district.schema

    px, py = plan.plant_xy
    tiles[py][px] = TileKind.PLANT

    # Arterials: the database trunk out to each district, as POWER_LINE. This
    # places the tile the map legend advertises and separates trunk from street.
    for district in plan.districts:
        _paint(
            tiles,
            manhattan_path(plan.plant_xy, _entry_point(district, plan.plant_xy)),
            TileKind.POWER_LINE,
        )

    # Lineage roads between districts. Same-district edges already have streets.
    for edge in ctx.edges:
        src, dst = lots.get(edge.src), lots.get(edge.dst)
        if src is None or dst is None:
            continue
        if district_of[edge.src] == district_of[edge.dst]:
            continue
        _paint(tiles, manhattan_path((src.x, src.y), (dst.x, dst.y)), TileKind.ROAD)

    roads = [
        (x, y) for y in range(plan.grid) for x in range(plan.grid) if tiles[y][x] is TileKind.ROAD
    ]

    return CityMap(
        width=plan.grid,
        height=plan.grid,
        tiles=tiles,
        lots=lots,
        plant_xy=plan.plant_xy,
        roads=roads,
        district_of=district_of,
    )


def generate_city(
    ctx: PipelineContext,
    style_rules: list[tuple[str, ZoneStyle]],
) -> CityMap:
    """Lay out a catalog as districts on lineage-depth rings. Deterministic."""
    return _build(ctx, plan_layout(ctx), style_rules)


def refresh(
    city: CityMap,
    new_ctx: PipelineContext,
    style_rules: list[tuple[str, ZoneStyle]],
) -> CityMap:
    # Regenerate deterministically, carrying the current (presentation) density
    # for lots that persist so buildings do not snap. The real
    # target_density/powered/edge_rates are re-derived by the caller's Engine.
    new_city = generate_city(new_ctx, style_rules)
    for key, lot in new_city.lots.items():
        previous = city.lots.get(key)
        if previous is not None:
            lot.density = previous.density
    return new_city
```

- [ ] **Step 4: Update the refresh tests for the new signature**

In `tests/sim/test_refresh.py`, drop the seed argument from all four calls:

- line 23: `city = generate_city(ctx, RULES)`
- line 32: `new_city = refresh(city, new_ctx, RULES)`
- line 46: `city = generate_city(ctx, RULES)`
- line 54: `new_city = refresh(city, ctx, RULES)`

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/sim/ -v`
Expected: PASS.

Run: `uv run pytest -q`
Expected: PASS. `tests/test_app.py` and `tests/test_smoke.py` also call the generator — if either fails on the removed `seed` argument, fix the call there too; that is in scope for this task.

- [ ] **Step 6: Lint and commit**

```bash
cd ~/Projects/pipeline-city
uv run ruff format . && uv run ruff check .
git add src/pipeline_city/sim/generator.py tests/sim/test_generator.py tests/sim/test_refresh.py
git commit -m "feat: generate districts on lineage rings with arterials and lineage roads"
```

---

### Task 4: Make `powered` mean something

**Files:**
- Modify: `src/pipeline_city/sim/signals.py` (add a function, comment the old one)
- Modify: `src/pipeline_city/sim/channels.py:14-18` (rebind `POWERED`)
- Test: `tests/sim/test_signals.py` (extend), `tests/sim/test_channels.py` (extend)

**Interfaces:**
- Consumes: the `DataFunction` protocol in `sim/signals.py` — `name: str`, `scope: Literal["object", "edge"]`, `compute(ctx) -> dict[str, float]`. `register(fn)` adds to `REGISTRY`.
- Produces: `LineageParticipation` registered under the name `"lineage_participation"`, and `DEFAULT_BINDINGS[VisualChannel.POWERED] == "lineage_participation"`.

**Why:** `LineageReachability` seeds its traversal from every object with no incoming edge, so on an acyclic graph every object is reachable and `powered` is always `True`. The dimming path in `render/tilemap.py:66` has never fired in practice.

- [ ] **Step 1: Write the failing tests**

Append to `tests/sim/test_signals.py`:

```python
def test_lineage_participation_marks_orphans_unpowered():
    from pipeline_city.catalog.models import CatalogObject, Edge, PipelineContext
    from pipeline_city.sim.signals import REGISTRY

    ctx = PipelineContext(
        "demo",
        (
            CatalogObject("raw", "a", "table", 1),
            CatalogObject("mart", "b", "view", 1),
            CatalogObject("raw", "orphan", "table", 1),
        ),
        (Edge("raw.a", "mart.b"),),
    )
    values = REGISTRY["lineage_participation"].compute(ctx)
    assert values == {"raw.a": 1.0, "mart.b": 1.0, "raw.orphan": 0.0}


def test_lineage_participation_ignores_edges_to_unknown_objects():
    from pipeline_city.catalog.models import CatalogObject, Edge, PipelineContext
    from pipeline_city.sim.signals import REGISTRY

    ctx = PipelineContext(
        "demo",
        (CatalogObject("raw", "a", "table", 1),),
        (Edge("raw.a", "gone.b"),),
    )
    assert REGISTRY["lineage_participation"].compute(ctx) == {"raw.a": 0.0}


def test_lineage_reachability_is_always_true_on_a_dag():
    # Documents why it is unfit as the POWERED default: every node of an
    # acyclic graph traces back to some source, so nothing ever dims.
    from pipeline_city.catalog.models import CatalogObject, Edge, PipelineContext
    from pipeline_city.sim.signals import REGISTRY

    ctx = PipelineContext(
        "demo",
        (
            CatalogObject("raw", "a", "table", 1),
            CatalogObject("stg", "b", "view", 1),
            CatalogObject("mart", "c", "view", 1),
        ),
        (Edge("raw.a", "stg.b"), Edge("stg.b", "mart.c")),
    )
    values = REGISTRY["lineage_reachability"].compute(ctx)
    assert set(values.values()) == {1.0}
```

Append to `tests/sim/test_channels.py`:

```python
def test_powered_binds_to_lineage_participation():
    from pipeline_city.sim.channels import DEFAULT_BINDINGS, VisualChannel

    assert DEFAULT_BINDINGS[VisualChannel.POWERED] == "lineage_participation"


def test_apply_signals_dims_an_orphaned_object():
    from pipeline_city.catalog.models import CatalogObject, Edge, PipelineContext
    from pipeline_city.sim.channels import DEFAULT_BINDINGS, apply_signals
    from pipeline_city.sim.generator import generate_city
    from pipeline_city.sim.tiles import ZoneStyle

    rules = [("raw", ZoneStyle.INDUSTRIAL), ("mart", ZoneStyle.RESIDENTIAL)]
    ctx = PipelineContext(
        "demo",
        (
            CatalogObject("raw", "a", "table", 10),
            CatalogObject("mart", "b", "view", 5),
            CatalogObject("raw", "orphan", "table", 7),
        ),
        (Edge("raw.a", "mart.b"),),
    )
    city = generate_city(ctx, rules)
    apply_signals(city, ctx, DEFAULT_BINDINGS)

    assert city.lots["raw.a"].powered is True
    assert city.lots["mart.b"].powered is True
    assert city.lots["raw.orphan"].powered is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/sim/test_signals.py tests/sim/test_channels.py -v`
Expected: FAIL — `KeyError: 'lineage_participation'`

- [ ] **Step 3: Write the minimal implementation**

In `src/pipeline_city/sim/signals.py`, add a note to the existing class and append the new one. Change the `LineageReachability` docstring area by inserting this comment directly above `class LineageReachability:`:

```python
# Retained as a registered function and as history: it is NOT the POWERED
# default because it is always true on an acyclic graph. Every node traces back
# to some source, so only a dependency cycle could ever dim a building, and
# DuckDB does not produce one. See LineageParticipation below.
```

Then append, before the `register(...)` calls at the bottom:

```python
class LineageParticipation:
    """1.0 when an object takes part in lineage at all, 0.0 when orphaned.

    Unlike LineageReachability this can actually return 0.0, which is what
    makes the unpowered visual channel carry information.
    """

    name = "lineage_participation"
    scope: Literal["object", "edge"] = "object"

    def compute(self, ctx: PipelineContext) -> dict[str, float]:
        keys = {obj.key for obj in ctx.objects}
        connected: set[str] = set()
        for edge in ctx.edges:
            if edge.src in keys and edge.dst in keys:
                connected.add(edge.src)
                connected.add(edge.dst)
        return {k: (1.0 if k in connected else 0.0) for k in keys}
```

And add to the registrations at the bottom of the file:

```python
register(LineageParticipation())
```

In `src/pipeline_city/sim/channels.py`, change the `POWERED` binding:

```python
DEFAULT_BINDINGS: dict[VisualChannel, str] = {
    VisualChannel.DENSITY: "row_count",
    VisualChannel.POWERED: "lineage_participation",
    VisualChannel.TRAFFIC_RATE: "edge_volume",
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/sim/test_signals.py tests/sim/test_channels.py -v`
Expected: PASS.

Run: `uv run pytest -q`
Expected: PASS.

- [ ] **Step 5: Lint and commit**

```bash
cd ~/Projects/pipeline-city
uv run ruff format . && uv run ruff check .
git add src/pipeline_city/sim/signals.py src/pipeline_city/sim/channels.py \
        tests/sim/test_signals.py tests/sim/test_channels.py
git commit -m "feat: bind powered to lineage participation so orphans dim"
```

---

### Task 5: Wire up the app and cache the dim overlay

**Files:**
- Modify: `src/pipeline_city/app.py:28-45` (`_built_tiles` docstring), `app.py:68` (`refresh` call), `app.py:84` (`generate_city` call)
- Modify: `src/pipeline_city/render/tilemap.py:33-36` (`_dim_overlay` cache)
- Test: `tests/render/test_tilemap.py` (extend)

**Interfaces:**
- Consumes: `generate_city(ctx, style_rules)` and `refresh(city, new_ctx, style_rules)` from Task 3 — both without `seed`.
- Produces: a working `pipeline-city` CLI. No new public API.

**Why the cache:** `_dim_overlay(size)` allocates a fresh `pygame.Surface` for every unpowered tile on every frame (`render/tilemap.py:67`). Dimming was unreachable before Task 4 and is now live, putting that allocation on the hot path.

- [ ] **Step 1: Write the failing test**

Append to `tests/render/test_tilemap.py`:

```python
def test_dim_overlay_is_cached_per_size():
    from pipeline_city.render.tilemap import _dim_overlay

    first = _dim_overlay(32)
    second = _dim_overlay(32)
    other = _dim_overlay(48)
    assert first is second  # same size -> same surface, no per-frame allocation
    assert other is not first
    assert other.get_width() == 48
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/render/test_tilemap.py::test_dim_overlay_is_cached_per_size -v`
Expected: FAIL — `assert first is second` fails, two distinct Surfaces.

- [ ] **Step 3: Write the minimal implementation**

In `src/pipeline_city/render/tilemap.py`, replace `_dim_overlay`:

```python
_DIM_CACHE: dict[int, pygame.Surface] = {}


def _dim_overlay(size: int) -> pygame.Surface:
    """Cached dim overlay for unpowered lots, one Surface per tile size."""
    overlay = _DIM_CACHE.get(size)
    if overlay is None:
        overlay = pygame.Surface((size, size), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, _UNPOWERED_ALPHA))
        _DIM_CACHE[size] = overlay
    return overlay
```

- [ ] **Step 4: Update the app call sites**

In `src/pipeline_city/app.py` line 68, drop the seed:

```python
    state.city = refresh(state.city, new_ctx, state.theme.style_rules)
```

In `src/pipeline_city/app.py` line 84, drop the seed:

```python
    city = generate_city(ctx, theme.style_rules)
```

Replace the `_built_tiles` docstring (lines 30-39), which describes generator behaviour this plan deleted:

```python
def _built_tiles(city) -> list[tuple[int, int]]:
    """Coordinates worth framing the camera on: the lots.

    The grid is now sized to the catalog and districts cluster around the
    plant, so a lot bbox is a tight frame rather than the sliver-in-a-wasteland
    the old fixed 128-tile grid produced. Roads and the plant are still
    excluded: arterials radiate outward, so including them would widen the
    frame without adding anything worth looking at.
    """
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest -q`
Expected: PASS, all tests.

- [ ] **Step 6: Verify the real render**

```bash
cd ~/Projects/pipeline-city
uv run python scripts/screenshot.py demo.duckdb /tmp/pc-foundation/
```

Open `/tmp/pc-foundation/map.png` and confirm all five, by looking at the image:
1. No full-height grey road stripes across the map.
2. Three labelled district clusters (`raw`, `staging`, `marts`), each a compact block of buildings with streets between them, not one horizontal row.
3. The red plant tile is visible near the districts, with yellow `power_line` arterials radiating from it.
4. `raw.events` — which has no lineage at all — renders visibly dimmer than its neighbours.
5. No stray lone blue water tile.

If the districts overlap or the map is mostly empty, stop and revisit Task 2's radius maths rather than patching the generator.

- [ ] **Step 7: Lint and commit**

```bash
cd ~/Projects/pipeline-city
uv run ruff format . && uv run ruff check .
git add src/pipeline_city/app.py src/pipeline_city/render/tilemap.py tests/render/test_tilemap.py
git commit -m "feat: wire the app to the seedless generator and cache the dim overlay"
```

---

### Task 6: Update the README and docs log

**Files:**
- Modify: `README.md` ("Reading the map" and "Run" sections)
- Modify: `docs/log.md`

**Why:** the README currently claims roads are lineage (they were a static grid), and describes power lines that were never drawn. After Task 3 both become true, and the wording should say what the map now actually does.

- [ ] **Step 1: Update the README**

In `README.md`, replace the "Roads are lineage" and "The database powers the map" bullets under "Reading the map":

```markdown
- **Roads are lineage and streets.** Streets run inside each schema's area so
  every table and view is reachable. Between areas, a road exists because a
  dependency exists — the road grid is not decoration.
- **The database powers the map.** The database is the plant, and yellow
  arterials radiate from it to every schema area. A dimmed building takes no
  part in lineage at all: nothing feeds it and it feeds nothing.
- **Schema areas sit at their lineage depth.** Source schemas cluster near the
  plant; each downstream layer sits further out, so data flows outward.
```

Leave the determinism sentence under "Run" alone for now — it is still true in this phase. It becomes false only when the simulation layer ships, and the spec records that.

- [ ] **Step 2: Add a docs log entry**

Add at the top of the `# Log` list in `docs/log.md`:

```markdown
- 2026-08-03 — Phase 1 city foundation implemented on `feature/city-foundation`:
  new `sim/layout.py` (lineage depth, isolation, district planning on
  depth rings), generator rewritten to paint district streets, POWER_LINE
  arterials and cross-district lineage roads, `powered` rebound to
  `lineage_participation` so orphaned objects finally dim, random water and the
  generator's `seed` parameter removed, and the dim overlay cached. README
  updated so "roads are lineage" and the power-line description are true.
  Drag-to-pan and camera clamping were cut from the phase as throwaway ahead of
  the 3D renderer.
```

- [ ] **Step 3: Verify and commit**

```bash
cd ~/Projects/pipeline-city
uv run pytest -q
uv run ruff format . && uv run ruff check .
git add README.md docs/log.md
git commit -m "docs: describe the real map in the README and log the phase"
```

---

## Self-Review

**Spec coverage.** Walking the spec's Design section against these tasks:

| Spec requirement | Task |
|---|---|
| `compute_depths`, Kahn's, cycles at `max + 1` | 1 |
| `isolated_keys` | 1 |
| `plan_districts`, modal-depth rings, lowest-depth tie-break | 2 |
| Footprint `2 * ceil(sqrt(n)) + 1`, lots on even/streets on odd | 2 |
| Entry point = footprint tile nearest the plant | 3 (`_entry_point`) |
| `grid_size`, 256 soft target with compaction | 2 |
| Delete the unconditional column loop | 3 |
| District streets, arterials as `POWER_LINE`, lineage roads | 3 |
| Remove random water; drop the `seed` parameter | 3 |
| `refresh` keeps carrying density | 3 (unchanged behaviour, covered by `test_refresh.py`) |
| `LineageParticipation`, rebind `POWERED`, comment the old function | 4 |
| `_dim_overlay` cache | 5 |
| Camera clamping, drag-to-pan | **Cut** — recorded in Global Constraints |
| Every lot borders a road (invariant test) | 3 |
| Determinism test | 2 and 3 |
| Edge cases: empty, single, all-isolated, cyclic, 500-object | 1, 2, 3 |

Two spec items are deliberately absent: camera clamping and drag-to-pan, cut by the 2026-08-03 amendment. The "all objects isolated" edge case is covered indirectly — `test_empty_catalog_generates_a_bare_map` plus `test_lineage_participation_marks_orphans_unpowered` — rather than by a dedicated generator test, because a catalog with no edges simply produces no lineage roads, which `test_no_water_is_generated`-style absence assertions already tolerate.

**Placeholder scan.** No TBD, TODO, "handle edge cases", or "similar to Task N". Every code step carries real code. Every test step carries real assertions.

**Type consistency.** Checked across tasks: `plan_layout` returns `LayoutPlan` with `.grid`, `.plant_xy`, `.districts`; Task 3 reads exactly those. `DistrictPlan` fields `schema/ring/x/y/size` are used consistently by `_lot_slots`, `_street_cells`, and `_entry_point`. `generate_city(ctx, style_rules)` and `refresh(city, new_ctx, style_rules)` are two-and-three-arg everywhere after Task 3, including the Task 5 call sites and the Task 3 test updates. `"lineage_participation"` is spelled identically in `signals.py`, `channels.py`, and both test files.

One fix applied during review: Task 2's `plan_layout` needed the plant at the origin included in the bounding box, otherwise a single ring of districts could place the plant outside the grid after translation. The `min(min_x, 0)` / `max(max_x, 0)` lines cover it, and `test_plant_sits_inside_the_grid_and_on_no_district` asserts it.
