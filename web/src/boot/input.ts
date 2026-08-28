/**
 * Input handling: keyboard shortcuts and window resize.
 *
 * Wires up the key events that drive the viewer (R refresh, overlay toggles,
 * etc.) and the resize handler that keeps the renderers sized correctly.
 * Receives callbacks from setup/hud rather than owning state.
 */

import type { OverlayRegistry } from "../ui/overlays";
import type { RequestsPanel } from "../ui/requests";
import type { SetupResult } from "./setup";

export function setupInput(
  setup: SetupResult,
  overlays: OverlayRegistry,
  requests: RequestsPanel | null,
  refresh: () => Promise<void>,
): void {
  const { renderer, labels, camera } = setup;

  window.addEventListener("keydown", (event) => {
    const tag = (event.target as HTMLElement | null)?.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA") return;
    if (event.key === "r" || event.key === "R") void refresh();
    if (event.key === "b" || event.key === "B") requests?.toggle();
    overlays.handleKey(event.key);
  });

  function resize(): void {
    const { clientWidth: w, clientHeight: h } = setup.app;
    renderer.setSize(w, h);
    labels.setSize(w, h);
    camera.resize(w, h);
  }
  window.addEventListener("resize", resize);
  resize();
}
