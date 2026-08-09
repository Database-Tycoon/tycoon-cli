/**
 * Seeded randomness for the client-side tick. mulberry32 per the plan;
 * bit-equality with Python's `random.Random` is an explicit non-goal — the
 * traffic layer is presentation, so only determinism *within* the client
 * matters (same seed → same vehicles → screenshot-stable).
 */

export type Rng = () => number;

export function mulberry32(seed: number): Rng {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** FNV-1a, so `database.name` can seed the RNG the way the Python engine
 * seeds `random.Random(ctx.database_name)` — stable across reloads. */
export function hashSeed(text: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}
