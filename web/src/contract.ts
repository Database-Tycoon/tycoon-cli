/**
 * The client side of `city.json` v1. `docs/city-json-v1.md` is normative; this
 * module is its consumer and must never invent structure the document does not
 * guarantee. Validation is zod so a malformed document fails at load with a
 * named path instead of as NaN geometry three frames later.
 */

import { z } from "zod";

export const FORMAT = "database-tycoon.city";
export const VERSION = 1;

const box = z.object({
  min_x: z.number().int(),
  min_y: z.number().int(),
  max_x: z.number().int(),
  max_y: z.number().int(),
});

// Streets v2 (2026-08-05): districts are bounding rects around a schema's
// lots, not ring-placed squares — w/h replaced `size` and `ring`.
const district = z.object({
  schema: z.string(),
  x: z.number().int(),
  y: z.number().int(),
  w: z.number().int().positive(),
  h: z.number().int().positive(),
});

const lot = z.object({
  object_key: z.string(),
  x: z.number().int(),
  y: z.number().int(),
  // Ground plan in tiles, NW-anchored: big tables (top decile of the
  // catalog's row counts) are 2x2, everything else 1x1.
  w: z.number().int().min(1),
  h: z.number().int().min(1),
  zone_style: z.enum(["industrial", "commercial", "residential"]),
  target_density: z.number().int().min(1).max(8),
  powered: z.boolean(),
  // Temporal signals; null = UNKNOWN, and unknown renders as full colour,
  // no tint, no marker — never as stale.
  last_build_age_s: z.number().nullable(),
  build_status: z.string().nullable(),
  test_status: z.string().nullable(),
  freshness_status: z.string().nullable(), // dbt's SLA verdict for sources
  schema_drift_age_s: z.number().nullable(), // seconds since schema change
});

/**
 * How often an object appears in observed runs — the traffic that justifies
 * its building.
 *
 * `source` is a DISCRIMINATOR, not decoration: `"runs"` is build/run usage,
 * which is all vanilla DuckDB can measure (there is no query log). A
 * MotherDuck or Snowflake build reading a real query history emits
 * `"queries"`, and a client switching on this field never has to guess which
 * one it is looking at. Kept a plain string so an unknown source is a
 * forward-compatible no-op.
 *
 * `rate_per_day` is null with fewer than two appearances or a zero span —
 * unknown cadence, never a guess from one data point.
 */
const usage = z.object({
  source: z.string(),
  runs_seen: z.number().int().nonnegative(),
  window_days: z.number().nonnegative(),
  rate_per_day: z.number().nullable(),
});

/**
 * `objects[].semantic` — the OSI Dataset that CLAIMS this object, or null.
 *
 * Null means no dataset declares it at all. A block whose `instructions` is
 * null and whose lists are empty is a DIFFERENT fact — a dataset someone named
 * without annotating — and the inspector renders the two differently: the
 * first is an undocumented building, the second a documented one with no
 * signage yet. Collapsing them would turn "nobody has looked at this" into
 * "somebody looked and found nothing to say".
 *
 * Every list carries a default so a producer that omits one degrades to an
 * empty shelf rather than failing the whole city at load.
 */
const semantic = z.object({
  // The business name, often not the table's — the nameplate over the lobby.
  name: z.string(),
  primary_key: z.array(z.string()).optional().default([]),
  unique_keys: z.array(z.array(z.string())).optional().default([]),
  instructions: z.string().nullable().optional().default(null),
  synonyms: z.array(z.string()).optional().default([]),
  example_queries: z.array(z.string()).optional().default([]),
});

const objectRecord = z.object({
  key: z.string(),
  schema: z.string(),
  name: z.string(),
  kind: z.enum(["table", "view"]),
  row_count: z.number().int().nonnegative(),
  // Measured schema: (name, type) in table order; description declared by
  // dbt (null = undocumented); test_status = worst column-test verdict.
  columns: z.array(
    z.object({
      name: z.string(),
      type: z.string(),
      description: z.string().nullable(),
      test_status: z.string().nullable(),
    }),
  ),
  // dbt's declared semantics; null when dbt does not manage the object.
  dbt: z
    .object({
      description: z.string(),
      materialized: z.string(),
      tags: z.array(z.string()),
      owner: z.string().nullable(),
      tests: z.array(
        z.object({
          name: z.string(),
          column: z.string().nullable(),
          status: z.string().nullable(), // null = declared but never run
        }),
      ),
    })
    .nullable(),
  // Measured run appearances (2026-08-06). Optional with a null default for
  // the same reason `street_features` is: documents written before the seam
  // landed omit the key and must keep validating.
  //
  // **null is UNKNOWN, never "unused."** A client that renders a null `usage`
  // as a quiet building has invented a fact the document does not carry.
  usage: usage.nullable().optional().default(null),
  // The declared OSI dataset for this object (2026-08-06). Optional with a
  // null default: documents written before the OSI loader omit the key.
  semantic: semantic.nullable().optional().default(null),
});

