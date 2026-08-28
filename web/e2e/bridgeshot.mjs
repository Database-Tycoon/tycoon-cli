import { chromium } from "@playwright/test";
const browser = await chromium.launch({ channel: "chrome", headless: true,
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto("http://localhost:5173/?settle=1");
await page.waitForSelector('body[data-ready="1"]');
await page.waitForTimeout(400);
await page.evaluate(() => window.__tycoonCity.visit("mart.mart__revenue"));
await page.waitForTimeout(1100);
console.log("bridges:", await page.evaluate(() => window.__tycoonCity.skybridgeCount()));
await page.screenshot({ path: process.argv[2] });
process.exit(0);
