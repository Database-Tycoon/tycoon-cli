# The layered architecture: sources → staging → intermediate → marts

Tycoon is opinionated about the **layered analytics warehouse**. Every
table in a tycoon project should live in one of four layers, and the
direction of dependency only ever runs left to right:

```
sources  →  staging  →  intermediate  →  marts
```

This page explains why, how tycoon classifies your tables into layers,
and how to override the defaults when your project uses different
folder names.

## The four layers

| Layer | Owner | What lives here | Example |
|---|---|---|---|
| **sources** | dlt / Fivetran / Airbyte | Raw, unmodified data exactly as it arrived | `raw_pokeapi.pokemon`, `raw_stripe.charges` |
| **staging** | dbt | One model per source table; renames, casts, simple cleaning | `stg_pokeapi__pokemon` |
| **intermediate** | dbt | Joins between staging models; business logic; not consumer-facing | `int_orders_with_customers` |
| **marts** | dbt | Consumer-facing facts + dimensions; the tables BI tools query | `fct_orders`, `dim_customer`, `obt_customer_orders` |

The pattern is documented across the analytics community — dbt's own
docs, Kimball, the medallion architecture all teach the same shape
under different names. Tycoon adopts dbt's vocabulary because most
tycoon users come in via dbt.

## How tycoon classifies tables

### Sources

Sources are identified by **vendor metadata**, not by table name:

* **dlt sources** are registered in `tycoon.yml`'s `sources:` block.
  Each entry has a `schema:` field — that's the raw schema in DuckDB
  (or your warehouse) that tycoon flags as the source layer.
* **Fivetran connectors** come from the Fivetran Metadata API (see
  the [Fivetran metadata recipe](fivetran-metadata.md)).

There's nothing to configure for layer-classification on the source
side beyond what you already set up to register the source.

### dbt models

dbt models classify via the **folder convention** in your `dbt_project/`:

| Folder | Layer |
|---|---|
| `models/staging/` | staging |
| `models/intermediate/` | intermediate |
| `models/marts/` | mart |
| `models/core/` or `models/published/` | mart (common aliases) |

Nested folders are fine — `models/staging/finance/stg_invoices.sql`
still classifies as staging.

### Snapshots and seeds

dbt snapshots (`snapshots/snap_*.sql`) and seeds (`seeds/*.csv`) get
their own layer values (`snapshot` / `seed`) regardless of where they
live on disk.

## When tycoon's classifier shows up

| Surface | What changes |
|---|---|
| `tycoon data status` | Four panels: Sources / Staging / Intermediate / Marts |
| `tycoon doctor` | Reports any registered source that has no staging model |
| `tycoon semantics scaffold` | Generates OSI for tables classified as marts |
| `tycoon data history --layer mart` | Filter run history to invocations that touched marts |

Hand-rolled tables that don't come from dbt or a registered ingestion
source classify as `unclassified` and are ignored by these surfaces.
That's the right behaviour — tycoon governs dbt + ingestion, and
that's what it has an opinion about.

## Overriding the defaults

Some projects use folder names that don't match the conventional set
(say `models/curated/` instead of `models/marts/`). dbt's `meta`
mechanism handles this without any new tycoon configuration:

### Per-folder override — `dbt_project.yml`

```yaml
# dbt_project.yml
models:
  my_project:
    curated:
      +meta:
        tycoon_layer: mart
```

Every model under `models/curated/` now classifies as `mart`.

### Per-model override — `schema.yml`

```yaml
# models/scratch/_models.yml
version: 2
models:
  - name: fct_quarterly_summary
    meta:
      tycoon_layer: mart
```

A one-off model in `models/scratch/` is promoted to `mart` for
tycoon's surfaces.

### Why not a `layers:` block in `tycoon.yml`?

It was considered and rejected. dbt already owns the model-layer
mapping via folder convention + `meta`. Duplicating that into
`tycoon.yml` would create two places truth could live and they'd
inevitably drift. **Classification authority lives in the tool that
owns the object** — dbt for models, the ingestion config for sources.

## What about projects without dbt?

Projects with `stack.transformation: none` still see the staging /
intermediate / marts panels in `tycoon data status` — they're just
populated with empty-state hints. Tycoon stays opinionated about the
architecture even when it's not in place yet:

```text
─── Staging ───
No staging models. Scaffold one with `tycoon data analyze <source>`.
```

When you're ready to add dbt, `tycoon register dbt --create`
bootstraps a fresh project wired to your warehouse in seconds.

## Adopting the model in an existing project

If you have a flat `models/` directory and want to migrate:

1. Make the three folders: `models/staging/`, `models/intermediate/`,
   `models/marts/`.
2. Move your existing files based on what they actually do — anything
   that reads from `{{ source(...) }}` typically belongs in staging;
   anything that reads from staging models and emits consumer-shaped
   tables belongs in marts.
3. Run `tycoon data transform run` to regenerate the manifest.
4. Run `tycoon doctor` to confirm every registered source has a
   staging model.

The migration is mechanical — dbt itself doesn't care about the
folders; the layered convention is purely a discipline that tycoon
(and most of the community's tooling) now reads from.
