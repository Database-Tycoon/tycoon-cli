/**
 * Guest flow (parked experiment, `?guests=1`): animated agents carrying
 * queries from the database to buildings and back, coloured by REAL verdicts —
 * a failing test or build error sends the guest home red. Per Stephen
 * (2026-08-04): Database Tycoon is an observation platform, not a game (yet) —
 * so there is no score, no ratings, no invented numbers. This module owns its
 * own fields only (enforced by tests/test_web_layering.py) and everything it
 * shows derives from the document's facts.
 */

import type { CityDocument, LotRecord } from "../contract";
import type { Tile } from "../sim/paths";
import { RoadNet } from "../sim/roadnet";
import type { Rng } from "../sim/rng";

const MAX_GUESTS = 48;
const SPAWN_PER_TICK = 0.35;
const STALE_HALF_LIFE_S = 14 * 86400;

export interface Guest {
  path: Tile[];
  progress: number;
  targetKey: string;
  happy: boolean;
  returning: boolean;
}

export class Guests {
  readonly guests: Guest[] = [];
  private weights: { lot: LotRecord; weight: number }[];
  private plant: Tile;

  private routes = new Map<string, Tile[]>();

  constructor(
    private doc: CityDocument,
    private rng: Rng,
  ) {
    this.plant = [doc.plant.x, doc.plant.y];
    // All vehicles travel on roads: each guest walks the drivable network
    // (roads + lot junctions + the utility corridor) from the plant. A
    // building the network cannot reach is simply never visited.
    const net = new RoadNet(doc);
    this.weights = doc.lots
      .filter((lot) => lot.powered)
      .map((lot) => {
        const staleness =
          lot.last_build_age_s !== null ? 0.5 ** (lot.last_build_age_s / STALE_HALF_LIFE_S) : 1;
        return { lot, weight: lot.target_density * staleness };
      })
      .filter((entry) => entry.weight > 0)
      .filter((entry) => {
        const path = net.path(this.plant, [[entry.lot.x, entry.lot.y]]);
        if (path) this.routes.set(entry.lot.object_key, path);
        return path !== null;
      });
  }

  tick(): void {
    let alive = 0;
    for (const guest of this.guests) {
      guest.progress += 1;
      if (guest.progress < guest.path.length) {
        this.guests[alive++] = guest;
        continue;
      }
      if (!guest.returning) {
        this.turnBack(guest);
        this.guests[alive++] = guest;
      }
    }
    this.guests.length = alive;

    if (this.weights.length === 0 || this.guests.length >= MAX_GUESTS) return;
    if (this.rng() < SPAWN_PER_TICK) {
      const target = this.pick();
      if (target) {
        this.guests.push({
          path: this.routes.get(target.object_key)!,
          progress: 0,
          targetKey: target.object_key,
          happy: true,
          returning: false,
        });
      }
    }
  }

  private pick(): LotRecord | null {
    const total = this.weights.reduce((sum, w) => sum + w.weight, 0);
    let roll = this.rng() * total;
    for (const { lot, weight } of this.weights) {
      roll -= weight;
      if (roll <= 0) return lot;
    }
    return this.weights.at(-1)?.lot ?? null;
  }

  private turnBack(guest: Guest): void {
    const lot = this.doc.lots.find((l) => l.object_key === guest.targetKey);
    // The verdict is a fact, not a simulation: failing tests and build errors
    // are what the warehouse reported.
    guest.happy = !(lot?.test_status === "fail" || lot?.build_status === "error");
    guest.returning = true;
    guest.path = [...guest.path].reverse();
    guest.progress = 0;
  }
}
