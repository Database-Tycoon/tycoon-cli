/**
 * The `window.__tycoonCity` seam's own contract — the bindings, not the answers.
 *
 * Every other spec trusts that a hook still points at the live city. This one
 * checks that trust directly, because the failure mode is silent: a hook that
 * captured its value at install time keeps answering, plausibly, for a
 * document that an R refresh already took off the scene. No screenshot and no
 * count assertion can tell that apart from a correct answer.
 *
 * The regression this exists for: `doc` was installed as a captured VALUE and
 * then patched afterwards — `main.ts` redefined it as a getter-only accessor
 * while `hud.ts`'s refresh still assigned to it. Modules are strict mode, so
 * the assignment threw, `refresh()`'s own try/catch swallowed the throw, and
 * everything after it — including the selection restore — silently stopped
 * running.
 */

import { expect, test, type Page } from "@playwright/test";
import { open } from "./helpers";

/** Answer the NEXT `city.json` fetch with the real document, mutated. The
 * initial page load has already happened, so this only reaches the refetch. */
async function serveMutated(page: Page, mutate: (doc: any) => void): Promise<void> {
  await page.route("**/city.json*", async (route) => {
    const doc = await (await route.fetch()).json();
    mutate(doc);
    await route.fulfill({ contentType: "application/json", body: JSON.stringify(doc) });
  });
}

test("__tycoonCity.doc tracks the refetched document across a refresh", async ({ page }) => {
  await open(page, "?settle=1");
  const before = await page.evaluate(() => window.__tycoonCity!.doc.database.name);
  expect(before).not.toBe("refetched");

  await serveMutated(page, (doc) => {
    doc.database.name = "refetched";
  });
  await page.evaluate(() => window.__tycoonCity!.refresh());

  // A captured value answers "demo" here; a live getter answers "refetched".
  expect(await page.evaluate(() => window.__tycoonCity!.doc.database.name)).toBe("refetched");
});

test("a refresh runs to the end instead of aborting into its own catch", async ({ page }) => {
  // The catch arm paints this text and is the only thing that does. Reading it
  // is how a swallowed exception mid-refresh becomes visible: without this,
  // an aborted refresh looks exactly like a completed one that did less.
  await open(page, "?settle=1");
  await serveMutated(page, (doc) => {
    doc.database.name = "refetched";
  });

  await page.evaluate(() => window.__tycoonCity!.refresh());

  const status = await page.locator("#status").innerText();
  expect(status).not.toContain("refresh failed");
});
