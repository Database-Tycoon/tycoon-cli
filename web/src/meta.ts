/**
 * `meta.json` — how old the picture in front of you actually is.
 *
 * THE BUG THIS EXISTS FOR: the footer's age used to be measured from the
 * moment the browser fetched `city.json`. That is exactly right for the live
 * server, which builds the document for the request that asked for it, and
 * exactly wrong for a static export — a week-old `city.json` sitting on a CDN
 * read "as of 3s ago", which is a freshness claim nobody made.
 *
 * `city.json` cannot carry the fix. It is byte-stable by law
 * (`docs/city-json-v1.md`): no uuid, no timestamp, no path, no seed, which is
 * what makes a committed golden and a cross-language contract test possible.
 * So the export time rides in a SIBLING document, exactly as `runs.json` does,
 * and `tycoon-city-export` writes it next to the city.
 *
 * THE THREE STATES, and all three are named rather than guessed at:
 *
 *   1. `meta.json` with a `generated_at`  → "exported 6 days ago". The
 *      producer's own time, which is the only one that can be right.
 *   2. `meta.json` with `generated_at: null` → the live server saying it has
 *      no export time to give, because the document was built for this fetch.
 *   3. no `meta.json` at all (404) — an export written before this document
 *      existed, or a hand-assembled directory.
 *
 * 2 and 3 land on the same fallback: "as of Ns ago", measured from the fetch,
 * with a title that says that is what it is. **A malformed or unreadable
 * `meta.json` also lands there**, deliberately — this module never throws and
 * never blocks the city, because a bad sidecar must not cost you the map.
 */

/** Where the age on the footer is measured from. */
export type Freshness =
  /** The producer's own stamp: `tycoon-city-export` wrote city.json at `at`. */
  | { kind: "exported"; at: number }
  /** All we can know: the browser fetched city.json at `at`. */
  | { kind: "fetched"; at: number };

/**
 * The `generated_at` in a parsed `meta.json` body, as epoch ms — or null for
 * every shape that does not carry one.
 *
 * Hand-rolled rather than zod on purpose. The city document is validated
 * strictly because a malformed one must fail loudly at load instead of as NaN
 * geometry three frames later; this one has the opposite requirement, where
 * every unrecognised shape has a correct fallback already. So the rule is
 * simply: a string that `Date.parse` understands, or nothing.
 */
export function generatedAtOf(body: unknown): number | null {
  if (typeof body !== "object" || body === null) return null;
  const raw = (body as { generated_at?: unknown }).generated_at;
  if (typeof raw !== "string") return null; // includes the server's explicit null
  const at = Date.parse(raw);
  return Number.isFinite(at) ? at : null;
}

/**
 * Read the sidecar and decide which clock the footer counts from.
 *
 * `fetchedAt` is when `city.json` came back, and it is passed in rather than
 * measured here so the fallback describes the CITY's fetch, not this one.
 * Nothing in here can reject: a 404, a 500, an offline host, HTML from a
 * catch-all route, or a truncated body all mean "no export time", which is a
 * state this app knows how to display.
 */
export async function loadFreshness(url: string, fetchedAt: number): Promise<Freshness> {
  try {
    const response = await fetch(url);
    if (!response.ok) return { kind: "fetched", at: fetchedAt };
    const at = generatedAtOf(await response.json());
    return at === null ? { kind: "fetched", at: fetchedAt } : { kind: "exported", at };
  } catch {
    return { kind: "fetched", at: fetchedAt };
  }
}

/**
 * An age a human reads at a glance, coarsening as it grows: seconds while you
 * are watching a pipeline, days when you are looking at last week's export.
 *
 * Days FLOOR rather than round — "6 days ago" for anything in the sixth day
 * understates by less than a day, where rounding would let a 36-hour-old
 * export claim two. A negative age (a producer clock ahead of the viewer's)
 * clamps to zero rather than rendering a city from the future.
 */
export function humanAge(ms: number): string {
  const s = Math.max(0, Math.round(ms / 1000));
  if (s < 90) return `${s}s`;
  const m = Math.round(s / 60);
  if (m < 90) return `${m}m`;
  const h = Math.round(s / 3600);
  if (h < 36) return `${h}h`;
  const d = Math.floor(s / 86400);
  return d === 1 ? "1 day" : `${d} days`;
}

/**
 * The footer line. The VERB is the load-bearing part: "exported" is the
 * producer's claim about the document, "as of" is the viewer's claim about its
 * own fetch, and a reader must be able to tell which one they are being given
 * without opening the network tab.
 */
export function freshnessLabel(freshness: Freshness, now: number): string {
  const age = humanAge(now - freshness.at);
  return freshness.kind === "exported" ? `exported ${age} ago` : `as of ${age} ago`;
}

/** The hover text, where the absence gets named in full. */
export function freshnessTitle(freshness: Freshness): string {
  return freshness.kind === "exported"
    ? `city.json was exported at ${new Date(freshness.at).toISOString()} (from meta.json)`
    : "no export time available: this is when your browser fetched city.json, " +
        "which is the document's own age only when a server generated it for you";
}
