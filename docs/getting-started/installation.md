# Installation

Tycoon is published to PyPI as **`database-tycoon`** and installs the
`tycoon` CLI on your `$PATH`.

## Requirements

- **Python 3.12+**
- A Unix-like shell (macOS, Linux, WSL2). The CLI itself is
  cross-platform but several integrations assume POSIX paths.

## Install via pip

```bash
pip install database-tycoon
```

## Install via uv

```bash
uv tool install database-tycoon
# or, inside a project:
uv add database-tycoon
```

## Verify

```bash
tycoon --version       # tycoon 0.1.5
tycoon --help          # top-level command surface
```

## Optional extras

The base install covers the full data pipeline. Two **optional
dependency groups** exist, installed by appending the name in brackets:

```bash
pip install 'database-tycoon[motherduck]'       # MotherDuck raw loads
pip install 'database-tycoon[docs]'             # MkDocs docs site
```

| Extra | Pulls in | When to use |
|---|---|---|
| `[motherduck]` | `pyarrow` (through `dlt[motherduck]`, pinned to the same dlt version as the base install) | `database.raw` is an `md:` or `motherduck:` target |
| `[docs]` | `mkdocs` + Material theme | You're hacking on these docs |

dlt loads into MotherDuck through Parquet, so a MotherDuck raw database needs
`pyarrow`. Projects that keep their raw database in local DuckDB files don't,
which is why it is an extra and not part of the base install. Install it into
the environment tycoon runs in. For a project `.venv` built by `tycoon setup`,
that means building it with the extra:

```bash
tycoon setup --force --from 'database-tycoon[motherduck]'
```

`--force` rebuilds the `.venv`, so skip it on a project that has no `.venv` yet.

## External tools

Tycoon orchestrates several tools that aren't Python packages — install
them separately if you want their integrations:

- **DuckDB CLI** — useful for ad-hoc inspection of the warehouse:
  ```bash
  brew install duckdb         # macOS
  ```

- **Rill** — local-first BI dashboards:
  ```bash
  curl https://rill.sh | sh
  ```

- **MotherDuck** (optional, for cloud DuckDB):
  set `MOTHERDUCK_TOKEN` in your environment, or run `motherduck connect`
  to use OAuth.

None of these are required for `tycoon` itself to work — tycoon will
detect what you have installed and skip integrations you don't.

## What gets created

Installing `database-tycoon` adds the `tycoon` binary to your shell. It
does **not** create any directories, configuration files, or background
services until you run `tycoon init`.

## Uninstall

```bash
pip uninstall database-tycoon
```

To also remove projects you've initialized: just `rm -rf` the project
directory. Tycoon writes nothing outside it (the project's `.tycoon/`
folder holds all per-project state).
