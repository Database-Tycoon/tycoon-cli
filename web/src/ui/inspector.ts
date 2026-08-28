/**
 * The right-side inspector: the 2D Object screen reborn as a panel. Shows the
 * catalog facts for one object plus its lineage, with each neighbour clickable
 * so lineage can be walked without leaving the panel.
 */

import type { CityDocument, JoinRecord, LineageEntry, SemanticRecord } from "../contract";
import { hasSemanticModel, joinsOf, lineageOf, PROVENANCE_LABEL } from "../contract";
import { graphSvg } from "./graph";
import { PLANT_KEY } from "../scene/plant";
import { FIREHOUSE_KEY, LIBRARY_KEY } from "../scene/civic";

export class Inspector {
  private root: HTMLElement;

  constructor(
    private doc: CityDocument,
    private onJump: (key: string) => void,
    // Extra <dt>/<dd> rows from the simulated layer; the inspector is the
    // provenance seam, so callers label these rows themselves.
    private extras: (key: string) => string = () => "",
  ) {
    this.root = document.getElementById("inspector")!;
  }

  /** In-place R refresh: swap the document; panels re-render on next show. */
  setDoc(doc: CityDocument): void {
    this.doc = doc;
  }

  show(key: string | null): void {
    if (key === null) {
      this.root.hidden = true;
      return;
    }
    this.root.hidden = false;
    this.root.innerHTML =
      key === PLANT_KEY
        ? this.plantHtml()
        : key === LIBRARY_KEY
          ? this.libraryHtml()
          : key === FIREHOUSE_KEY
            ? this.firehouseHtml()
            : this.objectHtml(key);

    this.root.querySelector(".close")?.addEventListener("click", () => this.onJump(""));
    for (const link of this.root.querySelectorAll<HTMLElement>("[data-key]")) {
      link.addEventListener("click", () => this.onJump(link.dataset.key!));
    }
  }

  private libraryHtml(): string {
    // The context inventory: every number is a count of real declared
    // artifacts. This is where the city's documentation lives — and where
    // the semantic layer (Apache Ossie) will shelve when it lands.
    const objects = this.doc.objects;
    const described = objects.filter((o) => (o.dbt?.description ?? "").length > 0).length;
    const cols = objects.flatMap((o) => o.columns);
    const colsDocumented = cols.filter((c) => c.description !== null).length;
    const tagged = objects.filter((o) => (o.dbt?.tags.length ?? 0) > 0).length;
    const owned = objects.filter((o) => o.dbt?.owner != null).length;
    const tested = objects.filter((o) => (o.dbt?.tests.length ?? 0) > 0).length;
    const pct = (n: number, d: number) => (d ? `${Math.round((100 * n) / d)}%` : "—");
    return `
      <button class="close" title="close">×</button>
      <h2>public library</h2>
      <p class="note">The city's context lives here. Every shelf is a count
      of real documentation — filling these in builds the city.</p>
      <dl>
        <dt>objects described</dt><dd>${described} / ${objects.length} (${pct(described, objects.length)})</dd>
        <dt>columns documented</dt><dd>${colsDocumented} / ${cols.length} (${pct(colsDocumented, cols.length)})</dd>
        <dt>objects tagged</dt><dd>${tagged} / ${objects.length}</dd>
        <dt>owners assigned</dt><dd>${owned} / ${objects.length}</dd>
        <dt>objects tested</dt><dd>${tested} / ${objects.length}</dd>
      </dl>
      <p class="note">Descriptions come from the dbt manifest. A semantic
      model (Apache Ossie / OSI) is not connected yet — when it is, its
      relationships and ai_context shelve here too.</p>`;
  }

