/**
 * Screen-space collision handling for the district and civic chips (#385).
 *
 * CSS2DRenderer places each chip at its anchor's projection and knows nothing
 * about its neighbours, so two anchors a few tiles apart draw one chip over
 * the other once the camera pitches down. This pass runs after every
 * `labels.render()`: it takes the chips in priority order, keeps each one
 * where it landed if that spot is free, otherwise stacks it one or two chip
 * heights above or below, and hides it only when every slot is taken.
 *
 * Nothing accumulates between frames. CSS2DRenderer rewrites each chip's
 * `transform` on every render, so the nudge appended here is recomputed from
 * the fresh placement each time.
 */

const GAP_PX = 3;
/** Slots tried in order, in chip heights: stay, then up, then down. Two steps
 * each way keeps a nudged chip visibly attached to the place it names. */
const SLOTS = [0, -1, 1, -2, 2];

interface Box {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

function overlaps(a: Box, b: Box): boolean {
  return a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
}

function shifted(box: Box, dy: number): Box {
  return { left: box.left, right: box.right, top: box.top + dy, bottom: box.bottom + dy };
}

/** `data-label-priority` on a chip ranks it; a chip without one ranks last.
 * The sort is stable, so equal ranks keep scene order. */
export function declutterLabels(root: HTMLElement): void {
  const chips = [...root.querySelectorAll<HTMLElement>(".district-label")].filter(
    (el) => el.style.display !== "none",
  );
  for (const el of chips) el.style.visibility = "";

  const ranked = chips
    .map((el) => ({
      el,
      box: el.getBoundingClientRect() as Box,
      priority: Number(el.dataset.labelPriority ?? 0),
    }))
    .sort((a, b) => b.priority - a.priority);

  const placed: Box[] = [];
  for (const { el, box, priority } of ranked) {
    const step = box.bottom - box.top + GAP_PX;
    // A district chip is how a viewer finds the schema, so it may move further
    // than a civic chip before giving up; it is never hidden.
    const slots = priority > 0 ? [...SLOTS, -3, 3, -4, 4] : SLOTS;
    const slot = slots.find((k) => !placed.some((p) => overlaps(shifted(box, k * step), p)));
    if (slot === undefined && priority <= 0) {
      el.style.visibility = "hidden";
      continue;
    }
    const dy = (slot ?? 0) * step;
    if (dy !== 0) el.style.transform += ` translateY(${dy}px)`;
    placed.push(shifted(box, dy));
  }
}
