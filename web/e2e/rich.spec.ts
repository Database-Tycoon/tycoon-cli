/**
 * The POSITIVE-path suite. The main suite runs against the plain demo
 * fixture, where fires, trucks, road heat and traffic are all absent by
 * honest design — so until now every rich behaviour was verified only by
 * render-and-look. This file serves a COMMITTED demo-tycoon export
 * (fixtures/rich.city.json — ages frozen at generation time, so the facts
 * inside never move) via route interception, and pins the features ON.
 *
 * If the contract changes shape, regenerate the fixture deliberately:
 *   uv run python scripts/make_demo_tycoon.py
 *   uv run tycoon-city-export demo-tycoon /tmp/rich-export
 *   cp /tmp/rich-export/city.json web/e2e/fixtures/rich.city.json
 * and re-read these assertions against its printed facts.
 *
 * STREET FEATURES are REAL planner output since the v4 integration
 * (2026-08-05): 12 features — 9 aprons, 1 dock (raw.customers' court),
 * 2 plazas (incl. the 1x2 pad fronting the 2x2 raw.orders). The counts
 * asserted below were re-derived independently from the document (closed
 * edges off the RLE, minus pad-tile edges, plus apron notches), per this
 * header's original instruction — never edited to match the runtime.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect, test } from "@playwright/test";
import { open } from "./helpers";

// Resolved from the web/ package root (Playwright's cwd) — __dirname does
// not exist under ESM transpilation.
const FIXTURE = path.resolve("e2e/fixtures/rich.city.json");

/** The fixture's bytes, for the one test that serves a modified copy. */
const readFixture = (): Promise<string> => readFile(FIXTURE, "utf8");

test.beforeEach(async ({ page }) => {
  await page.route("**/city.json*", (route) => route.fulfill({ path: FIXTURE }));
});

test("a failing test burns, and the firehouse dispatches exactly one truck", async ({ page }) => {
  await open(page, "?seed=7&lens=none");

  expect(await page.evaluate(() => window.__tycoonCity!.fireCount())).toBe(1);
  expect(await page.evaluate(() => window.__tycoonCity!.truckCount())).toBe(1);

  await page.evaluate(() => window.__tycoonCity!.select("__firehouse__"));
  const firehouse = (await page.locator("#inspector").innerText()).toLowerCase();
  expect(firehouse).toContain("active fires (1)");
  expect(firehouse).toContain("mart.mart__revenue");
});

test("fresh builds put real vehicles on the streets", async ({ page }) => {
  await open(page, "?seed=7&lens=none");
  await page.waitForTimeout(3000); // ~30 ticks of spawn chances on 4 fresh edges

  expect(await page.evaluate(() => window.__tycoonCity!.vehicleCount())).toBeGreaterThan(0);
});

test("run history lights the road-load overlay, and T toggles it", async ({ page }) => {
  await open(page, "?settle=1");

  const lit = await page.evaluate(() => window.__tycoonCity!.flowTileCount());
  expect(lit).toBeGreaterThan(0);
  await page.keyboard.press("t");
  // Toggling hides the layer but never destroys the measured tiles.
  expect(await page.evaluate(() => window.__tycoonCity!.flowTileCount())).toBe(lit);
});

test("the health strip carries the rich fixture's findings as doors", async ({ page }) => {
  await open(page, "?settle=1");

  const chips = page.locator("#health [data-chip]");
  expect(await chips.count()).toBeGreaterThanOrEqual(4); // fail, error, late, warn
  await page.locator('#health [data-chip="tests-fail"]').click();
  await page.waitForTimeout(900); // the glide
  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBe("mart.mart__revenue");
});

test("skybridges rise for a selected building with traced columns", async ({ page }) => {
  await open(page, "?settle=1");

  await page.evaluate(() => window.__tycoonCity!.select("mart.mart__revenue"));
  expect(await page.evaluate(() => window.__tycoonCity!.skybridgeCount())).toBeGreaterThan(0);
});

