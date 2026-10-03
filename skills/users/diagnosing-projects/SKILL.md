---
name: diagnosing-projects
description: Use when a tycoon project misbehaves — commands fail, dbt can't find a profile, `data run-all` fails where `data transform run` works, schema_version warnings or "newer than this tycoon" errors, DuckDB "Unique file handle conflict" or file-lock errors, wrong Python version, "No tycoon.yml found" — or when wiring tycoon health checks into CI.
license: MIT
compatibility: Requires the tycoon CLI (pip install database-tycoon) inside a tycoon project (tycoon.yml present)
metadata:
  author: database-tycoon
  tier: users
---

# Diagnosing tycoon projects

Start with `tycoon doctor`: it reports the Python interpreter, `tycoon.yml`,
dbt and Rill projects, warehouse credentials (MotherDuck/Snowflake/BigQuery),
the dbt profile, staging-model coverage per source, and the observability DB.

## CI gating — the exit-code trap

**`tycoon doctor` always exits 0.** It is a report, not a gate — putting it
in CI never fails the job. The commands that exit 1 on failure are:

```bash
tycoon profiles doctor      # dbt profile valid + matches stack.warehouse
tycoon semantics doctor     # OSI YAML valid (only if you use semantics)
```

Use those for CI; use `tycoon doctor` for humans.

## `data run-all` fails where `data transform run` works

These two resolve the dbt profile differently:

- `data transform run` uses the full resolution chain: `--profiles-dir` →
  `tycoon.yml dbt_profiles_dir` → the dbt project dir → `$DBT_PROFILES_DIR` →
  `~/.dbt`. It also runs the `dbt` binary co-located with the tycoon venv.
- `data run-all` **hardcodes** `--profiles-dir <dbt_project_dir>` and uses
  whatever `dbt` is first on PATH. A profile that only exists in
  `~/.dbt/profiles.yml` works under `transform run` and breaks under
  `run-all`. Setting `DBT_PROFILES_DIR` does **not** fix `run-all`.

Fix: put (or symlink) `profiles.yml` inside the dbt project directory, or
replace `run-all` with the two explicit steps:

```bash
tycoon data sources run-all && tycoon data transform run
```

## Python and the venv

Supported interpreter range is **3.12 ≤ Python < 3.14** (dbt has no 3.14
wheels). A bad interpreter fails at `data transform run`, far from the cause.

- `tycoon setup` builds a project-local `.venv` via uv and installs tycoon
  into it (flags: `--python`, `--from`, `--force`).
- `tycoon doctor --fix` builds the same `.venv` but cannot swap the running
  interpreter — activate it afterwards (`source .venv/bin/activate`).

## `schema_version` ladder

- Missing or older than current → every command prints a warning; run
  `tycoon init --upgrade` (comment-preserving, idempotent).
- Newer than the installed tycoon → hard exit 1 on every command; upgrade
  the tycoon package, not the file.

## DuckDB file locks

- While `tycoon start` is running, Quack holds an exclusive lock on the
  warehouse. `tycoon data query` transparently routes warehouse queries
  through it, but external tools (duckdb CLI, BI tools) will hit the lock —
  `tycoon stop` first.
- "Unique file handle conflict" on dbt runs means the raw and warehouse
  paths point at the same file — they must differ in `tycoon.yml`'s
  `database:` block.
- Rill reads Parquet exports under `data/parquet/` rather than the DuckDB
  files precisely to avoid these locks; that is by design.

## "No tycoon.yml found" in the wrong place

Project-root discovery walks up looking for `tycoon.yml` **or**
`pyproject.toml`. Inside any Python repo, tycoon roots itself there and then
reports no `tycoon.yml`. `cd` into the actual tycoon project directory.