const edge = z.object({
  src: z.string(),
  dst: z.string(),
  rate: z.number().min(0).max(1),
  provenance: z.enum(["manifest", "duckdb", "view_sql"]),
  // Streets ARE the lineage: the exact tile path this edge's street takes.
  route: z.array(z.tuple([z.number().int(), z.number().int()])),
  // Column-level lineage: [src_col, dst_col] pairs — the skybridges.
  columns: z.array(z.tuple([z.string(), z.string()])),
  // Expected warehouse-seconds/day this street carries (dst's measured build
  // cadence x mean cost) — the road-load overlay. null = history can't say.
  daily_load_s: z.number().nullable(),
});

/**
 * `joins[]` — DECLARED joins from an OSI semantic model, deliberately NOT
 * folded onto `edges`.
 *
 * The two are different claims. An edge asserts *data moved here at build
 * time*; a join asserts *these two are formally joinable*, which is true
 * whether or not a build ever ran between them — the common case being a
 * dimension every query joins and no build ever reads. A client that reads
 * `edges` and ignores `joins` therefore renders exactly what it always did,
 * and a client that reads both must never let one wear the other's provenance.
 *
 * `lineage_edge` is what reconciles them: when the same pair also has lineage
 * it names that edge IN THE EDGE'S OWN DIRECTION, which is usually the reverse
 * of the join's (the dimension flows *into* the fact while the join points *at*
 * the dimension). Null means the pair has no measured lineage at all.
 *
 * `cardinality` and `provenance` are plain strings, not enums, for the same
 * forward-compatible reason `street_feature.kind` is: today the spec has only
 * `many_to_one` and only `declared`, and a newer producer must not be able to
 * fail the whole document by inventing a third word.
 */
const join = z.object({
  name: z.string(),
  many: z.string(),
  one: z.string(),
  cardinality: z.string(),
  // [many-side column, one-side column] pairs, in declaration order.
  keys: z.array(z.tuple([z.string(), z.string()])),
  // Declared by the producer, never derived here: a renderer keys its
  // double-marked crossing off one field.
  composite: z.boolean(),
  provenance: z.string(),
  lineage_edge: z.tuple([z.string(), z.string()]).nullable().optional().default(null),
});

/** Human labels for edge provenance: declared lineage vs inferred. */
export const PROVENANCE_LABEL: Record<z.infer<typeof edge>["provenance"], string> = {
  manifest: "declared (dbt)",
  duckdb: "declared (duckdb)",
  view_sql: "inferred (SQL scan)",
};

/**
 * Streets v4 dressed endings (`docs/road-grammar.md` theme 7: "terminations
 * are dressed, never raw"). The planner names WHERE a treatment goes and the
 * renderer decides what it looks like.
 *
 * `kind` is deliberately a plain string, not an enum: the frozen v4 kinds are
 * apron / dock / plaza, and an unknown kind must be a forward-compatible
 * NO-OP (a newer planner emitting `bulb` renders nothing rather than failing
 * the whole document at load). `facing` is the direction the treatment faces
 * — for an apron/dock, toward the building it serves — and null when the
 * treatment has no direction (a plaza pad). `w`/`h` are tile extents,
 * NW-anchored at (x, y) exactly like `lots`.
 */
const streetFeature = z.object({
  kind: z.string(),
  x: z.number().int(),
  y: z.number().int(),
  facing: z.enum(["n", "e", "s", "w"]).nullable(),
  w: z.number().int().positive(),
  h: z.number().int().positive(),
});

/**
 * The compute bill: measured load at a DECLARED rate (`docs/city-json-v1.md`).
 *
 * The two zeros a client must keep apart: `daily_cost: 0` with a non-null
 * `daily_load_s` is a FACT (local DuckDB is free, and `note` says so), while
 * a null `daily_load_s`/`daily_cost` means nothing could be priced. Render
 * the second as unknown, never as a paid-nothing bill.
 *
 * `price_source` is the provenance of the one number here that was not
 * measured. Show it wherever the cost is shown.
 */
