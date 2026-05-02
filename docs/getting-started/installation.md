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
tycoon --version       # tycoon 0.1.4
tycoon --help          # top-level command surface
```

## Optional extras

Tycoon ships with several **optional dependency groups** that you opt
into based on what parts of the stack you use. Each extra is installed
by appending its name in brackets:

```bash
pip install 'database-tycoon[ask]'              # AI agent
pip install 'database-tycoon[dagster]'          # orchestration
pip install 'database-tycoon[server]'           # local web UI for tycoon start
pip install 'database-tycoon[ask,dagster]'      # combine
```

| Extra | Pulls in | When to use |
|---|---|---|
| `[ask]` | `nao-core` + `ibis-framework[duckdb]` | You want `tycoon ask chat` and the AGENTS.md context surface |
| `[dagster]` | `dagster` family | You want `tycoon start --only dagster` to run materializations on a schedule |
| `[server]` | `fastapi`, `uvicorn`, `websockets` | You want `tycoon start` to expose a local web dashboard |
| `[docs]` | `mkdocs` + Material theme | You're hacking on these docs |

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

- **LM Studio** (optional, for the local-LLM `tycoon ask` story):
  download from [lmstudio.ai](https://lmstudio.ai/) and start the
  built-in OpenAI-compat server on `:1234`.

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