  private firehouseHtml(): string {
    const burning = this.doc.lots.filter((lot) => lot.test_status === "fail");
    const stale = this.doc.lots.filter(
      (lot) => lot.freshness_status === "warn" || lot.freshness_status === "error",
    );
    const staleRows = stale.length
      ? stale
          .map(
            (lot) =>
              `<li data-key="${escapeHtml(lot.object_key)}">${escapeHtml(lot.object_key)} <span class="prov">${escapeHtml(lot.freshness_status!)}</span></li>`,
          )
          .join("")
      : '<li class="none">no stale sources</li>';
    const rows = burning.length
      ? burning
          .map(
            (lot) =>
              `<li data-key="${escapeHtml(lot.object_key)}">${escapeHtml(lot.object_key)}</li>`,
          )
          .join("")
      : '<li class="none">no active fires</li>';
    return `
      <button class="close" title="close">×</button>
      <h2>firehouse</h2>
      <h3>active fires (${burning.length})</h3>
      <ul>${rows}</ul>
      <h3>repair calls (${stale.length})</h3>
      <ul>${staleRows}</ul>
      <p class="note">A fire is a failing test; a repair call is a source
      violating its dbt freshness SLA (the worn, boarded-up buildings).
      Trucks and contractor vans on the street mean a problem is awaiting
      response — they never mean a fix is running.</p>
      <p class="note">AI responder: <b>not connected</b> in the local
      version. When connected, dispatch will run an agent against the
      failing model and prepare a suggested fix for review.</p>`;
  }

  private objectHtml(key: string): string {
    const obj = this.doc.objects.find((o) => o.key === key);
    const lot = this.doc.lots.find((l) => l.object_key === key);
    if (!obj || !lot) return `<button class="close">×</button><h2>${escapeHtml(key)}</h2>`;

    const { upstream, downstream } = lineageOf(this.doc, key);
    const labels = this.doc.theme.labels;
    const dbt = obj.dbt;
    // Temporal rows only when known: an unknown must not render as a value.
    const temporal = [
      lot.freshness_status !== null
        ? `<dt>freshness</dt><dd class="tests-${lot.freshness_status === "pass" ? "pass" : lot.freshness_status === "warn" ? "warn" : "fail"}">${escapeHtml(lot.freshness_status)} <span class="prov">dbt SLA</span></dd>`
        : "",
      lot.last_build_age_s !== null
        ? `<dt>last build</dt><dd>${age(lot.last_build_age_s)} ago</dd>`
        : "",
      lot.build_status !== null ? `<dt>build</dt><dd>${escapeHtml(lot.build_status)}</dd>` : "",
      lot.test_status !== null
        ? `<dt>tests</dt><dd class="tests-${escapeHtml(lot.test_status)}">${escapeHtml(lot.test_status)}</dd>`
        : "",
    ].join("");
    return `
      <button class="close" title="close">×</button>
      <h2>${escapeHtml(obj.name)}</h2>
      <dl>
        <dt>${escapeHtml(labels.schema ?? "schema")}</dt><dd>${escapeHtml(obj.schema)}</dd>
        <dt>kind</dt><dd>${obj.kind}</dd>
        <dt>${escapeHtml(labels.rows ?? "rows")}</dt><dd>${obj.row_count.toLocaleString()}</dd>
        <dt>density</dt><dd>${lot.target_density} / 8</dd>
        <dt>powered</dt><dd>${lot.powered ? "yes" : "no — takes no part in lineage"}</dd>
        ${dbt?.materialized ? `<dt>materialized</dt><dd>${escapeHtml(dbt.materialized)}</dd>` : ""}
        ${dbt?.owner ? `<dt>owner</dt><dd>${escapeHtml(dbt.owner)}</dd>` : ""}
        ${temporal}
        ${this.extras(key)}
      </dl>
      ${dbt?.description ? `<p class="doc">${escapeHtml(dbt.description)}</p>` : ""}
      ${dbt?.tags.length ? `<p class="chips">${dbt.tags.map((t) => `<span class="chip">${escapeHtml(t)}</span>`).join("")}</p>` : ""}
      ${this.semanticHtml(obj.semantic)}
      ${graphSvg(this.doc, key)}
      ${this.columnsHtml(obj.columns)}
      ${this.testsHtml(dbt?.tests ?? [])}
      ${this.lineageHtml("upstream", upstream)}
      ${this.lineageHtml("downstream", downstream)}
      ${this.joinsHtml(key)}
    `;
  }

