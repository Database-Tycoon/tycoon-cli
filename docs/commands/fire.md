# `tycoon fire` / `firehouse` / `repair`

CLI views of the city's fire-and-response system. These commands read the
**same data** the 3D city renders — dbt run artifacts for test results, the
observability metadata DB for run history and source freshness — and present
it as text, so you can check "what's burning?" without opening the browser.

## The metaphor, and what it promises

The city keeps one honest rule for every emergency vehicle, and these
commands keep it too:

> A vehicle on the street means a problem is **awaiting response** — it never
> means a fix is running.

| In the data | In the city | In the CLI |
|---|---|---|
| A test with `status: fail` | Its building is **on fire**; the firehouse dispatches one red **fire truck** over the roads | `tycoon fire` lists it |
| A source past its freshness SLA (`warn` / `error`) | A **worn building**; one amber **contractor van** dispatched; **fog** over every district it feeds | `tycoon repair` lists it |
| The dispatch overview | The **firehouse** on the civic strip, wired in by its access road | `tycoon firehouse` counts the fleets |

Trucks and vans are restatements of measured, unresolved facts — the same
`test_status` / `freshness_status` fields in `city.json`, selected by the same
rules the renderer's fleets use. Nothing here claims a fix is in progress.

## `tycoon fire`

Failing tests from the latest run, one row per fire:

```
tycoon fire              # standing state (latest run)
tycoon fire --run 1a2b   # a specific run, by invocation-ID prefix
```

Reads the metadata DB when the project has one (`tycoon data transform run`
captures it), falling back to dbt's own `target/run_results.json`.

## `tycoon repair`

The contractor call sheet — every source past its SLA, with status and last
load time:

```
tycoon repair
```

## `tycoon firehouse`

Dispatch stats: the station's map location (when an exported `city.json`
exists — the location is a map fact) and the fleet counts (facts about the
data, available with or without a map):

```
tycoon firehouse
```

There is no "unreachable buildings" stat: the planner guarantees every lot
fronts the one connected street network, and the renderer independently
re-checks by routing each vehicle over roads.
