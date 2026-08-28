/**
 * THE GUIDED TOUR — and the two laws it exists to obey.
 *
 * 1. **Semantic addressing.** A stop names an object key, a schema or a civic
 *    key; never a tile. The guard is not "the tour flew somewhere" — that
 *    passes on a tour hard-coded to a coordinate. It is: MOVE EVERY BUILDING
 *    (streets v5's whole job) and watch the same stop still land on the same
 *    object, at its NEW position. A coordinate-addressed tour dies on that
 *    fixture; this one must not.
 *
 * 2. **`requires` on any stop that states a fact.** The guard is the same
 *    document with its failing test removed: the fire stop must vanish and
 *    the companion "quiet city" stop must appear in its place. A tour that
 *    narrates a fire in a city with none is exactly the invention
 *    `database.notes` is written to prevent.
 *
 * `?settle=1` throughout, so these run against the frozen city — and `&lens=`
 * explicitly, so the first-run picker never sits on top of the tour.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import { open } from "./helpers";

const FIXTURE = path.resolve("e2e/fixtures/rich.city.json");
const readFixture = async (): Promise<Record<string, never>> =>
  JSON.parse(await readFile(FIXTURE, "utf8"));

test.beforeEach(async ({ page }) => {
  await page.route("**/city.json*", (route) => route.fulfill({ path: FIXTURE }));
});

const serve = (page: Page, doc: unknown): Promise<void> =>
  page.route("**/city.json*", (route) =>
    route.fulfill({ contentType: "application/json", body: JSON.stringify(doc) }),
  );

/** The stop ids the tour walks, by clicking `next` to the end. */
async function walk(page: Page, max = 30): Promise<string[]> {
  const seen: string[] = [];
  for (let i = 0; i < max; i += 1) {
    if (await page.locator("#tour").isHidden()) break;
    seen.push((await page.locator(".tour-card").getAttribute("data-stop"))!);
    await page.locator(".tour-next").click();
    await page.waitForTimeout(60);
  }
  return seen;
}

test("the tour walks the city's core metaphors, in order", async ({ page }) => {
  await open(page, "?settle=1&lens=none&tour=1");

  const stops = await walk(page);
  expect(stops).toEqual([
    "view",
    "lenses",
    "districts",
    "streets",
    "plant",
    "orphans",
    "fire",
    "firehouse",
    "library",
    "weather",
    "load",
    "wear",
    "drift",
    "replay",
    "controls",
  ]);
  // The last `next` finished it, and a finished tour stays closed.
  await expect(page.locator("#tour")).toBeHidden();
});

test("a stop addresses its subject SEMANTICALLY: move every building, it still lands", async ({
  page,
}) => {
  // First, where the fire stop lands on the fixture as shipped. The on-call
  // playlist opens on two orientation stops ("view", "lenses") with no
  // target, so click past them to reach "fire".
  await open(page, "?settle=1&lens=on-call&tour=1");
  await page.locator(".tour-next").click();
  await page.locator(".tour-next").click();
  expect(await page.locator(".tour-card").getAttribute("data-stop")).toBe("fire");
  await page.waitForTimeout(900); // the glide
  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBe("mart.mart__revenue");
  const before = await page.evaluate(() => window.__tycoonCity!.cameraPose());

  // Now streets v5 arrives and every lot moves. Nothing about WHICH object is
  // on fire changed — only where it stands.
  const doc = await readFixture();
  const moved = { ...doc, lots: (doc.lots as { x: number; y: number }[]).map((l) => ({ ...l, x: l.x + 4, y: l.y + 3 })) };
  await serve(page, moved);

  // Progress is persisted by stop id, so reopening the tour resumes on
  // "fire" directly rather than restarting at "view".
  await open(page, "?settle=1&lens=on-call&tour=1");
  expect(await page.locator(".tour-card").getAttribute("data-stop")).toBe("fire");
  await page.waitForTimeout(900);

  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBe("mart.mart__revenue");
  // And it flew to the NEW place: a tour that remembered a tile would have
  // landed on the old one, which is now an empty patch of ground.
  const after = await page.evaluate(() => window.__tycoonCity!.cameraPose());
  expect(after.target[0]! - before.target[0]!).toBeCloseTo(4, 1);
  expect(after.target[2]! - before.target[2]!).toBeCloseTo(3, 1);
});

