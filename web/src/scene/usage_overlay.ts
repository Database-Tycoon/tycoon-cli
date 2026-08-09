/**
 * The usage overlay: how much each building is actually EXERCISED, painted
 * from `objects[].usage` — measured run appearances, which vanilla DuckDB can
 * see and query traffic, which it cannot. `src/usage.ts` owns the
 * classification and the scale; this module only draws the answer.
 *
 * Four states, three treatments, and the fourth treatment is deliberately
 * nothing:
 *
 * | state     | treatment                                       |
 * |-----------|-------------------------------------------------|
 * | `busy`    | a bar standing UP over the roof, height ∝ cadence, violet→magenta |
 * | `unrated` | a FLAT pale ring — seen, cadence unknowable |
 * | `quiet`   | a grey cone pointing DOWN, plus a grey lid laid across the roof |
 * | `unknown` | **nothing at all** |
 *
 * Three shapes, three hues, three directions, all in one band above the
 * rooftops so the whole city is scannable in a glance: `quiet` and `unrated`
 * cannot be mistaken for each other or for a short `busy` bar, which matters
 * because confusing them is the exact way this feature would lie. `quiet`
 * gets a second mark — a lid on the actual roof — because it is the one state
 * somebody would act on (a measured, unused table is a deprecation candidate)
 * and a floating marker alone leaves which-building ambiguous from above.
 *
 * `unknown` draws nothing while `quiet` draws something POSITIVE: an absence
 * of paint is never a claim, and the legend names how many objects are in
 * that state, the same way `weather` names an empty cell list rather than
 * painting fair weather over a city nobody judged.
 *
 * Everything floats clear of the condition markers (`buildings.ts` hangs those
 * at roof + ~0.55): a building can be busy, failing its tests and late all at
 * once, and no signal may hide another.
 *
 * `U` toggles it — the binding lives here, as the `Overlay` this class
 * implements, and `ui/overlays.ts` routes the key. The busy bars breathe, so
 * `tick` is gated on `!settle` by the composition root exactly as the fog is.
 */

import * as THREE from "three";
import type { CityDocument, LotRecord, UsageRecord } from "../contract";
import type { UsageState } from "../usage";
import { USAGE_COLOR, busyFraction, classifyUsage, usageSummary } from "../usage";
import type { Overlay } from "../ui/overlays";
import { makeHeights } from "./buildings";

/** Clear of the tallest condition marker (roof + 0.55, half-extent 0.28), so
 * a failing building's octahedron and its usage beacon are both readable. */
const BASE_GAP = 0.95;
const BAR_RADIUS = 0.13;
const BAR_MIN_H = 0.35;
const BAR_MAX_H = 1.9;
/** Flat ring for `unrated`: a shape, not a shorter bar. */
const RING_RADIUS = 0.3;
const RING_TUBE = 0.055;
/** The `quiet` cone hangs in the same band, pointing back down at its roof. */
const CONE_RADIUS = 0.26;
const CONE_HEIGHT = 0.5;
/** The `quiet` lid sits just above the roof cap and overhangs it. */
const LID_THICKNESS = 0.09;
const LID_OVERHANG = 0.1;

const LOW = new THREE.Color(USAGE_COLOR.busyLow);
const HIGH = new THREE.Color(USAGE_COLOR.busyHigh);

/** A lot to paint, with the fact that put it there. */
interface Marked {
  lot: LotRecord;
  usage: UsageRecord;
}

export class UsageOverlay implements Overlay {
  readonly id = "usage";
  readonly key = "u";
  readonly group = new THREE.Group();
  visible = true;
  /** The breathing clock, public so the e2e suite can prove `?settle=1`
   * freezes it rather than merely catching a still-looking frame. */
  elapsed = 0;
  private breathing: THREE.MeshBasicMaterial[] = [];

