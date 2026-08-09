/**
 * Fire trucks: dispatch made visible — ON ROADS ONLY (Stephen, 2026-08-05:
 * "the vehicles must be required to travel on roads"). Each truck BFS-routes
 * from the firehouse over ROAD tiles (the planner wires the station in via a
 * civic access road) to a road tile beside the burning building, parks with
 * its light bar flashing, drives home, repeats.
 *
 * A fire the road network cannot reach gets NO truck — a burning orphan in
 * the streetless suburb is unreachable by design, and pretending otherwise
 * would be theater. The truck itself is a restatement of a fact
 * (`test_status === "fail"`, unresolved), never a claim that a fix is
 * running: the firehouse panel states whether a responder is connected.
 *
 * Deterministic in elapsed time (phase from the fire's coordinates, no RNG);
 * `?settle=1` never ticks this, so screenshots stay reproducible.
 */

import * as THREE from "three";
import type { CityDocument, LotRecord } from "../contract";
import type { Tile } from "../sim/paths";
import { RoadNet } from "../sim/roadnet";
import { disposeTree } from "./dispose";

const SPEED = 3.2; // tiles per second
const PAUSE = 2.4; // seconds parked at the callout before heading home

interface Truck {
  group: THREE.Group;
  light: THREE.Mesh;
  path: Tile[]; // station -> roadside beside the callout, road tiles only
  phase: number;
}

/** What a fleet responds to and how its vehicles look. */
export interface FleetSpec {
  select: (lot: LotRecord) => boolean;
  cab: string;
  light: string;
  phaseSalt: number; // keeps two fleets' cycles from moving in lockstep
}

const FIRE_SPEC: FleetSpec = {
  select: (lot) => lot.test_status === "fail",
  cab: "#c03028",
  light: "#ff3030",
  phaseSalt: 0,
};

// Contractors (Stephen, 2026-08-05: stale sources "need to have contractors
// come and fix it"): amber repair vans answer freshness SLA violations. They
// share the station and the roads-only rule; like the fire trucks they
// restate a measured fact (dbt's sources.json verdict, unresolved) and never
// claim a fix is running.
const REPAIR_SPEC: FleetSpec = {
  select: (lot) => lot.freshness_status === "warn" || lot.freshness_status === "error",
  cab: "#d8a028",
  light: "#ffb830",
  phaseSalt: 3,
};

export class DispatchFleet {
  readonly group = new THREE.Group();
  private trucks: Truck[] = [];
  private elapsed = 0;
  private unreachableCount = 0;
  private spec: FleetSpec;
  private doc: CityDocument;
  private net: RoadNet | null = null;
  /** The callouts this fleet answers by default — what an override replaces. */
  private standing: LotRecord[] = [];

  /** Vehicles on duty — the e2e counting hook. */
  get count(): number {
    return this.trucks.length;
  }

  /** Callouts the road network cannot reach (e.g. streetless orphans). */
  get unreachable(): number {
    return this.unreachableCount;
  }

  constructor(doc: CityDocument, spec: FleetSpec) {
    this.spec = spec;
    this.doc = doc;
    if (!doc.firehouse) return;
    this.net = new RoadNet(doc);
    this.standing = doc.lots.filter(spec.select);
    this.build(this.standing);
  }

  /**
   * Answer exactly `keys` instead of this fleet's own selector; `null`
   * restores it. This is how the fire trucks follow a run replay's fires
   * without knowing a replay exists — the fleet still only ever drives to a
   * building the road network can reach, and still never claims a fix.
   */
  setOverride(keys: Set<string> | null): void {
    if (!this.doc.firehouse) return;
    this.build(
      keys === null ? this.standing : this.doc.lots.filter((l) => keys.has(l.object_key)),
    );
  }

  /** Replace the fleet wholesale, freeing the vehicles it retires. */
  private build(callouts: LotRecord[]): void {
    const net = this.net;
    if (!net || !this.doc.firehouse) return;
    disposeTree(this.group);
    this.group.clear();
    this.trucks = [];
    this.unreachableCount = 0;
    const spec = this.spec;
    for (const lot of callouts) {
      // Goal: any drivable tile orthogonally beside the burning building.
      const goals = (
        [
          ...Array.from({ length: lot.w }, (_, dx): [number, number][] => [
            [lot.x + dx, lot.y - 1],
            [lot.x + dx, lot.y + lot.h],
          ]).flat(),
          ...Array.from({ length: lot.h }, (_, dy): [number, number][] => [
            [lot.x - 1, lot.y + dy],
            [lot.x + lot.w, lot.y + dy],
          ]).flat(),
        ] as Tile[]
      ).filter(([x, y]) => net.isDrivable(x, y));
      const path = net.path([this.doc.firehouse.x, this.doc.firehouse.y], goals);
      if (!path) {
        this.unreachableCount += 1;
        continue;
      }
      const body = new THREE.Group();
      const cab = new THREE.Mesh(
        new THREE.BoxGeometry(0.34, 0.16, 0.18),
        new THREE.MeshBasicMaterial({ color: spec.cab }),
      );
      cab.position.y = 0.1;
      const light = new THREE.Mesh(
        new THREE.BoxGeometry(0.08, 0.06, 0.08),
        new THREE.MeshBasicMaterial({ color: spec.light }),
      );
      light.position.y = 0.21;
      body.add(cab, light);
      this.group.add(body);
      this.trucks.push({
        group: body,
        light,
        path,
        phase: (lot.x * 13 + lot.y * 7 + spec.phaseSalt) % 5,
      });
    }
  }

  tick(delta: number): void {
    this.elapsed += delta;
    for (const truck of this.trucks) {
      const travel = truck.path.length / SPEED;
      const cycle = travel + PAUSE + travel + PAUSE;
      const t = (this.elapsed + truck.phase) % cycle;
      let at: number;
      if (t < travel) {
        at = t * SPEED; // outbound
      } else if (t < travel + PAUSE) {
        at = truck.path.length - 1; // parked at the fire
      } else if (t < travel + PAUSE + travel) {
        at = truck.path.length - 1 - (t - travel - PAUSE) * SPEED; // home
      } else {
        at = 0; // parked at the station
      }
      const i = Math.min(Math.max(Math.floor(at), 0), truck.path.length - 1);
      const next = Math.min(i + 1, truck.path.length - 1);
      const f = at - i;
      const [x0, y0] = truck.path[i]!;
      const [x1, y1] = truck.path[next]!;
      truck.group.position.set(x0 + 0.5 + (x1 - x0) * f, 0.02, y0 + 0.5 + (y1 - y0) * f);
      // The light bar flashes while on duty away from the station.
      const onDuty = at > 0.5;
      (truck.light.material as THREE.MeshBasicMaterial).color.set(
        onDuty && Math.floor(this.elapsed * 6) % 2 === 0 ? "#ffffff" : this.spec.light,
      );
    }
  }
}

/** Red engines answering fires (test_status === "fail"). */
export class FireTrucks extends DispatchFleet {
  constructor(doc: CityDocument) {
    super(doc, FIRE_SPEC);
  }
}

/** Amber contractor vans answering stale sources (freshness warn/error). */
export class RepairVans extends DispatchFleet {
  constructor(doc: CityDocument) {
    super(doc, REPAIR_SPEC);
  }
}
