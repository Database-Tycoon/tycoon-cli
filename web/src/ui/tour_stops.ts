/**
 * Tour stop definitions and semantic helpers.
 *
 * The stop list is data, not logic. The Tour class (in tour.ts) is the
 * state machine that walks stops. Keeping the stops in a separate file
 * makes it easy to audit the full tour without reading the class.
 *
 * TWO RULES MATTER MORE THAN THE COPY (see tour.ts for the full explanation).
 */

import type { CityDocument } from "../contract";
import type { Lens, OverlayId } from "./lenses";
import { DRIFT_RECENT_S } from "./health";
import { PLANT_KEY } from "../scene/plant";
import { FIREHOUSE_KEY, LIBRARY_KEY } from "../scene/civic";

const lotsIn = (doc: CityDocument, schema: string): string[] =>
  doc.lots
    .map((l) => l.object_key)
    .filter((k) => k.startsWith(`${schema}.`))
    .sort();

/** The first object in a schema, or null when the district holds none. */
const firstIn = (doc: CityDocument, schema: string): string | null => lotsIn(doc, schema)[0] ?? null;

const firstLot = (doc: CityDocument, match: (lot: CityDocument["lots"][number]) => boolean) =>
  doc.lots.filter(match).sort((a, b) => a.object_key.localeCompare(b.object_key))[0] ?? null;

const burning = (doc: CityDocument) => firstLot(doc, (l) => l.test_status === "fail");
const worn = (doc: CityDocument) =>
  firstLot(doc, (l) => l.freshness_status === "warn" || l.freshness_status === "error");
const drifting = (doc: CityDocument) =>
  firstLot(doc, (l) => l.schema_drift_age_s !== null && l.schema_drift_age_s < DRIFT_RECENT_S);
const routed = (doc: CityDocument) => doc.edges.filter((e) => e.route.length > 0)[0] ?? null;
const busiest = (doc: CityDocument) =>
  doc.edges
    .filter((e) => e.daily_load_s !== null && e.daily_load_s > 0)
    .sort((a, b) => b.daily_load_s! - a.daily_load_s!)[0] ?? null;
const fogged = (doc: CityDocument) =>
  (doc.weather?.cells ?? []).filter((c) => c.condition !== "clear");

const days = (seconds: number): number => Math.round(seconds / 86400);

