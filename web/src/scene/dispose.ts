/**
 * Freeing a mounted city. `main.ts` replaces everything built FROM a document
 * wholesale on R, so every geometry, material, texture and CSS2D label under
 * the old group has to go — a leak here shows up as a browser tab that grows
 * every refresh on a monitor left open for a day, which is the way this app is
 * meant to be used.
 */

import * as THREE from "three";
import { CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";

/** Free GPU resources and CSS2D label DOM for everything under `root`.
 * CSS2DRenderer leaves label divs in its container after their object leaves
 * the graph, so their elements are removed explicitly. */
export function disposeTree(root: THREE.Object3D): void {
  root.traverse((obj) => {
    if (obj instanceof CSS2DObject) obj.element.remove();
    const mesh = obj as THREE.Mesh;
    if (mesh.geometry) mesh.geometry.dispose();
    const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    for (const material of materials) {
      if (!material) continue;
      const textured = material as THREE.MeshBasicMaterial;
      textured.map?.dispose();
      material.dispose();
    }
  });
}
