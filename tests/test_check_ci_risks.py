"""`scripts/check_ci_risks.py`, the CI risk check from #500.

The rules only judge what a PR adds, so every rule is tested both ways: the
risky addition is flagged, and the same text already on the base is not.
Risky strings are assembled at runtime so this file does not trip the check
when it is itself added in a PR.
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

TOJSON_SECRETS = "toJSON(" + "secrets)"
PIPE_TO_SHELL = "curl -fsSL https://example.com/install | " + "sh"


@pytest.fixture(scope="module")
def risks():
    spec = importlib.util.spec_from_file_location("check_ci_risks", REPO / "scripts" / "check_ci_risks.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_ci_risks"] = module
    spec.loader.exec_module(module)
    return module


def _rules(findings):
    return sorted(f.rule for f in findings)


# --------------------------------------------------------------------------- #
# added-line rules
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "text",
    [
        "run: echo '${{ " + TOJSON_SECRETS + " }}'",
        "env: ${{ tojson( " + "vars ) }}",
    ],
)
def test_serializing_secrets_or_vars_is_flagged(risks, text):
    findings = risks.scan_added_lines([risks.AddedLine("ci.yml", 3, text)])
    assert _rules(findings) == ["tojson-context"]
    assert findings[0].line == 3


def test_tojson_of_another_context_is_not_flagged(risks):
    assert risks.scan_added_lines([risks.AddedLine("ci.yml", 1, "${{ toJSON(github.event) }}")]) == []


@pytest.mark.parametrize(
    "text",
    [
        PIPE_TO_SHELL,
        "wget -qO- https://example.com/x.sh | " + "bash",
        "curl -sSL https://example.com | sudo -E " + "bash -s -- --yes",
        "bash <(" + "curl -s https://example.com/x.sh)",
    ],
)
def test_piping_a_download_into_a_shell_is_flagged(risks, text):
    assert _rules(risks.scan_added_lines([risks.AddedLine("x.sh", 1, text)])) == ["pipe-to-shell"]


@pytest.mark.parametrize(
    "text",
    [
        'curl -sSfL -o /tmp/tool.tar.gz "https://example.com/tool.tar.gz"',
        "curl -s https://example.com/data.json | jq .version",
        "cat install.sh | " + "sh",
    ],
)
def test_downloads_that_do_not_reach_a_shell_are_not_flagged(risks, text):
    assert risks.scan_added_lines([risks.AddedLine("x.sh", 1, text)]) == []


# --------------------------------------------------------------------------- #
# added-file rules
# --------------------------------------------------------------------------- #
def test_added_pth_files_and_workflows_are_flagged(risks):
    findings = risks.scan_added_files(
        ["src/evil.pth", ".github/workflows/new.yml", "docs/workflows/notes.md", ".github/pr-size.yml"]
    )
    assert [(f.rule, f.path) for f in findings] == [
        ("pth-file", "src/evil.pth"),
        ("new-workflow", ".github/workflows/new.yml"),
    ]


# --------------------------------------------------------------------------- #
# package.json lifecycle scripts
# --------------------------------------------------------------------------- #
def _pkg(**scripts):
    return json.dumps({"name": "web", "scripts": {"build": "vite build", **scripts}}, indent=2)


def test_a_new_install_script_is_flagged_with_its_line(risks):
    head = _pkg(postinstall="node setup.js")
    findings = risks.scan_package_json("web/package.json", _pkg(), head)
    assert _rules(findings) == ["install-script"]
    assert "adds" in findings[0].message
    assert head.splitlines()[findings[0].line - 1].strip().startswith('"postinstall"')


def test_a_changed_install_script_is_flagged(risks):
    findings = risks.scan_package_json("package.json", _pkg(prepare="husky"), _pkg(prepare="node x.js"))
    assert _rules(findings) == ["install-script"]
    assert "changes" in findings[0].message


def test_an_install_script_already_on_the_base_is_not_flagged(risks):
    assert risks.scan_package_json("package.json", _pkg(prepare="husky"), _pkg(prepare="husky")) == []


def test_a_brand_new_package_json_with_install_scripts_is_flagged(risks):
    findings = risks.scan_package_json("tools/package.json", None, _pkg(preinstall="a", install="b"))
    assert _rules(findings) == ["install-script", "install-script"]


def test_ordinary_scripts_and_unparseable_json_are_ignored(risks):
    assert risks.scan_package_json("package.json", _pkg(), _pkg(test="vitest")) == []
    assert risks.scan_package_json("package.json", None, "{ not json") == []


# --------------------------------------------------------------------------- #
# diff parsing
# --------------------------------------------------------------------------- #
def test_parse_added_lines_tracks_paths_and_line_numbers(risks):
    diff = "\n".join(
        [
            "diff --git a/a.yml b/a.yml",
            "index 1..2 100644",
            "--- a/a.yml",
            "+++ b/a.yml",
            "@@ -3,0 +4,2 @@ jobs:",
            "+first",
            "++ starts with plus signs",
            "diff --git a/gone.txt b/gone.txt",
            "deleted file mode 100644",
            "--- a/gone.txt",
            "+++ /dev/null",
            "@@ -1 +0,0 @@",
            "-old",
        ]
    )
    assert risks.parse_added_lines(diff) == [
        risks.AddedLine("a.yml", 4, "first"),
        risks.AddedLine("a.yml", 5, "+ starts with plus signs"),
    ]


def test_annotation_escapes_workflow_command_syntax(risks):
    finding = risks.Finding("pth-file", "a,b:c.pth", 2, "50% bad\nnews")
    assert risks.annotation(finding) == "::error file=a%2Cb%3Ac.pth,line=2,title=pth-file::50%25 bad%0Anews"


# --------------------------------------------------------------------------- #
# against a real repository
# --------------------------------------------------------------------------- #
@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for var in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{var}_NAME", "test")
        monkeypatch.setenv(f"GIT_{var}_EMAIL", "test@example.com")

    def run(*args):
        return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()

    run("init", "-q", "-b", "base")
    return run


def _write(path, text):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def test_collect_flags_only_what_the_branch_adds(risks, repo):
    _write("ci.sh", PIPE_TO_SHELL + "\n")
    _write("web/package.json", _pkg(prepare="husky"))
    _write("old/existing.pth", "")
    repo("add", "-A")
    repo("commit", "-qm", "base")
    base = repo("rev-parse", "HEAD")

    repo("checkout", "-qb", "pr")
    _write("ci.sh", PIPE_TO_SHELL + "\necho ok\n")
    _write("web/package.json", _pkg(prepare="husky", postinstall="node x.js"))
    _write(".github/workflows/new.yml", "run: echo ${{ " + TOJSON_SECRETS + " }}\n")
    Path("src").mkdir()
    repo("mv", "old/existing.pth", "src/moved.pth")
    repo("add", "-A")
    repo("commit", "-qm", "pr")

    findings = risks.collect(base, repo("rev-parse", "HEAD"))
    assert sorted((f.rule, f.path) for f in findings) == [
        ("install-script", "web/package.json"),
        ("new-workflow", ".github/workflows/new.yml"),
        ("pth-file", "src/moved.pth"),
        ("tojson-context", ".github/workflows/new.yml"),
    ]


def test_main_exits_zero_on_a_clean_branch_and_writes_the_summary(risks, repo, tmp_path, monkeypatch):
    _write("README.md", "hello\n")
    repo("add", "-A")
    repo("commit", "-qm", "base")
    base = repo("rev-parse", "HEAD")
    _write("README.md", "hello\nworld\n")
    repo("commit", "-qam", "pr")

    summary = tmp_path / "summary.md"
    monkeypatch.setenv("BASE_SHA", base)
    monkeypatch.setenv("HEAD_SHA", repo("rev-parse", "HEAD"))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    assert risks.main() == 0
    assert "No risky additions found." in summary.read_text()


def test_main_requires_a_base_sha(risks, monkeypatch, capsys):
    monkeypatch.delenv("BASE_SHA", raising=False)
    assert risks.main() == 1
    assert "BASE_SHA is required" in capsys.readouterr().out
