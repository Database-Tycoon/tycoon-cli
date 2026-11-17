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
    // selecting whatever the pointer happens to be over. A click counts only
    // when both the press and the release land on the scene canvas: the
    // panels inside `dom` (inspector, stats, problems) are not the scene, so
    // clicking or selecting text in one, or dragging from one onto the map,
    // must not select what lies behind it.
    let downAt: { x: number; y: number } | null = null;
    dom.addEventListener("pointerdown", (e) => {
      downAt = this.onScene(e) ? { x: e.clientX, y: e.clientY } : null;
    });
    dom.addEventListener("pointerup", (e) => {
      const start = downAt;
      downAt = null;
      if (!start || !this.onScene(e)) return;
      if (Math.hypot(e.clientX - start.x, e.clientY - start.y) > 5) return;
      onClick(this.resolve(e));
    });
    dom.addEventListener("pointermove", (e) => onHover(this.onScene(e) ? this.resolve(e) : null));
  }

  /** True when the event's target is the WebGL canvas itself, not an overlay. */
  private onScene(e: Event): boolean {
    return e.target instanceof HTMLCanvasElement && e.target.parentElement === this.dom;
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
