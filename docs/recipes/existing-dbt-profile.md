# Use an existing dbt profile

If you already have a `profiles.yml` somewhere — `~/.dbt/`, a shared
config repo, or alongside an existing dbt project — tycoon will pick it
up without copying or rewriting anything.

## TL;DR

```bash
# 1. Tell tycoon where the profile lives (only if it's not co-located).
tycoon register dbt /path/to/your/dbt-project --profiles-dir ~/dbt-config

# 2. Verify what tycoon resolved.
tycoon profiles list
tycoon profiles doctor

# 3. Run as normal — tycoon shells out to dbt with the right --profile /
#    --profiles-dir / --target every time.
tycoon data transform build
```

## Resolution order

Same as dbt's own CLI, so nothing surprising:

1. `--profiles-dir` / `--profile` / `--target` on the tycoon command.
2. `dbt_profiles_dir` / `dbt_profile` / `dbt_target` in `tycoon.yml`.
3. `<dbt_project_dir>/profiles.yml` (dbt 1.5+ co-located).
4. `$DBT_PROFILES_DIR`.
5. `~/.dbt/profiles.yml`.

The first one that contains the requested profile wins. Tycoon never
copies, edits, or rewrites your `profiles.yml` — it only reads from it.

## Common scenarios

### "My profile lives under `~/.dbt`"

Nothing to do. `tycoon profiles list` will find it automatically.

```bash
tycoon profiles list
# Reading /Users/me/.dbt/profiles.yml (via ~/.dbt/profiles.yml)
# ...
```

### "My profile lives in a shared config repo"

Persist the path in `tycoon.yml`:

```yaml
dbt_project_dir: ./dbt
dbt_profiles_dir: ~/work/data-config
dbt_profile: analytics
dbt_target: dev
```

Or pass `--profiles-dir` per command:

```bash
tycoon data transform build --profiles-dir ~/work/data-config
```

### "I want to run a one-off against prod"

```bash
tycoon data transform build --target prod
```

Doesn't touch `tycoon.yml`. The next invocation falls back to the default
target.

### "Different profiles for dev and CI"

Two ways:

- Set `dbt_profile: ci` via env-aware `tycoon.yml` (use `${VAR}` interpolation).
- Or pass `--profile ci` from your CI pipeline.

## Validating before you run

```bash
tycoon profiles doctor
# ✓ Found profiles.yml: /Users/me/.dbt/profiles.yml (via ~/.dbt/profiles.yml)
# ✓ Active profile: analytics (target: dev)
# ✓ Adapter: snowflake
#   → snowflake://acct123/ANALYTICS_DB
# ✓ Adapter matches stack.warehouse (snowflake).
```

The doctor check catches the most common foot-gun: `tycoon.yml` declares
`stack.warehouse: duckdb` but the active profile actually points at
Snowflake. `tycoon doctor` runs the same check and reports it
non-fatally alongside the rest of your environment.

## What about secrets?

`tycoon profiles show` redacts known secret-bearing fields (`password`,
`private_key`, `token`, `client_secret`, `api_key`, etc.) before
printing. The original `profiles.yml` is never modified.

Use `${VAR}` env-var interpolation in your `profiles.yml` and source the
values from `.env` or the shell — tycoon doesn't add any new way to
configure secrets, it just reads dbt's existing one.
