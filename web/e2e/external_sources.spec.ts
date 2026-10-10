/**
 * gh-387: a staging model whose dbt sources live outside the rendered
 * warehouse (nyc_data's `database: raw`) has no inbound edge, and the
 * inspector used to list its upstream as "none". It must name those sources
 * instead, and say they are unmeasured.
 *
 * Serves a modified copy of the rich fixture: `staging.stg_orders` loses its
 * one inbound edge and gains an `external_upstream` entry, which is exactly
 * the shape the export produces for that project.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import { open } from "./helpers";

const FIXTURE = path.resolve("e2e/fixtures/rich.city.json");
const KEY = "staging.stg_orders";

interface Doc {
  objects: { key: string; dbt: Record<string, unknown> | null }[];
  edges: { dst: string }[];
}

async function serve(page: Page, external: unknown[]): Promise<void> {
  const doc = JSON.parse(await readFile(FIXTURE, "utf8")) as Doc;
  doc.edges = doc.edges.filter((e) => e.dst !== KEY);
  doc.objects.find((o) => o.key === KEY)!.dbt!.external_upstream = external;
  await page.route("**/city.json*", (route) => route.fulfill({ json: doc }));
}

async function upstreamList(page: Page): Promise<string> {
  await page.evaluate((key) => window.__tycoonCity!.select(key), KEY);
  const heading = page.locator("#inspector h3", { hasText: /^upstream$/ });
  return (await heading.locator("xpath=following-sibling::ul[1]").innerText()).toLowerCase();
}

test("a source outside the warehouse is named as upstream, not none", async ({ page }) => {
  await serve(page, [
    {
      name: "raw_citibike.station_information",
      relation: "raw.raw_citibike.station_information",
      freshness_status: "warn",
    },
  ]);
  await open(page, "?settle=1");

  const upstream = await upstreamList(page);
  expect(upstream).toContain("raw_citibike.station_information");
  expect(upstream).toContain("outside this warehouse, not measured");
  expect(upstream).toContain("freshness warn");
  expect(upstream).not.toContain("none");
  await expect(page.locator("#inspector li.external")).toHaveAttribute(
    "title",
    "raw.raw_citibike.station_information",
  );
});

test("with no edges and no external sources, upstream still says none", async ({ page }) => {
  await serve(page, []);
  await open(page, "?settle=1");

  expect((await upstreamList(page)).trim()).toBe("none");
});
