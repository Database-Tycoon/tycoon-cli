/**
 * The map legend, ported from the 2D renderer's bottom-right panel: names what
 * the colours mean in the database's own vocabulary. Built from the palette
 * module so a palette change can never leave the legend lying about a colour —
 * the 2D version once carried a row for a tile the generator could not emit.
 */

import type * as THREE from "three";
import type { CityDocument } from "../contract";
import { GROUND, PLANT_BODY, ZONE, dimmed } from "../palette";
import { USAGE_COLOR, usageSummary } from "../usage";

function css(color: THREE.Color): string {
  return `#${color.clone().convertLinearToSRGB().getHexString()}`;
}

/** `doc` is optional only so the legend keeps working for a caller that has
 * no document yet; with one it can name the weather, which is the only row
 * whose meaning depends on what the catalog actually reported. */
export function buildLegend(doc?: CityDocument): void {
  const rows: [string, string[], string?][] = [
    ["table / view", [css(ZONE.industrial!), css(ZONE.commercial!), css(ZONE.residential!)]],
    ["no lineage", [css(dimmed(ZONE.residential!))]],
    ["road (lineage)", [css(GROUND.road!)]],
    ["power line", [css(GROUND.power_line!)]],
    ["database", [css(PLANT_BODY)]],
    ["tests: fail = ON FIRE / warn / pass", ["#ff5a1f", "#e0a832", "#5ee07a"]],
    ["source late (dbt SLA)", ["#e0a832"]],
    // Not a colour row, but the legend is where meaning lives: traffic is a
    // fact (a recent build/load on that street), not ambience.
    ["traffic = built in the last hour", []],
    // The road-load overlay's ramp: expected compute per street, measured
    // from run history (cadence x mean build cost). Engine-neutral wording —
    // Snowflake bills this as warehouses, MotherDuck as ducklings.
    ["road heat = compute load (s/day)", ["#3fa7ff", "#ffd75e", "#ff5533"]],
    ["stale source = worn building, contractor van", ["#b3945f", "#d8a028"]],
  ];
  // Weather is the one row that must state an ABSENCE out loud. `cells: []`
  // means nothing was judged — and clear-because-unknown must never be shown
  // as clear-because-fine, so the legend names the unknown instead of
  // quietly omitting the row. The full note rides along as the tooltip.
  const weather = doc?.weather;
  if (weather) {
    const weathered = weather.cells.filter((cell) => cell.condition !== "clear").length;
    rows.push(
      weathered
        ? [
            `fog = district fed by a late source (${weathered})`,
            ["#e4ecf2", "#b7bec6"],
            weather.note,
          ]
        : ["weather: none to show", [], weather.note],
    );
  }
  // Usage is the second row that must state an absence out loud, and the
  // stakes are higher than the weather's: a table nobody has MEASURED must
  // never read as a table nobody USES, because the second is a deprecation
  // signal somebody would act on. So the unknown count is named in its own
  // row whenever there is one, and the source discriminator — run appearances
  // here, query history on an engine that has one — rides along as the
  // tooltip, because these numbers mean different things per engine.
  if (doc) {
    const usage = usageSummary(doc);
    const note =
      `source: ${usage.source ?? "none"} — build/run appearances, not query traffic; ` +
      `beacon height is cadence relative to this city's busiest object`;
    if (usage.measured) {
      rows.push([
        `usage beacon = runs/day (${usage.busy} busy)`,
        [USAGE_COLOR.busyLow, USAGE_COLOR.busyHigh],
        note,
      ]);
      if (usage.quiet) {
        rows.push([`quiet lid = measured, little used (${usage.quiet})`, [USAGE_COLOR.quiet], note]);
      }
      if (usage.unrated) {
        rows.push([
          `usage ring = seen, cadence unknown (${usage.unrated})`,
          [USAGE_COLOR.unrated],
          "fewer than two appearances, or a zero span: no cadence to report",
        ]);
      }
    }
    if (usage.unknown) {
      rows.push([
        `usage unmeasured for ${usage.unknown} — unknown, not unused`,
        [],
        "the run history says nothing about these objects; that is a gap in the history, not a fact about the table",
      ]);
    }
  }
  const root = document.getElementById("legend")!;
  root.innerHTML = rows
    .map(
      ([label, colors, title]) =>
        `<div class="legend-row"${title ? ` title="${title.replace(/"/g, "&quot;")}"` : ""}>${colors
          .map((c) => `<span class="swatch" style="background:${c}"></span>`)
          .join("")}<span>${label}</span></div>`,
    )
    .join("");
}
