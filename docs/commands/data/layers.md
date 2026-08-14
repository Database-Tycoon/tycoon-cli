# `tycoon data layers` / `tycoon data health`

Text views of the layered architecture and its health — the **same data** the
3D city renders, without the browser.

## Layers are the city's rings

The canonical warehouse layers map to the city's radial geometry: **marts
build downtown** against the civic core, intermediate and staging ring
outward from it, and **sources sit on the outskirts**. (Districts are a
different thing on the map: one plate per *schema*. A layer can span many
districts.)

`tycoon data layers` lists every classified object ring by ring, and adds
the vendor each one comes from:

- **dlt** sources, from `tycoon.yml`'s `sources:` block
- **Fivetran** connectors, from the latest `tycoon data fivetran sync` snapshot
- **dbt** models, classified from the manifest's folder convention
  (`models/staging/` → staging, …) with per-model `meta.tycoon_layer`
  overrides taking priority

Objects tycoon doesn't govern (hand-rolled SQL, notebook outputs) classify
as *unclassified* — tycoon has opinions only about the surfaces it manages.

```
tycoon data layers
```

## `tycoon data health`

The city UI's **health strip** as text: one chip per problem class —
failing tests, build errors, late sources, test warnings, stale builds
(14+ days), schema drift (7 days). Every chip is a count of problematic
objects from the same fields the city colors buildings with.

```
tycoon data health
```

Drill into any count with `tycoon fire` (failing tests), `tycoon repair`
(late sources), or `tycoon data history` (per-run detail).
