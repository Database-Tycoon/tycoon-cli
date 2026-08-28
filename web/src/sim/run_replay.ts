/**
 * Step-through replay of ONE named dbt invocation: the failure cascade as a
 * state machine (Stephen, 2026-08-06 — replay a specific run, step by step,
 * "the building ignites at the moment its step errors, and downstream models
 * dbt reported as skipped dim as the cascade spreads").
 *
 * NO Three.js in this file, and no accumulated animation state. The design
 * property everything else here rests on:
 *
 *   **`stateOf(key)` is a PURE TOTAL FUNCTION OF THE CURSOR.**
 *
 * Not a tally that steps mutate. Stepping backward is therefore free and
 * exact rather than an undo log, `jumpTo` needs no replay of the steps it
 * skipped, and — the reason that matters most in this repo — every claim the
 * dramatization makes is assertable in the e2e page context without a
 * screenshot. A cascade rendered from accumulated state can only be checked
 * by looking at it, and "some building is on fire" is exactly the assertion
 * this codebase has been burned by.
 *
 * There is NO timer anywhere in this module, in any mode. The machine advances
 * only when something calls `stepForward` / `stepBack` / `jumpTo` / `reset`.
 * `?settle=1` therefore needs no special case to be deterministic; the whole
 * machine is.
 *
 * THE CURSOR. `at` is the index of the step CURRENTLY EXECUTING, in
 * `[0, total]`. `at === total` means the run is over. So step `i`:
 *
 *   i <  at   already resolved -> built / failed / skipped
 *   i === at  the current step -> failed or skipped if that is dbt's word for
 *             it (the fire lights the moment its step errors, not a step
 *             later), otherwise "building"
 *   i >  at   pending, unless a failure the cursor has already reached took it
 *             down — see `dimsAt`
 *
 * An object that is not a step in this run is NOT pending: it is unknown, and
 * an unknown building sinking into the ground during playback would read as a
 * build failure. It keeps standing, exactly as `sim/replay.ts` treats a lot
 * the aggregate schedule does not cover.
 */

import type { RunDocument, RunStep } from "../contract_runs";
import { isFailure, isSkip } from "../contract_runs";

export type RunState = "pending" | "building" | "built" | "failed" | "skipped";

/** `off` = not replaying; `playing` = a step is current; `done` = past the end. */
export type RunPhase = "off" | "playing" | "done";

/** Height factor per state for `Buildings.setReplayProgress`. A skipped model
 * was never built in this run, so it stands stunted rather than absent — and a
 * failed one keeps its full height, because it is the fire that says it failed
 * and a building that shrinks says something different. */
const HEIGHT: Record<RunState, number> = {
  pending: 0,
  building: 0.55,
  built: 1,
  failed: 1,
  skipped: 0.28,
};

export class RunReplay {
  private doc: RunDocument | null = null;
  /** object_key -> step index. */
  private index = new Map<string, number>();
  /** object_key -> the cursor at which a failure's cascade dims it, and which
   * failure that was. */
  private dimsAt = new Map<string, Blame>();
  private cursor = 0;

  /** Adopt a run document and go to its first step. */
  load(doc: RunDocument): void {
    this.doc = doc;
    this.index = new Map(doc.steps.map((step, i) => [step.object_key, i]));
    this.dimsAt = cascadeSchedule(doc, this.index);
    this.cursor = 0;
  }

  /** Leave replay entirely. The document is dropped, so `stateOf` goes back to
   * answering "built" for everything and the scene's overrides can be lifted. */
  exit(): void {
    this.doc = null;
    this.index = new Map();
    this.dimsAt = new Map();
    this.cursor = 0;
  }

  /** Back to the first step, keeping the run loaded. */
  reset(): void {
    this.cursor = 0;
  }

  get phase(): RunPhase {
    if (!this.doc) return "off";
    return this.cursor >= this.doc.steps.length ? "done" : "playing";
  }

  get at(): number {
    return this.cursor;
  }

  get total(): number {
    return this.doc?.steps.length ?? 0;
  }

  get document(): RunDocument | null {
    return this.doc;
  }

  /** The step under the cursor, or null past the end (and when off). */
  current(): RunStep | null {
    return this.doc?.steps[this.cursor] ?? null;
  }

  stepForward(): void {
    this.jumpTo(this.cursor + 1);
  }

  stepBack(): void {
    this.jumpTo(this.cursor - 1);
  }

  /** Clamped to [0, total]; `total` is the legal past-the-end cursor. */
  jumpTo(n: number): void {
    if (!this.doc) return;
    this.cursor = Math.min(Math.max(0, Math.trunc(n)), this.doc.steps.length);
  }

