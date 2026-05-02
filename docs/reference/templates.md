# Templates reference

Tycoon ships four built-in templates. Pick one with `tycoon init
--template <name>` or list them with `tycoon init --list-templates`.

## When to use which

| Template | What you get | Network needed | Best for |
|---|---|---|---|
| [`csv-import`](#csv-import) | CSV ingest + dbt + Rill | No | Smoke-testing the full pipeline offline |
| [`nyc-transit`](#nyc-transit) | Live NYC public-data feeds | Yes (no auth) | Demo / showing real ingestion |
| [`github-analytics`](#github-analytics) | GitHub repo metrics | Yes (`GITHUB_TOKEN`) | Tracking your own / a target repo |
| [`weather-station`](#weather-station) | NOAA weather data | Yes (no auth) | Time-series / parameterized template demo |

---

## `csv-import`

The fully-offline template. Ships with a working dbt project and a
sample CSV so the full ingest → transform pipeline runs end-to-end on
a fresh install.

```bash
tycoon init --template csv-import --name my-project
tycoon data sources run files
tycoon data transform run
```

### What's in it

```
my-project/
├── tycoon.yml
├── data/input/widgets.csv          # bundled sample data
├── dbt_project/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/staging/
│       ├── stg_widgets.sql
│       └── schema.yml
└── rill/rill.yaml
```

### Generated `tycoon.yml`

```yaml
name: my-project
sources:
  files:
    type: filesystem
    schema: raw_files
    config:
      bucket_url: data/input
      file_glob: "*.csv"
```

### Useful for

- First-time tycoon users who want to see the whole stack work without
  signing up for anything
- CI tests of any change touching ingestion / transformation /
  observability — this template is the basis for the `offline_e2e`
  marker that runs on every PR

---

## `nyc-transit`

Live ingestion from NYC's open public-data APIs (Socrata-flavored REST).
No authentication. No rate limits worth worrying about for demo-scale
runs.

```bash
tycoon init --template nyc-transit --name nyc
tycoon data sources run nyc-dot --max-records 50
```

### What's in it

Three pre-registered sources:

- `nyc-dot` — NYC Department of Transportation traffic feeds (Socrata)
- `mta-gtfs` — MTA static GTFS feeds (subway / bus zip files)
- `mta-bus-speeds` — MTA bus segment speeds (Socrata)

### Generated `tycoon.yml`

```yaml
name: nyc-transit-demo
database:
  raw: data/nyc_open_data_raw.duckdb
  warehouse: data/nyc_open_data_local.duckdb

sources:
  nyc-dot:
    type: rest_api
    schema: raw_nyc_dot
    config:
      base_url: https://data.cityofnewyork.us/resource/
      datasets: [i4gi-tjb9, ycrg-ses3, 7ym2-wayt]
```

### Useful for

- Showing the full live-ingestion path
- Time-series tables that play well with Rill dashboards
- Conference talks (the public-data part is the legible bit)

---

## `github-analytics`

Pulls commits, issues, and PRs from a parameterized GitHub repo.

```bash
tycoon init --template github-analytics --name gh-demo \
  --param owner=anthropics --param repo=claude-code

export GITHUB_TOKEN=ghp_...
tycoon data sources run github
```

### Template parameters

The `github-analytics` template declares two required parameters via
its `template.yml`:

| Param | Description |
|---|---|
| `owner` | GitHub org or user (e.g. `anthropics`) |
| `repo` | Repository name (e.g. `claude-code`) |

If you omit them on the CLI, `tycoon init` prompts interactively.

### Auth

`GITHUB_TOKEN` must be set in the environment. `tycoon data sources run
github` will warn loudly if the token is missing or unexpanded in
`tycoon.yml`.

### Useful for

- Tracking metrics on a specific OSS project
- Demoing template parameterization (`--param name=value`)

---

## `weather-station`

NOAA weather data for a specific station, parameterized per location.

```bash
tycoon init --template weather-station --name kjfk \
  --param station_id=KJFK --param office=OKX \
  --param gridX=32 --param gridY=34

tycoon data sources run noaa
```

### Template parameters

| Param | Description |
|---|---|
| `station_id` | NOAA station code (e.g. `KJFK`, `KSFO`) |
| `office` | NOAA forecast office identifier (e.g. `OKX`) |
| `gridX` | NOAA grid X coordinate |
| `gridY` | NOAA grid Y coordinate |

Find the right values for any location at
[weather.gov](https://forecast.weather.gov/).

### Useful for

- Time-series demos that need a known stable data source
- Showing template parameterization with multi-param prompts
- The `xfail`-on-upstream-flake e2e marker — when NOAA's API has an
  outage, the test marks as expected-fail rather than red

---

## Adding your own template

Templates live under `src/tycoon/templates/<name>/` in the tycoon
source repo. Each contains:

```
templates/my-template/
├── tycoon.yml              # source template, with {{ var }} placeholders
├── template.yml            # optional — declares parameters
└── (any other files to copy verbatim into a new project)
```

`template.yml` (optional) declares parameters:

```yaml
parameters:
  - name: owner
    description: GitHub org or user
  - name: repo
    description: Repository name
```

`tycoon init --template my-template` substitutes `{{ owner }}` /
`{{ repo }}` placeholders in any `.yml`, `.yaml`, `.sql`, `.md`, or
`.txt` file at scaffold time. The `template.yml` itself isn't copied
into the target project (it's build-time metadata only).

For now, custom templates require a tycoon source checkout — there's no
`~/.tycoon/templates/` discovery path yet. Tracked as a follow-up.
