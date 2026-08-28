/**
 * The user-path suite: every assertion drives the real input path — mouse
 * events at projected screen coordinates — and reads back app state through
 * the __tycoonCity seam, never only DOM presence. The sky-click test is the
 * counterweight that keeps "clicking selects things" falsifiable.
 */

import { expect, test } from "@playwright/test";
import { open } from "./helpers";

test("clicking a building selects it and fills the inspector", async ({ page }) => {
  const errors = await open(page, "?settle=1");

  const pos = await page.evaluate(() => window.__tycoonCity!.screenPos("raw.orders"));
  expect(pos).not.toBeNull();
  await page.mouse.click(pos!.x, pos!.y);

  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBe("raw.orders");
  const inspector = await page.locator("#inspector").innerText();
  expect(inspector).toContain("50,000");
  expect(inspector).toContain("raw");
  expect(errors).toEqual([]);
});

test("lineage links in the inspector walk the graph", async ({ page }) => {
  await open(page, "?settle=1");

  const pos = await page.evaluate(() => window.__tycoonCity!.screenPos("raw.orders"));
  await page.mouse.click(pos!.x, pos!.y);
  // li[data-key]: the lineage LIST specifically -- the model graph's SVG
  // nodes are also [data-key] and now come first in the panel.
  await page.locator("#inspector li[data-key]").first().click();

  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBe("staging.stg_orders");
});

test("hovering a building shows its tooltip", async ({ page }) => {
  await open(page, "?settle=1");

  const pos = await page.evaluate(() => window.__tycoonCity!.screenPos("raw.events"));
  await page.mouse.move(pos!.x, pos!.y);
  await page.waitForTimeout(150);

  await expect(page.locator("#tooltip")).toBeVisible();
  await expect(page.locator("#tooltip")).toContainText("raw.events — 250,000 rows");
});

test("clicking the sky clears the selection", async ({ page }) => {
  await open(page, "?settle=1");

  const pos = await page.evaluate(() => window.__tycoonCity!.screenPos("raw.orders"));
  await page.mouse.click(pos!.x, pos!.y);
  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).not.toBeNull();

  await page.mouse.click(80, 120);
  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBeNull();
  await expect(page.locator("#inspector")).toBeHidden();
});

test("an orbit drag does not select what it ends over", async ({ page }) => {
  await open(page, "?settle=1");

  const pos = await page.evaluate(() => window.__tycoonCity!.screenPos("raw.orders"));
  // Drag that releases over the building: a click would select it.
  await page.mouse.move(pos!.x - 120, pos!.y - 60);
  await page.mouse.down();
  await page.mouse.move(pos!.x, pos!.y, { steps: 8 });
  await page.mouse.up();

  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBeNull();
});

test("the stats modal lists the catalog and its rows select on the map", async ({ page }) => {
  await open(page, "?settle=1");

  await page.click("#stats-button");
  await expect(page.locator("#stats")).toBeVisible();
  await expect(page.locator("#stats h2")).toContainText("demo — 7 objects");

  await page.locator('#stats tr[data-key="marts.fct_revenue"]').click();
  await expect(page.locator("#stats")).toBeHidden();
  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBe("marts.fct_revenue");
});

test("the stats button works while an inspector is open", async ({ page }) => {
  // Regression: the inspector, parented to <body>, anchored to the viewport
  // and sat over the header's Stats button — unclickable exactly when a
  // building was selected. Only this ordering (select first, then Stats)
  // exercises it; the plain stats test starts from a fresh page.
  await open(page, "?settle=1");

  const pos = await page.evaluate(() => window.__tycoonCity!.screenPos("raw.orders"));
  await page.mouse.click(pos!.x, pos!.y);
  await expect(page.locator("#inspector")).toBeVisible();

  await page.click("#stats-button", { timeout: 3000 });
  await expect(page.locator("#stats")).toBeVisible();
});

