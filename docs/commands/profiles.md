# `tycoon profiles`

Discover, inspect, and validate dbt profiles. Sits next to `tycoon
register` and `tycoon doctor` because profiles are a configuration
concern, not a pipeline concern.

```bash
tycoon profiles --help
```

Three subcommands: [`list`](#list), [`show`](#show), [`doctor`](#doctor).

For background on how tycoon resolves profiles in the first place, see
[the `tycoon.yml` reference](../reference/tycoon-yml.md#dbt-profiles)
and [the existing-profile recipe](../recipes/existing-dbt-profile.md).

## `list`

```bash
tycoon profiles list [--profiles-dir PATH]
```

Lists every profile in the active `profiles.yml`, with each profile's
targets, default target, adapter type(s), and a marker on the one tycoon
will use by default.

```text
Reading /Users/me/.dbt/profiles.yml (via ~/.dbt/profiles.yml)

 Profile        Targets         Default   Adapter(s)   Active
 analytics      dev, prod       dev       snowflake    ✓
 sandbox        dev             dev       duckdb

Tycoon will use: analytics (target: dev)
```

The active profile, the active target column, and the active row are
bolded in the terminal output (omitted in the docs render above).

### Options

| Flag | Default | Notes |
|---|---|---|
| `--profiles-dir` | unset | Override the discovered `profiles.yml` location. Same fallback chain as `dbt --profiles-dir`. |

## `show`

```bash
tycoon profiles show [NAME] [--profiles-dir PATH]
```

Pretty-prints one profile in YAML form, with secret-bearing fields
redacted. `NAME` defaults to the active profile (whatever `tycoon
profiles list` flagged with ✓).

```yaml
analytics:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: acct123
      user: me
      password: ***redacted***
      database: ANALYTICS_DB
      schema: PUBLIC
      warehouse: WH
```

Redacted fields: `password`, `private_key`, `private_key_passphrase`,
`client_secret`, `secret`, `api_key`, `token`, `access_token`,
`refresh_token`. Match is case-insensitive.

The original `profiles.yml` is never modified.

## `doctor`

```bash
tycoon profiles doctor [--profile NAME] [--profiles-dir PATH] [--target NAME]
```

Validates four things:

1. A `profiles.yml` exists somewhere in the resolution chain.
2. The named profile is present in that file.
3. The target is defined under the profile's `outputs:` block.
4. The adapter (`duckdb` / `snowflake` / `bigquery` / `redshift`) matches
   `stack.warehouse` in `tycoon.yml`.

Exits 0 on success, 1 on the first hard failure. Adapter mismatch is the
most common real-world catch:

```text
✓ Found profiles.yml: /Users/me/.dbt/profiles.yml (via ~/.dbt/profiles.yml)
✓ Active profile: analytics (target: dev)
✓ Adapter: snowflake
  → snowflake://acct123/ANALYTICS_DB
✗ Adapter mismatch: tycoon.yml stack.warehouse = duckdb but profile is snowflake.
  Either edit tycoon.yml or pick a different profile/target.
```

### How it differs from `tycoon doctor`

`tycoon doctor` runs the same checks but non-fatally as one row alongside
the rest of the environment audit. Use `tycoon profiles doctor` when you
want a hard exit code (e.g. in CI), or when you're iterating on a single
profile and don't need the full doctor run.
