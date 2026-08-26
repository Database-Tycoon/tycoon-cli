# `tycoon city`

Serve your project's catalog as an interactive 3D city in the browser. Schemas become districts, tables become buildings, and lineage becomes the road network — a way to *see* the shape of a warehouse that a table listing can't give you.

The renderer ships with tycoon — the pre-built web bundle is in the wheel, so there is nothing extra to install.

## Install

```bash
pip install database-tycoon
```

The renderer is imported inside `tycoon city` itself rather than at startup, so registering the command costs nothing: it pulls in duckdb and sqlglot only once you actually run it, and no other command pays for that.

## Synopsis

```
tycoon city [OPTIONS]

Options:
  --path TEXT       Project directory, DuckDB file, or md: catalog to render
                    (default: this project)
  --port INTEGER    Port to serve on  [default: 8000]
  --host TEXT       Interface to bind  [default: 127.0.0.1]
  --theme TEXT      Visual theme to render with  [default: default]
  --dist PATH       Built web bundle directory (defaults to the one shipped
                    with the add-on)
  --pricing PATH    TOML file declaring the compute rate the budget block is
                    billed at
  -h, --help        Show this message and exit
```

## Usage

With no arguments, `tycoon city` walks up from your working directory to the project root — the nearest directory holding a `tycoon.yml`, falling back to `pyproject.toml` — and renders that:

```bash
tycoon city
```

Then open <http://127.0.0.1:8000>. Ctrl-C stops the server.

### Render something else

`--path` takes a project directory, a DuckDB file, or a MotherDuck catalog:

```bash
tycoon city --path data/warehouse.duckdb
tycoon city --path md:my_catalog
tycoon city --path md:_share/sales/abc-123
```

Relative paths are resolved against your working directory before being handed to the renderer. MotherDuck `md:` URIs are passed through untouched.

### Change the port

```bash
tycoon city --port 8080
```

Useful when 8000 is already taken — or when you want the city up alongside [`tycoon start`](start.md)'s Rill (9009) and Quack (9494).

## Binding beyond localhost

The default is `127.0.0.1`, and that default is deliberate. **The city names your real schemas, tables, and columns.** Rendering it on a public interface publishes your warehouse's structure to anyone who can reach the port.

```bash
tycoon city --host 0.0.0.0    # only when you mean to publish
```

There's no auth in front of it. Pass `0.0.0.0` for a demo on a trusted network, not on anything routable.

## Costs

`--pricing` points at a TOML file declaring the compute rate the city's budget block bills against. Left unset, the renderer looks for a `pricing.toml` beside the catalog; failing that, a local DuckDB warehouse is treated as free.

```bash
tycoon city --pricing pricing.toml
```

## Themes

`--theme` selects the visual style. Only `default` ships today; the flag exists so future themes don't need a new interface.

## The renderer's own entry point

`tycoon city` is the integrated entry point — it finds your project for you — but the renderer also installs its own console script, `tycoon-city`, for rendering a catalog with no tycoon project around it (and for renderer development). It takes the same options and renders its `--help` the same way:

```bash
tycoon-city path/to/some.duckdb          # shorthand for `tycoon-city serve path/to/some.duckdb`
tycoon-city demo                         # a generated demo catalog, nothing to set up
tycoon-city demo --help
```

`tycoon-city demo` materialises a whole sample project — runs, tests, a failure cascade, freshness verdicts, a semantic model — into a temp directory and serves it exactly as an ordinary serve would. Nothing is written outside `$TMPDIR`; Ctrl-C removes it. `python -m tycoon_city.webserve [demo]` reaches the same server and the same demo for Docker and CI.

> A project directory named `demo` is still served as your directory, not the sample catalog — `tycoon city` always hands the renderer an absolute path, and for the standalone script `tycoon-city serve ./demo` is the unambiguous form.

## Related

- [`tycoon start`](start.md) — Rill dashboards and the Quack warehouse server
- [`tycoon data status`](data/status.md) — the same catalog as freshness and row counts
- [`tycoon data history`](data/history.md) — the run history the city's activity draws from
