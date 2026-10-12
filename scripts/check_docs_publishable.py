#!/usr/bin/env python3
"""Fail if the built docs site publishes internal pages or dead nav links.

`mkdocs build --strict` catches neither case, which is why this exists
(gh-348):

* A page that `draft_docs` or `exclude_docs` should have withheld ships anyway
  if someone edits `mkdocs.yml`. Those pages build cleanly, so the build stays
  green and the pages go public.
* A `nav` entry pointing at a withheld page is reported at INFO. MkDocs caps
  that message at INFO regardless of `validation.nav.not_found`, so `--strict`
  exits 0, the page is not built, and every page in the site carries a sidebar
  link that 404s.

Both checks read `mkdocs.yml` through MkDocs' own loader rather than restating
its lists here, so this cannot drift from the configuration it enforces. Both
are positive checks against the built tree: an empty or missing `site/` fails
rather than passing quietly, because a guard that cannot tell "nothing wrong"
from "did not look" is worse than no guard.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

from mkdocs.config import load_config
from mkdocs.structure.files import File
from mkdocs.utils import is_markdown_file

REPO_ROOT = Path(__file__).resolve().parents[1]

# Directories that must stay out of the published site. The two checks below
# read their lists from `mkdocs.yml`, which means they follow the config: drop
# `city/` from `draft_docs` and those pages simply become publishable, which
# reads as an intentional change rather than the regression it is. This is the
# floor. Publishing one of these deliberately means editing this line, which a
# reviewer sees.
MUST_STAY_WITHHELD = ("city", "proposals")


def dest_of(src: str, config) -> Path:
    """Where MkDocs would write the page built from `src`."""
    return Path(
        File(
            src,
            config["docs_dir"],
            config["site_dir"],
            config["use_directory_urls"],
        ).abs_dest_path
    )


def nav_targets(nav) -> list[str]:
    """Every Markdown file referenced anywhere in the nav tree."""
    found: list[str] = []
    if isinstance(nav, str):
        target = nav.split("#", 1)[0].split("?", 1)[0]
        if is_markdown_file(target):
            found.append(target)
    elif isinstance(nav, list):
        for entry in nav:
            found.extend(nav_targets(entry))
    elif isinstance(nav, dict):
        for value in nav.values():
            found.extend(nav_targets(value))
    return found


def main() -> int:
    config = load_config(str(REPO_ROOT / "mkdocs.yml"))
    docs_dir = Path(config["docs_dir"])
    site_dir = Path(config["site_dir"])

    if not site_dir.is_dir() or not (site_dir / "index.html").is_file():
        print(
            f"::error::{site_dir} has no index.html; run `mkdocs build` before this check",
            file=sys.stderr,
        )
        return 1

    failures: list[str] = []

    specs = [config[key] for key in ("exclude_docs", "draft_docs") if config[key] is not None]
    if not specs:
        print(
            "::error::neither draft_docs nor exclude_docs is set in mkdocs.yml, "
            "so every page under docs/ would publish",
            file=sys.stderr,
        )
        return 1

    def withheld_by_config(rel: str) -> bool:
        return any(spec.match_file(rel) for spec in specs)

    # 1. The directories this check exists for must still be withheld.
    for name in MUST_STAY_WITHHELD:
        directory = docs_dir / name
        if not directory.is_dir():
            failures.append(
                f"MUST_STAY_WITHHELD names docs/{name}/, which no longer exists. Update that "
                "list in the same change that moved or removed it, so the floor keeps meaning "
                "something."
            )
            continue
        exposed = [
            path.relative_to(docs_dir).as_posix()
            for path in sorted(directory.rglob("*"))
            if path.is_file() and not withheld_by_config(path.relative_to(docs_dir).as_posix())
        ]
        if exposed:
            failures.append(
                f"docs/{name}/ is no longer withheld by mkdocs.yml ({len(exposed)} files, including {exposed[0]})"
            )

    # 2. Nothing withheld may appear in the built site.
    withheld = 0
    for path in sorted(docs_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(docs_dir).as_posix()
        if not withheld_by_config(rel):
            continue
        withheld += 1
        if is_markdown_file(rel) and dest_of(rel, config).exists():
            failures.append(f"{rel} is withheld by mkdocs.yml but was published")

    # 3. Every relative link in the built site must resolve to something on
    #    disk. This covers nav entries and in-page links alike: MkDocs caps
    #    both at INFO (`nav.py` and `pages.py` use `min(logging.INFO, ...)`),
    #    so no `validation:` setting can make `--strict` fail on either, and a
    #    link to a withheld page 404s for every reader.
    base_path = urlsplit(config["site_url"] or "/").path or "/"
    checked = 0
    for page in sorted(site_dir.rglob("*.html")):
        for href in set(re.findall(r'href="([^"]+)"', page.read_text(encoding="utf-8"))):
            if href.startswith(("http://", "https://", "//", "#", "mailto:", "tel:", "data:")):
                continue
            target = href.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            if target.startswith("/"):
                # Rooted at site_url's path (404.html uses absolute links).
                rel = target[len(base_path) :] if target.startswith(base_path) else target[1:]
                resolved = (site_dir / rel).resolve()
            else:
                resolved = (page.parent / target).resolve()
            if resolved.is_dir():
                resolved = resolved / "index.html"
            checked += 1
            if not resolved.exists():
                failures.append(f"{page.relative_to(site_dir)} links to {href}, which was not built")

    if failures:
        for failure in failures:
            print(f"::error::{failure}", file=sys.stderr)
        print(
            "\nCheck `nav`, `draft_docs` and `exclude_docs` in mkdocs.yml. "
            "See the Documentation section of CONTRIBUTING.md.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: {withheld} withheld files absent from the build, {checked} links all resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
