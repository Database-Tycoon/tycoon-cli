# `tycoon data status`

Per-source freshness, row counts, and capture history. The "is the pipeline alive?" view.

## Synopsis

```
tycoon data status [OPTIONS]
```

No flags. Reads from `data/raw.duckdb` + `.tycoon/metadata.duckdb` and prints a per-source status table.

## Output

```
                            Sources
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Name           ┃ Type       ┃ Last loaded  ┃ Runs   ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━┩
│ nyc-dot        │ rest_api   │ 2h 14m ago   │  12    │
│ mta-gtfs       │ filesystem │ 1d 3h ago    │   3    │
│ mta-bus-speeds │ rest_api   │ —            │   0    │
└────────────────┴────────────┴──────────────┴────────┘

Drill in with tycoon data history
```

Columns:

| Column | What it shows |
|---|---|
| **Name** | Source name from `tycoon.yml` |
| **Type** | dlt source type |
| **Last loaded** | Time since the most recent successful ingest. `—` if never run. |
| **Runs** | Total dlt loads captured in `metadata.duckdb`. `—` if observability hasn't fired. |

## When the metadata DB doesn't exist

```
                  Sources
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━┓
┃ Name           ┃ Type       ┃     ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━┩
│ nyc-dot        │ rest_api   │ —   │
└────────────────┴────────────┴─────┘
```

The Last-loaded and Runs columns degrade gracefully when `.tycoon/metadata.duckdb` is missing. This is expected on a fresh project — the metadata DB only appears after the first ingest.

## How "Last loaded" is computed

The latest `inserted_at` for the source's load IDs in `dlt_runs`. Reformatted as a coarse delta (`Nh Nm ago`, `Nd Nh ago`, etc.) so it's scannable across many sources.

For sources with `write_disposition: replace`, this is the moment of the most recent overwrite. For `append` it's the moment of the most recent batch. For `merge` it's the moment of the most recent upsert.

## Related

- [`tycoon data history`](history.md) — drill into individual runs
- [`tycoon doctor`](../doctor.md) — broader environment health check
- [Concepts → Observability is a side-effect of running](../../getting-started/concepts.md#3-observability-is-a-side-effect-of-running)
