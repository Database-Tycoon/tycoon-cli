/**
 * ROLE LENSES — the same city, re-weighted for the job you actually do.
 *
 * Stephen's framing (2026-08-06): give data teams as many ways as possible to
 * map their real work concerns onto this engine, organised around the ROLES
 * people play. Four lenses; one city.
 *
 * **THE LAW, and it is the whole design: a lens re-weights PRESENTATION ONLY.
 * It never changes arithmetic.** The health-strip counts, the problems list
 * contents and the gauge values are identical under every lens — only ORDER,
 * DEFAULTS and EMPHASIS move. Two lenses shown the same document must display
 * the same numbers, and `e2e/lens.spec.ts` asserts exactly that, byte for
 * byte, because "lens" drifting into "invented score" is the failure mode this
 * repo forbids everywhere else.
 *
 * Which is why every list below is an ORDERING (`chipOrder`, `gauges`) or a
 * DEFAULT (`overlays`, `defaultPanel`), never a filter. A chip a lens does not
 * name still renders — after the ones it does. The moment one of these fields
 * could remove a finding from the strip, the lens would be editing the facts.
 *
 * This module is pure data plus pure functions: no DOM, no Three.js, no
 * `localStorage` (the store is injected), so the e2e suite can unit-test it in
 * the page context.
 */

/** Health-strip chips, by the `data-chip` id the strip renders. */
export type ChipId = "tests-fail" | "build-error" | "source-late" | "tests-warn" | "stale" | "drift";

/**
 * Map overlays, by the id each overlay class declares to `OverlayRegistry`.
 * `flow` IS the road-load overlay (`T`) — the registry's id, not the brief's
 * word for it, because `applyLens` looks these up for real. `usage` (`U`) was
 * named here before it existed, on the rule that an unregistered id is a
 * no-op; it landed 2026-08-06 and the analytics-engineer lens lit up with no
 * change to this file, which is what that rule was for.
 */
export type OverlayId = "flow" | "weather" | "usage";

/** Coverage gauges in the problems-panel header. */
export type GaugeId = "documented" | "tested" | "sla" | "budget" | "quiet";

/** The four roles. `NO_LENS` carries `"none"`, which is not a role. */
export type LensId = "data-engineer" | "analytics-engineer" | "on-call" | "data-lead";

export interface Lens {
  id: LensId | "none";
  label: string;
  /** One line for the picker card. */
  blurb: string;
  /** Leading chips first; chips this lens does not name keep document order
   * after them. Never a filter. */
  chipOrder: readonly ChipId[];
  /** Overlays this lens turns ON by default (others go off). */
  overlays: readonly OverlayId[];
  defaultPanel: "problems" | "library" | "none";
  /** Which coverage gauges lead. Same rule as `chipOrder`: never a filter. */
  gauges: readonly GaugeId[];
  /** Stop ids from `ui/tour.ts`, in the order this role should walk them. */
  tourStops: readonly string[];
}

export const LENSES: Readonly<Record<LensId, Lens>> = {
  "data-engineer": {
    id: "data-engineer",
    label: "data engineer",
    blurb: "Did the pipeline run, and what did it cost? Build errors and the streets they ran on.",
    chipOrder: ["build-error", "stale", "drift"],
    overlays: ["flow"],
    defaultPanel: "problems",
    gauges: ["sla", "budget"],
    tourStops: ["view", "lenses", "districts", "streets", "plant", "orphans", "load", "replay", "drift", "controls"],
  },
  "analytics-engineer": {
    id: "analytics-engineer",
    label: "analytics engineer",
    blurb: "Do the models hold up? Failing tests, warnings, and how much of this is documented.",
    chipOrder: ["tests-fail", "tests-warn", "drift"],
    // Which models are actually exercised — and, louder, which measured ones
    // are not. `usage` never speaks for an unmeasured object.
    overlays: ["usage"],
    defaultPanel: "problems",
    gauges: ["documented", "tested"],
    tourStops: ["view", "lenses", "districts", "library", "fire", "quiet-city", "streets", "orphans", "controls"],
  },
  "on-call": {
    id: "on-call",
    label: "on-call responder",
    blurb: "What is broken right now? Fires, late sources, and the weather they cause downstream.",
    chipOrder: ["tests-fail", "source-late", "build-error"],
    overlays: ["weather"],
    defaultPanel: "problems",
    gauges: ["sla", "tested"],
    tourStops: ["view", "lenses", "fire", "quiet-city", "firehouse", "weather", "wear", "replay", "orphans", "controls"],
  },
  "data-lead": {
    id: "data-lead",
    label: "data lead",
    blurb: "Is my city healthy? Standing neglect, what it costs, and how much context we have.",
    chipOrder: ["stale", "drift", "source-late"],
    // Two overlays, and `applyLens` is exclusive but not single-valued. `flow`
    // is the lead's cost picture; `usage` is here because this lens's gauges
    // lead with `budget, quiet, documented`, and `quiet` alone would be a
    // number in a panel with no map treatment behind it — the quiet marker IS
    // that number made spatial. (Recommended by the usage overlay's author on
    // 2026-08-06 and deliberately left for a separate change.)
    overlays: ["flow", "usage"],
    defaultPanel: "library",
    gauges: ["budget", "quiet", "documented"],
    tourStops: ["view", "lenses", "districts", "library", "plant", "orphans", "load", "quiet-city", "controls"],
  },
};