  /**
   * Instances actually IN THE SCENE — the e2e counting hook.
   *
   * Walked from the live scene graph, not returned from a tally kept beside
   * it, and zero unless this group really hangs off a `THREE.Scene`: a
   * bookkeeping integer can be right while nothing is rendered, and the whole
   * job of this hook is to make "built but never added" read as missing.
   */
  get instanceCount(): number {
    if (!this.inScene) return 0;
    let n = 0;
    this.group.traverse((object) => {
      const mesh = object as THREE.InstancedMesh;
      if (mesh.isInstancedMesh) n += mesh.count;
    });
    return n;
  }

  /**
   * The object keys this overlay actually PAINTED with `state`, sorted.
   *
   * Read back off the meshes in the scene rather than off the buckets that
   * built them, for the same reason as above — and `keysPainted("unknown")`
   * is therefore always empty, which is the honesty rule stated as a query.
   *
   * De-duplicated: `quiet` is marked twice (cone and lid), and this answers
   * "which objects wear this treatment", not "how many meshes carry it" —
   * `instanceCount` is the mesh question.
   */
  keysPainted(state: UsageState): string[] {
    if (!this.inScene) return [];
    const keys = new Set<string>();
    this.group.traverse((object) => {
      if (object.userData.usageState !== state) return;
      for (const key of object.userData.usageKeys as string[]) keys.add(key);
    });
    return [...keys].sort();
  }

  private get inScene(): boolean {
    let node: THREE.Object3D | null = this.group;
    while (node) {
      if ((node as THREE.Scene).isScene) return true;
      node = node.parent;
    }
    return false;
  }

  build(doc: CityDocument): void {
    for (const child of [...this.group.children]) {
      this.group.remove(child);
      const mesh = child as THREE.Mesh;
      mesh.geometry?.dispose();
      (mesh.material as THREE.Material)?.dispose();
    }
    this.breathing = [];
    this.elapsed = 0;

    const usageOf = new Map(doc.objects.map((o) => [o.key, o.usage]));
    const buckets: Record<"busy" | "quiet" | "unrated", Marked[]> = {
      busy: [],
      quiet: [],
      unrated: [],
    };
    for (const lot of doc.lots) {
      // A lot whose object is missing from `objects` is UNKNOWN, not quiet —
      // `?? null` keeps the absent case on the honest branch.
      const usage = usageOf.get(lot.object_key) ?? null;
      const state = classifyUsage(usage);
      // `unknown` has no bucket by construction: there is nothing to draw,
      // and `usage!` below is safe only because of this guard.
      if (state === "unknown") continue;
      buckets[state].push({ lot, usage: usage! });
    }

    const heightOf = makeHeights(doc);
    const baseY = (lot: LotRecord) => heightOf(lot) + BASE_GAP;
    const peak = usageSummary(doc).peakRate;
    if (buckets.busy.length) this.addBars(buckets.busy, baseY, peak);
    if (buckets.unrated.length) this.addRings(buckets.unrated, baseY);
    if (buckets.quiet.length) {
      this.addCones(buckets.quiet, baseY);
      this.addLids(buckets.quiet, heightOf);
    }
    this.group.visible = this.visible;
  }

  /** Busy: a standing bar whose HEIGHT is the cadence and whose COLOUR runs
   * the same ramp — two channels for one fact, so it survives both a small
   * screenshot and a colour-blind reader. */
  private addBars(marked: Marked[], baseY: (lot: LotRecord) => number, peak: number): void {
    const material = new THREE.MeshBasicMaterial({
      transparent: true,
      opacity: 0.95,
      depthWrite: false,
    });
    const geometry = new THREE.CylinderGeometry(BAR_RADIUS, BAR_RADIUS, 1, 10).translate(0, 0.5, 0);
    const mesh = new THREE.InstancedMesh(geometry, material, marked.length);
    const m = new THREE.Matrix4();
    const color = new THREE.Color();
    for (const [i, { lot, usage }] of marked.entries()) {
      const at = busyFraction(usage.rate_per_day!, peak);
      m.makeScale(1, BAR_MIN_H + (BAR_MAX_H - BAR_MIN_H) * at, 1);
      m.setPosition(lot.x + lot.w / 2, baseY(lot), lot.y + lot.h / 2);
      mesh.setMatrixAt(i, m);
      mesh.setColorAt(i, color.copy(LOW).lerp(HIGH, at));
    }
    this.breathing.push(material);
    this.adopt(mesh, "busy", marked);
  }

