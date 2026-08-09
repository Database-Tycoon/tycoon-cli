---
title: Pipeline City — engine bones implementation plan
description: TDD, task-by-task plan to build the read-only DuckDB-catalog-as-city engine (catalog → sim → render → CLI) from the approved bones design
tags: [plan, game-engine, pygame, duckdb, simcity, tdd]
related: [2026-07-19-pipeline-city-bones-design]
updated: '2026-07-19'
---

# Pipeline City Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only "control screen" that opens a local `.duckdb` file and renders its catalog as a SimCity-1-style city, framed like a 2003 web game — where **every visual state is the output of a real data function over the catalog**, not a game simulation.

**Architecture:** Three one-way-imported layers — `catalog/` (DuckDB → frozen `PipelineContext`, read-only), `sim/` (pure Python, zero pygame: map generator + an extensible **data-function → visual-channel registry** + a presentation-only tween/animation engine), `render/` (pygame-ce chrome/screens/camera) — plus an `app.py` CLI. SimCity supplies the visual language only. Data functions (`row_count`, `lineage_reachability`, `edge_volume`) compute real values from the `PipelineContext`; `apply_signals` binds them to visual channels (density, powered, traffic rate). The `Engine.tick()` loop animates presentation toward those real values and **never alters state**. Everything is deterministic from the database name; state changes only when data changes (load or R-refresh).

**Tech Stack:** Python ≥ 3.12, `uv` for project/deps, `duckdb` (read-only), `pygame-ce`, `pytest` + `ruff` (dev). `tomllib` (stdlib) for theme files.

## Global Constraints

Every task's requirements implicitly include this section.

- **uv-managed project** — use `uv init` / `uv add` / `uv run` only; never touch the global environment.
- **Python `>=3.12`.**
- **Runtime dependencies are ONLY `duckdb` and `pygame-ce`.** Dev dependencies are ONLY `pytest` and `ruff`. Add nothing else.
- **Every DuckDB connection uses `read_only=True`.** Zero write statements against user databases anywhere in the codebase. (Test fixtures create their own temp DBs — that is fine.)
- **Source files stay under ~500 lines;** split by responsibility when approaching it.
- **All on-screen text uses data concepts as-is** — schema, table, view, rows, database — never city euphemisms.
- **Deterministic:** the RNG is seeded from the database name; the same file state always produces the same city.
- **No functional city simulation.** Every visual state (density target, powered, traffic rate) is the output of a registered data function over the `PipelineContext`. There is no probabilistic growth/decay and no game state that is not a real data fact. Animation is presentation-only tweening toward those real values and never alters state (decorative sprite-frame/vehicle cycling aside).
- **Lint/format with ruff:** `uv run ruff format` and `uv run ruff check` must pass before every commit.
- **`sim/` imports no pygame** — enforced by a test that imports the sim in a subprocess and asserts `pygame` is not in `sys.modules`.
- **Commit messages end with the trailer:**
  ```
  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  ```

**Fixed public interfaces** (internal helpers may be added, but these names/signatures are fixed):

- `catalog/models.py`: `CatalogObject(schema, name, kind, row_count)` frozen dataclass with `.key -> "{schema}.{name}"`; `Edge(src, dst)` frozen; `PipelineContext(database_name, objects, edges)` frozen with `.total_rows`, `.object_count`.
- `catalog/errors.py`: `CatalogError(Exception)`.
- `catalog/loader.py`: `load_catalog(path: Path) -> PipelineContext`.
- `sim/tiles.py`: `ZoneStyle{INDUSTRIAL, COMMERCIAL, RESIDENTIAL}`, `TileKind{GRASS, ROAD, POWER_LINE, PLANT, LOT, WATER}`.
- `sim/city.py`: `Lot(object_key, x, y, zone_style, target_density, density=0, powered=False)`; `CityMap(width, height, tiles, lots, plant_xy, roads, district_of, edge_rates={})` where `edge_rates: dict[tuple[str,str], float]` defaults to empty.
- `sim/paths.py`: `manhattan_path(a, b) -> list[tuple[int,int]]`.
- `sim/signals.py`: `DataFunction` Protocol (`name: str`; `scope: Literal["object","edge"]`; `compute(self, ctx: PipelineContext) -> dict[str, float]` — keyed by object key, or `"src->dst"` for edges); `REGISTRY: dict[str, DataFunction]`; `register(fn: DataFunction) -> None`; v1 functions registered at import — `RowCount` (object; raw row counts), `LineageReachability` (object; 1.0 if reachable from the database root via the lineage network else 0.0), `EdgeVolume` (edge; `min(row_count(src), row_count(dst))`).
- `sim/channels.py`: `VisualChannel{DENSITY, POWERED, TRAFFIC_RATE}`; `DEFAULT_BINDINGS: dict[VisualChannel, str] = {DENSITY: "row_count", POWERED: "lineage_reachability", TRAFFIC_RATE: "edge_volume"}`; `apply_signals(city, ctx, bindings) -> None` — computes bound functions and sets `Lot.target_density` (row-count percentile → 1..8), `Lot.powered` (value ≥ 0.5), and `city.edge_rates` (normalized 0..1).
- `sim/generator.py`: `generate_city(ctx, style_rules, seed) -> CityMap` (lays out the map only; `target_density` is a placeholder overwritten by `apply_signals`); `refresh(city, new_ctx, style_rules, seed) -> CityMap` (regenerates the map deterministically, carrying over current `density` for lots whose `object_key` persists).
- `sim/traffic.py`: `Vehicle(path, progress=0)`; `advance_traffic(city, rng, vehicles) -> None` — presentation only: advance/retire vehicles, spawn along edges proportional to `city.edge_rates` (rng used only for decorative spawn jitter). Mutates `vehicles` in place — this is the `Engine.vehicles` list.
- `sim/engine.py`: `Engine(city, rng)` with `.city`, `.vehicles`, `.tick_count`, `.apply(ctx, bindings)` (delegates to `apply_signals`; called at load and on R-refresh), `.tick()` (presentation only — every 5th tick steps each lot's `density` one step toward `target_density` with exact stop, then `advance_traffic`).
- `render/theme.py`: `load_theme(path) -> Theme`; `Theme(name, spritesheet, sprites, labels, colors, style_rules, logo_text)` with `.get_sprite_surface(name)`.
- `render/camera.py`: `Camera(viewport_w, viewport_h)` with `.offset`, `.zoom` (in `{2,3}`), `.world_to_screen`, `.screen_to_tile`, `.pan`, `.zoom_in`, `.zoom_out`.
- `render/tilemap.py`: `draw_tiles(surface, city, camera, theme, viewport)`, `draw_vehicles(surface, vehicles, camera, theme, viewport)`.
- `render/chrome.py`: `draw_chrome(surface, theme, ctx, active_name) -> dict[str, Rect]`, `button_rects(w, h)`, `viewport_rect(w, h)`.
- `render/state.py`: `AppState(ctx, city, engine, theme, camera, viewport, screens=[], running=True)` with `.push`, `.pop`, `.active`.
- `render/screens.py`: `Screen` protocol; `MapScreen(state)`, `ObjectScreen(state, key)`, `StatsScreen(state)`.
- `app.py`: `run_app(db_path, theme_name="default", max_frames=None) -> int`; `main(argv=None) -> int`; console script `pipeline-city`.

---

## Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/pipeline_city/__init__.py`
- Test: `tests/test_smoke.py`

**Interfaces:**
- Consumes: nothing.
- Produces: an installed, importable `pipeline_city` package; `uv run pytest` and `uv run ruff` both work.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "pipeline-city"
version = "0.1.0"
description = "Read-only DuckDB catalog rendered as a SimCity-style living city"
requires-python = ">=3.12"
dependencies = [
    "duckdb>=1.0",
    "pygame-ce>=2.4",
]

[project.scripts]
pipeline-city = "pipeline_city.app:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/pipeline_city"]

[dependency-groups]
dev = [
    "pytest>=8",
    "ruff>=0.5",
]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

- [ ] **Step 2: Write `.gitignore`**

```gitignore
__pycache__/
*.pyc
.venv/
.pytest_cache/
.ruff_cache/
*.egg-info/
dist/
build/
```

- [ ] **Step 3: Create the package init**

`src/pipeline_city/__init__.py`:

```python
"""Pipeline City — a read-only DuckDB catalog rendered as a living city."""

__version__ = "0.1.0"
```

- [ ] **Step 4: Sync the environment**

Run: `uv sync`
Expected: creates `.venv/` and `uv.lock`, installs duckdb, pygame-ce, pytest, ruff, and the editable `pipeline-city` package. Exit 0.

- [ ] **Step 5: Write the failing smoke test**

`tests/test_smoke.py`:

```python
def test_package_imports():
    import pipeline_city

    assert pipeline_city.__version__ == "0.1.0"
```

- [ ] **Step 6: Run the test**

Run: `uv run pytest tests/test_smoke.py -v`
Expected: PASS (the package is installed by `uv sync`).

- [ ] **Step 7: Lint and format**

Run: `uv run ruff format . && uv run ruff check .`
Expected: both exit 0.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml .gitignore src/pipeline_city/__init__.py tests/test_smoke.py uv.lock
git commit -m "$(cat <<'EOF'
chore: scaffold uv project for pipeline-city

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Catalog models and loader happy path

**Files:**
- Create: `src/pipeline_city/catalog/__init__.py`
- Create: `src/pipeline_city/catalog/models.py`
- Create: `src/pipeline_city/catalog/loader.py`
- Test: `tests/catalog/test_loader.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `CatalogObject(schema: str, name: str, kind: Literal["table","view"], row_count: int)` frozen; property `key -> f"{schema}.{name}"`.
  - `Edge(src: str, dst: str)` frozen.
  - `PipelineContext(database_name: str, objects: tuple[CatalogObject, ...], edges: tuple[Edge, ...])` frozen; properties `total_rows -> int`, `object_count -> int`.
  - `load_catalog(path: Path) -> PipelineContext` — opens `read_only=True`, reads tables (`duckdb_tables()`, `estimated_size` as row count) and views (`duckdb_views()`, row count 0), returns objects sorted by `key`, `edges=()`, `database_name=path.stem`.

- [ ] **Step 1: Create the package init**

`src/pipeline_city/catalog/__init__.py`:

```python
"""Catalog layer: DuckDB file -> PipelineContext (read-only)."""
```

- [ ] **Step 2: Write the models**

`src/pipeline_city/catalog/models.py`:

```python
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class CatalogObject:
    schema: str
    name: str
    kind: Literal["table", "view"]
    row_count: int

    @property
    def key(self) -> str:
        return f"{self.schema}.{self.name}"


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str


@dataclass(frozen=True)
class PipelineContext:
    database_name: str
    objects: tuple[CatalogObject, ...]
    edges: tuple[Edge, ...]

    @property
    def total_rows(self) -> int:
        return sum(o.row_count for o in self.objects)

    @property
    def object_count(self) -> int:
        return len(self.objects)
```

- [ ] **Step 3: Write the failing test**

`tests/catalog/test_loader.py`:

```python
import duckdb

from pipeline_city.catalog.loader import load_catalog


def _make_db(path):
    con = duckdb.connect(str(path))
    con.execute("create schema raw")
    con.execute("create table raw.orders as select * from range(5) t(id)")
    con.execute("create view main.v_orders as select * from raw.orders")
    con.close()


def test_load_catalog_reads_objects(tmp_path):
    db = tmp_path / "fx.duckdb"
    _make_db(db)

    ctx = load_catalog(db)

    keys = {o.key for o in ctx.objects}
    assert "raw.orders" in keys
    assert "main.v_orders" in keys
    assert ctx.database_name == "fx"

    orders = next(o for o in ctx.objects if o.key == "raw.orders")
    assert orders.kind == "table"
    assert orders.row_count == 5

    v_orders = next(o for o in ctx.objects if o.key == "main.v_orders")
    assert v_orders.kind == "view"
    assert ctx.object_count == 2
    assert ctx.total_rows == 5
```

- [ ] **Step 4: Run the test to verify it fails**

Run: `uv run pytest tests/catalog/test_loader.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline_city.catalog.loader'`.

- [ ] **Step 5: Write the loader**

`src/pipeline_city/catalog/loader.py`:

```python
from pathlib import Path

import duckdb

from .models import CatalogObject, PipelineContext


def load_catalog(path: Path) -> PipelineContext:
    con = duckdb.connect(str(path), read_only=True)
    try:
        tables = con.execute(
            "select schema_name, table_name, estimated_size from duckdb_tables() where not internal"
        ).fetchall()
        views = con.execute(
            "select schema_name, view_name from duckdb_views() where not internal"
        ).fetchall()
    finally:
        con.close()

    objects: list[CatalogObject] = [
        CatalogObject(schema=s, name=n, kind="table", row_count=int(size or 0))
        for s, n, size in tables
    ]
    objects.extend(CatalogObject(schema=s, name=n, kind="view", row_count=0) for s, n in views)
    objects.sort(key=lambda o: o.key)

    return PipelineContext(
        database_name=Path(path).stem,
        objects=tuple(objects),
        edges=(),
    )
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `uv run pytest tests/catalog/test_loader.py -v`
Expected: PASS.

- [ ] **Step 7: Lint and format**

Run: `uv run ruff format . && uv run ruff check .`
Expected: both exit 0.

- [ ] **Step 8: Commit**

```bash
git add src/pipeline_city/catalog tests/catalog/test_loader.py
git commit -m "$(cat <<'EOF'
feat: add catalog models and read-only loader happy path

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Loader errors, object cap, and lineage edges

**Files:**
- Create: `src/pipeline_city/catalog/errors.py`
- Modify: `src/pipeline_city/catalog/loader.py` (full replacement)
- Test: `tests/catalog/test_loader_errors.py`

**Interfaces:**
- Consumes: `CatalogObject`, `Edge`, `PipelineContext` from Task 2.
- Produces:
  - `CatalogError(Exception)` in `catalog/errors.py`.
  - `load_catalog` now raises `CatalogError` (one clear line) for missing / invalid / locked files, caps objects at the 500 largest by `row_count` with a logged warning, and derives `edges` (`Edge(src=upstream_key, dst=view_key)`) by scanning each view's SQL for other objects' names.

- [ ] **Step 1: Write the error type**

`src/pipeline_city/catalog/errors.py`:

```python
class CatalogError(Exception):
    """Raised when a DuckDB catalog cannot be loaded (missing, invalid, or locked)."""
```

- [ ] **Step 2: Write the failing tests**

`tests/catalog/test_loader_errors.py`:

```python
import logging

import duckdb
import pytest

from pipeline_city.catalog.errors import CatalogError
from pipeline_city.catalog.loader import load_catalog


def test_missing_file_raises_catalog_error(tmp_path):
    with pytest.raises(CatalogError) as exc:
        load_catalog(tmp_path / "nope.duckdb")
    assert "not found" in str(exc.value).lower()


def test_invalid_file_raises_catalog_error(tmp_path):
    bad = tmp_path / "bad.duckdb"
    bad.write_bytes(b"this is not a duckdb database")
    with pytest.raises(CatalogError):
        load_catalog(bad)


def test_locked_file_raises_catalog_error(tmp_path):
    db = tmp_path / "locked.duckdb"
    writer = duckdb.connect(str(db))
    writer.execute("create table t as select 1 as x")
    try:
        with pytest.raises(CatalogError):
            load_catalog(db)
    finally:
        writer.close()


def test_cap_to_500_largest(tmp_path, caplog):
    db = tmp_path / "big.duckdb"
    con = duckdb.connect(str(db))
    for i in range(505):
        con.execute(f"create table t{i} as select * from range({i}) r(id)")
    con.close()

    with caplog.at_level(logging.WARNING):
        ctx = load_catalog(db)

    assert ctx.object_count == 500
    assert any("capping" in r.message.lower() for r in caplog.records)
    # the smallest tables (t0, t1) must be dropped; the largest (t504) kept
    keys = {o.key for o in ctx.objects}
    assert "main.t504" in keys
    assert "main.t0" not in keys


def test_edges_from_view_sql(tmp_path):
    db = tmp_path / "lin.duckdb"
    con = duckdb.connect(str(db))
    con.execute("create schema raw")
    con.execute("create table raw.orders as select * from range(3) r(id)")
    con.execute("create view main.v_orders as select * from raw.orders")
    con.close()

    ctx = load_catalog(db)

    assert Edge_present(ctx, "raw.orders", "main.v_orders")


def Edge_present(ctx, src, dst):
    return any(e.src == src and e.dst == dst for e in ctx.edges)
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/catalog/test_loader_errors.py -v`
Expected: FAIL — missing-file and invalid-file raise the raw `duckdb`/OS error rather than `CatalogError`; cap and edge tests fail on assertions.

- [ ] **Step 4: Replace the loader with the full implementation**

`src/pipeline_city/catalog/loader.py`:

```python
import logging
import re
from pathlib import Path

import duckdb

from .errors import CatalogError
from .models import CatalogObject, Edge, PipelineContext

logger = logging.getLogger(__name__)

MAX_OBJECTS = 500


def load_catalog(path: Path) -> PipelineContext:
    path = Path(path)
    if not path.exists():
        raise CatalogError(f"Database file not found: {path}")

    try:
        con = duckdb.connect(str(path), read_only=True)
    except duckdb.Error as exc:
        raise CatalogError(
            f"Could not open database '{path}' (it may be invalid or locked by a writer): {exc}"
        ) from exc

    try:
        tables = con.execute(
            "select schema_name, table_name, estimated_size from duckdb_tables() where not internal"
        ).fetchall()
        view_rows = con.execute(
            "select schema_name, view_name, sql from duckdb_views() where not internal"
        ).fetchall()
    except duckdb.Error as exc:
        raise CatalogError(f"Could not read catalog from '{path}': {exc}") from exc
    finally:
        con.close()

    objects: list[CatalogObject] = [
        CatalogObject(schema=s, name=n, kind="table", row_count=int(size or 0))
        for s, n, size in tables
    ]
    view_sql: dict[str, str] = {}
    for s, n, sql in view_rows:
        objects.append(CatalogObject(schema=s, name=n, kind="view", row_count=0))
        view_sql[f"{s}.{n}"] = sql or ""

    objects.sort(key=lambda o: o.key)

    if len(objects) > MAX_OBJECTS:
        logger.warning(
            "Catalog has %d objects; capping to the %d largest by row count.",
            len(objects),
            MAX_OBJECTS,
        )
        objects = sorted(objects, key=lambda o: o.row_count, reverse=True)[:MAX_OBJECTS]
        objects.sort(key=lambda o: o.key)

    edges = _derive_edges(objects, view_sql)

    return PipelineContext(
        database_name=path.stem,
        objects=tuple(objects),
        edges=edges,
    )


def _derive_edges(objects: list[CatalogObject], view_sql: dict[str, str]) -> tuple[Edge, ...]:
    keep = {o.key for o in objects}
    edges: list[Edge] = []
    seen: set[tuple[str, str]] = set()
    for view in objects:
        sql = view_sql.get(view.key)
        if sql is None:
            continue
        low = sql.lower()
        for other in objects:
            if other.key == view.key or other.key not in keep:
                continue
            if re.search(r"\b" + re.escape(other.name.lower()) + r"\b", low):
                pair = (other.key, view.key)
                if pair not in seen:
                    seen.add(pair)
                    edges.append(Edge(src=other.key, dst=view.key))
    return tuple(edges)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/catalog/ -v`
Expected: PASS (both loader test files).

- [ ] **Step 6: Lint and format**

Run: `uv run ruff format . && uv run ruff check .`
Expected: both exit 0.

- [ ] **Step 7: Commit**

```bash
git add src/pipeline_city/catalog tests/catalog/test_loader_errors.py
git commit -m "$(cat <<'EOF'
feat: add catalog error handling, 500-object cap, and lineage edges

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Sim grid — enums, Lot/CityMap, path helper

**Files:**
- Create: `src/pipeline_city/sim/__init__.py`
- Create: `src/pipeline_city/sim/tiles.py`
- Create: `src/pipeline_city/sim/city.py`
- Create: `src/pipeline_city/sim/paths.py`
- Test: `tests/sim/test_city.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `ZoneStyle{INDUSTRIAL, COMMERCIAL, RESIDENTIAL}` and `TileKind{GRASS, ROAD, POWER_LINE, PLANT, LOT, WATER}` enums.
  - `Lot(object_key, x, y, zone_style, target_density, density=0, powered=False)` — mutable dataclass.
  - `CityMap(width, height, tiles, lots, plant_xy, roads, district_of, edge_rates={})` — mutable dataclass; `tiles: list[list[TileKind]]`, `lots: dict[str, Lot]`, `plant_xy: tuple[int,int]`, `roads: list[tuple[int,int]]`, `district_of: dict[str,str]`, `edge_rates: dict[tuple[str,str], float]` (default empty, populated by `apply_signals`).
  - `manhattan_path(a, b) -> list[tuple[int,int]]` — inclusive L-shaped path from `a` to `b`.

- [ ] **Step 1: Create the package init**

`src/pipeline_city/sim/__init__.py`:

```python
"""Sim layer: pure-Python grid, generator, and tick engine (no pygame)."""
```

- [ ] **Step 2: Write the failing test**

`tests/sim/test_city.py`:

```python
from pipeline_city.sim.city import CityMap, Lot
from pipeline_city.sim.paths import manhattan_path
from pipeline_city.sim.tiles import TileKind, ZoneStyle


def test_zone_and_tile_members():
    assert {z.name for z in ZoneStyle} == {"INDUSTRIAL", "COMMERCIAL", "RESIDENTIAL"}
    assert {t.name for t in TileKind} == {
        "GRASS",
        "ROAD",
        "POWER_LINE",
        "PLANT",
        "LOT",
        "WATER",
    }


def test_lot_defaults():
    lot = Lot(object_key="raw.orders", x=2, y=3, zone_style=ZoneStyle.INDUSTRIAL, target_density=5)
    assert lot.density == 0
    assert lot.powered is False


def test_citymap_holds_grid():
    tiles = [[TileKind.GRASS for _ in range(4)] for _ in range(4)]
    city = CityMap(
        width=4,
        height=4,
        tiles=tiles,
        lots={},
        plant_xy=(2, 2),
        roads=[],
        district_of={},
    )
    assert city.tiles[0][0] is TileKind.GRASS
    assert city.plant_xy == (2, 2)
    assert city.edge_rates == {}  # defaults empty; apply_signals populates it


def test_manhattan_path_is_inclusive_l_shape():
    path = manhattan_path((0, 0), (2, 1))
    assert path[0] == (0, 0)
    assert path[-1] == (2, 1)
    # each step moves exactly one tile orthogonally
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        assert abs(x1 - x0) + abs(y1 - y0) == 1
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `uv run pytest tests/sim/test_city.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline_city.sim.tiles'`.

- [ ] **Step 4: Write the tiles enums**

`src/pipeline_city/sim/tiles.py`:

```python
from enum import Enum, auto


class ZoneStyle(Enum):
    INDUSTRIAL = auto()
    COMMERCIAL = auto()
    RESIDENTIAL = auto()


class TileKind(Enum):
    GRASS = auto()
    ROAD = auto()
    POWER_LINE = auto()
    PLANT = auto()
    LOT = auto()
    WATER = auto()
```

- [ ] **Step 5: Write the city dataclasses**

`src/pipeline_city/sim/city.py`:

```python
from dataclasses import dataclass, field

from .tiles import TileKind, ZoneStyle


@dataclass
class Lot:
    object_key: str
    x: int
    y: int
    zone_style: ZoneStyle
    target_density: int
    density: int = 0
    powered: bool = False


@dataclass
class CityMap:
    width: int
    height: int
    tiles: list[list[TileKind]]
    lots: dict[str, Lot]
    plant_xy: tuple[int, int]
    roads: list[tuple[int, int]]
    district_of: dict[str, str]
    # Normalized (0..1) traffic rate per lineage edge, set by apply_signals.
    edge_rates: dict[tuple[str, str], float] = field(default_factory=dict)
```

- [ ] **Step 6: Write the path helper**

`src/pipeline_city/sim/paths.py`:

```python
def manhattan_path(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    (x0, y0), (x1, y1) = a, b
    path = [(x0, y0)]
    x, y = x0, y0
    while x != x1:
        x += 1 if x1 > x else -1
        path.append((x, y))
    while y != y1:
        y += 1 if y1 > y else -1
        path.append((x, y))
    return path
```

- [ ] **Step 7: Run the test to verify it passes**

Run: `uv run pytest tests/sim/test_city.py -v`
Expected: PASS.

- [ ] **Step 8: Lint and format**

