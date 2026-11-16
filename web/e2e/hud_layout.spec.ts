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

test("a trackpad pinch over a HUD panel does not zoom the page off the window (gh-384)", async ({
  page,
}) => {
  // On macOS a trackpad pinch reaches the page as ctrl+wheel. The canvas
  // consumes it for the camera, but over a panel it zoomed the whole page,
  // pushing the panels and the header chips past both window edges.
  await page.setViewportSize({ width: 1280, height: 720 });
  await open(page, "?settle=1");
  await page.keyboard.press("p");
  const panel = (await page.locator("#problems").boundingBox())!;

  const cdp = await page.context().newCDPSession(page);
  await cdp.send("Input.synthesizePinchGesture", {
    x: panel.x + panel.width / 2,
    y: panel.y + panel.height / 2,
    scaleFactor: 1.6,
    gestureSourceType: "mouse",
  });
  await page.waitForTimeout(300);

  const viewport = await page.evaluate(() => ({
    scale: window.visualViewport!.scale,
    left: window.visualViewport!.offsetLeft,
  }));
  expect(viewport).toEqual({ scale: 1, left: 0 });
});

test("HUD panels stay inside a narrow window (gh-384)", async ({ page }) => {
  // 300 px is narrower than every panel's natural width (inspector 300,
  // problems 340, legend about 350, run panel 360), so each width cap is
  // what keeps its panel on screen with the same 12 px gutter it has at
  // full size. Without its cap the legend shrinks to the window but loses
  // the gutter on the left, so the gutter is what this checks.
  const width = 300;
  const gutter = 12;
  await page.setViewportSize({ width, height: 640 });
  await open(page, "?settle=1");
  const inside = async (id: string) => {
    const box = (await page.locator(id).boundingBox())!;
    expect(box.x, id).toBeGreaterThanOrEqual(gutter - 0.5);
    expect(box.x + box.width, id).toBeLessThanOrEqual(width - gutter + 0.5);
  };

  // The legend hides while the detail panel is open (gh-382), so measure it first.
  await expect(page.locator("#legend")).toBeVisible();
  await inside("#legend");

  await page.keyboard.press("p");
  await page.click("#replay-button");
  await page.evaluate(() => window.__tycoonCity!.select("staging.stg_customers"));
  await expect(page.locator("#run-panel")).toBeVisible();
  await expect(page.locator("#inspector dl")).toBeVisible();
  for (const id of ["#problems", "#run-panel", "#inspector"]) await inside(id);
});

test("a short window keeps the legend inside the map, scrolling its content (gh-384)", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 260 });
  await open(page, "?settle=1");
  const fit = await page.locator("#legend").evaluate((el) => {
    const box = el.getBoundingClientRect();
    const map = (el.offsetParent as HTMLElement).getBoundingClientRect();
    return { top: box.top - map.top, bottom: map.bottom - box.bottom, scrolls: el.scrollHeight > el.clientHeight };
  });
  expect(fit.top).toBeGreaterThanOrEqual(0);
  expect(fit.bottom).toBeGreaterThanOrEqual(0);
  expect(fit.scrolls).toBe(true);
});

test("touch pinch-zoom is off for the page (gh-384)", async ({ page }) => {
  await open(page, "?settle=1");
  const touch = await page.evaluate(() => getComputedStyle(document.body).touchAction);
  expect(touch).toBe("pan-x pan-y");
});

test("a name with no break point still wraps inside the panel, clear of the close button (gh-383)", async ({
  page,
}) => {
  // No underscore or dot means no <wbr>, so only the panel's
  // overflow-wrap fallback keeps these inside it.
  const doc = JSON.parse(await readFile(RICH, "utf8"));
  const revenue = doc.objects.find((o: { key: string }) => o.key === "mart.mart__revenue");
  revenue.name = "x".repeat(120);
  revenue.dbt.tests = [{ name: "y".repeat(120), column: "station_id", status: "pass" }];
  await page.route("**/city.json*", (route) => route.fulfill({ body: JSON.stringify(doc) }));
  await open(page, "?seed=7&lens=none");
  await page.evaluate(() => window.__tycoonCity!.select("mart.mart__revenue"));

  const panel = page.locator("#inspector");
  await expect(panel).toBeVisible();
  expect(await panel.evaluate((el) => el.scrollWidth - el.clientWidth)).toBe(0);
  expect((await wrappedLines(page, "#inspector h2")).length).toBeGreaterThan(1);
  expect((await wrappedLines(page, "#inspector ul.tests li >> nth=0 >> .ident")).length).toBeGreaterThan(1);

  // The title's first line must end before the close button starts.
  const titleRight = await page.locator("#inspector h2").evaluate((el) => {
    const range = document.createRange();
    range.selectNodeContents(el);
    const first = range.getClientRects()[0]!;
    return first.right;
  });
  const close = (await page.locator("#inspector .close").boundingBox())!;
  expect(titleRight).toBeLessThanOrEqual(close.x);
});
