# `tycoon setup`

Build a project-local `.venv` on a **supported** Python interpreter, using [uv](https://docs.astral.sh/uv/). Added in v0.1.9 (#57).

## Why

tycoon runs dbt out of the *same* interpreter it lives in — it imports `dlt`/`duckdb` in-process and resolves dbt at `Path(sys.executable).parent / "dbt"`. So the single most common first-mile failure is a mismatched Python: dbt-core / dbt-duckdb ship no wheels for 3.14 yet, and an out-of-range interpreter fails far from its cause (at `tycoon data transform run`).

`tycoon setup` removes the trap by owning the environment. It creates one `.venv` beside `tycoon.yml` on a supported interpreter, pins it with `.python-version`, and installs tycoon + its dbt/dlt/duckdb stack into it. uv downloads a [python-build-standalone](https://docs.astral.sh/uv/concepts/python-versions/) CPython if your machine only has an unsupported one — **zero manual interpreter installs**.

## Synopsis

```
tycoon setup [OPTIONS]

Options:
  --python TEXT    Python version (major.minor) for the .venv. Must be in
                   tycoon's supported range (>=3.12,<3.14). Default: 3.13.
  --from TEXT      Package spec to install. Default: database-tycoon.
                   Pass `-e .` (or a path) for a dev checkout.
  --no-install     Create and pin the .venv but skip installing tycoon.
  --force          Recreate the .venv if one already exists.
  --no-prompt      Skip confirmation prompts (CI / scripted bootstrap).
  -h, --help       Show this message and exit.
```

## Quick start

```bash
cd my-project          # a dir with tycoon.yml (run `tycoon init` first)
tycoon setup           # builds .venv on Python 3.13 via uv
source .venv/bin/activate
tycoon doctor          # confirms the interpreter is now in range
```

The new environment is **separate** from the interpreter running `tycoon` right now — `setup` can't swap Python under its own feet, so activate the `.venv` before running further commands.

## Prerequisites

`setup` needs **uv** on your `PATH`. If it's missing, `setup` points you at the standalone installer rather than running it for you (a network installer is a deliberate, user-triggered step):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Recipes

```bash
# Pin a specific supported interpreter
tycoon setup --python 3.12

# Dev checkout — install the working tree editable instead of the published wheel
tycoon setup --from '-e .'

# Recreate a broken/stale environment
tycoon setup --force

# Scaffold the env in CI without installing tycoon into it
tycoon setup --no-install --no-prompt
```

## Relationship to `tycoon doctor`

[`tycoon doctor`](doctor.md)'s first check verifies the running interpreter is in range. When it's out of range, `tycoon doctor --fix` runs this same `.venv`-build flow for you. `setup` is the explicit front door; `doctor --fix` is the in-context repair.

## Related

- [`tycoon doctor`](doctor.md) — the interpreter check + `--fix`
- [`tycoon init`](init.md) — scaffold the project that `setup` builds an env for
