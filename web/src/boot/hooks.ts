/**
 * `window.__tycoonCity`: the verification seam the headless suite drives the city
 * through, and the only place the app talks to a test.
 *
 * Every hook is a question the e2e suite cannot answer from pixels — how many
 * vehicles exist, where a building landed on screen, what the camera pose is —
 * or an action a scripted drag cannot reproduce. Nothing here may compute
 * anything the app itself does not already compute: a hook that derives its
 * own answer is a test asserting against a second implementation.
 *
 * The names are a contract with `web/e2e/`. Renaming one silently turns a
 * spec into a no-op, so they are moved, never renamed.
 */

import * as THREE from "three";
import type { Cameras } from "../cameras";
import type { CityDocument } from "../contract";
import type { FlowOverlay } from "../scene/flow_overlay";
import type { Skybridges } from "../scene/skybridges";
import type { UsageOverlay } from "../scene/usage_overlay";
import type { Weather } from "../scene/weather";
import { PLANT_KEY } from "../scene/plant";
import type { UsageState } from "../usage";
import type { LensId } from "../ui/lenses";
import type { RunPhase, RunState } from "../sim/run_replay";
import type { MountedCity } from "./mount";
import type { RunWiring } from "./run_wiring";

export interface TycoonCityHooks {
  select: (key: string) => void;
  selectedKey: () => string | null;
  screenPos: (key: string) => { x: number; y: number } | null;
  vehicleCount: () => number;
  guestCount: () => number;
  skybridgeCount: () => number;
  flowTileCount: () => number;
  /** Fog/overcast meshes actually IN the scene — walked, not tallied, so a
   * bookkeeping integer cannot pass while the scene is empty. */
  weatherMeshCount: () => number;
  /** Which districts the weather overlay actually painted. */
  weatherSchemas: () => string[];
  /** The fog's own animation clock. Stays 0 under `?settle=1` — the proof
   * that the freeze is real and not just a still-looking screenshot. */
  weatherElapsed: () => number;
  /** Each overlay's OWN visibility flag — the field `setVisible` writes, not
   * a second opinion about it. A role lens's overlay defaults are assertable
   * only through these. */
  weatherVisible: () => boolean;
  flowVisible: () => boolean;
  usageVisible: () => boolean;
  /** Usage instances actually IN the scene — walked from the scene graph, so
   * an overlay that built its meshes and never added them reads as missing. */
  usageInstanceCount: () => number;
  /** WHICH objects the usage overlay painted with a given treatment, read back
   * off the live meshes. `unknown` is always empty: a null measurement draws
   * nothing, and that is the one thing this overlay may never get wrong. */
  usagePainted: (state: UsageState) => string[];
  /** The beacons' own breathing clock. Stays 0 under `?settle=1`. */
  usageElapsed: () => number;
  fireCount: () => number;
  truckCount: () => number;
  vanCount: () => number;
  wearCount: () => number;
  curbCount: () => number;
  streetFeatureCount: () => number;
  setPose: (name: "home" | "top" | "low") => void;
  visit: (key: string) => void;
  cameraPose: () => { position: number[]; target: number[] };
  setCameraPose: (pose: { position: number[]; target: number[] }) => void;
  refresh: () => Promise<void>;
  districtScreenRect: (
    schema: string,
  ) => { left: number; top: number; right: number; bottom: number } | null;
  /** Open the run panel and begin a run — the named one, or the picker's
   * first (worst, then newest) when unnamed. */
  runReplay: (id?: string) => Promise<void>;
  /** The replay's own pure answer for a key at the current cursor. Nothing is
   * recomputed here: this IS the function the scene is painted from, which is
   * what lets a spec assert WHICH building burns at WHICH cursor without a
   * screenshot. */
  runStateOf: (key: string) => RunState;
  /** Advance one step without a synthetic keypress. */
  runStep: () => void;
  /** Where the machine is. `at` is the index of the step currently executing;
   * `at === total` is the past-the-end cursor. */
  runCursor: () => { phase: RunPhase; at: number; total: number; key: string | null };
  /** The active role lens, and the door that changes it WITHOUT persisting —
   * a spec that wrote the preference would leak its choice into the next one.
   * This is how the cross-lens equality guard shows the same document to two
   * lenses in one page load. */
  lensId: () => LensId | "none";
  setLens: (id: LensId | "none") => void;
  /** The document on the screen right now. Read-only and computed on every
   * access: it is derived from `deps.doc()`, never assigned. Assigning it is
   * what broke the R refresh once already — a write to an accessor throws
   * under strict mode, and the throw was swallowed by `refresh()`'s own
   * try/catch, taking the selection restore down with it. */
  readonly doc: CityDocument;
  /** Top-level objects on the scene, straight off `scene.children`. The one
   * question a doubled mount answers differently: a second city sits at the
   * same coordinates as the first, so counts, screen positions and pixels all
   * keep reading correctly while the graph quietly grows by one group per
   * refresh. Nothing else in this seam can see that. */
  sceneChildCount: () => number;
}

declare global {
  interface Window {
    __tycoonCity?: TycoonCityHooks;
  }
}