test("the dressed endings render: an apron, a dock and a plaza", async ({ page }) => {
  const errors = await open(page, "?settle=1");

  expect(await page.evaluate(() => window.__tycoonCity!.doc.street_features.length)).toBe(12);
  // Counted off the live primary meshes (the ramp, the court, the pad), so a
  // feature that validated but never reached the scene reads as missing.
  expect(await page.evaluate(() => window.__tycoonCity!.streetFeatureCount())).toBe(12);
  expect(errors).toEqual([]);
});

test("a dressed ending owns its curb: the apron notches it, the pads replace it", async ({
  page,
}) => {
  await open(page, "?settle=1");

  // 72 closed road edges in the regenerated fixture. The dock and the two
  // plazas re-pave tiles carrying 10 of those edges, which lose their curb;
  // each of the 9 aprons NOTCHES its faced edge into two flanking stubs
  // (+1 apiece). 72 - 10 + 9 = 71, derived independently off the RLE.
  expect(await page.evaluate(() => window.__tycoonCity!.curbCount())).toBe(71);
});

test("an unknown street-feature kind is a no-op, not a load failure", async ({ page }) => {
  // Forward compatibility, deliberately exercised: a NEWER planner emitting a
  // kind this renderer has never heard of must draw nothing and break
  // nothing — never fail validation and blank the city.
  const doc = JSON.parse(await readFixture());
  doc.street_features.push({ kind: "bulb", x: 18, y: 9, facing: "e", w: 1, h: 1 });
  await page.route("**/city.json*", (route) =>
    route.fulfill({ contentType: "application/json", body: JSON.stringify(doc) }),
  );

  const errors = await open(page, "?settle=1");

  expect(await page.evaluate(() => window.__tycoonCity!.doc.street_features.length)).toBe(13);
  expect(await page.evaluate(() => window.__tycoonCity!.streetFeatureCount())).toBe(12);
  // It claims no curb either: the count is the unmodified fixture's.
  expect(await page.evaluate(() => window.__tycoonCity!.curbCount())).toBe(71);
  expect(errors).toEqual([]);
});

test("a stale source wears down, and a contractor van answers the call", async ({ page }) => {
  await open(page, "?settle=1");

  // raw.customers violates its freshness SLA (error) in the frozen fixture.
  expect(await page.evaluate(() => window.__tycoonCity!.wearCount())).toBe(1);
  expect(await page.evaluate(() => window.__tycoonCity!.vanCount())).toBe(1);

  await page.evaluate(() => window.__tycoonCity!.select("__firehouse__"));
  const panel = (await page.locator("#inspector").innerText()).toLowerCase();
  expect(panel).toContain("repair calls (1)");
  expect(panel).toContain("raw.customers");
});

// ---------------------------------------------------------------------------
// WEATHER — fog over the districts a late source FEEDS
// ---------------------------------------------------------------------------
//
// Hand-counted from the fixture: raw.customers violates its freshness SLA
// (error) and feeds staging.stg_customers, which feeds four mart models. So
// `staging` and `mart` are fogged, `raw` — which HOLDS the late source — is
// clear, and `scratch` (no lineage at all) gets no cell. 2 fogged districts x
// 4 fog layers = 8 meshes.

test("fog covers the districts the late source feeds, and NOT its own", async ({ page }) => {
  await open(page, "?settle=1");

  // The document's own claim, so a renderer bug and a fixture drift stay
  // distinguishable.
  const cells = await page.evaluate(() => window.__tycoonCity!.doc.weather!.cells);
  expect(cells.map((c) => `${c.schema}:${c.condition}`).sort()).toEqual([
    "mart:fog",
    "raw:clear",
    "staging:fog",
  ]);

  // What actually reached the scene.
  expect(await page.evaluate(() => window.__tycoonCity!.weatherSchemas())).toEqual(["mart", "staging"]);
  expect(await page.evaluate(() => window.__tycoonCity!.weatherMeshCount())).toBe(8);
});

test("a district with no judged source upstream stays unpainted", async ({ page }) => {
  await open(page, "?settle=1");

  // `scratch` has no lineage, so nothing judged reaches it and the emitter
  // sends no cell. The renderer must not fill that in — with fog OR with the
  // comforting fair weather that would be clear-because-unknown.
  const schemas = await page.evaluate(() => window.__tycoonCity!.doc.districts.map((d) => d.schema));
  expect(schemas).toContain("scratch");
  const cells = await page.evaluate(() => window.__tycoonCity!.doc.weather!.cells.map((c) => c.schema));
  expect(cells).not.toContain("scratch");
  expect(await page.evaluate(() => window.__tycoonCity!.weatherSchemas())).not.toContain("scratch");
});

