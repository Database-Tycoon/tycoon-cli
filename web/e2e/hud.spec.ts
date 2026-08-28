/**
 * HUD: the health strip and its doors. The demo fixture is healthy, so the
 * strip's all-clear is asserted here; the chip-visit path is exercised via
 * the same visit() door the chips call, asserting the camera actually moved
 * and the selection landed — a count you cannot visit is trivia.
 */

import { expect, test } from "@playwright/test";
import { open } from "./helpers";

test("a healthy catalog shows the quiet all-clear, never an empty strip", async ({ page }) => {
  await open(page, "?settle=1");

  await expect(page.locator("#health")).toContainText("no findings");
  await expect(page.locator("#health [data-chip]")).toHaveCount(0);
});

test("visit() is a door: the camera flies and the selection lands", async ({ page }) => {
  await open(page, "?settle=1");

  const before = await page.evaluate(() => window.__tycoonCity!.cameraPose());
  await page.evaluate(() => window.__tycoonCity!.visit("raw.events"));
  await page.waitForTimeout(900); // the 0.6s glide plus settle

  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBe("raw.events");
  const after = await page.evaluate(() => window.__tycoonCity!.cameraPose());
  expect(after.target).not.toEqual(before.target); // it actually moved
  // And the flight ended framing the building: target near the lot.
  const lot = await page.evaluate(() => {
    const l = window.__tycoonCity!.doc.lots.find((l) => l.object_key === "raw.events")!;
    return { x: l.x + 0.5, y: l.y + 0.5 };
  });
  expect(Math.abs(after.target[0]! - lot.x)).toBeLessThan(0.5);
  expect(Math.abs(after.target[2]! - lot.y)).toBeLessThan(0.5);
});

test("P opens the problems panel; a healthy catalog says so", async ({ page }) => {
  await open(page, "?settle=1");

  await page.keyboard.press("p");
  await expect(page.locator("#problems")).toBeVisible();
  await expect(page.locator("#problems")).toContainText("nothing needs attention");
  await page.keyboard.press("Escape");
  await expect(page.locator("#problems")).toBeHidden();
});

test("slash opens search; typing narrows; Enter flies to the pick", async ({ page }) => {
  await open(page, "?settle=1");

  await page.keyboard.press("/");
  await expect(page.locator("#search")).toBeVisible();
  await page.keyboard.type("events");
  await expect(page.locator(".search-card li.active")).toContainText("raw.events");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(900);

  await expect(page.locator("#search")).toBeHidden();
  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBe("raw.events");
});

test("typing in search never triggers the R/F/P shortcuts", async ({ page }) => {
  await open(page, "?settle=1");

  await page.evaluate(() => {
    (window as unknown as { __marker: number }).__marker = 1;
  });
  await page.keyboard.press("/");
  await page.keyboard.type("raw performance"); // contains r, f, p, h
  await page.keyboard.press("Escape");

  const marker = await page.evaluate(() => (window as unknown as { __marker?: number }).__marker);
  expect(marker).toBe(1); // no refresh happened
  await expect(page.locator("#problems")).toBeHidden(); // no P toggle
});

test("the footer carries as-of, the keymap, and no crammed notes", async ({ page }) => {
  await open(page, "?settle=1");

  // This suite is served from a real `tycoon-city-export` in web/public, which
  // writes meta.json — so the honest reading here is the EXPORT's age, not
  // this page's fetch. `freshness.spec.ts` pins both verbs against fixtures.
  await expect(page.locator("#asof")).toContainText("exported");
  await page.click("#keys-button");
  await expect(page.locator("#keys-pop")).toContainText("problems panel");
  // demo has no degradation notes: the notes button must not exist at all.
  await expect(page.locator("#notes-button")).toBeHidden();
});

test("the problems panel carries the coverage gauges", async ({ page }) => {
  await open(page, "?settle=1");
  await page.keyboard.press("p");

  await expect(page.locator("#problems .coverage")).toContainText("columns documented");
  await expect(page.locator("#problems .coverage")).toContainText("objects tested");
});

test("the civic strip: library inventory and firehouse dispatch panels", async ({ page }) => {
  await open(page, "?settle=1");

  await page.evaluate(() => window.__tycoonCity!.select("__library__"));
  const library = await page.locator("#inspector").innerText();
  expect(library).toContain("public library");
  expect(library).toContain("columns documented");

  await page.evaluate(() => window.__tycoonCity!.select("__firehouse__"));
  const firehouse = await page.locator("#inspector").innerText();
  expect(firehouse.toLowerCase()).toContain("active fires (0)"); // demo has no failing tests
  expect(firehouse).toContain("not connected"); // the AI responder, named absence

  // No fires -> no trucks on the street.
  expect(await page.evaluate(() => window.__tycoonCity!.truckCount())).toBe(0);
});