test("no run history means a STILL city — traffic is real movement only", async ({ page }) => {
  // demo.duckdb is a plain file with no run history: every last_build_age_s
  // is null, so nothing may move. Movement without data movement is theater.
  await open(page, "?seed=42&lens=none");
  await page.waitForTimeout(2500);

  expect(await page.evaluate(() => window.__tycoonCity!.vehicleCount())).toBe(0);
});

test("?ambient=1 restores the decorative flow for demos", async ({ page }) => {
  await open(page, "?seed=42&ambient=1&lens=none");
  await page.waitForTimeout(2500);

  const count = await page.evaluate(() => window.__tycoonCity!.vehicleCount());
  expect(count).toBeGreaterThan(0);
});

test("the plant opens the database inspector", async ({ page }) => {
  await open(page, "?settle=1");

  const pos = await page.evaluate(() => window.__tycoonCity!.screenPos("__plant__"));
  await page.mouse.click(pos!.x, pos!.y);

  const inspector = await page.locator("#inspector").innerText();
  expect(inspector).toContain("demo");
  expect(inspector).toContain("301,200");
});

test("with no run history the replay control stays and NAMES the absence", async ({ page }) => {
  // demo.duckdb is a plain file with no `.tycoon/metadata.duckdb` behind it,
  // so its exported `runs.json` is an empty list plus the loader's reason.
  // The old single button hid itself here; the panel must not. A control that
  // disappears is indistinguishable from a broken build, which is exactly why
  // `/runs.json` is answered 200-with-notes instead of 404.
  await open(page, "?settle=1");
  await expect(page.locator("#replay-button")).toBeVisible();

  await page.locator("#replay-button").click();
  const panel = page.locator("#run-panel"); // the index fetch resolves async
  await expect(panel).toContainText("run replay unavailable");
  await expect(panel).toContainText("no dbt run history for this catalog");
});

test("R refreshes in place: no navigation, camera and selection survive", async ({ page }) => {
  await open(page, "?settle=1");

  // A window-scope marker: any navigation (the old reload-based R) wipes it.
  await page.evaluate(() => {
    (window as unknown as { __marker: number }).__marker = 1;
  });

  const pos = await page.evaluate(() => window.__tycoonCity!.screenPos("raw.orders"));
  await page.mouse.click(pos!.x, pos!.y);
  const poseBefore = await page.evaluate(() => window.__tycoonCity!.cameraPose());

  await page.keyboard.press("r");
  await page.waitForTimeout(800); // refetch + remount

  const marker = await page.evaluate(
    () => (window as unknown as { __marker?: number }).__marker,
  );
  expect(marker).toBe(1); // same page, no reload
  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBe("raw.orders");
  const poseAfter = await page.evaluate(() => window.__tycoonCity!.cameraPose());
  expect(poseAfter).toEqual(poseBefore);
  // And the scene still resolves clicks after the remount (new targets wired).
  await page.mouse.click(80, 120);
  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBeNull();
  const pos2 = await page.evaluate(() => window.__tycoonCity!.screenPos("raw.events"));
  await page.mouse.click(pos2!.x, pos2!.y);
  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBe("raw.events");
});

test("no usable history means no road-load overlay", async ({ page }) => {
  // demo.duckdb has no run history at all: every edge's daily_load_s is
  // null, so not one road tile may claim an expected load.
  await open(page, "?settle=1");

  expect(await page.evaluate(() => window.__tycoonCity!.flowTileCount())).toBe(0);
});

test("nothing burns in a catalog with no failing tests", async ({ page }) => {
  // demo.duckdb has no test verdicts at all: fire is a fact about a failing
  // test, never ambience. The positive case lives in the rich fixture
  // (render-and-look): mart__revenue's failing not_null burns.
  await open(page, "?settle=1");

  expect(await page.evaluate(() => window.__tycoonCity!.fireCount())).toBe(0);
});