test("fog does not put out a fire", async ({ page }) => {
  await open(page, "?settle=1");

  // The burning building stands INSIDE a fogged district — otherwise this
  // says nothing about the two layers interacting.
  const burning = await page.evaluate(
    () => window.__tycoonCity!.doc.lots.find((l) => l.test_status === "fail")!.object_key,
  );
  expect(burning).toBe("mart.mart__revenue");
  expect(await page.evaluate(() => window.__tycoonCity!.weatherSchemas())).toContain("mart");

  // The fire survives the fog, and the fog stays strictly below the lowest
  // roof this renderer can build — so no flame is ever inside the volume.
  expect(await page.evaluate(() => window.__tycoonCity!.fireCount())).toBe(1);
});

test("W toggles the weather without destroying it", async ({ page }) => {
  await open(page, "?settle=1");

  const meshes = await page.evaluate(() => window.__tycoonCity!.weatherMeshCount());
  expect(meshes).toBe(8);
  await page.keyboard.press("w");
  // Hiding a layer never discards the measured facts behind it.
  expect(await page.evaluate(() => window.__tycoonCity!.weatherMeshCount())).toBe(meshes);
});

test("the fog is frozen under ?settle=1 and drifts without it", async ({ page }) => {
  await open(page, "?settle=1");
  await page.waitForTimeout(900);
  expect(await page.evaluate(() => window.__tycoonCity!.weatherElapsed())).toBe(0);

  // `lens=none`, not because the fog cares, but because this is the one spec
  // that loads WITHOUT `?settle=1` — the only state where the first-run lens
  // picker would open over the city. Weakening the picker's trigger to keep a
  // spec quiet would be testing the wrong thing.
  await open(page, "?lens=none");
  await page.waitForTimeout(900);
  expect(await page.evaluate(() => window.__tycoonCity!.weatherElapsed())).toBeGreaterThan(0.3);
});

test("no cells means no weather, named — not fair weather", async ({ page }) => {
  // The state `loader` calls "no source freshness snapshot": sources exist,
  // the command never ran. All-clear here would be clear-because-unknown
  // rendered as clear-because-fine.
  const doc = JSON.parse(await readFixture());
  doc.weather = { cells: [], note: "no source freshness verdicts — weather unknown" };
  await page.route("**/city.json*", (route) =>
    route.fulfill({ contentType: "application/json", body: JSON.stringify(doc) }),
  );

  const errors = await open(page, "?settle=1");

  expect(await page.evaluate(() => window.__tycoonCity!.weatherMeshCount())).toBe(0);
  // The absence is NAMED, not silent: the legend carries the note.
  const legend = await page.locator("#legend").innerText();
  expect(legend.toLowerCase()).toContain("weather: none to show");
  expect(await page.locator("#legend").innerHTML()).toContain("weather unknown");
  expect(errors).toEqual([]);
});

test("an unknown weather condition is a no-op, not a load failure", async ({ page }) => {
  // Forward compatibility, same rule as the street features: a newer emitter
  // inventing a condition must draw nothing and break nothing.
  const doc = JSON.parse(await readFixture());
  doc.weather.cells.push({
    schema: "scratch",
    condition: "hail",
    worst_source: "raw.customers",
    verdict: "error",
    hops: 1,
  });
  await page.route("**/city.json*", (route) =>
    route.fulfill({ contentType: "application/json", body: JSON.stringify(doc) }),
  );

  const errors = await open(page, "?settle=1");

  expect(await page.evaluate(() => window.__tycoonCity!.doc.weather!.cells.length)).toBe(4);
  expect(await page.evaluate(() => window.__tycoonCity!.weatherMeshCount())).toBe(8);
  expect(await page.evaluate(() => window.__tycoonCity!.weatherSchemas())).toEqual(["mart", "staging"]);
  expect(errors).toEqual([]);
});
