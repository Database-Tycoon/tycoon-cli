"""Rebuild CHANGELOG.md's [Unreleased] section when a tidy-up branch conflicts.

Use when a branch that reorders or relinks the Unreleased section (usually the
release-notes PR) conflicts with entries other PRs added since. Instead of
hand-merging, this takes:

  base  - CHANGELOG.md from the release branch tip (has every merged entry)
  tidy  - CHANGELOG.md from the tidy-up branch (has the wanted order + PR links)

and writes `out`: every entry from both (matched by bold title), in the tidy
branch's order with new entries appended per section. Each entry keeps the base
text, except its "(…)" link group: when the two branches differ there, the one
citing more `[#N][]` refs wins, and a tie goes to the tidy branch. All `[#N]: url` definitions are gathered at the end of the
section, issues first, then PRs. Everything outside the Unreleased section is
copied from base unchanged.

It then verifies that every entry is present and that the text outside the
link group is unchanged, and exits 1 if not. Entries must be single-line bullets
(`- **Title** (...). Text`), which is the CHANGELOG's convention.

    uv run python plugins/maintainers/skills/cutting-a-release/rebuild_unreleased.py base.md tidy.md out.md
"""

import re
import sys

REPO = "https://github.com/Database-Tycoon/tycoon-cli"


def section_bounds(s: str) -> tuple[int, int]:
    a = s.index("## [Unreleased]")
    return a, s.index("\n## [", a + 5)


def parse(sec: str):
    sections: dict[str, list[str]] = {}
    order: list[str] = []
    links: dict[int, str] = {}
    cur = None
    for line in sec.splitlines():
        if m := re.match(r"^### (\w+)", line):
            cur = m.group(1)
            sections[cur] = []
            order.append(cur)
        elif m := re.match(r"^\[#(\d+)\]: (\S+)", line):
            links[int(m.group(1))] = m.group(2)
        elif line.startswith("- **") and cur:
            sections[cur].append(line)
    return sections, order, links


def title(b: str) -> str:
    return re.match(r"- \*\*(.*?)\*\*", b).group(1)


def link_group(b: str):
    return re.search(r"\*\* \((.*?)\)\.", b)


def main(base_path: str, tidy_path: str, out_path: str) -> int:
    base, tidy = open(base_path).read(), open(tidy_path).read()
    ba, bb = section_bounds(base)
    ta, tb = section_bounds(tidy)
    B, border, blinks = parse(base[ba:bb])
    T, torder, tlinks = parse(tidy[ta:tb])
    links = {**tlinks, **blinks}

    out = []
    for sec in border + [s for s in torder if s not in border]:
        by_title = {title(b): b for b in B.get(sec, [])}
        for x in T.get(sec, []):
            by_title.setdefault(title(x), x)  # entry only on the tidy branch
        tidy_titles = [title(x) for x in T.get(sec, [])]
        ordered = [t for t in tidy_titles if t in by_title]
        ordered += [t for t in by_title if t not in ordered]
        bullets = []
        for t in ordered:
            b = by_title[t]
            tb_ = next((x for x in T.get(sec, []) if title(x) == t), None)
            hg, tg = link_group(b), tb_ and link_group(tb_)
            if hg and tg and hg.group(1) != tg.group(1):
                refs = lambda g: len(re.findall(r"\[#\d+\]\[\]", g))  # noqa: E731
                if refs(tg.group(1)) >= refs(hg.group(1)):
                    b = b.replace(f"({hg.group(1)})", f"({tg.group(1)})", 1)
            bullets.append(b)
        out.append(f"### {sec}\n\n" + "\n".join(bullets) + "\n")
    body = "\n".join(out)

    used = sorted({int(n) for n in re.findall(r"\[#(\d+)\]\[\]", body)})
    for n in used:
        links.setdefault(n, f"{REPO}/issues/{n}")
    issues = [n for n in used if "/issues/" in links[n]]
    prs = [n for n in used if "/pull/" in links[n]]
    defs = "\n".join(f"[#{n}]: {links[n]}" for n in issues + prs)
    new = base[:ba] + "## [Unreleased]\n\n" + body + "\n" + defs + "\n" + base[bb:]

    na, nb = section_bounds(new)
    N, _, _ = parse(new[na:nb])

    def strip(b: str) -> str:
        return re.sub(r"\*\* \(.*?\)\.", "** ().", b)

    want = {strip(b) for s in [*B.values(), *T.values()] for b in s}
    got = [strip(b) for s in N.values() for b in s]
    ok = sorted(want) == sorted(got)
    print(f"entries: expected {len(want)}, written {len(got)}, text unchanged outside links: {ok}")
    if not ok:
        return 1
    open(out_path, "w").write(new)
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
