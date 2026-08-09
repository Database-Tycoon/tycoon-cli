/**
 * How hard each building is actually worked — the PURE half of the usage
 * overlay: the classification, the scale and the counts, with no Three.js and
 * no DOM, so the scene layer and the legend share one implementation instead
 * of agreeing by coincidence.
 *
 * What the document carries (`docs/city-json-v1.md`, `objects[].usage`) is
 * MEASURED BUILD/RUN APPEARANCES, not query traffic: vanilla DuckDB has no
 * query log, so there is no query history to read. The `source` discriminator
 * is what holds that seam open — a MotherDuck or Snowflake document says
 * `"queries"` there — and it is shown wherever these numbers are shown, so a
 * viewer never has to guess which fact they are looking at.
 *
 * **THE RULE THIS MODULE EXISTS TO HOLD: `usage: null` is UNKNOWN, and
 * unknown must never render as unused.** They are different facts and they
 * are not close: "measured, and nobody ran it" is a deprecation signal a
 * consultant would act on, while "never measured" is a gap in the run history
 * and says nothing at all about the table. `classifyUsage` therefore keeps
 * four states, not three, and `unknown` is the one state with NO map
 * treatment — the same shape weather uses, where the absence is named in the
 * legend rather than painted as fair weather.
 *
 * The fourth state is the one the guards Python-side already force on us:
 * `rate_per_day` is null with fewer than two appearances or a zero span, so an
 * object can be *seen* with no knowable cadence. That is `unrated`, and it is
 * neither busy nor quiet — placing it on the busy ramp would be inventing a
 * cadence, and calling it quiet would be the null-as-unused lie one level in.
 */

import type { CityDocument, UsageRecord } from "./contract";

/**
 * - `busy`    — measured, with a known cadence at or above `QUIET_PER_DAY`
 * - `quiet`   — measured, and genuinely little-used: zero appearances, or a
 *               known cadence below `QUIET_PER_DAY`
 * - `unrated` — appeared in runs, but the cadence is unknowable (< 2
 *               appearances, or a zero span)
 * - `unknown` — no measurement at all. NOT unused. Draws nothing.
 */
export type UsageState = "busy" | "quiet" | "unrated" | "unknown";

/**
 * The busy/quiet line: less than once a week. Chosen because it is a sentence
 * a data team says out loud ("this hasn't run in a week"), not a percentile of
 * this city — a threshold relative to the busiest object would move under a
 * catalog's feet and re-label a table nobody touched.
 */
export const QUIET_PER_DAY = 1 / 7;

/** The overlay's palette, here rather than in the scene so the legend cannot
 * drift from what is painted. Deliberately a hue family nothing else in the
 * city uses: green is passing tests, amber is warnings, red is fire, the
 * cool→hot ramp is road load, grey-white is fog. */
export const USAGE_COLOR = {
  /** Bottom of the busy ramp (just above the quiet line). */
  busyLow: "#7b4fd6",
  /** Top of the busy ramp (this city's most-run object). */
  busyHigh: "#ff5edb",
  /** Seen, cadence unknowable. */
  unrated: "#9fe8ff",
  /** Measured and little-used — the deprecation candidate. */
  quiet: "#79838f",
} as const;

/** The state one object's `usage` block puts it in. The whole honesty rule is
 * these four lines; every other module reads this answer. */
export function classifyUsage(usage: UsageRecord | null | undefined): UsageState {
  if (usage === null || usage === undefined) return "unknown";
  if (usage.runs_seen === 0) return "quiet";
  if (usage.rate_per_day === null) return "unrated";
  return usage.rate_per_day < QUIET_PER_DAY ? "quiet" : "busy";
}

export interface UsageSummary {
  busy: number;
  quiet: number;
  unrated: number;
  /** Objects the run history says nothing about. Unknown, never unused. */
  unknown: number;
  /** Objects carrying a usage block at all (busy + quiet + unrated). */
  measured: number;
  /** The `source` discriminator, or null when nothing is measured. Mixed
   * sources report the first one seen in document order — a document with two
   * would be a producer bug, and guessing a winner here would hide it. */
  source: string | null;
  /** The busiest known cadence in this city, or 0 when none is known. The
   * ramp is normalised to it, exactly as the road-load overlay normalises to
   * its busiest tile: heights are comparable WITHIN a city, never across. */
  peakRate: number;
}

export function usageSummary(doc: CityDocument): UsageSummary {
  const out: UsageSummary = {
    busy: 0,
    quiet: 0,
    unrated: 0,
    unknown: 0,
    measured: 0,
    source: null,
    peakRate: 0,
  };
  for (const object of doc.objects) {
    const usage = object.usage;
    out[classifyUsage(usage)] += 1;
    if (!usage) continue;
    out.measured += 1;
    out.source ??= usage.source;
    if (usage.rate_per_day !== null) out.peakRate = Math.max(out.peakRate, usage.rate_per_day);
  }
  return out;
}

/**
 * Where a rate sits on the busy ramp, 0..1.
 *
 * Logarithmic, because run cadence is heavily skewed — one hourly model beside
 * a dozen dailies would flatten every other beacon to nothing on a linear
 * scale, and a reader would come away thinking the dailies were never run. A
 * peak at or below the quiet line (possible only if `peak` is stale) yields 0
 * rather than dividing by zero.
 */
export function busyFraction(rate: number, peak: number): number {
  const span = Math.log1p(peak) - Math.log1p(QUIET_PER_DAY);
  if (span <= 0) return 0;
  const at = (Math.log1p(rate) - Math.log1p(QUIET_PER_DAY)) / span;
  return Math.min(1, Math.max(0, at));
}
