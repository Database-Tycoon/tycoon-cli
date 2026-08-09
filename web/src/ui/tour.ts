/**
 * The guided city tour (`?tour=1`): the metaphor, explained on the map itself.
 *
 * The Tour class is the state machine. The stop list (in tour_stops.ts) is
 * data. Two separate files make it easy to audit the full tour without
 * reading the class, and easy to change the class without touching the copy.
 *
 * TWO RULES MATTER MORE THAN THE COPY.
 *
 * 1. **Stops address things SEMANTICALLY** — an object key, a schema name, a
 *    civic key ("__plant__" / "__library__" / "__firehouse__") — and NEVER a
 *    tile coordinate. Streets v5 will move every building on this map; a tour
 *    that knew where things were would die that day and nobody would notice
 *    until it narrated an empty lot. Every stop resolves its target by looking
 *    the thing up in the document and then walks through main.ts's existing
 *    `visit(key)` door.
 *
 * 2. **`requires` is MANDATORY on any stop that describes a fact.** A tour on
 *    a catalog with no fires must not narrate a fire. A stop whose predicate
 *    fails is skipped — and where the ABSENCE is itself worth seeing there is
 *    a companion stop that names it ("no failing tests here — that's what a
 *    quiet city looks like"), which is the same law as `database.notes`:
 *    absence stays named, and unknown never renders as fine.
 *
 * Esc skips for good; progress is persisted so a reload resumes where the
 * viewer was instead of starting the lecture over.
 */

import type { CityDocument } from "../contract";
import type { OverlayId } from "./lenses";
import { TOUR_STOPS } from "./tour_stops";

const STORAGE_KEY = "tycoon-city.tour";

export interface TourStop {
  id: string;
  title: string;
  /**
   * Whether this catalog can honestly support the stop. Required on every
   * stop that states a fact — which is every stop that says a number, a name,
   * or "there is a…". A stop without one may only describe the RENDERER.
   */
  requires?: (doc: CityDocument) => boolean;
  body: (doc: CityDocument) => string;
  /** Semantic address → the key `visit()` understands. Null: stay put. */
  target?: (doc: CityDocument) => string | null;
  /** Turn this overlay on while the stop is showing. */
  overlay?: OverlayId;
}

export interface TourStore {
  read(): string | null;
  write(value: string): void;
}

export const tourStore: TourStore = {
  read: () => {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch {
      return null;
    }
  },
  write: (value) => {
    try {
      localStorage.setItem(STORAGE_KEY, value);
    } catch {
      /* progress lost, tour intact */
    }
  },
};

export interface TourDeps {
  doc: () => CityDocument;
  /** main.ts's camera door. The tour never touches a coordinate itself. */
  visit: (key: string) => void;
  lens: () => import("./lenses").Lens;
  /** Optional: lets a stop raise the overlay it is talking about. */
  setOverlay?: (id: OverlayId) => void;
  store?: TourStore;
}

export class Tour {
  private root: HTMLElement;
  private store: TourStore;
  private playlist: TourStop[] = [];
  private at = 0;

  constructor(private deps: TourDeps) {
    this.root = document.getElementById("tour")!;
    this.store = deps.store ?? tourStore;
    window.addEventListener("keydown", (event) => {
      if (this.root.hidden) return;
      const tag = (event.target as HTMLElement | null)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      if (event.key === "Escape") this.skip();
      if (event.key === "Enter" || event.key === "n" || event.key === "N") this.next();
    });
  }

  /**
   * Build the playlist for THIS document and lens, then resume.
   *
   * `restart` (`?tour=restart`) clears the saved progress; otherwise a tour
   * already finished stays closed — it has said its piece.
   */
  start(restart = false): void {
    if (restart) this.store.write("");
    const saved = this.store.read();
    if (!restart && saved === "done") return;
    this.playlist = this.stops();
    if (!this.playlist.length) return;
    // Persist the stop's ID, not its index: inserting a stop must not move
    // every reader mid-tour to a different subject. An unknown ID — a stop
    // that was renamed or dropped — starts over rather than guessing.
    const savedId = restart ? null : saved;
    const resumedAt = savedId ? this.playlist.findIndex((s) => s.id === savedId) : 0;
    this.at = resumedAt >= 0 ? resumedAt : 0;
    this.render();
  }

  /** Stops this catalog can honestly support, in this lens's order. */
  private stops(): TourStop[] {
    const honest = TOUR_STOPS.filter((stop) => !stop.requires || stop.requires(this.deps.doc()));
    const wanted = this.deps.lens().tourStops;
    if (!wanted.length) return honest;
    return wanted
      .map((id) => honest.find((stop) => stop.id === id))
      .filter((stop): stop is TourStop => stop !== undefined);
  }

  next(): void {
    if (this.at + 1 >= this.playlist.length) {
      this.finish();
      return;
    }
    this.at += 1;
    this.store.write(this.playlist[this.at]!.id);
    this.render();
  }

  /** Esc: the viewer is done being told things, for good. */
  skip(): void {
    this.finish();
  }

  private finish(): void {
    this.store.write("done");
    this.root.hidden = true;
  }

  private render(): void {
    const stop = this.playlist[this.at]!;
    const doc = this.deps.doc();
    this.store.write(stop.id);
    this.root.hidden = false;
    this.root.innerHTML =
      `<div class="tour-card" data-stop="${stop.id}">` +
      `<h3>${stop.title}<span class="tour-progress">${this.at + 1} / ${this.playlist.length}</span></h3>` +
      `<p>${stop.body(doc)}</p>` +
      `<div class="tour-buttons"><button class="tour-next">` +
      `${this.at + 1 >= this.playlist.length ? "done" : "next"}</button>` +
      `<button class="tour-skip">skip</button>` +
      `<span class="keys">enter / n · esc</span></div></div>`;
    this.root.querySelector(".tour-next")!.addEventListener("click", () => this.next());
    this.root.querySelector(".tour-skip")!.addEventListener("click", () => this.skip());
    if (stop.overlay && this.deps.setOverlay) this.deps.setOverlay(stop.overlay);
    const key = stop.target?.(doc) ?? null;
    if (key) this.deps.visit(key);
  }
}