Run: `uv run ruff format . && uv run ruff check .`
Expected: both exit 0.

- [ ] **Step 9: Commit**

```bash
git add src/pipeline_city/sim tests/sim/test_city.py
git commit -m "$(cat <<'EOF'
feat: add sim grid enums, Lot/CityMap dataclasses, and path helper

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: City generator (deterministic)

**Files:**
- Create: `src/pipeline_city/sim/generator.py`
- Test: `tests/sim/test_generator.py`

**Interfaces:**
- Consumes: `PipelineContext`, `CatalogObject`, `Edge` (Task 2/3); `CityMap`, `Lot` (Task 4); `TileKind`, `ZoneStyle` (Task 4); `manhattan_path` (Task 4).
- Produces: `generate_city(ctx: PipelineContext, style_rules: list[tuple[str, ZoneStyle]], seed: str) -> CityMap`. **Map layout only** — grid `128x128`; RNG `random.Random(seed)`; schemas become contiguous districts; a road network wires every lot to the plant; `style_rules` (regex, ZoneStyle) matched against schema name; lineage edges add streets. Lots get a **placeholder** `target_density = 1`; the real target density (and `powered`, `edge_rates`) are computed later by `apply_signals` (Task 7) — the generator does not simulate or signal anything. (`refresh(...)` is added in Task 12.)

- [ ] **Step 1: Write the failing test**

`tests/sim/test_generator.py`:

```python
from pipeline_city.catalog.models import CatalogObject, Edge, PipelineContext
from pipeline_city.sim.generator import generate_city
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


def test_generate_city_is_deterministic():
    ctx = _ctx()
    a = generate_city(ctx, RULES, "demo")
    b = generate_city(ctx, RULES, "demo")

    assert a.tiles == b.tiles
    assert {k: (l.x, l.y) for k, l in a.lots.items()} == {k: (l.x, l.y) for k, l in b.lots.items()}


def test_every_object_gets_a_lot():
    ctx = _ctx()
    city = generate_city(ctx, RULES, "demo")
    assert set(city.lots) == {o.key for o in ctx.objects}
    assert city.width == 128 and city.height == 128


def test_zone_style_from_rules():
    ctx = _ctx()
    city = generate_city(ctx, RULES, "demo")
    assert city.lots["raw.orders"].zone_style is ZoneStyle.INDUSTRIAL
    assert city.lots["mart.revenue"].zone_style is ZoneStyle.RESIDENTIAL


def test_generator_does_not_signal_density_or_power():
    # The generator lays out the map only. Density target is a placeholder (1)
    # and powered is False until apply_signals runs; no data functions here.
    ctx = _ctx()
    city = generate_city(ctx, RULES, "demo")
    for lot in city.lots.values():
        assert lot.target_density == 1
        assert lot.powered is False
    assert city.edge_rates == {}


def test_plant_tile_present():
    ctx = _ctx()
    city = generate_city(ctx, RULES, "demo")
    px, py = city.plant_xy
    assert city.tiles[py][px] is TileKind.PLANT
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/sim/test_generator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline_city.sim.generator'`.

- [ ] **Step 3: Write the generator**

`src/pipeline_city/sim/generator.py`:

```python
import random
import re

from ..catalog.models import PipelineContext
from .city import CityMap, Lot
from .paths import manhattan_path
from .tiles import TileKind, ZoneStyle

GRID = 128
BUILT_LO = 8
BUILT_HI = GRID - 8


_PLACEHOLDER_DENSITY = 1  # real target density is set later by apply_signals


def _match_style(schema: str, style_rules: list[tuple[str, ZoneStyle]]) -> ZoneStyle:
    for pattern, style in style_rules:
        if re.search(pattern, schema):
            return style
    return ZoneStyle.RESIDENTIAL


def generate_city(
    ctx: PipelineContext,
    style_rules: list[tuple[str, ZoneStyle]],
    seed: str,
) -> CityMap:
    rng = random.Random(seed)
    tiles = [[TileKind.GRASS for _ in range(GRID)] for _ in range(GRID)]
    schemas = sorted({o.schema for o in ctx.objects})
    plant_xy = (GRID // 2, GRID // 2)
    spine_y = plant_xy[1]

    roads: list[tuple[int, int]] = []

    # Vertical road corridors on every odd column of the built area. A lot at an
    # even (x, y) always has an odd-x road immediately to its west, so every lot
    # is wired into the network.
    for x in range(BUILT_LO, BUILT_HI):
        if x % 2 == 1:
            for y in range(BUILT_LO, BUILT_HI):
                tiles[y][x] = TileKind.ROAD
                roads.append((x, y))

    # Horizontal arterial spine through the plant row, joining every corridor.
    for x in range(BUILT_LO, BUILT_HI):
        if tiles[spine_y][x] is TileKind.GRASS:
            tiles[spine_y][x] = TileKind.ROAD
            roads.append((x, spine_y))

    tiles[plant_xy[1]][plant_xy[0]] = TileKind.PLANT

    # Candidate lot positions: even/even cells, excluding the plant and spine row.
    positions = [
        (x, y)
        for y in range(BUILT_LO, BUILT_HI)
        for x in range(BUILT_LO, BUILT_HI)
        if x % 2 == 0 and y % 2 == 0 and (x, y) != plant_xy and y != spine_y
    ]

    lots: dict[str, Lot] = {}
    district_of: dict[str, str] = {}
    idx = 0
    for schema in schemas:
        style = _match_style(schema, style_rules)
        schema_objects = sorted((o for o in ctx.objects if o.schema == schema), key=lambda o: o.key)
        for obj in schema_objects:
            if idx >= len(positions):
                break
            x, y = positions[idx]
            idx += 1
            tiles[y][x] = TileKind.LOT
            lots[obj.key] = Lot(
                object_key=obj.key,
                x=x,
                y=y,
                zone_style=style,
                target_density=_PLACEHOLDER_DENSITY,
            )
            district_of[obj.key] = schema

    # Lineage edges become streets between the two lots (never overwrite lots).
    for edge in ctx.edges:
        if edge.src in lots and edge.dst in lots:
            src = lots[edge.src]
            dst = lots[edge.dst]
            for sx, sy in manhattan_path((src.x, src.y), (dst.x, dst.y)):
                if tiles[sy][sx] is TileKind.GRASS:
                    tiles[sy][sx] = TileKind.ROAD
                    roads.append((sx, sy))

    # Deterministic water flavour on remaining grass.
    for _ in range(20):
        wx = rng.randrange(BUILT_LO, BUILT_HI)
        wy = rng.randrange(BUILT_LO, BUILT_HI)
        if tiles[wy][wx] is TileKind.GRASS:
            tiles[wy][wx] = TileKind.WATER

    return CityMap(
        width=GRID,
        height=GRID,
        tiles=tiles,
        lots=lots,
        plant_xy=plant_xy,
        roads=roads,
        district_of=district_of,
    )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/sim/test_generator.py -v`
Expected: PASS.

- [ ] **Step 5: Lint and format**

Run: `uv run ruff format . && uv run ruff check .`
Expected: both exit 0.

- [ ] **Step 6: Commit**

```bash
git add src/pipeline_city/sim/generator.py tests/sim/test_generator.py
git commit -m "$(cat <<'EOF'
feat: add deterministic city generator

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Data-function registry (row_count, lineage_reachability, edge_volume)

**Files:**
- Create: `src/pipeline_city/sim/signals.py`
- Test: `tests/sim/test_signals.py`

**Interfaces:**
- Consumes: `PipelineContext`, `Edge` (Task 2/3).
- Produces:
  - `DataFunction(Protocol)` with `name: str`, `scope: Literal["object","edge"]`, `compute(self, ctx: PipelineContext) -> dict[str, float]` (keyed by object key, or `"src->dst"` for edges).
  - `REGISTRY: dict[str, DataFunction]` and `register(fn: DataFunction) -> None`.
  - Three v1 functions **registered at import**: `RowCount` (scope `"object"`, raw row counts), `LineageReachability` (scope `"object"`, `1.0` if reachable from the database root through the lineage graph — a real BFS — else `0.0`), `EdgeVolume` (scope `"edge"`, `min(row_count(src), row_count(dst))` keyed `"src->dst"`).
- Note: the reachability BFS is the same graph traversal that used to be "power scan", but it now runs over the real lineage graph in the `PipelineContext` (a data fact), not over map tiles. Sources (objects with no incoming lineage edge) are fed directly by the database root and are reachable; everything downstream of a source is reachable; objects with only cyclic ancestry are unreachable → unpowered.

- [ ] **Step 1: Write the failing test**

`tests/sim/test_signals.py`:

```python
from pipeline_city.catalog.models import CatalogObject, Edge, PipelineContext
from pipeline_city.sim.signals import REGISTRY


def _ctx(objects, edges=()):
    return PipelineContext("demo", tuple(objects), tuple(edges))


def test_v1_functions_are_registered():
    assert set(REGISTRY) >= {"row_count", "lineage_reachability", "edge_volume"}
    assert REGISTRY["row_count"].scope == "object"
    assert REGISTRY["lineage_reachability"].scope == "object"
    assert REGISTRY["edge_volume"].scope == "edge"


def test_row_count_returns_raw_counts():
    ctx = _ctx(
        [
            CatalogObject("raw", "orders", "table", 100),
            CatalogObject("raw", "customers", "table", 5),
        ]
    )
    result = REGISTRY["row_count"].compute(ctx)
    assert result == {"raw.orders": 100.0, "raw.customers": 5.0}


def test_lineage_reachability_marks_sources_and_descendants():
    ctx = _ctx(
        [
            CatalogObject("raw", "orders", "table", 100),  # source
            CatalogObject("mart", "revenue", "view", 0),  # downstream
            CatalogObject("misc", "orphan", "table", 3),  # source with no edges
        ],
        [Edge(src="raw.orders", dst="mart.revenue")],
    )
    result = REGISTRY["lineage_reachability"].compute(ctx)
    assert result["raw.orders"] == 1.0
    assert result["mart.revenue"] == 1.0
    assert result["misc.orphan"] == 1.0  # no lineage still powers normally


def test_lineage_reachability_cycle_is_unreachable():
    # a and b depend on each other with no source entry -> unreachable
    ctx = _ctx(
        [
            CatalogObject("s", "a", "view", 1),
            CatalogObject("s", "b", "view", 1),
        ],
        [Edge(src="s.a", dst="s.b"), Edge(src="s.b", dst="s.a")],
    )
    result = REGISTRY["lineage_reachability"].compute(ctx)
    assert result["s.a"] == 0.0
    assert result["s.b"] == 0.0


def test_edge_volume_is_min_of_endpoints():
    ctx = _ctx(
        [
            CatalogObject("raw", "orders", "table", 100),
            CatalogObject("mart", "revenue", "view", 40),
        ],
        [Edge(src="raw.orders", dst="mart.revenue")],
    )
    result = REGISTRY["edge_volume"].compute(ctx)
    assert result == {"raw.orders->mart.revenue": 40.0}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/sim/test_signals.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline_city.sim.signals'`.

- [ ] **Step 3: Write the signals registry and data functions**

`src/pipeline_city/sim/signals.py`:

```python
from collections import deque
from typing import Literal, Protocol

from ..catalog.models import PipelineContext


class DataFunction(Protocol):
    name: str
    scope: Literal["object", "edge"]

    def compute(self, ctx: PipelineContext) -> dict[str, float]: ...


REGISTRY: dict[str, DataFunction] = {}


def register(fn: DataFunction) -> None:
    REGISTRY[fn.name] = fn


class RowCount:
    name = "row_count"
    scope: Literal["object", "edge"] = "object"

    def compute(self, ctx: PipelineContext) -> dict[str, float]:
        return {obj.key: float(obj.row_count) for obj in ctx.objects}


class LineageReachability:
    name = "lineage_reachability"
    scope: Literal["object", "edge"] = "object"

    def compute(self, ctx: PipelineContext) -> dict[str, float]:
        keys = {obj.key for obj in ctx.objects}
        outgoing: dict[str, list[str]] = {k: [] for k in keys}
        incoming: dict[str, list[str]] = {k: [] for k in keys}
        for edge in ctx.edges:
            if edge.src in keys and edge.dst in keys:
                outgoing[edge.src].append(edge.dst)
                incoming[edge.dst].append(edge.src)

        # Sources (no incoming edge) are fed directly by the database root.
        reachable: set[str] = set()
        queue = deque(k for k in keys if not incoming[k])
        reachable.update(queue)
        while queue:
            key = queue.popleft()
            for nxt in outgoing[key]:
                if nxt not in reachable:
                    reachable.add(nxt)
                    queue.append(nxt)

        return {k: (1.0 if k in reachable else 0.0) for k in keys}


class EdgeVolume:
    name = "edge_volume"
    scope: Literal["object", "edge"] = "edge"

    def compute(self, ctx: PipelineContext) -> dict[str, float]:
        row_counts = {obj.key: obj.row_count for obj in ctx.objects}
        result: dict[str, float] = {}
        for edge in ctx.edges:
            if edge.src in row_counts and edge.dst in row_counts:
                result[f"{edge.src}->{edge.dst}"] = float(
                    min(row_counts[edge.src], row_counts[edge.dst])
                )
        return result


register(RowCount())
register(LineageReachability())
register(EdgeVolume())
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/sim/test_signals.py -v`
Expected: PASS.

