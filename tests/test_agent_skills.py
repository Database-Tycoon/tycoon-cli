"""Guards on the agent skills shipped in skills/.

A skill's claims are about this repository's CLI and conventions, so a stale
one is worse than none. These checks catch the drift a review found by hand.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"

# Commands and paths that were wrong in a published skill. Each entry names the
# correct replacement so the failure message tells the author what to write.
STALE = {
    "uvx ruff": "use `uv run ruff`; CI and CONTRIBUTING.md gate on the project's pinned ruff",
    "highest open `v0.1": "name the active release branch (see CONTRIBUTING.md, Release process)",
    "—": "use a comma, colon or period; see skills/repository-writing-style",
}


def _skill_files() -> list[Path]:
    return sorted(SKILLS.glob("*/*/SKILL.md"))


def test_every_skill_is_inside_a_tier() -> None:
    stray = sorted(p.relative_to(ROOT) for p in SKILLS.glob("*/SKILL.md"))
    assert not stray, f"skills must sit under a tier directory, found: {stray}"


@pytest.mark.parametrize("path", _skill_files(), ids=lambda p: str(p.relative_to(SKILLS)))
def test_frontmatter_names_the_directory(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, "SKILL.md must open with frontmatter"
    fields = dict(line.split(":", 1) for line in match.group(1).splitlines() if re.match(r"^\w+:", line))
    assert fields["name"].strip() == path.parent.name
    assert fields["description"].strip(), "description must state when to load the skill"


@pytest.mark.parametrize("path", _skill_files(), ids=lambda p: str(p.relative_to(SKILLS)))
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


def test_marketplace_points_at_real_skills() -> None:
    manifest = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    for plugin in manifest["plugins"]:
        for rel in plugin.get("skills", []):
            assert (ROOT / rel / "SKILL.md").is_file(), f"{plugin['name']} lists missing {rel}"
