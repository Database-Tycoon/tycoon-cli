/**
 * THE USAGE OVERLAY — measured run appearances, and the absence of them.
 *
 * THE FIXTURE. `fixtures/usage.city.json` is `fixtures/rich.city.json` (the
 * committed demo-tycoon export) with exactly TWO `usage` blocks rewritten —
 * `diff` the two files and that is the whole change:
 *
 *   mart.dim__customers  → runs_seen 0, rate null   (measured, never ran)
 *   raw.orders           → runs_seen 2, rate 0.0952 (measured, ~once per 10d)
 *
 * They are hand-written because demo-tycoon's real run history cannot produce
 * them: every object its runs mention was actually built, so the export has no
 * zero-appearance object at all. Regenerate the base with the recipe in
 * `rich.spec.ts`'s header, then re-apply those two blocks. Everything else in
 * the file — including the four objects with `usage: null` — is real exporter
 * output, and the FIXTURE PRECONDITION test below refuses to run against a
 * fixture that has drifted out of carrying all four states.
 *
 * THE WRONG-AXIS TRAP THIS FILE IS BUILT AGAINST: `expect(overlay).toBeVisible()`
 * and "some building is marked" both pass when the WRONG buildings are marked,
 * and the specific wrong marking that matters here is the one this feature
 * exists to prevent — an UNMEASURED table wearing the quiet treatment, which
 * reads as a deprecation candidate to anyone looking at the map. So every
 * assertion below names WHICH object keys got WHICH treatment, hand-counted
 * from the fixture, and `usagePainted` reads them back off the live meshes in
 * the scene rather than off a bookkeeping tally.
 *
 * Hand-counted from the fixture (`QUIET_PER_DAY` is once a week, 0.1428/day):
 *   busy    3 — mart__revenue 1.145, stg_customers 1.145, stg_orders 4.081
 *   quiet   2 — dim__customers (0 runs), raw.orders (0.095/day)
 *   unrated 1 — mart__forgotten (1 run, so no cadence exists to report)
 *   unknown 4 — dim__customer_status, mart__broken, raw.customers,
 *               scratch.experiment — and these get NOTHING
 *   → 8 instances in the scene (3 bars + 1 ring + 2 cones + 2 lids: quiet is
 *     marked twice, on the roof and in the beacon band), 4 objects with none.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect, test } from "@playwright/test";
import { open } from "./helpers";

const FIXTURE = path.resolve("e2e/fixtures/usage.city.json");
const readFixture = (): Promise<string> => readFile(FIXTURE, "utf8");

const BUSY = ["mart.mart__revenue", "staging.stg_customers", "staging.stg_orders"];
const QUIET = ["mart.dim__customers", "raw.orders"];
const UNRATED = ["mart.mart__forgotten"];
const UNKNOWN = [
  "mart.dim__customer_status",
  "mart.mart__broken",
  "raw.customers",
  "scratch.experiment",
];

test.beforeEach(async ({ page }) => {
  await page.route("**/city.json*", (route) => route.fulfill({ path: FIXTURE }));
});

// ---------------------------------------------------------------------------
// The fixture itself. Everything below is worthless if this drifts.
// ---------------------------------------------------------------------------

test("FIXTURE PRECONDITION: the document really carries all four usage states", async ({
  page,
}) => {
  await open(page, "?settle=1");

  const usage = await page.evaluate(() =>
    Object.fromEntries(
      window.__tycoonCity!.doc.objects.map((o) => [
        o.key,
        o.usage === null ? null : [o.usage.source, o.usage.runs_seen, o.usage.rate_per_day],
      ]),
    ),
  );
  expect(usage).toEqual({
    "mart.dim__customer_status": null,
    "mart.dim__customers": ["runs", 0, null],
    "mart.mart__broken": null,
    "mart.mart__forgotten": ["runs", 1, null],
    "mart.mart__revenue": ["runs", 8, 1.145455],
    "raw.customers": null,
    "raw.orders": ["runs", 2, 0.095238],
    "scratch.experiment": null,
    "staging.stg_customers": ["runs", 8, 1.145455],
    "staging.stg_orders": ["runs", 29, 4.080972],
  });

  // Every object owns a lot, so "not painted" can only ever mean the overlay
  // chose not to paint it — never that the building was missing.
  const lots = await page.evaluate(() => window.__tycoonCity!.doc.lots.map((l) => l.object_key).sort());
  expect(lots).toEqual([...BUSY, ...QUIET, ...UNRATED, ...UNKNOWN].sort());
});

