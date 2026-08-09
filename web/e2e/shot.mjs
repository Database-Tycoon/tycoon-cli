// Ad-hoc screenshot of the dev server: node e2e/shot.mjs <out.png> [query]
// DATABASE_TYCOON_WEB_PORT (default 5173) picks the server. A parallel worktree MUST set
// it — a picture of another checkout looks fine and lies.
import { chromium } from "@playwright/test";
const [out = "shot.png", query = "?settle=1"] = process.argv.slice(2);
const port = process.env.DATABASE_TYCOON_WEB_PORT ?? "5173";
const browser = await chromium.launch({ channel: "chrome", headless: true,
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto(`http://localhost:${port}/${query}`);
await page.waitForSelector('body[data-ready="1"]', { timeout: 30000 });
await page.waitForTimeout(600);
await page.screenshot({ path: out });
process.exit(0);
