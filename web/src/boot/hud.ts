/**
 * HUD/UI setup: status bar, chrome, overlays, panels, picking, lenses, tour, replay.
 *
 * Everything that renders on top of the Three.js canvas, all the UI panels,
 * and the semantic "door" (visit/select) that connects user interaction to
 * the 3D scene. Receives the scene/camera from setup.ts and wires itself
 * into the scene graph.
 */

import type { CityDocument } from "../contract";
import type { Lens, OverlayId } from "../ui/lenses";
import { DRIFT_RECENT_S } from "../ui/health";
import * as THREE from "three";
import { PLANT_KEY } from "../scene/plant";
import { FIREHOUSE_KEY, LIBRARY_KEY } from "../scene/civic";
import type { SetupResult } from "./setup";
import { freshnessLabel, freshnessTitle, loadFreshness } from "../meta";
import { SELECTION } from "../palette";
import { Skybridges } from "../scene/skybridges";
import { FlowOverlay } from "../scene/flow_overlay";
import { Weather } from "../scene/weather";
import { UsageOverlay } from "../scene/usage_overlay";
import { OverlayRegistry } from "../ui/overlays";
import { Inspector } from "../ui/inspector";
import { Stats } from "../ui/stats";
import { HealthStrip } from "../ui/health";
import { Problems } from "../ui/problems";
import { RequestsPanel } from "../ui/requests";
import { Search } from "../ui/search";
import { buildLegend } from "../ui/legend";
import { resolveLens, LENSES, NO_LENS } from "../ui/lenses";
import { LensSwitcher, LensPicker, lensStore } from "../ui/lens_picker";
import { Tour } from "../ui/tour";
import { installRunReplay } from "../boot/run_wiring";
import { Picking } from "../picking";
import { mountCity, type MountedCity, type MountOptions, unmountCity } from "./mount";

export interface HUDResult {
  status: HTMLElement;
  statusLine: string;
  asof: HTMLElement;
  /** The document currently on the screen. An R refresh replaces it wholesale,
   * so this is a getter: whoever reads the value instead of the function is
   * answering for a city that has already been unmounted. */
  doc: () => CityDocument;
  city: () => SetupResult["city"];
  camera: SetupResult["camera"];
  skybridges: Skybridges;
  flow: FlowOverlay;
  weather: Weather;
  usage: UsageOverlay;
  overlays: OverlayRegistry;
  outline: THREE.LineSegments;
  inspector: Inspector;
  stats: Stats;
  health: HealthStrip;
  problems: Problems;
  requests: RequestsPanel | null;
  search: Search;
  selected: () => string | null;
  select: (key: string | null) => void;
  visit: (key: string) => void;
  lens: () => Lens;
  setLens: (id: string) => void;
  tour: Tour;
  run: ReturnType<typeof installRunReplay>;
  picking: Picking;
  tooltip: HTMLElement;
  refresh: () => Promise<void>;
}

