# `tycoon register`

Attach existing dbt, Rill, or warehouse components to a tycoon project. Use these when you already have a dbt project / Rill dashboards / cloud warehouse and want tycoon to run them without scaffolding from scratch.

Three subcommands:

| Command | What it does |
|---|---|
| [`tycoon register dbt`](#tycoon-register-dbt) | Attach an existing dbt project (with profile flags) |
| [`tycoon register rill`](#tycoon-register-rill) | Attach an existing Rill project |
| [`tycoon register warehouse`](#tycoon-register-warehouse) | Switch warehouse type (DuckDB / MotherDuck) |

All three commands edit `tycoon.yml` in place and update `stack.<component>_managed` to `false` so tycoon stays out of the way of the existing project.

---

## `tycoon register dbt`

Attach an existing dbt project. Local path or GitHub URL.

### Synopsis

```
tycoon register dbt [OPTIONS] [SOURCE]

Arguments:
  [SOURCE]  Local path or GitHub URL of an existing dbt project.
            Required unless --create is set (in which case it overrides
            the default sibling path).

Options:
  --create               Bootstrap a new dbt project at ../<project>-dbt
                         (or [SOURCE] if given), wired to the active tycoon
                         warehouse, then register it
  --profiles-dir PATH    Directory containing profiles.yml (default:
                         <SOURCE>/profiles.yml, then ~/.dbt/profiles.yml)
  --profile NAME         Profile name within profiles.yml (default:
                         dbt_project.yml's `profile:` field)
  --target NAME          Target within the profile (default: profile's
                         `target:` field, then 'dev')
  --no-attach-metadata   Skip wiring `.tycoon/metadata.duckdb` into the
                         registered profile as `tycoon_meta`
  -h, --help             Show this message and exit
```

### Examples

```bash
# Register a sibling dbt project
tycoon register dbt ../my-existing-dbt-project

# Register from GitHub (clones into a sibling dir)
tycoon register dbt https://github.com/me/my-dbt-project

# Bootstrap a new dbt project (recovery path if you skipped dbt during
# `tycoon init` — sibling repo at ../<project>-dbt, profile points at
# whatever DuckDB/MotherDuck the tycoon project already uses)
tycoon register dbt --create

# Same, with an explicit location
tycoon register dbt --create ./dbt_project

# With non-default profile resolution
tycoon register dbt ../my-dbt \
  --profiles-dir ~/.config/dbt \
  --profile production_profile \
  --target prod
```

### `--create`: bootstrap a new dbt project

If you picked **Skip** on the dbt prompt during `tycoon init`, `--create`
is the recovery path. It writes a fresh `dbt_project.yml` + `profiles.yml`
(plus the standard `models/`, `analyses/`, etc. layout) at the target
location, then runs the same registration flow as if you'd handed it an
existing project.

The generated profile points at the same warehouse paths recorded in
`tycoon.yml`'s `database` block, so `tycoon data transform run` works
immediately without further configuration.

**Limitations:**

- DuckDB and MotherDuck warehouses only. For Snowflake/BigQuery, hand-author
  `dbt_project.yml` + `profiles.yml` and use plain `tycoon register dbt <path>` —
  the warehouse-alignment step picks up the cloud adapter from there.
- Refuses to overwrite an existing `dbt_project.yml`. If the target directory
  already has one, register it directly (drop the `--create` flag).
- Marks `stack.transformation_managed: true` (tycoon owns the project,
  same as the init wizard's "Create new" option). Plain
  `tycoon register dbt <path>` keeps `transformation_managed: false`.

### Profile resolution

The three profile flags (`--profiles-dir`, `--profile`, `--target`) mirror dbt's own CLI options. They control:

1. **Which `profiles.yml` to read.** The flag wins, then `<SOURCE>/profiles.yml` if co-located, then `~/.dbt/profiles.yml`.
2. **Which profile within that file.** The flag wins, then `dbt_project.yml`'s `profile:` field.
3. **Which target within the profile.** The flag wins, then the profile's `target:` field, then `"dev"`.

Anything you pass on the CLI is **persisted in `tycoon.yml`** under `dbt_profiles_dir` / `dbt_profile` / `dbt_target` so subsequent `tycoon data transform` runs reuse it automatically. Re-running `register dbt` without a flag clears the persisted value.

### Warehouse alignment

After resolving the dbt target, `register dbt` reads the adapter type and offers to align tycoon's `stack.warehouse` accordingly:

- **dbt-duckdb** → tycoon adopts the same `path:` (local DuckDB or `md:<catalog>` for MotherDuck)
- **dbt-snowflake / dbt-bigquery / dbt-redshift** → tycoon updates `stack.warehouse` to match the adapter type. `database.warehouse` (only meaningful for DuckDB / MotherDuck) is left alone for cloud adapters.

Snowflake registration also surfaces an account-mismatch warning if `tycoon.yml`'s `warehouse_connection.account` was previously recorded as a different value.

### `register dbt` writes

`tycoon.yml` gains:

```yaml
dbt_project_dir: ../my-dbt
dbt_profiles_dir: /path/to/profiles      # only if --profiles-dir was passed
dbt_profile: my_profile                   # only if --profile was passed
dbt_target: prod                          # only if --target was passed
stack:
  transformation: dbt
  transformation_managed: false
```

---

## `tycoon register rill`

Attach an existing Rill project. Local path or GitHub URL.

### Synopsis

```
tycoon register rill [OPTIONS] SOURCE

Arguments:
  SOURCE  Local path or GitHub URL of the Rill project to register
```

### Example

```bash
tycoon register rill ../my-dashboards
```

`register rill` validates that the source contains `rill.yaml` and updates `tycoon.yml`:

```yaml
rill_dir: ../my-dashboards
stack:
  bi: rill
  bi_managed: false
```

---

## `tycoon register warehouse`

Switch the warehouse type — local DuckDB ↔ MotherDuck — without re-running `init`.

### Synopsis

```
tycoon register warehouse [OPTIONS]

Options:
  --type TEXT       Warehouse type — 'duckdb' (or 'local') / 'motherduck' (or 'cloud')
  --path TEXT       For --type duckdb: local file path (default: data/warehouse.duckdb)
  --catalog TEXT    For --type motherduck: catalog name (becomes md:<catalog>)
  --no-prompt       Fail rather than prompt — for CI
  --force           Overwrite an existing warehouse without prompting
```

### Examples

```bash
# Interactive (prompts for everything)
tycoon register warehouse

# Non-interactive — fully scriptable
tycoon register warehouse --type motherduck --catalog my_catalog --no-prompt
tycoon register warehouse --type duckdb --path ./data/warehouse.duckdb --no-prompt

# Force-overwrite an existing warehouse setting
tycoon register warehouse --type motherduck --catalog new_catalog --force --no-prompt
```

### Behavior matrix

| `--type` set | Type-specific value set | `--no-prompt` | Result |
|---|---|---|---|
| ✓ | ✓ | any | No prompts (CI mode) |
| ✓ | — | absent | Prompts for the value |
| ✓ | — | `--no-prompt` | Fails fast |
| — | — | absent | Prompts for everything (default) |
| — | — | `--no-prompt` | Fails fast — `--type` is required |

### MotherDuck auth

When you set warehouse to `md:<catalog>`, `register warehouse` warns if `MOTHERDUCK_TOKEN` is not in the environment. It doesn't fail — OAuth is also valid (run `motherduck connect` once) and `tycoon doctor` will recognize either path.

---

## Related

- [Reference: tycoon.yml](../reference/tycoon-yml.md#stack) — `stack` block schema
- [Concepts → The CLI is a thin facade over real tools](../getting-started/concepts.md#4-the-cli-is-a-thin-facade-over-real-tools)
- [Issue #18](https://github.com/Database-Tycoon/tycoon-cli/issues/18) — register dbt profile flags (closed in v0.1.4)
- [Issue #19](https://github.com/Database-Tycoon/tycoon-cli/issues/19) — register warehouse flags (closed in v0.1.4)
