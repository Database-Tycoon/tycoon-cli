/**
 * The weather overlay: source freshness as ground fog over the districts a
 * late source FEEDS.
 *
 * The document does the thinking (`docs/city-json-v1.md`, `weather`): Python
 * walks downstream reachability from every judged source, applies the
 * precedence rule, and ships one cell per covered district. This layer only
 * paints what the cells say — it never re-derives which district is late, and
 * it never fills a missing cell in with fair weather. A district with no cell
 * has no judged source upstream; a `clear` cell draws nothing because clear
 * IS the absence of fog.
 *
 * Two hard constraints, both structural rather than eyeballed:
 *
 * 1. **Fog must never hide a fire.** Fires are the higher-priority signal.
 *    The whole volume is capped below `heightFromRows(0)` — the shortest roof
 *    this renderer can produce — so no flame is ever *inside* the fog, and
 *    every layer draws with `renderOrder` below the fires so a flame in front
 *    of a fog plane blends over it rather than under it. Per-layer opacity is
 *    capped too: even four layers stacked leave a fire plainly readable.
 * 2. **Frozen under `?settle=1`.** The drift lives in `tick`, which the
 *    composition root gates on `!settle` exactly as it gates `fires.tick`, so
 *    a screenshot of a foggy city is reproducible.
 *
 * `W` toggles it; the binding lives here, as the `Overlay` this class
 * implements, and `ui/overlays.ts` routes the key.
 */

import * as THREE from "three";
import type { CityDocument, DistrictRecord } from "../contract";
import type { Overlay } from "../ui/overlays";
import { heightFromRows } from "./buildings";

/** Per-condition look. A condition absent from this table draws nothing —
 * which covers `clear` and any future word a newer emitter invents. */
const STYLE: Record<string, { color: string; layers: number; opacity: number }> = {
  fog: { color: "#eef4f8", layers: 4, opacity: 0.19 },
  overcast: { color: "#c2c9d0", layers: 3, opacity: 0.12 },
};

/** The lowest roof this renderer can produce (`buildings.MIN_H`). The fog
 * ceiling sits just below it, so a flame — which starts at roof height — can
 * never be inside the volume. Derived, not copied: if the floor height ever
 * changes, the fog follows it. */
const CEILING = heightFromRows(0) - 0.01;
const FLOOR = 0.05;

/** Below the fires' default 0, so THREE draws fog first and a flame blends
 * on top of it instead of under it. */
const RENDER_ORDER = -2;

interface Layer {
  mesh: THREE.Mesh<THREE.PlaneGeometry, THREE.MeshBasicMaterial>;
  baseY: number;
  baseOpacity: number;
  phase: number;
}

export class Weather implements Overlay {
  readonly id = "weather";
  readonly key = "w";
  readonly group = new THREE.Group();
  visible = true;
  private layers: Layer[] = [];
  /** The drift clock, public so the e2e suite can prove `?settle=1` really
   * freezes it rather than merely producing a still-looking frame. */
  elapsed = 0;

  constructor() {
    this.group.renderOrder = RENDER_ORDER;
  }

  /**
   * Live meshes currently in the scene — the e2e counting hook.
   *
   * Counted by walking the group rather than returned from a tally kept
   * alongside it: a bookkeeping integer can be right while the scene is
   * empty, and this hook exists to answer "what actually reached the scene".
   */
  get meshCount(): number {
    let n = 0;
    this.group.traverse((object) => {
      if ((object as THREE.Mesh).isMesh) n += 1;
    });
    return n;
  }

  /** Districts under fog or overcast right now — what the HUD would name. */
  get weatheredSchemas(): string[] {
    return [...new Set(this.layers.map((l) => l.mesh.userData.schema as string))].sort();
  }

  build(doc: CityDocument): void {
    for (const child of [...this.group.children]) {
      this.group.remove(child);
      const mesh = child as THREE.Mesh;
      mesh.geometry?.dispose();
      (mesh.material as THREE.Material)?.dispose();
    }
    this.layers = [];
    this.elapsed = 0;

    const cells = doc.weather?.cells ?? [];
    if (!cells.length) return; // nothing judged, or nothing late: no weather

    const rectOf = new Map<string, DistrictRecord>(doc.districts.map((d) => [d.schema, d]));
    for (const cell of cells) {
      const style = STYLE[cell.condition];
      const rect = rectOf.get(cell.schema);
      // `clear`, an unknown condition, or a schema with no district on this
      // map: all no-ops. None of them may invent geometry.
      if (!style || !rect) continue;
      this.fogDistrict(rect, style);
    }
    this.group.visible = this.visible;
  }

  /** Stacked horizontal planes clipped exactly to the district rect. Layers
   * approximate a volume without a shader, and — unlike a drifting sprite
   * field — they cannot wander outside the district they describe. */
  private fogDistrict(
    rect: DistrictRecord,
    style: { color: string; layers: number; opacity: number },
  ): void {
    const span = CEILING - FLOOR;
    for (let i = 0; i < style.layers; i += 1) {
      const t = style.layers === 1 ? 0 : i / (style.layers - 1);
      const y = FLOOR + span * t;
      // Thinner toward the top: the volume reads as settling, and the
      // topmost sheet never competes with the buildings standing in it.
      const opacity = style.opacity * (1 - 0.35 * t);
      const mesh = new THREE.Mesh(
        new THREE.PlaneGeometry(rect.w, rect.h),
        new THREE.MeshBasicMaterial({
          color: style.color,
          transparent: true,
          opacity,
          depthWrite: false,
          side: THREE.DoubleSide,
        }),
      );
      mesh.rotateX(-Math.PI / 2);
      mesh.position.set(rect.x + rect.w / 2, y, rect.y + rect.h / 2);
      mesh.renderOrder = RENDER_ORDER;
      mesh.frustumCulled = false;
      mesh.userData.schema = rect.schema;
      this.group.add(mesh);
      this.layers.push({
        mesh,
        baseY: y,
        baseOpacity: opacity,
        // Deterministic in the district's own coordinates — no RNG, so the
        // same city always breathes the same way.
        phase: (rect.x * 0.7 + rect.y * 1.3 + i * 2.1) % 6.283,
      });
    }
  }

  /** Slow breathing; deterministic in `elapsed`, and never called under
   * `?settle=1` — the composition root gates it exactly as it gates the
   * fires. Only opacity and height move: drifting the planes sideways would
   * take the fog outside the district rect it is a statement about. */
  tick(delta: number): void {
    this.elapsed += delta;
    const t = this.elapsed;
    for (const layer of this.layers) {
      const breath = Math.sin(t * 0.31 + layer.phase);
      layer.mesh.material.opacity = layer.baseOpacity * (0.82 + 0.18 * breath);
      layer.mesh.position.y = layer.baseY + 0.015 * breath;
    }
  }

  setVisible(on: boolean): void {
    this.visible = on;
    this.group.visible = on;
  }

  toggle(): void {
    this.setVisible(!this.visible);
  }
}
