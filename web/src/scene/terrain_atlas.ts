/**
 * Atlas terrain: runtime atlas, shader-based rendering.
 *
 * An R8 DataTexture holds one kind id per tile (905^2 = 0.8 MB, far under any
 * texture limit); the fragment shader reads the id under each fragment and
 * samples the matching 16x16 cell of a small runtime atlas built from the
 * theme spritesheet. Do NOT pre-bake a canvas at sprite resolution (905*16 px
 * exceeds common GPU limits) and do NOT instance 819k tile quads.
 *
 * Unlit on purpose: the sprites carry their own shading, exactly like the 2D
 * map.
 */

import * as THREE from "three";
import type { CityDocument } from "../contract";
import { decodeRle } from "../contract";
import { GROUND } from "../palette";
import { roadMask, ROAD_N, ROAD_E, ROAD_S, ROAD_W } from "./road_mask";

/** Load a spritesheet image from a URL. Returns undefined on failure. */
export async function loadImage(url: string): Promise<HTMLImageElement | undefined> {
  const img = new Image();
  img.src = url;
  await new Promise<void>((resolve) => (img.onload = () => resolve()));
  return img;
}

const SKIRT_SIZE = 4096;
const SPRITE = 16;

// Runtime atlas layout. Kind ids index the wire legend (grass, road,
// power_line, plant, lot, water); the atlas inserts grass_alt after grass so
// the shader can do the (x + y) % 2 checker, and paints `lot` as a flat pad —
// buildings are 3D boxes here, so the 2D building sprite never shows.
const ATLAS_CELLS = ["grass", "grass_alt", "road", "power_line", "plant", "__pad__", "water"];
const PAD_FILL = "#3f3f46";

// PROPER STREETS (Stephen, 2026-08-05: the flat road slabs looked "strange
// and unrealistic"). Sixteen connectivity-variant road cells appended after
// the legend cells: the CPU computes each road tile's N/E/S/W road-adjacency
// mask (bit 1=N, 2=E, 4=S, 8=W — `road_mask.ts`, shared with the 3D curbs in
// streetscape.ts) and the shader picks cell ROAD_BASE + mask. Curbs wrap only
// the CLOSED edges, so adjacent road tiles fuse into one continuous asphalt
// surface — a two-lane trunk reads as one wide road, a junction as a junction
// — and a dashed centre line marks pure straights. A street ending at a
// building keeps its curb cap: the driveway look.
const ROAD_BASE = ATLAS_CELLS.length;
const ROAD_VARIANTS = 16;
const ASPHALT = "#46464c";
const GUTTER = "#2f2f34";
const CURB = "#8a8a92";
const LANE_PAINT = "#d8c86a";
const STOP_PAINT = "#e4e4dc";  // stop bars and crossings: white, not lane yellow

// ROAD PAINT ON EVERY VARIANT (Stephen, 2026-08-07: "add paint to all the
// roads too. Then maybe it will be obvious how awkward they look right now
// compared to real life roads"). Until now only the two pure straights were
// painted, so on a real catalog — where almost every road tile is fused into a
// junction or a widened trunk — the network rendered as one featureless slab.
// The vocabulary below is the minimum that makes a road read as a road, and
// each mark states something TRUE about the tile's connectivity:
//
//   straight   dashed centre line, as before
//   corner     the centre line turns through the tile on an L
//   T          stop bar across the STEM only; the through road keeps its
//              centre line, because at a T the minor approach is what yields
//   crossroads four stop bars, no centre line — an all-way stop; the box
//              itself stays bare, exactly as a real junction box is
//   stub       a short centre approach stub (a driveway, not a through road)
//
// A junction box that stayed unpainted is the tell that the network is a
// diagram; these marks are what `docs/road-grammar.md` calls the road's own
// grammar, drawn.
const OPPOSITE = new Map<number, number>([
  [ROAD_N, ROAD_S],
  [ROAD_S, ROAD_N],
  [ROAD_E, ROAD_W],
  [ROAD_W, ROAD_E],
]);

