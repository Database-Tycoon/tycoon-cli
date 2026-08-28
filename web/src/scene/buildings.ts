/**
 * Every catalog object as one instance of a unit box: a single InstancedMesh,
 * <= 500 instances by the loader's cap, height from `target_density`, colour
 * from the resolved zone style, unpowered dimmed via instance colour.
 *
 * Phase F's temporal channels land here too (never in ?flat=1, whose exact
 * colours the pixel tests count):
 * - DECAY: age since last build desaturates toward grey over ~30 days.
 *   null age = UNKNOWN = full colour — unknown must never render as stale.
 * - TINT: build_status "error" shifts the colour toward red.
 * - CONDITION: test_status fail/warn hangs a marker above the roof
 *   (`ConditionMarkers` below).
 *
 * The grow-in is client-side presentation, exactly as the contract intends:
 * the document ships the target and this module animates 0 -> target itself.
 * `?settle=1` jumps straight to the target so screenshots are deterministic.
 */

import * as THREE from "three";
import type { CityDocument, LotRecord } from "../contract";
import { ZONE, dimmed } from "../palette";

const DECAY_FULL_S = 30 * 86400; // fully decayed at ~30 days
const DECAY_FLOOR = 0.35; // never below this saturation: old, not invisible
const ERROR_TINT = new THREE.Color("#c03030");

/** The lot's rendered colour with every Phase F channel applied. */
export function lotColor(lot: LotRecord): THREE.Color {
  const zone = ZONE[lot.zone_style] ?? ZONE.residential!;
  const color = (lot.powered ? zone : dimmed(zone)).clone();

  if (lot.last_build_age_s !== null) {
    const freshness = Math.max(DECAY_FLOOR, 1 - lot.last_build_age_s / DECAY_FULL_S);
    const hsl = { h: 0, s: 0, l: 0 };
    color.getHSL(hsl);
    color.setHSL(hsl.h, hsl.s * freshness, hsl.l);
  }
  if (lot.build_status === "error") {
    color.lerp(ERROR_TINT, 0.45);
  }
  return color;
}

const FOOT = 0.72; // building footprint inside its 1-tile pad
const GROW_SECONDS = 1.2;
const MIN_H = 0.35;
const H_SCALE = 0.14; // height = 0.14 * rows^(1/3): 1k -> 1.4, 60k -> 5.5, 1M -> 14

/** Continuous height from the REAL row count (cube root, so a 60k-row table
 * visibly towers over a 1.5k one — Stephen: "size to scale with row counts").
 * The decade `target_density` survives for attraction and the contract; the
 * skyline now reads magnitude directly. */
export function heightFromRows(rows: number): number {
  return Math.max(MIN_H, H_SCALE * Math.cbrt(Math.max(0, rows)));
}

/** Per-lot height resolver for a document (row counts live on objects). */
export function makeHeights(doc: CityDocument): (lot: LotRecord) => number {
  const rows = new Map(doc.objects.map((o) => [o.key, o.row_count]));
  return (lot) => heightFromRows(rows.get(lot.object_key) ?? 0);
}

export class Buildings {
  readonly group = new THREE.Group();
  readonly mesh: THREE.InstancedMesh;
  private roof: THREE.InstancedMesh;
  private base: THREE.InstancedMesh;
  readonly lots: LotRecord[];
  readonly heightOf: (lot: LotRecord) => number;
  private progress: number;
  // Per-lot 0..1 overrides while a build replay plays; null = normal heights.
  private replayProgress: number[] | null = null;

  constructor(doc: CityDocument, settle: boolean, flat = false) {
    this.lots = doc.lots;
    this.heightOf = makeHeights(doc);
    this.progress = settle || doc.lots.length === 0 ? 1 : 0;

    // Origin at the base, so scaling in y grows a building out of the ground
    // instead of through it.
    const box = new THREE.BoxGeometry(1, 1, 1);
    box.translate(0, 0.5, 0);
    const count = Math.max(1, doc.lots.length);

    this.mesh = new THREE.InstancedMesh(
      box,
      flat ? new THREE.MeshBasicMaterial() : new THREE.MeshLambertMaterial(),
      count,
    );
    // Roof cap and plinth: the two cheapest cues that turn a box into a
    // building. Same instancing, darker shades of the body colour.
    this.roof = new THREE.InstancedMesh(box.clone(), new THREE.MeshLambertMaterial(), count);
    this.base = new THREE.InstancedMesh(box.clone(), new THREE.MeshLambertMaterial(), count);
    this.mesh.count = this.roof.count = this.base.count = doc.lots.length;

    const shade = new THREE.Color();
    for (const [i, lot] of doc.lots.entries()) {
      // Flat mode keeps the exact zone colours the pixel tests count; the
      // temporal channels only colour the real render.
      const zone = ZONE[lot.zone_style] ?? ZONE.residential!;
      const body = flat ? (lot.powered ? zone : dimmed(zone)) : lotColor(lot);
      this.mesh.setColorAt(i, body);
      this.roof.setColorAt(i, shade.copy(body).multiplyScalar(0.55));
      this.base.setColorAt(i, shade.copy(body).multiplyScalar(0.4));
    }
    for (const m of [this.mesh, this.roof, this.base]) {
      if (m.instanceColor) m.instanceColor.needsUpdate = true;
    }
    this.group.add(this.mesh, ...(flat ? [] : [this.roof, this.base]));
    if (flat) this.roof.count = this.base.count = 0; // exact-colour mode: body only
    this.apply();
  }

