/**
 * The problems panel: the triage list, Stats reborn as a tool. Toggle with
 * `P`. Every flagged object — failing tests, build errors, late sources,
 * warnings, long-unbuilt — one row each, click → fly-to + inspect. Facts only;
 * the ordering is display order, not a score.
 *
 * ROLE LENSES (2026-08-06) swap the COMPARATOR and choose which coverage
 * gauges lead. Nothing else. `problemsOf()` runs first and lens-blind, so the
 * SET of flagged objects and the VALUE of every gauge are identical under all
 * four lenses — only the order they arrive in changes. A comparator that could
 * drop a row, or a gauge list that could hide a number, would make the lens an
 * editor of facts; `e2e/lens.spec.ts` pins both by comparing the sorted key
 * sets and the gauge texts across lenses.
 */

import type { CityDocument, LotRecord } from "../contract";
import type { GaugeId, Lens } from "./lenses";
import { NO_LENS } from "./lenses";
import { DRIFT_RECENT_S } from "./health";

const STALE_S = 14 * 86400;

interface Problem {
  key: string;
  schema: string;
  severity: number; // ordering only
  badges: string[];
  /** Ordering inputs the comparators read. Null stays null: unknown is not
   * old, and it is not fresh either — every comparator sorts nulls last. */
  buildAge: number | null;
  driftAge: number | null;
  buildError: boolean;
  testFail: boolean;
  testWarn: boolean;
  sourceLate: boolean;
}

function problemsOf(doc: CityDocument): Problem[] {
  const rows: Problem[] = [];
  for (const lot of doc.lots) {
    const badges: string[] = [];
    let severity = 0;
    if (lot.test_status === "fail") {
      badges.push('<span class="tests-fail">● tests fail</span>');
      severity = Math.max(severity, 4);
    }
    if (lot.build_status === "error") {
      badges.push('<span class="tests-fail">✕ build error</span>');
      severity = Math.max(severity, 4);
    }
    if (lot.freshness_status === "error") {
      badges.push('<span class="tests-fail">▲ source late</span>');
      severity = Math.max(severity, 3);
    }
    if (lot.freshness_status === "warn") {
      badges.push('<span class="tests-warn">▲ freshness warn</span>');
      severity = Math.max(severity, 2);
    }
    if (lot.test_status === "warn") {
      badges.push('<span class="tests-warn">● test warning</span>');
      severity = Math.max(severity, 2);
    }
    if (lot.schema_drift_age_s !== null && lot.schema_drift_age_s < DRIFT_RECENT_S) {
      badges.push(
        `<span class="prov">⌂ shape changed ${Math.round(lot.schema_drift_age_s / 86400)}d ago</span>`,
      );
      severity = Math.max(severity, 1);
    }
    if (lot.last_build_age_s !== null && lot.last_build_age_s > STALE_S) {
      badges.push(`<span class="prov">◐ ${Math.round(lot.last_build_age_s / 86400)}d old</span>`);
      severity = Math.max(severity, 1);
    }
    if (badges.length) rows.push(toProblem(lot, severity, badges));
  }
  return rows;
}

function toProblem(lot: LotRecord, severity: number, badges: string[]): Problem {
  return {
    key: lot.object_key,
    schema: lot.object_key.includes(".") ? lot.object_key.split(".")[0]! : "",
    severity,
    badges,
    buildAge: lot.last_build_age_s,
    driftAge: lot.schema_drift_age_s,
    buildError: lot.build_status === "error",
    testFail: lot.test_status === "fail",
    testWarn: lot.test_status === "warn",
    sourceLate: lot.freshness_status === "error" || lot.freshness_status === "warn",
  };
}

type Comparator = (a: Problem, b: Problem) => number;

const flag = (on: boolean): number => (on ? 0 : 1);
/** Nulls last, whichever direction the caller sorts. */
const oldestFirst = (a: number | null, b: number | null): number =>
  a === null ? (b === null ? 0 : 1) : b === null ? -1 : b - a;
const freshestFirst = (a: number | null, b: number | null): number =>
  a === null ? (b === null ? 0 : 1) : b === null ? -1 : a - b;
const worstFirst: Comparator = (a, b) => b.severity - a.severity || a.key.localeCompare(b.key);

/**
 * One comparator per role — the triage order that role would write by hand.
 * Every one of them is a total order over the SAME list; none can shorten it.
 */
const COMPARATORS: Record<string, Comparator> = {
  // Did the pipeline run? Broken builds, then whatever has gone longest
  // without one.
  "data-engineer": (a, b) =>
    flag(a.buildError) - flag(b.buildError) ||
    oldestFirst(a.buildAge, b.buildAge) ||
    worstFirst(a, b),
  // Do the models hold up? Failures, then warnings, then the rest.
  "analytics-engineer": (a, b) =>
    flag(a.testFail) - flag(b.testFail) ||
    flag(a.testWarn) - flag(b.testWarn) ||
    worstFirst(a, b),
  // What is breaking NOW: worst first, and among equals the most RECENT
  // build wins — a page is about what just moved, not what has been sad for
  // a month.
  "on-call": (a, b) =>
    b.severity - a.severity ||
    flag(a.sourceLate) - flag(b.sourceLate) ||
    freshestFirst(a.buildAge, b.buildAge) ||
    a.key.localeCompare(b.key),
  // The portfolio read: grouped by district, worst first inside each.
  "data-lead": (a, b) => a.schema.localeCompare(b.schema) || worstFirst(a, b),
  // The neutral lens keeps the panel's original order exactly.
  none: worstFirst,
};