function drawStopBar(ctx: CanvasRenderingContext2D, x0: number, dir: number): void {
  const S = SPRITE;
  const back = 3; // set-back from the open edge, in px
  if (dir === ROAD_N) ctx.fillRect(x0 + 3, back, S - 6, 1);
  else if (dir === ROAD_S) ctx.fillRect(x0 + 3, S - back - 1, S - 6, 1);
  else if (dir === ROAD_W) ctx.fillRect(x0 + back, 3, 1, S - 6);
  else ctx.fillRect(x0 + S - back - 1, 3, 1, S - 6);
}

function drawCentreArm(ctx: CanvasRenderingContext2D, x0: number, dir: number): void {
  const S = SPRITE;
  const mid = Math.floor(S / 2);
  if (dir === ROAD_N) for (let y = 1; y < mid; y += 4) ctx.fillRect(x0 + mid, y, 1, 2);
  else if (dir === ROAD_S) for (let y = mid + 1; y < S - 1; y += 4) ctx.fillRect(x0 + mid, y, 1, 2);
  else if (dir === ROAD_W) for (let x = 1; x < mid; x += 4) ctx.fillRect(x0 + x, mid, 2, 1);
  else for (let x = mid + 1; x < S - 1; x += 4) ctx.fillRect(x0 + x, mid, 2, 1);
}

function drawRoadCell(ctx: CanvasRenderingContext2D, x0: number, mask: number): void {
  const S = SPRITE;
  ctx.fillStyle = ASPHALT;
  ctx.fillRect(x0, 0, S, S);

  const closed = {
    n: !(mask & ROAD_N),
    e: !(mask & ROAD_E),
    s: !(mask & ROAD_S),
    w: !(mask & ROAD_W),
  };
  // A gutter shadow one pixel inside each closed edge, then the curb on it.
  ctx.fillStyle = GUTTER;
  if (closed.n) ctx.fillRect(x0, 1, S, 1);
  if (closed.s) ctx.fillRect(x0, S - 2, S, 1);
  if (closed.w) ctx.fillRect(x0 + 1, 0, 1, S);
  if (closed.e) ctx.fillRect(x0 + S - 2, 0, 1, S);
  ctx.fillStyle = CURB;
  if (closed.n) ctx.fillRect(x0, 0, S, 1);
  if (closed.s) ctx.fillRect(x0, S - 1, S, 1);
  if (closed.w) ctx.fillRect(x0, 0, 1, S);
  if (closed.e) ctx.fillRect(x0 + S - 1, 0, 1, S);

  const open = [ROAD_N, ROAD_E, ROAD_S, ROAD_W].filter((bit) => mask & bit);
  // A through axis is a pair of facing open edges: the road that does NOT stop.
  const through = open.filter((bit) => mask & OPPOSITE.get(bit)!);

  if (open.length >= 3) {
    // Junction. Stop bars go on the approaches that yield: at a T that is the
    // stem alone, at a crossroads it is all four. The box stays bare.
    const stems = open.filter((bit) => !(mask & OPPOSITE.get(bit)!));
    ctx.fillStyle = STOP_PAINT;
    for (const dir of stems.length ? stems : open) drawStopBar(ctx, x0, dir);
    ctx.fillStyle = LANE_PAINT;
    for (const dir of through) drawCentreArm(ctx, x0, dir);
    return;
  }

  // Straights, corners and stubs all get their centre line: one arm per open
  // edge, so a corner's line turns and a stub's line simply stops.
  ctx.fillStyle = LANE_PAINT;
  for (const dir of open) drawCentreArm(ctx, x0, dir);
}

