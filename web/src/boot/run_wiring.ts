/**
 * The run replay's composition: the state machine (`sim/run_replay.ts`), the
 * panel (`ui/run_panel.ts`) and the scene handles they drive, joined in one
 * place so `main.ts` stays a wiring file.
 *
 * Nothing here computes a fact. Every channel it moves is a restatement of
 * something the run document already says:
 *
 * - `Fires` / `FireTrucks` take an OVERRIDE of the keys dbt reported errored
 *   at the cursor, so a specific invocation's failures burn and the station
 *   answers them — the trucks follow for free, still on roads only, still
 *   never claiming a fix.
 * - `Buildings.setReplayProgress` renders pending (not yet reached) and
 *   skipped (stunted — never built in this run) from the same pure `stateOf`.
 * - `Traffic` is overridden to the CURRENT step's in-edges and nothing else.
 *   Ambient flow is suppressed for the length of the playback: that build
 *   really did move data along exactly those streets, and anything else on
 *   screen during a step would be theater.
 * - The camera visits the current step through main's existing `visit`.
 */

import type { CityDocument } from "../contract";
import { loadRun, loadRuns } from "../contract_runs";
import type { Tile } from "../sim/paths";
import { RunReplay } from "../sim/run_replay";
import { RunPanel } from "../ui/run_panel";
import type { MountedCity } from "./mount";

export interface RunWiringDeps {
  /** Getters: both are replaced wholesale by an R refresh. */
  doc: () => CityDocument;
  city: () => MountedCity;
  /** main's door: fly the camera to a key and select it. */
  visit: (key: string) => void;
  /** Footer line; null restores the standing status. */
  setStatus: (text: string | null) => void;
}

export interface RunWiring {
  replay: RunReplay;
  panel: RunPanel;
  /** Push the machine's current state onto the scene. Idempotent, and safe to
   * call against a freshly mounted city after an R refresh. */
  apply: () => void;
  /** Open the panel and begin a run; the picker's first entry when unnamed. */
  start: (id?: string) => Promise<void>;
}

export function installRunReplay(deps: RunWiringDeps): RunWiring {
  const replay = new RunReplay();

  const panel = new RunPanel({
    replay,
    loadIndex: () => loadRuns("./runs.json"),
    onPick: (id) => pick(id),
    onExit: () => {
      replay.exit();
      apply();
    },
    onChange: () => apply(),
    onVisit: deps.visit,
    aggregate: () => ({
      available: deps.city().replay.available,
      note: deps.city().replay.note,
      start: () => {
        deps.city().replay.start();
        deps.setStatus(`replaying last run — ${deps.city().replay.note}`);
      },
    }),
  });

  async function pick(id: string): Promise<void> {
    try {
      replay.load(await loadRun(id));
    } catch (error) {
      // A run the index advertised but whose document will not load is a fact
      // worth showing; silently falling back to the picker would read as a
      // click that did nothing.
      panel.noteError(String(error));
      return;
    }
    apply();
  }

  function apply(): void {
    const city = deps.city();
    if (replay.phase === "off") {
      city.buildings.setReplayProgress(null);
      city.fires.setOverride(null);
      city.trucks.setOverride(null);
      city.traffic.setOverride(null);
      deps.setStatus(null);
      panel.render();
      return;
    }
    const doc = deps.doc();
    city.buildings.setReplayProgress(replay.heightFactors(doc.lots.map((l) => l.object_key)));
    const burning = replay.failedKeys();
    city.fires.setOverride(burning);
    city.trucks.setOverride(burning);
    city.traffic.setOverride(inEdgeRoutes(doc, replay));
    const step = replay.current();
    if (step) deps.visit(step.object_key);
    const run = replay.document!.run;
    deps.setStatus(
      replay.phase === "done"
        ? `replay finished — ${run.command} ${run.id} — ${replay.document!.note}`
        : `replaying ${run.command} ${run.id} — step ${replay.at + 1}/${replay.total} — ` +
          `${replay.document!.note}`,
    );
    panel.render();
  }

  async function start(id?: string): Promise<void> {
    await panel.open();
    const chosen = id ?? panel.firstRunId();
    if (chosen === null || chosen === undefined) return;
    await pick(chosen);
  }

  const button = document.getElementById("replay-button") as HTMLButtonElement;
  button.addEventListener("click", () => {
    if (panel.visible && replay.phase === "off") panel.close();
    else void panel.open();
  });

  return { replay, panel, apply, start };
}

/**
 * The streets the CURRENT step's build actually moved data along: edges whose
 * destination is the step and whose source the run document lists as one of
 * its dependencies. Empty past the end of the run, and empty for a step with
 * no upstream on this map — a still city, never a fallback to ambience.
 */
function inEdgeRoutes(doc: CityDocument, replay: RunReplay): Tile[][] {
  const step = replay.current();
  if (!step) return [];
  const upstream = new Set(step.depends_on);
  return doc.edges
    .filter((e) => e.dst === step.object_key && upstream.has(e.src) && e.route.length > 0)
    .map((e) => e.route.map(([x, y]) => [x, y] as Tile));
}
