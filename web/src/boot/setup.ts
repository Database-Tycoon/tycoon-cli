/**
 * Three.js infrastructure: renderer, labels, scene, lights, camera.
 *
 * This module handles ONLY the low-level WebGL setup — the canvas, the
 * renderer, the scene, and the camera. Everything else (HUD, overlays,
 * input, the animation loop) lives in separate modules that receive the
 * camera and scene from here.
 */

import * as THREE from "three";
import { CSS2DRenderer } from "three/addons/renderers/CSS2DRenderer.js";
import type { CityDocument } from "../contract";
import { loadCity } from "../contract";
import { Guests } from "../mechanics/guests";
import { Cameras } from "../cameras";
import { FLAT_SENTINEL, SKY } from "../palette";
import { GuestLayer } from "../scene/guest_layer";
import { VehicleLayer } from "../scene/vehicles";
import { hashSeed, mulberry32 } from "../sim/rng";
import { mountCity, type MountedCity } from "./mount";

/**
 * What boot produces once. `doc`, `city` and `guests` are the BOOT-TIME
 * values and are never replaced: this module has no refresh of its own.
 *
 * Re-reading the catalog on `R` belongs entirely to the HUD, which owns the
 * other half of the cycle — it holds the handle it must unmount, re-points the
 * picker at the new buildings, and restores the selection. A second refresh
 * here would mount a city nobody holds a handle to, so nothing could ever
 * take it off the scene again. That is exactly what used to happen.
 *
 * So read `hud.doc()` and `hud.city()` for what is on the screen now; the
 * fields below answer only for the first frame.
 */
export interface SetupResult {
  renderer: THREE.WebGLRenderer;
  labels: CSS2DRenderer;
  scene: THREE.Scene;
  app: HTMLElement;
  camera: import("../cameras").Cameras;
  doc: CityDocument;
  city: MountedCity;
  guests: Guests;
  vehicleLayer: VehicleLayer;
  guestLayer: GuestLayer;
  seedFor: (offset: number) => () => number;
}

export async function setupThree(params: URLSearchParams): Promise<SetupResult> {
  const flat = params.get("flat") === "1";
  const settle = params.get("settle") === "1";
  const showGuests = params.get("guests") === "1";
  const ambient = params.get("ambient") === "1";
  const seedParam = params.get("seed");

  const doc = await loadCity("./city.json");

  const app = document.getElementById("app")!;
  const renderer = new THREE.WebGLRenderer({ antialias: !flat });
  renderer.setPixelRatio(flat ? 1 : Math.min(2, window.devicePixelRatio));
  app.appendChild(renderer.domElement);

  const labels = new CSS2DRenderer();
  labels.domElement.className = "labels";
  app.appendChild(labels.domElement);

  const scene = new THREE.Scene();
  scene.background = flat ? new THREE.Color(FLAT_SENTINEL) : SKY;
  if (!flat) {
    scene.add(new THREE.HemisphereLight(0xdfeeff, 0x4a6a45, 1.1));
    const sun = new THREE.DirectionalLight(0xffffff, 1.6);
    sun.position.set(1, 2.2, 1.4);
    scene.add(sun);
  }

  const vehicleLayer = new VehicleLayer();
  scene.add(vehicleLayer.mesh);
  const guestLayer = new GuestLayer();
  if (showGuests) scene.add(guestLayer.mesh);

  const seedFor = (offset: number) =>
    mulberry32((seedParam ? Number(seedParam) : hashSeed(doc.database.name)) ^ offset);

  // The one mount this module does. Every later mount is the HUD's.
  const city = await mountCity(scene, doc, { flat, settle, ambient, seedFor });
  const guests = new Guests(doc, seedFor(0x9e3779b9));

  const cameras = new Cameras(doc, renderer.domElement);

  return {
    renderer,
    labels,
    scene,
    app,
    camera: cameras,
    doc,
    city,
    guests,
    vehicleLayer,
    guestLayer,
    seedFor,
  };
}