// ---------------------------------------------------------------------------
// WHICH buildings, not how many
// ---------------------------------------------------------------------------

test("each measured building gets its own treatment, and the unmeasured get none", async ({
  page,
}) => {
  const errors = await open(page, "?settle=1");

  expect(await page.evaluate(() => window.__tycoonCity!.usagePainted("busy"))).toEqual(BUSY.slice().sort());
  expect(await page.evaluate(() => window.__tycoonCity!.usagePainted("quiet"))).toEqual(
    QUIET.slice().sort(),
  );
  expect(await page.evaluate(() => window.__tycoonCity!.usagePainted("unrated"))).toEqual(UNRATED);

  // 3 bars + 1 ring + 2 cones + 2 lids — counted off the live meshes, so a
  // treatment that was built and never added to the scene reads as missing.
  expect(await page.evaluate(() => window.__tycoonCity!.usageInstanceCount())).toBe(8);
  expect(errors).toEqual([]);
});

test("a NULL usage is unknown, and unknown is never drawn as quiet", async ({ page }) => {
  await open(page, "?settle=1");

  // The rule, stated four ways, because this is the one way this feature can
  // lie: an object the run history never mentioned must not appear under ANY
  // treatment, least of all the quiet one a consultant would act on.
  for (const state of ["busy", "quiet", "unrated"] as const) {
    const painted = await page.evaluate((s) => window.__tycoonCity!.usagePainted(s), state);
    for (const key of UNKNOWN) expect(painted).not.toContain(key);
  }
  expect(await page.evaluate(() => window.__tycoonCity!.usagePainted("unknown"))).toEqual([]);
});

test("seen-once is its own state: no cadence exists, so none is invented", async ({ page }) => {
  await open(page, "?settle=1");

  // mart__forgotten appeared in exactly one run over a zero span, so
  // `rate_per_day` is null by the emitter's own guard. It is not busy (there
  // is no rate to place on the ramp) and it is not quiet (it demonstrably
  // ran), and it is certainly not unknown — it was measured.
  const forgotten = await page.evaluate(
    () => window.__tycoonCity!.doc.objects.find((o) => o.key === "mart.mart__forgotten")!.usage,
  );
  expect(forgotten).toMatchObject({ runs_seen: 1, rate_per_day: null });

  expect(await page.evaluate(() => window.__tycoonCity!.usagePainted("unrated"))).toEqual([
    "mart.mart__forgotten",
  ]);
  for (const state of ["busy", "quiet"] as const) {
    expect(await page.evaluate((s) => window.__tycoonCity!.usagePainted(s), state)).not.toContain(
      "mart.mart__forgotten",
    );
  }
});

test("a catalog with no run history at all shows no usage, named", async ({ page }) => {
  // The state the loader reaches on any database whose runs were never
  // recorded — which is most of them. Painting every building quiet here
  // would tell a viewer their whole warehouse is dead.
  const doc = JSON.parse(await readFixture());
  for (const object of doc.objects) object.usage = null;
  await page.route("**/city.json*", (route) =>
    route.fulfill({ contentType: "application/json", body: JSON.stringify(doc) }),
  );

  const errors = await open(page, "?settle=1");

  expect(await page.evaluate(() => window.__tycoonCity!.usageInstanceCount())).toBe(0);
  for (const state of ["busy", "quiet", "unrated"] as const) {
    expect(await page.evaluate((s) => window.__tycoonCity!.usagePainted(s), state)).toEqual([]);
  }

  // The absence is NAMED, exactly as the weather names an empty cell list.
  const legend = (await page.locator("#legend").innerText()).toLowerCase();
  expect(legend).toContain("usage unmeasured for 10 — unknown, not unused");
  expect(legend).not.toContain("quiet lid");
  expect(legend).not.toContain("usage beacon");
  expect(errors).toEqual([]);
});