interface Gauge {
  id: GaugeId;
  text: string;
  /** Provenance / the named absence behind the number, as a tooltip. */
  title: string;
}

export class Problems {
  private root: HTMLElement;
  private doc: CityDocument;
  private lens: Lens = NO_LENS;

  constructor(
    doc: CityDocument,
    private visit: (key: string) => void,
  ) {
    this.doc = doc;
    this.root = document.getElementById("problems")!;
    window.addEventListener("keydown", (event) => {
      const tag = (event.target as HTMLElement | null)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      if (event.key === "p" || event.key === "P") this.toggle();
      if (event.key === "Escape" && !this.root.hidden) this.hide();
    });
  }

  setDoc(doc: CityDocument): void {
    this.doc = doc;
    if (!this.root.hidden) this.show(); // re-render live if open
  }

  /** Re-weight the triage order and the gauge emphasis. Presentation only. */
  setLens(lens: Lens): void {
    this.lens = lens;
    if (!this.root.hidden) this.show();
  }

  toggle(): void {
    if (this.root.hidden) this.show();
    else this.hide();
  }

  hide(): void {
    this.root.hidden = true;
  }

  /** Every gauge, always, in document order. The lens picks which LEAD. */
  private gauges(): Gauge[] {
    const objects = this.doc.objects;
    const cols = objects.flatMap((o) => o.columns);
    const documented = cols.filter((c) => c.description !== null).length;
    const tested = objects.filter((o) => (o.dbt?.tests.length ?? 0) > 0).length;
    const sources = this.doc.lots.filter((l) => l.freshness_status !== null).length;
    const pct = (n: number, d: number) => (d ? `${Math.round((100 * n) / d)}%` : "—");
    // Usage is null for "never measured", which is NOT "nobody uses it": the
    // quiet gauge counts only objects the run history actually spoke about,
    // and names how many it could not.
    const measured = objects.filter((o) => o.usage !== null);
    const quiet = measured.filter((o) => o.usage!.runs_seen === 0).length;
    const budget = this.doc.budget;
    return [
      {
        id: "documented",
        text: `columns documented ${pct(documented, cols.length)}`,
        title: `${documented} of ${cols.length} columns carry a description (dbt manifest)`,
      },
      {
        id: "tested",
        text: `objects tested ${pct(tested, objects.length)}`,
        title: `${tested} of ${objects.length} objects declare at least one dbt test`,
      },
      {
        id: "sla",
        text: `freshness SLAs ${sources}`,
        title: "sources dbt judged against a declared freshness SLA",
      },
      {
        id: "budget",
        text: budget
          ? `compute ${budget.currency} ${budget.daily_cost?.toFixed(2) ?? "—"}/day`
          : "compute cost unpriced",
        title: budget
          ? `${budget.price_source} — ${budget.priced_objects} priced, ${budget.unpriced_objects} unpriced`
          : "no run history to price: unknown, not free",
      },
      {
        id: "quiet",
        text: measured.length
          ? `quiet buildings ${quiet}/${measured.length}`
          : "quiet buildings — (no usage measured)",
        title: measured.length
          ? `${quiet} of ${measured.length} measured objects appeared in zero runs; ` +
            `${objects.length - measured.length} objects have no usage measurement at all`
          : "no object carries a usage measurement — unknown, never unused",
      },
    ];
  }

  private coverageHtml(): string {
    const rank = (id: GaugeId): number => {
      const at = this.lens.gauges.indexOf(id);
      return at === -1 ? Number.MAX_SAFE_INTEGER : at;
    };
    const ordered = this.gauges()
      .map((gauge, i) => ({ gauge, i }))
      .sort((a, b) => rank(a.gauge.id) - rank(b.gauge.id) || a.i - b.i);
    if (!ordered.length) return "";
    return (
      `<p class="coverage">` +
      ordered
        .map(
          ({ gauge }) =>
            `<span data-gauge="${gauge.id}"${this.lens.gauges.includes(gauge.id) ? ' class="lead"' : ""}` +
            ` title="${gauge.title.replace(/"/g, "&quot;")}">${gauge.text}</span>`,
        )
        .join(" · ") +
      `</p>`
    );
  }

  show(): void {
    // The set first, lens-blind; then the lens decides only the order.
    const problems = problemsOf(this.doc).sort(COMPARATORS[this.lens.id] ?? worstFirst);
    const rows = problems.length
      ? problems
          .map(
            (p) =>
              `<li data-key="${p.key.replace(/"/g, "&quot;")}">` +
              `<b>${p.key}</b><span class="badges">${p.badges.join(" ")}</span></li>`,
          )
          .join("")
      : '<li class="none">✓ nothing needs attention</li>';
    this.root.innerHTML =
      `<h3>needs attention (${problems.length})</h3>${this.coverageHtml()}<ul>${rows}</ul>`;
    this.root.hidden = false;
    for (const row of this.root.querySelectorAll<HTMLElement>("li[data-key]")) {
      row.addEventListener("click", () => this.visit(row.dataset.key!));
    }
  }
}
