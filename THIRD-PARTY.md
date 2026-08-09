# Third-party software

Database Tycoon is MIT licensed (see [`LICENSE`](LICENSE)). It redistributes
the runtime dependencies listed below — the web bundle the wheel ships at
`src/tycoon_city/web_dist/` (built from the renderer's TypeScript sources) is
compiled *with three.js and zod inside it*, and the wheel carries the Python
packages alongside — so their copyright notices travel here, which is what each
of their licences asks for.

**Why `THIRD-PARTY.md` and not `NOTICE`.** `NOTICE` is a term of art: Apache-2.0
§4(d) defines it as a file whose contents every downstream redistributor must
reproduce. Nothing here is Apache-2.0 and this project is MIT, so no such
obligation exists to propagate, and naming the file `NOTICE` would imply one
that does not. This is an attribution inventory, plainly named.

## Verdict

**Every runtime dependency is MIT.** No copyleft, no source-availability
obligation, no field-of-use restriction, nothing that constrains a public MIT
release or a commercial deployment. There is no licence blocker for launch.

The licence text was read from the installed artifact in each case, not
inferred from a package index — the table's "verified from" column says exactly
which file, and the versions are the ones this repo currently pins.

## Runtime dependencies

### Web (bundled into `src/tycoon_city/web_dist/`, the copy the wheel ships and `tycoon city` serves)

| Package | Version | Licence | Copyright | Verified from |
|---|---|---|---|---|
| [three.js](https://threejs.org) | 0.185.1 | MIT | © 2010-2026 three.js authors | `web/node_modules/three/LICENSE` |
| [zod](https://zod.dev) | 3.25.76 | MIT | © 2025 Colin McDonnell | `web/node_modules/zod/LICENSE` |

Both are leaf dependencies: `npm ls --omit=dev --all` shows no transitive
runtime package under either, so this table is the whole web-side inventory.
The only three.js addon this app imports is `CSS2DRenderer`, which ships inside
the `three` package and under the same licence.

### Python (declared in `pyproject.toml`, installed into the wheel's environment)

| Package | Version | Licence | Copyright | Verified from |
|---|---|---|---|---|
| [duckdb](https://duckdb.org) | 1.5.5 | MIT | © 2018-2026 Stichting DuckDB Foundation | `duckdb-1.5.5.dist-info/licenses/LICENSE` |
| [sqlglot](https://github.com/tobymao/sqlglot) | 30.15.0 | MIT | © 2026 Toby Mao | `sqlglot-30.15.0.dist-info/licenses/LICENSE` |
| [PyYAML](https://pyyaml.org) | 6.0.3 | MIT | © 2017-2021 Ingy döt Net; © 2006-2016 Kirill Simonov | `pyyaml-6.0.3.dist-info/licenses/LICENSE` |

The `duckdb` wheel vendors the DuckDB C++ engine itself rather than linking a
system copy; the engine is under the same Stichting DuckDB Foundation MIT
licence as the Python bindings, and the wheel carries the one licence file for
both. These three are also leaf dependencies — `uv.lock` lists no transitive
runtime requirement behind any of them.

## Not covered here

Development-only tools are not redistributed and so carry no attribution
obligation from this project: pytest, ruff, Vite, TypeScript, Playwright,
pngjs and `pygame-ce` (the `art` group, used only by
`scripts/make_default_theme.py` to rasterise the spritesheet — deliberately
kept out of the runtime dependencies so the shipped package imports and serves
with no SDL anywhere).

The DuckDB catalogs you point this at are yours; Database Tycoon only reads
them.

## Re-verifying this file

Licences change between major versions, so this is checked against the
installed tree rather than trusted:

```bash
# Web: the licence text and the declared field, per package
for p in three zod; do
  cat "web/node_modules/$p/LICENSE"
  node -p "require('./web/node_modules/$p/package.json').license"
done
npm --prefix web ls --omit=dev --all        # confirm the inventory is complete

# Python: the licence file each wheel shipped
grep -iE '^(License|License-Expression|Classifier: License)' \
  .venv/lib/python3.*/site-packages/{duckdb,sqlglot,pyyaml}-*.dist-info/METADATA
cat .venv/lib/python3.*/site-packages/{duckdb,sqlglot,pyyaml}-*.dist-info/licenses/LICENSE
```

Last verified 2026-08-06 against the versions in the tables above.

## Trademarks

dbt is a trademark of dbt Labs, Inc. This project is independent and is not
affiliated with, sponsored by, or endorsed by dbt Labs. It reads the artifacts
dbt produces; the name is used only to say so.
