/**
 * The opening camera fits the city (#386). On nyc_data the overview left the
 * city as a thin strip in a frame of grass, and the street-level pose cut the
 * tallest towers off at the top of the screen.
 *
 * Two opposed assertions per pose, both on projected screen geometry. Every
 * building, footprint to roof, lies inside the canvas: that alone passes for
 * a camera parked far enough away. The city's screen box must also span most
 * of the canvas along one axis: that alone passes for a camera parked inside
 * the city. Together they pin "fitted".
 */

import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import { open, setPose } from "./helpers";

const RICH = path.resolve("e2e/fixtures/rich.city.json");

/** The share of the canvas the city's buildings and plates must span along
 * their better-filled axis. The fit keeps a 5% border and also makes room for
 * rooftop spires and usage beacons that this box does not measure, so 0.9 is
 * the ceiling. Before the fit, the rich fixture's overview spanned 0.39 to
 * 0.43. */
const MIN_FILL = 0.7;

type Rect = { left: number; top: number; right: number; bottom: number };

async function measure(page: Page): Promise<{ canvas: Rect; lots: [string, Rect | null][]; city: Rect }> {
  return page.evaluate(() => {
    const hooks = window.__tycoonCity!;
    const c = document.querySelector("canvas")!.getBoundingClientRect();
    const lots = hooks.doc.lots.map(
      (l) => [l.object_key, hooks.lotScreenRect(l.object_key)] as [string, Rect | null],
    );
    const rects = [
      ...lots.map(([, r]) => r),
      ...hooks.doc.districts.map((d) => hooks.districtScreenRect(d.schema)),
    ].filter((r): r is Rect => r !== null);
    return {
      canvas: { left: c.left, top: c.top, right: c.right, bottom: c.bottom },
      lots,
      city: {
        left: Math.min(...rects.map((r) => r.left)),
        top: Math.min(...rects.map((r) => r.top)),
        right: Math.max(...rects.map((r) => r.right)),
        bottom: Math.max(...rects.map((r) => r.bottom)),
      },
    };
  });
}

const documents: [string, string | null][] = [
  ["demo", null],
  ["rich", RICH],
];

for (const [name, fixture] of documents) {
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 1280, height: 720 },
  ]) {
    test(`the overview and street poses frame the whole city (${name}, ${viewport.width}x${viewport.height})`, async ({
      page,
    }) => {
      await page.setViewportSize(viewport);
      if (fixture) await page.route("**/city.json*", (route) => route.fulfill({ path: fixture }));
      await open(page, "?settle=1&lens=none");

      for (const pose of ["home", "low"] as const) {
        await setPose(page, pose);
        const { canvas, lots, city } = await measure(page);
        const tolerance = 1;
        for (const [key, r] of lots) {
          expect(r, `${pose}: ${key} in front of the camera`).not.toBeNull();
          const inside =
            r!.left >= canvas.left - tolerance &&
            r!.right <= canvas.right + tolerance &&
            r!.top >= canvas.top - tolerance &&
            r!.bottom <= canvas.bottom + tolerance;
          expect(inside, `${pose}: ${key} at ${JSON.stringify(r)} in ${JSON.stringify(canvas)}`).toBe(
            true,
          );
        }
        const fill = Math.max(
          (city.right - city.left) / (canvas.right - canvas.left),
          (city.bottom - city.top) / (canvas.bottom - canvas.top),
        );
        expect(fill, `${pose}: city ${JSON.stringify(city)} in ${JSON.stringify(canvas)}`).toBeGreaterThanOrEqual(
          MIN_FILL,
        );
      }
    });
  }
}

test("a resize refits the opening view until the viewer takes the camera", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page, "?settle=1&lens=none");
  const pose = () => page.evaluate(() => window.__tycoonCity!.cameraPose());

  const wide = await pose();
  await page.setViewportSize({ width: 900, height: 900 });
  await page.waitForTimeout(300);
  const square = await pose();
  // A narrower window needs a more distant camera to keep the city's width in
  // frame; an unchanged pose means the fit was solved once, for a stale aspect.
  expect(square.position, "refit on resize").not.toEqual(wide.position);

  const canvas = page.locator("canvas");
  const box = (await canvas.boundingBox())!;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + 120, box.y + box.height / 2 + 40, { steps: 6 });
  await page.mouse.up();
  await page.waitForTimeout(400);
  const dragged = await pose();
  expect(dragged.position, "the drag moved the camera").not.toEqual(square.position);

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.waitForTimeout(300);
  const after = await pose();
  const moved = Math.hypot(...after.target.map((v, i) => v - dragged.target[i]!));
  expect(moved, "a resize after a drag leaves the viewer's camera alone").toBeLessThan(0.01);
});
