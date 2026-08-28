// Street-level look at the 3D streetscape (curbs, aprons, docks, plazas):
//   DATABASE_TYCOON_WEB_PORT=5297 node e2e/streetshot.mjs out.png [tileX] [tileY] [dx] [dz] [query]
// The camera targets tile (tileX, tileY) from (dx, dz) tiles away at eye
// height, because the "flat/pasted" defect these curbs fix is only visible
// from a shallow angle — the home pose hides it. Nudge dx/dz when a building
// stands between the camera and the thing being inspected.
import { chromium } from "@playwright/test";
const [out = "street.png", tx = "20", ty = "8", dx = "-5", dz = "6", query = "?settle=1"] =
  process.argv.slice(2);
const port = process.env.DATABASE_TYCOON_WEB_PORT ?? "5173";
const browser = await chromium.launch({ channel: "chrome", headless: true,
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto(`http://localhost:${port}/${query}`);
await page.waitForSelector('body[data-ready="1"]');
await page.waitForTimeout(400);
// The road-load overlay paints translucent heat over the whole street surface
// and hides the geometry under it; T turns it off for a geometry look.
await page.keyboard.press("t");
await page.evaluate(([x, y, ox, oz]) => {
  window.__tycoonCity.setCameraPose({ position: [x + ox, 2.2, y + oz], target: [x, 0, y] });
}, [Number(tx), Number(ty), Number(dx), Number(dz)]);
await page.waitForTimeout(500);
await page.screenshot({ path: out });
process.exit(0);
