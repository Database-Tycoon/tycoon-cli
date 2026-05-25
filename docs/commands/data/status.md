# `tycoon data status`

The layered view of the project: **sources → staging → intermediate → marts**. The "is the pipeline alive?" view, organized by the canonical analytics-warehouse architecture.

## Synopsis

```
tycoon data status [OPTIONS]
```

No flags. Reads from `data/raw.duckdb`, `.tycoon/metadata.duckdb`, and the dbt manifest at `<dbt_project_dir>/target/manifest.json`.

## Output

```
╭─────────────────────────────────────────────────────────────╮
│ Data Status                                                 │
╰─────────────────────────────────────────────────────────────╯

╭─────────╮
│ Sources │
╰─────────╯
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Source         ┃ Vendor   ┃ Schema       ┃ Last Sync    ┃ Freshness ┃ Runs ┃ Tables ┃   Rows ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ pokeapi        │ dlt      │ raw_pokeapi  │ 2026-05-25.. │ 12m ago   │   3  │   3    │ 1,432  │
│ orders_pg      │ fivetran │ raw_pg       │ —            │ —         │   —  │   —    │   —    │
└────────────────┴──────────┴──────────────┴──────────────┴───────────┴──────┴────────┴────────┘

Drill in with tycoon data history for per-run detail.

╭─────────╮
│ Staging │
╰─────────╯
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Model                  ┃ Schema ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ stg_pokeapi__pokemon   │ main   │
│ stg_pokeapi__berry     │ main   │
│ stg_pokeapi__type      │ main   │
└────────────────────────┴────────┘
3 model(s) — last build 8m ago

╭──────────────╮
│ Intermediate │
╰──────────────╯
> No intermediate models. Optional layer — typically used to combine staging models before marts.

╭───────╮
│ Marts │
╰───────╯
┏━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Model          ┃ Schema ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ fct_pokemon    │ main   │
└────────────────┴────────┘
1 model(s) — last build 8m ago
```

## What each panel shows

**Sources** — dlt sources from `tycoon.yml` and Fivetran connectors from the metadata API, unified into one table. The `Vendor` column distinguishes them. Per-source freshness (Last Sync, Freshness, Runs, Tables, Rows) is populated for dlt sources from `data/raw.duckdb` + `.tycoon/metadata.duckdb`; Fivetran rows surface via a follow-up service / sync-state detail table when `stack.ingestion = fivetran`.

**Staging / Intermediate / Marts** — dbt models classified via the manifest (see [`docs/recipes/layered-architecture.md`](../../recipes/layered-architecture.md) for the classification rules). Each panel lists the models in that layer and reports the last-build timestamp computed by joining `dbt_runs` against `dbt_nodes` in the metadata DB.

## Empty states

| State | Panel behaviour |
|---|---|
| No sources registered | Sources panel shows a hint to run `tycoon data sources add` |
| No `data/raw.duckdb` yet | Sources rows render with `—` in freshness columns |
| No `.tycoon/metadata.duckdb` yet | Runs column shows `—`; staging/intermediate/marts last-build shows `never` |
| `transformation: none` in `tycoon.yml` | The three dbt panels collapse to a single hint pointing at `tycoon register dbt` |
| No `target/manifest.json` (dbt never compiled) | The three dbt panels collapse to a single hint pointing at `tycoon data transform run` |

Tycoon stays opinionated about the layered architecture even when it's not in place yet — the panels always appear, with hints describing what's missing.

## Related

- [`tycoon data history`](history.md) — drill into individual runs (now supports `--layer`)
- [`tycoon doctor`](../doctor.md) — broader environment health check, including the v0.1.7 layer-coverage row
- [Layered architecture recipe](../../recipes/layered-architecture.md) — the mental model behind the panels
- [Concepts → Observability is a side-effect of running](../../getting-started/concepts.md#3-observability-is-a-side-effect-of-running)
