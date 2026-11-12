#!/usr/bin/env python3
"""Flag supply-chain risks a pull request adds (issue #500).

Rules, each applied only to what the PR adds relative to its base:

  * an added line passes the whole `secrets` or `vars` context to `toJSON`
  * a `package.json` gains (or changes) a `preinstall`, `install`,
    `postinstall` or `prepare` script, or no longer parses as JSON
  * a `.pth` file is added
  * an added command pipes a `curl` or `wget` download into a shell or
    script interpreter, anywhere later in the pipeline (backslash-continued
    lines are joined first)
  * a file is added under `.github/workflows/`

The last rule is noisy by design: new workflows are rare here, and each one
should get a deliberate look.

CI runs this file from the PR's base ref, not from the PR's own checkout, so a
PR cannot loosen the rules that judge it. It is deliberately dependency-free so
it runs under a bare `python3`.

Environment:
  BASE_SHA             the PR's base commit (required)
  HEAD_SHA             the PR's head commit (default: HEAD)
  GITHUB_STEP_SUMMARY  optional path; the markdown report is appended here

Exit code: 1 when any rule matches, 0 otherwise.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import PurePosixPath

LIFECYCLE_SCRIPTS = ("preinstall", "install", "postinstall", "prepare")
WORKFLOWS_DIR = ".github/workflows/"

# GitHub expression function names are case-insensitive.
TOJSON_RE = re.compile(r"toJSON\(\s*(secrets|vars)\s*\)", re.IGNORECASE)
_INTERPRETER = r"(?:\S*/)?(?:(?:ba|z|da|k)?sh|python3?|perl|ruby|node)\b"
_RUNNER = r"(?:sudo\s+(?:-\S+\s+)*)?(?:(?:\S*/)?env\s+)?" + _INTERPRETER
_DOWNLOAD = r"\b(?:curl|wget)\b"
PIPE_TO_SHELL_RES = (
    # A download anywhere upstream of a single `|` (not `||`) into a runner,
    # so `tee` or `grep` stages in between don't hide it.
    re.compile(_DOWNLOAD + r".*?(?<!\|)\|(?!\|)\s*" + _RUNNER),
    re.compile(r"\b" + _RUNNER + r"\s+<\(\s*" + _DOWNLOAD),
    re.compile(r"\b" + _RUNNER + r"\s+-c\s+[\"']?\$\(\s*" + _DOWNLOAD),
)


@dataclass(frozen=True)
class Finding:
    rule: str
    path: str
    line: int | None
    message: str


@dataclass(frozen=True)
class AddedLine:
    path: str
    line: int
    text: str


# --------------------------------------------------------------------------- #
# rules (pure, so the tests don't need a repository)
# --------------------------------------------------------------------------- #
def join_continuations(lines: list[AddedLine]) -> list[AddedLine]:
    """Join backslash-continued added lines into one logical line.

    The joined line keeps the path and line number of its first physical
    line, and its parts are separated by newlines. Only consecutive added
    lines in the same file are joined.
    """
    joined: list[AddedLine] = []
    for added in lines:
        if joined:
            prev = joined[-1]
            last_line = prev.line + prev.text.count("\n")
            head = prev.text.rstrip()
            if prev.path == added.path and added.line == last_line + 1 and head.endswith("\\"):
                joined[-1] = AddedLine(prev.path, prev.line, head[:-1] + "\n" + added.text)
                continue
        joined.append(added)
    return joined


def scan_added_lines(lines: list[AddedLine]) -> list[Finding]:
    findings: list[Finding] = []
    for added in join_continuations(lines):
        m = TOJSON_RE.search(added.text)
        if m:
            findings.append(
                Finding(
                    "tojson-context",
                    added.path,
                    added.line,
                    f"serializes the whole `{m.group(1)}` context; reference the values you need by name",
                )
            )
        command = added.text.replace("\n", " ")
        if any(rx.search(command) for rx in PIPE_TO_SHELL_RES):
            findings.append(
                Finding(
                    "pipe-to-shell",
                    added.path,
                    added.line,
                    "pipes a download into a shell; download to a file and verify its checksum first",
                )
            )
    return findings


def scan_added_files(paths: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        if path.endswith(".pth"):
            findings.append(
                Finding(
                    "pth-file",
                    path,
                    None,
                    "adds a .pth file, which Python executes at interpreter startup",
                )
            )
        if path.startswith(WORKFLOWS_DIR):
            findings.append(
                Finding(
                    "new-workflow",
                    path,
                    None,
                    "adds a new workflow; it needs a deliberate review of its triggers and permissions",
                )
            )
    return findings


def _lifecycle_scripts(text: str | None) -> dict[str, str] | None:
    """Return the lifecycle scripts in a package.json, or None if it doesn't parse."""
    if text is None:
        return {}
    try:
        data = json.loads(text.removeprefix("\ufeff"))
    except ValueError:
        return None
    scripts = data.get("scripts") if isinstance(data, dict) else None
    if not isinstance(scripts, dict):
        return {}
    return {name: str(scripts[name]) for name in LIFECYCLE_SCRIPTS if name in scripts}


def _key_line(text: str, key: str) -> int | None:
    pattern = re.compile(r'"' + re.escape(key) + r'"\s*:')
    for number, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            return number
    return None


def scan_package_json(path: str, base_text: str | None, head_text: str) -> list[Finding]:
    before = _lifecycle_scripts(base_text) or {}
    after = _lifecycle_scripts(head_text)
    if after is None:
        # Fail closed: a file this check can't read could hold anything.
        return [
            Finding(
                "install-script",
                path,
                None,
                "is not valid JSON, so its install scripts could not be checked",
            )
        ]
    findings: list[Finding] = []
    for name, command in after.items():
        if before.get(name) == command:
            continue
        verb = "changes" if name in before else "adds"
        findings.append(
            Finding(
                "install-script",
                path,
                _key_line(head_text, name),
                f"{verb} an npm `{name}` script, which runs on every install",
            )
        )
    return findings


