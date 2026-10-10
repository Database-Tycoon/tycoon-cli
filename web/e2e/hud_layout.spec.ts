/**
 * HUD layout: panels that share the screen must not stack translucent text on
 * top of each other or run past the window. These were all found on a real
 * 90-object catalog (nyc_data), where panels grow past what the demo fixture
 * produces, so each test forces the crowded case instead of hoping for it.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import { open } from "./helpers";

const RICH = path.resolve("e2e/fixtures/rich.city.json");

/** The rendered text of `selector`, split where the browser wrapped it. */
async function wrappedLines(page: Page, selector: string): Promise<string[]> {
  return page.locator(selector).evaluate((el) => {
    const lines: { top: number; text: string }[] = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const text = node.textContent ?? "";
      for (let i = 0; i < text.length; i++) {
        const range = document.createRange();
        range.setStart(node, i);
        range.setEnd(node, i + 1);
        const rect = range.getBoundingClientRect();
        if (rect.width === 0) continue;
        const last = lines[lines.length - 1];
        if (last && Math.abs(last.top - rect.top) < rect.height / 2) last.text += text[i];
        else lines.push({ top: rect.top, text: text[i]! });
      }
    }
    return lines.map((line) => line.text);
  });
}

test("the legend steps aside while the detail panel is open (gh-382)", async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 700 });
  await open(page, "?settle=1");
  await expect(page.locator("#legend")).toBeVisible();

  await page.evaluate(() => window.__tycoonCity!.select("staging.stg_customers"));
  await expect(page.locator("#inspector")).toBeVisible();
  // Both panels are translucent and anchored bottom-right / top-right, so any
  // shared area shows one panel's text through the other.
  await expect(page.locator("#legend")).toBeHidden();

  await page.evaluate(() => window.__tycoonCity!.select(""));
  await expect(page.locator("#inspector")).toBeHidden();
  await expect(page.locator("#legend")).toBeVisible();
});

test("long model and test names wrap at underscores, never mid-word or off the edge (gh-383)", async ({
  page,
}) => {
  const doc = JSON.parse(await readFile(RICH, "utf8"));
  const revenue = doc.objects.find((o: { key: string }) => o.key === "mart.mart__revenue");
  revenue.name = "stg_citibike__station_information";
  revenue.dbt.tests = [
    "not_null_stg_citibike__station_information_station_id",
    "unique_stg_citibike__station_information_station_id",
    "relationships_stg_citibike__station_information_region_id__region_id__ref_stg_citibike__system_regions_",
  ].map((name) => ({ name, column: "station_id", status: "pass" }));
  await page.route("**/city.json*", (route) => route.fulfill({ body: JSON.stringify(doc) }));
  await open(page, "?seed=7&lens=none");
  await page.evaluate(() => window.__tycoonCity!.select("mart.mart__revenue"));

  const title = await wrappedLines(page, "#inspector h2");
  expect(title.length).toBeGreaterThan(1);
  for (const line of title.slice(0, -1)) expect(line).toMatch(/_$/);

  const panel = page.locator("#inspector");
  const overflow = await panel.evaluate((el) => el.scrollWidth - el.clientWidth);
  expect(overflow).toBe(0);
  const right = await panel.evaluate((el) => el.getBoundingClientRect().right);
  const tests = page.locator("#inspector ul.tests li");
  await expect(tests).toHaveCount(3);
  for (let i = 0; i < 3; i++) {
    const box = (await tests.nth(i).boundingBox())!;
    expect(box.x + box.width).toBeLessThanOrEqual(right);
    const name = await wrappedLines(page, `#inspector ul.tests li >> nth=${i} >> .ident`);
    for (const line of name.slice(0, -1)) expect(line).toMatch(/_$/);
  }
});