  /**
   * The declared OSI dataset: the business name over the door, its keys, and
   * the ai_context that makes the object legible.
   *
   * Three states, kept apart on purpose (`docs/city-json-v1.md`):
   * - no semantic model in this document at all → nothing is said, because a
   *   catalog without one has no absence to report;
   * - a model exists and does not claim this object → SAY SO;
   * - a model claims it but annotates nothing → say that instead, because a
   *   named-but-unannotated dataset is a different fact from an unclaimed one.
   */
  private semanticHtml(semantic: SemanticRecord | null): string {
    if (!hasSemanticModel(this.doc)) return "";
    if (semantic === null) {
      return `<h3>semantic (OSI)</h3><p class="note">no declared dataset —
        the semantic model does not mention this object</p>`;
    }
    const keyRow = (label: string, columns: readonly string[]): string =>
      columns.length
        ? `<dt>${label}</dt><dd>${columns.map((c) => escapeHtml(c)).join(", ")}</dd>`
        : "";
    const uniques = semantic.unique_keys
      .map((columns) => `<li>${columns.map((c) => escapeHtml(c)).join(", ")}</li>`)
      .join("");
    const annotated =
      semantic.instructions !== null ||
      semantic.synonyms.length > 0 ||
      semantic.example_queries.length > 0;
    return `
      <h3>semantic (OSI)</h3>
      <dl>
        <dt>dataset</dt><dd>${escapeHtml(semantic.name)} <span class="prov">declared</span></dd>
        ${keyRow("primary key", semantic.primary_key)}
      </dl>
      ${uniques ? `<h3>unique keys</h3><ul class="cols">${uniques}</ul>` : ""}
      ${semantic.instructions ? `<p class="doc">${escapeHtml(semantic.instructions)}</p>` : ""}
      ${
        semantic.synonyms.length
          ? `<p class="chips">${semantic.synonyms
              .map((s) => `<span class="chip">${escapeHtml(s)}</span>`)
              .join("")}</p>`
          : ""
      }
      ${
        semantic.example_queries.length
          ? `<h3>example queries</h3><ul class="cols">${semantic.example_queries
              .map((q) => `<li>${escapeHtml(q)}</li>`)
              .join("")}</ul>`
          : ""
      }
      ${annotated ? "" : '<p class="note">declared, not yet annotated — no instructions, synonyms or example queries</p>'}`;
  }

  /**
   * The declared joins touching this object.
   *
   * PROVENANCE IS THE POINT. A join is DECLARED — somebody wrote it in a
   * semantic model — while lineage is MEASURED or inferred from SQL, and the
   * two must never be mistaken for one another. So every row states its own
   * provenance, and then states separately whether the same pair also carries
   * a lineage edge, with that edge's own label and the model graph's marker
   * vocabulary: solid = declared, dashed = inferred. A join with no lineage
   * says so in words — it is the join street that has to be paved out of the
   * dirt, and it is emphatically not a claim that data moved.
   *
   * Join streets are deliberately NOT drawn in the 3D scene yet (blocked on
   * streets v5 dirt tracks); this panel is where they live for now.
   */
  private joinsHtml(key: string): string {
    const entries = joinsOf(this.doc, key);
    if (!entries.length) {
      // Only worth stating when a semantic model exists to have omitted it.
      return hasSemanticModel(this.doc)
        ? `<h3>declared joins</h3><ul><li class="none">none declared</li></ul>`
        : "";
    }
    const rows = entries
      .map(({ join, other, side }) => {
        const direction =
          side === "many"
            ? `many → one · this object is the many side`
            : `many → one · this object is the one side`;
        // `keys` is always [many-side column, one-side column], whichever end
        // of the join this object happens to be — the pair is a fact about the
        // relationship, not about the viewpoint.
        const pairs = join.keys
          .map(([manyCol, oneCol]) => `${escapeHtml(manyCol)} → ${escapeHtml(oneCol)}`)
          .join(", ");
        return (
          `<li><span class="door" data-key="${escapeHtml(other)}">${escapeHtml(other)}</span>` +
          `<span class="prov">${escapeHtml(join.provenance)} (OSI)</span>` +
          `<div class="join-line">${escapeHtml(join.name)} · ${direction}</div>` +
          `<div class="join-line">on ${pairs}${join.composite ? " <span class='prov'>composite</span>" : ""}</div>` +
          `<div class="join-line">${this.lineageNote(join)}</div></li>`
        );
      })
      .join("");
    return `<h3>declared joins (${entries.length})</h3><ul class="joins">${rows}</ul>`;
  }