const budget = z.object({
  engine: z.string(),
  currency: z.string(),
  unit_price_per_s: z.number().nonnegative(),
  price_source: z.string(),
  daily_load_s: z.number().nullable(),
  daily_cost: z.number().nullable(),
  priced_objects: z.number().int().nonnegative(),
  unpriced_objects: z.number().int().nonnegative(),
  by_object: z.array(
    z.object({
      object_key: z.string(),
      daily_load_s: z.number(),
      daily_cost: z.number(),
    }),
  ),
  note: z.string(),
});

/**
 * Source freshness as weather. One cell per district a JUDGED source reaches
 * — including `clear`, which is a positive assertion ("judged sources reach
 * this district and none is late") rather than an absence.
 *
 * `condition` is a plain string, not an enum, for the same forward-compat
 * reason `street_feature.kind` is: an unknown condition must be a no-op, not
 * a failed load. `clear` draws nothing.
 *
 * A district with NO cell has no judged source upstream — the client must not
 * fill that in with fair weather. `cells: []` with a note is the
 * nothing-was-judged case: render no weather at all, and show the note.
 */
const weatherCell = z.object({
  schema: z.string(),
  condition: z.string(),
  worst_source: z.string().nullable(),
  verdict: z.string().nullable(),
  hops: z.number().int().nullable(),
});

const weather = z.object({
  cells: z.array(weatherCell),
  note: z.string(),
});

const replay = z.object({
  span_ticks: z.number().int().positive(),
  note: z.string(), // "durations measured, ordering reconstructed" — display it
  steps: z.array(
    z.object({
      object_key: z.string(),
      start: z.number().int().nonnegative(),
      duration: z.number().int().positive(),
    }),
  ),
});

export const citySchema = z.object({
  format: z.literal(FORMAT),
  version: z.literal(VERSION),
  database: z.object({
    name: z.string(),
    object_count: z.number().int().nonnegative(),
    total_rows: z.number().int().nonnegative(),
    has_known_edges: z.boolean(),
    // The degradation ladder's messages (missing manifest, locked metadata…);
    // shown in the footer so a named absence never reads as a broken feature.
    notes: z.array(z.string()),
  }),
  grid: z.object({
    width: z.number().int().positive(),
    height: z.number().int().positive(),
    tile_kinds: z.array(z.string()),
    tiles_rle: z.array(z.number().int().nonnegative()),
  }),
  plant: z.object({ x: z.number().int(), y: z.number().int() }),
  focus: box,
  districts: z.array(district),
  lots: z.array(lot),
  objects: z.array(objectRecord),
  edges: z.array(edge),
  // Declared OSI joins (2026-08-06). Optional with a [] default for the same
  // reason `street_features` is: documents predating the seam must keep
  // validating, and `[]` is also the honest value for the many catalogs with
  // no semantic model at all.
  joins: z.array(join).optional().default([]),
  // The measured blocks (2026-08-06). Optional with a null default so every
  // document written before they landed — the committed golden and the web
  // fixtures included — keeps validating without a version check.
  //
  // `budget` is null when the run history knows nothing: that is UNKNOWN, and
  // a client must not draw it as a free city. `weather` is an object even
  // when nothing was judged, and its `note` is the named absence to show.
  budget: budget.nullable().optional().default(null),
  weather: weather.nullable().optional().default(null),
  street_features: z.array(streetFeature).optional().default([]),
  // Civic buildings (2026-08-05, additive): the public library (context /
  // documentation inventory) and the firehouse (fire-response dispatch).
  library: z.object({ x: z.number().int(), y: z.number().int() }).nullable(),
  firehouse: z.object({ x: z.number().int(), y: z.number().int() }).nullable(),
  // The last run as a playable schedule; null when there is no history or it
  // does not match this catalog (the server refuses rather than misleads).
  replay: replay.nullable(),
  theme: z.object({
    name: z.string(),
    logo_text: z.string(),
    labels: z.record(z.string(), z.string()),
    colors: z.record(z.string(), z.array(z.number())),
    sprites: z.record(z.string(), z.array(z.number())),
    spritesheet: z.string(),
  }),
});

export type CityDocument = z.infer<typeof citySchema>;
export type LotRecord = z.infer<typeof lot>;
export type DistrictRecord = z.infer<typeof district>;
export type ObjectRecord = z.infer<typeof objectRecord>;
export type EdgeRecord = z.infer<typeof edge>;
export type StreetFeatureRecord = z.infer<typeof streetFeature>;
export type UsageRecord = z.infer<typeof usage>;
export type BudgetRecord = z.infer<typeof budget>;
export type WeatherRecord = z.infer<typeof weather>;
export type WeatherCellRecord = z.infer<typeof weatherCell>;
export type JoinRecord = z.infer<typeof join>;
export type SemanticRecord = z.infer<typeof semantic>;
export type ColumnRecord = ObjectRecord["columns"][number];

