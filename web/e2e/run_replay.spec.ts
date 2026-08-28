/**
 * RUN REPLAY — stepping through one named invocation, and the failure cascade.
 *
 * Served by route interception, exactly as `rich.spec.ts` does, over the
 * committed `fixtures/rich.city.json` so the city under the replay is the same
 * frozen one every other positive-path spec uses. The run documents are
 * COMMITTED FIXTURES, never a live server's run data: a spec pointed at real
 * history asserts whatever happened to run last.
 *
 * To regenerate the run documents deliberately (after a `run.json` v1 change):
 *   uv run python scripts/make_demo_tycoon.py
 *   uv run tycoon-city-export demo-tycoon /tmp/rich-export
 *   cp /tmp/rich-export/runs.json      web/e2e/fixtures/runs.index.json
 *   cp /tmp/rich-export/runs/<id>.json web/e2e/fixtures/run.fail.json
 * and re-derive every count below from the new documents by hand. The demo
 * generator does not currently write a FAILING invocation, so `run.fail.json`
 * is authored against the frozen city's real object keys and edges; it is the
 * document `export/run_json.py` would produce for a build in which
 * `staging.stg_customers` errored, and it is checked against that module's
 * three cascade rules by the guard tests at the bottom of this file.
 *
 * EVERY NUMBER HERE IS HAND-COUNTED off `fixtures/run.fail.json`:
 *
 *   idx key                        status
 *   0   raw.customers              success
 *   1   raw.orders                 success
 *   2   staging.stg_customers      error     <- the fire
 *   3   staging.stg_orders         success
 *   4   mart.dim__customer_status  skipped   |
 *   5   mart.dim__customers        skipped   | the cascade of #2,
 *   6   mart.mart__broken          skipped   | as dbt reported it
 *   8   mart.mart__revenue         skipped   |
 *   7   mart.mart__forgotten       success   <- downstream of stg_ORDERS, lit
 *
 * and `scratch.experiment` is in the city but not in the run at all.
 *
 * THE WRONG-AXIS TRAP THIS FILE IS BUILT AGAINST: "some building is on fire
 * during replay" passes when the wrong building burns AND passes on this
 * fixture, which already has a standing fire (`mart.mart__revenue`,
 * test_status "fail"). So every assertion names WHICH key at WHICH cursor, and
 * cursor 0 is pinned at ZERO fires — which only holds because the replay
 * override really did take the document's own fire off the map.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import { open } from "./helpers";

const CITY = path.resolve("e2e/fixtures/rich.city.json");
const INDEX = path.resolve("e2e/fixtures/runs.index.json");
const RUN_FAIL = path.resolve("e2e/fixtures/run.fail.json");
const RUN_OK = path.resolve("e2e/fixtures/run.ok.json");

const FAIL_ID = "8b4d19e2-0000-4000-8000-00000000000b";
const OK_ID = "2f1c6b40-0000-4000-8000-00000000000a";

/** The four models dbt itself reported skipped behind stg_customers' error. */
const CASCADE = [
  "mart.dim__customer_status",
  "mart.dim__customers",
  "mart.mart__broken",
  "mart.mart__revenue",
];

const readJson = async (file: string): Promise<Record<string, unknown>> =>
  JSON.parse(await readFile(file, "utf8")) as Record<string, unknown>;

/** Serve the frozen city, the run index, and both run documents. */
async function serve(page: Page, runFail?: unknown, index?: unknown): Promise<void> {
  await page.route("**/city.json*", (route) => route.fulfill({ path: CITY }));
  await page.route("**/runs.json*", (route) =>
    index === undefined
      ? route.fulfill({ path: INDEX })
      : route.fulfill({ contentType: "application/json", body: JSON.stringify(index) }),
  );
  await page.route("**/runs/*.json*", (route) => {
    if (route.request().url().includes(OK_ID)) return route.fulfill({ path: RUN_OK });
    return runFail === undefined
      ? route.fulfill({ path: RUN_FAIL })
      : route.fulfill({ contentType: "application/json", body: JSON.stringify(runFail) });
  });
}

/** Every lot's replay state at the current cursor, as one map. */
async function states(page: Page): Promise<Record<string, string>> {
  return page.evaluate(() =>
    Object.fromEntries(
      window.__tycoonCity!.doc.lots.map((l) => [l.object_key, window.__tycoonCity!.runStateOf(l.object_key)]),
    ),
  );
}

const keysWhere = (map: Record<string, string>, state: string): string[] =>
  Object.entries(map)
    .filter(([, s]) => s === state)
    .map(([k]) => k)
    .sort();

// ---------------------------------------------------------------------------
// The picker, and the named absence
// ---------------------------------------------------------------------------

