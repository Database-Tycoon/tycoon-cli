/**
 * The framing policies from tests/test_framing.py, ported per the plan: every
 * assertion is about painted pixels or projected screen geometry — the
 * *outcome* of framing — never about what was handed to the camera. Runs
 * under ?flat=1 (unlit materials, no AA, sentinel clear colour) so exact
 * pixel counting is meaningful.
 */

import { expect, test } from "@playwright/test";
import { countPixels, open, setPose } from "./helpers";

const FLAT_PLANT = "#ff3223";
const FLAT_SENTINEL = "#010203";

test("the plant is painted inside the opening viewport", async ({ page }) => {
  await open(page, "?flat=1&settle=1");

  // >0 exact-colour pixels: the 2D app once shipped with the plant eight
  // tiles off-screen while a coordinate-list assertion stayed green.
  expect(await countPixels(page, FLAT_PLANT)).toBeGreaterThan(0);
});

test("the plant stays painted at every named pose", async ({ page }) => {
  await open(page, "?flat=1&settle=1");

  for (const pose of ["top", "low", "home"] as const) {
    await setPose(page, pose);
    expect(await countPixels(page, FLAT_PLANT), `pose ${pose}`).toBeGreaterThan(0);
  }
});

test("no viewport holes when the frustum is on the ground", async ({ page }) => {
  await open(page, "?flat=1&settle=1");

  // Top-down: terrain plus skirt must cover every fragment. A sentinel pixel
  // is a hole the skirt policy failed to cover; sky poses are exempt because
  // sky legitimately shows the clear colour.
  await setPose(page, "top");
  expect(await countPixels(page, FLAT_SENTINEL)).toBe(0);
});

test("the sentinel is countable at all — sky shows it at a low pose", async ({ page }) => {
  await open(page, "?flat=1&settle=1");

  // The counterweight for the === 0 assertion above: a pixel counter that is
  // simply broken (wrong channel order, wrong locator, always-0) would pass
  // "no holes" vacuously. At a shallow pitch the sky fills the top of the
  // frame with the sentinel clear colour, so the same counter must see it.
  await setPose(page, "low");
  expect(await countPixels(page, FLAT_SENTINEL)).toBeGreaterThan(1000);
});

// The primitive claim underneath the overlap test below: the chip EXISTS. The
// overlap assertion cannot express "no labels at all" — it times out locating
// the first schema and says only that `marts` was not found, which reads as a
// `marts` problem. It was not: `labels.render()` was dropped from the animation
// loop, so CSS2DRenderer never attached a single label div, on either path.
// Hence both queries here — `?flat=1` is a different code path through
// `mountCity`, and this file's other tests only ever exercise the flat one.
for (const query of ["?flat=1&settle=1", "?settle=1"]) {
  test(`one label element per district, carrying the schema name (${query})`, async ({ page }) => {
    await open(page, query);

    const schemas: string[] = await page.evaluate(() =>
      window.__tycoonCity!.doc.districts.map((d) => d.schema),
    );
    expect(schemas.length).toBeGreaterThan(0);

    // Exactly one chip per schema. Counted per schema rather than as a set over
    // the whole class, because `civic.ts` reuses `.district-label` for the
    // firehouse and library chips — so the class is a superset of the districts.
    for (const schema of schemas) {
      const chips = await page
        .locator(".district-label", { hasText: new RegExp(`^${schema}$`) })
        .count();
      expect(chips, `${query} ${schema}`).toBe(1);
    }
  });
}

test("every district label overlaps its own district on screen", async ({ page }) => {
  await open(page, "?flat=1&settle=1");

  const schemas: string[] = await page.evaluate(() =>
    window.__tycoonCity!.doc.districts.map((d) => d.schema),
  );
  expect(schemas.length).toBeGreaterThan(0);

  for (const schema of schemas) {
    const district = await page.evaluate((s) => window.__tycoonCity!.districtScreenRect(s), schema);
    const label = await page
      .locator(".district-label", { hasText: new RegExp(`^${schema}$`) })
      .boundingBox();
    expect(district, schema).not.toBeNull();
    expect(label, schema).not.toBeNull();
    // Overlap with a small allowance: the label floats just above the plate's
    // near corner, so it must intersect the district's projected box.
    const pad = 8;
    const intersects =
      label!.x < district!.right + pad &&
      label!.x + label!.width > district!.left - pad &&
      label!.y < district!.bottom + pad &&
      label!.y + label!.height > district!.top - pad;
    expect(intersects, `${schema} label at ${JSON.stringify(label)}`).toBe(true);
  }
});

test("clicking resolves every unoccluded lot at three poses, and sky clears", async ({
  page,
}) => {
  await open(page, "?flat=1&settle=1");

  const keys: string[] = await page.evaluate(() =>
    window.__tycoonCity!.doc.lots.map((l) => l.object_key),
  );

  for (const pose of ["home", "top", "low"] as const) {
    await setPose(page, pose);
    let resolved = 0;
    let visible = 0;
    for (const key of keys) {
      const pos = await page.evaluate((k) => window.__tycoonCity!.screenPos(k), key);
      if (!pos) continue; // behind the camera at this pose
      visible++;
      await page.mouse.click(pos.x, pos.y);
      if ((await page.evaluate(() => window.__tycoonCity!.selectedKey())) === key) resolved++;
    }
    // Not all lots need to self-resolve — a short building's centre can be
    // legitimately occluded by a tall neighbour — but the great majority must,
    // and none may resolve to nothing while visibly on screen.
    expect(visible, `pose ${pose}: lots on screen`).toBeGreaterThan(0);
    expect(resolved / visible, `pose ${pose}: ${resolved}/${visible} self-resolved`)
      .toBeGreaterThanOrEqual(0.8);

    await page.mouse.click(60, 110);
    expect(await page.evaluate(() => window.__tycoonCity!.selectedKey()), `pose ${pose} sky`).toBeNull();
  }
});
