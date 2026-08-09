/**
 * Traffic = data movement, and ONLY data movement (Stephen, 2026-08-05: "I
 * don't know why the people are moving between buildings so much").
 *
 * A vehicle on an edge asserts a fact: data arrived at that edge's
 * destination recently. The measured signal is the destination lot's
 * `last_build_age_s` (dbt builds; dlt loads for raw tables) — traffic starts
 * at full flow the moment something is built and fades to nothing over
 * FRESH_WINDOW_S. No run history means NO movement: an idle warehouse is
 * visibly still, exactly like the unknown-never-renders-stale rule.
 *
 * The old always-on ambient flow survives behind `?ambient=1` (demo theater,
 * like `?guests=1`). Decorative by architectural decree either way — this
 * file must never influence any derived state.
 *
 * `setOverride` is the run replay's seam: during a step-through playback the
 * standing flow is suppressed entirely and vehicles run ONLY on the current
 * step's in-edges. That is honest rather than decorative — the build under the
 * cursor really did move data along exactly those streets — and an empty
 * override (the past-the-end cursor, or a step with no upstream on this map)
 * is a still city rather than a fallback to ambience.
 */

import type { CityDocument } from "../contract";
import type { Tile } from "./paths";
import type { Rng } from "./rng";

const SPAWN_SCALE = 0.5; // caps spawn probability at half the edge weight
const FRESH_WINDOW_S = 3600; // movement fades over the hour after a build
export const TICK_SECONDS = 0.1; // 10 presentation ticks/sec, same as the pygame app

export interface Vehicle {
  path: Tile[];
  progress: number;
}

interface Route {
  weight: number;
  path: Tile[];
}

export class Traffic {
  readonly vehicles: Vehicle[] = [];
  private routes: Route[];
  /** Non-null while a run replay drives the streets; `[]` means "no movement",
   * which is a state the standing flow reaches too. */
  private override: Route[] | null = null;

  constructor(
    doc: CityDocument,
    private rng: Rng,
    ambient = false,
  ) {
    const lots = new Map(doc.lots.map((l) => [l.object_key, l]));
    // ALL vehicles travel on roads: only the document's per-edge route (the
    // literal street) may carry traffic. A document without routes gets no
    // vehicles — off-road motion would be theater.
    this.routes = doc.edges
      .filter((e) => lots.has(e.src) && lots.has(e.dst) && e.route.length > 0)
      .map((e) => {
        const dst = lots.get(e.dst)!;
        const age = dst.last_build_age_s;
        // Recency of the destination's last build is what makes the flow a
        // fact; the edge rate only shades relative volume among fresh edges.
        const recency = ambient ? 1 : age === null ? 0 : Math.max(0, 1 - age / FRESH_WINDOW_S);
        const weight = ambient ? e.rate : recency * (0.25 + 0.75 * e.rate);
        return {
          weight,
          path: e.route.map(([x, y]) => [x, y] as Tile),
        };
      })
      .filter((r) => r.weight > 0);
  }

  /**
   * Drive ONLY these tile paths (at full weight) until `setOverride(null)`
   * restores the measured flow. Vehicles in flight are dropped, because a
   * vehicle left on a street the current step does not use would be asserting
   * data movement that is not part of the step being shown.
   */
  setOverride(paths: readonly Tile[][] | null): void {
    this.override = paths === null ? null : paths.map((path) => ({ weight: 1, path: [...path] }));
    this.vehicles.length = 0;
  }

  tick(): void {
    // Advance in place, dropping arrivals — same order as the Python: move
    // first, then spawn, so a new vehicle is visible at its origin for a tick.
    let alive = 0;
    for (const vehicle of this.vehicles) {
      vehicle.progress += 1;
      if (vehicle.progress < vehicle.path.length) this.vehicles[alive++] = vehicle;
    }
    this.vehicles.length = alive;

    for (const route of this.override ?? this.routes) {
      if (this.rng() < route.weight * SPAWN_SCALE) {
        this.vehicles.push({ path: route.path, progress: 0 });
      }
    }
  }
}
