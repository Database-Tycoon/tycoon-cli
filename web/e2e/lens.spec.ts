/**
 * ROLE LENSES — and the one guard that makes the whole feature honest.
 *
 * THE WRONG-AXIS TRAP THIS FILE IS BUILT AGAINST: `expect(chip).toBeVisible()`
 * passes under EVERY lens, including a lens that does nothing at all. It is
 * worthless here. Only two kinds of assertion can fail for the right reason,
 * and this file contains only those two:
 *
 *   1. ORDERING — `indexOf(a) < indexOf(b)` on what the DOM actually rendered.
 *   2. CROSS-LENS EQUALITY — the same document under two lenses must show
 *      byte-identical counts. This is the anti-invention guard: it is what
 *      pins "a lens re-weights presentation and never changes arithmetic",
 *      and the mutation that kills it is a lens that filters a chip out of
 *      the aggregation (logged in docs/log.md, 2026-08-06).
 *
 * Served over the committed `fixtures/rich.city.json` — the plain demo is
 * healthy, and a strip with no chips cannot be reordered.
 *
 * Hand-counted off that fixture, which is why the ordering assertions below
 * can name specific chips:
 *   tests-fail  1  mart.mart__revenue
 *   build-error 1  mart.mart__broken
 *   source-late 1  raw.customers (freshness error)
 *   tests-warn  1  staging.stg_orders
 *   stale       1  mart.mart__forgotten (21d)
 *   drift       1  staging.stg_customers (2d)
 */

import { expect, test, type Page } from "@playwright/test";
import { open } from "./helpers";

const FIXTURE = "e2e/fixtures/rich.city.json";

test.beforeEach(async ({ page }) => {
  await page.route("**/city.json*", (route) => route.fulfill({ path: FIXTURE }));
});

/** The chip ids the strip rendered, in DOM order. */
const chipOrder = (page: Page): Promise<string[]> =>
  page.$$eval("#health [data-chip]", (els) =>
    els.map((el) => (el as HTMLElement).dataset.chip!),
  );

/** The chip TEXTS, in DOM order — the counts as a viewer reads them. */
const chipTexts = (page: Page): Promise<string[]> =>
  page.$$eval("#health [data-chip]", (els) => els.map((el) => el.textContent!));

const gaugeOrder = (page: Page): Promise<string[]> =>
  page.$$eval("#problems [data-gauge]", (els) =>
    els.map((el) => (el as HTMLElement).dataset.gauge!),
  );

const gaugeTexts = (page: Page): Promise<string[]> =>
  page.$$eval("#problems [data-gauge]", (els) => els.map((el) => el.textContent!));

const problemKeys = (page: Page): Promise<string[]> =>
  page.$$eval("#problems li[data-key]", (els) =>
    els.map((el) => (el as HTMLElement).dataset.key!),
  );

// ---------------------------------------------------------------------------
// THE ANTI-INVENTION GUARD
// ---------------------------------------------------------------------------

test("two lenses on one document show byte-identical counts", async ({ page }) => {
  await open(page, "?settle=1&lens=data-engineer");
  const engineerTexts = await chipTexts(page);
  const engineerOrder = await chipOrder(page);

  // Same page, same document, same fetch — only the lens moves. A reload
  // would let a fixture difference masquerade as lens neutrality.
  await page.evaluate(() => window.__tycoonCity!.setLens("on-call"));
  const oncallTexts = await chipTexts(page);
  const oncallOrder = await chipOrder(page);

  // 1. The COUNTS are identical, byte for byte, once order is set aside.
  expect([...oncallTexts].sort()).toEqual([...engineerTexts].sort());
  // 2. And the set of chips is identical too: a lens may not drop a finding.
  expect([...oncallOrder].sort()).toEqual([...engineerOrder].sort());
  // 3. But the ORDER really did change — otherwise (1) and (2) would pass on
  //    a lens implementation that does nothing whatsoever.
  expect(oncallOrder).not.toEqual(engineerOrder);
});

