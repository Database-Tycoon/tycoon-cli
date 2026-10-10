/**
 * OrbitControls by default, framed on the city's own bounds. `F` toggles
 * FlyControls, `Home` (or `H`) reframes.
 *
 * Every named pose is solved, not guessed: from a fixed viewing direction the
 * camera takes the closest spot from which every building, rooftop dressing
 * included, projects inside the viewport with a small margin and the city
 * sits in the middle. Guessing is how the 2D app once shipped with
 * its plant eight tiles off-screen, and how this one opened on a thin strip
 * of city with its tallest towers cut off at the top (#386).
 */

import * as THREE from "three";
import { FlyControls } from "three/addons/controls/FlyControls.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import type { CityDocument } from "./contract";
import { makeHeights } from "./scene/buildings";
import { classifyUsage } from "./usage";

/** How much of each half of the viewport the city may use, in NDC. */
const FILL = 0.9;
const PLANT_HEIGHT = 4;
const CIVIC_HEIGHT = 1.6;

/** Top of what stands on a roof. A temporal spire grows with the building
 * (silhouettes.ts), and a measured object's usage beacon reaches 2.85 above
 * its roof (usage_overlay.ts). Leaving them out is what cut the tallest
 * towers off at the top of the frame; the beacon is counted only where one
 * is drawn, so a catalog without usage data is not framed for beacons it
 * does not have. */
function rooftop(height: number, measured: boolean): number {
  const spire = 0.8 + 0.13 * height;
  return height + (measured ? Math.max(spire, 2.9) : spire);
}

export type PoseName = "home" | "top" | "low";

/** Unit vectors from the target toward the camera. `home` looks from the
 * south at 45 degrees, so grid-north (low y) is up-screen like the 2D map;
 * `top` keeps the whole frustum on the ground so the no-holes sentinel test
 * sees no legitimate sky; `low` is a shallow 15 degrees with sky in frame. */
const DIRECTIONS: Record<PoseName, THREE.Vector3> = {
  home: new THREE.Vector3(0, Math.SQRT1_2, Math.SQRT1_2),
  top: new THREE.Vector3(0, 1, 0.001).normalize(),
  low: new THREE.Vector3(
    Math.sin(0.6) * Math.cos(Math.PI / 12),
    Math.sin(Math.PI / 12),
    Math.cos(0.6) * Math.cos(Math.PI / 12),
  ),
};

/** The points that must stay on screen: each lot's box up to its rooftop,
 * every district plate, the plant and the civic buildings. */
export function cityPoints(doc: CityDocument): THREE.Vector3[] {
  const points: THREE.Vector3[] = [];
  const box = (x: number, z: number, w: number, d: number, top: number) => {
    for (const px of [x, x + w]) {
      for (const pz of [z, z + d]) {
        points.push(new THREE.Vector3(px, 0, pz), new THREE.Vector3(px, top, pz));
      }
    }
  };
  const heightOf = makeHeights(doc);
  const usageOf = new Map(doc.objects.map((o) => [o.key, o.usage]));
  for (const lot of doc.lots) {
    const measured = classifyUsage(usageOf.get(lot.object_key) ?? null) !== "unknown";
    box(lot.x, lot.y, lot.w, lot.h, rooftop(heightOf(lot), measured));
  }
  for (const d of doc.districts) box(d.x, d.y, d.w, d.h, 0);
  box(doc.plant.x, doc.plant.y, 1, 1, PLANT_HEIGHT);
  for (const civic of [doc.library, doc.firehouse]) {
    if (civic) box(civic.x - 0.25, civic.y, 1.5, 1, CIVIC_HEIGHT);
  }
  return points;
}

interface Pose {
  position: THREE.Vector3;
  target: THREE.Vector3;
}

/** The closest pose looking along `direction` at which every point projects
 * within `FILL` of the viewport centre, with the city centred.
 *
 * With the orientation fixed, each edge of the view is a plane through the
 * camera, and "every point on the inner side" is linear in the camera's
 * position. So the answer is solved exactly rather than searched: the left
 * and right planes pinned to their outermost points fix the camera's
 * sideways position and how close it may come; top and bottom do the same
 * vertically; the camera takes the more distant of the two. */