  /** Seen, cadence unknowable: a flat ring, lying where a bar would stand.
   * Not a short bar — a short bar is a real, low cadence. */
  private addRings(marked: Marked[], baseY: (lot: LotRecord) => number): void {
    const geometry = new THREE.TorusGeometry(RING_RADIUS, RING_TUBE, 6, 18).rotateX(-Math.PI / 2);
    const mesh = new THREE.InstancedMesh(
      geometry,
      new THREE.MeshBasicMaterial({ color: USAGE_COLOR.unrated }),
      marked.length,
    );
    const m = new THREE.Matrix4();
    for (const [i, { lot }] of marked.entries()) {
      m.identity();
      m.setPosition(lot.x + lot.w / 2, baseY(lot), lot.y + lot.h / 2);
      mesh.setMatrixAt(i, m);
    }
    this.adopt(mesh, "unrated", marked);
  }

  /** Measured and little-used: a cone in the beacon band, pointing DOWN at the
   * building it judges — the opposite gesture to a busy bar, at the same
   * height, so one sweep of the eye reads the whole city. */
  private addCones(marked: Marked[], baseY: (lot: LotRecord) => number): void {
    const geometry = new THREE.ConeGeometry(CONE_RADIUS, CONE_HEIGHT, 12).rotateX(Math.PI);
    const mesh = new THREE.InstancedMesh(
      geometry,
      new THREE.MeshBasicMaterial({ color: USAGE_COLOR.quiet }),
      marked.length,
    );
    const m = new THREE.Matrix4();
    for (const [i, { lot }] of marked.entries()) {
      m.identity();
      m.setPosition(lot.x + lot.w / 2, baseY(lot) + CONE_HEIGHT / 2, lot.y + lot.h / 2);
      mesh.setMatrixAt(i, m);
    }
    this.adopt(mesh, "quiet", marked);
  }

  /** Measured and little-used, marked a second time: a grey lid laid over the
   * roof, overhanging the roof cap so it reads as put there rather than as
   * part of the building — and so WHICH building is unambiguous from above. */
  private addLids(marked: Marked[], heightOf: (lot: LotRecord) => number): void {
    const geometry = new THREE.BoxGeometry(1, 1, 1).translate(0, 0.5, 0);
    const mesh = new THREE.InstancedMesh(
      geometry,
      new THREE.MeshBasicMaterial({ color: USAGE_COLOR.quiet }),
      marked.length,
    );
    const m = new THREE.Matrix4();
    for (const [i, { lot }] of marked.entries()) {
      m.makeScale(lot.w - LID_OVERHANG, LID_THICKNESS, lot.h - LID_OVERHANG);
      m.setPosition(lot.x + lot.w / 2, heightOf(lot) + 0.06, lot.y + lot.h / 2);
      mesh.setMatrixAt(i, m);
    }
    this.adopt(mesh, "quiet", marked);
  }

  /** Label the mesh with what it means and which objects it speaks for, then
   * put it in the group. The labels are what `keysPainted` reads back, so
   * they can only ever describe geometry that exists. */
  private adopt(mesh: THREE.InstancedMesh, state: UsageState, marked: Marked[]): void {
    mesh.frustumCulled = false;
    mesh.userData.usageState = state;
    mesh.userData.usageKeys = marked.map((entry) => entry.lot.object_key);
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    this.group.add(mesh);
  }

  /** Slow breathing on the busy bars only — a city that is being used looks
   * alive. Deterministic in `elapsed`, and never called under `?settle=1`. */
  tick(delta: number): void {
    this.elapsed += delta;
    const breath = 0.83 + 0.17 * Math.sin(this.elapsed * 1.7);
    for (const material of this.breathing) material.opacity = 0.95 * breath;
  }

  setVisible(on: boolean): void {
    this.visible = on;
    this.group.visible = on;
  }

  toggle(): void {
    this.setVisible(!this.visible);
  }
}
