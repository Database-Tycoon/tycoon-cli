# `tycoon run`

Pass through any argument list to one of the underlying CLI tools. The escape hatch when you want the tool's full surface area without remembering which `pip install` shipped its binary under what name.

## Synopsis

```
tycoon run TOOL [TOOL_ARGS...]

Tools:
  dlt       The dlt CLI
  dbt       The dbt CLI (dbt-core + dbt-duckdb)
  rill      The Rill CLI
  duckdb    The DuckDB CLI (when installed externally)
```

`tycoon run` resolves the tool's binary in this order:

1. Venv-colocated (`<sys.executable_dir>/<tool>`) — preferred, matches the version pinned by tycoon's deps
2. `$PATH` lookup via `shutil.which`

It then `exec`s the tool with the rest of the argv passed through. tycoon doesn't interpret any flags after the tool name.

## Examples

### dbt

```bash
tycoon run dbt --version
tycoon run dbt run --select stg_widgets
tycoon run dbt show --select stg_widgets --limit 10
tycoon run dbt parse                  # check yml validity
tycoon run dbt deps                   # install dbt packages
```

For the common build/test/run/docs commands, prefer `tycoon data transform <cmd>` — same dbt invocation, plus tycoon adds observability capture and Rill refresh. Use `tycoon run dbt` for everything else.

### dlt

```bash
tycoon run dlt --version
tycoon run dlt init github duckdb     # scaffold a new source
tycoon run dlt deploy --help          # dlt's deploy command
```

### Rill

```bash
tycoon run rill --version
tycoon run rill validate              # check Rill project health
tycoon run rill query "SELECT 1"      # query a metrics view
```

### DuckDB

```bash
tycoon run duckdb data/warehouse.duckdb -c "SHOW ALL TABLES"
tycoon run duckdb data/warehouse.duckdb     # interactive shell
```

## Why use `tycoon run` instead of the tool directly?

Three reasons:

1. **Version coherence.** `tycoon run dbt` always invokes the dbt that ships in tycoon's venv. If you have a system-wide `dbt` from a different version, it won't get picked up here.
2. **Cwd correctness.** `tycoon run dbt` runs from `config.dbt_project_dir`, not from your shell's cwd. Means `tycoon run dbt run` works the same whether you're at the project root or in a subdirectory.
3. **Forward propagation.** Future tycoon versions may add hooks (auth env injection, profile resolution, etc.) inside `tycoon run`. Code that habitually uses `tycoon run dbt` will pick those up automatically.

For one-shot ad-hoc invocations where none of those matter, calling the tool directly is fine.

## Observability is NOT captured for `tycoon run`

Deliberate. `tycoon run dbt run` does **not** write to `.tycoon/metadata.duckdb`. That capture is reserved for `tycoon data transform run/test/build`. Otherwise `tycoon run dbt show` / `dbt compile` / `dbt parse` would pollute the run history.

If you want a `tycoon run` invocation captured, run the wrapped tycoon command instead. There's no flag to force capture.

## Related

- [`tycoon data transform`](data/transform.md) — wraps `dbt run/test/build/docs` with capture
- [Concepts → The CLI is a thin facade over real tools](../getting-started/concepts.md#4-the-cli-is-a-thin-facade-over-real-tools)