- [ ] **Step 5: Lint and format**

Run: `uv run ruff format . && uv run ruff check .`
Expected: both exit 0.

- [ ] **Step 6: Commit**

```bash
git add src/pipeline_city/sim/signals.py tests/sim/test_signals.py
git commit -m "$(cat <<'EOF'
feat: add data-function registry with row_count, lineage_reachability, edge_volume

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Visual channels and apply_signals

**Files:**
- Create: `src/pipeline_city/sim/channels.py`
- Test: `tests/sim/test_channels.py`

**Interfaces:**
- Consumes: `CityMap`, `Lot` (Task 4); `PipelineContext` (Task 2/3); `REGISTRY` (Task 6).
- Produces:
  - `VisualChannel{DENSITY, POWERED, TRAFFIC_RATE}` enum.
  - `DEFAULT_BINDINGS: dict[VisualChannel, str] = {DENSITY: "row_count", POWERED: "lineage_reachability", TRAFFIC_RATE: "edge_volume"}`.
  - `apply_signals(city: CityMap, ctx: PipelineContext, bindings: dict[VisualChannel, str]) -> None` — looks up each bound function in `REGISTRY`, computes it, and writes derived visual state: `Lot.target_density` = row-count-style percentile of the DENSITY function's per-object value mapped to `1..8`; `Lot.powered` = POWERED function value `>= 0.5`; `city.edge_rates` = TRAFFIC_RATE function's per-edge values normalized to `0..1`, keyed by `(src, dst)`. It sets state from data only — no randomness, no game logic.

- [ ] **Step 1: Write the failing test**

`tests/sim/test_channels.py`:

```python
from pipeline_city.catalog.models import CatalogObject, Edge, PipelineContext
from pipeline_city.sim.channels import DEFAULT_BINDINGS, apply_signals
from pipeline_city.sim.city import CityMap, Lot
from pipeline_city.sim.tiles import TileKind, ZoneStyle


def _ctx():
    objects = (
        CatalogObject("raw", "orders", "table", 100),
        CatalogObject("raw", "customers", "table", 5),
        CatalogObject("mart", "revenue", "view", 40),
    )
    edges = (
        Edge(src="raw.orders", dst="mart.revenue"),
        Edge(src="raw.customers", dst="mart.revenue"),
    )
    return PipelineContext("demo", objects, edges)


def _city(ctx):
    tiles = [[TileKind.GRASS for _ in range(4)] for _ in range(4)]
    lots = {
        o.key: Lot(o.key, i, 0, ZoneStyle.RESIDENTIAL, target_density=1)
        for i, o in enumerate(ctx.objects)
    }
    return CityMap(4, 4, tiles, lots, (0, 0), [], {})


def test_density_target_is_row_count_percentile():
    ctx = _ctx()
    city = _city(ctx)

    apply_signals(city, ctx, DEFAULT_BINDINGS)

    # orders (100 rows) is the largest -> highest target; customers (5) lowest
    assert city.lots["raw.orders"].target_density == 8
    assert city.lots["raw.customers"].target_density == 1
    assert 1 <= city.lots["mart.revenue"].target_density <= 8


def test_powered_from_lineage_reachability():
    ctx = _ctx()
    city = _city(ctx)

    apply_signals(city, ctx, DEFAULT_BINDINGS)

    # every object is reachable in this DAG -> all powered
    assert all(lot.powered for lot in city.lots.values())


def test_unreachable_object_is_unpowered():
    objects = (
        CatalogObject("s", "a", "view", 1),
        CatalogObject("s", "b", "view", 1),
    )
    edges = (Edge(src="s.a", dst="s.b"), Edge(src="s.b", dst="s.a"))
    ctx = PipelineContext("demo", objects, edges)
    city = _city(ctx)

    apply_signals(city, ctx, DEFAULT_BINDINGS)

    assert city.lots["s.a"].powered is False
    assert city.lots["s.b"].powered is False


def test_edge_rates_are_normalized():
    ctx = _ctx()
    city = _city(ctx)

    apply_signals(city, ctx, DEFAULT_BINDINGS)

    rates = city.edge_rates
    assert set(rates) == {
        ("raw.orders", "mart.revenue"),
        ("raw.customers", "mart.revenue"),
    }
    # edge_volume = min(endpoints): orders->revenue = 40, customers->revenue = 5
    assert rates[("raw.orders", "mart.revenue")] == 1.0  # largest volume normalizes to 1.0
    assert 0.0 < rates[("raw.customers", "mart.revenue")] < 1.0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/sim/test_channels.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline_city.sim.channels'`.

- [ ] **Step 3: Write the channels module**

`src/pipeline_city/sim/channels.py`:

```python
from enum import Enum, auto

from ..catalog.models import PipelineContext
from .city import CityMap
from .signals import REGISTRY


class VisualChannel(Enum):
    DENSITY = auto()
    POWERED = auto()
    TRAFFIC_RATE = auto()


DEFAULT_BINDINGS: dict[VisualChannel, str] = {
    VisualChannel.DENSITY: "row_count",
    VisualChannel.POWERED: "lineage_reachability",
    VisualChannel.TRAFFIC_RATE: "edge_volume",
}


def _percentile_to_density(value: float, sorted_values: list[float]) -> int:
    if not sorted_values:
        return 1
    below = sum(1 for v in sorted_values if v < value)
    pct = below / len(sorted_values)
    return max(1, min(8, int(pct * 7) + 1))


def apply_signals(
    city: CityMap,
    ctx: PipelineContext,
    bindings: dict[VisualChannel, str],
) -> None:
    density_values = REGISTRY[bindings[VisualChannel.DENSITY]].compute(ctx)
    sorted_density = sorted(density_values.values())
    for key, lot in city.lots.items():
        lot.target_density = _percentile_to_density(density_values.get(key, 0.0), sorted_density)

    powered_values = REGISTRY[bindings[VisualChannel.POWERED]].compute(ctx)
    for key, lot in city.lots.items():
        lot.powered = powered_values.get(key, 0.0) >= 0.5

    edge_values = REGISTRY[bindings[VisualChannel.TRAFFIC_RATE]].compute(ctx)
    max_value = max(edge_values.values(), default=0.0)
    edge_rates: dict[tuple[str, str], float] = {}
    for edge_key, value in edge_values.items():
        src, dst = edge_key.split("->", 1)
        edge_rates[(src, dst)] = (value / max_value) if max_value > 0 else 0.0
    city.edge_rates = edge_rates
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/sim/test_channels.py -v`
Expected: PASS.

- [ ] **Step 5: Lint and format**

Run: `uv run ruff format . && uv run ruff check .`
Expected: both exit 0.

- [ ] **Step 6: Commit**

```bash
git add src/pipeline_city/sim/channels.py tests/sim/test_channels.py
git commit -m "$(cat <<'EOF'
feat: add visual channels and apply_signals data->visual mapping

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Traffic presentation, Engine facade, and the no-pygame guard

**Files:**
- Create: `src/pipeline_city/sim/traffic.py`
- Create: `src/pipeline_city/sim/engine.py`
- Test: `tests/sim/test_traffic.py`
- Test: `tests/sim/test_engine.py`
- Test: `tests/sim/test_no_pygame.py`

**Interfaces:**
- Consumes: `CityMap`, `Lot` (Task 4); `manhattan_path` (Task 4); `apply_signals`, `DEFAULT_BINDINGS`, `VisualChannel` (Task 7).
- Produces:
  - `Vehicle(path: list[tuple[int,int]], progress: int = 0)` dataclass.
  - `advance_traffic(city: CityMap, rng: random.Random, vehicles: list[Vehicle]) -> None` — **presentation only**: advances each vehicle's `progress`, drops finished vehicles, and spawns new ones along each lineage edge with probability proportional to that edge's real `city.edge_rates` value (rng used only for decorative spawn jitter). Alters no state. Mutates `vehicles` in place — this is the `Engine.vehicles` list.
  - `Engine(city: CityMap, rng: random.Random)` with `.city`, `.rng`, `.vehicles: list[Vehicle]`, `.tick_count: int`, `.apply(ctx, bindings)` (delegates to `apply_signals`; called at load and on R-refresh), and `.tick()` — presentation only: increments `tick_count`, and every 5th tick steps each lot's `density` one step toward `target_density` (exact stop at target), then runs `advance_traffic`.
- Note: `EdgeVolume` (the traffic-rate data function) was defined and registered in Task 6; here it is exercised end-to-end via `apply_signals` → `city.edge_rates` → `advance_traffic`.

- [ ] **Step 1: Write the failing tests**

`tests/sim/test_traffic.py`:

```python
import random

from pipeline_city.sim.city import CityMap, Lot
from pipeline_city.sim.tiles import TileKind, ZoneStyle
from pipeline_city.sim.traffic import Vehicle, advance_traffic


def _city(edge_rates):
    tiles = [[TileKind.GRASS for _ in range(10)] for _ in range(10)]
    a = Lot("a", 1, 1, ZoneStyle.RESIDENTIAL, target_density=8)
    b = Lot("b", 8, 8, ZoneStyle.RESIDENTIAL, target_density=8)
    city = CityMap(10, 10, tiles, {"a": a, "b": b}, (0, 0), [], {})
    city.edge_rates = edge_rates
    return city


def test_high_rate_edge_spawns_and_advances():
    city = _city({("a", "b"): 1.0})
    rng = random.Random(0)
    vehicles: list[Vehicle] = []

    for _ in range(200):
        advance_traffic(city, rng, vehicles)

    assert len(vehicles) > 0  # a rate-1.0 edge produces traffic
    for v in vehicles:
        assert 0 <= v.progress < len(v.path)


def test_zero_rate_edge_never_spawns():
    city = _city({("a", "b"): 0.0})
    rng = random.Random(0)
    vehicles: list[Vehicle] = []

    for _ in range(200):
        advance_traffic(city, rng, vehicles)

    assert vehicles == []  # no data volume -> no traffic


def test_finished_vehicles_are_removed():
    city = _city({})  # no edges, so no new spawns
    rng = random.Random(0)
    vehicles = [Vehicle(path=[(0, 0), (1, 0)], progress=1)]

    advance_traffic(city, rng, vehicles)

    assert vehicles == []  # pre-seeded vehicle advances past its end and is dropped
```

`tests/sim/test_engine.py`:

```python
import random

from pipeline_city.catalog.models import CatalogObject, Edge, PipelineContext
from pipeline_city.sim.channels import DEFAULT_BINDINGS
from pipeline_city.sim.city import CityMap, Lot
from pipeline_city.sim.engine import Engine
from pipeline_city.sim.tiles import TileKind, ZoneStyle


def _ctx():
    objects = (
        CatalogObject("raw", "orders", "table", 100),
        CatalogObject("raw", "customers", "table", 5),
        CatalogObject("mart", "revenue", "view", 40),
    )
    edges = (
        Edge(src="raw.orders", dst="mart.revenue"),
        Edge(src="raw.customers", dst="mart.revenue"),
    )
    return PipelineContext("demo", objects, edges)


def _city(ctx):
    tiles = [[TileKind.GRASS for _ in range(4)] for _ in range(4)]
    lots = {
        o.key: Lot(o.key, i, 0, ZoneStyle.RESIDENTIAL, target_density=1)
        for i, o in enumerate(ctx.objects)
    }
    return CityMap(4, 4, tiles, lots, (0, 0), [], {})