test("an R refresh mid-tour repoints the next stop at the city now on screen", async ({ page }) => {
  // The same law as the semantic-addressing guard above, but for the OTHER way
  // a document is replaced: not a reload, an `R` refresh inside one page load.
  // The tour and the run replay were both handed the BOOT document instead of
  // the HUD's current one, so after `R` the tour narrated and flew against a
  // city that had already been unmounted. It is invisible while the catalog
  // holds still, which is why it survived to a release candidate.
  const doc = await readFixture();
  const lots = doc.lots as unknown as { object_key: string; x: number; y: number; w: number; h: number }[];
  const before = lots.find((l) => l.object_key === "mart.mart__revenue")!;

  await open(page, "?settle=1&lens=on-call&tour=1");
  expect(await page.locator(".tour-card").getAttribute("data-stop")).toBe("view");

  // Streets v5 lands while the reader is still on the first card: every lot
  // moves, nothing about WHICH object burns changes.
  await serve(page, { ...doc, lots: lots.map((l) => ({ ...l, x: l.x + 4, y: l.y + 3 })) });
  await page.evaluate(() => window.__tycoonCity!.refresh());
  expect(await page.locator("#status").innerText()).not.toContain("refresh failed");

  // Two cards on ("view", "lenses") is the fire stop, which targets the
  // failing mart by key and walks through the HUD's `visit` door.
  await page.locator(".tour-next").click();
  await page.locator(".tour-next").click();
  expect(await page.locator(".tour-card").getAttribute("data-stop")).toBe("fire");
  await page.waitForTimeout(900); // the glide

  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBe("mart.mart__revenue");
  const pose = await page.evaluate(() => window.__tycoonCity!.cameraPose());
  // Where the building stands NOW…
  expect(pose.target[0]!).toBeCloseTo(before.x + 4 + before.w / 2, 1);
  expect(pose.target[2]!).toBeCloseTo(before.y + 3 + before.h / 2, 1);
  // …and emphatically not where it stood before the refresh.
  expect(pose.target[0]!).not.toBeCloseTo(before.x + before.w / 2, 1);
});

test("a catalog with no fire is never told about one — the absence is narrated", async ({
  page,
}) => {
  const doc = await readFixture();
  const quiet = {
    ...doc,
    lots: (doc.lots as { test_status: string | null }[]).map((l) =>
      l.test_status === "fail" ? { ...l, test_status: "pass" } : l,
    ),
  };
  await serve(page, quiet);

  const errors = await open(page, "?settle=1&lens=none&tour=1");
  const stops = await walk(page);

  expect(stops).not.toContain("fire"); // requires() skipped it
  expect(stops).toContain("quiet-city"); // and the absence took its place
  expect(errors).toEqual([]);
});

test("the quiet-city stop never runs on a city that IS burning", async ({ page }) => {
  // The other half of the same predicate: the two stops are exclusive, so a
  // tour can never both narrate a fire and claim the city is quiet.
  await open(page, "?settle=1&lens=none&tour=1");

  const stops = await walk(page);
  expect(stops).toContain("fire");
  expect(stops).not.toContain("quiet-city");
});

test("a document with no weather verdicts gets the named absence, not fog", async ({ page }) => {
  const doc = await readFixture();
  await serve(page, {
    ...doc,
    weather: { cells: [], note: "no source freshness verdicts — weather unknown" },
  });

  await open(page, "?settle=1&lens=none&tour=1");
  const stops = await walk(page);

  expect(stops).not.toContain("weather");
  expect(stops).toContain("weather-unknown");
});

test("the plain demo tour skips every stop its catalog cannot support", async ({ page }) => {
  // No route interception: the real, healthy demo export. No fires, no late
  // sources, no run history, no drift — every one of those stops must be gone,
  // and the ones the demo CAN support must remain.
  await page.unroute("**/city.json*");
  await open(page, "?settle=1&lens=none&tour=1");

  const stops = await walk(page);
  expect(stops).toEqual([
    "view",
    "lenses",
    "districts",
    "streets",
    "plant",
    "orphans",
    "quiet-city",
    "firehouse",
    "library",
    "weather-unknown",
    "controls",
  ]);
});

