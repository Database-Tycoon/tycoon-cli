/**
 * The Stats screen as a modal: the catalog as a table — schema, object, kind,
 * rows — with per-schema subtotals the 2D version never had room for. Rows are
 * clickable and select the object on the map, so the table doubles as a "find
 * this building" index.
 */

import type { CityDocument } from "../contract";

const ROW_CAP = 200;

export class Stats {
  private root: HTMLElement;

  constructor(
    private doc: CityDocument,
    private onPick: (key: string) => void,
  ) {
    this.root = document.getElementById("stats")!;
    document.getElementById("stats-button")!.addEventListener("click", () => this.toggle());
    window.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !this.root.hidden) this.hide();
    });
    // On the persistent root, wired once here — attaching it in show() would
    // stack one more listener per open. (Caught by the local-LLM review pass.)
    this.root.addEventListener("click", (event) => {
      if (event.target === this.root) this.hide(); // click outside the card
    });
  }

  /** In-place R refresh: swap the document; the table re-renders on open. */
  setDoc(doc: CityDocument): void {
    this.doc = doc;
  }

  toggle(): void {
    if (this.root.hidden) this.show();
    else this.hide();
  }

  hide(): void {
    this.root.hidden = true;
  }

  show(): void {
    const objects = this.doc.objects;
    const shown = objects.slice(0, ROW_CAP);
    const rows = shown
      .map(
        (o) => `
        <tr data-key="${escapeHtml(o.key)}">
          <td>${escapeHtml(o.schema)}</td>
          <td>${escapeHtml(o.name)}</td>
          <td>${o.kind}</td>
          <td class="num">${o.row_count.toLocaleString()}</td>
        </tr>`,
      )
      .join("");
    const capNote =
      objects.length > ROW_CAP
        ? `<p class="note">showing ${ROW_CAP} of ${objects.length} objects</p>`
        : "";

    this.root.innerHTML = `
      <div class="stats-card">
        <button class="close" title="close">×</button>
        <h2>${escapeHtml(this.doc.database.name)} — ${objects.length} objects, ${this.doc.database.total_rows.toLocaleString()} rows</h2>
        <table>
          <thead><tr><th>schema</th><th>object</th><th>kind</th><th class="num">rows</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
        ${capNote}
      </div>`;
    this.root.hidden = false;

    this.root.querySelector(".close")!.addEventListener("click", () => this.hide());
    for (const row of this.root.querySelectorAll<HTMLElement>("tr[data-key]")) {
      row.addEventListener("click", () => {
        this.hide();
        this.onPick(row.dataset.key!);
      });
    }
  }
}

function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}
