"""Guards on the agent skills shipped in this repository.

A skill's claims are about this repository's CLI and conventions, so a stale
one is worse than none. Each tier is a plugin root under plugins/, and the
skills directly under skills/ are for working on this repository. These checks
catch the drift a review found by hand.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"

# Commands and paths that were wrong in a published skill. Each entry names the
# correct replacement so the failure message tells the author what to write.
STALE = {
    "uvx ruff": "use `uv run ruff`; CI and CONTRIBUTING.md gate on the project's pinned ruff",
    "highest open `v0.1": "name the active release branch (see CONTRIBUTING.md, Release process)",
    "—": "use a comma, colon or period; see skills/repository-writing-style",
}


def _all_skill_files() -> list[Path]:
    return sorted([*ROOT.glob("skills/*/SKILL.md"), *ROOT.glob("plugins/*/skills/*/SKILL.md")])


def _plugin_roots() -> list[Path]:
    return sorted(p for p in (ROOT / "plugins").iterdir() if p.is_dir())


@pytest.mark.parametrize("root", _plugin_roots(), ids=lambda p: p.name)
def test_plugin_root_has_a_manifest_and_only_its_own_skills(root: Path) -> None:
    manifest = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] and manifest["version"] and manifest["description"]
    # Default discovery scans skills/*/SKILL.md under the plugin root. Nothing
    # else may sit at that depth, or installing the plugin ships it too.
    assert (root / "skills").is_dir(), f"{root.name} has no skills/ directory"


def test_marketplace_paths_resolve_from_each_plugin_source() -> None:
    manifest = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    for plugin in manifest["plugins"]:
        base = ROOT / plugin["source"]
        for rel in plugin.get("skills", []):
            assert (base / rel / "SKILL.md").is_file(), (
                f"{plugin['name']} lists {rel}, which is not a skill under {plugin['source']}"
            )


@pytest.mark.parametrize("path", _all_skill_files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_frontmatter_names_the_directory(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, "SKILL.md must open with frontmatter"
    fields = dict(line.split(":", 1) for line in match.group(1).splitlines() if re.match(r"^\w+:", line))
    assert fields["name"].strip() == path.parent.name
    assert fields["description"].strip(), "description must state when to load the skill"


@pytest.mark.parametrize("path", _all_skill_files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_no_stale_claims(path: Path) -> None:
    # A line that warns against a stale command (e.g. "Do not use `uvx ruff`") is
    # the point of a skill, so only lines that recommend the stale text are flagged.
    lines = path.read_text(encoding="utf-8").splitlines()
    hits = [
        f"{needle!r}: {advice}"
        for needle, advice in STALE.items()
        for line in lines
        if needle in line and not re.search(r"\bnot\b|\bnever\b|\bdon't\b", line, re.I)
    ]
    assert not hits, f"{path.relative_to(ROOT)} has stale text:\n" + "\n".join(hits)


def _marketplace() -> dict:
    return json.loads(MARKETPLACE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("plugin", _marketplace()["plugins"], ids=lambda p: p["name"])
def test_each_plugin_root_contains_exactly_its_listed_skills(plugin: dict) -> None:
    # The plugin's default scan reads skills/*/SKILL.md under its root. The skills
    # on disk must be the skills the marketplace lists, nothing more or less.
    base = ROOT / plugin["source"]
    on_disk = {p.parent.name for p in (base / "skills").glob("*/SKILL.md")}
    listed = {Path(rel).name for rel in plugin.get("skills", [])}
    assert on_disk == listed, f"{plugin['name']}: on disk {sorted(on_disk)}, listed {sorted(listed)}"


def test_readme_install_commands_name_a_real_plugin() -> None:
    names = {p["name"] for p in _marketplace()["plugins"]}
    readme = (ROOT / "skills" / "README.md").read_text(encoding="utf-8")
    for name in re.findall(r"/plugin install (\S+?)@", readme):
        assert name in names, f"README installs {name!r}; the marketplace has {sorted(names)}"


def test_contributing_citations_name_real_sections() -> None:
    # Cite a section by heading, not by line number: line numbers drift as
    # CONTRIBUTING.md changes, and a heading that disappears should fail here.
    headings = {
        " ".join(m.group(1).split())
        for m in re.finditer(r"^#{2,3} (.+)$", (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8"), re.M)
    }
    for path in _all_skill_files():
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\(line \d+\)", text), f"{path.relative_to(ROOT)} cites a line number"
        for section in re.findall(r'CONTRIBUTING\.md, "([^"]+)"', text):
            section = " ".join(section.split())
            assert section in headings, f"{path.relative_to(ROOT)} cites missing section {section!r}"
