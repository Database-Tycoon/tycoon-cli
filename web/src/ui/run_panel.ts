/**
 * The run picker and the current-step inspector — the HUD half of the
 * step-through replay (`sim/run_replay.ts` is the state machine, and this file
 * knows nothing about the scene).
 *
 * It REPLACES the single "replay last run" button. That button played the
 * aggregate schedule in `city.json` and could name no run; this panel lists
 * the actual invocations from `/runs.json`, worst first, and plays the one you
 * pick step by step.
 *
 * ABSENCE STAYS NAMED. When there is no run metadata — none written, or the
 * database locked by a running tycoon command — the panel opens and SAYS SO,
 * with the loader's own sentences underneath. It does not hide. A control that
 * quietly disappears is indistinguishable from a broken build, and
 * `/runs.json` is answered 200 with the reason in `notes` precisely so a
 * client has something to show.
 *
 * Every object name in here is a door (the HUD's "every number is a door"):
 * clicking the current step, an upstream dependency or a cascaded model flies
 * the camera to it.
 */

import type { RunsIndex } from "../contract_runs";
import { foldStatus, pickerOrder } from "../contract_runs";
import type { RunReplay } from "../sim/run_replay";

export interface RunPanelDeps {
  replay: RunReplay;
  /** Fetch `/runs.json`. Injected so the panel does no I/O policy of its own. */
  loadIndex: () => Promise<RunsIndex>;
  /** Load and begin the named run. */
  onPick: (id: string) => Promise<void>;
  /** Leave replay; the scene drops its overrides. */
  onExit: () => void;
  /** Re-apply the machine's state to the scene after a cursor move. */
  onChange: () => void;
  /** Fly to and select an object. */
  onVisit: (key: string) => void;
  /** The `city.json` aggregate schedule, kept as a labelled second-best: it is
   * a different, weaker fact (newest status per node, naming no run) and the
   * picker says so rather than mixing it in with the real invocations. */
  aggregate: () => { available: boolean; note: string; start: () => void };
}

export class RunPanel {
  private root: HTMLElement;
  private index: RunsIndex | null = null;
  private error: string | null = null;

  constructor(private deps: RunPanelDeps) {
    this.root = document.getElementById("run-panel")!;
    window.addEventListener("keydown", (event) => this.handleKey(event));
  }

  get visible(): boolean {
    return !this.root.hidden;
  }

  /** Show the panel, fetching the index on first open. */
  async open(): Promise<void> {
    this.root.hidden = false;
    if (this.index === null && this.error === null) {
      this.render(); // "reading…" — the fetch is not always instant
      try {
        this.index = await this.deps.loadIndex();
      } catch (error) {
        this.error = String(error);
      }
    }
    this.render();
  }

  close(): void {
    this.root.hidden = true;
  }

  /** The run the picker puts first — worst, then newest. Null when the index
   * is missing or empty. */
  firstRunId(): string | null {
    if (!this.index?.runs.length) return null;
    return pickerOrder(this.index.runs)[0]!.id;
  }

  /** Name a failure the panel could not otherwise show (a run document that
   * would not load). Rendered where the picker would be, never swallowed. */
  noteError(message: string): void {
    this.error = message;
    this.root.hidden = false;
    this.render();
  }

  /**
   * The controls. Space and ArrowRight advance, ArrowLeft steps back, 0
   * restarts, Esc exits — and NOTHING advances on a timer, in any mode. The
   * machine moves only from here and from `window.__tycoonCity.runStep()`, which is
   * what makes every spec's cursor assertion deterministic under `?settle=1`.
   */
  private handleKey(event: KeyboardEvent): void {
    const tag = (event.target as HTMLElement | null)?.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA") return;
    const replay = this.deps.replay;
    if (replay.phase === "off") return;
    if (event.key === " " || event.key === "ArrowRight") {
      event.preventDefault(); // Space scrolls the document otherwise
      replay.stepForward();
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      replay.stepBack();
    } else if (event.key === "0") {
      replay.reset();
    } else if (event.key === "Escape") {
      this.deps.onExit();
      return;
    } else {
      return;
    }
    this.deps.onChange();
  }

  /** Re-render for whatever the machine currently says. Called after every
   * cursor move and every state change; the panel holds no state of its own
   * beyond the fetched index. */
  render(): void {
    this.root.innerHTML =
      this.deps.replay.phase === "off" ? this.pickerHtml() : this.stepHtml();
    this.root.querySelector(".close")?.addEventListener("click", () => {
      if (this.deps.replay.phase === "off") this.close();
      else this.deps.onExit();
    });
    for (const row of this.root.querySelectorAll<HTMLElement>("[data-run]")) {
      row.addEventListener("click", () => void this.deps.onPick(row.dataset.run!));
    }
    for (const row of this.root.querySelectorAll<HTMLElement>("[data-aggregate]")) {
      row.addEventListener("click", () => this.deps.aggregate().start());
    }
    for (const link of this.root.querySelectorAll<HTMLElement>("[data-key]")) {
      link.addEventListener("click", () => this.deps.onVisit(link.dataset.key!));
    }
  }

  // --- the picker ----------------------------------------------------------