test("the picker lists runs worst-first, not newest-first", async ({ page }) => {
  await serve(page);
  await open(page, "?settle=1");

  await page.locator("#replay-button").click();
  const rows = page.locator("#run-panel li[data-run]");
  await expect(rows).toHaveCount(2);
  // The index arrives newest-first, and the OK run IS the newer one — so this
  // only passes if the panel re-sorted worst-first rather than echoing order.
  expect(await rows.nth(0).getAttribute("data-run")).toBe(FAIL_ID);
  expect(await rows.nth(1).getAttribute("data-run")).toBe(OK_ID);
  expect((await rows.nth(0).innerText()).toLowerCase()).toContain("1 failed here");
});

test("locked run metadata SAYS SO — the control never quietly disappears", async ({ page }) => {
  // `/runs.json` answers 200 with the loader's own sentence precisely so a
  // client has something to show. Hiding the button here would make a locked
  // metadata database indistinguishable from a broken build.
  await serve(page, undefined, {
    format: "database-tycoon.runs",
    version: 1,
    database: "demo",
    runs: [],
    notes: ["run metadata unreadable (locked by a running tycoon command?)"],
  });
  const errors = await open(page, "?settle=1");

  await expect(page.locator("#replay-button")).toBeVisible();
  await page.locator("#replay-button").click();
  const panel = page.locator("#run-panel"); // the index fetch resolves async
  await expect(panel).toContainText("run replay unavailable — run metadata locked");
  // And the loader's sentence itself, verbatim, underneath the headline.
  await expect(panel).toContainText("locked by a running tycoon command");
  expect(errors).toEqual([]);
});

// ---------------------------------------------------------------------------
// The cascade, cursor by cursor
// ---------------------------------------------------------------------------

test("cursor 0 puts out the document's own fire: nothing has been built yet", async ({ page }) => {
  await serve(page);
  await open(page, "?settle=1");

  // Before the replay the frozen fixture burns mart.mart__revenue.
  expect(await page.evaluate(() => window.__tycoonCity!.fireCount())).toBe(1);

  await page.evaluate((id) => window.__tycoonCity!.runReplay(id), FAIL_ID);
  expect(await page.evaluate(() => window.__tycoonCity!.runCursor())).toMatchObject({
    phase: "playing",
    at: 0,
    total: 9,
    key: "raw.customers",
  });
  // ZERO, not "fewer": at step one of the run nothing has failed yet, and the
  // standing fire belongs to a different question.
  expect(await page.evaluate(() => window.__tycoonCity!.fireCount())).toBe(0);

  const map = await states(page);
  expect(map["raw.customers"]).toBe("building");
  expect(map["staging.stg_customers"]).toBe("pending");
  expect(keysWhere(map, "skipped")).toEqual([]);
  expect(keysWhere(map, "failed")).toEqual([]);
  // Not a step in this run: unknown, and unknown keeps standing.
  expect(map["scratch.experiment"]).toBe("built");
});

test("staging.stg_customers ignites at cursor 2 and takes exactly four with it", async ({
  page,
}) => {
  await serve(page);
  await open(page, "?settle=1");
  await page.evaluate((id) => window.__tycoonCity!.runReplay(id), FAIL_ID);
  await page.evaluate(() => {
    window.__tycoonCity!.runStep();
    window.__tycoonCity!.runStep();
  });

  expect(await page.evaluate(() => window.__tycoonCity!.runCursor())).toMatchObject({
    at: 2,
    key: "staging.stg_customers",
  });
  const map = await states(page);
  // WHICH building burns, not how many — the fixture's own fire is on
  // mart.mart__revenue, so a count alone would pass on the wrong one.
  expect(keysWhere(map, "failed")).toEqual(["staging.stg_customers"]);
  expect(await page.evaluate(() => window.__tycoonCity!.fireCount())).toBe(1);
  // The EXACT dimmed set. mart.mart__forgotten is downstream of stg_ORDERS and
  // dbt built it, so it must stay lit; staging.stg_orders has not been reached.
  expect(keysWhere(map, "skipped")).toEqual(CASCADE);
  expect(keysWhere(map, "built")).toEqual([
    "raw.customers",
    "raw.orders",
    "scratch.experiment", // not in the run: unknown keeps standing
  ]);
  expect(keysWhere(map, "pending")).toEqual(["mart.mart__forgotten", "staging.stg_orders"]);
});

