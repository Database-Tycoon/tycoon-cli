import type { Page } from "@playwright/test";
import { PNG } from "pngjs";

/** Load the app, wait for the first rendered frame, and fail the test on any
 * console error, page error, or >= 400 response. Returns the error sink so a
 * spec can assert it stayed empty at the end. */
export async function open(page: Page, query = ""): Promise<string[]> {
  const errors: string[] = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("response", (r) => r.status() >= 400 && errors.push(`${r.status()} ${r.url()}`));
  await page.goto(`/${query}`);
  await page.waitForSelector('body[data-ready="1"]');
  await page.waitForTimeout(300);
  return errors;
}

/** Count canvas pixels of an exact #rrggbb colour. Exact-match is the point:
 * it only means anything under ?flat=1, where materials are unlit. */
export async function countPixels(page: Page, hex: string): Promise<number> {
  const buffer = await page.locator("canvas").screenshot();
  const png = PNG.sync.read(buffer);
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  let count = 0;
  for (let i = 0; i < png.data.length; i += 4) {
    if (png.data[i] === r && png.data[i + 1] === g && png.data[i + 2] === b) count++;
  }
  return count;
}

export async function setPose(page: Page, pose: "home" | "top" | "low"): Promise<void> {
  await page.evaluate((p) => window.__tycoonCity!.setPose(p), pose);
  await page.waitForTimeout(250); // orbit damping settles across a few frames
}
