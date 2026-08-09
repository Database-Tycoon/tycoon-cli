"""The built-in demo catalog: a whole tycoon project, generated on demand.

`tycoon-city demo` serves this — no database, no dbt project, no checkout, no
`scripts/`. See `tycoon_city.demo.project` for what the city contains and why it
is generated rather than baked into the wheel (short version: every fact in it
is a time, and a baked one decays into a month-old "fresh pipeline").
"""

import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .project import build_demo_project

__all__ = ["DEMO_DIR_NAME", "build_demo_project", "materialise"]

# The project's directory name inside the temp dir. Visible in the footer as
# the database name, and in the path this prints at start-up, so it is worth
# being a name rather than a mkdtemp suffix.
DEMO_DIR_NAME = "demo-tycoon"


@contextmanager
def materialise(now: datetime | None = None) -> Iterator[Path]:
    """Build the demo project in a fresh temp directory; remove it on the way
    out. Yields the project root.

    A temp directory, rebuilt per run, and both halves of that are deliberate:

    - **temp**, because an installed wheel may sit in a read-only site-packages
      and the working directory is not ours to litter. `$TMPDIR` is the one
      place a CLI can always write.
    - **per run**, because the timestamps are generated relative to now. A
      cached copy would age exactly like a baked one — which is the failure
      this whole module exists to avoid — and rebuilding costs a couple of
      seconds once, at start-up.
    """
    tmp = Path(tempfile.mkdtemp(prefix="tycoon_city-"))
    try:
        yield build_demo_project(tmp / DEMO_DIR_NAME, now)
    finally:
        # ignore_errors: a locked metadata database on the way out must not
        # turn a clean Ctrl-C into a traceback.
        shutil.rmtree(tmp, ignore_errors=True)