export const TOUR_STOPS: readonly import("./tour").TourStop[] = [
  {
    id: "view",
    title: "You are looking at a 3D city",
    requires: () => true,
    body: () =>
      `This is a three-dimensional city — not a 2D map or a static diagram. ` +
      `Drag to orbit, scroll to zoom, click a building to inspect it. ` +
      `Arrow keys (or WASD) move the camera; press F to fly through it, ` +
      `H to reframe, R to re-read the catalog. Nothing here is a mockup: ` +
      `every building, street, and signal is measured from the real document.`,
  },
  {
    id: "lenses",
    title: "Four lenses, one city",
    requires: () => true,
    body: () =>
      `Four presets re-weight the SAME city for the job you do: data engineer ` +
      `(build errors and street load), analytics engineer (failing tests and ` +
      `documentation), on-call responder (fires and freshness), and data lead ` +
      `(cost, context, quiet). Switch with the footer picker or ` +
      `?lens=<name>. A lens never invents numbers — chips, gauges, and ` +
      `overlays just change order and defaults.`,
  },
  {
    id: "districts",
    title: "Schemas are districts",
    requires: (doc) => doc.districts.length > 0 && doc.lots.length > 0,
    body: (doc) =>
      `Every schema is its own neighbourhood — ${doc.districts.length} here: ` +
      `${doc.districts.map((d) => d.schema).join(", ")}. Each building is a table or a ` +
      `view, and its height is its row count. Nothing on this map is decoration.`,
    target: (doc) => firstIn(doc, doc.districts[0]!.schema),
  },
  {
    id: "streets",
    title: "Roads follow lineage",
    requires: (doc) => routed(doc) !== null,
    body: (doc) => {
      const edge = routed(doc)!;
      return (
        `The road network is not a decoration around the graph — it IS the graph. ` +
        `Lineage from the catalog IS the streets: ${doc.edges.length} lineage edges ` +
        `are paved here. Each street follows a real data flow from ` +
        `${edge.src} → ${edge.dst}. Freight on it means that build really moved data.`
      );
    },
    target: (doc) => routed(doc)!.dst,
  },
  {
    id: "no-lineage",
    title: "A city with no streets",
    requires: (doc) => !doc.database.has_known_edges,
    body: () =>
      `No lineage was detected in this catalog, so there are no streets to drive. ` +
      `The buildings still stand — an unconnected city is a finding about the ` +
      `catalog, never a blank map pretending nothing is there.`,
  },
  {
    id: "plant",
    title: "The database is the power plant",
    requires: (doc) => doc.objects.length > 0,
    body: (doc) =>
      `${doc.database.name} is the plant: ${doc.database.object_count} objects, ` +
      `${doc.database.total_rows.toLocaleString()} rows. POWER_LINE arterials ` +
      `radiate from it to every lot — a building with no power line is one ` +
      `nothing can read.`,
    target: () => PLANT_KEY,
  },
  {
    id: "orphans",
    title: "Dimmed buildings are orphans",
    requires: (doc) => doc.objects.length > 0,
    body: (doc) => {
      const orphans = doc.lots.filter(
        (l) => !doc.edges.some((e) => e.src === l.object_key || e.dst === l.object_key),
      ).length;
      return (
        `${orphans} building${orphans === 1 ? " is" : "s are"} dimmed here — ` +
        `an orphan: no edge touches it, no power line reaches it, no street ` +
        `leads to it. An unconnected building is a finding about the catalog, ` +
        `not a rendering bug. The strip would tell you if it had tests.`
      );
    },
  },
  {
    id: "fire",
    title: "A failing test is a fire",
    requires: (doc) => burning(doc) !== null,
    body: (doc) =>
      `${burning(doc)!.object_key} is ON FIRE: its dbt tests failed. Fires are the ` +
      `highest-priority signal on this map — fog is capped below the lowest roof so ` +
      `it can never hide one.`,
    target: (doc) => burning(doc)!.object_key,
  },
  {
    id: "quiet-city",
    title: "A quiet city",
    requires: (doc) => burning(doc) === null,
    body: () =>
      `No failing tests here — that's what a quiet city looks like. Nothing is ` +
      `burning, and nothing is pretending to: the strip would say so the moment ` +
      `one test failed.`,
  },
  {
    id: "firehouse",
    title: "The firehouse dispatches",
    requires: (doc) => doc.firehouse !== null,
    body: (doc) => {
      const fires = doc.lots.filter((l) => l.test_status === "fail").length;
      const calls = doc.lots.filter(
        (l) => l.freshness_status === "warn" || l.freshness_status === "error",
      ).length;
      return (
        `One truck per fire (${fires} now), one contractor van per stale source ` +
        `(${calls} repair calls). A truck on the street means a problem is AWAITING ` +
        `response — it never means a fix is running. The AI responder is not connected.`
      );
    },
    target: () => FIREHOUSE_KEY,
  },
  {
    id: "library",
    title: "The library is your context",
    requires: (doc) => doc.library !== null && doc.objects.length > 0,
    body: (doc) => {
      const cols = doc.objects.flatMap((o) => o.columns);
      const documented = cols.filter((c) => c.description !== null).length;
      const tested = doc.objects.filter((o) => (o.dbt?.tests.length ?? 0) > 0).length;
      return (
        `Every shelf is a count of real documentation: ${documented}/${cols.length} ` +
        `columns described, ${tested}/${doc.objects.length} objects tested. Writing ` +
        `docs is how you build this city out — the counts are artifacts, never points.`
      );
    },
    target: () => LIBRARY_KEY,
  },
  {
    id: "weather",
    title: "Fog is source freshness",
    requires: (doc) => fogged(doc).length > 0,
    body: (doc) => {
      const cells = fogged(doc);
      return (
        `A late source fogs every district it FEEDS — not its own, which is where ` +
        `the problem actually is. Under weather now: ` +
        `${cells.map((c) => `${c.schema} (${c.condition}, from ${c.worst_source ?? "?"})`).join(", ")}. ` +
        `W toggles it.`
      );
    },
    target: (doc) => firstIn(doc, fogged(doc)[0]!.schema),
    overlay: "weather",
  },
  {
    id: "weather-unknown",
    title: "Weather nobody judged",
    requires: (doc) => fogged(doc).length === 0,
    body: (doc) =>
      `No fog on this map, and that is not the same as fine weather: ` +
      `${doc.weather?.note ?? "this document carries no weather block at all"}. ` +
      `Clear-because-unknown is never drawn as clear-because-good.`,
  },
  {
    id: "load",
    title: "Road heat is compute load",
    requires: (doc) => busiest(doc) !== null,
    body: (doc) => {
      const edge = busiest(doc)!;
      return (
        `Heat on a street is measured: build cadence × mean build cost, accumulated ` +
        `per tile, so a shared trunk glows with everything it carries. Hottest here: ` +
        `${edge.src} → ${edge.dst} at ${edge.daily_load_s!.toFixed(1)}s/day. T toggles it.`
      );
    },
    target: (doc) => busiest(doc)!.dst,
    overlay: "flow",
  },
  {
    id: "wear",
    title: "Wear and tear, and the contractors",
    requires: (doc) => worn(doc) !== null,
    body: (doc) =>
      `${worn(doc)!.object_key} is boarded up: its source missed the freshness SLA ` +
      `dbt declared for it (${worn(doc)!.freshness_status}). The amber van answering ` +
      `the call is a dispatch, never a repair anyone has made.`,
    target: (doc) => worn(doc)!.object_key,
  },
  {
    id: "drift",
    title: "Cranes mean the shape moved",
    requires: (doc) => drifting(doc) !== null,
    body: (doc) => {
      const lot = drifting(doc)!;
      return (
        `A crane over a roof means the object's SHAPE changed recently — ` +
        `${lot.object_key}, ${days(lot.schema_drift_age_s!)}d ago. Under construction, ` +
        `literally: columns came or went since the last time you looked.`
      );
    },
    target: (doc) => drifting(doc)!.object_key,
  },
  {
    id: "replay",
    title: "Replay a real run",
    requires: (doc) => (doc.replay?.steps.length ?? 0) > 0,
    body: (doc) =>
      `"Replay a run" steps through one real dbt invocation — ${doc.replay!.steps.length} ` +
      `steps. ${doc.replay!.note}. Buildings grow as they build, failures burn, and ` +
      `traffic runs only on the streets that step actually used.`,
    target: (doc) => doc.replay!.steps[0]!.object_key,
  },
  {
    id: "controls",
    title: "Controls",
    requires: () => true,
    body: () =>
      `Navigation: drag to orbit, scroll to zoom, arrow keys (or WASD) to move. ` +
      `Click any building to inspect it. F toggles fly mode, H reframes, R re-reads ` +
      `the catalog in place. T/W/U toggle road-load, weather, and usage overlays. ` +
      `?tour=1 walks this tour; ?lens=<name> switches role presets.`,
  },
];
