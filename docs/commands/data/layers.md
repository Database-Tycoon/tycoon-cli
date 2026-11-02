# `tycoon data layers`

A text view of the layered architecture: the **same data** the 3D city
renders, without the browser.

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
as *unclassified*; tycoon has opinions only about the surfaces it manages.

```
tycoon data layers
```

Each dbt panel ends with the layer's model count and when it was last built,
read from the run ledger `tycoon data transform run` captures. Drill into a
failing test with `tycoon fire`, or into one run with `tycoon data history`.
