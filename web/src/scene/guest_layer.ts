/**
 * Guests rendered as small spheres riding the roads: white-cyan on the way
 * out, green coming back happy, red coming back from a bad experience — the
 * skyline shows quality problems as a stream of red walking away from the
 * building. Presentation only; reads the mechanics state, owns nothing.
 */

import * as THREE from "three";
import type { Guests } from "../mechanics/guests";

const CAP = 64;
const HEIGHT = 0.22;

const OUTBOUND = new THREE.Color("#cfe8ff");
const HAPPY = new THREE.Color("#5ee07a");
const UNHAPPY = new THREE.Color("#ff5348");

export class GuestLayer {
  readonly mesh: THREE.InstancedMesh;

  constructor() {
    this.mesh = new THREE.InstancedMesh(
      new THREE.SphereGeometry(0.16, 10, 8),
      new THREE.MeshBasicMaterial(),
      CAP,
    );
    this.mesh.count = 0;
    this.mesh.frustumCulled = false;
  }

  update(guests: Guests, fraction: number): void {
    const m = new THREE.Matrix4();
    const count = Math.min(guests.guests.length, CAP);
    for (let i = 0; i < count; i++) {
      const guest = guests.guests[i]!;
      const at = guest.path[guest.progress] ?? guest.path.at(-1)!;
      const next = guest.path[guest.progress + 1] ?? at;
      const x = at[0] + (next[0] - at[0]) * fraction + 0.5;
      const z = at[1] + (next[1] - at[1]) * fraction + 0.5;
      m.setPosition(x, HEIGHT, z);
      this.mesh.setMatrixAt(i, m);
      this.mesh.setColorAt(i, guest.returning ? (guest.happy ? HAPPY : UNHAPPY) : OUTBOUND);
    }
    this.mesh.count = count;
    this.mesh.instanceMatrix.needsUpdate = true;
    if (this.mesh.instanceColor) this.mesh.instanceColor.needsUpdate = true;
  }
}
