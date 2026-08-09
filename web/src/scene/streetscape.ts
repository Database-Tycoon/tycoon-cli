/**
 * Streets in three dimensions, and their dressed endings.
 *
 * Stephen (2026-08-05): the streets "look flat/pasted". They were: the road
 * surface was painted into the terrain atlas, so at any low camera angle the
 * city's whole street network was a decal on a plane. This module gives the
 * network real geometry:
 *
 * - **Sidewalk curbs.** A thin raised concrete lip along every CLOSED edge of
 *   every road tile — the same closed-edge set the atlas paints its curb line
 *   on (`road_mask.ts` is the one definition, deliberately shared). Straddling
 *   the tile boundary, so half the lip sits on the street and half on the
 *   ground beside it, which is where a real curb sits and what makes the
 *   asphalt read as sunken. Adjacent road tiles fuse exactly as the paint
 *   does: no curb ever crosses a junction.
 * - **Dressed endings** from `doc.street_features` (`docs/road-grammar.md`
 *   theme 7: "terminations are dressed, never raw"). `apron` = a paved ramp
 *   from the street over the curb line toward the building it serves, plus a
 *   door on that building's face; `dock` = a striped loading court for the
 *   industrial grammar; `plaza` = the lighter paved forecourt of a terminated
 *   vista. An unknown kind renders nothing — a newer planner must never break
 *   an older renderer.
 *
 * A dressed ending owns the curb it replaces: an apron cuts the curb on its
 * facing side only (a driveway is a notch, not a gap in the sidewalk), while a
 * dock or plaza re-paves its tiles and takes all four.
 *
 * Deterministic: every position comes from the document, no RNG, so
 * `?settle=1` screenshots are stable. Never built in `?flat=1` — that mode's
 * pixel tests count exact colours, and unlit concrete is not one of them.
 */

import * as THREE from "three";
import type { CityDocument, StreetFeatureRecord } from "../contract";
import { ROAD_E, ROAD_EDGES, ROAD_N, ROAD_S, ROAD_W, roadMask } from "./road_mask";

const CURB_H = 0.045; // low enough to stay a lip, high enough to catch the sun
const CURB_T = 0.13; // straddles the tile boundary: 0.065 either side
const CURB = "#a3a5ad"; // light concrete against #46464c asphalt

const APRON_LOW = 0.008; // meets the road just above the surface
const APRON_HIGH = 0.055; // clears the curb it replaces
const APRON_WIDE = 0.55; // fraction of the tile across: a driveway, not a plaza
const APRON = "#b2b0ae";
const DOOR = "#e0d8c8"; // the same warm door tone the civic buildings use
const DOOR_W = 0.26;
const DOOR_H = 0.3;
const DOOR_T = 0.06;
const BUILDING_MARGIN = 0.09; // outer face of buildings.ts's plinth (fw + 0.1)

const DOCK_H = 0.026;
const DOCK_PAD = "#4e4a46"; // oil-dark court, industrial grammar
const DOCK_STRIPE = "#d9d2b8";
// A raised platform along the building face at roughly truck-bed height: the
// tell that distinguishes a loading bay from a zebra crossing.
const DOCK_PLATFORM = "#9a938a";
const PLATFORM_H = 0.13;
const PLATFORM_D = 0.22;
const STRIPE_PITCH = 0.25;
const STRIPE_W = 0.09;

const PLAZA_H = 0.03; // under CURB_H, so a curb around a plaza still reads
const PLAZA = "#c2bfb4"; // lighter pavement — the forecourt, not more asphalt

const FACING_ANGLE: Record<string, number> = {
  s: 0,
  e: Math.PI / 2,
  n: Math.PI,
  w: -Math.PI / 2,
};
const FACING_BIT: Record<string, number> = {
  n: ROAD_N,
  e: ROAD_E,
  s: ROAD_S,
  w: ROAD_W,
};
const FACING_STEP: Record<string, [number, number]> = {
  n: [0, -1],
  e: [1, 0],
  s: [0, 1],
  w: [-1, 0],
};

