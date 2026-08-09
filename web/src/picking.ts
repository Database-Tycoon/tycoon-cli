/**
 * Hover and click resolution. One raycaster over the buildings InstancedMesh
 * (instanceId -> lot) and the plant group (userData.key). Clicking sky clears
 * the selection -- the counterweight the e2e suite will assert.
 */

import * as THREE from "three";
import type { Buildings } from "./scene/buildings";

export type PickHandler = (key: string | null) => void;

export class Picking {
  private raycaster = new THREE.Raycaster();
  private pointer = new THREE.Vector2();
  private targets: THREE.Object3D[];

  setTargets(buildings: Buildings, plant: THREE.Group, extras: THREE.Object3D[] = []): void {
    this.buildings = buildings;
    this.targets = [buildings.mesh, plant, ...extras];
  }

  constructor(
    private buildings: Buildings,
    plant: THREE.Group,
    private camera: THREE.Camera,
    private dom: HTMLElement,
    onHover: PickHandler,
    onClick: PickHandler,
  ) {
    this.targets = [buildings.mesh, plant];

    // Distinguish a click from an orbit drag, or every camera move ends by
    // selecting whatever the pointer happens to be over.
    let downAt: { x: number; y: number } | null = null;
    dom.addEventListener("pointerdown", (e) => (downAt = { x: e.clientX, y: e.clientY }));
    dom.addEventListener("pointerup", (e) => {
      const wasDrag =
        downAt && Math.hypot(e.clientX - downAt.x, e.clientY - downAt.y) > 5;
      downAt = null;
      if (!wasDrag) onClick(this.resolve(e));
    });
    dom.addEventListener("pointermove", (e) => onHover(this.resolve(e)));
  }

  /** The object key under a pointer event, or null over sky/terrain. */
  resolve(event: { clientX: number; clientY: number }): string | null {
    const rect = this.dom.getBoundingClientRect();
    this.pointer.set(
      ((event.clientX - rect.left) / rect.width) * 2 - 1,
      -((event.clientY - rect.top) / rect.height) * 2 + 1,
    );
    this.raycaster.setFromCamera(this.pointer, this.camera as THREE.PerspectiveCamera);
    const hit = this.raycaster.intersectObjects(this.targets, true)[0];
    if (!hit) return null;
    // The plant and the civic buildings all resolve via userData.key.
    if (typeof hit.object.userData.key === "string") return hit.object.userData.key;
    if (hit.instanceId !== undefined && hit.object === this.buildings.mesh) {
      return this.buildings.lots[hit.instanceId]?.object_key ?? null;
    }
    return null;
  }
}