  /**
   * What this object looks like at the current cursor. Total: every key
   * answers, including keys this run never touched.
   */
  stateOf(key: string): RunState {
    if (!this.doc) return "built";
    const i = this.index.get(key);
    // Not a step in this run: UNKNOWN, and unknown keeps standing.
    if (i === undefined) return "built";
    const status = this.doc.steps[i]!.status;
    if (i <= this.cursor) {
      // dbt's own verdict, folded. Checked BEFORE "building" so a failing step
      // ignites on the cursor that reaches it, not the one after.
      if (isFailure(status)) return "failed";
      if (isSkip(status)) return "skipped";
      return i === this.cursor ? "building" : "built";
    }
    // Not reached yet — but a failure already on screen may have taken it down.
    const blame = this.dimsAt.get(key);
    return blame !== undefined && this.cursor >= blame.at ? "skipped" : "pending";
  }

  /** Keys burning at the current cursor — what `Fires.setOverride` wants. */
  failedKeys(): Set<string> {
    const keys = new Set<string>();
    if (!this.doc) return keys;
    for (const step of this.doc.steps) {
      if (this.stateOf(step.object_key) === "failed") keys.add(step.object_key);
    }
    return keys;
  }

  /** Keys dimmed by a cascade at the current cursor. */
  skippedKeys(): Set<string> {
    const keys = new Set<string>();
    if (!this.doc) return keys;
    for (const step of this.doc.steps) {
      if (this.stateOf(step.object_key) === "skipped") keys.add(step.object_key);
    }
    return keys;
  }

  /**
   * The steps `failureKey`'s error took down, AFTER this module's two guards —
   * not the document's raw list. Cursor-independent, so the panel can name the
   * cascade at the moment the failure ignites; sorted, as the document has it.
   *
   * The panel reads THIS rather than `failure_cascade[].skipped` directly, so
   * a guard that drops an entry drops it from the words as well as from the
   * buildings. A panel counting one thing while the city dims another is how a
   * guard gets believed without being true.
   */
  cascadeOf(failureKey: string): string[] {
    return [...this.dimsAt.entries()]
      .filter(([, blame]) => blame.by === failureKey)
      .map(([key]) => key)
      .sort();
  }

  /** The failure whose cascade dimmed `key`, or null. The panel names it so a
   * dimmed building never has to be explained by the viewer. Null for a step
   * dbt reported skipped that no failure on screen accounts for — "skipped,
   * cause not established" is a different fact from "taken down by that one". */
  blamedFor(key: string): string | null {
    if (this.stateOf(key) !== "skipped") return null;
    const blame = this.dimsAt.get(key);
    return blame !== undefined && this.cursor >= blame.at ? blame.by : null;
  }

  /** Per-key height factors, index-aligned with whatever key list is passed —
   * `doc.lots.map(l => l.object_key)` at the call site, which is the order
   * `Buildings` instances in. Pure; no Three.js reaches this module. */
  heightFactors(keys: readonly string[]): number[] {
    return keys.map((key) => HEIGHT[this.stateOf(key)]);
  }
}

/**
 * key -> the cursor at which a failure's cascade dims it.
 *
 * The document's `failure_cascade` is the measured answer and is not
 * recomputed here — it joins three facts (dbt's own `skipped`, reachability
 * over the city's edges, this run's order) that the producer owns. What this
 * function adds is the TIMING, plus two guards on what the document is allowed
 * to make the city say:
 *
 * 1. **Only a step dbt itself reported skipped may dim.** Without this, a
 *    cascade entry naming a model dbt reported built would dim a building that
 *    really did build — an inferred blast radius, which is exactly what the
 *    format refuses to emit and what a client must refuse to draw.
 * 2. **Only a step that comes LATER in this run's order than the failure.** A
 *    cascade cannot run backwards up the graph; a skip recorded before the
 *    failure was reached was not caused by it.
 *
 * Both restate rules `export/run_json.py` already applies, deliberately: a
 * document is not a trusted input, and the cost of the restatement is nine
 * lines against a failure mode (a building dimmed for a reason that is not
 * true) that no screenshot would catch.
 */
function cascadeSchedule(doc: RunDocument, index: Map<string, number>): Map<string, Blame> {
  const dimsAt = new Map<string, Blame>();
  for (const entry of doc.failure_cascade) {
    for (const key of entry.skipped) {
      const i = index.get(key);
      if (i === undefined) continue;
      if (!isSkip(doc.steps[i]!.status)) continue; // guard 1
      if (i <= entry.order) continue; // guard 2
      const previous = dimsAt.get(key);
      // The EARLIEST failure that took it down owns the moment it dims.
      if (previous === undefined || entry.order < previous.at) {
        dimsAt.set(key, { at: entry.order, by: entry.object_key });
      }
    }
  }
  return dimsAt;
}

/** When a cascade dims a building, and which failure did it. */
interface Blame {
  at: number;
  by: string;
}
