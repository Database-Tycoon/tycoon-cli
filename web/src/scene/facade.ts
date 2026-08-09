/**
 * Facades as schema fingerprints: each window is a COLUMN. Hue = type family
 * (numeric blue, text green, temporal amber, nested violet), LIT = documented,
 * dark = undocumented, red ring = that column's tests fail. All facts; the
 * facade is the schema made legible from the street.
 *
 * One InstancedMesh of thin emissive quads on the building's south face.
 * Windows wrap in rows of three from the bottom; buildings with more columns
 * than fit show the first rows -- the inspector's column table is complete.
 */

import * as THREE from "three";
import type { CityDocument, LotRecord, ObjectRecord } from "../contract";
import { typeFamily } from "../contract";
import { makeHeights } from "./buildings";

const FAMILY_COLOR: Record<ReturnType<typeof typeFamily>, string> = {
  numeric: "#6fa8ff",
  text: "#79e08a",
  temporal: "#ffcb52",
  boolean: "#c9c9d6",
  nested: "#c07ee8",
  other: "#9aa0b0",
};
const FAIL = "#ff3b30";
const PER_ROW = 3;
const FOOT = 0.72;
const MARGIN = 0.1; // facade side margin
const WIN_W = (FOOT - 2 * MARGIN - 2 * 0.05) / PER_ROW; // three windows + gaps
const WIN_H = 0.15;
const PITCH_Y = 0.27; // floor-to-floor
const FRAME_PAD = 0.028;

export interface WindowSpot {
  x: number;
  y: number;
  z: number;
  column: ObjectRecord["columns"][number];
}

/** Where each shown column's window sits in world space, in column order.
 * Shared between the facade meshes and the skybridges, so a bridge always
 * lands exactly on the window it feeds. Truncated columns get no spot. */
export function layoutWindows(
  lot: LotRecord,
  columns: ObjectRecord["columns"],
  height: number,
): WindowSpot[] {
  const maxRows = Math.max(1, Math.floor((height - 0.3) / PITCH_Y));
  const shown = columns.slice(0, maxRows * PER_ROW);
  const rowsUsed = Math.ceil(shown.length / PER_ROW);
  // Centre the used rows across the facade's height: a tall tower with a
  // narrow schema reads as floors, not as a storefront with blank storeys.
  const bottom = Math.max(0.22, (height - rowsUsed * PITCH_Y) / 2);
  return shown.map((column, i) => {
    const row = rowsUsed - 1 - Math.floor(i / PER_ROW);
    const col = i % PER_ROW;
    const inRow = Math.min(PER_ROW, shown.length - Math.floor(i / PER_ROW) * PER_ROW);
    const rowWidth = inRow * WIN_W + (inRow - 1) * 0.05;
    return {
      x: lot.x + lot.w / 2 - rowWidth / 2 + WIN_W / 2 + col * (WIN_W + 0.05),
      y: bottom + row * PITCH_Y + WIN_H / 2,
      z: lot.y + lot.h - (1 - FOOT) / 2, // flush with the south face
      column,
    };
  });
}

export function buildFacades(doc: CityDocument): THREE.Group | null {
  const byKey = new Map(doc.objects.map((o) => [o.key, o.columns]));
  const heightOf = makeHeights(doc);
  type Win = { x: number; y: number; z: number; color: string; dim: boolean };
  const windows: Win[] = [];

  for (const lot of doc.lots) {
    for (const spot of layoutWindows(lot, byKey.get(lot.object_key) ?? [], heightOf(lot))) {
      const { column } = spot;
      windows.push({
        x: spot.x,
        y: spot.y,
        z: spot.z,
        color: column.test_status === "fail" ? FAIL : FAMILY_COLOR[typeFamily(column.type)],
        dim: column.description === null && column.test_status !== "fail",
      });
    }
  }
  if (!windows.length) return null;

  const group = new THREE.Group();
  // Frames first: slightly larger, near-black, a hair behind the pane -- what
  // makes these read as windows set into the wall instead of stickers.
  const frames = new THREE.InstancedMesh(
    new THREE.PlaneGeometry(WIN_W + FRAME_PAD * 2, WIN_H + FRAME_PAD * 2),
    new THREE.MeshBasicMaterial({ color: "#14101f", side: THREE.DoubleSide }),
    windows.length,
  );
  const panes = new THREE.InstancedMesh(
    new THREE.PlaneGeometry(WIN_W, WIN_H),
    new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }),
    windows.length,
  );
  const m = new THREE.Matrix4();
  const color = new THREE.Color();
  for (const [i, win] of windows.entries()) {
    m.identity();
    m.setPosition(win.x, win.y, win.z + 0.004);
    frames.setMatrixAt(i, m);
    m.setPosition(win.x, win.y, win.z + 0.008);
    panes.setMatrixAt(i, m);
    color.set(win.color);
    if (win.dim) color.multiplyScalar(0.22); // undocumented: the window is dark
    panes.setColorAt(i, color);
  }
  frames.frustumCulled = panes.frustumCulled = false;
  group.add(frames, panes);
  return group;
}
