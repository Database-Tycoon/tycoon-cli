/**
 * Skybridges: column-level lineage renders for the selected building only.
 * The demo fixture's views carry traced column pairs (raw.customers.id ->
 * staging.stg_customers.id -> marts.dim_customers.id), so selecting the
 * middle of that chain must show bridges both ways, and deselecting must
 * clear them — always-on bridges would be spaghetti, and their absence when
 * nothing is selected is part of the design.
 */

import { expect, test } from "@playwright/test";
import { open } from "./helpers";

test("the contract carries column pairs on the demo's traced edges", async ({ page }) => {
  await open(page, "?settle=1");

  const pairs = await page.evaluate(
    () =>
      window.__tycoonCity!.doc.edges.find(
        (e) => e.src === "raw.customers" && e.dst === "staging.stg_customers",
      )?.columns,
  );
  expect(pairs).toEqual([["id", "id"]]);
});

test("selecting a building raises its bridges; deselecting clears them", async ({ page }) => {
  await open(page, "?settle=1");

  expect(await page.evaluate(() => window.__tycoonCity!.skybridgeCount())).toBe(0);

  // stg_customers sits mid-chain: one bridge in (raw), one out (marts).
  await page.evaluate(() => window.__tycoonCity!.select("staging.stg_customers"));
  expect(await page.evaluate(() => window.__tycoonCity!.skybridgeCount())).toBe(2);

  // A building with no traced columns shows none rather than guessing.
  await page.evaluate(() => window.__tycoonCity!.select("raw.events"));
  expect(await page.evaluate(() => window.__tycoonCity!.skybridgeCount())).toBe(0);

  await page.evaluate(() => window.__tycoonCity!.select(""));
  expect(await page.evaluate(() => window.__tycoonCity!.skybridgeCount())).toBe(0);
});

test("bridges survive an R refresh with the selection", async ({ page }) => {
  await open(page, "?settle=1");

  await page.evaluate(() => window.__tycoonCity!.select("staging.stg_customers"));
  await page.evaluate(() => window.__tycoonCity!.refresh());
  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBe("staging.stg_customers");
  expect(await page.evaluate(() => window.__tycoonCity!.skybridgeCount())).toBe(2);
});