test("the legend counts every state and names what was measured", async ({ page }) => {
  await open(page, "?settle=1");

  const legend = (await page.locator("#legend").innerText()).toLowerCase();
  expect(legend).toContain("usage beacon = runs/day (3 busy)");
  expect(legend).toContain("quiet lid = measured, little used (2)");
  expect(legend).toContain("usage ring = seen, cadence unknown (1)");
  expect(legend).toContain("usage unmeasured for 4 — unknown, not unused");
  // The `source` discriminator travels with the numbers: these are build/run
  // appearances, and a MotherDuck document's would not be.
  expect(await page.locator("#legend").innerHTML()).toContain("not query traffic");
});

// ---------------------------------------------------------------------------
// Wiring: the key, the lens, the freeze
// ---------------------------------------------------------------------------

test("U toggles the overlay without destroying the measured facts", async ({ page }) => {
  await open(page, "?settle=1");

  expect(await page.evaluate(() => window.__tycoonCity!.usageVisible())).toBe(true);
  const instances = await page.evaluate(() => window.__tycoonCity!.usageInstanceCount());
  expect(instances).toBe(8);

  await page.keyboard.press("u");
  expect(await page.evaluate(() => window.__tycoonCity!.usageVisible())).toBe(false);
  expect(await page.evaluate(() => window.__tycoonCity!.usageInstanceCount())).toBe(instances);

  // And the keymap says so, so a viewer can find it without reading source.
  await page.locator("#keys-button").click();
  expect((await page.locator("#keys-pop").innerText()).toLowerCase()).toContain("usage overlay");
});

test("the analytics-engineer lens raises usage — and only usage", async ({ page }) => {
  await open(page, "?settle=1&lens=analytics-engineer");

  expect(await page.evaluate(() => window.__tycoonCity!.usageVisible())).toBe(true);
  expect(await page.evaluate(() => window.__tycoonCity!.flowVisible())).toBe(false);
  expect(await page.evaluate(() => window.__tycoonCity!.weatherVisible())).toBe(false);

  // Exclusive on purpose: another role's view puts it away again, and hiding
  // it never discards what was measured.
  await page.evaluate(() => window.__tycoonCity!.setLens("on-call"));
  expect(await page.evaluate(() => window.__tycoonCity!.usageVisible())).toBe(false);
  expect(await page.evaluate(() => window.__tycoonCity!.weatherVisible())).toBe(true);
  expect(await page.evaluate(() => window.__tycoonCity!.usageInstanceCount())).toBe(8);
});

test("the beacons are frozen under ?settle=1 and breathe without it", async ({ page }) => {
  await open(page, "?settle=1");
  await page.waitForTimeout(900);
  expect(await page.evaluate(() => window.__tycoonCity!.usageElapsed())).toBe(0);

  // `lens=none` only to keep the first-run picker out of the one load that
  // runs without `?settle=1` — the same reason the weather's freeze spec does.
  await open(page, "?lens=none");
  await page.waitForTimeout(900);
  expect(await page.evaluate(() => window.__tycoonCity!.usageElapsed())).toBeGreaterThan(0.3);
});

test("an R refresh rebuilds the overlay from the new document", async ({ page }) => {
  await open(page, "?settle=1");
  expect(await page.evaluate(() => window.__tycoonCity!.usagePainted("quiet"))).toEqual(
    QUIET.slice().sort(),
  );

  // The catalog moves: the quiet pair got run, and the busiest model stopped.
  const doc = JSON.parse(await readFixture());
  for (const object of doc.objects) {
    if (QUIET.includes(object.key)) object.usage = { ...object.usage, runs_seen: 9, rate_per_day: 3 };
    if (object.key === "staging.stg_orders") object.usage = null;
  }
  await page.route("**/city.json*", (route) =>
    route.fulfill({ contentType: "application/json", body: JSON.stringify(doc) }),
  );
  await page.evaluate(() => window.__tycoonCity!.refresh());

  expect(await page.evaluate(() => window.__tycoonCity!.usagePainted("quiet"))).toEqual([]);
  expect(await page.evaluate(() => window.__tycoonCity!.usagePainted("busy"))).toEqual(
    ["mart.dim__customers", "mart.mart__revenue", "raw.orders", "staging.stg_customers"].sort(),
  );
  // The object that lost its measurement loses its beacon — it did not become
  // quiet, it became unknown.
  expect(await page.evaluate(() => window.__tycoonCity!.usagePainted("unrated"))).toEqual(UNRATED);
  expect(await page.evaluate(() => window.__tycoonCity!.usageInstanceCount())).toBe(5);
});
