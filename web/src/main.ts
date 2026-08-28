/**
 * Pipeline City — main entry point.
 *
 * Thin orchestrator that wires together the four boot modules:
 * setup (Three.js infrastructure), hud (UI panels), input (keyboard/resize),
 * and loop (animation). Each module is self-contained; this file just
 * passes state between them.
 */

import type { SetupResult } from "./boot/setup";
import { setupThree } from "./boot/setup";
import { setupHUD, type HUDResult } from "./boot/hud";
import { setupInput } from "./boot/input";
import { setupLoop } from "./boot/loop";
import { installHooks } from "./boot/hooks";
import { mountCity, type MountOptions } from "./boot/mount";

async function start(): Promise<void> {
  const params = new URLSearchParams(window.location.search);
  const settle = params.get("settle") === "1";
  const showGuests = params.get("guests") === "1";

  let setup: SetupResult;
  let hud: HUDResult;
  let mountOptions: MountOptions;

  try {
    setup = await setupThree(params);
    mountOptions = {
      flat: params.get("flat") === "1",
      settle: params.get("settle") === "1",
      ambient: params.get("ambient") === "1",
      seedFor: setup.seedFor,
    };
    hud = setupHUD(setup, setup.scene, params, mountOptions);
  } catch (error) {
    document.getElementById("status")!.textContent = String(error);
    console.error(error);
    return;
  }

  // One `R`, one city. The HUD owns the whole mount/unmount cycle — it is the
  // side that holds the handle it must unmount — so this is a straight
  // delegation, not a two-step. Calling a second module's refresh here once
  // added a city group nobody could ever remove, on top of a second fetch of
  // the same document.
  const refresh = () => hud.refresh();
  setupInput(setup, hud.overlays, hud.requests, refresh);
  setupLoop(setup, hud, settle, showGuests);

  // Install the verification seam that the headless suite drives the city
  // through. Every hook is a question the e2e suite cannot answer from pixels
  // — how many vehicles exist, where a building landed on screen, what the
  // camera pose is — or an action a scripted drag cannot reproduce.
  const run = hud.run;
  const hooks = installHooks({
    // The HUD owns the document currently mounted: `setup.doc` is the one the
    // page booted with and is never replaced, so reading it would answer for a
    // city that an R refresh has already taken off the scene.
    doc: () => hud.doc(),
    city: () => hud.city(),
    cameras: setup.camera,
    renderer: setup.renderer,
    scene: setup.scene,
    skybridges: hud.skybridges,
    flow: hud.flow,
    weather: hud.weather,
    usage: hud.usage,
    guestCount: () => setup.guests.guests.length,
    selectedKey: hud.selected,
    select: (key) => hud.select(key || null),
    visit: hud.visit,
    refresh,
    run,
    lensId: () => hud.lens().id,
    setLens: hud.setLens,
  });

  // Expose for headless verification. `hooks.doc` is a live getter over the
  // HUD's current document, so nothing here patches the object afterwards.
  (window as any).__tycoonCity = hooks;
}

start().catch((error) => {
  document.getElementById("status")!.textContent = String(error);
  console.error(error);
});