function buildAtlasTexture(doc: CityDocument, sheet: HTMLImageElement): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = (ATLAS_CELLS.length + ROAD_VARIANTS) * SPRITE;
  canvas.height = SPRITE;
  const ctx = canvas.getContext("2d")!;
  for (const [cell, name] of ATLAS_CELLS.entries()) {
    if (name === "__pad__") {
      ctx.fillStyle = PAD_FILL;
      ctx.fillRect(cell * SPRITE, 0, SPRITE, SPRITE);
      continue;
    }
    const rect = doc.theme.sprites[name];
    if (!rect) throw new Error(`theme has no sprite ${name!}`);
    const [sx, sy, sw, sh] = rect as [number, number, number, number];
    ctx.drawImage(sheet, sx, sy, sw, sh, cell * SPRITE, 0, SPRITE, SPRITE);
  }
  for (let mask = 0; mask < ROAD_VARIANTS; mask++) {
    drawRoadCell(ctx, (ROAD_BASE + mask) * SPRITE, mask);
  }
  const texture = new THREE.CanvasTexture(canvas);
  // NoColorSpace: the PNG's sRGB bytes pass straight through the shader into
  // the sRGB drawing buffer. Tagging it sRGB would decode-to-linear on sample
  // and render everything dark (the same bug the palette path hit in reverse).
  texture.colorSpace = THREE.NoColorSpace;
  texture.magFilter = THREE.NearestFilter;
  texture.minFilter = THREE.NearestFilter;
  texture.generateMipmaps = false;
  return texture;
}

function buildIndexTexture(doc: CityDocument): THREE.DataTexture {
  const { width, height } = doc.grid;
  const cells = decodeRle(doc.grid.tiles_rle, width, height);
  const data = new Uint8Array(width * height);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      data[(height - 1 - y) * width + x] = cells[y * width + x]!;
    }
  }
  const texture = new THREE.DataTexture(data, width, height, THREE.RedFormat);
  texture.magFilter = THREE.NearestFilter;
  texture.minFilter = THREE.NearestFilter; // ids must never interpolate
  // Rows are bytes, not vec4s: without this, any width not divisible by 4
  // shears the whole map (WebGL's default unpack alignment is 4).
  texture.unpackAlignment = 1;
  texture.needsUpdate = true;
  return texture;
}

function buildRoadMaskTexture(doc: CityDocument): THREE.DataTexture {
  const { width, height, masks } = roadMask(doc);
  const data = new Uint8Array(width * height);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      // World north (y-1) is texture-up after the bottom-up flip; the cell
      // art is drawn in canvas coordinates (y down), matching world y down,
      // so N in the mask means world y-1 and this flip keeps them aligned.
      data[(height - 1 - y) * width + x] = masks[y * width + x]!;
    }
  }
  const texture = new THREE.DataTexture(data, width, height, THREE.RedFormat);
  texture.magFilter = THREE.NearestFilter;
  texture.minFilter = THREE.NearestFilter;
  texture.unpackAlignment = 1;
  texture.needsUpdate = true;
  return texture;
}

const VERTEX = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

// For each fragment: which tile am I over -> which kind -> which atlas cell.
// Grass alternates by tile parity, matching the 2D map. `local` is clamped a
// half-texel in so linear rasterisation at cell borders can never bleed the
// neighbouring sprite.
const FRAGMENT = /* glsl */ `
  uniform sampler2D indexMap;
  uniform sampler2D roadMask;
  uniform sampler2D atlas;
  uniform vec2 gridSize;
  uniform float cellCount;
  uniform float roadId;
  uniform float roadBase;
  varying vec2 vUv;
  void main() {
    vec2 tile = vUv * gridSize;
    vec2 tileIndex = floor(tile);
    float id = texture2D(indexMap, (tileIndex + 0.5) / gridSize).r * 255.0;
    // uv v runs opposite world z, and rows were stored bottom-up to match, so
    // world-parity needs the flipped row index.
    float row = gridSize.y - 1.0 - tileIndex.y;
    float parity = mod(tileIndex.x + row, 2.0);
    float cell = id < 0.5 ? parity : id + 1.0;
    // Roads pick their connectivity variant instead of the flat slab: curbs
    // only on edges facing non-road, so adjacent tiles fuse into one street.
    if (abs(id - roadId) < 0.5) {
      float mask = texture2D(roadMask, (tileIndex + 0.5) / gridSize).r * 255.0;
      cell = roadBase + mask;
    }
    vec2 local = clamp(fract(tile), 0.5 / 16.0, 15.5 / 16.0);
    gl_FragColor = texture2D(atlas, vec2((cell + local.x) / cellCount, local.y));
  }
`;