export function setupHUD(
  setup: SetupResult,
  scene: THREE.Scene,
  params: URLSearchParams,
  mountOptions: MountOptions,
): HUDResult {
  const { doc, city, app } = setup;

  const status = document.getElementById("status")!;
  const statusLine =
    `database: ${doc.database.name}   ·   ${doc.database.object_count} objects   ·   ` +
    `${doc.database.total_rows.toLocaleString()} rows`;
  status.textContent = statusLine;
  status.title = statusLine;

  const notes = [
    ...(doc.database.has_known_edges ? [] : ["no lineage detected"]),
    ...doc.database.notes,
  ];
  const notesButton = document.getElementById("notes-button") as HTMLButtonElement;
  const notesPop = document.getElementById("notes-pop")!;
  notesButton.hidden = notes.length === 0;
  notesButton.textContent = `ⓘ notes (${notes.length})`;
  notesPop.innerHTML = `<b>degradation notes</b><ul>${notes
    .map((n) => `<li>${n}</li>`)
    .join("")}</ul>`;

  document.getElementById("notes-button")!.addEventListener("click", () => {
    const pop = document.getElementById("notes-pop")!;
    pop.hidden = !pop.hidden;
    document.getElementById("keys-pop")!.hidden = true;
  });
  const keysPop = document.getElementById("keys-pop")!;
  keysPop.innerHTML = `<table>
    <tr><td>/</td><td>search</td></tr>
    <tr><td>P</td><td>problems panel</td></tr>
    <tr><td>?lens=…</td><td>role lens (footer switcher; presentation only)</td></tr>
    <tr><td>?tour=1</td><td>guided tour — enter/n next, esc skip</td></tr>
    <tr><td>space / →</td><td>replay: next step</td></tr>
    <tr><td>←</td><td>replay: previous step</td></tr>
    <tr><td>0</td><td>replay: back to step 1</td></tr>
    <tr><td>esc</td><td>replay: exit</td></tr>
    <tr><td>T</td><td>toggle the road-load overlay</td></tr>
    <tr><td>W</td><td>toggle the weather overlay (source freshness)</td></tr>
    <tr><td>U</td><td>toggle the usage overlay (measured run appearances)</td></tr>
    <tr><td>R</td><td>re-read the catalog in place</td></tr>
    <tr><td>F</td><td>fly camera</td></tr>
    <tr><td>H</td><td>home framing</td></tr>
    <tr><td>drag / wheel</td><td>orbit / zoom</td></tr>
    <tr><td>click</td><td>inspect a building</td></tr></table>`;
  document.getElementById("keys-button")!.addEventListener("click", () => {
    keysPop.hidden = !keysPop.hidden;
    document.getElementById("notes-pop")!.hidden = true;
  });

  const asof = document.getElementById("asof")!;
  let freshness: import("../meta").Freshness = { kind: "fetched", at: Date.now() };
  function paintAsOf(): void {
    asof.textContent = freshnessLabel(freshness, Date.now());
    asof.title = freshnessTitle(freshness);
  }
  async function readFreshness(fetchedAt: number, bust = false): Promise<void> {
    const url = bust ? `./meta.json?t=${fetchedAt}` : "./meta.json";
    freshness = await loadFreshness(url, fetchedAt);
    paintAsOf();
  }
  paintAsOf();
  setInterval(paintAsOf, 1000);
  void readFreshness(Date.now());

  const vehicleLayer = setup.vehicleLayer;
  const guestLayer = setup.guestLayer;
  let selected: string | null = null;
  let currentDoc = doc;
  const cityRef = { current: setup.city };

  function select(key: string | null): void {
    selected = key;
    inspector.show(key);
    skybridges.setSelection(key);
    const lot = currentDoc.lots.find((l) => l.object_key === key);
    if (lot) {
      outline.visible = true;
      outline.scale.set(lot.w - 0.22, cityRef.current.buildings.heightOf(lot) + 0.06, lot.h - 0.22);
      outline.position.set(lot.x + lot.w / 2, 0, lot.y + lot.h / 2);
    } else if (key === PLANT_KEY) {
      outline.visible = true;
      outline.scale.set(1.5, 4.0, 1.5);
      outline.position.set(currentDoc.plant.x + 0.5, 0, currentDoc.plant.y + 0.5);
    } else if (key === LIBRARY_KEY && currentDoc.library) {
      outline.visible = true;
      outline.scale.set(1.7, 1.1, 1.3);
      outline.position.set(currentDoc.library.x + 0.5, 0, currentDoc.library.y + 0.5);
    } else if (key === FIREHOUSE_KEY && currentDoc.firehouse) {
      outline.visible = true;
      outline.scale.set(1.6, 1.3, 1.2);
      outline.position.set(currentDoc.firehouse.x + 0.5, 0, currentDoc.firehouse.y + 0.5);
    } else {
      outline.visible = false;
    }
  }

  const skybridges = new Skybridges(doc);
  scene.add(skybridges.group);

  const flow = new FlowOverlay();
  flow.build(doc);
  scene.add(flow.group);
  const weather = new Weather();
  weather.build(doc);
  scene.add(weather.group);
  const usage = new UsageOverlay();
  usage.build(doc);
  scene.add(usage.group);
  const overlays = new OverlayRegistry();
  overlays.register(flow);
  overlays.register(weather);
  overlays.register(usage);

  const outline = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(1, 1, 1).translate(0, 0.5, 0)),
    new THREE.LineBasicMaterial({ color: SELECTION }),
  );
  outline.visible = false;
  scene.add(outline);

  const inspector = new Inspector(doc, (key) => select(key || null));
  const stats = new Stats(doc, (key) => select(key));
  const health = new HealthStrip(doc, (key) => visit(key));
  const problems = new Problems(doc, (key) => visit(key));
  const requests = params.get("crlf") === "1" ? new RequestsPanel() : null;
  if (requests) {
    void requests.load("./requests.json");
  }
  const search = new Search(doc, (key) => visit(key));
  buildLegend(doc);

  // Every lookup here reads `currentDoc`, never the boot `doc`: an R refresh
  // replaces the document wholesale, and a door that resolved a key against
  // the previous city would fly the camera to where the building used to be.
  function visit(key: string): void {
    const c = cityRef.current;
    const d = currentDoc;
    const civic =
      key === PLANT_KEY ? d.plant : key === LIBRARY_KEY ? d.library : key === FIREHOUSE_KEY ? d.firehouse : null;
    if (civic) {
      setup.camera.flyTo(civic.x + 0.5, civic.y + 0.5, 3);
      select(key);
      return;
    }
    const lot = d.lots.find((l) => l.object_key === key);
    if (!lot) return;
    setup.camera.flyTo(lot.x + lot.w / 2, lot.y + lot.h / 2, c.buildings.heightOf(lot));
    select(key);
  }

  const resolved = resolveLens(params.get("lens"), lensStore);
  let lens: Lens = resolved.lens;
  const switcher = new LensSwitcher((next) => applyLens(next, true));

  function applyLens(next: Lens, persist: boolean): void {
    lens = next;
    if (persist) lensStore.write(next.id);
    switcher.setLens(next);
    health.setLens(next);
    problems.setLens(next);
    overlays.applyLens(next);
    if (next.defaultPanel === "library" && currentDoc.library) select(LIBRARY_KEY);
    else if (next.defaultPanel !== "none") problems.show();
  }
  applyLens(lens, false);
  if (resolved.firstRun && !params.get("settle") && params.get("lens") === null) {
    new LensPicker((next) => applyLens(next, true)).open();
  }

  // `?selected=` is honoured after the lens has had its say, so an explicit
  // request beats a lens's default panel. It runs here rather than at the top
  // of setupHUD because `select` closes over consts declared below it.
  const initial = params.get("selected");
  if (initial) select(initial);

  const tour = new Tour({
    doc: () => currentDoc,
    visit,
    lens: () => lens,
    setOverlay: (id) => overlays.get(id)?.setVisible(true),
  });
  const tourParam = params.get("tour");
  if (tourParam !== null && tourParam !== "0") {
    tour.start(tourParam === "restart");
  }

  const run = installRunReplay({
    doc: () => currentDoc,
    city: () => cityRef.current,
    visit,
    setStatus: (text) => {
      status.textContent = text ?? statusLine;
      status.title = status.textContent;
    },
  });

  const tooltip = document.getElementById("tooltip")!;
  const picking = new Picking(
    cityRef.current.buildings,
    cityRef.current.plant,
    setup.camera.camera,
    app,
    (key) => {
      if (key === null || key === PLANT_KEY) {
        tooltip.hidden = true;
        app.style.cursor = key === null ? "default" : "pointer";
        return;
      }
      tooltip.hidden = false;
      tooltip.textContent = `${key} — ${(cityRef.current.rows.get(key) ?? 0).toLocaleString()} rows`;
      app.style.cursor = "pointer";
    },
    select,
  );
  picking.setTargets(cityRef.current.buildings, cityRef.current.plant, cityRef.current.civicTargets);
  app.addEventListener("pointermove", (e) => {
    tooltip.style.left = `${e.clientX + 14}px`;
    tooltip.style.top = `${e.clientY + 14}px`;
  });

  let refreshing = false;
  async function refresh(): Promise<void> {
    if (refreshing) return;
    refreshing = true;
    status.textContent = "refreshing…";
    try {
      const next = await import("../contract").then(({ loadCity }) =>
        loadCity(`./city.json?t=${Date.now()}`)
      );
      const fetchedAt = Date.now();
      const keep = selected;
      select(null);
      unmountCity(scene, cityRef.current, [vehicleLayer.mesh, guestLayer.mesh]);
      cityRef.current = await mountCity(scene, next, mountOptions);
      // The document and the mounted city are swapped together, and before
      // anything below reads either. `run.apply()` in particular walks back
      // through `visit()`, which resolves keys against `currentDoc` — leaving
      // this until after that call pointed the replay at the previous city.
      // It is set after mountCity, not before, so a failed mount leaves both
      // halves on the old city that is still on screen.
      currentDoc = next;
      picking.setTargets(cityRef.current.buildings, cityRef.current.plant, cityRef.current.civicTargets);
      inspector.setDoc(next);
      stats.setDoc(next);
      health.setDoc(next);
      problems.setDoc(next);
      search.setDoc(next);
      skybridges.setDoc(next);
      flow.build(next);
      weather.build(next);
      usage.build(next);
      applyChrome(next);
      void readFreshness(fetchedAt, true);
      run.apply();
      if (keep && (keep === PLANT_KEY || next.lots.some((l) => l.object_key === keep))) {
        select(keep);
      }
    } catch (error) {
      status.textContent = `refresh failed: ${String(error)} — showing previous city`;
      status.title = status.textContent;
      setTimeout(() => {
        status.textContent = statusLine;
        status.title = statusLine;
      }, 6000);
      refreshing = false;
      return;
    }
    refreshing = false;
  }

  function applyChrome(d: CityDocument): void {
    (document.getElementById("logo")! as HTMLElement).textContent = d.theme.logo_text;
    status.textContent = statusLine;
    status.title = statusLine;
  }

  (window as any).__tycoonCityRefresh = () => void refresh();

  return {
    status,
    statusLine,
    asof,
    doc: () => currentDoc,
    city: () => cityRef.current,
    camera: setup.camera,
    skybridges,
    flow,
    weather,
    usage,
    overlays,
    outline,
    inspector,
    stats,
    health,
    problems,
    requests,
    search,
    selected: () => selected,
    select,
    visit,
    lens: () => lens,
    setLens: (id) => applyLens(id === "none" ? NO_LENS : LENSES[id as keyof typeof LENSES], false),
    tour,
    run,
    picking,
    tooltip,
    refresh,
  };
}
