/**
 * The flat-colour palette pass the plan calls the de-risking first step: every
 * colour the 3D scene uses, in one place. Sprite-atlas sampling is an additive
 * follow-up; nothing else may hardcode a colour.
 *
 * Ground colours track the 2D map so the two renderers stay recognisably the
 * same city (checkerboard grass, grey streets, yellow arterials, red plant).
 */

import * as THREE from "three";

export const GROUND: Record<string, THREE.Color> = {
  grass: new THREE.Color("#4a9e4d"),
  grass_alt: new THREE.Color("#459548"),
  road: new THREE.Color("#5a5a62"),
  power_line: new THREE.Color("#d9c445"),
  plant: new THREE.Color("#b03a37"),
  lot: new THREE.Color("#3f3f46"), // the pad a building stands on
  water: new THREE.Color("#3d6fb0"), // in the legend; the generator never emits it
};

export const ZONE: Record<string, THREE.Color> = {
  industrial: new THREE.Color("#c47f45"),
  commercial: new THREE.Color("#5b8dd9"),
  residential: new THREE.Color("#79c96e"),
};

/** Unpowered lots: same box, dimmed to ~30% and desaturated — reads as dark
 * from any angle with no second material. Mirrors the 2D 55%-black overlay. */
export function dimmed(color: THREE.Color): THREE.Color {
  const hsl = { h: 0, s: 0, l: 0 };
  color.getHSL(hsl);
  return new THREE.Color().setHSL(hsl.h, hsl.s * 0.35, hsl.l * 0.3);
}

export const SKY = new THREE.Color("#b8d4e8");
export const PLANT_BODY = new THREE.Color("#8f2f2c");
export const PLANT_GLOW = new THREE.Color("#ffd23e");
export const SELECTION = new THREE.Color("#ffffff");

// ?flat=1 verification mode: MeshBasicMaterial, no AA, no lights, so an e2e
// test can count exact-colour pixels. These two must stay unique — nothing
// else in the scene may render either value.
export const FLAT_PLANT = "#ff3223"; // the plant body, for "plant is painted"
export const FLAT_SENTINEL = "#010203"; // the clear colour, for "no viewport holes"
