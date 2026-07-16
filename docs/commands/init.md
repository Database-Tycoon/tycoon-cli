# `tycoon init`

Scaffold a new tycoon project from a built-in template.

## Synopsis

```
tycoon init [OPTIONS]

Options:
  -t, --template TEXT      Template name to scaffold from
  -n, --name TEXT          Project name (default: current directory name)
  --list-templates         List available templates and exit
  -p, --param TEXT         Template parameter in 'name=value' form (repeatable)
  -h, --help               Show this message and exit
```

## Quick start

```bash
mkdir my-project && cd my-project
tycoon init --template csv-import --name my-project
```

Or the full interactive wizard:

```bash
tycoon init
```

The wizard asks about each component (ingestion, warehouse, dbt, Rill) with sensible defaults. Pick `none` for any component you don't use.

## What gets created

In the current directory:

```
my-project/
├── tycoon.yml              # the config you'll touch most
├── data/                   # DuckDB files + parquet exports
├── dbt_project/            # dbt models (if scaffolded)
├── rill/                   # Rill dashboards (if scaffolded)
└── .gitignore
```

The exact tree depends on the template. See [Reference: Templates](../reference/templates.md) for what each template ships.

## Templates

`tycoon init --list-templates` shows them. The two featured built-in:

- `csv-import` — fully offline, smoke-test the full pipeline
- `nyc-transit` — live ingestion from NYC public APIs

See [Reference: Templates](../reference/templates.md) for the full list.

## Template parameters

Some templates declare parameters in their `template.yml`. Pass them with `--param`:

```bash
tycoon init --template <name> --param key=value --param other=value
```

If you omit a parameter the template requires, `init` prompts interactively.

Placeholders use `{{ name }}` / `{{ owner }}` syntax in any `.yml`, `.yaml`, `.sql`, `.md`, or `.txt` file the template ships. dbt's own `{{ ref(...) }}` Jinja passes through untouched.

## Picking a project name

The default is the current directory name. Override with `--name`:

```bash
tycoon init --template csv-import --name my-analytics
```

The name shows up in:

- `tycoon.yml`'s `name:` field
- dlt pipeline names (`my-analytics-files-pipeline`)

## After init

```bash
tycoon doctor                        # health check
tycoon data sources run files        # ingest first source
tycoon data transform run            # run dbt
tycoon data analyze files --rill     # generate dashboards
tycoon start --only rill             # serve dashboards
```

See [Your first project](../getting-started/first-project.md) for a 10-minute walkthrough.

## Re-running `init`

`tycoon init` refuses to overwrite an existing `tycoon.yml`. To reset a project:

```bash
rm -rf my-project && mkdir my-project && cd my-project
tycoon init --template csv-import
```

### Adding components you skipped

If you picked "Skip" on the dbt or Rill prompts during the wizard, you can add them later non-destructively without re-running `init`:

```bash
tycoon register dbt --create     # bootstrap a sibling dbt project
tycoon register rill ./rill      # or register an existing one
```

See [`tycoon register`](register.md#-create-bootstrap-a-new-dbt-project) for the full `--create` behavior.

## Related

- [Reference: tycoon.yml](../reference/tycoon-yml.md) — full schema of what `init` writes
- [`tycoon register`](register.md) — attach existing dbt / Rill / warehouse to a project