/**
 * What the hooks read. The document and the mounted city are passed as
 * getters, not values: both are replaced wholesale by an R refresh, and a hook
 * closing over the first one would answer for a city that is no longer on the
 * screen. The rest are objects that outlive every refresh.
 */
export interface HookDeps {
  doc: () => CityDocument;
  city: () => MountedCity;
  cameras: Cameras;
  renderer: THREE.WebGLRenderer;
  /** The one scene, which outlives every refresh. */
  scene: THREE.Scene;
  skybridges: Skybridges;
  flow: FlowOverlay;
  weather: Weather;
  usage: UsageOverlay;
  /** The simulated layer stays behind the composition root; only its count
   * crosses into the hooks. */
  guestCount: () => number;
  selectedKey: () => string | null;
  select: (key: string | null) => void;
  visit: (key: string) => void;
  refresh: () => Promise<void>;
  run: RunWiring;
  lensId: () => LensId | "none";
  setLens: (id: LensId | "none") => void;
}

/** Install `window.__tycoonCity` and hand the object back. Every hook — `doc`
 * included — reads through `deps`, so the object needs no patching after a
 * refresh and the caller has nothing to keep current. */
export function installHooks(deps: HookDeps): TycoonCityHooks {
  const { cameras, renderer, scene, skybridges, flow, weather, usage } = deps;
  const hooks: TycoonCityHooks = {
    get doc() {
      return deps.doc();
    },
    sceneChildCount: () => scene.children.length,
    select: deps.select,
    selectedKey: deps.selectedKey,
    vehicleCount: () => deps.city().traffic.vehicles.length,
    guestCount: deps.guestCount,
    skybridgeCount: () => skybridges.count,
    flowTileCount: () => flow.count,
    weatherMeshCount: () => weather.meshCount,
    weatherSchemas: () => weather.weatheredSchemas,
    weatherElapsed: () => weather.elapsed,
    weatherVisible: () => weather.visible,
    flowVisible: () => flow.visible,
    usageVisible: () => usage.visible,
    usageInstanceCount: () => usage.instanceCount,
    usagePainted: (state) => usage.keysPainted(state),
    usageElapsed: () => usage.elapsed,
    fireCount: () => deps.city().fires.count,
    truckCount: () => deps.city().trucks.count,
    vanCount: () => deps.city().vans.count,
    wearCount: () => deps.city().wear.count,
    curbCount: () => deps.city().streetscape?.curbCount ?? 0,
    streetFeatureCount: () => deps.city().streetscape?.featureCount ?? 0,
    setPose: (name) => cameras.setPose(name),
    visit: deps.visit,
    cameraPose: () => cameras.serialize(),
    // Place the camera exactly: street-level looks at geometry (curbs, ramps)
    // need a pose the named poses do not offer, and a scripted orbit drag is
    // not reproducible.
    setCameraPose: (pose) => cameras.restore(pose),
    refresh: deps.refresh,
    lensId: deps.lensId,
    setLens: deps.setLens,
    runReplay: (id) => deps.run.start(id),
    runStateOf: (key) => deps.run.replay.stateOf(key),
    runStep: () => {
      deps.run.replay.stepForward();
      deps.run.apply();
    },
    runCursor: () => ({
      phase: deps.run.replay.phase,
      at: deps.run.replay.at,
      total: deps.run.replay.total,
      key: deps.run.replay.current()?.object_key ?? null,
    }),
    screenPos: (key: string) => {
      const doc = deps.doc();
      const lot = doc.lots.find((l) => l.object_key === key);
      const at = lot
        ? new THREE.Vector3(
            lot.x + lot.w / 2,
            deps.city().buildings.heightOf(lot) / 2,
            lot.y + lot.h / 2,
          )
        : key === PLANT_KEY
          ? new THREE.Vector3(doc.plant.x + 0.5, 1.6, doc.plant.y + 0.5)
          : null;
      if (!at) return null;
      at.project(cameras.camera);
      if (at.z > 1) return null; // behind the camera
      const rect = renderer.domElement.getBoundingClientRect();
      return {
        x: rect.left + ((at.x + 1) / 2) * rect.width,
        y: rect.top + ((1 - at.y) / 2) * rect.height,
      };
    },
    districtScreenRect: (schema: string) => {
      const district = deps.doc().districts.find((d) => d.schema === schema);
      if (!district) return null;
      const rect = renderer.domElement.getBoundingClientRect();
      const corners = [
        [district.x, district.y],
        [district.x + district.w, district.y],
        [district.x, district.y + district.h],
        [district.x + district.w, district.y + district.h],
      ].map(([x, z]) => {
        const p = new THREE.Vector3(x!, 0, z!).project(cameras.camera);
        return {
          x: rect.left + ((p.x + 1) / 2) * rect.width,
          y: rect.top + ((1 - p.y) / 2) * rect.height,
        };
      });
      return {
        left: Math.min(...corners.map((c) => c.x)),
        top: Math.min(...corners.map((c) => c.y)),
        right: Math.max(...corners.map((c) => c.x)),
        bottom: Math.max(...corners.map((c) => c.y)),
      };
    },
  };
  window.__tycoonCity = hooks;
  return hooks;
}
