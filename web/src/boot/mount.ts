/**
 * The mount/unmount cycle: everything built FROM a city document.
 *
 * `main.ts` owns the doc-independent world — renderer, scene, lights, camera,
 * the instanced vehicle/guest layers, the HUD — and this module owns the half
 * that is replaced wholesale when `R` re-reads the catalog. `mountCity` builds
 * one group plus the per-document handles the animation loop, the picker and
 * the test hooks read; `unmountCity` takes that same bundle back off the scene
 * and frees its GPU resources.
 *
 * This is the existing R-refresh seam, not a new one: mount → unmount → mount
 * must leave the scene exactly as a single mount would, which is why the
 * mounted handles are returned as one bundle rather than assigned into
 * long-lived variables — a stale handle after a refresh is the failure mode
 * this shape rules out.
 */

import * as THREE from "three";
import type { CityDocument } from "../contract";
import type { Rng } from "../sim/rng";
import { Buildings, ConditionMarkers } from "../scene/buildings";
import { buildDistricts } from "../scene/districts";
import { buildPlant } from "../scene/plant";
import { buildSilhouettes } from "../scene/silhouettes";
import { buildFirehouse, buildLibrary } from "../scene/civic";
import { Fires } from "../scene/fire";
import { FireTrucks, RepairVans } from "../scene/firetrucks";
import { Wear } from "../scene/wear";
import { buildFacades } from "../scene/facade";
import { disposeTree } from "../scene/dispose";
import { Streetscape } from "../scene/streetscape";
import { buildTerrain, loadImage } from "../scene/terrain";
import { Traffic } from "../sim/traffic";
import { Replay } from "../sim/replay";

/** The URL-param flags a mount reads, plus the composition root's seeding. */
export interface MountOptions {
  /** `?flat=1`: unlit exact colours for pixel tests; the 3D streetscape, the
   * lit extras and the spritesheet are all skipped. */
  flat: boolean;
  /** `?settle=1`: buildings start at their target height. */
  settle: boolean;
  /** `?ambient=1`: decorative flow on top of real data movement. */
  ambient: boolean;
  /** Deterministic stream factory; the root owns the seed policy. */
  seedFor: (offset: number) => Rng;
}

/** Everything one document produced. Replaced as a unit on refresh. */
export interface MountedCity {
  group: THREE.Group;
  buildings: Buildings;
  plant: THREE.Group;
  traffic: Traffic;
  fires: Fires;
  trucks: FireTrucks;
  vans: RepairVans;
  wear: Wear;
  /** Null in `?flat=1`: the streetscape is skipped there, and its hooks must
   * report the absence rather than a stale count. */
  streetscape: Streetscape | null;
  /** Civic buildings the picker adds to its raycast set. */
  civicTargets: THREE.Object3D[];
  replay: Replay;
  /** object key → row count, for the hover tooltip. */
  rows: Map<string, number>;
}

/** Build `d` into `scene` and hand back the handles that outlive the call. */
export async function mountCity(
  scene: THREE.Scene,
  d: CityDocument,
  options: MountOptions,
): Promise<MountedCity> {
  const { flat, settle, ambient, seedFor } = options;
  const group = new THREE.Group();
  const sheet = flat ? undefined : await loadImage(`./${d.theme.spritesheet}?t=${Date.now()}`);
  group.add(buildTerrain(d, flat, sheet));
  group.add(buildDistricts(d));
  const plant = buildPlant(d, flat);
  group.add(plant);
  const buildings = new Buildings(d, settle, flat);
  group.add(buildings.group);
  const fires = new Fires(d);
  const trucks = new FireTrucks(d);
  const vans = new RepairVans(d);
  const wear = new Wear(d);
  const civicTargets: THREE.Object3D[] = [];
  for (const civic of [buildLibrary(d), buildFirehouse(d)]) {
    if (civic) {
      group.add(civic);
      civicTargets.push(civic);
    }
  }
  let streetscape: Streetscape | null = null;
  if (!flat) {
    group.add(fires.group);
    group.add(trucks.group);
    group.add(vans.group);
    group.add(wear.group);
    group.add(new ConditionMarkers(d).group);
    streetscape = new Streetscape(d);
    group.add(streetscape.group);
    const facades = buildFacades(d);
    if (facades) group.add(facades);
    group.add(buildSilhouettes(d));
  }
  scene.add(group);

  return {
    group,
    buildings,
    plant,
    traffic: new Traffic(d, seedFor(0), ambient),
    fires,
    trucks,
    vans,
    wear,
    streetscape,
    civicTargets,
    replay: new Replay(d),
    rows: new Map(d.objects.map((o) => [o.key, o.row_count])),
  };
}

/** Take a mounted city off the scene and free it. `layers` are the persistent
 * instanced layers whose contents belonged to that document — they survive the
 * refresh as objects, so their instance counts are zeroed instead. */
export function unmountCity(
  scene: THREE.Scene,
  city: MountedCity,
  layers: THREE.InstancedMesh[],
): void {
  scene.remove(city.group);
  disposeTree(city.group);
  for (const layer of layers) layer.count = 0;
}
