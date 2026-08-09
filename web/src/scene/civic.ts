/**
 * Civic buildings on the western utility strip (Stephen, 2026-08-05):
 *
 * - The PUBLIC LIBRARY — "where we store the context and other documentation".
 *   Classical box with a colonnade; its inspector panel is the city's context
 *   inventory (measured documentation coverage, all counts of real artifacts).
 * - The FIREHOUSE — where fire response dispatches from. Red station with a
 *   garage door; its panel lists the active fires and says plainly whether an
 *   AI responder is connected (in the local version it is not — named
 *   absence, not a fake siren).
 *
 * Every mesh carries `userData.key` so picking resolves them like the plant.
 */

import * as THREE from "three";
import { CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";
import type { CityDocument } from "../contract";

export const LIBRARY_KEY = "__library__";
export const FIREHOUSE_KEY = "__firehouse__";

function label(text: string): CSS2DObject {
  const el = document.createElement("div");
  el.className = "district-label";
  el.textContent = text;
  return new CSS2DObject(el);
}

function stamp(group: THREE.Group, key: string): THREE.Group {
  group.traverse((o) => {
    o.userData.key = key;
  });
  return group;
}

export function buildLibrary(doc: CityDocument): THREE.Group | null {
  if (!doc.library) return null;
  const { x, y } = doc.library;
  const group = new THREE.Group();
  const marble = new THREE.MeshBasicMaterial({ color: "#e8e2d0" });
  const dark = new THREE.MeshBasicMaterial({ color: "#b8b2a0" });

  const base = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.16, 1.1), dark);
  base.position.set(x + 0.5, 0.08, y + 0.5);
  const hall = new THREE.Mesh(new THREE.BoxGeometry(1.3, 0.62, 0.9), marble);
  hall.position.set(x + 0.5, 0.16 + 0.31, y + 0.5);
  group.add(base, hall);
  for (let i = 0; i < 4; i += 1) {
    const column = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.62, 6), marble);
    column.position.set(x + 0.5 - 0.48 + i * 0.32, 0.16 + 0.31, y + 0.5 + 0.5);
    group.add(column);
  }
  const pediment = new THREE.Mesh(new THREE.BoxGeometry(1.44, 0.16, 1.04), dark);
  pediment.position.set(x + 0.5, 0.16 + 0.62 + 0.08, y + 0.5);
  group.add(pediment);

  const tag = label("library");
  tag.position.set(x + 0.5, 1.2, y + 0.5);
  group.add(tag);
  return stamp(group, LIBRARY_KEY);
}

export function buildFirehouse(doc: CityDocument): THREE.Group | null {
  if (!doc.firehouse) return null;
  const { x, y } = doc.firehouse;
  const group = new THREE.Group();
  const red = new THREE.MeshBasicMaterial({ color: "#b03028" });
  const door = new THREE.MeshBasicMaterial({ color: "#e0d8c8" });

  const station = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.7, 1.0), red);
  station.position.set(x + 0.5, 0.35, y + 0.5);
  const garage = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.44, 0.05), door);
  garage.position.set(x + 0.5, 0.22, y + 0.5 + 0.5);
  const tower = new THREE.Mesh(new THREE.BoxGeometry(0.3, 1.1, 0.3), red);
  tower.position.set(x + 0.5 + 0.45, 0.55, y + 0.5 - 0.25);
  group.add(station, garage, tower);

  const tag = label("firehouse");
  tag.position.set(x + 0.5, 1.4, y + 0.5);
  group.add(tag);
  return stamp(group, FIREHOUSE_KEY);
}
