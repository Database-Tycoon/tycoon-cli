/**
 * The drivable network — ONE rule for every vehicle in the city (Stephen,
 * 2026-08-05: "all vehicles in the game are subject to that rule").
 *
 * Drivable = ROAD, plus building LOTS (streets terminate ON their buildings,
 * so lots are the junctions that stitch streets together), plus POWER_LINE
 * (the utility corridor is the paved strip everything uses to leave the
 * plant and the civic buildings). Grass is never drivable. Anything the
 * network cannot reach simply is not visited — no vehicle teleports.
 *
 * BFS with a fixed neighbour order, so paths are deterministic.
 */

import type { CityDocument } from "../contract";
import { decodeRle } from "../contract";
import type { Tile } from "./paths";

const STEPS = [
  [1, 0],
  [0, -1],
  [0, 1],
  [-1, 0],
] as const;

export class RoadNet {
  private drivable: Uint8Array;
  private width: number;
  private height: number;

  constructor(doc: CityDocument) {
    this.width = doc.grid.width;
    this.height = doc.grid.height;
    const flat = decodeRle(doc.grid.tiles_rle, this.width, this.height);
    const ids = new Set(
      ["road", "lot", "power_line"]
        .map((kind) => doc.grid.tile_kinds.indexOf(kind))
        .filter((id) => id >= 0),
    );
    this.drivable = new Uint8Array(flat.length);
    for (let i = 0; i < flat.length; i += 1) {
      this.drivable[i] = ids.has(flat[i]!) ? 1 : 0;
    }
  }

  isDrivable(x: number, y: number): boolean {
    return (
      x >= 0 &&
      y >= 0 &&
      x < this.width &&
      y < this.height &&
      this.drivable[y * this.width + x] === 1
    );
  }

  /** Shortest drivable path from `start` to any goal tile, or null. The
   * start itself need not be drivable (a station door, the plant). */
  path(start: Tile, goals: Tile[]): Tile[] | null {
    const goalSet = new Set(goals.map(([x, y]) => `${x},${y}`));
    if (!goalSet.size) return null;
    const key = (t: Tile) => `${t[0]},${t[1]}`;
    if (goalSet.has(key(start))) return [start];
    const came = new Map<string, Tile>([[key(start), start]]);
    const frontier: Tile[] = [start];
    let found: Tile | null = null;
    while (frontier.length && !found) {
      const [cx, cy] = frontier.shift()!;
      for (const [dx, dy] of STEPS) {
        const next: Tile = [cx + dx, cy + dy];
        const k = key(next);
        if (came.has(k) || !this.isDrivable(next[0], next[1])) continue;
        came.set(k, [cx, cy]);
        if (goalSet.has(k)) {
          found = next;
          break;
        }
        frontier.push(next);
      }
    }
    if (!found) return null;
    const path: Tile[] = [found];
    while (key(path[path.length - 1]!) !== key(start)) {
      path.push(came.get(key(path[path.length - 1]!))!);
    }
    return path.reverse();
  }
}
