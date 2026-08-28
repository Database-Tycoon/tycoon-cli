/**
 * The road-load overlay: expected warehouse load painted on the streets.
 *
 * Stephen's analogy (2026-08-05): "warehouses carry load, so the roads should
 * basically correspond to warehouse load" — and it should be worth looking at
 * while nothing is moving. Every edge ships `daily_load_s` (its destination's
 * measured build cadence x mean build cost); this layer accumulates that per
 * ROAD TILE across all routes crossing it, so a shared trunk glows with the
 * combined load of everything it carries, then tints each tile on a
 * cool-to-hot ramp normalised to the busiest tile in this city.
 *
 * Facts only: edges with null load contribute nothing, a city with no usable
 * history shows no overlay at all, and the legend names the source. `T`
 * toggles it — the binding lives here, as the `Overlay` this class implements,
 * and the registry in `ui/overlays.ts` routes the key to it.
 */

import * as THREE from "three";
import type { CityDocument } from "../contract";
import { decodeRle } from "../contract";
import type { Overlay } from "../ui/overlays";

const COOL = new THREE.Color("#3fa7ff");
const MID = new THREE.Color("#ffd75e");
const HOT = new THREE.Color("#ff5533");

function rampColor(t: number, out: THREE.Color): void {
  if (t < 0.5) out.copy(COOL).lerp(MID, t * 2);
  else out.copy(MID).lerp(HOT, (t - 0.5) * 2);
}

export class FlowOverlay implements Overlay {
  readonly id = "flow";
  readonly key = "t";
  readonly group = new THREE.Group();
  visible = true;
  private tiles = 0;

  /** Road tiles carrying a known expected load — the e2e counting hook. */
  get count(): number {
    return this.tiles;
  }

  build(doc: CityDocument): void {
    for (const child of [...this.group.children]) {
      this.group.remove(child);
      const mesh = child as THREE.Mesh;
      mesh.geometry?.dispose();
      (mesh.material as THREE.Material)?.dispose();
    }
    this.tiles = 0;

    // Accumulate load per road tile: interiors only — endpoints are lots.
    const loadAt = new Map<string, number>();
    const routeTiles = new Set<string>();
    for (const edge of doc.edges) {
      for (const [x, y] of edge.route.slice(1, -1)) routeTiles.add(`${x},${y}`);
      if (edge.daily_load_s === null || edge.daily_load_s <= 0) continue;
      for (const [x, y] of edge.route.slice(1, -1)) {
        const key = `${x},${y}`;
        loadAt.set(key, (loadAt.get(key) ?? 0) + edge.daily_load_s);
      }
    }
    if (!loadAt.size) return;

    // A widened road is one street: spread each tile's heat across its extra
    // lanes (ROAD tiles east/south of a heated tile that belong to no route
    // centre-line), chaining so a four-lane trunk tints wall to wall. Max,
    // not sum — the centre line already carries the summed load.
    const { width, height } = doc.grid;
    const flat = decodeRle(doc.grid.tiles_rle, width, height);
    const roadId = doc.grid.tile_kinds.indexOf("road");
    const isLane = (x: number, y: number) =>
      x >= 0 &&
      y >= 0 &&
      x < width &&
      y < height &&
      flat[y * width + x] === roadId &&
      !routeTiles.has(`${x},${y}`);
    const frontier = [...loadAt.entries()];
    while (frontier.length) {
      const [key, load] = frontier.pop()!;
      const [x, y] = key.split(",").map(Number) as [number, number];
      for (const [nx, ny] of [
        [x + 1, y],
        [x, y + 1],
      ] as const) {
        const nk = `${nx},${ny}`;
        if (!isLane(nx, ny)) continue;
        if ((loadAt.get(nk) ?? 0) >= load) continue;
        loadAt.set(nk, load);
        frontier.push([nk, load]);
      }
    }

    const peak = Math.max(...loadAt.values());
    const quads = new THREE.InstancedMesh(
      new THREE.PlaneGeometry(1, 1),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.45, depthWrite: false }),
      loadAt.size,
    );
    const m = new THREE.Matrix4();
    const rot = new THREE.Matrix4().makeRotationX(-Math.PI / 2);
    const color = new THREE.Color();
    let i = 0;
    for (const [key, load] of loadAt) {
      const [x, y] = key.split(",").map(Number);
      m.copy(rot).setPosition(x! + 0.5, 0.045, y! + 0.5);
      quads.setMatrixAt(i, m);
      rampColor(load / peak, color);
      quads.setColorAt(i, color);
      i += 1;
    }
    quads.frustumCulled = false;
    this.group.add(quads);
    this.tiles = loadAt.size;
    this.group.visible = this.visible;
  }

  setVisible(on: boolean): void {
    this.visible = on;
    this.group.visible = on;
  }

  toggle(): void {
    this.setVisible(!this.visible);
  }
}
