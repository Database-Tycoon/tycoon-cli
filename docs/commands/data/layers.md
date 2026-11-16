# `tycoon data layers`

A text view of the layered architecture: the same data the 3D city
renders, without the browser.

## Layers are the city's rings

The canonical warehouse layers map to the city's radial geometry: **marts
build downtown** against the civic core, intermediate and staging ring
outward from it, and **sources sit on the outskirts**. (Districts are a
different thing on the map: one plate per *schema*. A layer can span many
districts.)

`tycoon data layers` prints one panel per layer, sources first, and adds
the vendor each object comes from:

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

## Sources

Each dlt source shows its last sync in local time (as `tycoon data history`
does), how fresh that is, how many loads were captured, and the tables and
rows of the last load.

## Staging, intermediate and marts

Every model row shows two things from the run ledger that `tycoon data
transform run` captures:

- **Latest run:** the model's status in the newest run that included it
  (`success`, `error`, `skipped`), or `not run`.
- **Last successful build:** how long ago it last built, or `never`. A model
  whose newest run errored keeps the time of its last success here.

The line under each panel gives the model count, the newest successful
build of any model in the layer, and how many models failed in their
latest run:

```
2 model(s), newest successful build 5m ago, 1 failed in their latest run
```

Look at the failed run with `tycoon data history`, and at failing tests
with `tycoon fire`.
