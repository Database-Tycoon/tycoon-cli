# `tycoon fire` / `firehouse`

Failing tests, as text. These commands read the same data the 3D city
renders (the observability metadata DB for run history, falling back to
dbt's own `target/run_results.json`), so you can check what is failing
without opening the browser.

## What counts as a fire

In the city, a failing test sets its building on fire and the firehouse
sends one fire truck to it. These commands keep the same rule:

| In the data | In the city | In the CLI |
|---|---|---|
| A test with status `fail` or `error` | Its building is **on fire**; the firehouse sends one **fire truck** over the roads | `tycoon fire` lists it |
| All current fires | The **firehouse** on the civic strip | `tycoon firehouse` counts the trucks |

A truck on the street means a problem is **awaiting response**. It never
means a fix is running.

A model that failed to build is not a fire, and the city doesn't set its
building on fire. The commands don't stay quiet about it, though: when
models failed, both print how many and point at `tycoon data history`,
where the failed run and its error are listed. They never report a broken
build as healthy.

## `tycoon fire`

One row per failing test:

```
tycoon fire                 # failing tests now
tycoon fire --run 480db459  # failing tests in one run
```

Without `--run`, each test counts by its newest result across all captured
runs, the way the city folds run history. A later `dbt run` that runs no
tests leaves the last test results in place, so a failure stays listed
until a run that includes the test passes it. A test or model that is
renamed or removed from the project drops out of the list, as it has no
building in the city.

`--run` shows a single run. It takes the run id `tycoon data history`
prints for a dbt run, or a prefix of dbt's own invocation id, and the
output names the run it shows (`Run: dbt test (6110ef1d)`). A prefix that
matches more than one run is an error that lists the matches.

The command reads the metadata DB when the project has one (`tycoon data
transform run` captures it) and falls back to dbt's own
`target/run_results.json`, which holds only the most recent run. Tests are
named the way dbt names them (`not_null_stg_widgets_id`), without the
project prefix or the hash suffix dbt appends to a test's unique id.

## `tycoon firehouse`

The number of fire trucks on duty: one per failing test, counted the same
way as `tycoon fire`.

```
tycoon firehouse
```

There is no "unreachable buildings" stat: the planner guarantees every lot
fronts the one connected street network, and the renderer independently
re-checks by routing each vehicle over roads.

The contractor vans (one amber van per source past its freshness SLA) are
not listed yet.
