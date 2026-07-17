# Dependencies

Every package tycoon pins in `pyproject.toml`, what it does, and where it shows up at runtime. Useful when auditing the install footprint or deciding which extras to skip.

The base install (`pip install database-tycoon`) is enough for the full data pipeline (`init`, `data sources`, `data transform`, `data sync`, `data analyze`, `register`, `doctor`). One optional extra adds the docs surface.

## Base — always installed

| Package | Pinned | Used for |
|---|---|---|
| `typer` | `0.25.0` | CLI surface — every `tycoon …` command. ~26 import sites. |
| `rich` | `15.0.0` | Status tables, panels, colored output. Powers `tycoon doctor`, `tycoon data status`. |
| `dbt-core` | `1.11.8` | The dbt engine. Tycoon shells out to `dbt build` from `tycoon data transform`. Not imported as a Python lib in tycoon's own code, but required at runtime so `dbt` resolves on PATH. |
| `dbt-duckdb` | `1.10.1` | dbt adapter for DuckDB / MotherDuck. Required because every tycoon-scaffolded `profiles.yml` uses the `duckdb` adapter. |
| `dlt[duckdb]` | `1.26.0` | Ingestion engine. Powers `tycoon data sources run`. The `[duckdb]` extra wires dlt's DuckDB destination. ~20 import sites. |
| `pandas` | `3.0.3` | Nothing in `src/` imports it, but dlt's filesystem source (downloaded on demand via `dlt init`) needs it for its CSV reader — CSV ingestion fails without it. |
| `duckdb` | `1.5.2` | Local analytical engine. Backs `.tycoon/raw.duckdb`, `.tycoon/metadata.duckdb`, `data sync`, every `data query`. ~22 import sites. |
| `httpx` | `0.28.1` | HTTP client used by `tycoon notify` webhooks and the Fivetran / Socrata ingestion clients. |
| `pyyaml` | `6.0.3` | Reading / writing `tycoon.yml`, `dbt_project.yml`, `profiles.yml`, dlt source configs, AGENTS.md scaffolding, rill scaffolding. |
| `pydantic` | `2.13.3` | Typed config models in `src/tycoon/project.py` (the `tycoon.yml` schema). |

## `[docs]` — optional MkDocs site

`pip install 'database-tycoon[docs]'`

| Package | Pinned | Used for |
|---|---|---|
| `mkdocs` | `1.6.1` | Static-site generator that backs `tycoon docs serve / build`. Pulled transitively by `mkdocs-material`; pinned explicitly so the version is reproducible. |
| `mkdocs-material` | `9.5.49` | Material theme used by [the docs site you're reading right now](https://database-tycoon.github.io/tycoon-cli/). |

## Dev — `[dependency-groups]`

`uv sync` (no `--no-dev`) installs these. Not exposed as a `pip install` extra.

| Package | Pinned | Used for |
|---|---|---|
| `pytest` | `9.0.3` | Test runner. `pyproject.toml`'s `[tool.pytest.ini_options]` defines the `e2e` / `offline_e2e` markers. |
| `pytest-cov` | `>=7.1.0` | Coverage reporter. The coverage floor is enforced via `[tool.coverage.report] fail_under`. |
| `syrupy` | `5.2.0` | Snapshot assertions for CLI output tests. |

## Footprint at a glance

| Install line | Direct top-level packages |
|---|---|
| `pip install database-tycoon` | 10 |
| `+ [docs]` | +2 |
| `+ dev` | +3 |

## Update cadence

Tycoon pins exact versions for every direct dep so a fresh `pip install database-tycoon==<X>` resolves to the same versions every time, regardless of when the install happens. We refresh pins at release boundaries — see the changelog under each `[X.Y.Z]` section for "Dependencies bumped" entries when the bump is meaningful (security, compatibility, new feature dependency).
