# Environment variables

Every environment variable tycoon reads or recommends. Set them in your shell, in a `.env` file, or via your CI's secret-injection.

## Used by tycoon

### `MOTHERDUCK_TOKEN`

MotherDuck access token. Read by `tycoon doctor`, surfaced as a warning by `tycoon ask doctor` when the warehouse is `md:*`, and passed through to dlt / dbt / DuckDB when they ATTACH `md:` URLs.

```bash
export MOTHERDUCK_TOKEN=eyJ…
```

Get one at [app.motherduck.com/token](https://app.motherduck.com/token).

OAuth is also recognized — run `motherduck connect` once to cache a session token under `~/.duckdb/`. `tycoon doctor` accepts either.

### `DLT_*`

Tycoon does not consume DLT's environment variables directly, but they're respected by dlt itself when `tycoon data sources run` invokes it. The most common:

- `DLT_HOME_DIR` — override `~/.dlt`
- `DLT_DATA_DIR` — override the dlt working dir per pipeline

If you set these, they should be in scope for both interactive shells and any cron / CI environment that runs `tycoon data sources run`.

### `DB_URI`

Set automatically by `tycoon ask` to point Nao's chat SQLite database at `.tycoon/nao/db.sqlite`. Don't override unless you know why — the per-project location ensures chat history survives `uv sync` / venv rebuilds (issue #8 fix from v0.1.2).

### `NAO_DEFAULT_PROJECT_PATH`

Set automatically by `tycoon ask` so Nao can resolve its working directory. Same advice — don't override.

### `FORCE_COLOR` / `NO_COLOR`

Standard environment variables for forcing or disabling Rich's color output. Tycoon respects both.

## Used by source configs (interpolated into `tycoon.yml`)

`tycoon.yml` supports `${VAR}` interpolation in any string. Common patterns:

### `GITHUB_TOKEN`

Used by the `github` source type:

```yaml
sources:
  github:
    type: rest_api
    config:
      access_token: ${GITHUB_TOKEN}
```

Set in your shell:

```bash
export GITHUB_TOKEN=ghp_…
```

`tycoon data sources run github` warns loudly if the token is unset:

```
WARN  Config key 'access_token' contains an unexpanded env var: ${GITHUB_TOKEN}
        Set it with: export GITHUB_TOKEN=<your-value>
```

### `STRIPE_API_KEY`, `SLACK_BOT_TOKEN`, etc.

Catalog source types each declare their own env-var conventions. The names follow each tool's own:

| Source | Recommended env var |
|---|---|
| `stripe` | `STRIPE_API_KEY` |
| `slack` | `SLACK_BOT_TOKEN` |
| `notion` | `NOTION_API_KEY` |
| `hubspot` | `HUBSPOT_ACCESS_TOKEN` |

`tycoon data sources add <type>` prompts for the env-var name interactively when you register the source.

### Custom REST APIs

For `rest_api` sources, set whatever name fits:

```yaml
sources:
  my_api:
    type: rest_api
    config:
      base_url: https://api.example.com/v1
      auth_header: "Bearer ${MY_API_TOKEN}"
```

## Used by `ask.llm`

The `ask` block uses `api_key_env` to declare which environment variable holds the LLM's API key. Tycoon translates that to Nao's interpolation syntax (`{{ env('VAR_NAME') }}`) when generating `nao_config.yaml`:

```yaml
ask:
  llm:
    provider: anthropic
    api_key_env: ANTHROPIC_API_KEY
    model: claude-opus-4-5
```

Then:

```bash
export ANTHROPIC_API_KEY=sk-…
```

For LM Studio, no API key is needed — set `provider: lm-studio` and tycoon emits a placeholder `api_key: lm-studio` (the LM Studio server ignores it).

## Used by CI

For GitHub Actions, store any of the above as repo secrets and inject:

```yaml
env:
  MOTHERDUCK_TOKEN: ${{ secrets.MOTHERDUCK_TOKEN }}
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

Tycoon's own CI workflows (`.github/workflows/ci.yml`, `.github/workflows/e2e.yml`) demonstrate the pattern.

## Used by tests

The `e2e` pytest marker requires network access. Tests live under
`tests/test_templates_e2e.py`; tests that need credentials
`pytest.skip()` when the relevant env var is absent.

```bash
uv run pytest -m e2e
```

## Not consulted by tycoon

For clarity, these aren't read or set by tycoon:

- `DBT_PROFILES_DIR` — dbt's own. tycoon passes `--profiles-dir` explicitly when needed (see [`tycoon register dbt`](../commands/register.md#tycoon-register-dbt)).
- `DUCKDB_*` — none.
- `DAGSTER_HOME` — Dagster's own. Tycoon's `start --only dagster` sets it to `.tycoon/dagster/` per-project but doesn't read it back.

## Related

- [Reference: tycoon.yml](tycoon-yml.md) — where `${VAR}` interpolation happens
- [`tycoon doctor`](../commands/doctor.md) — the source of truth for "did this env var get picked up?"
- [`tycoon ask doctor`](../commands/ask/index.md#ask-doctor-health-check) — same for the ask stack