  /** Advance the grow-in; returns false once settled so the loop can stop
   * re-uploading matrices every frame. */
  tick(delta: number): boolean {
    if (this.progress >= 1) return false;
    this.progress = Math.min(1, this.progress + delta / GROW_SECONDS);
    this.apply();
    return true;
  }

  /** Per-lot height factors while a build replay plays (index-aligned with
   * `lots`); null returns to normal heights. Re-uploads matrices either way. */
  setReplayProgress(values: number[] | null): void {
    this.replayProgress = values;
    this.apply();
  }

  private apply(): void {
    const m = new THREE.Matrix4();
    // Ease-out, so tall buildings decelerate into place instead of snapping.
    const eased = 1 - (1 - this.progress) ** 3;
    for (const [i, lot] of this.lots.entries()) {
      const factor = this.replayProgress ? (this.replayProgress[i] ?? 1) : eased;
      const h = Math.max(0.01, this.heightOf(lot) * factor);
      // A 2x2 lot keeps the same pad margin around a footprint twice as wide.
      const fw = lot.w - (1 - FOOT);
      const fd = lot.h - (1 - FOOT);
      const cx = lot.x + lot.w / 2;
      const cz = lot.y + lot.h / 2;
      m.makeScale(fw, h, fd);
      m.setPosition(cx, 0, cz);
      this.mesh.setMatrixAt(i, m);
      m.makeScale(fw + 0.08, 0.055, fd + 0.08);
      m.setPosition(cx, h, cz);
      this.roof.setMatrixAt(i, m);
      m.makeScale(fw + 0.1, Math.min(0.12, h), fd + 0.1);
      m.setPosition(cx, 0, cz);
      this.base.setMatrixAt(i, m);
    }
    for (const mm of [this.mesh, this.roof, this.base]) {
      mm.instanceMatrix.needsUpdate = true;
      mm.computeBoundingSphere();
    }
  }
}

/**
 * CONDITION markers: a small octahedron floating over any building whose
 * test_status is fail (red) or warn (amber). No marker means "no failing
 * signal", which covers both "tests pass" and "unknown" — absence of
 * knowledge must not look like absence of problems' opposite either, so the
 * inspector carries the exact words while the skyline only flags trouble.
 */
export class ConditionMarkers {
  readonly group = new THREE.Group();

  constructor(doc: CityDocument) {
    const heightOf = makeHeights(doc);
    // Tests: octahedra for warn (amber, full size) and pass (small green --
    // "tested and passing" must not look identical to "never tested").
    // FAIL gets no marker here: failing buildings are ON FIRE (fire.ts).
    const tested = doc.lots.filter(
      (lot) => lot.test_status !== null && lot.test_status !== "fail",
    );
    if (tested.length) {
      const mesh = new THREE.InstancedMesh(
        new THREE.OctahedronGeometry(1),
        new THREE.MeshBasicMaterial(),
        tested.length,
      );
      const m = new THREE.Matrix4();
      const color = new THREE.Color();
      for (const [i, lot] of tested.entries()) {
        const pass = lot.test_status === "pass";
        const scale = pass ? 0.15 : 0.28;
        m.makeRotationY(Math.PI / 4);
        m.scale(new THREE.Vector3(scale, scale, scale));
        m.setPosition(lot.x + lot.w / 2, heightOf(lot) + 0.55, lot.y + lot.h / 2);
        mesh.setMatrixAt(i, m);
        color.set(lot.test_status === "warn" ? "#e0a832" : "#5ee07a");
        mesh.setColorAt(i, color);
      }
      mesh.frustumCulled = false;
      this.group.add(mesh);
    }

    // Source freshness: dbt's SLA verdict as a cone -- a different shape for a
    // different judgement. Only late sources flag; pass renders nothing (a
    // fresh source is just a normal building).
    const late = doc.lots.filter(
      (lot) => lot.freshness_status === "warn" || lot.freshness_status === "error",
    );
    if (late.length) {
      const mesh = new THREE.InstancedMesh(
        new THREE.ConeGeometry(0.22, 0.44, 8),
        new THREE.MeshBasicMaterial(),
        late.length,
      );
      const m = new THREE.Matrix4();
      const color = new THREE.Color();
      for (const [i, lot] of late.entries()) {
        // Offset sideways so a source that is both late and failing tests
        // shows both verdicts instead of hiding one inside the other.
        const offset = lot.test_status !== null ? 0.34 : 0;
        m.identity();
        m.setPosition(lot.x + lot.w / 2 + offset, heightOf(lot) + 0.5, lot.y + lot.h / 2);
        mesh.setMatrixAt(i, m);
        color.set(lot.freshness_status === "error" ? "#e03535" : "#e0a832");
        mesh.setColorAt(i, color);
      }
      mesh.frustumCulled = false;
      this.group.add(mesh);
    }
  }
}
