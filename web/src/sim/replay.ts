/**
 * Play the server's build-replay schedule: every building drops to zero and
 * grows back during its own (start, duration) window, in dependency order.
 * Pure presentation over a schedule Python derived from measured durations —
 * the note carried on the plan ("durations measured, ordering reconstructed")
 * is displayed for the whole run, because the ordering is honest but rebuilt.
 */

import type { CityDocument } from "../contract";

const END_GRACE_TICKS = 15; // hold the finished city briefly before ending

export class Replay {
  private tickCount = 0;
  private byLot: { start: number; end: number }[] | null = null;

  constructor(private doc: CityDocument) {}

  get available(): boolean {
    return this.doc.replay !== null;
  }

  get active(): boolean {
    return this.byLot !== null;
  }

  get note(): string {
    return this.doc.replay?.note ?? "";
  }

  start(): void {
    if (!this.doc.replay) return;
    const windows = new Map(
      this.doc.replay.steps.map((s) => [s.object_key, { start: s.start, end: s.start + s.duration }]),
    );
    // Index-aligned with doc.lots (the Buildings instance order). Objects the
    // schedule does not cover keep their height: absent is unknown, and an
    // unknown building vanishing during replay would read as a build failure.
    this.byLot = this.doc.lots.map(
      (lot) => windows.get(lot.object_key) ?? { start: -1, end: -1 },
    );
    this.tickCount = 0;
  }

  /** One 10 Hz tick; returns per-lot height factors, or null when finished. */
  tick(): number[] | null {
    if (!this.byLot || !this.doc.replay) return null;
    this.tickCount += 1;
    if (this.tickCount > this.doc.replay.span_ticks + END_GRACE_TICKS) {
      this.byLot = null;
      return null;
    }
    const t = this.tickCount;
    return this.byLot.map(({ start, end }) => {
      if (start < 0) return 1; // uncovered: keep the building standing
      if (t < start) return 0;
      if (t >= end) return 1;
      return (t - start) / (end - start);
    });
  }
}
