/**
 * The power plant: the database itself, the one landmark on the map. Built to
 * read as a landmark from any distance -- taller than a max-density building,
 * with an emissive core no lighting angle can darken.
 */

import * as THREE from "three";
import type { CityDocument } from "../contract";
import { FLAT_PLANT, PLANT_BODY, PLANT_GLOW } from "../palette";

export const PLANT_KEY = "__plant__";

export function buildPlant(doc: CityDocument, flat = false): THREE.Group {
  const group = new THREE.Group();

  // In ?flat=1 the body takes the unique FLAT_PLANT colour so the e2e suite
  // can assert "the plant is painted in the viewport" by exact pixel count.
  const body = new THREE.Mesh(
    new THREE.CylinderGeometry(0.55, 0.7, 3.2, 12),
    flat
      ? new THREE.MeshBasicMaterial({ color: FLAT_PLANT })
      : new THREE.MeshLambertMaterial({ color: PLANT_BODY }),
  );
  body.position.y = 1.6;

  const core = new THREE.Mesh(
    new THREE.SphereGeometry(0.42, 16, 12),
    new THREE.MeshBasicMaterial({ color: flat ? FLAT_PLANT : PLANT_GLOW }),
  );
  core.position.y = 3.4;

  group.add(body, core);
  if (!flat) {
    const glow = new THREE.PointLight(PLANT_GLOW, 18, 14);
    glow.position.y = 3.6;
    group.add(glow);
  }
  group.position.set(doc.plant.x + 0.5, 0, doc.plant.y + 0.5);
  // Picking resolves against descendants; tag them all back to the plant.
  group.traverse((child) => (child.userData.key = PLANT_KEY));
  return group;
}