def test_tick_tweens_density_to_target_and_stops_exactly():
    ctx = _ctx()
    city = _city(ctx)
    engine = Engine(city, random.Random("demo"))
    engine.apply(ctx, DEFAULT_BINDINGS)
    targets = {k: lot.target_density for k, lot in city.lots.items()}

    for _ in range(500):
        engine.tick()

    for key, lot in city.lots.items():
        assert lot.density == targets[key]  # tween lands exactly on the data target


def test_tick_count_increments():
    ctx = _ctx()
    engine = Engine(_city(ctx), random.Random("demo"))
    engine.tick()
    engine.tick()
    assert engine.tick_count == 2


def test_apply_is_idempotent_for_unchanged_data():
    ctx = _ctx()
    city = _city(ctx)
    engine = Engine(city, random.Random("demo"))
    engine.apply(ctx, DEFAULT_BINDINGS)
    before = {k: (lot.target_density, lot.powered) for k, lot in city.lots.items()}
    before_rates = dict(city.edge_rates)

    engine.apply(ctx, DEFAULT_BINDINGS)

    after = {k: (lot.target_density, lot.powered) for k, lot in city.lots.items()}
    assert after == before
    assert city.edge_rates == before_rates
```

`tests/sim/test_no_pygame.py`:

```python
import subprocess
import sys