test("stepping BACK is exact, not an undo log", async ({ page }) => {
  await serve(page);
  await open(page, "?settle=1");
  await page.evaluate((id) => window.__tycoonCity!.runReplay(id), FAIL_ID);
  await page.evaluate(() => {
    window.__tycoonCity!.runStep();
    window.__tycoonCity!.runStep();
  });
  expect(await page.evaluate(() => window.__tycoonCity!.fireCount())).toBe(1);

  await page.keyboard.press("ArrowLeft");
  expect(await page.evaluate(() => window.__tycoonCity!.runCursor())).toMatchObject({ at: 1 });
  // The fire and the whole cascade are GONE, because `stateOf` is a function
  // of the cursor and not a tally the steps mutated.
  expect(await page.evaluate(() => window.__tycoonCity!.fireCount())).toBe(0);
  const map = await states(page);
  expect(keysWhere(map, "failed")).toEqual([]);
  expect(keysWhere(map, "skipped")).toEqual([]);
  expect(map["raw.orders"]).toBe("building");
});

test("space walks to the end; 0 restarts; esc restores the document's own fire", async ({
  page,
}) => {
  await serve(page);
  await open(page, "?settle=1");
  await page.evaluate((id) => window.__tycoonCity!.runReplay(id), FAIL_ID);

  for (let i = 0; i < 9; i += 1) await page.keyboard.press(" ");
  expect(await page.evaluate(() => window.__tycoonCity!.runCursor())).toMatchObject({
    phase: "done",
    at: 9,
    key: null,
  });
  // Past the end everything the run touched is resolved; the error still burns.
  const finished = await states(page);
  expect(keysWhere(finished, "failed")).toEqual(["staging.stg_customers"]);
  expect(keysWhere(finished, "skipped")).toEqual(CASCADE);
  expect(keysWhere(finished, "pending")).toEqual([]);

  await page.keyboard.press("0");
  expect(await page.evaluate(() => window.__tycoonCity!.runCursor())).toMatchObject({ at: 0 });
  expect(await page.evaluate(() => window.__tycoonCity!.fireCount())).toBe(0);

  await page.keyboard.press("Escape");
  expect(await page.evaluate(() => window.__tycoonCity!.runCursor())).toMatchObject({ phase: "off" });
  // Exit restores the DOCUMENT's fires, which is a different fact and a
  // different building.
  expect(await page.evaluate(() => window.__tycoonCity!.fireCount())).toBe(1);
  expect(await page.evaluate(() => window.__tycoonCity!.runStateOf("staging.stg_customers"))).toBe("built");
});

test("the firehouse answers the run's fire, not the document's", async ({ page }) => {
  await serve(page);
  await open(page, "?settle=1");
  expect(await page.evaluate(() => window.__tycoonCity!.truckCount())).toBe(1); // mart__revenue

  await page.evaluate((id) => window.__tycoonCity!.runReplay(id), FAIL_ID);
  expect(await page.evaluate(() => window.__tycoonCity!.truckCount())).toBe(0); // nothing burning
  await page.evaluate(() => {
    window.__tycoonCity!.runStep();
    window.__tycoonCity!.runStep();
  });
  // One callout, and it is the replay's: the fleets follow the fire override
  // without knowing a replay exists.
  expect(await page.evaluate(() => window.__tycoonCity!.truckCount())).toBe(1);
});

test("an all-green run never burns anything, at any cursor", async ({ page }) => {
  // The negative control. Without it, every assertion above is satisfied by a
  // machine that sets fire to step 2 of whatever it is handed.
  await serve(page);
  await open(page, "?settle=1");
  await page.evaluate((id) => window.__tycoonCity!.runReplay(id), OK_ID);

  for (let cursor = 0; cursor <= 9; cursor += 1) {
    const map = await states(page);
    expect(keysWhere(map, "failed")).toEqual([]);
    expect(keysWhere(map, "skipped")).toEqual([]);
    expect(await page.evaluate(() => window.__tycoonCity!.fireCount())).toBe(0);
    await page.evaluate(() => window.__tycoonCity!.runStep());
  }
});

// ---------------------------------------------------------------------------
// The panel names the step, and every name is a door
// ---------------------------------------------------------------------------

test("the step inspector names the failure and its cascade, and the names are doors", async ({
  page,
}) => {
  await serve(page);
  await open(page, "?settle=1");
  await page.locator("#replay-button").click();
  await page.locator(`#run-panel li[data-run="${FAIL_ID}"]`).click();
  // The run document is fetched async; wait for step one before stepping on.
  await expect(page.locator("#run-panel")).toContainText(/step 1 \/ 9/i);
  await page.evaluate(() => {
    window.__tycoonCity!.runStep();
    window.__tycoonCity!.runStep();
  });

  const panel = await page.locator("#run-panel").innerText();
  expect(panel.toLowerCase()).toContain("step 3 / 9"); // the h3 is upper-cased by CSS
  expect(panel).toContain("staging.stg_customers");
  expect(panel).toContain("error");
  expect(panel).toContain("4 downstream models skipped");
  expect(panel).toContain("durations measured, ordering reconstructed");

  // Every object name is a door.
  await page.locator('#run-panel .door[data-key="mart.mart__broken"]').first().click();
  await page.waitForTimeout(900); // the glide
  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBe("mart.mart__broken");
});

