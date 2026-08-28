/**
 * OSI SEMANTICS IN THE HUD — `objects[].semantic` and `joins[]`.
 *
 * Served by route interception over the committed `fixtures/rich.city.json`,
 * exactly as `rich.spec.ts` does. The frozen fixture carries `joins: []` and a
 * null `semantic` on every object, because the demo catalog has no semantic
 * model — which is true of most catalogs and is itself one of the states
 * asserted below. The OSI content is therefore INJECTED here rather than
 * regenerated into the fixture, so the twelve specs that read that document's
 * geometry keep reading the same bytes.
 *
 * If the demo generator ever grows an OSI file, regenerate deliberately:
 *   uv run python scripts/make_demo_tycoon.py
 *   uv run tycoon-city-export demo-tycoon /tmp/rich-export
 *   cp /tmp/rich-export/city.json web/e2e/fixtures/rich.city.json
 * and re-derive the counts below from its printed `joins` and `semantic`.
 *
 * THE POINT OF THIS FILE IS PROVENANCE. A join is DECLARED — somebody wrote
 * it in a semantic model. Lineage is MEASURED (dbt's manifest, duckdb) or
 * INFERRED (a SQL scan). The panel must never let the first be read as the
 * second, so the marker vocabulary is the model graph's: SOLID = declared,
 * DASHED = inferred, and a join with no lineage says so in words.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import { open } from "./helpers";

const FIXTURE = path.resolve("e2e/fixtures/rich.city.json");

/**
 * The frozen city with a hand-written semantic model laid over it.
 *
 * Three joins, chosen to cover the three renderings a pair can have:
 *  1. revenue -> dim__customers  : NO lineage at all (the join street that has
 *     to be paved out of the dirt)
 *  2. revenue -> stg_customers   : also lineage, DECLARED by dbt's manifest —
 *     named in the EDGE's direction, which is the reverse of the join's
 *  3. broken  -> stg_customers   : composite, and also lineage that was
 *     INFERRED from view SQL (that one edge's provenance is doctored here,
 *     since every edge in the frozen export is a manifest edge)
 *
 * And three semantic states: annotated, declared-but-bare, and unclaimed.
 */
async function osiDoc(): Promise<Record<string, unknown>> {
  const doc = JSON.parse(await readFile(FIXTURE, "utf8")) as {
    joins: unknown[];
    edges: { src: string; dst: string; provenance: string }[];
    objects: { key: string; semantic: unknown }[];
  };
  doc.joins = [
    {
      name: "revenue_customer",
      many: "mart.mart__revenue",
      one: "mart.dim__customers",
      cardinality: "many_to_one",
      keys: [["customer_id", "id"]],
      composite: false,
      provenance: "declared",
      lineage_edge: null,
    },
    {
      name: "revenue_staging_customer",
      many: "mart.mart__revenue",
      one: "staging.stg_customers",
      cardinality: "many_to_one",
      keys: [["customer_id", "id"]],
      composite: false,
      provenance: "declared",
      lineage_edge: ["staging.stg_customers", "mart.mart__revenue"],
    },
    {
      name: "broken_staging_customer",
      many: "mart.mart__broken",
      one: "staging.stg_customers",
      cardinality: "many_to_one",
      keys: [
        ["id", "id"],
        ["name", "name"],
      ],
      composite: true,
      provenance: "declared",
      lineage_edge: ["staging.stg_customers", "mart.mart__broken"],
    },
  ];
  const inferred = doc.edges.find(
    (e) => e.src === "staging.stg_customers" && e.dst === "mart.mart__broken",
  )!;
  inferred.provenance = "view_sql";
  const semantic: Record<string, unknown> = {
    "mart.mart__revenue": {
      name: "Revenue",
      primary_key: ["id"],
      unique_keys: [["customer_id", "recognised_on"]],
      instructions: "Recognised revenue by customer and day. Amounts are USD cents.",
      synonyms: ["sales", "bookings"],
      example_queries: ["select channel, sum(amount) from mart.mart__revenue group by 1"],
    },
    // Named by the model, annotated by nobody — a DIFFERENT fact from null.
    "mart.dim__customers": {
      name: "Customers",
      primary_key: ["id"],
      unique_keys: [],
      instructions: null,
      synonyms: [],
      example_queries: [],
    },
  };
  for (const object of doc.objects) object.semantic = semantic[object.key] ?? null;
  return doc as unknown as Record<string, unknown>;
}

async function serveOsi(page: Page): Promise<void> {
  const doc = await osiDoc();
  await page.route("**/city.json*", (route) =>
    route.fulfill({ contentType: "application/json", body: JSON.stringify(doc) }),
  );
}

test("the declared dataset lands in the inspector with its keys and context", async ({ page }) => {
  await serveOsi(page);
  const errors = await open(page, "?settle=1");
  await page.evaluate(() => window.__tycoonCity!.select("mart.mart__revenue"));

  const panel = await page.locator("#inspector").innerText();
  expect(panel.toLowerCase()).toContain("semantic (osi)"); // the h3 is upper-cased by CSS
  expect(panel).toContain("Revenue"); // the business name, not the table's
  expect(panel).toContain("Recognised revenue by customer and day");
  expect(panel).toContain("sales");
  expect(panel).toContain("bookings");
  expect(panel).toContain("select channel, sum(amount)");
  expect(panel.toLowerCase()).toContain("unique keys");
  expect(panel).toContain("customer_id, recognised_on"); // the unique key
  expect(errors).toEqual([]);
});

