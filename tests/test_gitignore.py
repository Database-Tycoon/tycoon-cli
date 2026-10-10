"""The repo's .gitignore keeps local secret files out of commits.

tycoon-cli is a public repository, so a committed `.env` or dlt
`secrets.toml` would publish whatever credentials it holds.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _is_ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--quiet", path],
        cwd=REPO_ROOT,
        check=False,
    )
    return result.returncode == 0


@pytest.fixture(autouse=True)
def _require_git_checkout() -> None:
    if shutil.which("git") is None or not (REPO_ROOT / ".git").exists():
        pytest.skip("needs a git checkout of the repository")


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        ".env.local",
        "examples/demo/.env",
        ".dlt/secrets.toml",
        "src/tycoon/templates/nyc-transit/.dlt/secrets.toml",
    ],
)
def test_secret_files_are_ignored(path: str) -> None:
    assert _is_ignored(path), f"{path} would be committable"


def test_env_example_stays_committable() -> None:
    assert not _is_ignored(".env.example")
