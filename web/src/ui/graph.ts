/**
 * The dbt model graph, rendered in the HUD when a building is selected: the
 * selected object's full ancestry and descendants as a small layered SVG DAG
 * (dbt-docs style, left → right). Nodes colour by verdict (fail red, warn
 * amber, build error dark red), edges style by provenance (solid = declared,
 * dashed = inferred SQL scan), and every node carries data-key — the
 * inspector's existing click binding makes the whole graph walkable.
 */

import type { CityDocument } from "../contract";

const NODE_W = 96;
const NODE_H = 22;
const GAP_X = 42;
const GAP_Y = 8;
const MAX_NODES = 28; // beyond this, trim to ±2 hops and say so

interface Node {
  key: string;
  layer: number;
  row: number;
}

function neighbours(doc: CityDocument, key: string, direction: "up" | "down"): string[] {
  return direction === "up"
    ? doc.edges.filter((e) => e.dst === key).map((e) => e.src)
    : doc.edges.filter((e) => e.src === key).map((e) => e.dst);
}

/** BFS one direction, assigning signed layers relative to the selection. */
function walk(
  doc: CityDocument,
  start: string,
  direction: "up" | "down",
  layers: Map<string, number>,
  maxHops: number,
): void {
  let frontier = [start];
  for (let hop = 1; hop <= maxHops && frontier.length; hop++) {
    const next: string[] = [];
    for (const key of frontier) {
      for (const n of neighbours(doc, key, direction)) {
        if (!layers.has(n)) {
          layers.set(n, direction === "up" ? -hop : hop);
          next.push(n);
        }
      }
    }
    frontier = next;
  }
}

function verdictColor(doc: CityDocument, key: string): string {
  const lot = doc.lots.find((l) => l.object_key === key);
  if (lot?.test_status === "fail" || lot?.build_status === "error") return "#e03535";
  if (lot?.test_status === "warn" || lot?.freshness_status === "warn") return "#e0a832";
  if (lot?.freshness_status === "error") return "#e03535";
  return "#6a60a8";
}

export function graphSvg(doc: CityDocument, key: string): string {
  const layers = new Map<string, number>([[key, 0]]);
  walk(doc, key, "up", layers, 9);
  walk(doc, key, "down", layers, 9);
  let trimmed = false;
  if (layers.size > MAX_NODES) {
    for (const [k, layer] of [...layers]) {
      if (Math.abs(layer) > 2) layers.delete(k);
    }
    trimmed = true;
  }
  if (layers.size < 2) return ""; // an orphan has no graph to draw

  // Rows: stable order within each layer.
  const byLayer = new Map<number, string[]>();
  for (const [k, layer] of [...layers].sort((a, b) => a[0].localeCompare(b[0]))) {
    byLayer.set(layer, [...(byLayer.get(layer) ?? []), k]);
  }
  const layerIds = [...byLayer.keys()].sort((a, b) => a - b);
  const nodes = new Map<string, Node>();
  for (const [i, layer] of layerIds.entries()) {
    for (const [row, k] of byLayer.get(layer)!.entries()) {
      nodes.set(k, { key: k, layer: i, row });
    }
  }
  const width = layerIds.length * (NODE_W + GAP_X) - GAP_X;
  const height = Math.max(...[...byLayer.values()].map((l) => l.length)) * (NODE_H + GAP_Y);
  const x = (n: Node) => n.layer * (NODE_W + GAP_X);
  const y = (n: Node) => n.row * (NODE_H + GAP_Y);

  const edges = doc.edges
    .filter((e) => nodes.has(e.src) && nodes.has(e.dst))
    .map((e) => {
      const a = nodes.get(e.src)!;
      const b = nodes.get(e.dst)!;
      const x1 = x(a) + NODE_W;
      const y1 = y(a) + NODE_H / 2;
      const x2 = x(b);
      const y2 = y(b) + NODE_H / 2;
      const mid = (x1 + x2) / 2;
      const dash = e.provenance === "view_sql" ? ' stroke-dasharray="4 3"' : "";
      return `<path d="M${x1} ${y1} C${mid} ${y1} ${mid} ${y2} ${x2} ${y2}" fill="none" stroke="#8f86c9" stroke-width="1.2"${dash}/>`;
    })
    .join("");

  const boxes = [...nodes.values()]
    .map((n) => {
      const short = n.key.split(".").pop() ?? n.key;
      const label = short.length > 14 ? `${short.slice(0, 13)}…` : short;
      const isSelf = n.key === key;
      const stroke = isSelf ? "#ffffff" : verdictColor(doc, n.key);
      const fill = isSelf ? "#574c9c" : "#2c2358";
      return (
        `<g data-key="${n.key.replace(/"/g, "&quot;")}" style="cursor:pointer">` +
        `<rect x="${x(n)}" y="${y(n)}" rx="4" width="${NODE_W}" height="${NODE_H}" fill="${fill}" stroke="${stroke}" stroke-width="${isSelf ? 1.6 : 1.2}"/>` +
        `<text x="${x(n) + NODE_W / 2}" y="${y(n) + NODE_H / 2 + 3.5}" text-anchor="middle" font-size="9.5" fill="#f0f0ff">${label}</text>` +
        `<title>${n.key}</title></g>`
      );
    })
    .join("");

  const note = trimmed ? `<p class="prov">trimmed to ±2 hops</p>` : "";
  return (
    `<h3>model graph</h3>${note}<div class="graph-scroll">` +
    `<svg viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" ` +
    `xmlns="http://www.w3.org/2000/svg">${edges}${boxes}</svg></div>`
  );
}