  /** Whether the joined pair ALSO has measured lineage, and of what kind. */
  private lineageNote(join: JoinRecord): string {
    if (join.lineage_edge === null) {
      return `<span class="lin dash"></span>no lineage on this pair — declared join only`;
    }
    const [src, dst] = join.lineage_edge;
    const edge = this.doc.edges.find((e) => e.src === src && e.dst === dst);
    if (!edge) {
      // The document named an edge this client cannot find. Say so rather than
      // quietly upgrading the join to "has lineage".
      return `<span class="lin dash"></span>names a lineage edge ${escapeHtml(src)} → ${escapeHtml(dst)} that is not in this document`;
    }
    const inferred = edge.provenance === "view_sql";
    return (
      `<span class="lin${inferred ? " dash" : ""}"></span>` +
      `also lineage ${escapeHtml(src)} → ${escapeHtml(dst)} ` +
      `<span class="prov">${PROVENANCE_LABEL[edge.provenance]}</span>`
    );
  }

  /** The measured schema: every column with its type, doc state and column-
   * test verdict -- the complete version of what the facade windows sketch. */
  private columnsHtml(
    columns: { name: string; type: string; description: string | null; test_status: string | null }[],
  ): string {
    if (!columns.length) return "";
    const rows = columns
      .map((c) => {
        const verdict =
          c.test_status === null
            ? ""
            : `<span class="tests-${c.test_status === "pass" ? "pass" : c.test_status === "warn" ? "warn" : "fail"}">\u25CF</span> `;
        const doc = c.description
          ? `<div class="col-doc">${escapeHtml(c.description)}</div>`
          : "";
        return `<li>${verdict}<b>${escapeHtml(c.name)}</b> <span class="prov">${escapeHtml(c.type.toLowerCase())}</span>${doc}</li>`;
      })
      .join("");
    return `<h3>columns (${columns.length})</h3><ul class="cols">${rows}</ul>`;
  }

  /** dbt's declared tests by name, each with its last verdict. A test with a
   * null status is DECLARED, NEVER RUN — shown, but as unknown, because a
   * declared-but-unrun test must not read as passing. */
  private testsHtml(tests: { name: string; column: string | null; status: string | null }[]): string {
    if (!tests.length) return "";
    const dot = (status: string | null): string => {
      if (status === null) return "○";
      const s = status.toLowerCase();
      if (s === "pass" || s === "success") return "<span class='tests-pass'>●</span>";
      if (s === "warn") return "<span class='tests-warn'>●</span>";
      return "<span class='tests-fail'>●</span>";
    };
    const items = tests
      .map(
        (t) =>
          `<li>${dot(t.status)} ${escapeHtml(t.name)}` +
          `${t.column ? `<span class="prov">on ${escapeHtml(t.column)}</span>` : ""}` +
          `${t.status === null ? `<span class="prov">never run</span>` : ""}</li>`,
      )
      .join("");
    return `<h3>dbt tests</h3><ul class="tests">${items}</ul>`;
  }

  private lineageHtml(title: string, entries: LineageEntry[]): string {
    const items = entries.length
      ? entries
          .map(
            (e) =>
              `<li data-key="${escapeHtml(e.key)}">${escapeHtml(e.key)}` +
              `<span class="prov">${PROVENANCE_LABEL[e.provenance]}</span></li>`,
          )
          .join("")
      : "<li class='none'>none</li>";
    return `<h3>${title}</h3><ul>${items}</ul>`;
  }

  private plantHtml(): string {
    const db = this.doc.database;
    const note = db.has_known_edges
      ? ""
      : "<p class='note'>no lineage detected — lineage comes from view SQL, so a tables-only database yields none</p>";
    return `
      <button class="close" title="close">×</button>
      <h2>${escapeHtml(db.name)}</h2>
      <dl>
        <dt>${escapeHtml(this.doc.theme.labels.database ?? "database")}</dt><dd>the power plant</dd>
        <dt>objects</dt><dd>${db.object_count}</dd>
        <dt>total rows</dt><dd>${db.total_rows.toLocaleString()}</dd>
      </dl>
      ${note}
    `;
  }
}

function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}

/** 5400 -> "1h", 259200 -> "3d". Coarse on purpose; exact ages are noise. */
function age(seconds: number): string {
  if (seconds < 3600) return `${Math.max(1, Math.round(seconds / 60))}m`;
  if (seconds < 86400) return `${Math.round(seconds / 3600)}h`;
  return `${Math.round(seconds / 86400)}d`;
}
