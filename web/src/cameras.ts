/**
 * OrbitControls by default, framed on the document's `focus` box -- the 3D
 * analogue of `app.initial_camera`, and what makes a linear-pipeline strip
 * livable. `F` toggles FlyControls, `Home` reframes.
 *
 * The opening distance is solved from the focus diagonal and the fov so the
 * whole box fits at ~45° pitch, not guessed: guessing is how the 2D app once
 * shipped with its plant eight tiles off-screen.
 */

import * as THREE from "three";
import { FlyControls } from "three/addons/controls/FlyControls.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import type { CityDocument } from "./contract";

const PITCH = Math.PI / 4;
const MARGIN = 1.25;

export class Cameras {
  readonly camera: THREE.PerspectiveCamera;
  private orbit: OrbitControls;
  private fly: FlyControls;
  private flying = false;
  private home: { position: THREE.Vector3; target: THREE.Vector3 };

  constructor(doc: CityDocument, dom: HTMLElement) {
    this.camera = new THREE.PerspectiveCamera(50, 1, 0.1, 6000);

    const f = doc.focus;
    const target = new THREE.Vector3((f.min_x + f.max_x + 1) / 2, 0, (f.min_y + f.max_y + 1) / 2);
    const spanX = f.max_x - f.min_x + 1;
    const spanZ = f.max_y - f.min_y + 1;
    const diagonal = Math.hypot(spanX, spanZ);
    const distance = Math.max(
      12,
      ((diagonal / 2) * MARGIN) / Math.tan((this.camera.fov * Math.PI) / 360),
    );

    // From the south at 45°, so grid-north (low y) is up-screen like the 2D map.
    const position = target
      .clone()
      .add(new THREE.Vector3(0, Math.sin(PITCH) * distance, Math.cos(PITCH) * distance));
    this.home = { position, target };

    this.camera.position.copy(position);
    this.orbit = new OrbitControls(this.camera, dom);
    this.orbit.target.copy(target);
    this.orbit.enableDamping = true;
    this.orbit.maxPolarAngle = Math.PI / 2 - 0.02; // never below the ground
    this.orbit.update();

    this.fly = new FlyControls(this.camera, dom);
    this.fly.movementSpeed = Math.max(10, distance / 3);
    this.fly.rollSpeed = 0.5;
    this.fly.dragToLook = true;
    this.fly.enabled = false;

    window.addEventListener("keydown", (event) => {
      const tag = (event.target as HTMLElement | null)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      if (event.key === "f" || event.key === "F") this.toggleFly();
      if (event.key === "Home" || event.key === "h") this.reframe();
    });
  }

  get mode(): "orbit" | "fly" {
    return this.flying ? "fly" : "orbit";
  }

  toggleFly(): void {
    this.flying = !this.flying;
    this.orbit.enabled = !this.flying;
    this.fly.enabled = this.flying;
    document.body.dataset.camera = this.mode;
  }

  reframe(): void {
    if (this.flying) this.toggleFly();
    this.camera.position.copy(this.home.position);
    this.orbit.target.copy(this.home.target);
    this.orbit.update();
  }

  // --- flyTo: the HUD's "every number is a door" enabler -------------------
  private flight: {
    fromPos: THREE.Vector3;
    toPos: THREE.Vector3;
    fromTarget: THREE.Vector3;
    toTarget: THREE.Vector3;
    t: number;
  } | null = null;

  /** Glide to frame a tile (a building), keeping the current viewing angle
   * but closing to a readable distance. ~0.6 s ease-in-out. */
  flyTo(x: number, z: number, height = 2): void {
    if (this.flying) this.toggleFly();
    const target = new THREE.Vector3(x, height / 2, z);
    const offset = this.camera.position.clone().sub(this.orbit.target);
    const distance = Math.min(Math.max(offset.length() * 0.45, 10), 26);
    offset.setLength(distance);
    this.flight = {
      fromPos: this.camera.position.clone(),
      toPos: target.clone().add(offset),
      fromTarget: this.orbit.target.clone(),
      toTarget: target,
      t: 0,
    };
  }

  /** Named poses for the e2e suite: deterministic viewpoints the framing
   * tests can name instead of scripting drags. `top` keeps the whole frustum
   * on the ground so the no-holes sentinel test sees no legitimate sky. */
  setPose(name: "home" | "top" | "low"): void {
    if (this.flying) this.toggleFly();
    const target = this.home.target;
    const distance = this.home.position.distanceTo(target);
    if (name === "home") {
      this.camera.position.copy(this.home.position);
    } else if (name === "top") {
      this.camera.position.set(target.x, distance * 0.85, target.z + 0.01);
    } else {
      const pitch = Math.PI / 12; // 15 degrees: shallow, sky in frame
      this.camera.position.set(
        target.x + Math.sin(0.6) * Math.cos(pitch) * distance,
        Math.sin(pitch) * distance,
        target.z + Math.cos(0.6) * Math.cos(pitch) * distance,
      );
    }
    this.orbit.target.copy(target);
    this.orbit.update();
  }

  /** Orbit pose as plain data, for surviving an R-reload via sessionStorage. */
  serialize(): { position: number[]; target: number[] } {
    return {
      position: this.camera.position.toArray(),
      target: this.orbit.target.toArray(),
    };
  }

  restore(pose: { position: number[]; target: number[] }): void {
    this.camera.position.fromArray(pose.position);
    this.orbit.target.fromArray(pose.target);
    this.orbit.update();
  }

  resize(width: number, height: number): void {
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
  }

  tick(delta: number): void {
    if (this.flight) {
      this.flight.t = Math.min(1, this.flight.t + delta / 0.6);
      const t = this.flight.t;
      const ease = t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
      this.camera.position.lerpVectors(this.flight.fromPos, this.flight.toPos, ease);
      this.orbit.target.lerpVectors(this.flight.fromTarget, this.flight.toTarget, ease);
      if (t >= 1) this.flight = null;
    }
    if (this.flying) this.fly.update(delta);
    else this.orbit.update();
  }
}
