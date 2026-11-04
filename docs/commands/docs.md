# `tycoon docs`

Build and serve these docs locally. Two subcommands wrap MkDocs — same tooling that builds the public docs.

| Command | What it does |
|---|---|
| `tycoon docs serve` | Serve with hot reload on `:8000`, contributor notes included |
| `tycoon docs build` | One-shot build into `./site/`, matching what gets published |

!!! info "Optional extra"
    `tycoon docs` requires the `[docs]` extra:
    `pip install 'database-tycoon[docs]'`

## `tycoon docs serve`

Serves the docs on `http://127.0.0.1:8000` with auto-reload. Save any file under `docs/` and the browser refreshes.

### Synopsis

```
tycoon docs serve [OPTIONS]

Options:
  -p, --port INTEGER    Port to bind (default: 8000)
  --host TEXT           Host interface (default: 127.0.0.1 — local-only)
  --no-open             Don't try to open a browser
  -h, --help            Show this message and exit
```

### Examples

```bash
tycoon docs serve                  # http://127.0.0.1:8000
tycoon docs serve --port 9000
tycoon docs serve --host 0.0.0.0   # share on the local network (use with care)
```

Press Ctrl-C to stop. Tycoon catches the interrupt and exits cleanly.

## `tycoon docs build`

One-shot build. Writes the static site into `./site/`.

This is the published set of pages, which is smaller than what `serve` shows.
`mkdocs.yml` withholds the contributor notes under `docs/city/` and
`docs/proposals/` from the build, so `serve` renders them behind a DRAFT banner
and `build` leaves them out. Use `serve` to read them.

### Synopsis

```
tycoon docs build [OPTIONS]

Options:
  --strict      Fail on warnings (broken links, missing pages, etc.)
  -h, --help    Show this message and exit
```

### Examples

```bash
tycoon docs build              # builds into ./site/
tycoon docs build --strict     # fails fast on broken links — for CI
```

The build is fast (~1s on a warm cache), so it is worth running before you push. It is not a complete check on its own: a nav entry pointing at a withheld page, and a page in none of the nav or withholding lists, are both reported by MkDocs at INFO. `scripts/check_docs_publishable.py` covers the first and `validation.nav.omitted_files` the second, and CI runs both. CI workflows that publish docs should use `--strict` so a typo'd link blocks the deploy.

## Where these commands run

Both commands walk up from your current directory looking for `mkdocs.yml`. They work from any subdirectory of a tycoon source checkout:

```bash
cd ~/projects/tycoon-cli/docs
tycoon docs serve              # works
```

They do **not** run from a user's tycoon project. There's no `mkdocs.yml` there — the docs site is part of the tycoon source repo.

## Authoring tip

The site uses MkDocs Material. Common conventions:

- **Code blocks** — fenced with triple backticks, optional language hint
- **Admonitions** — `!!! info "Title"` / `!!! warning` / `!!! tip`
- **Tabs** — `=== "Tab name"` / `=== "Other tab"` (alternates)
- **Internal links** — relative paths (`[text](../reference/tycoon-yml.md)`)

`tycoon docs build --strict` catches every broken link — useful when refactoring.

## Related

- [MkDocs Material docs](https://squidfunk.github.io/mkdocs-material/) — full reference for the theme and extensions
- The `docs/` directory in the [tycoon-cli repo](https://github.com/Database-Tycoon/tycoon-cli/tree/main/docs) — source for these pages
