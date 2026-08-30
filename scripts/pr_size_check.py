#!/usr/bin/env python3
"""PR size check for the rule described in CONTRIBUTING.md.

Rules (all configurable in .github/pr-size.yml):

  * A PR may change at most `max_files` counted files. Files matching
    `exempt_path_globs` (e.g. template bundles) do not count.
  * Newly ADDED files matching `new_file_globs` may not exceed
    `new_file_max_lines` lines.
  * A PR whose head branch matches `exempt_head_branch_regex` and targets
    `release_promotion_base` is fully exempt (release-promotion roll-ups).

`mode: warn` reports violations without failing; `mode: fail` blocks.

The script is deliberately dependency-free so it can run under a bare
`python` in CI or `uv run` locally.

Environment:
  BASE_SHA, HEAD_SHA   commit range of the PR (required)
  HEAD_REF, BASE_REF   branch names (for the release-promotion exemption)
  PR_SIZE_MODE         optional override of the config `mode`
  GITHUB_STEP_SUMMARY  optional path; the markdown report is appended here
  PR_SIZE_REPORT_FILE  optional path; the markdown report is written here too

Exit code: 0 unless a violation is found while mode == "fail".
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

CONFIG_PATH = Path(".github/pr-size.yml")

DEFAULTS = {
    "mode": "warn",
    "max_files": 8,
    "new_file_max_lines": 300,
    "new_file_globs": ["src/**/*.py"],
    "exempt_path_globs": ["src/tycoon/templates/**"],
    "exempt_head_branch_regex": r"^v\d+\.\d+\.\d+$",
    "release_promotion_base": "main",
}


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
# glob matching with ** support (fnmatch has none)
# --------------------------------------------------------------------------- #
def glob_to_regex(pattern: str) -> re.Pattern[str]:
    i, n, out = 0, len(pattern), []
    while i < n:
        if pattern[i : i + 3] == "**/":
            out.append("(?:.*/)?")
            i += 3
        elif pattern[i : i + 2] == "**":
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(glob_to_regex(p).match(path) for p in patterns)


# --------------------------------------------------------------------------- #
# git plumbing
# --------------------------------------------------------------------------- #
def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def changed_entries(base_sha: str, head_sha: str) -> list[tuple[str, str]]:
    """Return (status, path) pairs. For renames the new path is used."""
    merge_base = git("merge-base", base_sha, head_sha).strip() or base_sha
    raw = git("diff", "--name-status", "-M", merge_base, head_sha)
    entries: list[tuple[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") or status.startswith("C"):
            entries.append((status[0], parts[2]))
        else:
            entries.append((status[0], parts[1]))
    return entries


def file_line_count(head_sha: str, path: str) -> int:
    try:
        blob = git("show", f"{head_sha}:{path}")
    except subprocess.CalledProcessError:
        return 0
    return len(blob.splitlines())


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    cfg = load_config(CONFIG_PATH)
    mode = os.environ.get("PR_SIZE_MODE") or cfg["mode"]
    mode = mode.strip().lower()
    if mode not in ("warn", "fail"):
        print(f"::error::invalid pr-size mode {mode!r} (expected warn or fail)")
        return 1

    base_sha = os.environ.get("BASE_SHA", "").strip()
    head_sha = os.environ.get("HEAD_SHA", "HEAD").strip() or "HEAD"
    head_ref = os.environ.get("HEAD_REF", "").strip()
    base_ref = os.environ.get("BASE_REF", "").strip()
    if not base_sha:
        print("::error::BASE_SHA is required")
        return 1

    report: list[str] = ["## PR size check", ""]
    report.append(f"**mode:** `{mode}`  |  **file limit:** {cfg['max_files']}")
    report.append("")

    # ----- release-promotion exemption ------------------------------------- #
    promo_re = cfg["exempt_head_branch_regex"]
    if (
        head_ref
        and re.match(promo_re, head_ref)
        and base_ref == cfg["release_promotion_base"]
    ):
        report.append(
            f"Release-promotion PR (`{head_ref}` → `{base_ref}`) — **exempt** "
            "from all size limits."
        )
        emit(report, violated=False, mode=mode)
        return 0

    entries = changed_entries(base_sha, head_sha)

    # ----- counted-files rule -------------------------------------------- #
    counted: list[str] = []
    exempt: list[str] = []
    for _status, path in entries:
        if matches_any(path, cfg["exempt_path_globs"]):
            exempt.append(path)
        else:
            counted.append(path)

    report.append(f"### Files changed: {len(counted)} counted / {cfg['max_files']} allowed")
    report.append("")
    for path in sorted(set(counted)):
        report.append(f"- `{path}`")
    if exempt:
        report.append("")
        report.append(f"<sub>{len(set(exempt))} exempt file(s) not counted:</sub>")
        for path in sorted(set(exempt)):
            report.append(f"<sub>- `{path}`</sub>")
    report.append("")

    violations: list[str] = []
    n_counted = len(set(counted))
    if n_counted > cfg["max_files"]:
        violations.append(
            f"{n_counted} counted files changed (limit {cfg['max_files']}). "
            "Split this into a sequence of smaller PRs "
            "(stack them by choosing the right base branch, or use gh-stack)."
        )

    # ----- new-file line-count rule ------------------------------------- #
    if cfg["new_file_max_lines"]:
        oversize: list[tuple[str, int]] = []
        for status, path in entries:
            if status != "A":
                continue
            if not matches_any(path, cfg["new_file_globs"]):
                continue
            lines = file_line_count(head_sha, path)
            if lines > cfg["new_file_max_lines"]:
                oversize.append((path, lines))
        if oversize:
            report.append(
                f"### New files over {cfg['new_file_max_lines']} lines"
            )
            report.append("")
            for path, lines in sorted(oversize):
                report.append(f"- `{path}` — {lines} lines")
                violations.append(
                    f"new file `{path}` is {lines} lines "
                    f"(limit {cfg['new_file_max_lines']} for added "
                    f"{'/'.join(cfg['new_file_globs'])})."
                )
            report.append("")

    emit(report, violated=bool(violations), mode=mode, violations=violations)
    if violations and mode == "fail":
        return 1
    return 0


def emit(
    report: list[str],
    *,
    violated: bool,
    mode: str,
    violations: list[str] | None = None,
) -> None:
    violations = violations or []

    if not violated:
        report.append("**Result:** :white_check_mark: within limits.")
    elif mode == "fail":
        report.append("**Result:** :x: over the limit — this check is **blocking**.")
    else:
        report.append(
            "**Result:** :warning: over the limit. This check is in **warn** "
            "mode, so it is not blocking yet — but it will once enforcement is on."
        )

    text = "\n".join(report) + "\n"

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(text)

    report_file = os.environ.get("PR_SIZE_REPORT_FILE")
    if report_file:
        Path(report_file).write_text(text, encoding="utf-8")

    print(text)
    for v in violations:
        level = "error" if mode == "fail" else "warning"
        print(f"::{level}::{v}")


if __name__ == "__main__":
    sys.exit(main())
