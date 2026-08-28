/**
 * Wear and tear: stale sources look dilapidated (Stephen, 2026-08-05:
 * "Source freshness is also something we should monitor visually. Maybe
 * allow the building to show signs of wear and tear, and they need to have
 * contractors come and fix it").
 *
 * Facts only: the trigger is dbt's sources.json SLA verdict
 * (`freshness_status`), the same measured signal the cone markers restate.
 * warn = boarded windows on the south face; error = more boards plus a
 * grime skirt around the base. Deterministic placement from the lot's
 * coordinates — no RNG, `?settle=1`-stable. The companion repair vans live
 * in firetrucks.ts (RepairVans).
 */

import * as THREE from "three";
import type { CityDocument } from "../contract";
import { makeHeights } from "./buildings";

const FOOT = 0.72; // must match buildings.ts
const BOARD = "#b3945f"; // weathered plywood — light enough to read on dark bodies
const GRIME = "#23231f";

export class Wear {
  readonly group = new THREE.Group();
  private worn = 0;

  /** Buildings showing wear — the e2e counting hook. */
  get count(): number {
    return this.worn;
  }

  constructor(doc: CityDocument) {
    const heightOf = makeHeights(doc);
    const boards: { x: number; y: number; z: number; w: number }[] = [];
    const grime: { x: number; z: number; w: number; d: number }[] = [];

    for (const lot of doc.lots) {
      const status = lot.freshness_status;
      if (status !== "warn" && status !== "error") continue;
      this.worn += 1;

      const h = heightOf(lot);
      const cx = lot.x + lot.w / 2;
      const southZ = lot.y + lot.h - (1 - FOOT) / 2 + 0.012; // just off the face
      const fw = lot.w - (1 - FOOT);
      const n = status === "error" ? 4 : 2;
      for (let i = 0; i < n; i++) {
        // Deterministic scatter: coordinates seed the pseudo-positions.
        const seed = lot.x * 31 + lot.y * 17 + i * 13;
        const bx = cx + ((seed % 7) / 7 - 0.5) * (fw - 0.2);
        const by = 0.15 + (((seed * 3) % 11) / 11) * Math.max(0.2, h - 0.35);
        boards.push({ x: bx, y: by, z: southZ, w: 0.16 + (seed % 3) * 0.04 });
      }
      if (status === "error") {
        grime.push({ x: cx, z: lot.y + lot.h / 2, w: fw + 0.14, d: lot.h - (1 - FOOT) + 0.14 });
      }
    }

    if (boards.length) {
      const mesh = new THREE.InstancedMesh(
        new THREE.BoxGeometry(1, 0.12, 0.03),
        new THREE.MeshBasicMaterial({ color: BOARD }),
        boards.length,
      );
      const m = new THREE.Matrix4();
      for (const [i, b] of boards.entries()) {
        m.makeScale(b.w, 1, 1);
        m.setPosition(b.x, b.y, b.z);
        mesh.setMatrixAt(i, m);
      }
      mesh.frustumCulled = false;
      this.group.add(mesh);
    }
    if (grime.length) {
      const mesh = new THREE.InstancedMesh(
        new THREE.BoxGeometry(1, 0.1, 1),
        new THREE.MeshBasicMaterial({ color: GRIME, transparent: true, opacity: 0.8 }),
        grime.length,
      );
      const m = new THREE.Matrix4();
      for (const [i, g] of grime.entries()) {
        m.makeScale(g.w, 1, g.d);
        m.setPosition(g.x, 0.05, g.z);
        mesh.setMatrixAt(i, m);
      }
      mesh.frustumCulled = false;
      this.group.add(mesh);
    }
  }
}