test("progress is persisted: a reload resumes instead of restarting the lecture", async ({
  page,
}) => {
  await open(page, "?settle=1&lens=none&tour=1");
  // The playlist opens on two orientation stops ("view", "lenses"); two
  // clicks lands on the third id, "districts".
  await page.locator(".tour-next").click();
  await page.locator(".tour-next").click();
  expect(await page.locator(".tour-card").getAttribute("data-stop")).toBe("districts");

  await open(page, "?settle=1&lens=none&tour=1");
  expect(await page.locator(".tour-card").getAttribute("data-stop")).toBe("districts");

  // …and `?tour=restart` is the way back to the beginning.
  await open(page, "?settle=1&lens=none&tour=restart");
  expect(await page.locator(".tour-card").getAttribute("data-stop")).toBe("view");
});

test("a persisted stop id resumes at the same subject regardless of its position", async ({
  page,
}) => {
  // Write a real, known id straight into storage rather than clicking there —
  // this is the behaviour the fix exists for: the READER is addressed by
  // subject, not by a position that a playlist edit can silently repoint.
  await open(page, "?settle=1&lens=none&tour=1");
  await page.evaluate((key) => localStorage.setItem(key, "fire"), "tycoon-city.tour");
  await open(page, "?settle=1&lens=none&tour=1");
  expect(await page.locator(".tour-card").getAttribute("data-stop")).toBe("fire");
});

test("a numeric index left by an older, index-based build no longer resolves to a position", async ({
  page,
}) => {
  // Before 2026-08-08 this repo persisted a numeric INDEX. A reader who had
  // stopped at position 2 back then would have the literal string "2" sitting
  // in localStorage today. That value is not just meaningless now — it is
  // actively dangerous: the playlist grew four stops longer, so index 2 is
  // "districts" today, a different subject than whatever used to sit at
  // position 2. A spec that fed in a value like "a-stop-that-no-longer-exists"
  // would pass under BOTH the old index-based code (Number(...) is NaN, so it
  // already fell back to 0) and the new id-based code — it would prove
  // nothing about this fix. "2" is the adversarial case: it parses as a valid
  // number, so only an id-aware reader recognizes it is not a real stop id.
  await open(page, "?settle=1&lens=none&tour=1");
  await page.evaluate((key) => localStorage.setItem(key, "2"), "tycoon-city.tour");
  await open(page, "?settle=1&lens=none&tour=1");
  const stop = await page.locator(".tour-card").getAttribute("data-stop");
  // The old, index-based reading of "2" would land here — a silent jump to a
  // different subject than the one this reader actually left off on.
  expect(stop).not.toBe("districts");
  // Unrecognized as a stop id, so it restarts cleanly instead of guessing.
  expect(stop).toBe("view");
});

test("Esc skips for good", async ({ page }) => {
  await open(page, "?settle=1&lens=none&tour=1");
  await expect(page.locator("#tour")).toBeVisible();

  await page.keyboard.press("Escape");
  await expect(page.locator("#tour")).toBeHidden();

  await open(page, "?settle=1&lens=none&tour=1");
  await expect(page.locator("#tour")).toBeHidden();
});

test("a lens picks which stops its role walks", async ({ page }) => {
  await open(page, "?settle=1&lens=data-engineer&tour=1");
  const engineer = await walk(page);
  expect(engineer).toEqual([
    "view",
    "lenses",
    "districts",
    "streets",
    "plant",
    "orphans",
    "load",
    "replay",
    "drift",
    "controls",
  ]);

  await page.evaluate(() => localStorage.removeItem("tycoon-city.tour"));
  await open(page, "?settle=1&lens=analytics-engineer&tour=1");
  const analyst = await walk(page);
  // Same city, same predicates — a different itinerary, and "quiet-city" is
  // dropped by `requires` even though this lens asks for it.
  expect(analyst).toEqual([
    "view",
    "lenses",
    "districts",
    "library",
    "fire",
    "streets",
    "orphans",
    "controls",
  ]);
});

test("no tour without ?tour, and the tour never gates readiness", async ({ page }) => {
  const errors = await open(page, "?settle=1&lens=none");
  await expect(page.locator("#tour")).toBeHidden();
  expect(await page.evaluate(() => document.body.dataset.ready)).toBe("1");
  expect(errors).toEqual([]);
});