  private pickerHtml(): string {
    const head = '<button class="close" title="close">×</button><h3>run replay</h3>';
    if (this.error !== null) {
      return `${head}<p class="none">run replay unavailable — ${escapeHtml(this.error)}</p>`;
    }
    if (this.index === null) return `${head}<p class="none">reading runs.json…</p>`;

    const notes = this.index.notes.length
      ? `<ul class="run-notes">${this.index.notes
          .map((n) => `<li>${escapeHtml(n)}</li>`)
          .join("")}</ul>`
      : "";
    if (!this.index.runs.length) {
      // The whole point of the 200-with-notes contract: say which absence this
      // is, in the loader's own words, instead of hiding the control.
      return `${head}<p class="none">run replay unavailable — ${escapeHtml(
        unavailableReason(this.index.notes),
      )}</p>${notes}${this.aggregateHtml()}`;
    }
    const rows = pickerOrder(this.index.runs)
      .map((run) => {
        const verdict = run.ok
          ? '<span class="tests-pass">● ok</span>'
          : `<span class="tests-fail">● ${run.failed_count} failed here</span>`;
        return (
          `<li data-run="${escapeHtml(run.id)}">` +
          `<b>${escapeHtml(run.command)} · ${escapeHtml(stamp(run.started_at))}</b>` +
          `<span class="badges">${verdict}` +
          `<span class="prov">${run.step_count} steps · ${run.elapsed_s.toFixed(1)}s · ` +
          `${escapeHtml(run.target)}</span></span></li>`
        );
      })
      .join("");
    return (
      `${head}<ul class="runs">${rows}</ul>${notes}` +
      `<p class="note">Pick a run to walk it step by step. ` +
      `"failed here" counts failing steps with a building on this map — dbt's ` +
      `own totals sit beside it in the step header.</p>${this.aggregateHtml()}`
    );
  }

  /** The aggregate schedule, offered as what it is and never as a run. */
  private aggregateHtml(): string {
    const aggregate = this.deps.aggregate();
    if (!aggregate.available) return "";
    return (
      `<h3>no run named</h3><ul class="runs"><li data-aggregate="1">` +
      `<b>aggregate schedule</b><span class="badges"><span class="prov">` +
      `newest status per node · ${escapeHtml(aggregate.note)}</span></span></li></ul>`
    );
  }

  // --- the current step ----------------------------------------------------

  private stepHtml(): string {
    const replay = this.deps.replay;
    const doc = replay.document!;
    const run = doc.run;
    const header =
      `<button class="close" title="exit replay">×</button>` +
      `<h3>run replay · ${replay.phase === "done" ? "finished" : `step ${replay.at + 1} / ${replay.total}`}</h3>` +
      `<p class="run-head"><b>${escapeHtml(run.command)} · ${escapeHtml(stamp(run.started_at))}</b>` +
      `<span class="prov">${escapeHtml(run.target)} · ${run.models_error} model errors, ` +
      `${run.tests_failed} tests failed · ${run.unmapped_count} nodes off this map</span></p>`;
    const keys =
      `<p class="keys">space / → next · ← back · 0 restart · esc exit</p>` +
      `<p class="note">${escapeHtml(doc.note)} (order ${escapeHtml(doc.order_source)}).</p>`;

    const step = replay.current();
    if (step === null) {
      const burning = [...replay.failedKeys()];
      const dimmed = [...replay.skippedKeys()];
      return (
        `${header}<p class="none">the run is over.</p>` +
        `<dl><dt>burning</dt><dd>${doors(burning)}</dd>` +
        `<dt>skipped</dt><dd>${doors(dimmed)}</dd></dl>${keys}`
      );
    }

    const folded = foldStatus(step.status);
    const cls = folded === "failed" ? "tests-fail" : folded === "skipped" ? "prov" : "tests-pass";
    // The machine's guarded cascade, not the document's raw list — so the
    // count in the words can never disagree with the buildings that dimmed.
    const cascade = replay.cascadeOf(step.object_key);
    const cascadeHtml =
      folded === "failed"
        ? `<p class="cascade"><b>${escapeHtml(step.object_key)} errored here.</b> ` +
          (cascade.length
            ? `dbt reported ${cascade.length} downstream model${
                cascade.length === 1 ? "" : "s"
              } skipped: ${doors(cascade)}`
            : "nothing measurable cascaded from it.") +
          `</p>`
        : "";
    const blame = replay.blamedFor(step.object_key);
    const blameHtml = blame
      ? `<p class="cascade">skipped — dbt did not run it after ${doors([blame])} errored.</p>`
      : "";

    return (
      `${header}<dl>` +
      `<dt>step</dt><dd>${doors([step.object_key])}</dd>` +
      `<dt>status</dt><dd class="${cls}">${escapeHtml(step.status)}</dd>` +
      `<dt>kind</dt><dd>${escapeHtml(step.node_kind || "—")}</dd>` +
      `<dt>took</dt><dd>${step.execution_time_s.toFixed(2)} s <span class="prov">measured</span></dd>` +
      `<dt>upstream</dt><dd>${step.depends_on.length ? doors(step.depends_on) : "<span class='prov'>none on this map</span>"}</dd>` +
      `</dl>${cascadeHtml}${blameHtml}${keys}`
    );
  }
}

/** Object keys as clickable doors. */
function doors(keys: readonly string[]): string {
  if (!keys.length) return "<span class='prov'>none</span>";
  return keys
    .map((k) => `<span class="door" data-key="${escapeHtml(k)}">${escapeHtml(k)}</span>`)
    .join(" ");
}

/**
 * Which absence this is, in the loader's own words where it has them. The
 * sentences come from `/runs.json`'s `notes`; this only picks the headline.
 */
function unavailableReason(notes: readonly string[]): string {
  if (notes.some((n) => /locked/i.test(n))) return "run metadata locked";
  if (notes.some((n) => /no run metadata/i.test(n))) return "no run metadata";
  if (notes.some((n) => /no dbt run history/i.test(n))) return "no dbt run history for this catalog";
  if (notes.some((n) => /no run history/i.test(n))) return "no run history yet";
  return "no runs to replay";
}

/** "2026-08-05T09:15:00" -> "2026-08-05 09:15". Naive UTC, as emitted. */
function stamp(isoish: string): string {
  return isoish.replace("T", " ").slice(0, 16);
}

function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}