export function fitPose(
  points: THREE.Vector3[],
  direction: THREE.Vector3,
  fov: number,
  aspect: number,
): Pose {
  const basis = new THREE.Object3D();
  basis.lookAt(direction.clone().negate());
  basis.updateMatrixWorld();
  // Object3D.lookAt points +z at the target, so +z is forward here.
  const right = new THREE.Vector3().setFromMatrixColumn(basis.matrixWorld, 0).negate();
  const up = new THREE.Vector3().setFromMatrixColumn(basis.matrixWorld, 1);
  const forward = direction.clone().negate();

  const ty = FILL * Math.tan((fov * Math.PI) / 360);
  const tx = ty * aspect;
  const solve = (axis: THREE.Vector3, t: number) => {
    let near = Infinity;
    let far = -Infinity;
    for (const p of points) {
      const along = p.dot(axis);
      const depth = p.dot(forward);
      near = Math.min(near, along + t * depth);
      far = Math.max(far, along - t * depth);
    }
    return { offset: (near + far) / 2, depth: (near - far) / (2 * t) };
  };
  const h = solve(right, tx);
  const v = solve(up, ty);

  const position = new THREE.Vector3()
    .addScaledVector(right, h.offset)
    .addScaledVector(up, v.offset)
    .addScaledVector(forward, Math.min(h.depth, v.depth));
  // Where the line of sight meets the ground: the orbit pivot stays on the
  // city instead of hanging in the air.
  const target = position.clone().addScaledVector(forward, -position.y / forward.y);
  return { position, target };
}

export class Cameras {
  readonly camera: THREE.PerspectiveCamera;
  private orbit: OrbitControls;
  private fly: FlyControls;
  private flying = false;
  private readonly points: THREE.Vector3[];
  /** True until the viewer moves the camera: a resize refits the opening
   * view only while nobody has taken the controls. */
  private framed = true;

  constructor(doc: CityDocument, dom: HTMLElement) {
    this.camera = new THREE.PerspectiveCamera(50, 1, 0.1, 6000);
    this.points = cityPoints(doc);

    this.orbit = new OrbitControls(this.camera, dom);
    this.orbit.enableDamping = true;
    this.orbit.maxPolarAngle = Math.PI / 2 - 0.02; // never below the ground
    this.orbit.addEventListener("start", () => {
      this.framed = false;
    });
    const home = this.apply("home");

    this.fly = new FlyControls(this.camera, dom);
    this.fly.movementSpeed = Math.max(10, home.position.distanceTo(home.target) / 3);
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

  private apply(name: PoseName): Pose {
    const pose = fitPose(this.points, DIRECTIONS[name], this.camera.fov, this.camera.aspect);
    this.camera.position.copy(pose.position);
    this.orbit.target.copy(pose.target);
    this.orbit.update();
    return pose;
  }

  get mode(): "orbit" | "fly" {
    return this.flying ? "fly" : "orbit";
  }

  toggleFly(): void {
    this.flying = !this.flying;
    this.orbit.enabled = !this.flying;
    this.fly.enabled = this.flying;
    if (this.flying) this.framed = false;
    document.body.dataset.camera = this.mode;
  }

  reframe(): void {
    if (this.flying) this.toggleFly();
    this.apply("home");
    this.framed = true;
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
    this.framed = false;
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
   * tests can name instead of scripting drags, each fitted to the city the
   * same way the opening view is. */
  setPose(name: PoseName): void {
    if (this.flying) this.toggleFly();
    this.apply(name);
    this.framed = name === "home";
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
    this.framed = false;
  }

  /** The fit depends on the aspect ratio, which is first known here, so the
   * opening view is solved again on every resize until the viewer moves. */
  resize(width: number, height: number): void {
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    if (this.framed) this.apply("home");
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