/**
 * A unit-footprint wedge: 1x1 in x/z centred on the origin, its top face
 * sloping from `low` at z = -0.5 up to `high` at z = +0.5, so the rise points
 * south before rotation. Non-indexed on purpose — shared vertices would
 * average the slope's normal into the side walls and the ramp would read as a
 * smudge instead of a ramp.
 */
function wedgeGeometry(low: number, high: number): THREE.BufferGeometry {
  const a = [-0.5, 0, -0.5];
  const b = [0.5, 0, -0.5];
  const c = [0.5, 0, 0.5];
  const d = [-0.5, 0, 0.5];
  const A = [-0.5, low, -0.5];
  const B = [0.5, low, -0.5];
  const C = [0.5, high, 0.5];
  const D = [-0.5, high, 0.5];
  const quad = (p: number[], q: number[], r: number[], s: number[]) => [
    ...p, ...q, ...r, ...p, ...r, ...s,
  ];
  const vertices = [
    ...quad(A, B, C, D), // sloped top
    ...quad(d, c, b, a), // bottom
    ...quad(D, C, c, d), // high end (the building side)
    ...quad(a, b, B, A), // low end (the street side)
    ...quad(B, b, c, C), // east wall
    ...quad(A, D, d, a), // west wall
  ];
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  geometry.computeVertexNormals();
  return geometry;
}

/** A box whose origin sits on the ground, so scaling in y raises it. */
function padGeometry(): THREE.BufferGeometry {
  return new THREE.BoxGeometry(1, 1, 1).translate(0, 0.5, 0);
}

const UP = new THREE.Vector3(0, 1, 0);

/** One instance matrix: ground position, y-rotation, per-axis size. */
function place(
  x: number,
  y: number,
  z: number,
  sx: number,
  sy: number,
  sz: number,
  angle = 0,
): THREE.Matrix4 {
  return new THREE.Matrix4().compose(
    new THREE.Vector3(x, y, z),
    new THREE.Quaternion().setFromAxisAngle(UP, angle),
    new THREE.Vector3(sx, sy, sz),
  );
}

function instance(
  geometry: THREE.BufferGeometry,
  color: string,
  places: THREE.Matrix4[],
): THREE.InstancedMesh {
  const mesh = new THREE.InstancedMesh(
    geometry,
    new THREE.MeshLambertMaterial({ color }),
    places.length,
  );
  for (const [i, m] of places.entries()) mesh.setMatrixAt(i, m);
  mesh.frustumCulled = false;
  return mesh;
}

export class Streetscape {
  readonly group = new THREE.Group();
  private curbMesh: THREE.InstancedMesh | null = null;
  // One primary slab per dressed ending (the ramp, the court, the pad); trim
  // like doors and stripes is not counted.
  private primaries: THREE.InstancedMesh[] = [];

  /**
   * Raised curb segments, read off the LIVE mesh rather than a bookkeeping
   * integer, and 0 unless that mesh is actually in the group: a counter that
   * survives its geometry is the wrong-axis trap this repo keeps catching.
   */
  get curbCount(): number {
    return this.curbMesh?.parent ? this.curbMesh.count : 0;
  }

  /**
   * Dressed endings actually rendered, summed off the live primary meshes for
   * the same reason as `curbCount`. An unknown kind draws nothing and so
   * counts as nothing.
   */
  get featureCount(): number {
    return this.primaries.reduce((n, m) => n + (m.parent ? m.count : 0), 0);
  }

