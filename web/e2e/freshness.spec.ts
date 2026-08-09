/**
 * THE FOOTER'S AGE, AND WHICH CLOCK IT COMES FROM.
 *
 * THE BUG: the age was measured from the browser's own fetch. Right for the
 * live server, which builds city.json for the request that asked for it;
 * WRONG for a static export, where a week-old city.json on a CDN read
 * "as of 3s ago" — a freshness claim nobody made.
 *
 * THE WRONG-AXIS TRAP THIS FILE IS BUILT AGAINST, and it is the whole reason
 * these specs are shaped the way they are: `expect(asof).toContainText("ago")`
 * PASSES ON THE BUG. So does asserting that some number is shown. The only
 * assertions that can fail for the right reason are the ones that pin the
 * age to the FIXTURE'S OWN TIMESTAMP and the verb to the source of it — which
 * is what every test below does, against a stamp computed in the test and
 * hand-checked in a comment.
 *
 * The four states, all four asserted: an export with a stamp, an export with
 * no meta.json at all (older exports), the server's explicit `generated_at:
 * null`, and a meta.json that is garbage.
 */

import { expect, test, type Page } from "@playwright/test";
import { open } from "./helpers";

/** 6 days in ms, written out: 6 × 24 × 3600 × 1000 = 518,400,000. */
const SIX_DAYS = 518_400_000;
/** 3 minutes: 3 × 60 × 1000 = 180,000. */
const THREE_MINUTES = 180_000;

/** Serve a meta.json body (or a status) for this page's `./meta.json`. */
async function serveMeta(page: Page, body: unknown, status = 200): Promise<void> {
  await page.route("**/meta.json*", (route) =>
    route.fulfill({
      status,
      contentType: "application/json",
      body: typeof body === "string" ? body : JSON.stringify(body),
    }),
  );
}

/**
 * `open()` fails a spec on ANY response >= 400 and on any console error, which
 * is exactly the guard we want everywhere else — and exactly what a
 * deliberately-missing meta.json trips twice over: the 404 itself, and the
 * "Failed to load resource" line Chrome logs for a 404 behind `fetch`.
 *
 * Both are expected here and NOTHING ELSE is: a page error, a thrown
 * exception, or a 404 on any other URL still fails the test. This second,
 * quieter cost of a missing sidecar is also why the live server answers
 * /meta.json with an explicit `generated_at: null` instead of 404 — otherwise
 * every page load against `tycoon-city` would print a red line to the console.
 */
async function openWithNoMeta(page: Page): Promise<string[]> {
  const expected = (text: string): boolean =>
    text.includes("meta.json") || text.includes("Failed to load resource");
  const errors: string[] = [];
  page.on("console", (m) => m.type() === "error" && !expected(m.text()) && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on(
    "response",
    (r) =>
      r.status() >= 400 && !expected(r.url()) && errors.push(`${r.status()} ${r.url()}`),
  );
  await page.goto("/?settle=1");
  await page.waitForSelector('body[data-ready="1"]');
  await page.waitForTimeout(300);
  return errors;
}

test("an export stamped six days ago reads six days old, not seconds", async ({ page }) => {
  const stamp = new Date(Date.now() - SIX_DAYS).toISOString();
  await serveMeta(page, { format: "database-tycoon.meta", version: 1, generated_at: stamp });

  await open(page, "?settle=1");

  const asof = page.locator("#asof");
  // The whole point, and the only assertion here that the bug fails:
  await expect(asof).toHaveText("exported 6 days ago");
  // Belt: the old behaviour rendered a seconds-scale age from the fetch.
  await expect(asof).not.toContainText("as of");
  expect(await asof.textContent()).not.toMatch(/\b\d+s ago\b/);
  // And the exact instant is one hover away, so the claim is checkable.
  expect(await asof.getAttribute("title")).toContain(stamp.slice(0, 19));
});

test("the age tracks the stamp, not a constant", async ({ page }) => {
  // The control for the test above: a DIFFERENT stamp must produce a
  // different age, or "6 days" could be hardcoded anywhere in the pipeline.
  await serveMeta(page, { generated_at: new Date(Date.now() - THREE_MINUTES).toISOString() });

  await open(page, "?settle=1");

  await expect(page.locator("#asof")).toHaveText("exported 3m ago");
});

test("no meta.json at all: the fallback says which clock it is using", async ({ page }) => {
  // An export written before meta.json existed. It must degrade to the fetch
  // time AND say so — claiming an export freshness it cannot know would be
  // the same lie in the other direction.
  await serveMeta(page, "not found", 404);

  const errors = await openWithNoMeta(page);

  const asof = page.locator("#asof");
  await expect(asof).toContainText("as of");
  await expect(asof).not.toContainText("exported");
  expect(await asof.getAttribute("title")).toContain("no export time available");
  // A missing sidecar costs you nothing else: the city is up and clean.
  expect(await page.evaluate(() => window.__tycoonCity!.doc.lots.length)).toBeGreaterThan(0);
  expect(errors).toEqual([]);
});

test("the live server's explicit null is the same named absence", async ({ page }) => {
  // What `tycoon-city` serves: a document that says, in as many words, "this
  // city.json was built for your request, so I have no export time to give".
  await serveMeta(page, {
    format: "database-tycoon.meta",
    version: 1,
    generated_at: null,
    note: "served live: city.json is generated per request",
  });

  await open(page, "?settle=1");

  await expect(page.locator("#asof")).toContainText("as of");
  await expect(page.locator("#asof")).not.toContainText("exported");
});

test("a garbage meta.json falls back instead of costing you the map", async ({ page }) => {
  await serveMeta(page, "{not json at all");

  const errors = await open(page, "?settle=1");

  await expect(page.locator("#asof")).toContainText("as of");
  expect(await page.evaluate(() => window.__tycoonCity!.doc.lots.length)).toBeGreaterThan(0);
  expect(errors).toEqual([]);
});
