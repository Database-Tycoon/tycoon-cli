/**
 * The ground: one quad, one draw call, however large the catalog.
 *
 * Two paths, chosen per the plan's de-risking order:
 *
 * - **Atlas (default):** an R8 DataTexture holds one kind id per tile
 *   (905^2 = 0.8 MB, far under any texture limit); the fragment shader reads
 *   the id under each fragment and samples the matching 16x16 cell of a small
 *   runtime atlas built from the theme spritesheet. Do NOT pre-bake a canvas at
 *   sprite resolution (905*16 px exceeds common GPU limits) and do NOT instance
 *   819k tile quads. Unlit on purpose: the sprites carry their own shading,
 *   exactly like the 2D map.
 * - **Flat (?flat=1):** the CPU-baked palette texture. The e2e suite counts
 *   exact-colour pixels in this mode, so it must stay byte-predictable — atlas
 *   art would make those counts meaningless.
 *
 * A large grass skirt sits just below the grid: ground past the city's edge is
 * unbuilt land, not a boundary — the same policy the 2D renderer implements by
 * painting GRASS outside the grid — and it is what prevents a void at low
 * camera angles. In atlas mode the skirt repeats a 2x2-tile checker pattern,
 * phase-aligned to the grid's own (x + y) parity so no seam shows at the
 * boundary.
 */

import * as THREE from "three";
import type { CityDocument } from "../contract";
import { loadImage, buildAtlasTerrain } from "./terrain_atlas";
import { buildFlatTerrain } from "./terrain_flat";

export { loadImage };

/** `sheet` is required in atlas mode; pass nothing with `flat` to get the
 * palette path the pixel tests count on. */
export function buildTerrain(
  doc: CityDocument,
  flat = false,
  sheet?: HTMLImageElement,
): THREE.Group {
  if (!flat && sheet) return buildAtlasTerrain(doc, sheet);
  return buildFlatTerrain(doc);
}
