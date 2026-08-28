/**
 * Skybridges: column-level lineage as thin bridges between building floors.
 *
 * Each [src_col, dst_col] pair on an edge becomes a gold bridge from the
 * source column's window to the destination column's window (positions from
 * facade.ts, so a bridge always lands on the window it feeds). Bridges show
 * for the SELECTED building only — its whole column neighbourhood, in and
 * out. Always-on bridges for every edge would be spaghetti at city scale;
 * detail-on-demand is the observation platform's own rule.
 *
 * A column past the facade's shown rows (very short building, wide schema)
 * anchors at the roof centre instead — approximate but never missing.
 */

import * as THREE from "three";
import type { CityDocument, LotRecord } from "../contract";
import { makeHeights } from "./buildings";
import { layoutWindows } from "./facade";

const BRIDGE = "#ffd75e";
const THICK = 0.045;

export class Skybridges {
  readonly group = new THREE.Group();
  private doc: CityDocument;
  private selected: string | null = null;
  private material = new THREE.MeshBasicMaterial({
    color: BRIDGE,
    transparent: true,
    opacity: 0.85,
  });

  constructor(doc: CityDocument) {
    this.doc = doc;
  }

  /** Bridges currently shown — the e2e suite's counting hook. */
  get count(): number {
    return this.group.children.length;
  }

  setDoc(doc: CityDocument): void {
    this.doc = doc;
    this.rebuild();
  }

  setSelection(key: string | null): void {
    this.selected = key;
    this.rebuild();
  }

  private anchor(lot: LotRecord, columnName: string, heightOf: (l: LotRecord) => number) {
    const columns = this.doc.objects.find((o) => o.key === lot.object_key)?.columns ?? [];
    const height = heightOf(lot);
    const spot = layoutWindows(lot, columns, height).find((s) => s.column.name === columnName);
    if (spot) return new THREE.Vector3(spot.x, spot.y, spot.z);
    return new THREE.Vector3(lot.x + lot.w / 2, height, lot.y + lot.h / 2); // roof fallback
  }

  private rebuild(): void {
    for (const child of [...this.group.children]) {
      this.group.remove(child);
      (child as THREE.Mesh).geometry?.dispose();
    }
    if (!this.selected) return;
    const lots = new Map(this.doc.lots.map((l) => [l.object_key, l]));
    const heightOf = makeHeights(this.doc);

    for (const edge of this.doc.edges) {
      if (edge.src !== this.selected && edge.dst !== this.selected) continue;
      const src = lots.get(edge.src);
      const dst = lots.get(edge.dst);
      if (!src || !dst) continue;
      for (const [srcCol, dstCol] of edge.columns) {
        const a = this.anchor(src, srcCol, heightOf);
        const b = this.anchor(dst, dstCol, heightOf);
        const length = a.distanceTo(b);
        if (length < 0.01) continue;
        const mesh = new THREE.Mesh(new THREE.BoxGeometry(THICK, THICK, length), this.material);
        mesh.position.copy(a).lerp(b, 0.5);
        mesh.lookAt(b);
        this.group.add(mesh);
      }
    }
  }
}
