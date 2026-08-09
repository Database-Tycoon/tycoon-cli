/**
 * One `R`, one city.
 *
 * The mount/unmount cycle has exactly one owner: the HUD. Its `refresh()`
 * unmounts `cityRef.current`, mounts the replacement, re-points the picker and
 * restores the selection. Anything else that mounts a city on `R` adds a group
 * nobody holds a handle to — it can never be unmounted, so it stays on the
 * scene forever, drawn on top of the real city at identical coordinates.
 *
 * That failure is nearly invisible from the outside: the doubled city renders
 * in the same place, so every count hook, every screen-position hook and every
 * pixel probe keeps answering correctly. What it costs is z-fighting, doubled
 * draw work, a second network round-trip, and a leak that compounds with each
 * press — and `R` is a documented, user-facing key.
 *
 * So this spec asserts the two invariants a second owner cannot satisfy: the
 * scene graph is the same SIZE after a refresh as before it, and the catalog is
 * read exactly ONCE per refresh. Note that neither is met by adding a
 * compensating unmount to balance the books — the second fetch would remain.
 */

import { expect, test } from "@playwright/test";
import { open } from "./helpers";

const sceneSize = (page: import("@playwright/test").Page): Promise<number> =>
  page.evaluate(() => window.__tycoonCity!.sceneChildCount());

/** The catch arm in the HUD's refresh is the only writer of this text, and it
 * swallows whatever threw. A refresh that aborted early also leaves the scene
 * size alone, so every assertion below is worthless without this check. */
async function assertRefreshSucceeded(
  page: import("@playwright/test").Page,
): Promise<void> {
  expect(await page.locator("#status").innerText()).not.toContain("refresh failed");
}

test("one refresh leaves the scene graph the same size", async ({ page }) => {
  await open(page, "?settle=1");

  const before = await sceneSize(page);
  expect(before).toBeGreaterThan(0);

  await page.evaluate(() => window.__tycoonCity!.refresh());

  await assertRefreshSucceeded(page);
  expect(await sceneSize(page)).toBe(before);
});

test("a refresh reads city.json exactly once", async ({ page }) => {
  await open(page, "?settle=1");

  // Registered AFTER the boot load, so only the refresh's reads are counted.
  let reads = 0;
  await page.route("**/city.json*", async (route) => {
    reads += 1;
    await route.continue();
  });

  await page.evaluate(() => window.__tycoonCity!.refresh());

  await assertRefreshSucceeded(page);
  expect(reads).toBe(1);
});

test("repeated refreshes do not grow the scene graph", async ({ page }) => {
  // The leak compounds: one press is a defect, ten is a slideshow. Pinning the
  // size across repeats is what makes this a leak guard and not a fencepost.
  await open(page, "?settle=1");

  const before = await sceneSize(page);
  for (let i = 0; i < 3; i += 1) {
    await page.evaluate(() => window.__tycoonCity!.refresh());
    await assertRefreshSucceeded(page);
  }

  expect(await sceneSize(page)).toBe(before);
});
