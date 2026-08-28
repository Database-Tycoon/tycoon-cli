/**
 * Vehicles as one InstancedMesh of small bright boxes riding the roads.
 *
 * The tick moves a vehicle a whole tile at 10 Hz; drawing that directly gives
 * the 2D renderer's stutter-step. Here the draw position interpolates between
 * the current and next path tile by the accumulator fraction — presentation
 * smoothing over the same discrete sim, changing nothing about the tick.
 */

import * as THREE from "three";
import type { Traffic } from "../sim/traffic";

const CAP = 1024; // instances; spawn rates cap at 0.5/edge/tick, so 1024 is
// unreachable at <= 500 objects — count is clamped anyway.
const SIZE = 0.34;
const HEIGHT = 0.17;

export class VehicleLayer {
  readonly mesh: THREE.InstancedMesh;

  constructor() {
    this.mesh = new THREE.InstancedMesh(
      new THREE.BoxGeometry(SIZE, SIZE, SIZE),
      new THREE.MeshBasicMaterial({ color: "#ffe066" }), // emissive-bright: readable on road grey
      CAP,
    );
    this.mesh.count = 0;
    this.mesh.frustumCulled = false; // count changes per frame; a stale bound would cull live vehicles
  }

  /** `fraction` is the tick accumulator's 0..1 progress toward the next tick. */
  update(traffic: Traffic, fraction: number): void {
    const m = new THREE.Matrix4();
    const count = Math.min(traffic.vehicles.length, CAP);
    for (let i = 0; i < count; i++) {
      const vehicle = traffic.vehicles[i]!;
      const at = vehicle.path[vehicle.progress]!;
      const next = vehicle.path[vehicle.progress + 1] ?? at;
      const x = at[0] + (next[0] - at[0]) * fraction + 0.5;
      const z = at[1] + (next[1] - at[1]) * fraction + 0.5;
      m.setPosition(x, HEIGHT, z);
      this.mesh.setMatrixAt(i, m);
    }
    this.mesh.count = count;
    this.mesh.instanceMatrix.needsUpdate = true;
  }
}