function buildSkirtTexture(doc: CityDocument, sheet: HTMLImageElement): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = SPRITE * 2;
  canvas.height = SPRITE * 2;
  const ctx = canvas.getContext("2d")!;
  const draw = (name: string, dx: number, dy: number) => {
    const [sx, sy, sw, sh] = doc.theme.sprites[name] as [number, number, number, number];
    ctx.drawImage(sheet, sx, sy, sw, sh, dx, dy, SPRITE, SPRITE);
  };
  draw("grass", 0, 0);
  draw("grass_alt", SPRITE, 0);
  draw("grass_alt", 0, SPRITE);
  draw("grass", SPRITE, SPRITE);
  const texture = new THREE.CanvasTexture(canvas);
  // sRGB here, unlike the atlas: the skirt uses MeshBasicMaterial, whose
  // shader decodes the map by this tag and re-encodes at output. NoColorSpace
  // told it the sRGB bytes were linear and the skirt rendered washed-out pale
  // against the grid (caught by eye). The atlas stays NoColorSpace because the
  // custom shader writes its samples straight to the sRGB buffer.
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(SKIRT_SIZE / 2, SKIRT_SIZE / 2);
  texture.magFilter = THREE.NearestFilter;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  return texture;
}

export function buildAtlasTerrain(doc: CityDocument, sheet: HTMLImageElement): THREE.Group {
  const { width, height } = doc.grid;

  const grid = new THREE.Mesh(
    new THREE.PlaneGeometry(width, height),
    new THREE.ShaderMaterial({
      uniforms: {
        indexMap: { value: buildIndexTexture(doc) },
        roadMask: { value: buildRoadMaskTexture(doc) },
        atlas: { value: buildAtlasTexture(doc, sheet) },
        gridSize: { value: new THREE.Vector2(width, height) },
        cellCount: { value: ATLAS_CELLS.length + ROAD_VARIANTS },
        roadId: { value: doc.grid.tile_kinds.indexOf("road") },
        roadBase: { value: ROAD_BASE },
      },
      vertexShader: VERTEX,
      fragmentShader: FRAGMENT,
    }),
  );
  grid.rotateX(-Math.PI / 2);
  grid.position.set(width / 2, 0, height / 2);

  // Snapped to whole tiles so the checker phase can be aligned exactly; a
  // half-tile of extra overhang on a 4096-tile plane is invisible.
  const cx = Math.floor(width / 2);
  const cz = Math.floor(height / 2);
  const texture = buildSkirtTexture(doc, sheet);
  // Phase-align the checker with the grid's (x + y) % 2. One repeat is two
  // tiles; the skirt's left/far edge sits at tile (cx - S/2, cz - S/2), so
  // shifting the pattern by half a repeat when that corner is odd lines the
  // two checkers up. v runs opposite z, which flips which corner v=0 sees --
  // hence the +1 on the z phase (S/2 is even, so only the corner parity and
  // the flip matter). Verified by rendering the boundary and looking.
  const phaseX = (((cx - SKIRT_SIZE / 2) % 2) + 2) % 2;
  const phaseZ = (((cz + SKIRT_SIZE / 2 + 1) % 2) + 2) % 2;
  texture.offset.set(phaseX / 2, phaseZ / 2);

  const skirt = new THREE.Mesh(
    new THREE.PlaneGeometry(SKIRT_SIZE, SKIRT_SIZE),
    // depthWrite off + drawn first: 0.02 of separation is nothing against a
    // 0.1..6000 depth range, so at shallow distant angles the 4096-tile skirt
    // used to win the depth fight over the grid and the STREETS DISAPPEARED
    // into grass (visible from any low camera a few tiles out; the 3D curbs
    // stayed and gave it away). Writing no depth lets the grid, drawn after,
    // always paint over it — the skirt is the lowest surface in the scene, so
    // nothing legitimately hides behind it.
    new THREE.MeshBasicMaterial({ map: texture, depthWrite: false }),
  );
  skirt.rotateX(-Math.PI / 2);
  skirt.position.set(cx, -0.02, cz);
  skirt.renderOrder = -1;

  const group = new THREE.Group();
  group.add(grid, skirt);
  return group;
}
