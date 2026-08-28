// Ad-hoc screenshot of the RUN REPLAY at a chosen cursor, over the committed
// run fixtures (never a live server's run data):
//   node e2e/replayshot.mjs <out.png> [cursor] [pose]
// cursor defaults to 2 — the step where staging.stg_customers errors — and
// pose is one of home|top|low (default home) or "step" to keep the camera
// where the replay's own fly-to put it.
//
// DATABASE_TYCOON_WEB_PORT (default 5173) picks the server. A parallel worktree MUST set
// it — a picture of another checkout looks fine and lies.
import { chromium } from "@playwright/test";
import path from "node:path";

const [out = "replay.png", cursorArg = "2", pose = "home"] = process.argv.slice(2);
const cursor = Number(cursorArg);
const port = process.env.DATABASE_TYCOON_WEB_PORT ?? "5173";
const CITY = path.resolve("e2e/fixtures/rich.city.json");
const INDEX = path.resolve("e2e/fixtures/runs.index.json");
const RUN_FAIL = path.resolve("e2e/fixtures/run.fail.json");
const FAIL_ID = "8b4d19e2-0000-4000-8000-00000000000b";

const browser = await chromium.launch({
  channel: "chrome",
  headless: true,
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.route("**/city.json*", (route) => route.fulfill({ path: CITY }));
await page.route("**/runs.json*", (route) => route.fulfill({ path: INDEX }));
await page.route("**/runs/*.json*", (route) => route.fulfill({ path: RUN_FAIL }));
await page.goto(`http://localhost:${port}/?settle=1`);
await page.waitForSelector('body[data-ready="1"]', { timeout: 30000 });

await page.evaluate((id) => window.__tycoonCity.runReplay(id), FAIL_ID);
await page.evaluate((n) => {
  for (let i = 0; i < n; i += 1) window.__tycoonCity.runStep();
}, cursor);
// The replay flies the camera to the current step; let that glide finish
// before overriding the pose, or the flight lerps back over it.
await page.waitForTimeout(900);
if (pose === "cascade") {
  // A framing that holds BOTH halves of the drama at a readable size: the
  // burning step in `staging` and the dimmed `mart` column it took down.
  await page.evaluate(() =>
    window.__tycoonCity.setCameraPose({ position: [11.5, 8.5, 18], target: [16.5, 0, 5.5] }),
  );
} else if (pose === "mart") {
  await page.evaluate(() =>
    window.__tycoonCity.setCameraPose({ position: [17, 6, 14], target: [22.5, 0, 7.5] }),
  );
} else if (pose !== "step") {
  await page.evaluate((p) => window.__tycoonCity.setPose(p), pose);
}
// The object inspector belongs to the selection the fly-to made; close it so
// the picture is of the CITY, with the run panel still naming the step.
await page.click("#inspector .close");
await page.waitForTimeout(600);

console.log("cursor:", JSON.stringify(await page.evaluate(() => window.__tycoonCity.runCursor())));
console.log("fires:", await page.evaluate(() => window.__tycoonCity.fireCount()));
console.log(
  "states:",
  JSON.stringify(
    await page.evaluate(() =>
      Object.fromEntries(
        window.__tycoonCity.doc.lots.map((l) => [l.object_key, window.__tycoonCity.runStateOf(l.object_key)]),
      ),
    ),
  ),
);
await page.screenshot({ path: out });
process.exit(0);
