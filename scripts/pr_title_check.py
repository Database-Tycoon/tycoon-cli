#!/usr/bin/env python3
"""PR title check for the rule described in CONTRIBUTING.md.

Validates that a PR title looks like `type(scope): description` where:

  * `type` is one of the allowed `types`.
  * for `issue_ref_types` the scope is an issue / ticket reference matching
    one of `issue_ref_patterns` (e.g. `gh-128`, `PTC-300`).
  * for `freeform_scope_types` the scope may be anything, but must be present
    and non-empty.
  * the description is present and does not end with a period.
  * the whole title is no longer than `max_length` characters.

Release-promotion PRs (head branch matches `exempt_head_branch_regex` and
targets `release_promotion_base`) and PRs by `ignore_authors` are exempt.

`mode: warn` reports violations without failing; `mode: fail` blocks.

The script is deliberately dependency-free so it can run under a bare
`python` in CI or `uv run` locally.

Environment:
  PR_TITLE             the pull request title (required)
  HEAD_REF, BASE_REF   branch names (for the release-promotion exemption)
  PR_AUTHOR            the PR author's login (for ignore_authors)
  PR_TITLE_MODE        optional override of the config `mode`
  GITHUB_STEP_SUMMARY  optional path; the markdown report is appended here
  PR_TITLE_REPORT_FILE optional path; the markdown report is written here too

Exit code: 0 unless a violation is found while mode == "fail".
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

CONFIG_PATH = Path(".github/pr-title.yml")

DEFAULTS = {
    "mode": "warn",
    "types": ["feat", "fix", "refactor", "test", "docs", "chore", "ci"],
    "issue_ref_types": ["feat", "fix", "refactor", "test", "docs"],
    "freeform_scope_types": ["chore", "ci"],
    "issue_ref_patterns": [r"^gh-[0-9]+$", r"^PTC-[0-9]+$"],
    "max_length": 100,
    "exempt_head_branch_regex": r"^v\d+\.\d+\.\d+$",
    "release_promotion_base": "main",
    "ignore_authors": [],
}

TITLE_RE = re.compile(
    r"^(?P<type>[a-z]+)"
    r"(?:\((?P<scope>[^()]*)\))?"
    r"(?P<bang>!)?"
    r": (?P<desc>.*)$"
)


# --------------------------------------------------------------------------- #
# tiny YAML reader: scalars, and `key:` followed by `  - item` string lists
# --------------------------------------------------------------------------- #
def load_config(path: Path) -> dict:
    cfg = dict(DEFAULTS)
    if not path.exists():
        return cfg

    current_list_key: str | None = None
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        if re.match(r"\s*-\s", line) and current_list_key:
            cfg[current_list_key].append(_unquote(line.strip()[1:].strip()))
            continue

        m = re.match(r"([A-Za-z0-9_]+):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value == "":
            cfg[key] = []
            current_list_key = key
        else:
            current_list_key = None
            cfg[key] = _coerce(_unquote(value))
    return cfg


def _unquote(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1]
    return s


def _coerce(s: str):
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return s


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def check_title(title: str, cfg: dict) -> list[str]:
    problems: list[str] = []
    allowed = ", ".join(cfg["types"])

    if len(title) > cfg["max_length"]:
        problems.append(
            f"title is {len(title)} characters (limit {cfg['max_length']})."
        )

    m = TITLE_RE.match(title)
    if not m:
        problems.append(
            "title is not in `type(scope): description` format "
            f"(type must be one of: {allowed})."
        )
        return problems

    ctype = m.group("type")
    scope = m.group("scope")  # None if no parens at all
    desc = m.group("desc")

    if ctype not in cfg["types"]:
        problems.append(f"`{ctype}` is not an allowed type (allowed: {allowed}).")

    if scope is None:
        problems.append(
            f"a scope is required — write `{ctype}(<scope>): ...`."
        )
    elif scope.strip() == "":
        problems.append("the scope is empty.")
    else:
        needs_ref = ctype in cfg["issue_ref_types"]
        if needs_ref:
            patterns = cfg["issue_ref_patterns"]
            if not any(re.match(p, scope) for p in patterns):
                shown = " or ".join(f"`{p}`" for p in patterns)
                problems.append(
                    f"`{ctype}` requires an issue / ticket reference as the "
                    f"scope (matching {shown}) — e.g. `{ctype}(gh-128): ...` "
                    f"or `{ctype}(PTC-300): ...`; got `{scope}`."
                )

    if desc.strip() == "":
        problems.append("the description is empty.")
    elif desc.rstrip().endswith("."):
        problems.append("the description must not end with a period.")

    return problems


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    cfg = load_config(CONFIG_PATH)
    mode = (os.environ.get("PR_TITLE_MODE") or cfg["mode"]).strip().lower()
    if mode not in ("warn", "fail"):
        print(f"::error::invalid pr-title mode {mode!r} (expected warn or fail)")
        return 1

    title = os.environ.get("PR_TITLE", "").strip()
    head_ref = os.environ.get("HEAD_REF", "").strip()
    base_ref = os.environ.get("BASE_REF", "").strip()
    author = os.environ.get("PR_AUTHOR", "").strip()

    report: list[str] = ["## PR title check", ""]
    report.append(f"**mode:** `{mode}`")
    report.append("")
    report.append(f"> {title or '(empty title)'}")
    report.append("")

    if author and author in cfg["ignore_authors"]:
        report.append(f"Author `{author}` is on `ignore_authors` — **skipped**.")
        emit(report, violations=[], mode=mode)
        return 0

    if (
        head_ref
        and re.match(cfg["exempt_head_branch_regex"], head_ref)
        and base_ref == cfg["release_promotion_base"]
    ):
        report.append(
            f"Release-promotion PR (`{head_ref}` → `{base_ref}`) — **exempt** "
            "from the title convention."
        )
        emit(report, violations=[], mode=mode)
        return 0

    if not title:
        emit(report, violations=["the PR title is empty."], mode=mode)
        return 1 if mode == "fail" else 0

    violations = check_title(title, cfg)

    if not violations:
        report.append("**Result:** :white_check_mark: title matches the convention.")
    else:
        report.append("**Problems:**")
        report.append("")
        for v in violations:
            report.append(f"- {v}")
        report.append("")
        report.append("Format: `type(scope): description`")
        report.append("")
        report.append("| type | scope | example |")
        report.append("| --- | --- | --- |")
        report.append(
            "| `feat` `fix` `refactor` `test` `docs` | `gh-<N>` or `PTC-<N>` "
            "| `feat(gh-128): add layer materialization command` |"
        )
        report.append(
            "| `chore` `ci` | free-form | `chore(deps): bump typer to 0.16` |"
        )

    emit(report, violations=violations, mode=mode)
    return 1 if (violations and mode == "fail") else 0


def emit(report: list[str], *, violations: list[str], mode: str) -> None:
    if violations:
        if mode == "fail":
            report.append("")
            report.append(
                "**Result:** :x: the title does not match the convention — "
                "this check is **blocking**."
            )
        else:
            report.append("")
            report.append(
                "**Result:** :warning: the title does not match the convention. "
                "This check is in **warn** mode, so it is not blocking yet — "
                "but it will once enforcement is on."
            )

    text = "\n".join(report) + "\n"

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(text)

    report_file = os.environ.get("PR_TITLE_REPORT_FILE")
    if report_file:
        Path(report_file).write_text(text, encoding="utf-8")

    print(text)
    for v in violations:
        print(f"::{'error' if mode == 'fail' else 'warning'}::{v}")


if __name__ == "__main__":
    sys.exit(main())
