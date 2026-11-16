/**
 * HUD layout: panels that share the screen must not stack translucent text on
 * top of each other or run past the window. These were all found on a real
 * 90-object catalog (nyc_data), where panels grow past what the demo fixture
 * produces, so each test forces the crowded case instead of hoping for it.
 */

import { expect, test } from "@playwright/test";
import { open } from "./helpers";

test("the legend steps aside while the detail panel is open (gh-382)", async ({ page }) => {
  // A short window plus the library panel (the tallest one the demo fixture
  // produces) is the crowded case from the issue: the two boxes really meet.
  await page.setViewportSize({ width: 1024, height: 560 });
  await open(page, "?settle=1");
  await expect(page.locator("#legend")).toBeVisible();
  const legend = (await page.locator("#legend").boundingBox())!;

  await page.evaluate(() => window.__tycoonCity!.select("__library__"));
  await expect(page.locator("#inspector")).toBeVisible();
  const panel = (await page.locator("#inspector").boundingBox())!;
  // Guard the fixture: if the panel no longer reaches the legend's spot, this
  // test stops proving anything about the overlap.
  expect(panel.y + panel.height).toBeGreaterThan(legend.y);
  expect(panel.x + panel.width).toBeGreaterThan(legend.x);
  // Both panels are translucent and anchored bottom-right / top-right, so any
  // shared area shows one panel's text through the other.
  await expect(page.locator("#legend")).toBeHidden();

  await page.evaluate(() => window.__tycoonCity!.select(""));
  await expect(page.locator("#inspector")).toBeHidden();
  await expect(page.locator("#legend")).toBeVisible();
});
