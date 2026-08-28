/**
 * The parked guest-flow experiment: OFF by default (observation platform, not
 * a game — no invented activity unless asked for), available under ?guests=1,
 * and never allowed to mutate a derived fact.
 */

import { expect, test } from "@playwright/test";
import { open } from "./helpers";

test("no guests and no score by default", async ({ page }) => {
  await open(page, "?seed=7&lens=none");
  await page.waitForTimeout(2500);

  expect(await page.evaluate(() => window.__tycoonCity!.guestCount())).toBe(0);
  await expect(page.locator("#score")).toHaveCount(0);
});

test("?guests=1 turns the flow on, and ticks never mutate derived state", async ({ page }) => {
  await open(page, "?guests=1&seed=7&lens=none");

  const before = await page.evaluate(() => JSON.stringify(window.__tycoonCity!.doc));
  await page.waitForTimeout(4000);
  const after = await page.evaluate(() => JSON.stringify(window.__tycoonCity!.doc));

  expect(await page.evaluate(() => window.__tycoonCity!.guestCount())).toBeGreaterThan(0);
  // Byte-identical: the flow layer owns its own fields only.
  expect(after).toBe(before);
});
