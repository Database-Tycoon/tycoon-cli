/**
 * Search: `/` or Cmd/Ctrl-K opens a type-ahead over object keys, tags and
 * owners; Enter (or click) flies to the pick. Districts and the plant are
 * findable too. Keyboard-first, per the design brief — this runs on an
 * engineer's monitor.
 */

import type { CityDocument } from "../contract";

interface Entry {
  key: string; // what visit() receives ("__plant__" for the plant)
  label: string;
  haystack: string; // lowercased searchable text
}

export class Search {
  private root: HTMLElement;
  private input: HTMLInputElement;
  private list: HTMLElement;
  private entries: Entry[] = [];
  private cursor = 0;

  constructor(
    doc: CityDocument,
    private visit: (key: string) => void,
  ) {
    this.root = document.getElementById("search")!;
    this.root.innerHTML = `<div class="search-card"><input type="text"
      placeholder="find a table, view, tag, owner…" spellcheck="false" /><ul></ul></div>`;
    this.input = this.root.querySelector("input")!;
    this.list = this.root.querySelector("ul")!;
    this.index(doc);

    window.addEventListener("keydown", (event) => {
      const tag = (event.target as HTMLElement | null)?.tagName;
      const inField = tag === "INPUT" || tag === "TEXTAREA";
      if (!inField && (event.key === "/" || ((event.metaKey || event.ctrlKey) && event.key === "k"))) {
        event.preventDefault();
        this.open();
      }
    });
    this.input.addEventListener("keydown", (event) => {
      if (event.key === "Escape") this.close();
      if (event.key === "ArrowDown") {
        event.preventDefault();
        this.move(1);
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        this.move(-1);
      }
      if (event.key === "Enter") this.pick(this.cursor);
      event.stopPropagation(); // typing must not trigger R/F/P/H shortcuts
    });
    this.input.addEventListener("input", () => {
      this.cursor = 0;
      this.render();
    });
    this.root.addEventListener("click", (event) => {
      if (event.target === this.root) this.close();
    });
  }

  setDoc(doc: CityDocument): void {
    this.index(doc);
  }

  private index(doc: CityDocument): void {
    this.entries = [
      {
        key: "__plant__",
        label: `⚡ ${doc.database.name} (the database)`,
        haystack: `${doc.database.name} database plant`.toLowerCase(),
      },
      ...(doc.library
        ? [{ key: "__library__", label: "📚 public library (context & docs)", haystack: "library context documentation docs coverage" }]
        : []),
      ...(doc.firehouse
        ? [{ key: "__firehouse__", label: "🚒 firehouse (fire response)", haystack: "firehouse fire response dispatch agents failing tests" }]
        : []),
      ...doc.objects.map((o) => ({
        key: o.key,
        label: o.key,
        haystack: [o.key, o.kind, ...(o.dbt?.tags ?? []), o.dbt?.owner ?? ""]
          .join(" ")
          .toLowerCase(),
      })),
    ];
  }

  private matches(): Entry[] {
    const q = this.input.value.trim().toLowerCase();
    if (!q) return this.entries.slice(0, 12);
    return this.entries.filter((e) => e.haystack.includes(q)).slice(0, 12);
  }

  open(): void {
    this.root.hidden = false;
    this.input.value = "";
    this.cursor = 0;
    this.render();
    this.input.focus();
  }

  close(): void {
    this.root.hidden = true;
    this.input.blur();
  }

  private move(delta: number): void {
    const n = this.matches().length;
    if (!n) return;
    this.cursor = (this.cursor + delta + n) % n;
    this.render();
  }

  private pick(index: number): void {
    const match = this.matches()[index];
    if (!match) return;
    this.close();
    this.visit(match.key);
  }

  private render(): void {
    const rows = this.matches()
      .map(
        (e, i) =>
          `<li class="${i === this.cursor ? "active" : ""}" data-i="${i}">${e.label}</li>`,
      )
      .join("");
    this.list.innerHTML = rows || '<li class="none">no matches</li>';
    for (const row of this.list.querySelectorAll<HTMLElement>("li[data-i]")) {
      row.addEventListener("click", () => this.pick(Number(row.dataset.i)));
    }
  }
}