// ---------------------------------------------------------------------------
// Determinism and traffic
// ---------------------------------------------------------------------------

test("nothing advances on a timer — the cursor moves only on input", async ({ page }) => {
  await serve(page);
  await open(page, "?settle=1");
  await page.evaluate((id) => window.__tycoonCity!.runReplay(id), FAIL_ID);

  await page.waitForTimeout(2500);
  expect(await page.evaluate(() => window.__tycoonCity!.runCursor())).toMatchObject({ at: 0 });
  expect(await page.evaluate(() => window.__tycoonCity!.fireCount())).toBe(0);
});

test("replay suppresses ambient traffic and drives the current step's in-edges", async ({
  page,
}) => {
  await serve(page);
  // ?ambient=1 is the strongest possible control: it normally puts vehicles on
  // every routed edge in the city regardless of history.
  await open(page, "?ambient=1&seed=7&lens=none");
  await page.waitForTimeout(1200);
  expect(await page.evaluate(() => window.__tycoonCity!.vehicleCount())).toBeGreaterThan(0);

  // Step 0 is raw.customers, a source with NO in-edges on this map: a still
  // city, not a fallback to ambience.
  await page.evaluate((id) => window.__tycoonCity!.runReplay(id), FAIL_ID);
  await page.waitForTimeout(1200);
  expect(await page.evaluate(() => window.__tycoonCity!.vehicleCount())).toBe(0);

  // Step 2 is staging.stg_customers, whose one in-edge (raw.customers ->
  // staging.stg_customers) really did carry data during that build.
  await page.evaluate(() => {
    window.__tycoonCity!.runStep();
    window.__tycoonCity!.runStep();
  });
  await page.waitForTimeout(1500);
  expect(await page.evaluate(() => window.__tycoonCity!.vehicleCount())).toBeGreaterThan(0);
});

// ---------------------------------------------------------------------------
// The client's two guards on what a run document may make the city say
// ---------------------------------------------------------------------------

test("a cascade naming a model dbt BUILT does not dim it", async ({ page }) => {
  // Guard 1. `run_json.py` will not emit this, and that is exactly why the
  // client restates the rule: an inferred blast radius is the thing this
  // format refuses to produce and a client must refuse to draw.
  const doc = await readJson(RUN_FAIL);
  (doc.failure_cascade as { skipped: string[] }[])[0]!.skipped.push("mart.mart__forgotten");
  await serve(page, doc);
  await open(page, "?settle=1");
  await page.evaluate((id) => window.__tycoonCity!.runReplay(id), FAIL_ID);
  await page.evaluate(() => {
    window.__tycoonCity!.runStep();
    window.__tycoonCity!.runStep();
  });

  const map = await states(page);
  // dbt reported mart.mart__forgotten "success". It stays pending until its
  // own turn, and the dimmed set is the honest four.
  expect(map["mart.mart__forgotten"]).toBe("pending");
  expect(keysWhere(map, "skipped")).toEqual(CASCADE);
});

test("a cascade cannot run backwards up the run order", async ({ page }) => {
  // Guard 2. raw.orders ran at order 1, BEFORE stg_customers failed at order
  // 2, so nothing stg_customers did can be blamed for it — even if the
  // document says so.
  const doc = await readJson(RUN_FAIL);
  (doc.steps as { object_key: string; status: string }[])[1]!.status = "skipped";
  (doc.failure_cascade as { skipped: string[] }[])[0]!.skipped.push("raw.orders");
  await serve(page, doc);
  await open(page, "?settle=1");
  await page.evaluate((id) => window.__tycoonCity!.runReplay(id), FAIL_ID);
  await page.evaluate(() => {
    window.__tycoonCity!.runStep();
    window.__tycoonCity!.runStep();
  });

  const panel = await page.locator("#run-panel").innerText();
  // The failure's own cascade line must not have adopted it...
  expect(panel).toContain("4 downstream models skipped");
  // ...and stepping back onto raw.orders must not blame the later failure.
  await page.keyboard.press("ArrowLeft");
  expect(await page.evaluate(() => window.__tycoonCity!.runCursor())).toMatchObject({
    at: 1,
    key: "raw.orders",
  });
  const earlier = await page.locator("#run-panel").innerText();
  expect(earlier).toContain("raw.orders");
  expect(earlier).toContain("skipped");
  expect(earlier).not.toContain("errored");
});
