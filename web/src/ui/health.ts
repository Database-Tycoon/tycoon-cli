/**
 * The health strip: zero-click health, always visible under the header.
 *
 * Pure aggregation over the document's facts — failing tests, warnings, late
 * sources, build errors, schema drift, the oldest build. Every chip is a door:
 * clicking it cycles through its offenders (fly-to + select), because a count
 * you cannot visit is trivia. Chips render only when nonzero; an all-clear
 * strip shows one quiet check so "healthy" and "not rendered" can never be
 * confused.
 *
 * ROLE LENSES (2026-08-06) reorder this strip and mark the first two chips as
 * LEADING. They do nothing else. `findings()` — the aggregation — is not
 * reachable from the lens at all: the ordering happens after every count is
 * computed, on a list the lens cannot shorten. That separation is what
 * `e2e/lens.spec.ts` pins by comparing the chip TEXTS across two lenses byte
 * for byte.
 */

import type { CityDocument, LotRecord } from "../contract";
import type { ChipId, Lens } from "./lenses";
import { NO_LENS } from "./lenses";

export interface Finding {
  key: string;
  lot: LotRecord;
}

interface Chip {
  id: ChipId;
  label: (n: number) => string;
  tone: "fail" | "warn" | "info";
  matches: (lot: LotRecord) => boolean;
}

const STALE_S = 14 * 86400; // informational chip: builds older than two weeks

/**
 * "Recently changed shape" — the CRANE rule. Exported because
 * `scene/silhouettes.ts` raises its cranes off this same constant: the chip
 * that counts drift and the cranes that show it must never be able to
 * disagree about what recent means.
 */
export const DRIFT_RECENT_S = 7 * 86400;

/**
 * Document order. A lens reorders this list; it can never edit it, and a chip
 * absent from every lens still renders after the ones a lens names.
 */
const CHIPS: Chip[] = [
  {
    id: "tests-fail",
    label: (n) => `● ${n} test${n === 1 ? "" : "s"} failing`,
    tone: "fail",
    matches: (l) => l.test_status === "fail",
  },
  {
    id: "build-error",
    label: (n) => `✕ ${n} build error${n === 1 ? "" : "s"}`,
    tone: "fail",
    matches: (l) => l.build_status === "error",
  },
  {
    id: "source-late",
    label: (n) => `▲ ${n} source${n === 1 ? "" : "s"} late`,
    tone: "warn",
    matches: (l) => l.freshness_status === "error" || l.freshness_status === "warn",
  },
  {
    id: "tests-warn",
    label: (n) => `● ${n} test warning${n === 1 ? "" : "s"}`,
    tone: "warn",
    matches: (l) => l.test_status === "warn",
  },
  {
    id: "stale",
    label: (n) => `◐ ${n} not built in 14d+`,
    tone: "info",
    matches: (l) => l.last_build_age_s !== null && l.last_build_age_s > STALE_S,
  },
  {
    id: "drift",
    label: (n) => `⌂ ${n} changed shape in 7d`,
    tone: "info",
    matches: (l) => l.schema_drift_age_s !== null && l.schema_drift_age_s < DRIFT_RECENT_S,
  },
];

export class HealthStrip {
  private root: HTMLElement;
  private cursors = new Map<string, number>();
  private doc: CityDocument;
  private lens: Lens = NO_LENS;

  constructor(
    doc: CityDocument,
    private visit: (key: string) => void,
  ) {
    this.root = document.getElementById("health")!;
    this.doc = doc;
    this.render();
  }

  setDoc(doc: CityDocument): void {
    this.doc = doc;
    this.cursors.clear();
    this.render();
  }

  /** Re-weight the strip. Presentation only — see this file's header. */
  setLens(lens: Lens): void {
    this.lens = lens;
    this.render();
  }

  private findings(chip: Chip): Finding[] {
    return this.doc.lots
      .filter(chip.matches)
      .map((lot) => ({ key: lot.object_key, lot }))
      .sort((a, b) => a.key.localeCompare(b.key));
  }

  private render(): void {
    // Step 1: the aggregation, in document order, lens-blind.
    const found = CHIPS.map((chip) => ({ chip, n: this.findings(chip).length })).filter(
      (entry) => entry.n > 0,
    );

    // Step 2: the lens. A stable sort on "how early does this lens name the
    // chip", so unnamed chips keep document order behind the named ones.
    const rank = (id: ChipId): number => {
      const at = this.lens.chipOrder.indexOf(id);
      return at === -1 ? Number.MAX_SAFE_INTEGER : at;
    };
    const ordered = found
      .map((entry, i) => ({ ...entry, i }))
      .sort((a, b) => rank(a.chip.id) - rank(b.chip.id) || a.i - b.i);

    // Step 3: emphasis. The first two chips this lens actually named lead;
    // under NO_LENS nothing leads, because emphasising document order would
    // be an opinion the neutral lens does not hold.
    const leading = new Set(
      ordered
        .filter((entry) => this.lens.chipOrder.includes(entry.chip.id))
        .slice(0, 2)
        .map((entry) => entry.chip.id),
    );

    const parts = ordered.map(
      (entry) =>
        `<button class="chip-h ${entry.chip.tone}${leading.has(entry.chip.id) ? " lead" : ""}" ` +
        `data-chip="${entry.chip.id}" title="click to visit each">` +
        `${entry.chip.label(entry.n)}</button>`,
    );
    this.root.innerHTML = parts.length
      ? parts.join("")
      : `<span class="chip-h ok">✓ no findings</span>`;

    for (const button of this.root.querySelectorAll<HTMLElement>("[data-chip]")) {
      button.addEventListener("click", () => this.cycle(button.dataset.chip!));
    }
  }

  /** Visit the chip's offenders one by one, wrapping around. */
  private cycle(chipId: string): void {
    const chip = CHIPS.find((c) => c.id === chipId);
    if (!chip) return;
    const found = this.findings(chip);
    if (!found.length) return;
    const at = this.cursors.get(chipId) ?? 0;
    this.cursors.set(chipId, (at + 1) % found.length);
    this.visit(found[at % found.length]!.key);
  }
}
