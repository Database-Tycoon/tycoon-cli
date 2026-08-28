/**
 * Animation loop: the per-frame tick that drives the city's life.
 *
 * This module owns the `setAnimationLoop` call and the per-frame logic:
 * camera ticks, building ticks, fire/truck/van ticks (when not settled),
 * traffic ticks, overlay ticks, and replay progress. Everything it needs
 * is passed in via the `loopDeps` argument.
 */

import * as THREE from "three";
import { TICK_SECONDS } from "../sim/traffic";
import type { SetupResult } from "./setup";
import type { HUDResult } from "./hud";

export function setupLoop(
  setup: SetupResult,
  hud: HUDResult,
  settle: boolean,
  showGuests: boolean,
): void {
  const { renderer, labels, scene, camera, guests } = setup;
  const { city, flow, weather, usage, run, status, statusLine } = hud;

  const clock = new THREE.Clock();
  let accumulator = 0;

  renderer.setAnimationLoop(() => {
    const delta = clock.getDelta();
    camera.tick(delta);
    city().buildings.tick(delta);
    if (!settle) {
      city().fires.tick(delta);
      city().trucks.tick(delta);
      city().vans.tick(delta);
      weather.tick(delta);
      usage.tick(delta);
    }
    if (!settle) {
      accumulator += delta;
      while (accumulator >= TICK_SECONDS) {
        city().traffic.tick();
        if (showGuests) guests.tick();
        if (city().replay.active) {
          const factors = city().replay.tick();
          city().buildings.setReplayProgress(factors);
          if (factors === null) {
            status.textContent = statusLine;
            status.title = statusLine;
          }
        }
        accumulator -= TICK_SECONDS;
      }
    }
    renderer.render(scene, camera.camera);
    // CSS2DRenderer is the ONLY thing that attaches a label's div to the DOM —
    // `new CSS2DObject(el)` leaves `el` detached until a render walks the graph.
    // Skipping this call does not throw and does not warn; the district and
    // civic chips simply never exist, which is how it survived a green suite
    // from 2968461 (the main.ts -> boot/ split) until now. Must run before the
    // ready flag, so the first-frame wait implies the labels are placed.
    labels.render(scene, camera.camera);
    document.body.dataset.ready = "1";
  });
}