test("every lens flags the same objects and shows the same gauge values", async ({ page }) => {
  // This lens OPENS the problems panel itself; pressing `P` here would close
  // it, and a hidden panel keeps its last HTML — every lens would then read
  // identical for the dullest possible reason.
  await open(page, "?settle=1&lens=data-engineer");
  await expect(page.locator("#problems")).toBeVisible();

  const seen: Record<string, { keys: string[]; gauges: string[]; order: string[] }> = {};
  for (const id of ["data-engineer", "analytics-engineer", "on-call", "data-lead"] as const) {
    await page.evaluate((lens) => window.__tycoonCity!.setLens(lens), id);
    seen[id] = {
      keys: [...(await problemKeys(page))].sort(),
      gauges: [...(await gaugeTexts(page))].sort(),
      order: await problemKeys(page),
    };
  }

  const base = seen["data-engineer"]!;
  for (const id of ["analytics-engineer", "on-call", "data-lead"] as const) {
    // The SET of flagged objects is identical under every lens…
    expect(seen[id]!.keys).toEqual(base.keys);
    // …and so is every gauge VALUE, string for string.
    expect(seen[id]!.gauges).toEqual(base.gauges);
  }
  // …while at least one lens really does triage them differently.
  expect(seen["data-lead"]!.order).not.toEqual(base.order);
});

// ---------------------------------------------------------------------------
// ORDERING — the only other axis that can fail for the right reason
// ---------------------------------------------------------------------------

test("the data-engineer lens leads with build errors, then the oldest build", async ({ page }) => {
  await open(page, "?settle=1&lens=data-engineer");

  const order = await chipOrder(page);
  expect(order.indexOf("build-error")).toBeLessThan(order.indexOf("tests-fail"));
  expect(order.indexOf("stale")).toBeLessThan(order.indexOf("tests-fail"));
  expect(order.indexOf("build-error")).toBeLessThan(order.indexOf("stale"));
  // A chip this lens never names still renders — after the ones it does.
  expect(order).toContain("source-late");
});

test("the on-call lens leads with fires and late sources, not with staleness", async ({ page }) => {
  await open(page, "?settle=1&lens=on-call");

  const order = await chipOrder(page);
  expect(order.indexOf("tests-fail")).toBeLessThan(order.indexOf("stale"));
  expect(order.indexOf("source-late")).toBeLessThan(order.indexOf("stale"));
  expect(order.indexOf("source-late")).toBeLessThan(order.indexOf("build-error"));
});

test("two lenses disagree about which chip comes first", async ({ page }) => {
  await open(page, "?settle=1&lens=data-engineer");
  expect((await chipOrder(page))[0]).toBe("build-error");

  await page.evaluate(() => window.__tycoonCity!.setLens("analytics-engineer"));
  expect((await chipOrder(page))[0]).toBe("tests-fail");

  await page.evaluate(() => window.__tycoonCity!.setLens("data-lead"));
  expect((await chipOrder(page))[0]).toBe("stale");
});

test("the neutral lens keeps document order and emphasises nothing", async ({ page }) => {
  await open(page, "?settle=1&lens=none");

  expect(await chipOrder(page)).toEqual([
    "tests-fail",
    "build-error",
    "source-late",
    "tests-warn",
    "stale",
    "drift",
  ]);
  expect(await page.locator("#health .chip-h.lead").count()).toBe(0);
});

test("a lens marks exactly its two leading chips", async ({ page }) => {
  await open(page, "?settle=1&lens=on-call");

  const lead = await page.$$eval("#health .chip-h.lead", (els) =>
    els.map((el) => (el as HTMLElement).dataset.chip!),
  );
  expect(lead).toEqual(["tests-fail", "source-late"]);
});

