/**
 * Failing tests are buildings ON FIRE (Stephen, 2026-08-05). A red dot on the
 * roof never conveyed "this mart is failing" — flames do.
 *
 * Facts only: a fire exists iff `test_status === "fail"`. Each burning
 * building gets a small cluster of emissive flame cones on its roof plus a
 * rising smoke puff; the render loop flickers scale/rotation deterministically
 * from the building's coordinates (no RNG — same city, same flames), and
 * `?settle=1` freezes the flicker so screenshots stay reproducible.
 *
 * `setOverride` lets the run replay take the fires over for the length of a
 * playback: a specific invocation's failures burn instead of the document's
 * standing ones. Still facts only — the override carries dbt's own `error`
 * word for that node in that run — and `setOverride(null)` puts the
 * document-derived fires back. The dispatch fleets take the same override, so
 * the trucks answer the run's fires without knowing a replay exists.
 */

import * as THREE from "three";
import type { CityDocument, LotRecord } from "../contract";
import { makeHeights } from "./buildings";
import { disposeTree } from "./dispose";

const FLAME_COLORS = ["#ff5a1f", "#ffa524", "#ffd75e"];

interface Flame {
  mesh: THREE.Mesh;
  baseY: number;
  baseScale: number;
  phase: number;
}

export class Fires {
  readonly group = new THREE.Group();
  private flames: Flame[] = [];
  private smoke: { mesh: THREE.Mesh; phase: number }[] = [];
  private elapsed = 0;
  private burningCount = 0;
  private heightOf: (lot: LotRecord) => number;
  /** The document's own fires: test_status === "fail". What an override
   * replaces and what `setOverride(null)` restores. */
  private standing: LotRecord[];
  private lots: LotRecord[];

  /** Buildings currently burning — the e2e counting hook. */
  get count(): number {
    return this.burningCount;
  }

  constructor(doc: CityDocument) {
    this.heightOf = makeHeights(doc);
    this.lots = doc.lots;
    this.standing = doc.lots.filter((lot) => lot.test_status === "fail");
    this.build(this.standing);
  }

  /**
   * Burn exactly `keys` instead of the document's failing tests; `null`
   * restores them. A key with no lot on this map simply does not burn — the
   * same rule `edges` and `depends_on` follow, since a fire needs a building.
   */
  setOverride(keys: Set<string> | null): void {
    this.build(keys === null ? this.standing : this.lots.filter((l) => keys.has(l.object_key)));
  }

  /** Replace the flames wholesale. Frees the old ones: a replay rebuilds this
   * on every step, and a leak here would grow with the length of the run. */
  private build(burning: LotRecord[]): void {
    disposeTree(this.group);
    this.group.clear();
    this.flames = [];
    this.smoke = [];
    this.burningCount = burning.length;
    for (const lot of burning) this.ignite(lot, this.heightOf(lot));
  }

  private ignite(lot: LotRecord, height: number): void {
    // Three flame tongues, offset around the roof centre; sizes vary by a
    // coordinate hash so two fires never look like copies.
    const seed = (lot.x * 31 + lot.y * 17) % 7;
    for (let i = 0; i < 3; i += 1) {
      const scale = 0.16 + 0.05 * ((seed + i) % 3);
      const flame = new THREE.Mesh(
        new THREE.ConeGeometry(scale, scale * 2.6, 6),
        new THREE.MeshBasicMaterial({
          color: FLAME_COLORS[i % FLAME_COLORS.length],
          transparent: true,
          opacity: 0.9,
        }),
      );
      const angle = ((seed + i) / 3) * Math.PI * 2;
      flame.position.set(
        lot.x + lot.w / 2 + Math.cos(angle) * 0.14 * lot.w,
        height + scale * 1.3,
        lot.y + lot.h / 2 + Math.sin(angle) * 0.14 * lot.h,
      );
      this.group.add(flame);
      this.flames.push({
        mesh: flame,
        baseY: flame.position.y,
        baseScale: 1,
        phase: seed + i * 2.1,
      });
    }
    const puff = new THREE.Mesh(
      new THREE.SphereGeometry(0.14, 6, 5),
      new THREE.MeshBasicMaterial({ color: "#5a5a60", transparent: true, opacity: 0.55 }),
    );
    puff.position.set(lot.x + lot.w / 2, height + 0.75, lot.y + lot.h / 2);
    this.group.add(puff);
    this.smoke.push({ mesh: puff, phase: seed });
  }

  /** Flicker; deterministic in `elapsed`, frozen entirely under ?settle=1. */
  tick(delta: number): void {
    this.elapsed += delta;
    const t = this.elapsed;
    for (const flame of this.flames) {
      const flicker = 1 + 0.22 * Math.sin(t * 11 + flame.phase) * Math.sin(t * 5.3 + flame.phase);
      flame.mesh.scale.set(flicker, 1 + 0.3 * Math.abs(Math.sin(t * 7 + flame.phase)), flicker);
      flame.mesh.rotation.y = t * 1.5 + flame.phase;
    }
    for (const puff of this.smoke) {
      // The puff loops a slow 1.2-tile rise, fading as it climbs.
      const cycle = (t * 0.35 + puff.phase * 0.13) % 1;
      puff.mesh.position.y = puff.mesh.userData.baseY ??= puff.mesh.position.y;
      puff.mesh.position.y = (puff.mesh.userData.baseY as number) + cycle * 1.2;
      (puff.mesh.material as THREE.MeshBasicMaterial).opacity = 0.55 * (1 - cycle);
      const grow = 1 + cycle * 1.6;
      puff.mesh.scale.set(grow, grow, grow);
    }
  }
}
