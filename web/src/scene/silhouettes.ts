/**
 * Type-driven silhouettes: three architectural motifs earned by facts.
 *
 * - CLOCK SPIRE: the table carries a temporal column — event/time data reads
 *   as a clock tower from across the map.
 * - ANTENNA: a nested column (JSON/STRUCT/LIST/MAP) — semi-structured data
 *   wears machinery on the roof.
 * - GOLD DOORWAY: a declared unique/primary-key test — the table has a proper
 *   entrance, keyed access.
 *
 * All instanced, all fact-derived, all skipped in ?flat=1.
 */

import * as THREE from "three";
import type { CityDocument } from "../contract";
import { typeFamily } from "../contract";
import { makeHeights } from "./buildings";
// The crane rule lives with the chip that counts it, so the strip and the
// skyline can never disagree about what "recently changed shape" means.
import { DRIFT_RECENT_S as CRANE_RECENT_S } from "../ui/health";

const SPIRE = new THREE.Color("#d8d2ee");
const ANTENNA = new THREE.Color("#9a93b8");
const GOLD = new THREE.Color("#e8b93e");
const CRANE = new THREE.Color("#e07a30");

export function buildSilhouettes(doc: CityDocument): THREE.Group {
  const group = new THREE.Group();
  const heightOf = makeHeights(doc);
  const byKey = new Map(doc.objects.map((o) => [o.key, o]));

  const spires: THREE.Matrix4[] = [];
  const antennas: THREE.Matrix4[] = [];
  const doors: THREE.Matrix4[] = [];
  const craneMasts: THREE.Matrix4[] = [];
  const craneBooms: THREE.Matrix4[] = [];

  for (const lot of doc.lots) {
    const obj = byKey.get(lot.object_key);
    if (!obj) continue;
    const h = heightOf(lot);
    const families = obj.columns.map((c) => typeFamily(c.type));

    if (families.includes("temporal")) {
      const m = new THREE.Matrix4();
      m.makeScale(1, 1 + h * 0.18, 1);
      m.setPosition(lot.x + lot.w / 2, h + 0.06, lot.y + lot.h / 2);
      spires.push(m);
    }
    if (families.includes("nested")) {
      const m = new THREE.Matrix4();
      m.setPosition(lot.x + lot.w / 2 + 0.24, h + 0.3, lot.y + lot.h / 2 - 0.24);
      antennas.push(m);
    }
    // Under construction: the schema changed in the last week. A mast beside
    // the building and a boom over the roof -- drift you can see driving by.
    if (lot.schema_drift_age_s !== null && lot.schema_drift_age_s < CRANE_RECENT_S) {
      const mast = new THREE.Matrix4();
      mast.makeScale(1, h + 0.9, 1);
      mast.setPosition(lot.x + lot.w / 2 - 0.42, (h + 0.9) / 2, lot.y + lot.h / 2 - 0.42);
      craneMasts.push(mast);
      const boom = new THREE.Matrix4();
      boom.makeRotationZ(Math.PI / 2);
      boom.setPosition(lot.x + lot.w / 2 - 0.12, h + 0.86, lot.y + lot.h / 2 - 0.42);
      craneBooms.push(boom);
    }
    const hasUnique = obj.dbt?.tests.some((t) => /^(unique|primary)/i.test(t.name)) ?? false;
    if (hasUnique) {
      const m = new THREE.Matrix4();
      m.setPosition(lot.x + lot.w / 2, 0.14, lot.y + lot.h / 2 + 0.36);
      doors.push(m);
    }
  }

  const add = (
    matrices: THREE.Matrix4[],
    geometry: THREE.BufferGeometry,
    color: THREE.Color,
  ) => {
    if (!matrices.length) return;
    const mesh = new THREE.InstancedMesh(
      geometry,
      new THREE.MeshLambertMaterial({ color }),
      matrices.length,
    );
    matrices.forEach((m, i) => mesh.setMatrixAt(i, m));
    mesh.frustumCulled = false;
    group.add(mesh);
  };

  add(spires, new THREE.ConeGeometry(0.12, 0.7, 6), SPIRE);
  add(antennas, new THREE.CylinderGeometry(0.02, 0.02, 0.6, 4), ANTENNA);
  add(doors, new THREE.BoxGeometry(0.2, 0.28, 0.05), GOLD);
  add(craneMasts, new THREE.BoxGeometry(0.06, 1, 0.06), CRANE);
  add(craneBooms, new THREE.BoxGeometry(0.06, 0.8, 0.06), CRANE);
  return group;
}