/**
 * The neutral lens: document order, nothing emphasised, no overlay opinion.
 * This is what `?lens=none` selects and what every existing e2e spec runs
 * under — a suite that met the first-run picker would be testing the picker.
 */
export const NO_LENS: Lens = {
  id: "none",
  label: "no lens",
  blurb: "The city as the document orders it — every finding, nothing emphasised.",
  chipOrder: [],
  overlays: [],
  defaultPanel: "none",
  gauges: [],
  tourStops: ["view", "lenses", "districts", "streets", "no-lineage", "plant", "orphans", "fire", "quiet-city", "firehouse", "library", "weather", "weather-unknown", "load", "wear", "drift", "replay", "controls"],
};

/** Every lens a picker or switcher offers, in role order. */
export const LENS_LIST: readonly Lens[] = [
  LENSES["data-engineer"],
  LENSES["analytics-engineer"],
  LENSES["on-call"],
  LENSES["data-lead"],
];

/**
 * Resolve a `?lens=` parameter to a lens, or null to keep looking.
 *
 * `null` in (no parameter at all) is `null` out — the caller falls through to
 * storage. An UNKNOWN id is also `null` out: a typo'd or future lens id must
 * not blank the viewer's own preference, and it must not silently mean "none"
 * either. `""` and `"none"` are explicit requests for the neutral lens.
 */
export function lensFromParam(raw: string | null): Lens | null {
  if (raw === null) return null;
  const id = raw.trim().toLowerCase();
  if (id === "" || id === "none") return NO_LENS;
  return (LENSES as Record<string, Lens | undefined>)[id] ?? null;
}

/** The persistence seam, injected so this module stays DOM-free. */
export interface LensStore {
  read(): string | null;
  write(id: string): void;
  clear(): void;
}

export interface LensResolution {
  lens: Lens;
  /** Where the lens came from. `url` NEVER persists: a shared link must not
   * rewrite the recipient's preference. */
  source: "url" | "stored" | "none";
  /** Show the first-run picker: nobody has ever chosen on this browser. */
  firstRun: boolean;
}

/**
 * The resolution order, and it matters:
 *
 *   `?lens=<id>` wins and does not persist  →  `?lens=none` / `?lens=` is the
 *   neutral lens with no picker  →  `localStorage["tycoon-city.lens"]`  →  nothing,
 *   which is the first run and shows the picker.
 *
 * An unknown STORED value is garbage: it falls back to `NO_LENS`, clears the
 * key, and asks again — quietly keeping a preference nobody can name would
 * leave a viewer stuck with a lens that no longer exists.
 */
export function resolveLens(raw: string | null, store: LensStore): LensResolution {
  const fromUrl = lensFromParam(raw);
  if (fromUrl) return { lens: fromUrl, source: "url", firstRun: false };

  const stored = store.read();
  if (stored === null) return { lens: NO_LENS, source: "none", firstRun: true };
  const fromStore = lensFromParam(stored);
  if (fromStore) return { lens: fromStore, source: "stored", firstRun: false };
  store.clear();
  return { lens: NO_LENS, source: "none", firstRun: true };
}