test("declared-but-bare and unclaimed are DIFFERENT states, and both are named", async ({
  page,
}) => {
  await serveOsi(page);
  await open(page, "?settle=1");

  // Named by the semantic model, annotated by nobody.
  await page.evaluate(() => window.__tycoonCity!.select("mart.dim__customers"));
  const bare = await page.locator("#inspector").innerText();
  expect(bare).toContain("Customers");
  expect(bare).toContain("declared, not yet annotated");

  // No dataset claims it at all. With a semantic model in the document that is
  // a finding, so it is stated rather than left blank.
  await page.evaluate(() => window.__tycoonCity!.select("mart.mart__forgotten"));
  const unclaimed = await page.locator("#inspector").innerText();
  expect(unclaimed).toContain("no declared dataset");
  expect(unclaimed).not.toContain("not yet annotated");
});

test("a join names the other object, the direction, the key pairs — and its provenance", async ({
  page,
}) => {
  await serveOsi(page);
  await open(page, "?settle=1");
  await page.evaluate(() => window.__tycoonCity!.select("mart.mart__revenue"));

  const panel = await page.locator("#inspector").innerText();
  expect(panel.toLowerCase()).toContain("declared joins (2)");
  expect(panel).toContain("mart.dim__customers");
  expect(panel).toContain("staging.stg_customers");
  expect(panel).toContain("this object is the many side");
  expect(panel).toContain("on customer_id → id");
  // A join is DECLARED. Never "measured", never bare.
  expect(panel).toContain("declared (OSI)");

  // The pair with no lineage says exactly that — it is not a claim that data
  // moved, and it must not be readable as one.
  expect(panel).toContain("no lineage on this pair — declared join only");
  // The pair that DOES have lineage names the edge in the EDGE's direction
  // (the reverse of the join's) with the edge's own provenance label.
  expect(panel).toContain("also lineage staging.stg_customers → mart.mart__revenue");
  expect(panel).toContain("declared (dbt)");

  // The markers follow the model graph's vocabulary exactly: solid for the
  // declared lineage, dashed for the pair that has none.
  expect(await page.locator("#inspector .lin.dash").count()).toBe(1);
  expect(await page.locator("#inspector .lin:not(.dash)").count()).toBe(1);
});

test("inferred lineage under a join is drawn DASHED, like the model graph", async ({ page }) => {
  await serveOsi(page);
  await open(page, "?settle=1");
  await page.evaluate(() => window.__tycoonCity!.select("mart.mart__broken"));

  const panel = await page.locator("#inspector").innerText();
  expect(panel.toLowerCase()).toContain("declared joins (1)");
  expect(panel).toContain("on id → id, name → name");
  expect(panel).toContain("composite");
  // Declared JOIN over INFERRED lineage: the two provenances sit side by side
  // and neither borrows the other's strength.
  expect(panel).toContain("declared (OSI)");
  expect(panel).toContain("inferred (SQL scan)");
  expect(await page.locator("#inspector .lin.dash").count()).toBe(1);
  expect(await page.locator("#inspector .lin:not(.dash)").count()).toBe(0);
});

test("the one side sees the join too, and every object name is a door", async ({ page }) => {
  await serveOsi(page);
  await open(page, "?settle=1");
  await page.evaluate(() => window.__tycoonCity!.select("staging.stg_customers"));

  const panel = await page.locator("#inspector").innerText();
  expect(panel.toLowerCase()).toContain("declared joins (2)"); // revenue and broken point at it
  expect(panel).toContain("this object is the one side");

  await page.locator('#inspector ul.joins .door[data-key="mart.mart__revenue"]').click();
  await page.waitForTimeout(900); // the glide
  expect(await page.evaluate(() => window.__tycoonCity!.selectedKey())).toBe("mart.mart__revenue");
});

test("an object a semantic model touches nowhere still says so", async ({ page }) => {
  await serveOsi(page);
  await open(page, "?settle=1");
  await page.evaluate(() => window.__tycoonCity!.select("scratch.experiment"));

  const panel = await page.locator("#inspector").innerText();
  expect(panel).toContain("no declared dataset");
  expect(panel).toContain("none declared"); // the joins list
});

test("a PRE-OSI document says nothing about semantics at all", async ({ page }) => {
  // The frozen fixture, untouched: joins [] and semantic null everywhere,
  // which is the honest state of most catalogs. With no semantic model in the
  // document there is no absence to report, and reporting one on every
  // building would be noise dressed as rigour.
  await page.route("**/city.json*", (route) => route.fulfill({ path: FIXTURE }));
  const errors = await open(page, "?settle=1");
  await page.evaluate(() => window.__tycoonCity!.select("mart.mart__revenue"));

  const panel = await page.locator("#inspector").innerText();
  expect(panel.toLowerCase()).not.toContain("semantic (osi)");
  expect(panel.toLowerCase()).not.toContain("declared joins");
  expect(panel).not.toContain("no declared dataset");
  expect(errors).toEqual([]);
});
