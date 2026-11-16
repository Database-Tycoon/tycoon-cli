/**
 * District and civic chips must not draw on top of each other (#385). On
 * nyc_data, `main_semantic` over `main_intermediate` read as "in_semantic
 * ntermediate", and the library and firehouse chips sat stacked on one spot.
 *
 * The assertion reads the chips' own DOM rects, the boxes a viewer actually
 * sees, at every named pose and on both committed documents. The rich fixture
 * matters: its library and firehouse are three tiles apart, which is the
 * shape that collided in real use.
 */

import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import { open, setPose } from "./helpers";

const RICH = path.resolve("e2e/fixtures/rich.city.json");

type Chip = { text: string; left: number; top: number; right: number; bottom: number };

/** Every chip a viewer can see right now: attached, displayed, not hidden. */
async function visibleChips(page: Page): Promise<Chip[]> {
  return page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>(".district-label")]
      .filter((el) => el.isConnected && getComputedStyle(el).display !== "none")
      .filter((el) => getComputedStyle(el).visibility !== "hidden")
      .map((el) => {
        const r = el.getBoundingClientRect();
        return { text: el.textContent ?? "", left: r.left, top: r.top, right: r.right, bottom: r.bottom };
      }),
  );
}

function collisions(chips: Chip[]): string[] {
  const out: string[] = [];
  for (const [i, a] of chips.entries()) {
    for (const b of chips.slice(i + 1)) {
      if (a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom) {
        out.push(`${a.text} / ${b.text}`);
      }
    }
  }
  return out;
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
    test(`no two labels overlap at any named pose (${name}, ${viewport.width}x${viewport.height})`, async ({
      page,
    }) => {
      await page.setViewportSize(viewport);
      if (fixture) await page.route("**/city.json*", (route) => route.fulfill({ path: fixture }));
      await open(page, "?settle=1&lens=none");
      const districts: string[] = await page.evaluate(() =>
        window.__tycoonCity!.doc.districts.map((d) => d.schema),
      );

      for (const pose of ["home", "top", "low"] as const) {
        await setPose(page, pose);
        const chips = await visibleChips(page);
        // The counterweight: hiding every chip would also have no overlaps.
        // District names are the labels the city is read by, so each one
        // must still be on screen; only a civic chip may give way.
        const shown = chips.map((c) => c.text);
        for (const schema of districts) {
          expect(shown, `${pose}: ${schema} visible`).toContain(schema);
        }
        expect(collisions(chips), `${pose}: ${JSON.stringify(chips)}`).toEqual([]);
      }
    });
  }
}
