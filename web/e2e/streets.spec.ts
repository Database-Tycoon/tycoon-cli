/**
 * Streets v4: the street network has real geometry (`scene/streetscape.ts`).
 * Runs against the plain committed demo export in `web/public`, which since
 * the v4 planner landed carries REAL `street_features` (9: 6 aprons, 2
 * docks, 1 plaza). Pre-planner documents omit the field entirely; that
 * absence is still pinned below by serving a stripped copy — the contract's
 * default must keep old documents loading.
 *
 * The dressed endings themselves are pinned in `rich.spec.ts`.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect, test } from "@playwright/test";
import { countPixels, open, setPose } from "./helpers";

const ASPHALT = "#46464c"; // the atlas's road fill, unlit -> exact on screen
const PAINTED_CURB = "#8a8a92"; // the 1-px kerb line drawn INTO the road cells
const GRASS = "#3c8c46"; // one of the two atlas grass shades, unlit

test("a document with no street_features loads and dresses nothing", async ({ page }) => {
  // A pre-planner document: the committed export with the field stripped.
  const doc = JSON.parse(
    await readFile(path.resolve("public/city.json"), "utf8"),
  ) as Record<string, unknown>;
  delete doc.street_features;
  await page.route("**/city.json*", (route) =>
    route.fulfill({ contentType: "application/json", body: JSON.stringify(doc) }),
  );

  const errors = await open(page, "?settle=1");

  expect(await page.evaluate(() => "street_features" in (window.__tycoonCity!.doc as object))).toBe(true);
  expect(await page.evaluate(() => window.__tycoonCity!.doc.street_features)).toEqual([]);
  expect(await page.evaluate(() => window.__tycoonCity!.streetFeatureCount())).toBe(0);
  expect(errors).toEqual([]);
});

test("every closed road edge gets a raised curb", async ({ page }) => {
  await open(page, "?settle=1");

  // 56 closed road edges in the demo export (counted straight off the
  // decoded RLE). The two docks and the plaza re-pave tiles carrying 8 of
  // them, which lose their curb; each of the 6 aprons notches its faced edge
  // into two flanking stubs (+1 apiece). 56 - 8 + 6 = 54, derived
  // independently — a drift here means the mask shared with terrain.ts
  // moved, or a feature stopped owning its curb.
  expect(await page.evaluate(() => window.__tycoonCity!.curbCount())).toBe(54);
});

test("the raised curb covers the painted kerb line instead of doubling it", async ({ page }) => {
  await open(page, "?settle=1");
  await setPose(page, "top");

  // The road cells paint their own 1-px kerb (#8a8a92) so far views read as
  // streets. The geometry sits exactly on that band: if it were thinner or
  // offset, the paint would peek out beside the concrete and every street
  // would grow a double kerb line. Mutation-checked — deleting the curb mesh
  // takes this count from 0 to ~2300, so the assertion can fail.
  expect(await countPixels(page, PAINTED_CURB)).toBe(0);
  // Counterweight: the same counter must see the asphalt it sits on, or a
  // broken counter would satisfy the line above vacuously.
  expect(await countPixels(page, ASPHALT)).toBeGreaterThan(1000);
});

test("the streets survive a grazing camera — the skirt must not swallow the grid", async ({
  page,
}) => {
  await open(page, "?settle=1");
  // Eye height, a few tiles out, looking almost along the ground: the 3D curbs
  // made this view worth taking, and it exposed a defect that had nothing to
  // do with them — the grass skirt 0.02 below the grid won the depth fight at
  // grazing incidence and the ENTIRE road network rendered as grass. The skirt
  // now writes no depth (terrain.ts). 70k asphalt pixels here with that fix,
  // exactly 0 without it, so this assertion is the regression guard.
  await page.evaluate(() =>
    window.__tycoonCity!.setCameraPose({ position: [6, 2.2, 7.5], target: [10, 0, 4] }),
  );
  await page.waitForTimeout(400);

  expect(await countPixels(page, ASPHALT)).toBeGreaterThan(10_000);
  // Counterweight: the same counter must still see the ground beside the road.
  expect(await countPixels(page, GRASS)).toBeGreaterThan(1000);
});

test("?flat=1 has no streetscape at all — the pixel-test mode stays pristine", async ({
  page,
}) => {
  await open(page, "?flat=1&settle=1");

  expect(await page.evaluate(() => window.__tycoonCity!.curbCount())).toBe(0);
  expect(await page.evaluate(() => window.__tycoonCity!.streetFeatureCount())).toBe(0);
  // And the flat terrain never carried the atlas's painted kerb either.
  expect(await countPixels(page, PAINTED_CURB)).toBe(0);
});