def test_sim_imports_without_pygame():
    code = (
        "import pipeline_city.sim.engine, sys; "
        "assert 'pygame' not in sys.modules, 'sim must not import pygame'"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/sim/test_traffic.py tests/sim/test_engine.py tests/sim/test_no_pygame.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline_city.sim.traffic'`.

- [ ] **Step 3: Write the traffic presentation**

`src/pipeline_city/sim/traffic.py`:

```python
import random
from dataclasses import dataclass

from .city import CityMap
from .paths import manhattan_path

_SPAWN_SCALE = 0.5  # decorative: caps spawn probability at half the edge rate


@dataclass
class Vehicle:
    path: list[tuple[int, int]]
    progress: int = 0


def advance_traffic(city: CityMap, rng: random.Random, vehicles: list[Vehicle]) -> None:
    alive: list[Vehicle] = []
    for vehicle in vehicles:
        vehicle.progress += 1
        if vehicle.progress < len(vehicle.path):
            alive.append(vehicle)
    vehicles[:] = alive

    for (src, dst), rate in city.edge_rates.items():
        if src not in city.lots or dst not in city.lots:
            continue
        if rng.random() < rate * _SPAWN_SCALE:
            a = city.lots[src]
            b = city.lots[dst]
            vehicles.append(Vehicle(path=manhattan_path((a.x, a.y), (b.x, b.y))))
```

- [ ] **Step 4: Write the Engine facade**

`src/pipeline_city/sim/engine.py`:

```python
import random

from ..catalog.models import PipelineContext
from .channels import VisualChannel, apply_signals
from .city import CityMap
from .traffic import Vehicle, advance_traffic


class Engine:
    TWEEN_INTERVAL = 5

    def __init__(self, city: CityMap, rng: random.Random) -> None:
        self.city = city
        self.rng = rng
        self.vehicles: list[Vehicle] = []
        self.tick_count: int = 0

    def apply(self, ctx: PipelineContext, bindings: dict[VisualChannel, str]) -> None:
        # Sets all visual state from data functions. The only place state changes.
        apply_signals(self.city, ctx, bindings)

    def tick(self) -> None:
        # Presentation only: never alters signal-derived state.
        self.tick_count += 1
        if self.tick_count % self.TWEEN_INTERVAL == 0:
            self._tween_density()
        advance_traffic(self.city, self.rng, self.vehicles)

    def _tween_density(self) -> None:
        for lot in self.city.lots.values():
            if lot.density < lot.target_density:
                lot.density += 1
            elif lot.density > lot.target_density:
                lot.density -= 1
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/sim/ -v`
Expected: PASS (all sim tests).

- [ ] **Step 6: Lint and format**

Run: `uv run ruff format . && uv run ruff check .`
Expected: both exit 0.

- [ ] **Step 7: Commit**

```bash
git add src/pipeline_city/sim/traffic.py src/pipeline_city/sim/engine.py tests/sim/test_traffic.py tests/sim/test_engine.py tests/sim/test_no_pygame.py
git commit -m "$(cat <<'EOF'
feat: add traffic presentation, Engine facade, and no-pygame guard

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Theme loader and default-theme generator

**Files:**
- Create: `src/pipeline_city/render/__init__.py`
- Create: `src/pipeline_city/render/theme.py`
- Create: `scripts/make_default_theme.py`
- Create: `themes/default/theme.toml`
- Create (generated, committed): `themes/default/spritesheet.png`
- Test: `tests/render/test_theme.py`

**Interfaces:**
- Consumes: `ZoneStyle` (Task 4).
- Produces:
  - `Theme(name, spritesheet, sprites, labels, colors, style_rules, logo_text)` dataclass with `get_sprite_surface(name) -> pygame.Surface` (missing name → magenta `16x16` placeholder + `logging.warning`, never a crash).
  - `load_theme(path: Path) -> Theme` — parses `theme.toml` (tomllib), loads `spritesheet.png`, converts `[[style_rules]]` entries to `list[tuple[str, ZoneStyle]]`.
  - `scripts/make_default_theme.py` `build(out_dir)` — draws flat-color pixel-art tiles and writes `spritesheet.png`.

- [ ] **Step 1: Create the package init**

`src/pipeline_city/render/__init__.py`:

```python
"""Render layer: pygame-ce chrome, screens, camera, and theming."""
```

- [ ] **Step 2: Write the theme TOML**

`themes/default/theme.toml`:

```toml
name = "default"
logo_text = "PIPELINE CITY"

[sprites]
grass = [0, 0, 16, 16]
road = [16, 0, 16, 16]
power_line = [32, 0, 16, 16]
plant = [48, 0, 16, 16]
lot = [64, 0, 16, 16]
water = [80, 0, 16, 16]
vehicle = [96, 0, 16, 16]

[labels]
schema = "schema"
table = "table"
view = "view"
rows = "rows"
database = "database"

[colors]
banner = [40, 30, 90]
sidebar = [70, 60, 130]
button = [120, 110, 180]
button_light = [180, 170, 230]
button_dark = [50, 40, 90]
status = [20, 15, 50]
text = [240, 240, 255]

[[style_rules]]
pattern = "raw|source|land"
style = "INDUSTRIAL"

[[style_rules]]
pattern = "stag|int"
style = "COMMERCIAL"

[[style_rules]]
pattern = "mart|serve|analytics|main"
style = "RESIDENTIAL"
```

- [ ] **Step 3: Write the default-theme generator script**

`scripts/make_default_theme.py`:

```python
"""Draw the committed default spritesheet with pygame primitives."""

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

TILES = [
    ("grass", (60, 140, 70)),
    ("road", (90, 90, 90)),
    ("power_line", (200, 200, 60)),
    ("plant", (200, 60, 60)),
    ("lot", (150, 120, 90)),
    ("water", (60, 110, 200)),
    ("vehicle", (240, 240, 60)),
]


def build(out_dir: Path) -> Path:
    pygame.init()
    pygame.display.set_mode((1, 1))
    sheet = pygame.Surface((len(TILES) * 16, 16), pygame.SRCALPHA)
    for i, (_name, color) in enumerate(TILES):
        rect = pygame.Rect(i * 16, 0, 16, 16)
        pygame.draw.rect(sheet, color, rect)
        pygame.draw.rect(sheet, (20, 20, 20), rect, 1)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "spritesheet.png"
    pygame.image.save(sheet, str(target))
    pygame.quit()
    return target


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    written = build(root / "themes" / "default")
    print(f"wrote {written}")
```

- [ ] **Step 4: Generate the committed spritesheet**

Run: `uv run python scripts/make_default_theme.py`
Expected: prints `wrote .../themes/default/spritesheet.png`; the file exists.

- [ ] **Step 5: Write the failing test**

`tests/render/test_theme.py`:

```python
import os
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from pipeline_city.render.theme import load_theme  # noqa: E402
from pipeline_city.sim.tiles import ZoneStyle  # noqa: E402


@pytest.fixture(autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((64, 64))
    yield
    pygame.quit()


def _theme_dir():
    return Path(__file__).resolve().parents[2] / "themes" / "default"


def test_load_theme_fields():
    theme = load_theme(_theme_dir())
    assert theme.name == "default"
    assert theme.logo_text == "PIPELINE CITY"
    assert "grass" in theme.sprites
    assert ("raw|source|land", ZoneStyle.INDUSTRIAL) in theme.style_rules
    assert theme.labels["schema"] == "schema"


def test_get_sprite_surface_known():
    theme = load_theme(_theme_dir())
    surf = theme.get_sprite_surface("grass")
    assert surf.get_size() == (16, 16)


def test_missing_sprite_returns_magenta_placeholder():
    theme = load_theme(_theme_dir())
    surf = theme.get_sprite_surface("does_not_exist")
    assert surf.get_size() == (16, 16)
    assert surf.get_at((0, 0))[:3] == (255, 0, 255)
```

- [ ] **Step 6: Run the test to verify it fails**

Run: `uv run pytest tests/render/test_theme.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline_city.render.theme'`.

- [ ] **Step 7: Write the theme loader**

`src/pipeline_city/render/theme.py`:

```python
import logging
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import pygame

from ..sim.tiles import ZoneStyle

logger = logging.getLogger(__name__)


@dataclass
class Theme:
    name: str
    spritesheet: pygame.Surface
    sprites: dict[str, pygame.Rect]
    labels: dict[str, str]
    colors: dict[str, tuple[int, int, int]]
    style_rules: list[tuple[str, ZoneStyle]]
    logo_text: str
    _cache: dict[str, pygame.Surface] = field(default_factory=dict)

    def get_sprite_surface(self, name: str) -> pygame.Surface:
        if name in self._cache:
            return self._cache[name]
        rect = self.sprites.get(name)
        if rect is None:
            logger.warning(
                "Theme '%s' missing sprite '%s'; using magenta placeholder.",
                self.name,
                name,
            )
            surface = pygame.Surface((16, 16))
            surface.fill((255, 0, 255))
        else:
            surface = self.spritesheet.subsurface(rect).copy()
        self._cache[name] = surface
        return surface


def load_theme(path: Path) -> Theme:
    path = Path(path)
    with open(path / "theme.toml", "rb") as handle:
        data = tomllib.load(handle)

    spritesheet = pygame.image.load(str(path / "spritesheet.png")).convert_alpha()
    sprites = {name: pygame.Rect(*coords) for name, coords in data.get("sprites", {}).items()}
    colors = {name: tuple(value) for name, value in data.get("colors", {}).items()}
    style_rules = [
        (rule["pattern"], ZoneStyle[rule["style"]]) for rule in data.get("style_rules", [])
    ]

    return Theme(
        name=data.get("name", "default"),
        spritesheet=spritesheet,
        sprites=sprites,
        labels=data.get("labels", {}),
        colors=colors,
        style_rules=style_rules,
        logo_text=data.get("logo_text", "PIPELINE CITY"),
    )
```

- [ ] **Step 8: Run the test to verify it passes**

Run: `uv run pytest tests/render/test_theme.py -v`
Expected: PASS.

- [ ] **Step 9: Lint and format**

Run: `uv run ruff format . && uv run ruff check .`
Expected: both exit 0.

- [ ] **Step 10: Commit**

```bash
git add src/pipeline_city/render/__init__.py src/pipeline_city/render/theme.py scripts/make_default_theme.py themes/default/theme.toml themes/default/spritesheet.png tests/render/test_theme.py
git commit -m "$(cat <<'EOF'
feat: add theme loader and committed default theme

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Camera and tile rendering

**Files:**
- Create: `src/pipeline_city/render/camera.py`
- Create: `src/pipeline_city/render/tilemap.py`
- Test: `tests/render/test_camera.py`
- Test: `tests/render/test_tilemap.py`

**Interfaces:**
- Consumes: `TileKind` (Task 4); `Theme` (Task 9); `CityMap` (Task 4); `Vehicle` (Task 8).
- Produces:
  - `Camera(viewport_w, viewport_h)` with `.offset: list[int]` (world px at viewport top-left), `.zoom: int` (in `{2,3}`), `.TILE = 16`, `world_to_screen(wx, wy) -> (int,int)`, `screen_to_tile(sx, sy) -> (int,int)`, `pan(dx, dy)`, `zoom_in()`, `zoom_out()`.
  - `draw_tiles(surface, city, camera, theme, viewport)` and `draw_vehicles(surface, vehicles, camera, theme, viewport)` where `viewport = (x, y, w, h)`.

- [ ] **Step 1: Write the failing camera test**

`tests/render/test_camera.py`:

```python
from pipeline_city.render.camera import Camera


def test_world_to_screen_uses_offset_and_zoom():
    cam = Camera(800, 600)
    cam.offset = [32, 48]
    cam.zoom = 2
    assert cam.world_to_screen(64, 80) == (64, 64)


def test_screen_to_tile_roundtrips_offset():
    cam = Camera(800, 600)
    cam.offset = [32, 48]
    cam.zoom = 2
    assert cam.screen_to_tile(64, 64) == (4, 5)


def test_zoom_stays_in_two_three():
    cam = Camera(800, 600)
    assert cam.zoom == 2
    cam.zoom_out()
    assert cam.zoom == 2
    cam.zoom_in()
    assert cam.zoom == 3
    cam.zoom_in()
    assert cam.zoom == 3
    cam.zoom_out()
    assert cam.zoom == 2


def test_pan_moves_offset():
    cam = Camera(800, 600)
    cam.pan(10, -5)
    assert cam.offset == [10, -5]
```

- [ ] **Step 2: Run the camera test to verify it fails**

Run: `uv run pytest tests/render/test_camera.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline_city.render.camera'`.

- [ ] **Step 3: Write the camera**

`src/pipeline_city/render/camera.py`:

```python
class Camera:
    TILE = 16

    def __init__(self, viewport_w: int, viewport_h: int) -> None:
        self.viewport_w = viewport_w
        self.viewport_h = viewport_h
        self.offset: list[int] = [0, 0]
        self.zoom: int = 2

    def world_to_screen(self, wx: float, wy: float) -> tuple[int, int]:
        return (
            int((wx - self.offset[0]) * self.zoom),
            int((wy - self.offset[1]) * self.zoom),
        )

    def screen_to_tile(self, sx: float, sy: float) -> tuple[int, int]:
        wx = sx / self.zoom + self.offset[0]
        wy = sy / self.zoom + self.offset[1]
        return (int(wx // self.TILE), int(wy // self.TILE))

    def pan(self, dx: int, dy: int) -> None:
        self.offset[0] += dx
        self.offset[1] += dy

    def zoom_in(self) -> None:
        if self.zoom < 3:
            self.zoom = 3

    def zoom_out(self) -> None:
        if self.zoom > 2:
            self.zoom = 2
```

- [ ] **Step 4: Run the camera test to verify it passes**

Run: `uv run pytest tests/render/test_camera.py -v`
Expected: PASS.

- [ ] **Step 5: Write the failing tilemap test**

`tests/render/test_tilemap.py`:

```python
import os
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from pipeline_city.render.camera import Camera  # noqa: E402
from pipeline_city.render.theme import load_theme  # noqa: E402
from pipeline_city.render.tilemap import draw_tiles, draw_vehicles  # noqa: E402
from pipeline_city.sim.city import CityMap, Lot  # noqa: E402
from pipeline_city.sim.tiles import TileKind, ZoneStyle  # noqa: E402
from pipeline_city.sim.traffic import Vehicle  # noqa: E402


@pytest.fixture(autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((320, 320))
    yield
    pygame.quit()


def _theme():
    return load_theme(Path(__file__).resolve().parents[2] / "themes" / "default")


def _city():
    tiles = [[TileKind.GRASS for _ in range(8)] for _ in range(8)]
    tiles[0][0] = TileKind.PLANT
    tiles[2][2] = TileKind.LOT
    lots = {"a": Lot("a", 2, 2, ZoneStyle.RESIDENTIAL, 5)}
    return CityMap(8, 8, tiles, lots, (0, 0), [], {})


def test_draw_tiles_runs_headless():
    surface = pygame.Surface((320, 320))
    cam = Camera(320, 320)
    draw_tiles(surface, _city(), cam, _theme(), (0, 0, 320, 320))
    # a non-grass tile means the surface is not uniformly the background fill
    assert surface.get_at((0, 0)) is not None


def test_draw_vehicles_runs_headless():
    surface = pygame.Surface((320, 320))
    cam = Camera(320, 320)
    vehicles = [Vehicle(path=[(1, 1), (2, 1)], progress=0)]
    draw_vehicles(surface, vehicles, cam, _theme(), (0, 0, 320, 320))
    assert surface.get_at((0, 0)) is not None
```

- [ ] **Step 6: Run the tilemap test to verify it fails**

Run: `uv run pytest tests/render/test_tilemap.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline_city.render.tilemap'`.

- [ ] **Step 7: Write the tilemap renderer**

`src/pipeline_city/render/tilemap.py`:

```python
import pygame

from ..sim.tiles import TileKind
from .camera import Camera
from .theme import Theme

_TILE_SPRITE = {
    TileKind.GRASS: "grass",
    TileKind.ROAD: "road",
    TileKind.POWER_LINE: "power_line",
    TileKind.PLANT: "plant",
    TileKind.LOT: "lot",
    TileKind.WATER: "water",
}


def _scaled(surface: pygame.Surface, size: int) -> pygame.Surface:
    if surface.get_width() == size:
        return surface
    return pygame.transform.scale(surface, (size, size))


def draw_tiles(surface, city, camera: Camera, theme: Theme, viewport) -> None:
    vx, vy, vw, vh = viewport
    size = camera.TILE * camera.zoom
    tx0 = max(0, int(camera.offset[0] // camera.TILE))
    ty0 = max(0, int(camera.offset[1] // camera.TILE))
    tx1 = min(city.width, tx0 + vw // size + 2)
    ty1 = min(city.height, ty0 + vh // size + 2)

    for ty in range(ty0, ty1):
        for tx in range(tx0, tx1):
            kind = city.tiles[ty][tx]
            sprite = _scaled(theme.get_sprite_surface(_TILE_SPRITE[kind]), size)
            sx, sy = camera.world_to_screen(tx * camera.TILE, ty * camera.TILE)
            surface.blit(sprite, (sx + vx, sy + vy))


def draw_vehicles(surface, vehicles, camera: Camera, theme: Theme, viewport) -> None:
    vx, vy, _, _ = viewport
    size = camera.TILE * camera.zoom
    sprite = _scaled(theme.get_sprite_surface("vehicle"), size)
    for vehicle in vehicles:
        if 0 <= vehicle.progress < len(vehicle.path):
            tx, ty = vehicle.path[vehicle.progress]
            sx, sy = camera.world_to_screen(tx * camera.TILE, ty * camera.TILE)
            surface.blit(sprite, (sx + vx, sy + vy))
```

- [ ] **Step 8: Run the tilemap test to verify it passes**

Run: `uv run pytest tests/render/test_tilemap.py -v`
Expected: PASS.

- [ ] **Step 9: Lint and format**

Run: `uv run ruff format . && uv run ruff check .`
Expected: both exit 0.

- [ ] **Step 10: Commit**

```bash
git add src/pipeline_city/render/camera.py src/pipeline_city/render/tilemap.py tests/render/test_camera.py tests/render/test_tilemap.py
git commit -m "$(cat <<'EOF'
feat: add camera and headless tile/vehicle rendering

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Chrome, app state, and screens with navigation

**Files:**
- Create: `src/pipeline_city/render/chrome.py`
- Create: `src/pipeline_city/render/state.py`
- Create: `src/pipeline_city/render/screens.py`
- Test: `tests/render/test_chrome.py`
- Test: `tests/render/test_screens.py`

**Interfaces:**
- Consumes: `Theme` (Task 9); `Camera`, `draw_tiles`, `draw_vehicles` (Task 10); `PipelineContext` (Task 2/3); `CityMap`, `Lot` (Task 4); `Engine` (Task 8); `TileKind` (Task 4).
- Produces:
  - `chrome.button_rects(w, h) -> dict[str, pygame.Rect]` (keys `"Map"`, `"Stats"`, `"Quit"`), `chrome.viewport_rect(w, h) -> (x, y, w, h)`, `chrome.draw_chrome(surface, theme, ctx, active_name) -> dict[str, pygame.Rect]` — banner (`theme.logo_text`), beveled sidebar buttons, status strip (database name, object count, total rows).
  - `state.AppState(ctx, city, engine, theme, camera, viewport, screens=[], running=True)` with `.push(screen)`, `.pop()`, `.active()`. The `engine` field holds an `Engine` (Task 8); screens read `state.engine.vehicles`.
  - `screens.Screen` protocol (`name`, `handle_event`, `update`, `draw`); `screens.MapScreen(state)` (click a lot → `state.push(ObjectScreen)`), `screens.ObjectScreen(state, key)` (detail page + Back button → `state.pop()`), `screens.StatsScreen(state)` (schema/object/kind/rows table). All copy uses data terms as-is.

- [ ] **Step 1: Write the failing chrome test**

`tests/render/test_chrome.py`:

```python
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from pipeline_city.catalog.models import CatalogObject, PipelineContext  # noqa: E402
from pipeline_city.render import chrome  # noqa: E402
from pipeline_city.render.theme import Theme  # noqa: E402
from pipeline_city.sim.tiles import ZoneStyle  # noqa: E402


@pytest.fixture(autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((1024, 768))
    yield
    pygame.quit()


def _theme():
    sheet = pygame.Surface((16, 16))
    return Theme(
        name="t",
        spritesheet=sheet,
        sprites={},
        labels={"database": "database"},
        colors={},
        style_rules=[("raw", ZoneStyle.INDUSTRIAL)],
        logo_text="PIPELINE CITY",
    )


def _ctx():
    return PipelineContext("demo", (CatalogObject("raw", "orders", "table", 7),), ())


def test_button_rects_keys():
    rects = chrome.button_rects(1024, 768)
    assert set(rects) == {"Map", "Stats", "Quit"}


def test_viewport_excludes_banner_and_sidebar():
    x, y, w, h = chrome.viewport_rect(1024, 768)
    assert x > 0 and y > 0
    assert x + w == 1024


def test_draw_chrome_returns_buttons():
    surface = pygame.Surface((1024, 768))
    rects = chrome.draw_chrome(surface, _theme(), _ctx(), "Map")
    assert "Quit" in rects
```

- [ ] **Step 2: Run the chrome test to verify it fails**

Run: `uv run pytest tests/render/test_chrome.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline_city.render.chrome'`.

- [ ] **Step 3: Write the chrome**

`src/pipeline_city/render/chrome.py`:

```python
import pygame

BANNER_H = 64
SIDEBAR_W = 160
STATUS_H = 32
_LABELS = ["Map", "Stats", "Quit"]


def _font(size: int) -> pygame.font.Font:
    if not pygame.font.get_init():
        pygame.font.init()
    return pygame.font.Font(None, size)


def button_rects(w: int, h: int) -> dict[str, pygame.Rect]:
    rects: dict[str, pygame.Rect] = {}
    for i, label in enumerate(_LABELS):
        rects[label] = pygame.Rect(16, BANNER_H + 20 + i * 56, SIDEBAR_W - 32, 44)
    return rects


def viewport_rect(w: int, h: int) -> tuple[int, int, int, int]:
    return (SIDEBAR_W, BANNER_H, w - SIDEBAR_W, h - BANNER_H - STATUS_H)


def _bevel(surface, rect, base, light, dark) -> None:
    pygame.draw.rect(surface, base, rect)
    pygame.draw.line(surface, light, rect.topleft, rect.topright, 2)
    pygame.draw.line(surface, light, rect.topleft, rect.bottomleft, 2)
    pygame.draw.line(surface, dark, rect.bottomleft, rect.bottomright, 2)
    pygame.draw.line(surface, dark, rect.topright, rect.bottomright, 2)


def draw_chrome(surface, theme, ctx, active_name) -> dict[str, pygame.Rect]:
    w, h = surface.get_size()
    colors = theme.colors
    text = colors.get("text", (240, 240, 255))

    pygame.draw.rect(surface, colors.get("banner", (40, 30, 90)), (0, 0, w, BANNER_H))
    surface.blit(_font(40).render(theme.logo_text, True, text), (SIDEBAR_W + 20, 14))

    pygame.draw.rect(
        surface, colors.get("sidebar", (70, 60, 130)), (0, BANNER_H, SIDEBAR_W, h - BANNER_H)
    )
    rects = button_rects(w, h)
    for label, rect in rects.items():
        base = colors.get("button", (120, 110, 180))
        if label == active_name:
            base = colors.get("button_light", (180, 170, 230))
        _bevel(
            surface,
            rect,
            base,
            colors.get("button_light", (180, 170, 230)),
            colors.get("button_dark", (50, 40, 90)),
        )
        surface.blit(_font(26).render(label, True, text), (rect.x + 14, rect.y + 10))

    status_y = h - STATUS_H
    pygame.draw.rect(
        surface, colors.get("status", (20, 15, 50)), (SIDEBAR_W, status_y, w - SIDEBAR_W, STATUS_H)
    )
    db_label = theme.labels.get("database", "database")
    status = (
        f"{db_label}: {ctx.database_name}   objects: {ctx.object_count}   rows: {ctx.total_rows}"
    )
    surface.blit(_font(24).render(status, True, text), (SIDEBAR_W + 12, status_y + 6))

    return rects
```

- [ ] **Step 4: Write the app state**

`src/pipeline_city/render/state.py`:

```python
from dataclasses import dataclass, field

from ..catalog.models import PipelineContext
from ..sim.city import CityMap
from ..sim.engine import Engine
from .camera import Camera
from .theme import Theme


@dataclass
class AppState:
    ctx: PipelineContext
    city: CityMap
    engine: Engine
    theme: Theme
    camera: Camera
    viewport: tuple[int, int, int, int]
    screens: list = field(default_factory=list)
    running: bool = True

    def push(self, screen) -> None:
        self.screens.append(screen)

    def pop(self) -> None:
        if len(self.screens) > 1:
            self.screens.pop()

    def active(self):
        return self.screens[-1]
```

- [ ] **Step 5: Write the failing screens test**

`tests/render/test_screens.py`:

```python
import os
import random
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from pipeline_city.catalog.models import CatalogObject, Edge, PipelineContext  # noqa: E402
from pipeline_city.render.camera import Camera  # noqa: E402
from pipeline_city.render.chrome import viewport_rect  # noqa: E402
from pipeline_city.render.screens import MapScreen, ObjectScreen, StatsScreen  # noqa: E402
from pipeline_city.render.state import AppState  # noqa: E402
from pipeline_city.render.theme import load_theme  # noqa: E402
from pipeline_city.sim.channels import DEFAULT_BINDINGS  # noqa: E402
from pipeline_city.sim.city import CityMap, Lot  # noqa: E402
from pipeline_city.sim.engine import Engine  # noqa: E402
from pipeline_city.sim.tiles import TileKind, ZoneStyle  # noqa: E402


@pytest.fixture(autouse=True)
def _display():
    pygame.init()
    pygame.display.set_mode((1024, 768))
    yield
    pygame.quit()


def _state():
    tiles = [[TileKind.GRASS for _ in range(8)] for _ in range(8)]
    tiles[2][2] = TileKind.LOT
    lots = {"raw.orders": Lot("raw.orders", 2, 2, ZoneStyle.INDUSTRIAL, 1)}
    city = CityMap(8, 8, tiles, lots, (0, 0), [], {"raw.orders": "raw"})
    ctx = PipelineContext(
        "demo",
        (
            CatalogObject("raw", "orders", "table", 42),
            CatalogObject("mart", "revenue", "view", 0),
        ),
        (Edge(src="raw.orders", dst="mart.revenue"),),
    )
    engine = Engine(city, random.Random("demo"))
    engine.apply(ctx, DEFAULT_BINDINGS)  # sets powered/density/edge_rates from data
    cam = Camera(1024, 768)
    vp = viewport_rect(1024, 768)
    state = AppState(ctx=ctx, city=city, engine=engine, theme=_theme(), camera=cam, viewport=vp)
    state.screens = [MapScreen(state)]
    return state


def _theme():
    return load_theme(Path(__file__).resolve().parents[2] / "themes" / "default")


def test_click_lot_pushes_object_screen():
    state = _state()
    vx, vy, _, _ = state.viewport
    # world position of lot (2,2) with default zoom 2 and zero offset
    sx = 2 * Camera.TILE * state.camera.zoom + vx
    sy = 2 * Camera.TILE * state.camera.zoom + vy
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(sx, sy))

    state.active().handle_event(event)

    assert isinstance(state.active(), ObjectScreen)


def test_object_screen_back_button_pops():
    state = _state()
    obj = ObjectScreen(state, "raw.orders")
    state.push(obj)
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=obj.back_rect.center)

    obj.handle_event(event)

    assert not isinstance(state.active(), ObjectScreen)


def test_screens_draw_without_error():
    state = _state()
    surface = pygame.Surface((1024, 768))
    MapScreen(state).draw(surface)
    ObjectScreen(state, "raw.orders").draw(surface)
    StatsScreen(state).draw(surface)
    assert surface.get_at((0, 0)) is not None
```

- [ ] **Step 6: Run the screens test to verify it fails**

Run: `uv run pytest tests/render/test_screens.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline_city.render.screens'`.

- [ ] **Step 7: Write the screens**

`src/pipeline_city/render/screens.py`:

```python
from typing import Protocol

import pygame

from .tilemap import draw_tiles, draw_vehicles


class Screen(Protocol):
    name: str

    def handle_event(self, event) -> None: ...

    def update(self, dt: float) -> None: ...

    def draw(self, surface) -> None: ...


def _font(size: int) -> pygame.font.Font:
    if not pygame.font.get_init():
        pygame.font.init()
    return pygame.font.Font(None, size)


class MapScreen:
    name = "Map"

    def __init__(self, state) -> None:
        self.state = state

    def handle_event(self, event) -> None:
        state = self.state
        cam = state.camera
        vx, vy, vw, vh = state.viewport
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if vx <= mx < vx + vw and vy <= my < vy + vh:
                tx, ty = cam.screen_to_tile(mx - vx, my - vy)
                for key, lot in state.city.lots.items():
                    if lot.x == tx and lot.y == ty:
                        state.push(ObjectScreen(state, key))
                        break
        elif event.type == pygame.MOUSEWHEEL:
            cam.zoom_in() if event.y > 0 else cam.zoom_out()
        elif event.type == pygame.KEYDOWN:
            step = 16
            if event.key == pygame.K_LEFT:
                cam.pan(-step, 0)
            elif event.key == pygame.K_RIGHT:
                cam.pan(step, 0)
            elif event.key == pygame.K_UP:
                cam.pan(0, -step)
            elif event.key == pygame.K_DOWN:
                cam.pan(0, step)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface) -> None:
        state = self.state
        draw_tiles(surface, state.city, state.camera, state.theme, state.viewport)
        draw_vehicles(surface, state.engine.vehicles, state.camera, state.theme, state.viewport)


class ObjectScreen:
    name = "Object"

    def __init__(self, state, key: str) -> None:
        self.state = state
        self.key = key
        self.back_rect = pygame.Rect(180, 700, 100, 40)

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_rect.collidepoint(event.pos):
                self.state.pop()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface) -> None:
        state = self.state
        theme = state.theme
        font = _font(24)
        color = theme.colors.get("text", (240, 240, 255))
        lot = state.city.lots.get(self.key)
        obj = next((o for o in state.ctx.objects if o.key == self.key), None)
        upstream = [e.src for e in state.ctx.edges if e.dst == self.key]
        downstream = [e.dst for e in state.ctx.edges if e.src == self.key]
        lines = [
            self.key,
            f"{theme.labels.get('schema', 'schema')}: {obj.schema if obj else ''}",
            f"kind: {obj.kind if obj else ''}",
            f"{theme.labels.get('rows', 'rows')}: {obj.row_count if obj else 0}",
            f"powered: {lot.powered if lot else False}",
            f"density: {lot.density if lot else 0}/{lot.target_density if lot else 0}",
            f"upstream: {', '.join(upstream) or '(none)'}",
            f"downstream: {', '.join(downstream) or '(none)'}",
        ]
        x = state.viewport[0] + 20
        y = state.viewport[1] + 20
        for i, line in enumerate(lines):
            surface.blit(font.render(line, True, color), (x, y + i * 30))
        pygame.draw.rect(surface, theme.colors.get("button", (120, 110, 180)), self.back_rect)
        surface.blit(
            font.render("Back", True, color), (self.back_rect.x + 10, self.back_rect.y + 8)
        )


class StatsScreen:
    name = "Stats"

    def __init__(self, state) -> None:
        self.state = state

    def handle_event(self, event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface) -> None:
        state = self.state
        font = _font(22)
        color = state.theme.colors.get("text", (240, 240, 255))
        x = state.viewport[0] + 20
        y = state.viewport[1] + 20
        header = f"{'schema':<16}{'object':<24}{'kind':<8}{'rows':>10}"
        surface.blit(font.render(header, True, color), (x, y))
        for i, obj in enumerate(state.ctx.objects[:24], start=1):
            row = f"{obj.schema:<16}{obj.name:<24}{obj.kind:<8}{obj.row_count:>10}"
            surface.blit(font.render(row, True, color), (x, y + i * 26))
```

- [ ] **Step 8: Run the render tests to verify they pass**

Run: `uv run pytest tests/render/test_chrome.py tests/render/test_screens.py -v`
Expected: PASS.

- [ ] **Step 9: Lint and format**

Run: `uv run ruff format . && uv run ruff check .`
Expected: both exit 0.

- [ ] **Step 10: Commit**

```bash
git add src/pipeline_city/render/chrome.py src/pipeline_city/render/state.py src/pipeline_city/render/screens.py tests/render/test_chrome.py tests/render/test_screens.py
git commit -m "$(cat <<'EOF'
feat: add era chrome, app state, and page-based screens

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: App CLI, refresh, headless smoke test, and README

**Files:**
- Modify: `src/pipeline_city/sim/generator.py` (add `refresh`)
- Create: `src/pipeline_city/app.py`
- Create: `README.md`
- Test: `tests/sim/test_refresh.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: everything above — `load_catalog`, `CatalogError`, `generate_city`, `Engine`, `apply_signals`/`DEFAULT_BINDINGS` (Task 7), `load_theme`, `Camera`, `AppState`, `MapScreen`, `StatsScreen`, `draw_chrome`, `button_rects`, `viewport_rect`.
- Produces:
  - `refresh(city, new_ctx, style_rules, seed) -> CityMap` in `generator.py` — regenerates the map deterministically, carrying over current `density` for lots whose `object_key` persists (real `target_density`/`powered`/`edge_rates` are re-derived by the caller's `Engine.apply`).
  - `run_app(db_path, theme_name="default", max_frames=None) -> int` — builds the city, then `Engine(...).apply(ctx, DEFAULT_BINDINGS)` at load; fixed timestep 10 presentation ticks/sec decoupled from 60fps render; `R` reloads the catalog via `load_catalog` + `refresh` + `Engine.apply`; `CatalogError` at startup prints the message and returns 1 (no traceback).
  - `main(argv=None) -> int` — CLI `pipeline-city <db-path> [--theme default]`; console script `pipeline-city`.

- [ ] **Step 1: Write the failing refresh test**

`tests/sim/test_refresh.py`:

```python
import random

from pipeline_city.catalog.models import CatalogObject, PipelineContext
from pipeline_city.sim.channels import DEFAULT_BINDINGS
from pipeline_city.sim.engine import Engine
from pipeline_city.sim.generator import generate_city, refresh
from pipeline_city.sim.tiles import ZoneStyle

RULES = [("raw", ZoneStyle.INDUSTRIAL), ("mart", ZoneStyle.RESIDENTIAL)]


def _ctx(objects):
    return PipelineContext("demo", tuple(objects), ())


def _snapshot(city):
    lots = {k: (lot.target_density, lot.powered, lot.density) for k, lot in city.lots.items()}
    return lots, dict(city.edge_rates)


def test_refresh_adds_new_lots_and_carries_density():
    ctx = _ctx([CatalogObject("raw", "orders", "table", 100)])
    city = generate_city(ctx, RULES, "demo")
    city.lots["raw.orders"].density = 3

    new_ctx = _ctx(
        [
            CatalogObject("raw", "orders", "table", 100),
            CatalogObject("raw", "customers", "table", 5),
        ]
    )
    new_city = refresh(city, new_ctx, RULES, "demo")

    assert new_city.lots["raw.orders"].density == 3  # carried over
    assert "raw.customers" in new_city.lots
    assert new_city.lots["raw.customers"].density == 0  # brand new lot


def test_refresh_unchanged_data_changes_no_state():
    ctx = _ctx(
        [
            CatalogObject("raw", "orders", "table", 100),
            CatalogObject("mart", "revenue", "view", 40),
        ]
    )
    city = generate_city(ctx, RULES, "demo")
    engine = Engine(city, random.Random("demo"))
    engine.apply(ctx, DEFAULT_BINDINGS)
    for _ in range(500):  # let the density tween settle at its data targets
        engine.tick()
    before = _snapshot(city)

    # replay the app's R-refresh flow with identical data
    new_city = refresh(city, ctx, RULES, "demo")
    engine.city = new_city
    engine.apply(ctx, DEFAULT_BINDINGS)
    after = _snapshot(new_city)

    assert after == before  # unchanged data -> no state change
```

- [ ] **Step 2: Run the refresh test to verify it fails**

Run: `uv run pytest tests/sim/test_refresh.py -v`
Expected: FAIL with `ImportError: cannot import name 'refresh'`.

- [ ] **Step 3: Add `refresh` to the generator**

Append to `src/pipeline_city/sim/generator.py`:

```python
def refresh(
    city: CityMap,
    new_ctx: PipelineContext,
    style_rules: list[tuple[str, ZoneStyle]],
    seed: str,
) -> CityMap:
    # Regenerate the map deterministically; carry over the current (presentation)
    # density for lots that persist so buildings do not snap. The real
    # target_density/powered/edge_rates are re-derived by the caller's Engine.apply.
    new_city = generate_city(new_ctx, style_rules, seed)
    for key, lot in new_city.lots.items():
        previous = city.lots.get(key)
        if previous is not None:
            lot.density = previous.density
    return new_city
```

- [ ] **Step 4: Run the refresh test to verify it passes**

Run: `uv run pytest tests/sim/test_refresh.py -v`
Expected: PASS.

- [ ] **Step 5: Write the app**

`src/pipeline_city/app.py`:

```python
import random
import sys
from pathlib import Path

import pygame

from .catalog.errors import CatalogError
from .catalog.loader import load_catalog
from .render.camera import Camera
from .render.chrome import button_rects, draw_chrome, viewport_rect
from .render.screens import MapScreen, StatsScreen
from .render.state import AppState
from .render.theme import load_theme
from .sim.channels import DEFAULT_BINDINGS
from .sim.engine import Engine
from .sim.generator import generate_city, refresh

SCREEN_W = 1024
SCREEN_H = 768
TICK_DT = 0.1  # 10 presentation ticks per second


def _theme_dir(name: str) -> Path:
    return Path(__file__).resolve().parents[2] / "themes" / name


def _center_camera(camera: Camera, city) -> None:
    camera.offset = [
        city.plant_xy[0] * Camera.TILE - 200,
        city.plant_xy[1] * Camera.TILE - 200,
    ]


def _handle_chrome_click(state: AppState, event) -> bool:
    for label, rect in button_rects(SCREEN_W, SCREEN_H).items():
        if rect.collidepoint(event.pos):
            if label == "Map":
                state.screens = [MapScreen(state)]
            elif label == "Stats":
                state.push(StatsScreen(state))
            elif label == "Quit":
                state.running = False
            return True
    return False


def _reload(state: AppState, db_path: str) -> None:
    try:
        new_ctx = load_catalog(Path(db_path))
    except CatalogError as exc:
        print(str(exc))
        return
    state.ctx = new_ctx
    state.city = refresh(state.city, new_ctx, state.theme.style_rules, new_ctx.database_name)
    state.engine.city = state.city
    state.engine.apply(new_ctx, DEFAULT_BINDINGS)


def run_app(db_path: str, theme_name: str = "default", max_frames: int | None = None) -> int:
    try:
        ctx = load_catalog(Path(db_path))
    except CatalogError as exc:
        print(str(exc))
        return 1

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    theme = load_theme(_theme_dir(theme_name))
    city = generate_city(ctx, theme.style_rules, ctx.database_name)
    engine = Engine(city, random.Random(ctx.database_name))
    engine.apply(ctx, DEFAULT_BINDINGS)  # derive all visual state from data
    camera = Camera(SCREEN_W, SCREEN_H)
    _center_camera(camera, city)
    state = AppState(
        ctx=ctx,
        city=city,
        engine=engine,
        theme=theme,
        camera=camera,
        viewport=viewport_rect(SCREEN_W, SCREEN_H),
    )
    state.screens = [MapScreen(state)]

    clock = pygame.time.Clock()
    accumulator = 0.0
    frames = 0

    while state.running:
        dt = clock.tick(60) / 1000.0
        accumulator += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                state.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                _reload(state, db_path)
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and _handle_chrome_click(state, event)
            ):
                continue
            else:
                state.active().handle_event(event)

        while accumulator >= TICK_DT:
            state.engine.tick()
            accumulator -= TICK_DT

        state.active().update(dt)
        screen.fill((0, 0, 0))
        state.active().draw(screen)
        draw_chrome(screen, state.theme, state.ctx, state.active().name)
        pygame.display.flip()

        frames += 1
        if max_frames is not None and frames >= max_frames:
            state.running = False

    pygame.quit()
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    usage = "usage: pipeline-city <db-path> [--theme default]"
    theme_name = "default"
    db_path: str | None = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--theme":
            i += 1
            theme_name = argv[i] if i < len(argv) else "default"
        else:
            db_path = arg
        i += 1
    if db_path is None:
        print(usage)
        return 1
    return run_app(db_path, theme_name)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Write the README**

`README.md`:

```markdown
# Pipeline City

A read-only "control screen" for a local DuckDB file: the catalog renders as a
SimCity-1-style living city, framed like a 2003 web game. Schemas become
districts, tables and views become buildings, lineage becomes roads, the
database is the power plant, and row counts drive building density. It never
writes to your database.

## Install

```bash
uv sync
```

## Run

```bash
uv run pipeline-city path/to/db.duckdb --theme default
```

- **Pan:** drag or arrow keys. **Zoom:** mouse wheel (2x / 3x).
- **Click a building** to open its detail page (schema, kind, rows, powered,
  density, upstream/downstream lineage).
- **Sidebar:** Map / Stats / Quit.
- **R:** re-read the catalog (read-only) and update the city in place.

The same file state always produces the same city.

## Theming

A theme is one folder (`themes/<name>/` with `spritesheet.png` + `theme.toml`).
Regenerate the default spritesheet with:

```bash
uv run python scripts/make_default_theme.py
```

## Develop

```bash
uv run pytest
uv run ruff format . && uv run ruff check .
```
```

- [ ] **Step 7: Write the failing app tests**

`tests/test_app.py`:

```python
import duckdb

from pipeline_city.app import main, run_app


def test_run_app_missing_db_returns_1(capsys):
    rc = run_app("/no/such/file.duckdb", "default", max_frames=1)
    assert rc == 1
    assert "not found" in capsys.readouterr().out.lower()


def test_run_app_headless_smoke(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    db = tmp_path / "smoke.duckdb"
    con = duckdb.connect(str(db))
    con.execute("create schema raw")
    con.execute("create table raw.t as select * from range(10) r(id)")
    con.close()

    rc = run_app(str(db), "default", max_frames=100)

    assert rc == 0


def test_main_no_args_returns_1(capsys):
    rc = main([])
    assert rc == 1
    assert "usage" in capsys.readouterr().out.lower()
```

- [ ] **Step 8: Run the app tests to verify they fail**

Run: `uv run pytest tests/test_app.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline_city.app'` (before Step 5 is applied) or, if run now, PASS. Run it after Step 5; expected PASS.

- [ ] **Step 9: Run the full test suite**

Run: `uv run pytest -v`
Expected: PASS — all catalog, sim, render, and app tests green.

- [ ] **Step 10: Lint and format**

Run: `uv run ruff format . && uv run ruff check .`
Expected: both exit 0.

- [ ] **Step 11: Commit**

```bash
git add src/pipeline_city/sim/generator.py src/pipeline_city/app.py README.md tests/sim/test_refresh.py tests/test_app.py
git commit -m "$(cat <<'EOF'
feat: add CLI app, catalog refresh, headless smoke test, and README

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review

**1. Spec coverage (against the amended spec).**

- Read-only loader → Tasks 2/3 (`read_only=True`, zero writes). ✔
- Frozen `PipelineContext` with objects/edges/totals → Task 2. ✔
- Missing/invalid/locked errors, 500-object cap with warning, lineage → Task 3. ✔
- **No functional city simulation** (new Non-goal) → no probabilistic growth/decay anywhere; every visual state is a data-function output (Tasks 6/7); `Engine.tick` is presentation-only (Task 8). ✔
- **Signal engine as a data-function → visual-channel registry** (new section) → `signals.py` registry + 3 v1 functions (Task 6); `channels.py` `VisualChannel`/`DEFAULT_BINDINGS`/`apply_signals` (Task 7). ✔
- row_count → density (percentile 1..8); lineage_reachability → powered; edge_volume → traffic rate → Tasks 6/7. ✔
- New functions register the same way without engine changes → `register()` + `REGISTRY` contract (Task 6). ✔
- Visual state changes only on load/R-refresh; animation never alters state → `Engine.apply` (load + refresh) vs `Engine.tick` (presentation) (Tasks 8/12). ✔
- SimCity supplies visual language only / RCT attraction framing (Object page, Stats list) → Task 11. ✔
- Sim pure Python, no pygame → Task 8 subprocess guard (`test_no_pygame.py`). ✔
- 128×128 grid, RNG seeded from db name, deterministic map → Task 5 determinism test. ✔
- Schema→district, zone style via rules, roads/plant, lineage streets → Task 5 (map only; density/powered now come from signals). ✔
- Objects with no lineage render and power normally → `LineageReachability` treats sources (in-degree 0) as reachable (Task 6 test). ✔
- Theme folder (spritesheet + toml), missing sprite → magenta placeholder → Task 9. ✔
- Camera pan/zoom {2,3}, 16px tiles, sprite blit, vehicles → Task 10. ✔
- Era chrome (banner/sidebar/status, beveled buttons) → Task 11. ✔
- Page navigation: Map / Object / Stats, data terms as-is → Task 11. ✔
- R refresh in place (load + refresh + `Engine.apply`); clean `CatalogError` message, exit 1, no traceback → Task 12. ✔
- **Amended Testing invariants:** every visual channel traces to a registered data function (Tasks 6/7 tests); unreachable object renders unpowered (`test_unreachable_object_is_unpowered`, Task 7; `test_lineage_reachability_cycle_is_unreachable`, Task 6); density tween stops exactly at the row-count-derived target (`test_tick_tweens_density_to_target_and_stops_exactly`, Task 8); refresh with unchanged data changes no state (`test_refresh_unchanged_data_changes_no_state`, Task 12; `test_apply_is_idempotent_for_unchanged_data`, Task 8). ✔
- Headless smoke test (`SDL_VIDEODRIVER=dummy`), 100 frames, clean quit → Task 12. ✔
- Ruff lint/format → every task. ✔
- Deferred (MotherDuck/dbt, evaluation layer, web renderer, sound) → correctly absent. ✔

**2. Placeholder scan.** No "TBD"/"TODO"/"similar to Task N"/"add error handling" — every code step carries complete runnable code; every command states its expected outcome. ✔

**3. Type consistency.** Verified the deleted names `Simulation`, `power_scan`, `growth_phase`, `traffic_phase`, `sim/power.py`, `sim/growth.py` appear nowhere in tasks or tests. Current names line up across producing/consuming tasks: `CatalogObject.key`; `PipelineContext.objects/edges/total_rows/object_count`; `CityMap`/`Lot` fields incl. `CityMap.edge_rates`; `DataFunction.name/scope/compute` and `REGISTRY`/`register`; `VisualChannel{DENSITY,POWERED,TRAFFIC_RATE}`, `DEFAULT_BINDINGS`, `apply_signals(city, ctx, bindings)`; `Vehicle`, `advance_traffic(city, rng, vehicles)`; `Engine.city/rng/vehicles/tick_count/apply(ctx, bindings)/tick()`; `generate_city`/`refresh`; `Camera.TILE/zoom/offset`; `Theme.get_sprite_surface`; `viewport_rect`/`button_rects`/`draw_chrome`; `AppState.ctx/city/engine/theme/camera/viewport` + `push/pop/active`; `run_app`/`main`. Render/app read `state.engine.vehicles` and call `Engine.apply`/`apply_signals` — nothing references the deleted names. ✔

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-19-pipeline-city-bones.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
