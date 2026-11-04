// Copy to web/e2e/zz-shot.spec.ts, set OUT, run `npx playwright test e2e/zz-shot.spec.ts`,
// then delete the copy. Runs inside the existing Playwright harness (webServer +
// helpers), so no dev server or Chrome channel is needed. Poses assume the ring
// planner's demo export (0.2.1+); re-aim if the layout moves.
import { test } from "@playwright/test";
import { open } from "./helpers";

const OUT = process.env.SHOT_OUT ?? "/tmp/city-shots";

test("release screenshots", async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 1000 });
  await open(page, "?settle=1");
  await page.screenshot({ path: `${OUT}/city-default.png` });
  // High overview: marts downtown beside the civic core, raw on the north edge.
  await page.evaluate(() => window.__tycoonCity!.setCameraPose({ position: [16, 18, 30], target: [16, 0, 12] }));
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${OUT}/city-overview.png` });
  // Street level, looking north up the trunk road (x = 18 in the demo export).
  await page.evaluate(() => window.__tycoonCity!.setCameraPose({ position: [18.5, 2.2, 16.5], target: [18.5, 0, 9] }));
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${OUT}/city-street-level.png` });
});
