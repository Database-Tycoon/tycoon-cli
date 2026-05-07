# Recipe: Adopt tycoon for an existing dbt project

You already have a dbt project (and maybe a Rill / Metabase setup, and a cloud warehouse). You want tycoon to orchestrate without rewriting any of it.

## What tycoon adds

For an existing dbt project:

- **Run history.** Every `tycoon data transform run` lands in `.tycoon/metadata.duckdb` — invocation timing, per-model status, manifest fingerprint, schema-change diffs across runs.
- **Auto-generated dashboards** for the run history (`_tycoon_dbt_usage` Rill dashboard) — drift detection without writing the dashboard yourself.
- **Cloud → local snapshots.** `tycoon data sync` from MotherDuck / etc. for an offline dev loop.
- **AI context layer.** `tycoon register llm lm-studio` gives any coding agent (or Nao's chat UI) a self-updating view of your warehouse + dbt models.
- **Consistent invocation across machines.** `tycoon run dbt run` always uses the venv-pinned dbt, never a system one.

## What tycoon doesn't replace

- Your dbt models — they stay where they are.
- Your existing CI — `tycoon data transform build` is invokable from CI, but you can keep using `dbt build` directly if you prefer.
- Your warehouse — tycoon points at whatever you've got (DuckDB, MotherDuck, Snowflake, BigQuery, Redshift).

## Setup

### 1. Initialize a tycoon project (without scaffolding dbt)

```bash
mkdir tycoon-orchestration && cd tycoon-orchestration
tycoon init                    # interactive wizard
```

In the wizard, when asked about transformation:

- Choose dbt
- Choose "I have an existing dbt project"

This sets `stack.transformation_managed: false` so tycoon doesn't try to scaffold over your project.

Or scriptable:

```bash
tycoon init --name tycoon-orchestration
tycoon register dbt ../my-existing-dbt-project
```

### 2. Register your dbt project with profile flags

If your dbt project has standard `profiles.yml` location and default target:

```bash
tycoon register dbt ../my-existing-dbt-project
```

If you use non-default profile resolution (CI profile, custom profiles dir, multiple profiles in one file):

```bash
tycoon register dbt ../my-existing-dbt-project \
  --profiles-dir ~/work/dbt-profiles \
  --profile production_profile \
  --target dev
```

Tycoon persists these into `tycoon.yml`:

```yaml
dbt_project_dir: ../my-existing-dbt-project
dbt_profiles_dir: /Users/me/work/dbt-profiles
dbt_profile: production_profile
dbt_target: dev
stack:
  transformation: dbt
  transformation_managed: false
```

After this, `tycoon data transform run` reuses these settings every time. CLI flags still override.

### 3. Register your warehouse

For DuckDB / MotherDuck:

```bash
tycoon register warehouse                                      # interactive
tycoon register warehouse --type motherduck --catalog prod --no-prompt
```

For Snowflake / BigQuery / Redshift, the warehouse type is auto-detected from your dbt profile during `register dbt` — `register warehouse` is only useful for switching DuckDB ↔ MotherDuck.

### 4. Register Rill (optional)

```bash
tycoon register rill ../my-existing-rill-dashboards
```

### 5. Health check

```bash
tycoon doctor
```

Should print a clean status panel for each registered component. Anything red, fix before proceeding.

## Day-to-day usage

### Run dbt with capture

Replace `dbt run` / `dbt build` in your usual workflow:

```bash
# Before:
cd ../my-dbt-project && dbt build

# After:
tycoon data transform build      # from the tycoon project; observability captured
```

`tycoon data transform` resolves `--target` / `--profiles-dir` / `--profile` from `tycoon.yml` automatically. Pass CLI flags to override.

### Read the run history

```bash
tycoon data history --tool dbt              # last 10 dbt runs
tycoon data history show <invocation_id>    # drill into one
```

The drilldown shows per-model status + duration, plus a "Schema changes vs. previous run" table when columns shift or SQL hashes change.

### Add observability dashboards

```bash
tycoon data analyze _tycoon --rill          # generates _tycoon_dbt_usage dashboard
tycoon start --only rill
```

Browse to `http://localhost:9009` and the `_tycoon_dbt_usage` dashboard shows trend lines on success rate, average duration, models built per run.

### Pull a local snapshot

If your warehouse is on MotherDuck and you want fast dev queries:

```yaml
# tycoon.yml
sync:
  to: data/local_snapshot.duckdb
  sources:
    - from: md:my_catalog
      schemas: [mart]
```

Then:

```bash
tycoon data sync                  # uses the block above
```

Point your dbt dev target at `data/local_snapshot.duckdb` for instant queries; switch to the cloud target when you actually want to write to prod.

### Add the AI agent

```bash
pip install 'database-tycoon[ask]'
tycoon register llm lm-studio
tycoon ask sync
tycoon ask chat
```

Nao reads from your warehouse and dbt project — your existing models become the agent's source of truth. See [Recipe: LM Studio local LLM](lm-studio-local-llm.md) for the full LM Studio walkthrough.

## CI integration

A typical CI workflow (GitHub Actions example):

```yaml
- run: pip install 'database-tycoon[dagster]'
- run: tycoon doctor                    # fail fast on env issues
- run: tycoon data run-all              # ingest + dbt build
- run: tycoon data transform test       # explicit test step (run-all does this too)
```

For dbt-only setups (no tycoon ingestion), skip `run-all` and call `tycoon data transform build` directly.

## What `register` doesn't move

Your dbt project files stay where they are. `tycoon register dbt` only writes `dbt_project_dir` (and the optional profile keys) to `tycoon.yml` — it doesn't copy or modify your dbt files. Same for Rill.

If you want a single-repo setup (dbt + tycoon together), move the dbt project into the tycoon project directory and re-register:

```bash
mv ../my-existing-dbt-project ./dbt_project
tycoon register dbt ./dbt_project
```

## Migrating away from tycoon

If you decide tycoon isn't for you: just stop using `tycoon` commands. Your dbt project, warehouse, and Rill setup are unchanged — tycoon never owned them.

To clean up tycoon's state:

```bash
rm -rf .tycoon/                         # removes metadata DB + nao state
rm tycoon.yml                            # removes tycoon's config
```

Your dbt project, dbt CI, and Rill dashboards keep working.

## Related

- [`tycoon register dbt`](../commands/register.md#tycoon-register-dbt)
- [`tycoon register warehouse`](../commands/register.md#tycoon-register-warehouse)
- [`tycoon data transform`](../commands/data/transform.md)
- [`tycoon data history`](../commands/data/history.md)