  constructor(doc: CityDocument) {
    const mask = roadMask(doc);
    const cut = this.curbCuts(doc);

    const curbs: THREE.Matrix4[] = [];
    for (let y = 0; y < mask.height; y++) {
      for (let x = 0; x < mask.width; x++) {
        if (!mask.isRoad(x, y)) continue;
        const bits = mask.masks[y * mask.width + x]!;
        for (const { bit, dx, dy } of ROAD_EDGES) {
          if (bits & bit) continue; // open edge: the street continues
          const owner = cut.get(`${x},${y},${bit}`);
          if (owner === "pave") continue; // re-paved: no curb at all
          const cx = x + 0.5 + dx * 0.5;
          const cz = y + 0.5 + dy * 0.5;
          // A notched edge keeps the sidewalk either side of the ramp: two
          // stubs flanking the crossing, which is what a curb cut looks like.
          const spans: [number, number][] =
            owner === "notch"
              ? [
                  [-(APRON_WIDE + (1 - APRON_WIDE) / 2) / 2, (1 - APRON_WIDE) / 2],
                  [(APRON_WIDE + (1 - APRON_WIDE) / 2) / 2, (1 - APRON_WIDE) / 2],
                ]
              : [[0, 1]];
          for (const [offset, length] of spans) {
            const along = dx === 0 ? length : CURB_T;
            const across = dx === 0 ? CURB_T : length;
            const ox = dx === 0 ? offset : 0;
            const oz = dx === 0 ? 0 : offset;
            curbs.push(place(cx + ox, 0, cz + oz, along, CURB_H, across));
          }
        }
      }
    }
    if (curbs.length) {
      this.curbMesh = instance(padGeometry(), CURB, curbs);
      this.group.add(this.curbMesh);
    }

    this.dress(doc);
  }

  /**
   * Edges a dressed ending takes over, as `x,y,bit`. An APRON cuts only the
   * curb it crosses — the one on its `facing` side — because the rest of that
   * tile's sidewalk is still sidewalk; a real driveway is a notch, not a gap.
   * A DOCK or PLAZA re-paves its tiles outright, so it owns all four ("pave").
   */
  private curbCuts(doc: CityDocument): Map<string, "notch" | "pave"> {
    const cut = new Map<string, "notch" | "pave">();
    for (const f of doc.street_features) {
      const paves = f.kind === "dock" || f.kind === "plaza";
      const bits = paves
        ? ROAD_EDGES.map((e) => e.bit)
        : f.kind === "apron"
          ? [FACING_BIT[f.facing ?? ""] ?? 0]
          : []; // unknown kind: touches nothing
      for (let dy = 0; dy < f.h; dy++) {
        for (let dx = 0; dx < f.w; dx++) {
          for (const bit of bits) {
            cut.set(`${f.x + dx},${f.y + dy},${bit}`, paves ? "pave" : "notch");
          }
        }
      }
    }
    return cut;
  }