# --------------------------------------------------------------------------- #
# git plumbing
# --------------------------------------------------------------------------- #
def git(*args: str) -> str:
    out = subprocess.run(["git", "-c", "core.quotePath=false", *args], capture_output=True, check=True).stdout
    return out.decode("utf-8", errors="replace")


# Every diff is forced to text with no textconv or external driver, so a PR
# can't hide its added lines behind a `.gitattributes` it adds itself.
DIFF_FLAGS = ("--no-renames", "--text", "--no-textconv", "--no-ext-diff", "--no-color")


def git_show(rev: str, path: str) -> str | None:
    try:
        return git("show", "--no-textconv", f"{rev}:{path}")
    except subprocess.CalledProcessError:
        return None


def merge_base(base_sha: str, head_sha: str) -> str:
    try:
        return git("merge-base", base_sha, head_sha).strip() or base_sha
    except subprocess.CalledProcessError:
        return base_sha


def changed_paths(base: str, head: str, diff_filter: str) -> list[str]:
    # --no-renames: a file moved into .github/workflows/ is a new workflow.
    raw = git("diff", *DIFF_FLAGS, "--name-only", "-z", f"--diff-filter={diff_filter}", base, head)
    return [p for p in raw.split("\0") if p]


_C_ESCAPES = {"a": 7, "b": 8, "t": 9, "n": 10, "v": 11, "f": 12, "r": 13, '"': 34, "\\": 92}


def unquote_c(quoted: str) -> str:
    """Undo git's C-style path quoting, as in `"b/caf\\303\\251.yml"`."""
    body = quoted[1:-1] if len(quoted) >= 2 and quoted[0] == quoted[-1] == '"' else quoted
    out = bytearray()
    i = 0
    while i < len(body):
        ch = body[i]
        if ch != "\\" or i + 1 == len(body):
            out += ch.encode("utf-8")
            i += 1
        elif re.fullmatch(r"[0-7]{3}", body[i + 1 : i + 4]):
            out.append(int(body[i + 1 : i + 4], 8))
            i += 4
        elif body[i + 1] in _C_ESCAPES:
            out.append(_C_ESCAPES[body[i + 1]])
            i += 2
        else:
            out += body[i : i + 2].encode("utf-8")
            i += 2
    return out.decode("utf-8", errors="replace")


_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def parse_added_lines(diff: str) -> list[AddedLine]:
    added: list[AddedLine] = []
    path: str | None = None
    line_no = 0
    # A file header runs from `diff --git` to its first hunk. Tracking that
    # keeps an added line that happens to start with "++ " from being read
    # as a `+++` header.
    in_header = False
    for raw in diff.splitlines():
        if raw.startswith("diff --git "):
            in_header, path = True, None
            continue
        if in_header:
            if raw.startswith("+++ "):
                target = raw[4:]
                if target.startswith('"'):
                    target = unquote_c(target)
                path = target[2:] if target.startswith("b/") else None
            elif _HUNK_RE.match(raw):
                in_header = False
            else:
                continue
        hunk = _HUNK_RE.match(raw)
        if hunk:
            line_no = int(hunk.group(1))
            continue
        if path is None or in_header:
            continue
        if raw.startswith("+"):
            added.append(AddedLine(path, line_no, raw[1:]))
            line_no += 1
        elif raw.startswith(" "):
            line_no += 1
    return added


def collect(base_sha: str, head_sha: str) -> list[Finding]:
    base = merge_base(base_sha, head_sha)
    diff = git("diff", *DIFF_FLAGS, "--unified=0", base, head_sha)
    findings = scan_added_lines(parse_added_lines(diff))
    findings += scan_added_files(changed_paths(base, head_sha, "A"))
    for path in changed_paths(base, head_sha, "AM"):
        if PurePosixPath(path).name != "package.json":
            continue
        head_text = git_show(head_sha, path)
        if head_text is not None:
            findings += scan_package_json(path, git_show(base, path), head_text)
    return findings


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #
def _escape(value: str, *, prop: bool = False) -> str:
    value = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    if prop:
        value = value.replace(":", "%3A").replace(",", "%2C")
    return value


def annotation(finding: Finding) -> str:
    props = f"file={_escape(finding.path, prop=True)}"
    if finding.line is not None:
        props += f",line={finding.line}"
    props += f",title={_escape(finding.rule, prop=True)}"
    return f"::error {props}::{_escape(finding.message)}"


def report(findings: list[Finding]) -> str:
    lines = ["## CI risk check", ""]
    if not findings:
        lines.append("No risky additions found.")
        return "\n".join(lines) + "\n"
    lines.append(f"{len(findings)} finding(s):")
    lines.append("")
    for f in findings:
        where = f"`{f.path}`" + (f" line {f.line}" if f.line is not None else "")
        lines.append(f"- **{f.rule}** in {where}: {f.message}")
    return "\n".join(lines) + "\n"


def main() -> int:
    base_sha = os.environ.get("BASE_SHA", "").strip()
    head_sha = os.environ.get("HEAD_SHA", "").strip() or "HEAD"
    if not base_sha:
        print("::error::BASE_SHA is required")
        return 1

    findings = collect(base_sha, head_sha)
    text = report(findings)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(text)
    print(text)
    for f in findings:
        print(annotation(f))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
