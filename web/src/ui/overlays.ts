/**
 * The overlay registry: one place that knows which map overlays exist and
 * which key each one answers to.
 *
 * An overlay is a layer painted ON the city that the viewer switches on and
 * off — the road-load overlay today, weather and usage next. Each one owns its
 * own visibility; the registry owns only the id → overlay map and the key
 * routing, so the keydown handler in `main.ts` does not grow a branch per
 * overlay and the help table has a single list to read from.
 *
 * Deliberately minimal: no rendering, no ordering, no exclusivity rules.
 * Overlays are independent, and nothing here may know what any of them draw.
 */

import type { Lens, OverlayId } from "./lenses";

/** A toggleable layer over the city. `key` is the single character that
 * toggles it (matched case-insensitively, as the keydown handler always has). */
export interface Overlay {
  readonly id: string;
  readonly key: string;
  setVisible(on: boolean): void;
  toggle(): void;
}

export class OverlayRegistry {
  private byId = new Map<string, Overlay>();

  /** Later registrations win a contested key and a repeated id — a collision
   * is a wiring bug, and silently keeping the first one hides it in the half
   * of the app that never fires. */
  register(overlay: Overlay): void {
    this.byId.set(overlay.id, overlay);
  }

  get(id: string): Overlay | undefined {
    return this.byId.get(id);
  }

  /**
   * Apply a role lens's overlay defaults: everything it names goes ON,
   * everything it does not goes OFF. Exclusive on purpose — "the on-call view"
   * means the weather is up and the load map is not, and a lens that could
   * only ever add would drift toward every layer at once.
   *
   * `NO_LENS` is a deliberate no-op: the neutral lens holds no opinion about
   * overlays, so the app's own defaults (both on) survive it, which is what
   * keeps every existing spec and screenshot describing the same city.
   *
   * An id no overlay claims is a silent no-op — a lens may name the overlay it
   * wants before that overlay exists.
   */
  applyLens(lens: Lens): void {
    if (lens.id === "none") return;
    for (const overlay of this.byId.values()) {
      overlay.setVisible(lens.overlays.includes(overlay.id as OverlayId));
    }
  }

  /** Toggle the overlay bound to `key`. Returns whether one was found, so the
   * caller can tell a handled key from a key that means something else. */
  handleKey(key: string): boolean {
    const wanted = key.toLowerCase();
    for (const overlay of this.byId.values()) {
      if (overlay.key.toLowerCase() !== wanted) continue;
      overlay.toggle();
      return true;
    }
    return false;
  }
}
