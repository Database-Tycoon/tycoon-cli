from __future__ import annotations

import subprocess
from pathlib import Path

from dagster import asset

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
RILL_PROJECT_DIR = PROJECT_DIR / "rill"


@asset(group_name="rill")
def rill_build(context):
    """Build the Rill project to refresh all dashboards."""
    if not RILL_PROJECT_DIR.exists():
        context.log.warning("No rill/ directory found — skipping Rill build.")
        return

    context.log.info("Building Rill project...")
    try:
        result = subprocess.run(
            ["rill", "build"],
            cwd=RILL_PROJECT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        context.log.info(f"Rill build successful:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        context.log.error(f"Rill build failed:\n{e.stderr}")
        raise
