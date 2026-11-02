# `tycoon fire` / `firehouse`

CLI views of the city's fire-and-response system. These commands read the
**same data** the 3D city renders (the observability metadata DB for run
history, falling back to dbt's own `target/run_results.json`) and present it
as text, so you can check "what's burning?" without opening the browser.

## The metaphor, and what it promises

The city keeps one honest rule for every emergency vehicle, and these
commands keep it too:

> A vehicle on the street means a problem is **awaiting response**; it never
> means a fix is running.

| In the data | In the city | In the CLI |
|---|---|---|
| A test with status `fail` or `error` | Its building is **on fire**; the firehouse dispatches one red **fire truck** over the roads | `tycoon fire` lists it |
| The dispatch overview | The **firehouse** on the civic strip, wired in by its access road | `tycoon firehouse` counts the fleet |

A fire is one failing test. A model that errored during a build is a build
failure, and `tycoon data history` is where to look for it; the city does not
set that building on fire, and neither does `fire`.

## `tycoon fire`

Failing tests from the latest run, one row per fire:

```
tycoon fire              # standing state (latest run)
tycoon fire --run 1a2b   # a specific run, by invocation-ID prefix
```

Reads the metadata DB when the project has one (`tycoon data transform run`
captures it), falling back to dbt's own `target/run_results.json`. Tests are
named the way dbt names them (`not_null_stg_widgets_id`), without the
project prefix or the hash suffix dbt appends to a test's unique id.

## `tycoon firehouse`

Dispatch stats: the number of fire trucks on duty, one per fire in the
latest run:

```
tycoon firehouse
```

There is no "unreachable buildings" stat: the planner guarantees every lot
fronts the one connected street network, and the renderer independently
re-checks by routing each vehicle over roads.

The contractor vans (one amber van per source past its freshness SLA) are
not listed yet. They arrive with the `tycoon repair` call sheet once tycoon
captures source freshness into the metadata DB.
