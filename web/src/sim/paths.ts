/**
 * Port of `tycoon_city.sim.paths.manhattan_path`: x leg first, then y leg,
 * inclusive of both endpoints. Vehicles ride these, and the generator paved
 * ROAD along exactly these cells — matching its leg order is what keeps
 * vehicles on the pavement instead of cutting the corner the road goes around.
 */

export type Tile = readonly [number, number];

export function manhattanPath(a: Tile, b: Tile): Tile[] {
  const [x1, y1] = b;
  let [x, y] = a;
  const path: Tile[] = [[x, y]];
  while (x !== x1) {
    x += x1 > x ? 1 : -1;
    path.push([x, y]);
  }
  while (y !== y1) {
    y += y1 > y ? 1 : -1;
    path.push([x, y]);
  }
  return path;
}