  /** apron / dock / plaza, batched one InstancedMesh per part. */
  private dress(doc: CityDocument): void {
    const aprons: THREE.Matrix4[] = [];
    const doors: THREE.Matrix4[] = [];
    const docks: THREE.Matrix4[] = [];
    const stripes: THREE.Matrix4[] = [];
    const platforms: THREE.Matrix4[] = [];
    const plazas: THREE.Matrix4[] = [];

    for (const f of doc.street_features) {
      const cx = f.x + f.w / 2;
      const cz = f.y + f.h / 2;
      if (f.kind === "apron") {
        const angle = FACING_ANGLE[f.facing ?? ""] ?? 0;
        // Narrow across, full depth along the approach: the wedge is authored
        // rising toward +z, so x is always the cross-street axis pre-rotation.
        const across = (f.facing === "e" || f.facing === "w" ? f.h : f.w) * APRON_WIDE;
        const along = f.facing === "e" || f.facing === "w" ? f.w : f.h;
        aprons.push(place(cx, 0, cz, across, 1, along, angle));
        const door = this.doorFor(doc, f);
        if (door) doors.push(door);
      } else if (f.kind === "dock") {
        docks.push(place(cx, 0, cz, f.w, DOCK_H, f.h));
        // Hatching across the bay: bars perpendicular to the approach.
        const acrossX = f.facing === "e" || f.facing === "w";
        const span = acrossX ? f.w : f.h;
        const bars = Math.max(1, Math.floor(span / STRIPE_PITCH) - 1);
        for (let i = 1; i <= bars; i++) {
          const at = (acrossX ? f.x : f.y) + i * STRIPE_PITCH;
          const sx = acrossX ? STRIPE_W : f.w;
          const sz = acrossX ? f.h : STRIPE_W;
          const px = acrossX ? at : cx;
          const pz = acrossX ? cz : at;
          stripes.push(place(px, DOCK_H, pz, sx, 0.006, sz));
        }
        // The raised platform hugs the building face.
        const px = f.facing === "e" ? f.x + f.w - PLATFORM_D / 2 : f.facing === "w" ? f.x + PLATFORM_D / 2 : cx;
        const pz = f.facing === "s" ? f.y + f.h - PLATFORM_D / 2 : f.facing === "n" ? f.y + PLATFORM_D / 2 : cz;
        const pw = acrossX ? PLATFORM_D : f.w;
        const pd = acrossX ? f.h : PLATFORM_D;
        if (f.facing) platforms.push(place(px, 0, pz, pw, PLATFORM_H, pd));
      } else if (f.kind === "plaza") {
        plazas.push(place(cx, 0, cz, f.w, PLAZA_H, f.h));
      }
      // Any other kind: no-op, by contract.
    }

    // Primaries first: one instance per feature, and what featureCount reads.
    if (aprons.length) {
      this.addPrimary(instance(wedgeGeometry(APRON_LOW, APRON_HIGH), APRON, aprons));
    }
    if (docks.length) this.addPrimary(instance(padGeometry(), DOCK_PAD, docks));
    if (plazas.length) this.addPrimary(instance(padGeometry(), PLAZA, plazas));
    if (doors.length) this.group.add(instance(padGeometry(), DOOR, doors));
    if (stripes.length) this.group.add(instance(padGeometry(), DOCK_STRIPE, stripes));
    if (platforms.length) this.group.add(instance(padGeometry(), DOCK_PLATFORM, platforms));
  }

  private addPrimary(mesh: THREE.InstancedMesh): void {
    this.primaries.push(mesh);
    this.group.add(mesh);
  }

  /**
   * The door an apron points at: the lot covering the tile one step along
   * `facing`, marked on the face the apron arrives at. No lot there (an apron
   * onto open ground, or a planner that named a direction with nothing in it)
   * means no door — never a door hanging in the air.
   */
  private doorFor(doc: CityDocument, f: StreetFeatureRecord): THREE.Matrix4 | null {
    const step = FACING_STEP[f.facing ?? ""];
    if (!step) return null;
    const tx = f.x + (f.w - 1) * Math.max(0, step[0]) + step[0];
    const ty = f.y + (f.h - 1) * Math.max(0, step[1]) + step[1];
    const lot = doc.lots.find(
      (l) => tx >= l.x && tx < l.x + l.w && ty >= l.y && ty < l.y + l.h,
    );
    if (!lot) return null;
    // Sit the slab in the plinth's outer face so it protrudes as a doorway.
    const west = lot.x + BUILDING_MARGIN;
    const east = lot.x + lot.w - BUILDING_MARGIN;
    const north = lot.y + BUILDING_MARGIN;
    const south = lot.y + lot.h - BUILDING_MARGIN;
    const cx = f.x + f.w / 2;
    const cz = f.y + f.h / 2;
    switch (f.facing) {
      case "e":
        return place(west, 0, cz, DOOR_T, DOOR_H, DOOR_W);
      case "w":
        return place(east, 0, cz, DOOR_T, DOOR_H, DOOR_W);
      case "s":
        return place(cx, 0, north, DOOR_W, DOOR_H, DOOR_T);
      default:
        return place(cx, 0, south, DOOR_W, DOOR_H, DOOR_T);
    }
  }
}