export const requestSchema = z.object({
  request_id: z.string().uuid(),
  citizen_id: z.string(),
  timestamp: z.string().datetime(),
  priority: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
  request_type: z.enum(["DATA_SOURCE", "SCHEMA_CHANGE", "QUALITY_FIX", "PERFORMANCE"]),
  description: z.string(),
  status: z.enum(["PENDING", "IN_PROGRESS", "FULFILLED", "EXPIRED"]),
  complexity: z.number().int().min(1).max(10),
});
export type RequestRecord = z.infer<typeof requestSchema>;

/**
 * Whether this document carries a semantic model at all.
 *
 * The inspector needs it to tell two absences apart: with no OSI model, a null
 * `semantic` is simply not a subject and saying so on every building would be
 * noise; with one, a null `semantic` means "the semantic model does not
 * mention this object", which is a finding and stays named.
 */
export function hasSemanticModel(doc: CityDocument): boolean {
  return doc.joins.length > 0 || doc.objects.some((o) => o.semantic !== null);
}

/** The declared joins touching `key`, with the OTHER endpoint resolved and
 * which side of the many→one this object sits on. Straight from `joins`; no
 * direction is inferred here. */
export function joinsOf(
  doc: CityDocument,
  key: string,
): { join: JoinRecord; other: string; side: "many" | "one" }[] {
  return doc.joins
    .filter((j) => j.many === key || j.one === key)
    .map((j) =>
      j.many === key
        ? { join: j, other: j.one, side: "many" as const }
        : { join: j, other: j.many, side: "one" as const },
    );
}

/** Type families for the facade window palette: one hue per family. */
export function typeFamily(sqlType: string): "numeric" | "text" | "temporal" | "boolean" | "nested" | "other" {
  const t = sqlType.toUpperCase();
  if (/INT|DECIMAL|NUMERIC|DOUBLE|FLOAT|REAL|HUGE/.test(t)) return "numeric";
  if (/CHAR|TEXT|STRING|UUID/.test(t)) return "text";
  if (/DATE|TIME/.test(t)) return "temporal";
  if (/BOOL/.test(t)) return "boolean";
  if (/JSON|STRUCT|LIST|MAP|ARRAY|UNION/.test(t)) return "nested";
  return "other";
}

/**
 * Decode the row-major run-length pairs into one flat Uint8Array of kind ids,
 * row-major, `width * height` long. Runs cross row boundaries by design.
 *
 * The count check mirrors the Python `decode_rle`: a truncated document must
 * fail here, not render as a subtly shifted map.
 */
export function decodeRle(runs: readonly number[], width: number, height: number): Uint8Array {
  if (runs.length % 2 !== 0) {
    throw new Error(`tiles_rle must hold (kind, run) pairs; got ${runs.length} numbers`);
  }
  const flat = new Uint8Array(width * height);
  let at = 0;
  for (let i = 0; i < runs.length; i += 2) {
    const kind = runs[i]!;
    const run = runs[i + 1]!;
    if (run < 1) throw new Error(`run length must be positive; got ${run}`);
    if (at + run > flat.length) {
      throw new Error(`tiles_rle decodes past ${flat.length} cells`);
    }
    flat.fill(kind, at, (at += run));
  }
  if (at !== flat.length) {
    throw new Error(`tiles_rle decodes to ${at} cells, expected ${flat.length}`);
  }
  return flat;
}

export async function loadCity(url: string): Promise<CityDocument> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`fetching ${url}: HTTP ${response.status}`);
  return citySchema.parse(await response.json());
}

export interface LineageEntry {
  key: string;
  provenance: EdgeRecord["provenance"];
}

/** Lineage neighbours of an object with each edge's provenance, straight from
 * the edge list — the inspector labels declared vs inferred per entry. */
export function lineageOf(
  doc: CityDocument,
  key: string,
): { upstream: LineageEntry[]; downstream: LineageEntry[] } {
  return {
    upstream: doc.edges
      .filter((e) => e.dst === key)
      .map((e) => ({ key: e.src, provenance: e.provenance })),
    downstream: doc.edges
      .filter((e) => e.src === key)
      .map((e) => ({ key: e.dst, provenance: e.provenance })),
  };
}
