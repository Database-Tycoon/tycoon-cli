/**
 * The first-run lens picker and the footer lens switcher.
 *
 * The picker is a modal over the ALREADY-MOUNTED city — the city is behind it,
 * lit and running, so the choice is made against the thing it re-weights
 * rather than in front of a splash screen.
 *
 * Three hard constraints, all of them things that would otherwise break the
 * harness or the user's trust:
 *
 * 1. **It must never gate `body[data-ready="1"]`.** That flag is the e2e
 *    readiness signal and it cannot wait on a human. The picker is a sibling
 *    of the render loop, not a step in it.
 * 2. **Suppressed under `?settle=1` and under any explicit `?lens=`.** A
 *    screenshot harness and a shared link both arrive with their mind made up.
 * 3. **Persist only on an explicit pick** — including "skip", which stores
 *    `"none"` so the picker never nags again. Fiddling with chips or overlays
 *    afterwards never rewrites the stored preset; if it did, the preset would
 *    stop meaning anything within a minute of use.
 */

import type { Lens } from "./lenses";
import { LENSES, LENS_LIST, NO_LENS, type LensStore } from "./lenses";

const STORAGE_KEY = "tycoon-city.lens";

/**
 * `localStorage` behind the injectable seam. Wrapped in try/catch because a
 * private-mode or storage-disabled browser must lose the PREFERENCE, never the
 * city: every failure here degrades to "no stored lens".
 */
export const lensStore: LensStore = {
  read(): string | null {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch {
      return null;
    }
  },
  write(id: string): void {
    try {
      localStorage.setItem(STORAGE_KEY, id);
    } catch {
      /* preference lost, city intact */
    }
  },
  clear(): void {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* as above */
    }
  },
};

function escapeHtml(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
}

/** What a card promises, in the app's own vocabulary. Presentation words
 * only — nothing here may suggest the numbers change. */
function cardDetail(lens: Lens): string {
  const bits = [
    lens.chipOrder.length ? `leads with ${lens.chipOrder.slice(0, 2).join(" + ")}` : "",
    lens.overlays.length ? `${lens.overlays.join(" + ")} overlay` : "no overlay",
    lens.defaultPanel === "none" ? "" : `opens the ${lens.defaultPanel} panel`,
  ].filter(Boolean);
  return bits.join(" · ");
}

export class LensPicker {
  private root: HTMLElement;

  constructor(private onPick: (lens: Lens, persist: boolean) => void) {
    this.root = document.getElementById("lens-modal")!;
  }

  open(): void {
    const cards = LENS_LIST.map(
      (lens) =>
        `<button class="lens-card" data-lens="${lens.id}">` +
        `<b>${escapeHtml(lens.label)}</b>` +
        `<span class="blurb">${escapeHtml(lens.blurb)}</span>` +
        `<span class="detail">${escapeHtml(cardDetail(lens))}</span></button>`,
    ).join("");
    this.root.innerHTML =
      `<div class="lens-modal-card"><h2>Which job are you here to do?</h2>` +
      `<p class="note">A lens re-weights what this HUD shows you first. It never
       changes a number: every lens counts the same city.</p>` +
      `<div class="lens-cards">${cards}</div>` +
      `<button class="lens-skip" data-lens="none">skip — show me everything</button></div>`;
    this.root.hidden = false;
    for (const button of this.root.querySelectorAll<HTMLElement>("[data-lens]")) {
      button.addEventListener("click", () => {
        const id = button.dataset.lens!;
        this.close();
        // Skip persists "none" too: a viewer who declined once has chosen,
        // and being asked again every reload is the nag this prevents.
        this.onPick(id === "none" ? NO_LENS : LENSES[id as keyof typeof LENSES], true);
      });
    }
  }

  close(): void {
    this.root.hidden = true;
  }
}

/**
 * The footer switcher: the choice stays changeable without clearing storage.
 * Changing it IS an explicit pick, so it persists — unlike toggling an overlay
 * by hand, which never does.
 */
export class LensSwitcher {
  private root: HTMLElement;

  constructor(private onPick: (lens: Lens, persist: boolean) => void) {
    this.root = document.getElementById("lens-switch")!;
    this.root.innerHTML =
      `<label>lens <select id="lens-select" title="role lens — presentation only">` +
      [NO_LENS, ...LENS_LIST]
        .map((lens) => `<option value="${lens.id}">${escapeHtml(lens.label)}</option>`)
        .join("") +
      `</select></label>`;
    this.select().addEventListener("change", () => {
      const id = this.select().value;
      this.onPick(id === "none" ? NO_LENS : LENSES[id as keyof typeof LENSES], true);
    });
  }

  private select(): HTMLSelectElement {
    return this.root.querySelector("select")!;
  }

  /** Reflect the active lens without firing a pick. */
  setLens(lens: Lens): void {
    this.select().value = lens.id;
  }
}