test("the problems panel triages in the lens's order, not one fixed order", async ({ page }) => {
  await open(page, "?settle=1&lens=data-engineer");
  await expect(page.locator("#problems")).toBeVisible();

  // The engineer's list opens on the build error, whatever its severity rank.
  const engineer = await problemKeys(page);
  expect(engineer[0]).toBe("mart.mart__broken");

  // On-call sorts worst-first and, among equals, most RECENTLY built first —
  // so the two severity-4 rows swap round.
  await page.evaluate(() => window.__tycoonCity!.setLens("on-call"));
  const oncall = await problemKeys(page);
  expect(oncall.indexOf("raw.customers")).toBeLessThan(oncall.indexOf("mart.mart__forgotten"));
  expect(oncall).not.toEqual(engineer);

  // The lead reads by district: every `mart.` row precedes every `raw.` row.
  await page.evaluate(() => window.__tycoonCity!.setLens("data-lead"));
  const lead = await problemKeys(page);
  const lastMart = lead.map((k) => k.startsWith("mart.")).lastIndexOf(true);
  const firstRaw = lead.findIndex((k) => k.startsWith("raw."));
  expect(lastMart).toBeLessThan(firstRaw);
});

test("gauges lead by lens, and the ones it does not name still render", async ({ page }) => {
  await open(page, "?settle=1&lens=analytics-engineer");
  await expect(page.locator("#problems")).toBeVisible();

  expect((await gaugeOrder(page)).slice(0, 2)).toEqual(["documented", "tested"]);
  expect(await gaugeOrder(page)).toContain("budget");

  await page.evaluate(() => window.__tycoonCity!.setLens("data-lead"));
  expect((await gaugeOrder(page)).slice(0, 3)).toEqual(["budget", "quiet", "documented"]);
  // Same five gauges, different order — never a different set.
  expect([...(await gaugeOrder(page))].sort()).toEqual([
    "budget",
    "documented",
    "quiet",
    "sla",
    "tested",
  ]);
});

// ---------------------------------------------------------------------------
// DEFAULTS: overlays and the opening panel
// ---------------------------------------------------------------------------

test("a lens turns on its own overlays and only its own", async ({ page }) => {
  await open(page, "?settle=1&lens=on-call");

  const weatherOn = () => page.evaluate(() => window.__tycoonCity!.weatherVisible());
  const flowOn = () => page.evaluate(() => window.__tycoonCity!.flowVisible());
  expect(await weatherOn()).toBe(true);
  expect(await flowOn()).toBe(false);

  await page.evaluate(() => window.__tycoonCity!.setLens("data-engineer"));
  expect(await weatherOn()).toBe(false);
  expect(await flowOn()).toBe(true);

  // Hiding a layer never destroys the measured facts behind it.
  expect(await page.evaluate(() => window.__tycoonCity!.weatherMeshCount())).toBe(8);
});

test("the data-lead lens raises flow AND usage — exclusive is not single-valued", async ({
  page,
}) => {
  // The lead's gauges lead with `budget, quiet, documented`. `quiet` without
  // the usage overlay is a number in a panel with no map treatment behind it,
  // and the quiet marker is exactly that number made spatial.
  await open(page, "?settle=1&lens=data-lead");

  expect(await page.evaluate(() => window.__tycoonCity!.flowVisible())).toBe(true);
  expect(await page.evaluate(() => window.__tycoonCity!.usageVisible())).toBe(true);
  // Still exclusive: an overlay this lens does not name is off.
  expect(await page.evaluate(() => window.__tycoonCity!.weatherVisible())).toBe(false);

  // The control: another lens does NOT carry both, so this cannot be passing
  // on an implementation that simply leaves every overlay on.
  await page.evaluate(() => window.__tycoonCity!.setLens("data-engineer"));
  expect(await page.evaluate(() => window.__tycoonCity!.flowVisible())).toBe(true);
  expect(await page.evaluate(() => window.__tycoonCity!.usageVisible())).toBe(false);
});

test("the lens opens its default panel; the neutral lens opens none", async ({ page }) => {
  await open(page, "?settle=1&lens=on-call");
  await expect(page.locator("#problems")).toBeVisible();

  await open(page, "?settle=1&lens=data-lead");
  await expect(page.locator("#problems")).toBeHidden();
  await expect(page.locator("#inspector")).toContainText("public library");

  await open(page, "?settle=1&lens=none");
  await expect(page.locator("#problems")).toBeHidden();
  await expect(page.locator("#inspector")).toBeHidden();
});

// ---------------------------------------------------------------------------
// RESOLUTION AND PERSISTENCE
// ---------------------------------------------------------------------------

