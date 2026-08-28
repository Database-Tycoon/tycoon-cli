from dataclasses import dataclass, field

from .layout import DistrictPlan, StreetFeature
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
    # Ground plan in tiles; (x, y) stays the NW anchor. Big tables (the top
    # decile of the catalog's row counts) get 2x2; everything else 1x1.
    w: int = 1
    h: int = 1
    # Temporal signals (Phase F), written by apply_signals from run history.
    # None means UNKNOWN, and unknown must never render as stale/broken --
    # dogfood's common case is a catalog with no recent runs at all.
    last_build_age_s: float | None = None
    build_status: str | None = None
    test_status: str | None = None
    freshness_status: str | None = None  # dbt's SLA verdict: pass/warn/error
    schema_drift_age_s: float | None = None  # seconds since the schema changed


@dataclass
class CityMap:
    width: int
    height: int
    tiles: list[list[TileKind]]
    lots: dict[str, Lot]
    plant_xy: tuple[int, int]
    district_of: dict[str, str]
    # Normalized (0..1) traffic rate per lineage edge, set by apply_signals.
    edge_rates: dict[tuple[str, str], float] = field(default_factory=dict)
    # The plan the generator laid this map out from. Carried so a renderer can
    # draw district footprints and rings; the tile grid alone cannot express
    # them, and re-deriving via plan_layout(ctx) would be a hidden
    # two-calls-must-agree coupling. Trailing default keeps hand-built CityMaps
    # in tests valid.
    districts: tuple[DistrictPlan, ...] = ()
    # Streets ARE the lineage: the exact tile path each edge's street takes,
    # lot to lot. The renderer's traffic drives these instead of approximating.
    edge_routes: dict[tuple[str, str], tuple[tuple[int, int], ...]] = field(default_factory=dict)
    # Civic buildings (None on hand-built maps): the public library holds the
    # city's context/documentation; the firehouse dispatches fire response.
    library_xy: tuple[int, int] | None = None
    firehouse_xy: tuple[int, int] | None = None
    # Streets v4: how every road is allowed to end — an apron, a dock or a
    # plaza at each route endpoint. Carried from the plan because the tile grid
    # cannot express it: a ROAD tile says nothing about which building it
    # serves, which way it faces, or that it is a paved forecourt.
    street_features: tuple[StreetFeature, ...] = ()
