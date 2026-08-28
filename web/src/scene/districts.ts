/**
 * District footprints and labels -- the thing `CityMap.districts` was exposed
 * for. A translucent plate just above the terrain marks each schema's square;
 * the label is a CSS2DObject, so it is crisp DOM text needing no font atlas,
 * and `page.screenshot()` captures it.
 */

import * as THREE from "three";
import { CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";
import type { CityDocument } from "../contract";

export function buildDistricts(doc: CityDocument): THREE.Group {
  const group = new THREE.Group();

  for (const district of doc.districts) {
    const plate = new THREE.Mesh(
      new THREE.PlaneGeometry(district.w, district.h),
      new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.14,
        depthWrite: false,
      }),
    );
    plate.rotateX(-Math.PI / 2);
    plate.position.set(district.x + district.w / 2, 0.02, district.y + district.h / 2);

    const edges = new THREE.LineSegments(
      new THREE.EdgesGeometry(plate.geometry),
      new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.35 }),
    );
    edges.rotation.copy(plate.rotation);
    edges.position.copy(plate.position);

    const el = document.createElement("div");
    el.className = "district-label";
    el.textContent = district.schema;
    const label = new CSS2DObject(el);
    // Over the district's near corner rather than its centre, so a tall
    // building in the middle does not sit on top of the text — and just
    // INSIDE the plate's one-tile padding ring (building-free by
    // construction), so the label always intersects its own plate on screen
    // however tight the city gets. (Floating 0.4 outside broke the framing
    // spec when streets v3 shrank the demo.)
    label.position.set(district.x + 1, 0.5, district.y + 0.5);

    group.add(plate, edges, label);
  }
  return group;
}