test("?lens= wins and does NOT persist: a shared link cannot rewrite a preference", async ({
  page,
}) => {
  await open(page, "?settle=1&lens=none");
  await page.evaluate(() => localStorage.setItem("tycoon-city.lens", "data-lead"));

  // Someone sends you an on-call link.
  await open(page, "?settle=1&lens=on-call");
  expect(await page.evaluate(() => window.__tycoonCity!.lensId())).toBe("on-call");
  expect(await page.evaluate(() => localStorage.getItem("tycoon-city.lens"))).toBe("data-lead");

  // Your own preference is still yours when you open it plain.
  await open(page, "?settle=1");
  expect(await page.evaluate(() => window.__tycoonCity!.lensId())).toBe("data-lead");
});

test("an unknown stored lens falls back to neutral and clears the key", async ({ page }) => {
  await open(page, "?settle=1&lens=none");
  await page.evaluate(() => localStorage.setItem("tycoon-city.lens", "wizard"));

  await open(page, "?settle=1");
  expect(await page.evaluate(() => window.__tycoonCity!.lensId())).toBe("none");
  expect(await page.evaluate(() => localStorage.getItem("tycoon-city.lens"))).toBe(null);
});

test("the first-run picker opens over a READY city, and never gates readiness", async ({
  page,
}) => {
  // No ?settle=1 and no ?lens=: the only state that shows the picker. `open()`
  // itself waits for body[data-ready="1"] — so if the picker could gate the
  // readiness flag this line would time out rather than fail an assertion.
  const errors = await open(page, "?seed=7");

  await expect(page.locator("#lens-modal")).toBeVisible();
  expect(await page.evaluate(() => document.body.dataset.ready)).toBe("1");
  // The city is mounted BEHIND the modal, not waiting on it.
  expect(await page.evaluate(() => window.__tycoonCity!.fireCount())).toBe(1);
  expect(errors).toEqual([]);
});

test("the picker is suppressed by ?settle=1 and by an explicit ?lens=", async ({ page }) => {
  await open(page, "?settle=1");
  await expect(page.locator("#lens-modal")).toBeHidden();

  await open(page, "?seed=7&lens=on-call");
  await expect(page.locator("#lens-modal")).toBeHidden();
});

test("picking persists; skipping persists 'none' so it never nags again", async ({ page }) => {
  await open(page, "?seed=7");
  await page.locator('[data-lens="on-call"]').click();

  await expect(page.locator("#lens-modal")).toBeHidden();
  expect(await page.evaluate(() => window.__tycoonCity!.lensId())).toBe("on-call");
  expect(await page.evaluate(() => localStorage.getItem("tycoon-city.lens"))).toBe("on-call");

  await page.evaluate(() => localStorage.removeItem("tycoon-city.lens"));
  await open(page, "?seed=7");
  await page.locator(".lens-skip").click();
  expect(await page.evaluate(() => localStorage.getItem("tycoon-city.lens"))).toBe("none");

  const errors = await open(page, "?seed=7");
  await expect(page.locator("#lens-modal")).toBeHidden();
  expect(errors).toEqual([]);
});

test("manual fiddling never rewrites the stored preset", async ({ page }) => {
  await open(page, "?seed=7");
  await page.locator('[data-lens="on-call"]').click();

  // Toggle both overlays and open a panel by hand — the preset must survive.
  await page.keyboard.press("t");
  await page.keyboard.press("w");
  await page.keyboard.press("p");

  expect(await page.evaluate(() => localStorage.getItem("tycoon-city.lens"))).toBe("on-call");
});

test("the footer switcher changes the lens and persists that pick", async ({ page }) => {
  await open(page, "?settle=1&lens=none");

  await page.selectOption("#lens-switch select", "analytics-engineer");
  expect(await page.evaluate(() => window.__tycoonCity!.lensId())).toBe("analytics-engineer");
  expect(await page.evaluate(() => localStorage.getItem("tycoon-city.lens"))).toBe("analytics-engineer");
  expect((await chipOrder(page))[0]).toBe("tests-fail");
});
