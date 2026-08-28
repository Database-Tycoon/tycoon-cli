/**
 * The client side of `runs.json` / `runs/<id>.json` v1. `docs/run-json-v1.md`
 * is normative; this module is its consumer.
 *
 * SEPARATE from `contract.ts` on purpose. That module is the `city.json`
 * consumer and nothing else, and these two formats are separate documents for
 * a reason the contract states out loud: `city.json` v1 is byte-stable and
 * carries no uuid, path or wall clock, so records that carry them — a run's
 * `invocation_id` and `started_at` — live in their own documents. Folding
 * their schemas into one module would be the first step back toward folding
 * the documents.
 *
 * Nothing here invents structure. In particular `status` is dbt's OWN word,
 * relayed by the producer and never remapped, so the CLIENT folds it: that is
 * what `foldStatus` is, and it is the only place in the web app allowed to
 * decide that "runtime error" means failure.
 */

import { z } from "zod";

export const RUNS_FORMAT = "database-tycoon.runs";
export const RUN_FORMAT = "database-tycoon.run";
export const VERSION = 1;

/**
 * The run header, carried in BOTH documents so a client renders the picker and
 * the run's own header from either without a second fetch.
 *
 * `ok` is derived by the producer (no error models, no failed tests) and the
 * stored `success` column is never read. `failed_count` is failing steps WITH
 * a building — what a replay can set on fire — and it differs from
 * `models_error` whenever the run touched models this city has not got. That
 * difference is information, so both are shown.
 */
const runHeader = z.object({
  id: z.string(),
  command: z.string(),
  started_at: z.string(),
  target: z.string(),
  ok: z.boolean(),
  models_error: z.number().int().nonnegative(),
  tests_failed: z.number().int().nonnegative(),
  elapsed_s: z.number().nonnegative(),
  step_count: z.number().int().nonnegative(),
  unmapped_count: z.number().int().nonnegative(),
  failed_count: z.number().int().nonnegative(),
});

export const runsIndexSchema = z.object({
  format: z.literal(RUNS_FORMAT),
  version: z.literal(VERSION),
  database: z.string(),
  runs: z.array(runHeader),
  // The loader's degradation ladder verbatim, plus this format's own two. A
  // client that hides these has turned a named absence back into a silence.
  notes: z.array(z.string()),
});

const runStep = z.object({
  order: z.number().int().nonnegative(),
  object_key: z.string(),
  unique_id: z.string(),
  node_kind: z.string(),
  // dbt's own word. Relayed, never remapped — see `foldStatus`.
  status: z.string(),
  execution_time_s: z.number(),
  // Upstream object_keys, already intersected with this city's objects, so a
  // client is never handed a key it cannot resolve to a building.
  depends_on: z.array(z.string()),
});

const unmappedNode = z.object({
  unique_id: z.string(),
  node_kind: z.string(),
  status: z.string(),
  execution_time_s: z.number(),
});

/**
 * What one failure took down with it: only steps dbt ITSELF reported skipped,
 * reachable from the failure over the city's measured edges, and later in this
 * run's order. An entry with an empty `skipped` is emitted for every failure —
 * "nothing measurable cascaded" is a fact, and a client that only ever sees
 * non-empty entries cannot tell it from "we did not look".
 */
const cascadeEntry = z.object({
  object_key: z.string(),
  order: z.number().int().nonnegative(),
  skipped: z.array(z.string()),
});

export const runSchema = z.object({
  format: z.literal(RUN_FORMAT),
  version: z.literal(VERSION),
  run: runHeader,
  // "reconstructed" today, "observed" the day a metadata database records
  // per-node start times. A plain string so that day needs no client change.
  order_source: z.string(),
  note: z.string(),
  steps: z.array(runStep),
  unmapped: z.array(unmappedNode),
  failure_cascade: z.array(cascadeEntry),
});

export type RunHeader = z.infer<typeof runHeader>;
export type RunsIndex = z.infer<typeof runsIndexSchema>;
export type RunDocument = z.infer<typeof runSchema>;
export type RunStep = z.infer<typeof runStep>;
export type RunCascadeEntry = z.infer<typeof cascadeEntry>;

// dbt's spellings, mirroring `export/run_json.py`'s FAILED_STATUSES /
// SKIPPED_STATUSES. The producer relays the original word precisely so that
// an unknown one such as "partial success" arrives intact; folding it into a
// channel a renderer can colour is the client's job, and this is that job.
const FAILED_STATUSES = new Set(["error", "fail", "failure", "runtime error"]);
const SKIPPED_STATUSES = new Set(["skipped", "skip"]);

export type FoldedStatus = "failed" | "skipped" | "other";

/** dbt's word folded to the three outcomes a city can draw. Anything this
 * vocabulary does not recognise is `other` — never guessed into a failure. */
export function foldStatus(status: string): FoldedStatus {
  const word = status.trim().toLowerCase();
  if (FAILED_STATUSES.has(word)) return "failed";
  if (SKIPPED_STATUSES.has(word)) return "skipped";
  return "other";
}

export function isFailure(status: string): boolean {
  return foldStatus(status) === "failed";
}

export function isSkip(status: string): boolean {
  return foldStatus(status) === "skipped";
}

/**
 * Picker order: WORST first, then newest first.
 *
 * The index already arrives newest-first, and a failed run is the one someone
 * opened this panel to look at. Sorted on (ok, started_at desc, id), which
 * cannot tie — ids are unique by construction.
 */
export function pickerOrder(runs: readonly RunHeader[]): RunHeader[] {
  return [...runs].sort(
    (a, b) =>
      Number(a.ok) - Number(b.ok) ||
      b.started_at.localeCompare(a.started_at) ||
      a.id.localeCompare(b.id),
  );
}

export async function loadRuns(url = "./runs.json"): Promise<RunsIndex> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`fetching ${url}: HTTP ${response.status}`);
  return runsIndexSchema.parse(await response.json());
}

/**
 * One run's document. The id is encoded because it becomes a path segment;
 * the server validates it against the known invocation set before it is used
 * for anything, but a client that pastes it into a URL raw would still be the
 * one that built the malformed request.
 */
export async function loadRun(id: string, base = "./runs/"): Promise<RunDocument> {
  const url = `${base}${encodeURIComponent(id)}.json`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`fetching ${url}: HTTP ${response.status}`);
  return runSchema.parse(await response.json());
}
