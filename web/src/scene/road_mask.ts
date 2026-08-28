/**
 * The road-connectivity mask: for every ROAD tile, which of its four edges
 * face another road tile (OPEN) and which face something else (CLOSED).
 *
 * One definition, two consumers, on purpose. `terrain.ts` picks the tile's
 * painted variant from it (curbs drawn only on closed edges, so adjacent road
 * tiles fuse into one asphalt surface); `streetscape.ts` extrudes the REAL
 * sidewalk curb along exactly those same closed edges. Duplicating the
 * adjacency rule would let the paint and the geometry drift apart — the
 * failure mode would be a curb standing in the middle of a fused junction.
 *
 * Bit order is the wire order the atlas cells were drawn in and must not be
 * reordered: 1=N (world y-1), 2=E (x+1), 4=S (y+1), 8=W (x-1).
 */

import type { CityDocument } from "../contract";
import { decodeRle } from "../contract";

export const ROAD_N = 1;
export const ROAD_E = 2;
export const ROAD_S = 4;
export const ROAD_W = 8;

/** The four edges in bit order with their tile-space offsets. */
export const ROAD_EDGES = [
  { bit: ROAD_N, dx: 0, dy: -1 },
  { bit: ROAD_E, dx: 1, dy: 0 },
  { bit: ROAD_S, dx: 0, dy: 1 },
  { bit: ROAD_W, dx: -1, dy: 0 },
] as const;

export interface RoadMask {
  width: number;
  height: number;
  /** Row-major, `width * height`: the adjacency mask on road tiles, 0
   * elsewhere. A mask of 0 on a road tile means an isolated tile (all four
   * edges closed), so read `isRoad` — never `masks[i] !== 0` — to test for
   * road. */
  masks: Uint8Array;
  isRoad: (x: number, y: number) => boolean;
  maskAt: (x: number, y: number) => number;
}

/** Decode the grid once and compute every road tile's adjacency mask. */
export function roadMask(doc: CityDocument): RoadMask {
  const { width, height } = doc.grid;
  const cells = decodeRle(doc.grid.tiles_rle, width, height);
  const roadId = doc.grid.tile_kinds.indexOf("road");
  const isRoad = (x: number, y: number): boolean =>
    x >= 0 && y >= 0 && x < width && y < height && cells[y * width + x] === roadId;

  const masks = new Uint8Array(width * height);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (!isRoad(x, y)) continue;
      let mask = 0;
      for (const { bit, dx, dy } of ROAD_EDGES) {
        if (isRoad(x + dx, y + dy)) mask |= bit;
      }
      masks[y * width + x] = mask;
    }
  }

  return {
    width,
    height,
    masks,
    isRoad,
    maskAt: (x, y) => (isRoad(x, y) ? masks[y * width + x]! : 0),
  };
}
